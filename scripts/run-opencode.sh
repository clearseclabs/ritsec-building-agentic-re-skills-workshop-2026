#!/usr/bin/env bash
# Load room inference, select a hosted MCP target, and start OpenCode.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

if [ ! -f .workshop.env ]; then
    echo "Room inference is not configured." >&2
    echo "Run: bash scripts/configure-workshop.sh" >&2
    exit 1
fi
if ! command -v opencode >/dev/null 2>&1; then
    echo "OpenCode is not installed or is not on PATH." >&2
    exit 1
fi

# Preserve an explicit per-run model override before the room environment loads its default.
requested_model="${WORKSHOP_MODEL:-}"
# shellcheck disable=SC1091
source .workshop.env
target="${1:-windows}"
shift || true
bash scripts/use-target.sh "$target"

model="${requested_model:-${WORKSHOP_MODEL:-agentic-re-skills/deepseek/deepseek-v4.1-flash-1017}}"
echo "Starting OpenCode with: $model"
exec opencode -m "$model" "$@"
