#!/usr/bin/env python3
"""Compare disabled and selection-shadow completion records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    if value.get("schema") != "sliminfer-shadow-request/v1":
        raise ValueError(f"{path} has an unexpected schema")
    return value


def compare_records(
    disabled: dict[str, Any], enabled: dict[str, Any]
) -> dict[str, Any]:
    request_fields = ("model", "prompt_tokens_requested", "token_id", "max_tokens")
    mismatched_request = [
        field for field in request_fields if disabled.get(field) != enabled.get(field)
    ]
    if mismatched_request:
        raise ValueError(f"request fields differ: {mismatched_request}")
    disabled_response = disabled.get("canonical_response")
    enabled_response = enabled.get("canonical_response")
    if not isinstance(disabled_response, dict) or not isinstance(enabled_response, dict):
        raise ValueError("both records must contain canonical_response")
    response_fields = (
        "text",
        "finish_reason",
        "stop_reason",
        "prompt_tokens",
        "completion_tokens",
    )
    mismatched_response = [
        field
        for field in response_fields
        if disabled_response.get(field) != enabled_response.get(field)
    ]
    if mismatched_response:
        raise ValueError(f"canonical response fields differ: {mismatched_response}")
    return {
        "schema": "sliminfer-shadow-output-parity/v1",
        "status": "passed",
        "request_sha256_equal": (
            disabled.get("request_sha256") == enabled.get("request_sha256")
        ),
        "compared_request_fields": list(request_fields),
        "compared_response_fields": list(response_fields),
        "canonical_response": disabled_response,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("disabled", type=Path)
    parser.add_argument("enabled", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f"output already exists: {args.output}")
    try:
        summary = compare_records(
            load_record(args.disabled),
            load_record(args.enabled),
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.exit(2, f"FAILED: {exc}\n")
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
