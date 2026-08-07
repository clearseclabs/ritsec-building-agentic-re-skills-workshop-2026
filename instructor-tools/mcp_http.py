#!/usr/bin/env python3
"""Minimal standard-library client for the workshop's hosted MCP endpoint."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


class McpClient:
    def __init__(self, url: str, target: str | None = None, timeout: int = 90):
        self.url = url
        self.target = target
        self.timeout = timeout
        self.session_id: str | None = None
        self.next_id = 1

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": "RITSEC-Context-Demo/1.0",
        }
        if self.target:
            headers["X-MCP-Target"] = self.target
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        request = Request(
            self.url,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            headers=self._headers(),
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            session_id = response.headers.get("Mcp-Session-Id")
            if session_id:
                self.session_id = session_id
            body = response.read().decode("utf-8", errors="replace")

        messages = []
        for line in body.splitlines():
            if line.startswith("data:"):
                messages.append(json.loads(line[5:].strip()))
        if messages:
            return messages[-1]
        if body.strip():
            return json.loads(body)
        return None

    def connect(self) -> None:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self.next_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "ritsec-context-demo", "version": "1.0"},
                },
            }
        )
        self.next_id += 1
        if not response or "result" not in response:
            raise RuntimeError(f"MCP initialize failed: {response}")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if not self.session_id:
            self.connect()
        request_id = self.next_id
        self.next_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
        )
        if not response:
            raise RuntimeError(f"Empty MCP response for {method}")
        if "error" in response:
            raise RuntimeError(json.dumps(response["error"], indent=2))
        return response.get("result")

    def tools(self) -> list[dict[str, Any]]:
        result = self.request("tools/list")
        return result.get("tools", [])

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError(json.dumps(result.get("content", result), indent=2))
        if "structuredContent" in result:
            return result["structuredContent"]
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return result
