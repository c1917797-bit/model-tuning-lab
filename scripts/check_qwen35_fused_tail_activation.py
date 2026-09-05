#!/usr/bin/env python3
"""Fail closed unless the live Qwen3.5 fused-tail graph is fully active."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SMALL_TRUE = (
    "Decode MMAR+Add+RMSNorm compile_range=(1, 16) "
    "applicable=True"
)
LARGE_FALSE = (
    "Decode MMAR+Add+RMSNorm compile_range=(17, 32768) "
    "applicable=False"
)


def check(
    log_path: Path,
    expected_ranks: int,
    expected_normalized: int,
    expected_fused: int,
) -> dict:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    normalized_line = (
        f"Normalized {expected_normalized} full-tensor MMAR attention copies"
    )
    fused_line = (
        f"Fused {expected_fused} decode MMAR+Add+RMSNorm patterns"
    )
    counts = {
        "small_range_applicable": text.count(SMALL_TRUE),
        "large_range_inapplicable": text.count(LARGE_FALSE),
        "expected_normalized_line": text.count(normalized_line),
        "expected_fused_line": text.count(fused_line),
    }
    passed = all(value == expected_ranks for value in counts.values())
    return {
        "schema": "qwen35-fused-tail-activation/v1",
        "passed": passed,
        "log_path": str(log_path),
        "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
        "expected": {
            "ranks": expected_ranks,
            "normalized_per_rank": expected_normalized,
            "fused_per_rank": expected_fused,
        },
        "counts": counts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-ranks", type=int, default=4)
    parser.add_argument("--expected-normalized", type=int, required=True)
    parser.add_argument("--expected-fused", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check(
        args.log,
        args.expected_ranks,
        args.expected_normalized,
        args.expected_fused,
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
