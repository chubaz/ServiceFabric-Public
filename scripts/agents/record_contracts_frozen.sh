#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib_wave.sh
source "$SCRIPT_DIR/lib_wave.sh"

sf_load_config
ROOT="$(sf_repo_root)"
CURRENT_ROOT="$(pwd -P)"
EXPECTED_INTEGRATION="$(cd "$SF_WT_INTEGRATION" 2>/dev/null && pwd -P || true)"
[[ "$CURRENT_ROOT" == "$EXPECTED_INTEGRATION" ]] || {
    echo "Run this command from the integration worktree: $SF_WT_INTEGRATION" >&2
    exit 2
}

WAVE_BASE="$(sf_wave_base)"
git cat-file -e "${WAVE_BASE}^{commit}" >/dev/null 2>&1 || {
    echo "AP-00C base is not available: $WAVE_BASE" >&2
    exit 2
}

WAVE_MANIFEST="$(sf_manifest_wave_id)"
for required in \
    AGENTS.md \
    "docs/workplans/parallel/$SF_WAVE_ID/objective.md" \
    "docs/workplans/parallel/$SF_WAVE_ID/frozen-contracts.md" \
    "docs/workplans/parallel/$SF_WAVE_ID/integration-order.md" \
    "config/agent/waves/$WAVE_MANIFEST.json" \
    "config/agent/waves/$WAVE_MANIFEST/tasks/integration.json"
do
    [[ -f "$ROOT/$required" ]] || { echo "Missing required $SF_WAVE_ID contract file: $required" >&2; exit 2; }
done

python3 - <<'PY'
import json
from pathlib import Path
import os

wave_id = os.environ["SF_WAVE_ID"]
manifest = "wave-1" if wave_id == "wave-01" else wave_id
wave = json.loads(Path(f"config/agent/waves/{manifest}.json").read_text())
for lane in wave["integration_order"]:
    task_path = Path(f"config/agent/waves/{manifest}/tasks/{lane}.json")
    if not task_path.exists():
        raise SystemExit(f"Missing task manifest: {lane}")
    task = json.loads(task_path.read_text())
    if not task["allowed_paths"] or not task["required_tests"]:
        raise SystemExit(f"Incomplete task manifest: {lane}")
policies = wave.get("operational_policies", {})
required = {"automatic_merger": False, "candidate_commits_allowed": True,
            "contracts_freeze_required_before_specialists": True,
            "integration_agent_launches_first": True,
            "runtime_state_isolated_per_worktree": True,
            "specialists_may_merge_or_pull_feature_branches": False}
for key, expected in required.items():
    if policies.get(key) is not expected:
        raise SystemExit(f"Operational policy mismatch: {key}")
if wave_id == "wave-01":
    for key, expected in {"ap00c_complete_not_specialist_lane": True,
                          "background_branch_watcher": False,
                          "integration_authority_accepts_or_rejects": True}.items():
        if policies.get(key) is not expected:
            raise SystemExit(f"Operational policy mismatch: {key}")
    if policies.get("integration_gates") != ["midday", "end-of-day"]:
        raise SystemExit("Integration gates are not encoded")
PY

mkdir -p "$(sf_state_dir)"
cat > "$(sf_contracts_path)" <<EOF
{
  "ap00cBase": "$WAVE_BASE",
  "contractsStatus": "frozen",
  "integrationAgent": "active",
  "verified": [
    "AP-00C base",
    "$SF_WAVE_ID contracts",
    "task ownership",
    "specialist manifests",
    "verification commands",
    "integration order"
  ],
  "waveId": "$SF_WAVE_ID"
}
EOF

echo "contractsStatus: frozen"
