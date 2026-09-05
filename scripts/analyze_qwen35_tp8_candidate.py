#!/usr/bin/env python3
"""Compare a repeated TP8 candidate with the immutable repeated TP8 baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONCURRENCIES = ("1", "5", "8", "16")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--candidate-summary", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--target-speedup", type=float, default=2.0)
    parser.add_argument("--quality-tolerance", type=float, default=0.02)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    baseline = load(args.baseline_summary)
    candidate = load(args.candidate_summary)
    if set(baseline.get("cells", {})) != set(CONCURRENCIES):
        raise ValueError("baseline summary does not contain c1/c5/c8/c16")
    if set(candidate.get("cells", {})) != set(CONCURRENCIES):
        raise ValueError("candidate summary does not contain c1/c5/c8/c16")

    result = {
        "schema": "qwen35-query-rewrite-tp8-candidate-decision/v1",
        "candidate_id": args.candidate_id,
        "baseline_summary": str(args.baseline_summary),
        "candidate_summary": str(args.candidate_summary),
        "target_speedup": args.target_speedup,
        "quality_tolerance": args.quality_tolerance,
        "cells": {},
    }
    all_performance = True
    all_quality = True
    for concurrency in CONCURRENCIES:
        base = baseline["cells"][concurrency]
        cand = candidate["cells"][concurrency]
        ttft_speedup = base["ttft_p50_ms"] / cand["ttft_p50_ms"]
        tpot_speedup = base["tpot_p50_ms"] / cand["tpot_p50_ms"]
        quality_delta = (
            cand["normalized_character_similarity_mean"]
            - base["normalized_character_similarity_mean"]
        )
        performance_pass = (
            ttft_speedup >= args.target_speedup
            and tpot_speedup >= args.target_speedup
        )
        quality_pass = quality_delta >= -args.quality_tolerance
        all_performance &= performance_pass
        all_quality &= quality_pass
        result["cells"][concurrency] = {
            "baseline_ttft_p50_ms": base["ttft_p50_ms"],
            "candidate_ttft_p50_ms": cand["ttft_p50_ms"],
            "ttft_speedup": ttft_speedup,
            "baseline_tpot_p50_ms": base["tpot_p50_ms"],
            "candidate_tpot_p50_ms": cand["tpot_p50_ms"],
            "tpot_speedup": tpot_speedup,
            "quality_similarity_delta": quality_delta,
            "performance_pass": performance_pass,
            "quality_pass": quality_pass,
        }
    if not all_quality:
        result["decision"] = "hold-correctness"
        status = 3
    elif all_performance:
        result["decision"] = "promote-goal-achieved"
        status = 0
    else:
        result["decision"] = "iterate-performance"
        status = 2
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
