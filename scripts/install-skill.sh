#!/usr/bin/env bash
# Install a reviewed SKILL.md into this repository's OpenCode Skill directory.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
force=0

usage() {
    echo "Usage: bash scripts/install-skill.sh PATH/TO/SKILL.md [--force]" >&2
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    usage
    exit 2
fi

source_file="$1"
if [ "${2:-}" = "--force" ]; then
    force=1
elif [ -n "${2:-}" ]; then
    usage
    exit 2
fi

if [ ! -f "$source_file" ]; then
    echo "Skill file not found: $source_file" >&2
    exit 1
fi

IFS= read -r first_line < "$source_file" || true
if [ "$first_line" != "---" ]; then
    echo "SKILL.md must begin with YAML frontmatter." >&2
    exit 1
fi

skill_name="$({
    awk '
        NR == 1 { next }
        /^---[[:space:]]*$/ { exit }
        /^name:[[:space:]]*/ {
            sub(/^name:[[:space:]]*/, "")
            sub(/[[:space:]]*$/, "")
            print
            exit
        }
    ' "$source_file"
} || true)"

first_character="${skill_name%"${skill_name#?}"}"
last_character="${skill_name#"${skill_name%?}"}"
if [ "$first_character" = '"' ] && [ "$last_character" = '"' ]; then
    skill_name="${skill_name:1:${#skill_name}-2}"
elif [ "$first_character" = "'" ] && [ "$last_character" = "'" ]; then
    skill_name="${skill_name:1:${#skill_name}-2}"
fi

if [[ ! "$skill_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || [ "${#skill_name}" -gt 64 ]; then
    echo "Invalid or missing frontmatter name: ${skill_name:-<empty>}" >&2
    exit 1
fi

if ! awk '
    NR == 1 { next }
    /^---[[:space:]]*$/ { exit }
    /^description:[[:space:]]*[^[:space:]]/ { found = 1 }
    END { exit(found ? 0 : 1) }
' "$source_file"; then
    echo "SKILL.md needs a non-empty frontmatter description." >&2
    exit 1
fi

line_count="$(wc -l < "$source_file" | tr -d ' ')"
if [ "$line_count" -ge 500 ]; then
    echo "SKILL.md has $line_count lines; keep it below 500." >&2
    exit 1
fi
if ! grep -Eqi 'validat|verify|evidence|check' "$source_file"; then
    echo "SKILL.md needs an explicit validation or evidence gate." >&2
    exit 1
fi
if grep -q 'DeviceIoControl' "$source_file" && ! grep -q 'CreateFile' "$source_file"; then
    echo "The DeviceIoControl workflow is missing its required CreateFile harness step." >&2
    exit 1
fi

destination_dir="$repo_dir/.opencode/skills/$skill_name"
destination="$destination_dir/SKILL.md"
if [ -e "$destination" ] && [ "$force" -ne 1 ]; then
    echo "Skill already exists: $destination" >&2
    echo "Review the diff, then rerun with --force if replacement is intentional." >&2
    exit 1
fi

mkdir -p "$destination_dir"
cp "$source_file" "$destination"
source_dir="$(cd "$(dirname "$source_file")" && pwd)"
for bundle_dir in agents scripts references assets; do
    if [ -d "$source_dir/$bundle_dir" ]; then
        cp -R "$source_dir/$bundle_dir" "$destination_dir/"
    fi
done
chmod 644 "$destination"

echo "Installed Skill: $destination"
if command -v opencode >/dev/null 2>&1; then
    echo
    skill_debug_file="$(mktemp "${TMPDIR:-/tmp}/opencode-skills.XXXXXX.json")"
    trap 'rm -f "$skill_debug_file"' EXIT
    if opencode debug skill >"$skill_debug_file" 2>&1; then
        if grep -Fq "\"name\": \"$skill_name\"" "$skill_debug_file"; then
            echo "  [ok]   OpenCode discovered $skill_name"
        else
            echo "  [FAIL] OpenCode did not discover $skill_name" >&2
            echo "  Run: bash scripts/show-skill.sh $skill_name" >&2
            exit 1
        fi
    else
        echo "  [FAIL] opencode debug skill failed:" >&2
        sed -n '1,80p' "$skill_debug_file" >&2
        exit 1
    fi
else
    echo "OpenCode is not installed; run 'opencode debug skill' after installing it." >&2
fi
