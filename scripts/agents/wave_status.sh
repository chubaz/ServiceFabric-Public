#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib_wave.sh
source "$SCRIPT_DIR/lib_wave.sh"

sf_load_config

BOOTSTRAP_SHA="unknown"
[[ -f "$(sf_bootstrap_path)" ]] && BOOTSTRAP_SHA="$(cat "$(sf_bootstrap_path)")"
CONTRACTS_STATUS="missing"
if [[ -f "$(sf_contracts_path)" ]] && grep -q '"contractsStatus": "frozen"' "$(sf_contracts_path)"; then
    CONTRACTS_STATUS="frozen"
fi

READY=1
CANDIDATES=0
COMMITTED_QUEUE="missing"
WAVE_COMPLETE=0
if [[ -f "$(sf_integration_queue_path)" ]]; then
    COMMITTED_QUEUE="$(python3 - <<'PY'
import json
with open("config/agent/waves/wave-1/integration-queue.json", encoding="utf-8") as handle:
    print(json.load(handle).get("overall", "missing"))
PY
)"
fi
if [[ "$COMMITTED_QUEUE" == "WAVE COMPLETE" ]] && python3 scripts/agent/wave_completion.py --wave "$(sf_manifest_wave_id)" >/dev/null 2>&1; then
    WAVE_COMPLETE=1
fi

printf '%-16s %-46s %-28s %-12s %-12s %-7s %-8s %-9s %-7s %-8s %-10s %-12s\n' \
    LANE WORKTREE BRANCH HEAD EXPECTED CLEAN RUNTIME PREFLIGHT PROMPT HANDOFF CANDIDATE QUEUE

for lane in $(sf_lanes); do
    path="$(sf_lane_path "$lane")"
    branch="invalid"
    head="invalid"
    clean="no"
    runtime="no"
    preflight="missing"
    prompt="missing"
    handoff="missing"
    candidate="none"
    queue="clear"

    if sf_is_valid_worktree "$path"; then
        branch="$(sf_branch "$path" 2>/dev/null || printf 'detached')"
        head="$(sf_head "$path" 2>/dev/null || printf 'unknown')"
        sf_is_clean "$path" && clean="yes" || clean="dirty"
        [[ -f "$(sf_runtime_env "$lane")" ]] && runtime="yes"
        [[ -f "$(sf_prompt_path "$lane")" ]] && prompt="ready"
        [[ -f "$(sf_readiness_path "$lane")" ]] && grep -q '"preflight": "pass"' "$(sf_readiness_path "$lane")" && preflight="pass"
        if [[ -f "$(sf_canonical_handoff_path "$lane")" ]]; then
            sf_mirror_handoff "$lane" || true
            handoff="present"
        fi
        if [[ "$WAVE_COMPLETE" != "1" && "$BOOTSTRAP_SHA" != "unknown" ]] && ! git -C "$path" merge-base --is-ancestor HEAD "$BOOTSTRAP_SHA" 2>/dev/null; then
            candidate="present"
            queue="pending"
            CANDIDATES=1
        fi
        [[ -f "$(sf_state_dir)/integration-queue/$lane.json" ]] && queue="queued"
    fi

    [[ "$lane" == "integration" ]] && queue="authority"
    if [[ "$WAVE_COMPLETE" == "1" && "$lane" != "integration" ]]; then
        queue="integrated"
        candidate="accepted"
    fi
    if [[ "$WAVE_COMPLETE" == "1" && "$lane" == "integration" ]]; then
        queue="complete"
        candidate="accepted"
    fi

    if [[ "$clean" != "yes" || "$runtime" != "yes" || "$preflight" != "pass" || "$prompt" != "ready" ]]; then
        READY=0
    fi

    printf '%-16s %-46s %-28s %-12s %-12s %-7s %-8s %-9s %-7s %-8s %-10s %-12s\n' \
        "$lane" "$path" "$branch" "${head:0:12}" "${BOOTSTRAP_SHA:0:12}" "$clean" "$runtime" "$preflight" "$prompt" "$handoff" "$candidate" "$queue"
done

echo
echo "contractsStatus: $CONTRACTS_STATUS"
if [[ "$CONTRACTS_STATUS" == "frozen" ]]; then
    if [[ "$WAVE_COMPLETE" == "1" ]]; then
        echo "integrationAgent: complete"
    else
        echo "integrationAgent: active"
    fi
fi

if [[ "$WAVE_COMPLETE" == "1" && "$READY" == "1" && "$CONTRACTS_STATUS" == "frozen" ]]; then
    OVERALL="WAVE COMPLETE"
elif [[ "$READY" != "1" ]]; then
    OVERALL="NOT READY"
elif [[ "$CANDIDATES" == "1" ]]; then
    OVERALL="INTEGRATION REQUIRED"
elif [[ "$CONTRACTS_STATUS" != "frozen" ]]; then
    OVERALL="READY FOR INTEGRATION AGENT"
else
    OVERALL="READY FOR SPECIALISTS"
    echo "specialistPrompts: ready"
fi

echo "OVERALL: $OVERALL"
