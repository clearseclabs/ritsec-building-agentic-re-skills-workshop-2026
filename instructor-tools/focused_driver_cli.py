#!/usr/bin/env python3
"""Focused driver-RE CLI backed by the hosted RITSEC Windows MCP project."""

from __future__ import annotations

import argparse
import json

from mcp_http import McpClient

DEFAULT_URL = "https://ritsec-agentic-re-skills.clearseclabs.com/mcp"
DEFAULT_TARGET = "http://pyghidra-mcp-windows:8000/mcp"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run six focused driver-RE operations against the hosted workshop project."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help=argparse.SUPPRESS)
    parser.add_argument("--target", default=DEFAULT_TARGET, help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-binaries", help="List analyzed project binaries.")

    metadata = commands.add_parser("metadata", help="Show identity, architecture, and hashes.")
    metadata.add_argument("--binary", required=True)

    symbols = commands.add_parser("find-symbol", help="Search function symbols by regex.")
    symbols.add_argument("--binary", required=True)
    symbols.add_argument("--query", required=True)
    symbols.add_argument("--limit", type=int, default=25)
    symbols.add_argument("--all-symbols", action="store_true", help="Include labels and data symbols.")

    decompile = commands.add_parser("decompile", help="Decompile one function or address.")
    decompile.add_argument("--binary", required=True)
    decompile.add_argument("--target", required=True, action="append", dest="function_target")
    decompile.add_argument("--callees", action="store_true")
    decompile.add_argument("--xrefs", action="store_true")

    xrefs = commands.add_parser("xrefs", help="List references to a function or address.")
    xrefs.add_argument("--binary", required=True)
    xrefs.add_argument("--target", required=True, action="append", dest="function_target")

    raw = commands.add_parser("read-bytes", help="Read a bounded byte range at an address.")
    raw.add_argument("--binary", required=True)
    raw.add_argument("--address", required=True)
    raw.add_argument("--size", required=True, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    client = McpClient(args.url, args.target)

    if args.command == "list-binaries":
        result = client.call("list_project_binaries", {})
    elif args.command == "metadata":
        result = client.call("list_project_binary_metadata", {"binary_name": args.binary})
    elif args.command == "find-symbol":
        result = client.call(
            "search_symbols_by_name",
            {
                "binary_name": args.binary,
                "query": args.query,
                "functions_only": not args.all_symbols,
                "limit": args.limit,
            },
        )
    elif args.command == "decompile":
        targets = args.function_target
        result = client.call(
            "decompile_function",
            {
                "binary_name": args.binary,
                "name_or_address": targets[0] if len(targets) == 1 else targets,
                "include_callees": args.callees,
                "include_xrefs": args.xrefs,
            },
        )
    elif args.command == "xrefs":
        targets = args.function_target
        result = client.call(
            "list_xrefs",
            {
                "binary_name": args.binary,
                "name_or_address": targets[0] if len(targets) == 1 else targets,
            },
        )
    else:
        result = client.call(
            "read_bytes",
            {"binary_name": args.binary, "address": args.address, "size": args.size},
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
