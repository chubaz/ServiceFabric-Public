#!/usr/bin/env bash
set -euo pipefail

sf_config_file() {
    printf '%s\n' "${SF_AGENT_WORKTREES_ENV:-.agent-worktrees.env}"
}

sf_load_config() {
    local requested_wave="${1:-}"
    local config_file
    if [[ -z "${SF_AGENT_WORKTREES_ENV:-}" && -n "$requested_wave" && -f ".agent-worktrees-$requested_wave.env" ]]; then
        config_file=".agent-worktrees-$requested_wave.env"
    elif [[ -z "${SF_AGENT_WORKTREES_ENV:-}" && -n "$requested_wave" && -f ".agent-worktrees.$requested_wave.env" ]]; then
        config_file=".agent-worktrees.$requested_wave.env"
    else
        config_file="$(sf_config_file)"
    fi
    if [[ ! -f "$config_file" ]]; then
        echo "Missing worktree configuration: $config_file" >&2
        echo "Create it from the selected wave's worktrees.local.example.env." >&2
        return 2
    fi
    # shellcheck disable=SC1090
    source "$config_file"
    : "${SF_WAVE_ID:?SF_WAVE_ID is required}"
    : "${SF_STATE_BASE:?SF_STATE_BASE is required}"
    if [[ -n "$requested_wave" && "$SF_WAVE_ID" != "$requested_wave" ]]; then
        echo "Worktree configuration declares $SF_WAVE_ID, not $requested_wave" >&2
        return 2
    fi
    : "${SF_WT_INTEGRATION:?SF_WT_INTEGRATION is required}"
    for variable in $(sf_wave_value specialist_worktree_env_values); do
        : "${!variable:?$variable is required}"
    done
}

sf_wave_value() {
    local key="$1"
    python3 - "$SF_WAVE_ID" "$key" <<'PY'
import sys
from scripts.agent.wave_common import wave
value = wave(sys.argv[1]).get(sys.argv[2])
if sys.argv[2] == "specialist_worktree_env_values":
    data = wave(sys.argv[1])["worktree_env"]
    print(" ".join(value for lane, value in data.items() if lane != "integration"))
elif isinstance(value, list):
    print(" ".join(str(item) for item in value))
elif value is not None:
    print(value)
PY
}

sf_repo_root() {
    git rev-parse --show-toplevel
}

sf_manifest_wave_id() {
    printf '%s\n' "$SF_WAVE_ID"
}

sf_task_name() {
    printf '%s\n' "$1"
}

sf_lane_path() {
    local variable
    variable="$(sf_lane_value "$1" worktree)" || return
    printf '%s\n' "${!variable}"
}

sf_lane_value() {
    local lane="$1" key="$2"
    python3 - "$SF_WAVE_ID" "$lane" "$key" <<'PY'
import sys
from scripts.agent.wave_common import task, wave
wave_id, lane, key = sys.argv[1:]
if key == "worktree":
    print(wave(wave_id)["worktree_env"][lane])
else:
    print(task(lane, wave_id)[key])
PY
}

sf_lane_branch() {
    sf_lane_value "$1" branch
}

sf_wave_base() {
    if [[ -n "${SF_AGENT_WAVE_BASE_OVERRIDE:-}" ]]; then
        printf '%s\n' "$SF_AGENT_WAVE_BASE_OVERRIDE"
        return 0
    fi
    sf_wave_value base_commit
}

sf_lanes() {
    sf_wave_value lanes | tr ' ' '\n'
}

sf_specialist_lanes() {
    sf_wave_value specialist_lanes | tr ' ' '\n'
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
    sf_lane_value "$1" handoff_path
}

sf_committed_readiness_path() {
    sf_wave_value readiness_metadata
}

sf_integration_queue_path() {
    sf_wave_value integration_queue
}

sf_mirror_handoff() {
    local lane="$1" path canonical
    path="$(sf_lane_path "$lane")"
    canonical="$(sf_repo_root)/$(sf_canonical_handoff_path "$lane")"
    [[ -f "$canonical" ]] || return 1
    python3 scripts/agent/sync_wave_handoffs.py --wave "$SF_WAVE_ID" --best-effort --task "$lane" --worktree "$path" >/dev/null
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
    local path="$1" top
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
