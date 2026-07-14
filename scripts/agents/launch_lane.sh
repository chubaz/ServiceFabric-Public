#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib_wave.sh
source "$SCRIPT_DIR/lib_wave.sh"

WAVE_ID=""
if [[ "${1:-}" == "--wave" ]]; then
    WAVE_ID="${2:-}"
    shift 2
fi
LANE="${1:-}"
[[ -n "$LANE" ]] || { echo "Usage: launch_lane.sh [--wave WAVE_ID] LANE [--interactive|--exec]" >&2; exit 2; }
shift
LANE="$(sf_task_name "$LANE")"

MODE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --interactive) MODE="interactive"; shift ;;
        --exec) MODE="exec"; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
[[ -n "$MODE" ]] || MODE="interactive"

[[ -n "$WAVE_ID" ]] && export SF_WAVE_ID="$WAVE_ID"
sf_load_config
WORKTREE="$(sf_lane_path "$LANE")"
EXPECTED_BRANCH="$(sf_lane_branch "$LANE")"
PROMPT="$(sf_prompt_path "$LANE")"
RUN_DIR="$(sf_run_dir "$LANE")"

sf_is_valid_worktree "$WORKTREE" || { echo "$LANE: invalid worktree: $WORKTREE" >&2; exit 2; }
[[ "$(sf_branch "$WORKTREE")" == "$EXPECTED_BRANCH" ]] || {
    echo "$LANE: wrong branch, expected $EXPECTED_BRANCH" >&2
    exit 2
}
sf_is_clean "$WORKTREE" || { echo "$LANE: dirty worktree" >&2; exit 2; }
[[ -f "$(sf_runtime_env "$LANE")" ]] || { echo "$LANE: runtime is not initialized" >&2; exit 2; }
[[ -f "$PROMPT" ]] || { echo "$LANE: rendered prompt is missing: $PROMPT" >&2; exit 2; }

if [[ "$LANE" != "integration" ]]; then
    [[ -f "$(sf_contracts_path)" ]] && grep -q '"contractsStatus": "frozen"' "$(sf_contracts_path)" || {
        echo "$LANE: contractsStatus:frozen is required before specialist launch" >&2
        exit 2
    }
fi

(
    cd "$WORKTREE"
    # shellcheck disable=SC1091
    source .agent-runtime.env
    python3 scripts/agent/wave_task_preflight.py --wave "$SF_WAVE_ID" --task "$LANE" >/dev/null
)

if [[ "$MODE" == "interactive" ]]; then
    echo "Prompt: $PROMPT"
    echo "Read and execute the rendered ${SF_WAVE_ID} prompt at $PROMPT."
    cd "$WORKTREE"
    # shellcheck disable=SC1091
    source .agent-runtime.env
    exec codex
fi

mkdir -p "$RUN_DIR"
EVENTS="$RUN_DIR/events.jsonl"
STDERR_LOG="$RUN_DIR/stderr.log"
cd "$WORKTREE"
# shellcheck disable=SC1091
source .agent-runtime.env
codex exec -C "$WORKTREE" --sandbox workspace-write --json - < "$PROMPT" > "$EVENTS" 2> "$STDERR_LOG"
