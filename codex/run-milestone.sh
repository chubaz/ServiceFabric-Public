#!/usr/bin/env bash
set -euo pipefail

PROMPT_FILE="${1:?Usage: codex/run-milestone.sh PROMPT_FILE}"
REPOSITORY="${2:-$(pwd)}"

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Prompt file not found: $PROMPT_FILE" >&2
    exit 2
fi

NAME="$(basename "$PROMPT_FILE" .md)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$REPOSITORY/codex/logs/${STAMP}-${NAME}.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "Repository: $REPOSITORY"
echo "Prompt:     $PROMPT_FILE"
echo "Log:        $LOG_FILE"

codex exec \
    -C "$REPOSITORY" \
    --sandbox workspace-write \
    - < "$PROMPT_FILE" 2>&1 | tee "$LOG_FILE"