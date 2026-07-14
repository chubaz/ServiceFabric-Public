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

mkdir -p "$RUNTIME_ROOT" "$WORKSPACE" "$HOME_DIR" "$TMP_DIR" "$LOG_DIR" "$RUN_DIR"

if [[ "${SF_AGENT_SKIP_VENV:-}" == "1" ]]; then
    mkdir -p "$VENV/bin"
    : > "$VENV/pyvenv.cfg"
elif [[ ! -f "$VENV/bin/activate" ]]; then
    python3 -m venv "$VENV"
fi

cat > "$WORKTREE/.agent-runtime.env" <<EOF
export SF_AGENT_LANE="$(printf '%s' "$LANE")"
export SF_AGENT_WAVE_ID="$(printf '%s' "$WAVE_ID")"
export SF_AGENT_RUN_DIR="$(printf '%s' "$RUN_DIR")"
export SERVICEFABRIC_WORKSPACE="$(printf '%s' "$WORKSPACE")"
export SERVICEFABRIC_HOME="$(printf '%s' "$HOME_DIR")"
export TMPDIR="$(printf '%s' "$TMP_DIR")"
export VIRTUAL_ENV="$(printf '%s' "$VENV")"
export PATH="$(printf '%s' "$VENV")/bin:\$PATH"
EOF

printf '%s\n' "$WORKTREE/.agent-runtime.env"
