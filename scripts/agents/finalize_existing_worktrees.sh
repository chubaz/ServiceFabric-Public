#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib_wave.sh
source "$SCRIPT_DIR/lib_wave.sh"

DRY_RUN=0
BOOTSTRAP_SHA=""
WAVE_ID=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --wave) WAVE_ID="${2:-}"; shift 2 ;;
        --bootstrap-sha) BOOTSTRAP_SHA="${2:-}"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

[[ -n "$BOOTSTRAP_SHA" ]] || { echo "--bootstrap-sha is required" >&2; exit 2; }
sf_load_config "$WAVE_ID"

ROOT="$(sf_repo_root)"
CURRENT_ROOT="$(pwd -P)"
EXPECTED_INTEGRATION="$(cd "$SF_WT_INTEGRATION" 2>/dev/null && pwd -P || true)"
[[ "$CURRENT_ROOT" == "$EXPECTED_INTEGRATION" ]] || {
    echo "Run this command from the integration worktree: $SF_WT_INTEGRATION" >&2
    exit 2
}

git cat-file -e "${BOOTSTRAP_SHA}^{commit}" >/dev/null 2>&1 || {
    echo "Bootstrap SHA is not a local commit: $BOOTSTRAP_SHA" >&2
    exit 2
}

WAVE_BASE="$(sf_wave_base)"
git merge-base --is-ancestor "$WAVE_BASE" "$BOOTSTRAP_SHA" || {
    echo "Bootstrap SHA does not descend from $SF_WAVE_ID base $WAVE_BASE" >&2
    exit 2
}

run_step() {
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "DRY-RUN: $*"
    else
        "$@"
    fi
}

verify_lane() {
    local lane="$1" path branch expected_branch
    path="$(sf_lane_path "$lane")"
    expected_branch="$(sf_lane_branch "$lane")"
    sf_is_valid_worktree "$path" || { echo "$lane: invalid Git worktree: $path" >&2; exit 2; }
    sf_is_clean "$path" || { echo "$lane: worktree is dirty: $path" >&2; exit 2; }
    branch="$(sf_branch "$path")" || { echo "$lane: detached HEAD is not allowed" >&2; exit 2; }
    [[ "$branch" == "$expected_branch" ]] || {
        echo "$lane: expected branch $expected_branch, found $branch" >&2
        exit 2
    }
    git -C "$path" merge-base --is-ancestor "$WAVE_BASE" HEAD || {
    echo "$lane: branch does not descend from $SF_WAVE_ID base $WAVE_BASE" >&2
        exit 2
    }
    if [[ "$lane" == "integration" ]]; then
        [[ "$(sf_head "$path")" == "$BOOTSTRAP_SHA" ]] || {
            echo "integration: HEAD must equal bootstrap SHA $BOOTSTRAP_SHA" >&2
            exit 2
        }
    else
        git -C "$path" merge-base --is-ancestor HEAD "$BOOTSTRAP_SHA" || {
            echo "$lane: unexpected commits exist before bootstrap synchronization" >&2
            exit 2
        }
    fi
}

for lane in $(sf_lanes); do
    verify_lane "$lane"
done

if [[ "$DRY_RUN" != "1" ]]; then
    mkdir -p "$(sf_state_dir)"
    printf '%s\n' "$BOOTSTRAP_SHA" > "$(sf_bootstrap_path)"
fi

for lane in $(sf_lanes); do
    path="$(sf_lane_path "$lane")"
    echo "$lane: $([[ "$lane" == "integration" ]] && printf 'verify only' || printf 'fast-forward -> initialize -> preflight -> render')"

    if [[ "$lane" != "integration" ]]; then
        run_step git -C "$path" merge --ff-only "$BOOTSTRAP_SHA"
    fi

    if [[ "$DRY_RUN" == "1" ]]; then
        run_step "$path/scripts/agents/init_worktree_runtime.sh" "$lane" "$path" "$SF_STATE_BASE" "$SF_WAVE_ID"
    elif ! "$path/scripts/agents/init_worktree_runtime.sh" "$lane" "$path" "$SF_STATE_BASE" "$SF_WAVE_ID"; then
        echo "$lane: runtime initialization failed" >&2
        exit 23
    fi

    if [[ "${SF_AGENT_FAIL_PREFLIGHT:-}" == "$lane" || "${SF_AGENT_FAIL_PREFLIGHT:-}" == "1" ]]; then
        echo "$lane: preflight forced to fail" >&2
        exit 24
    fi

    if [[ "$DRY_RUN" == "1" ]]; then
        echo "DRY-RUN: git -C $path status --short"
        echo "DRY-RUN: python3 scripts/agent/wave_task_preflight.py --wave $SF_WAVE_ID --task $lane"
        echo "DRY-RUN: python3 scripts/agent/render_wave_prompt.py --wave $SF_WAVE_ID --task $lane --output .agent-runs/$SF_WAVE_ID/$lane/prompt.md"
        continue
    fi

    preflight_log="$(sf_run_dir "$lane")/preflight.log"
    if ! (
        cd "$path"
        # shellcheck disable=SC1091
        source .agent-runtime.env
        python3 scripts/agent/wave_task_preflight.py --wave "$SF_WAVE_ID" --task "$lane" >"$preflight_log" 2>&1
        python3 scripts/agent/render_wave_prompt.py --wave "$SF_WAVE_ID" --task "$lane" --output ".agent-runs/$SF_WAVE_ID/$lane/prompt.md" >/dev/null
    ); then
        cat "$preflight_log" >&2
        echo "$lane: preflight or prompt rendering failed" >&2
        exit 24
    fi

    cat > "$(sf_readiness_path "$lane")" <<EOF
{
  "bootstrapSha": "$BOOTSTRAP_SHA",
  "branch": "$(sf_branch "$path")",
  "head": "$(sf_head "$path")",
  "lane": "$lane",
  "preflight": "pass",
  "prompt": "$(sf_prompt_path "$lane")",
  "runtimeEnv": "$(sf_runtime_env "$lane")",
  "waveId": "$SF_WAVE_ID"
}
EOF
    echo "$lane launch: $path/scripts/agents/launch_lane.sh --wave $SF_WAVE_ID $lane --interactive"
done
