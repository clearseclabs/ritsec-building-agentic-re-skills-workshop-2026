#!/usr/bin/env bash
# Save the shared room inference code without placing it in shell history.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_dir/.workshop.env"
gateway_url="https://ritsec-agentic-re-skills.clearseclabs.com/llm/v1"
default_model="agentic-re-skills/deepseek/deepseek-v4.1-flash-1017"
api_model="deepseek/deepseek-v4.1-flash-1017"

if [ "${1:-}" != "--reset" ] && [ -f "$env_file" ]; then
    # shellcheck disable=SC1090
    source "$env_file"
fi

workshop_key="${LLM_GATEWAY_API_KEY:-}"
if [ -z "$workshop_key" ] || [ "${1:-}" = "--reset" ]; then
    read -r -s -p "Room inference access code: " workshop_key
    echo
fi

if [ -z "$workshop_key" ]; then
    echo "The room access code cannot be empty." >&2
    exit 1
fi
if [[ ! "$workshop_key" =~ ^[-A-Za-z0-9._~+/=]+$ ]]; then
    echo "The access code contains unexpected characters; ask an instructor for help." >&2
    exit 1
fi

umask 077
{
    printf 'export LLM_GATEWAY_BASE_URL=%s\n' "$gateway_url"
    printf 'export LLM_GATEWAY_API_KEY=%s\n' "$workshop_key"
    printf 'export WORKSHOP_MODEL=%s\n' "$default_model"
    printf 'export WORKSHOP_API_MODEL=%s\n' "$api_model"
} > "$env_file"
chmod 600 "$env_file"

echo "Saved .workshop.env (gitignored, mode 600)."
echo "Next: bash scripts/check-workshop.sh"
echo "Guided launch: bash scripts/run-opencode.sh windows"
echo "Manual launch: source .workshop.env && opencode"
