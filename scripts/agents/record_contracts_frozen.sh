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
[[ $# -eq 0 ]] || { echo "Usage: record_contracts_frozen.sh [--wave WAVE]" >&2; exit 2; }
sf_load_config "$WAVE_ID"

ROOT="$(sf_repo_root)"
CURRENT_ROOT="$(pwd -P)"
EXPECTED_INTEGRATION="$(cd "$SF_WT_INTEGRATION" 2>/dev/null && pwd -P || true)"
[[ "$CURRENT_ROOT" == "$EXPECTED_INTEGRATION" ]] || {
    echo "Run this command from the integration worktree: $SF_WT_INTEGRATION" >&2
    exit 2
}

WAVE_BASE="$(sf_wave_base)"
git cat-file -e "${WAVE_BASE}^{commit}" >/dev/null 2>&1 || {
    echo "Wave base is not available: $WAVE_BASE" >&2
    exit 2
}

SF_WAVE_ID="$SF_WAVE_ID" python3 - <<'PY'
from pathlib import Path
import os
from scripts.agent.wave_common import task, task_ids, wave

wave_id = os.environ["SF_WAVE_ID"]
value = wave(wave_id)
for required in ("base_commit", "frozen_contracts", "integration_order", "worktree_env"):
    if not value.get(required):
        raise SystemExit(f"Incomplete wave manifest: {required}")
named_contract_paths = {
    "ToolDefinition": Path("packages/servicefabric_contracts/src/servicefabric_contracts/tool_definition.py"),
}
for contract in value["frozen_contracts"]:
    path = named_contract_paths.get(contract, Path(contract))
    if not path.exists():
        raise SystemExit(f"Missing frozen contract path: {contract}")
for lane in task_ids(wave_id):
    entry = task(lane, wave_id)
    if not entry["allowed_paths"] or not entry["required_tests"] or not entry["handoff_path"]:
        raise SystemExit(f"Incomplete task manifest: {lane}")
policies = value.get("operational_policies", {})
for key, expected in {
    "candidate_commits_allowed": True,
    "contracts_freeze_required_before_specialists": True,
    "automatic_merger": False,
    "specialists_may_merge_or_pull_feature_branches": False,
}.items():
    if policies.get(key) is not expected:
        raise SystemExit(f"Operational policy mismatch: {key}")
PY

mkdir -p "$(sf_state_dir)"
cat > "$(sf_contracts_path)" <<EOF
{
  "waveBase": "$WAVE_BASE",
  "contractsStatus": "frozen",
  "integrationAgent": "active",
  "verified": ["wave base", "frozen contracts", "task ownership", "specialist manifests", "verification commands", "integration order"],
  "waveId": "$SF_WAVE_ID"
}
EOF

echo "contractsStatus: frozen"
