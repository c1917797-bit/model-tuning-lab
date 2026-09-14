#!/usr/bin/env python3
"""Describe first-token output drift for a semantic SlimInfer canary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_sliminfer_shadow_outputs import load_record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("disabled", type=Path)
    parser.add_argument("enabled", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    disabled = load_record(args.disabled)
    enabled = load_record(args.enabled)
    request_fields = ("model", "prompt_tokens_requested", "token_id", "max_tokens")
    mismatch = [
        field for field in request_fields if disabled.get(field) != enabled.get(field)
    ]
    if mismatch or disabled.get("request_sha256") != enabled.get("request_sha256"):
        parser.error(f"request identity differs: {mismatch}")
    left = disabled["canonical_response"]
    right = enabled["canonical_response"]
    fields = ("text", "tokens", "finish_reason", "stop_reason")
    differing = [field for field in fields if left.get(field) != right.get(field)]
    result = {
        "schema": "sliminfer-semantic-first-token-comparison/v1",
        "status": "observed",
        "request_sha256_equal": True,
        "outputs_equal": not differing,
        "differing_fields": differing,
        "disabled": left,
        "enabled": right,
        "note": (
            "Output equality is observational, not a pass condition: semantic "
            "pruning is expected to permit model-output drift."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
