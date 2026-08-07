#!/usr/bin/env bash
# Show one discovered OpenCode Skill without piping the full registry through jq.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: bash scripts/show-skill.sh SKILL_NAME" >&2
    exit 2
fi

skill_name="$1"
if [[ ! "$skill_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "Invalid Skill name: $skill_name" >&2
    exit 2
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

if ! command -v opencode >/dev/null 2>&1; then
    echo "OpenCode is not installed." >&2
    exit 1
fi

skill_debug_file="$(mktemp "${TMPDIR:-/tmp}/opencode-skills.XXXXXX.json")"
trap 'rm -f "$skill_debug_file"' EXIT

if ! opencode debug skill >"$skill_debug_file" 2>&1; then
    echo "opencode debug skill failed:" >&2
    sed -n '1,80p' "$skill_debug_file" >&2
    exit 1
fi

python3 - "$skill_debug_file" "$skill_name" <<'PY'
import json
import sys

path, wanted = sys.argv[1:]
try:
    with open(path, encoding="utf-8") as handle:
        skills = json.load(handle)
except (OSError, json.JSONDecodeError) as exc:
    print(f"Could not read OpenCode Skill registry: {exc}", file=sys.stderr)
    raise SystemExit(1)

for skill in skills:
    if skill.get("name") == wanted:
        selected = {
            "name": skill.get("name"),
            "description": skill.get("description"),
            "location": skill.get("location"),
        }
        print(json.dumps(selected, indent=2))
        raise SystemExit(0)

print(f"OpenCode did not discover {wanted}", file=sys.stderr)
raise SystemExit(1)
PY
