#!/usr/bin/env bash
set -euo pipefail

sf_config_file() {
    printf '%s\n' "${SF_AGENT_WORKTREES_ENV:-.agent-worktrees.env}"
}

sf_load_config() {
    local config_file
    config_file="$(sf_config_file)"
    if [[ ! -f "$config_file" ]]; then
        echo "Missing worktree configuration: $config_file" >&2
        echo "Create it from the matching config/agents/<wave>/worktrees.local.example.env." >&2
        return 2
    fi
    # shellcheck disable=SC1090
    source "$config_file"
    : "${SF_WAVE_ID:?SF_WAVE_ID is required}"
    : "${SF_STATE_BASE:?SF_STATE_BASE is required}"
    : "${SF_WT_INTEGRATION:?SF_WT_INTEGRATION is required}"
    for lane in $(sf_lanes); do
        case "$lane" in
            integration) : "${SF_WT_INTEGRATION:?SF_WT_INTEGRATION is required}" ;;
            assembly) : "${SF_WT_ASSEMBLY:?SF_WT_ASSEMBLY is required}" ;;
            resources) : "${SF_WT_RESOURCES:?SF_WT_RESOURCES is required}" ;;
            kits-blueprints) : "${SF_WT_KITS_BLUEPRINTS:?SF_WT_KITS_BLUEPRINTS is required}" ;;
            testing) : "${SF_WT_TESTING:?SF_WT_TESTING is required}" ;;
            generator) : "${SF_WT_GENERATOR:?SF_WT_GENERATOR is required}" ;;
            application-builder) : "${SF_WT_APPLICATION_BUILDER:?SF_WT_APPLICATION_BUILDER is required}" ;;
            agent-guidance) : "${SF_WT_AGENT_GUIDANCE:?SF_WT_AGENT_GUIDANCE is required}" ;;
            acceptance) : "${SF_WT_ACCEPTANCE:?SF_WT_ACCEPTANCE is required}" ;;
        esac
    done
}

sf_repo_root() {
    git rev-parse --show-toplevel
}

sf_manifest_wave_id() {
    [[ "${SF_WAVE_ID}" == "wave-01" ]] && printf 'wave-1\n' || printf '%s\n' "$SF_WAVE_ID"
}

sf_task_name() {
    case "$1" in
        kits_blueprints) printf 'kits-blueprints\n' ;;
        *) printf '%s\n' "$1" ;;
    esac
}

sf_lane_path() {
    case "$1" in
        integration) printf '%s\n' "$SF_WT_INTEGRATION" ;;
        assembly) printf '%s\n' "$SF_WT_ASSEMBLY" ;;
        resources) printf '%s\n' "$SF_WT_RESOURCES" ;;
        kits-blueprints) printf '%s\n' "$SF_WT_KITS_BLUEPRINTS" ;;
        testing) printf '%s\n' "$SF_WT_TESTING" ;;
        generator) printf '%s\n' "$SF_WT_GENERATOR" ;;
        application-builder) printf '%s\n' "$SF_WT_APPLICATION_BUILDER" ;;
        agent-guidance) printf '%s\n' "$SF_WT_AGENT_GUIDANCE" ;;
        acceptance) printf '%s\n' "$SF_WT_ACCEPTANCE" ;;
        *) echo "Unknown lane: $1" >&2; return 2 ;;
    esac
}

sf_lane_branch() {
    local lane="$1"
    python3 - "$lane" <<'PY'
import json, os, sys
lane = sys.argv[1]
wave = os.environ.get("SF_WAVE_ID", "wave-01")
manifest = "wave-1" if wave == "wave-01" else wave
path = f"config/agent/waves/{manifest}.json" if lane == "integration" else f"config/agent/waves/{manifest}/tasks/{lane}.json"
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
print(data["integration_branch"] if lane == "integration" else data["branch"])
PY
}

