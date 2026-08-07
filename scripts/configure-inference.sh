#!/usr/bin/env bash
# Entry point for configuring the RITSEC room inference code.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$repo_dir/scripts/configure-workshop.sh" "$@"
