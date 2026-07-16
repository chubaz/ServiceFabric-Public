#!/usr/bin/env bash
set -euo pipefail

if [[ "${SF_AGENT_FAIL_RUNTIME_INIT:-}" == "${1:-}" || "${SF_AGENT_FAIL_RUNTIME_INIT:-}" == "1" ]]; then
    echo "Runtime initialization forced to fail for ${1:-unknown}" >&2
    exit 23
fi

LANE="${1:?Usage: init_worktree_runtime.sh LANE WORKTREE STATE_BASE WAVE_ID}"
WORKTREE="${2:?Usage: init_worktree_runtime.sh LANE WORKTREE STATE_BASE WAVE_ID}"
STATE_BASE="${3:?Usage: init_worktree_runtime.sh LANE WORKTREE STATE_BASE WAVE_ID}"
WAVE_ID="${4:?Usage: init_worktree_runtime.sh LANE WORKTREE STATE_BASE WAVE_ID}"

RUNTIME_ROOT="$STATE_BASE/$WAVE_ID/$LANE"
VENV="$RUNTIME_ROOT/.venv"
WORKSPACE="$RUNTIME_ROOT/workspace"
HOME_DIR="$RUNTIME_ROOT/home"
TMP_DIR="$RUNTIME_ROOT/tmp"
LOG_DIR="$WORKTREE/.agent-runs/$WAVE_ID/$LANE/logs"
RUN_DIR="$WORKTREE/.agent-runs/$WAVE_ID/$LANE"
WORKTREES_ENV_EXPORT=""
if [[ -n "${SF_AGENT_WORKTREES_ENV:-}" ]]; then
    WORKTREES_ENV_EXPORT="export SF_AGENT_WORKTREES_ENV=$(printf '%q' "$SF_AGENT_WORKTREES_ENV")"
fi

mkdir -p "$RUNTIME_ROOT" "$WORKSPACE" "$HOME_DIR" "$TMP_DIR" "$LOG_DIR" "$RUN_DIR"

if [[ "${SF_AGENT_SKIP_VENV:-}" == "1" ]]; then
    mkdir -p "$VENV/bin"
    : > "$VENV/pyvenv.cfg"
elif [[ ! -f "$VENV/bin/activate" ]]; then
    python3 -m venv "$VENV"
fi

if [[ "${SF_AGENT_SKIP_VENV:-}" != "1" ]]; then
    CONTRACTS="$WORKTREE/packages/servicefabric_contracts"
    GENERATED_APPLICATION_RUNTIME="$WORKTREE/5_core_services/fastapi_base/requirements/runtime.lock"
    "$VENV/bin/python" -m pip install --disable-pip-version-check --requirement "$CONTRACTS/requirements/test.lock"
    "$VENV/bin/python" -m pip install --disable-pip-version-check --requirement "$GENERATED_APPLICATION_RUNTIME"
    "$VENV/bin/python" -m pip install --disable-pip-version-check --no-build-isolation --no-deps --editable "$CONTRACTS"

    LOCAL_COMPOSITION_PACKAGES=(
        "packages/servicefabric_application_assembly"
        "packages/servicefabric_application_builder"
        "packages/servicefabric_application_generator"
        "packages/servicefabric_application_model"
        "packages/servicefabric_agent_guidance"
        "packages/servicefabric_artifacts"
        "packages/servicefabric_blueprints"
        "packages/servicefabric_capability_authoring"
        "packages/servicefabric_capability_runtime"
        "packages/servicefabric_capability_invocation"
        "packages/servicefabric_capability_model"
        "packages/servicefabric_capability_registry"
        "packages/servicefabric_http_operation_adapter"
        "packages/servicefabric_operation_model"
        "packages/servicefabric_builder"
        "packages/servicefabric_capsules"
        "packages/servicefabric_framework_kits"
        "packages/servicefabric_governance"
        "packages/servicefabric_mcp_projection"
        "packages/servicefabric_operations"
        "packages/servicefabric_process_runtime"
        "packages/servicefabric_resource_bindings"
        "packages/servicefabric_runtime"
        "packages/servicefabric_workspace"
        "services/application_dev_supervisor"
        "services/application_host"
        "services/capsule_host"
        "services/governance_operations"
        "services/mcp_gateway"
        "services/tool_runtime"
        "clients/python"
    )
    for package in "${LOCAL_COMPOSITION_PACKAGES[@]}"; do
        "$VENV/bin/python" -m pip install --disable-pip-version-check --no-build-isolation --no-deps --editable "$WORKTREE/$package"
    done
fi

cat > "$WORKTREE/.agent-runtime.env" <<EOF
export SF_AGENT_LANE="$(printf '%s' "$LANE")"
export SF_AGENT_WAVE_ID="$(printf '%s' "$WAVE_ID")"
export SF_AGENT_RUN_DIR="$(printf '%s' "$RUN_DIR")"
$WORKTREES_ENV_EXPORT
export SERVICEFABRIC_WORKSPACE="$(printf '%s' "$WORKSPACE")"
export SERVICEFABRIC_HOME="$(printf '%s' "$HOME_DIR")"
export TMPDIR="$(printf '%s' "$TMP_DIR")"
export VIRTUAL_ENV="$(printf '%s' "$VENV")"
export PATH="$(printf '%s' "$VENV")/bin:\$PATH"
EOF

printf '%s\n' "$WORKTREE/.agent-runtime.env"
