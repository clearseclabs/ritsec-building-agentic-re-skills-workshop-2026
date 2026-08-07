#!/usr/bin/env bash
# Generate and install a Skill from a captured-workflow text file.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required." >&2
    exit 1
fi

exec python3 scripts/create-skill.py "$@"
