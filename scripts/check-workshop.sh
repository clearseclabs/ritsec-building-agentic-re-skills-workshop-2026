#!/usr/bin/env bash
# Verify the minimal supported OpenCode workshop path.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

failed=0
for tool in git curl opencode python3; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf '  [ok]   %s: %s\n' "$tool" "$(command -v "$tool")"
    else
        printf '  [FAIL] %s is not installed\n' "$tool"
        failed=1
    fi
done

if [ ! -f .workshop.env ]; then
    echo "  [FAIL] .workshop.env is missing; run: bash scripts/configure-inference.sh"
    failed=1
else
    # shellcheck disable=SC1091
    source .workshop.env
    if [ -n "${LLM_GATEWAY_API_KEY:-}" ]; then
        echo "  [ok]   room inference code is configured"
    else
        echo "  [FAIL] room inference code is empty"
        failed=1
    fi
fi

for profile in windows linux dhcp ksthunk; do
    if [ -f "setup/opencode.${profile}.json" ]; then
        printf '  [ok]   %s MCP profile is staged\n' "$profile"
    else
        printf '  [FAIL] %s MCP profile is missing\n' "$profile"
        failed=1
    fi
done

for demo_file in \
    scripts/configure-inference.sh \
    scripts/check-inference.py \
    scripts/install-skill.sh \
    scripts/show-skill.sh \
    scripts/create-skill.sh \
    scripts/create-skill.py \
    scripts/compare-kb-manifests.py \
    scripts/fetch-patch-pair.py \
    workflows/driver-ioctl-harness.txt \
    workflows/patch-tuesday-diffing.txt \
    resources/patch-tuesday-report.schema.json \
    resources/cve-2026-44815-dhcpcore.ghidriff.md \
    reference-skills/capture-session-skill/SKILL.md \
    instructor-tools/mcp_http.py \
    instructor-tools/focused_driver_cli.py \
    instructor-tools/measure_mcp_context.py; do
    if [ -f "$demo_file" ]; then
        printf '  [ok]   %s is staged\n' "$demo_file"
    else
        printf '  [FAIL] %s is missing\n' "$demo_file"
        failed=1
    fi
done

if [ "$failed" -ne 0 ]; then
    exit 1
fi

echo
if python3 scripts/check-inference.py --ping; then
    echo "  [ok]   hosted inference completed a bounded request"
else
    echo "  [FAIL] hosted inference check failed"
    exit 1
fi

if python3 instructor-tools/focused_driver_cli.py list-binaries >/dev/null; then
    echo "  [ok]   hosted Windows MCP returned the project inventory"
else
    echo "  [FAIL] hosted Windows MCP check failed"
    exit 1
fi

# shellcheck disable=SC1091
source .workshop.env
bash scripts/use-target.sh windows >/dev/null
mcp_status="$(opencode mcp list 2>&1)"
printf '%s\n' "$mcp_status"
if [[ "$mcp_status" == *"pyghidra-mcp-windows"* && "$mcp_status" == *"connected"* ]]; then
    echo "  [ok]   OpenCode reports the hosted Windows MCP as connected"
else
    echo "  [FAIL] OpenCode did not report the hosted Windows MCP as connected"
    exit 1
fi

echo
echo "Setup is ready. Stop here for the room check before starting OpenCode."