sf_wave_base() {
    if [[ -n "${SF_AGENT_WAVE_BASE_OVERRIDE:-}" ]]; then
        printf '%s\n' "$SF_AGENT_WAVE_BASE_OVERRIDE"
        return 0
    fi
    python3 - <<'PY'
import json, os
wave = os.environ.get("SF_WAVE_ID", "wave-01")
manifest = "wave-1" if wave == "wave-01" else wave
with open(f"config/agent/waves/{manifest}.json", encoding="utf-8") as handle:
    print(json.load(handle)["base_commit"])
PY
}

sf_lanes() {
    case "${SF_WAVE_ID:-wave-01}" in
        wave-01|wave-1) printf '%s\n' integration assembly resources kits-blueprints testing ;;
        wave-03|wave-3) printf '%s\n' integration generator application-builder agent-guidance acceptance ;;
        *) echo "Unknown wave: ${SF_WAVE_ID:-}" >&2; return 2 ;;
    esac
}

sf_specialist_lanes() {
    sf_lanes | sed '/^integration$/d'
}

sf_state_dir() {
    printf '%s/%s\n' "$SF_STATE_BASE" "$SF_WAVE_ID"
}

sf_run_dir() {
    printf '%s/.agent-runs/%s/%s\n' "$(sf_lane_path "$1")" "$SF_WAVE_ID" "$1"
}

sf_runtime_env() {
    printf '%s/.agent-runtime.env\n' "$(sf_lane_path "$1")"
}

sf_prompt_path() {
    printf '%s/prompt.md\n' "$(sf_run_dir "$1")"
}

sf_readiness_path() {
    printf '%s/readiness.json\n' "$(sf_run_dir "$1")"
}

sf_canonical_handoff_path() {
    local lane="$1"
    python3 - "$lane" <<'PY'
import json, os, sys
lane = sys.argv[1]
wave = os.environ.get("SF_WAVE_ID", "wave-01")
manifest = "wave-1" if wave == "wave-01" else wave
with open(f"config/agent/waves/{manifest}.json", encoding="utf-8") as handle:
    data = json.load(handle)
print(data["canonical_handoffs"][lane])
PY
}

sf_committed_readiness_path() {
    python3 - <<'PY'
import json, os
wave = os.environ.get("SF_WAVE_ID", "wave-01")
manifest = "wave-1" if wave == "wave-01" else wave
with open(f"config/agent/waves/{manifest}.json", encoding="utf-8") as handle:
    data = json.load(handle)
print(data["readiness_metadata"])
PY
}

sf_integration_queue_path() {
    python3 - <<'PY'
import json, os
wave = os.environ.get("SF_WAVE_ID", "wave-01")
manifest = "wave-1" if wave == "wave-01" else wave
with open(f"config/agent/waves/{manifest}.json", encoding="utf-8") as handle:
    data = json.load(handle)
print(data["integration_queue"])
PY
}

sf_mirror_handoff() {
    local lane="$1"
    local path
    local canonical
    path="$(sf_lane_path "$lane")"
    canonical="$(sf_repo_root)/$(sf_canonical_handoff_path "$lane")"
    [[ -f "$canonical" ]] || return 1
    python3 scripts/agent/sync_wave_handoffs.py --best-effort --wave "$SF_WAVE_ID" --task "$lane" --worktree "$path" >/dev/null
}

sf_contracts_path() {
    printf '%s/contracts.json\n' "$(sf_state_dir)"
}

sf_bootstrap_path() {
    printf '%s/bootstrap.sha\n' "$(sf_state_dir)"
}

sf_is_clean() {
    [[ -z "$(git -C "$1" status --porcelain)" ]]
}

sf_branch() {
    git -C "$1" symbolic-ref --short HEAD
}

sf_head() {
    git -C "$1" rev-parse HEAD
}

sf_is_valid_worktree() {
    local path="$1"
    local top
    [[ -d "$path" ]] || return 1
    git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1
    top="$(git -C "$path" rev-parse --show-toplevel)" || return 1
    [[ "$(cd "$path" && pwd -P)" == "$(cd "$top" && pwd -P)" ]]
}

sf_shell_quote() {
    python3 - "$1" <<'PY'
import shlex, sys
print(shlex.quote(sys.argv[1]))
PY
}
