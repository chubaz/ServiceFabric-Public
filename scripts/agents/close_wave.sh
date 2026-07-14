#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/lib_wave.sh"
WAVE_ID=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --wave) WAVE_ID="${2:-}"; shift 2 ;;
        *) echo "Usage: close_wave.sh --wave WAVE_ID" >&2; exit 2 ;;
    esac
done
[[ -n "$WAVE_ID" ]] || { echo "--wave is required" >&2; exit 2; }
sf_load_config "$WAVE_ID"
[[ "$(pwd -P)" == "$(cd "$SF_WT_INTEGRATION" && pwd -P)" ]] || { echo "Run this command from the integration worktree: $SF_WT_INTEGRATION" >&2; exit 2; }
sf_is_clean "$SF_WT_INTEGRATION" || { echo "integration worktree is dirty" >&2; exit 2; }
status="$(scripts/agents/wave_status.sh --wave "$SF_WAVE_ID")"
printf '%s\n' "$status"
grep -q '^OVERALL: WAVE COMPLETE$' <<<"$status" || { echo "Wave is not complete" >&2; exit 2; }
for lane in $(sf_lanes); do
    [[ -f "$(sf_canonical_handoff_path "$lane")" ]] || { echo "$lane: missing canonical handoff" >&2; exit 2; }
    [[ -f "$(sf_readiness_path "$lane")" ]] && grep -q '"preflight": "pass"' "$(sf_readiness_path "$lane")" || { echo "$lane: missing passing readiness record" >&2; exit 2; }
done
make "verify-$SF_WAVE_ID"
git push -u origin "$(sf_lane_branch integration)"
branch="$(sf_lane_branch integration)"
printf '\nPR creation:\n  gh pr create --base main --head %q --fill\n' "$branch"
printf 'PR checks:\n  gh pr checks --watch\nThis script never merges a pull request.\n'
