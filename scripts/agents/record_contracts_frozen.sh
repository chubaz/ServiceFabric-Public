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

for required in \
    AGENTS.md \
    docs/workplans/waves/wave-1.md \
    config/agent/waves/wave-1.json \
    config/agent/waves/wave-1/tasks/assembly.json \
    config/agent/waves/wave-1/tasks/resources.json \
    config/agent/waves/wave-1/tasks/kits-blueprints.json \
    config/agent/waves/wave-1/tasks/testing.json \
    config/agent/waves/wave-1/tasks/integration.json
do
    [[ -f "$ROOT/$required" ]] || { echo "Missing required Wave-1 contract file: $required" >&2; exit 2; }
done

python3 - <<'PY'
import json
from pathlib import Path
wave = json.loads(Path("config/agent/waves/wave-1.json").read_text())
required_order = ["testing", "kits-blueprints", "resources", "assembly", "integration"]
if wave["integration_order"] != required_order:
    raise SystemExit("Unexpected integration order")
for lane in ["assembly", "resources", "kits-blueprints", "testing", "integration"]:
    task = json.loads(Path(f"config/agent/waves/wave-1/tasks/{lane}.json").read_text())
    if not task["allowed_paths"] or not task["required_tests"]:
        raise SystemExit(f"Incomplete task manifest: {lane}")
policies = wave.get("operational_policies", {})
required = {
    "ap00c_complete_not_specialist_lane": True,
    "automatic_merger": False,
    "background_branch_watcher": False,
    "candidate_commits_allowed": True,
    "contracts_freeze_required_before_specialists": True,
    "integration_agent_launches_first": True,
    "integration_authority_accepts_or_rejects": True,
    "runtime_state_isolated_per_worktree": True,
    "specialists_may_merge_or_pull_feature_branches": False,
}
for key, expected in required.items():
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
    "Wave-1 contracts",
    "task ownership",
    "specialist manifests",
    "verification commands",
    "integration order"
  ],
  "waveId": "$SF_WAVE_ID"
}
EOF

echo "contractsStatus: frozen"
