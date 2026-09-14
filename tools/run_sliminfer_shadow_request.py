#!/usr/bin/env python3
"""Send one deterministic token-ID prompt to a SlimInfer canary service."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any
from urllib.request import Request, urlopen


def build_payload(
    model: str,
    *,
    prompt_tokens: int,
    token_id: int,
    max_tokens: int = 1,
) -> dict[str, Any]:
    if not model:
        raise ValueError("model must not be empty")
    if prompt_tokens <= 0 or max_tokens <= 0:
        raise ValueError("prompt_tokens and max_tokens must be positive")
    if token_id < 0:
        raise ValueError("token_id must be non-negative")
    return {
        "model": model,
        "prompt": [token_id] * prompt_tokens,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "seed": 0,
        "logprobs": 1,
        "stream": False,
    }


def canonical_response(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    usage = response.get("usage")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response must contain exactly one choice")
    if not isinstance(usage, dict):
        raise ValueError("response must contain usage")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ValueError("response choice must be an object")
    return {
        "text": choice.get("text"),
        "finish_reason": choice.get("finish_reason"),
        "stop_reason": choice.get("stop_reason"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def send_request(endpoint: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    encoded = json.dumps(payload, separators=(",", ":")).encode()
    request = Request(
        endpoint,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        status = response.status
    elapsed = time.monotonic() - started
    if status != 200:
        raise RuntimeError(f"request failed with HTTP status {status}")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("service response is not a JSON object")
    return {
        "response": parsed,
        "canonical_response": canonical_response(parsed),
        "elapsed_seconds": elapsed,
        "http_status": status,
        "request_sha256": sha256(encoded).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-tokens", type=int, default=13000)
    parser.add_argument("--token-id", type=int, default=100)
    parser.add_argument("--max-tokens", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")

    try:
        payload = build_payload(
            args.model,
            prompt_tokens=args.prompt_tokens,
            token_id=args.token_id,
            max_tokens=args.max_tokens,
        )
        result = send_request(args.endpoint, payload, args.timeout)
    except Exception as exc:
        parser.exit(2, f"FAILED: {exc}\n")

    record = {
        "schema": "sliminfer-shadow-request/v1",
        "endpoint": args.endpoint,
        "model": args.model,
        "prompt_tokens_requested": args.prompt_tokens,
        "token_id": args.token_id,
        "max_tokens": args.max_tokens,
        **result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record["canonical_response"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
