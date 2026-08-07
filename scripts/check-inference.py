#!/usr/bin/env python3
"""Verify the RITSEC room inference catalog and make an optional bounded request."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://ritsec-agentic-re-skills.clearseclabs.com/llm/v1"
DEFAULT_API_MODEL = "deepseek/deepseek-v4.1-flash-1017"
WORKSHOP_MODELS = (
    "deepseek/deepseek-v4.1-flash-1017",
    "qwen/qwen3.7-flash",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "minimax/minimax-m3.1-flash",
)


def load_workshop_env() -> None:
    path = REPO_DIR / ".workshop.env"
    if not path.is_file():
        return
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        key, separator, value = line.partition("=")
        if separator and key:
            os.environ.setdefault(key, value)


def request_json(url: str, key: str, *, payload: dict | None = None) -> dict:
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "RITSEC-Inference-Check/1.0",
    }
    data = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
        method = "POST"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ping", action="store_true", help="Make one small chat-completion request.")
    args = parser.parse_args()

    load_workshop_env()
    base_url = os.environ.get("LLM_GATEWAY_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    key = os.environ.get("LLM_GATEWAY_API_KEY", "")
    api_model = os.environ.get("WORKSHOP_API_MODEL", DEFAULT_API_MODEL)

    if not key:
        print("Missing room inference code.", file=sys.stderr)
        print("Run: bash scripts/configure-inference.sh", file=sys.stderr)
        return 1

    try:
        catalog = request_json(f"{base_url}/models", key)
    except RuntimeError as exc:
        print(f"Inference catalog check failed: {exc}", file=sys.stderr)
        return 1

    available = sorted(item.get("id", "") for item in catalog.get("data", []))
    print(f"Inference endpoint: {base_url}")
    print("Configured workshop models:")
    for model in WORKSHOP_MODELS:
        print(f"  - {model}: {'available' if model in available else 'MISSING'}")

    if api_model not in available:
        print(f"Selected model is unavailable: {api_model}", file=sys.stderr)
        return 1
    print(f"Selected for guided exercises: {api_model}")

    if args.ping:
        try:
            response = request_json(
                f"{base_url}/chat/completions",
                key,
                payload={
                    "model": api_model,
                    "messages": [{"role": "user", "content": "Reply with exactly: AGENT_SKILLS_READY"}],
                    "temperature": 0,
                    # Reasoning models may consume a small budget before visible content.
                    "max_tokens": 512,
                },
            )
            reply = (response.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        except (RuntimeError, IndexError, AttributeError) as exc:
            print(f"Inference ping failed: {exc}", file=sys.stderr)
            return 1
        if not reply:
            print("Inference ping returned no visible content.", file=sys.stderr)
            return 1
        print(f"Inference reply: {reply[:200]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
