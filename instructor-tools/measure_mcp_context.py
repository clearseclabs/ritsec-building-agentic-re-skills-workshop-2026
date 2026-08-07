#!/usr/bin/env python3
"""Measure MCP and focused-CLI context surfaces for the workshop demo."""

from __future__ import annotations

import argparse
import json
import math

from focused_driver_cli import DEFAULT_TARGET, DEFAULT_URL, build_parser
from mcp_http import McpClient

FOCUSED_TOOLS = {
    "list_project_binaries",
    "list_project_binary_metadata",
    "search_symbols_by_name",
    "decompile_function",
    "list_xrefs",
    "read_bytes",
}


def count_tokens(text: str) -> tuple[int, str]:
    try:
        import tiktoken  # type: ignore

        return len(tiktoken.get_encoding("o200k_base").encode(text)), "tiktoken/o200k_base"
    except ImportError:
        return math.ceil(len(text.encode("utf-8")) / 4), "UTF-8 bytes / 4 estimate"


def openai_tools(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
            },
        }
        for tool in tools
    ]


def metric(label: str, value: object) -> dict[str, object]:
    text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"), sort_keys=True)
    tokens, method = count_tokens(text)
    return {
        "surface": label,
        "bytes": len(text.encode("utf-8")),
        "estimated_tokens": tokens,
        "token_method": method,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    args = parser.parse_args()

    client = McpClient(args.url, args.target)
    tools = client.tools()
    focused = [tool for tool in tools if tool.get("name") in FOCUSED_TOOLS]
    cli_help = build_parser().format_help()
    rows = [
        metric("MCP registry: full input + output schemas", tools),
        metric("Likely model request: all input tool definitions", openai_tools(tools)),
        metric("Likely model request: six focused MCP tools", openai_tools(focused)),
        metric("Focused CLI help exposed through Bash", cli_help),
    ]
    note = (
        "OpenCode may transform or lazily expose tools; these are serialized surface measurements, "
        "not a claim about hidden provider tokens. Tool results add further context during a session."
    )

    if args.json:
        print(
            json.dumps(
                {
                    "endpoint": args.url,
                    "tool_count": len(tools),
                    "focused_tool_count": len(focused),
                    "note": note,
                    "measurements": rows,
                },
                indent=2,
            )
        )
        return 0

    print(f"PyGhidra-MCP tools: {len(tools)} total; {len(focused)} in focused comparison")
    print()
    print(f"{'Surface':52} {'Bytes':>10} {'Est. tokens':>12}")
    print(f"{'-' * 52} {'-' * 10} {'-' * 12}")
    for row in rows:
        print(f"{row['surface'][:52]:52} {row['bytes']:10d} {row['estimated_tokens']:12d}")
    print()
    print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
