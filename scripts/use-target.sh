#!/usr/bin/env bash
# Select the hosted PyGhidra-MCP project exposed to OpenCode.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:-}"

case "$target" in
    windows|linux|dhcp|ksthunk) ;;
    *)
        echo "Usage: bash scripts/use-target.sh {windows|linux|dhcp|ksthunk}" >&2
        exit 2
        ;;
esac

mkdir -p "$repo_dir/.opencode"
cp "$repo_dir/setup/opencode.${target}.json" "$repo_dir/.opencode/opencode.json"
echo "OpenCode target: $target"
