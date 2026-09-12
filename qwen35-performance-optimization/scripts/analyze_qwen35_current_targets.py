#!/usr/bin/env python3
"""Decide the current Qwen3.5 P95 targets from paired three-repeat matrices."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


CONCURRENCIES = (1, 5, 8, 16)
REPETITIONS = (1, 2, 3)
IDENTITY_KEYS = (
    "model",
    "dataset_sha256",
    "requests",
    "max_tokens",
    "seed",
    "natural_eos",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_path(root: Path, concurrency: int, repetition: int) -> Path:
    native = root / f"c{concurrency}" / f"repeat-{repetition}.json"
    legacy = root / f"c{concurrency}-r{repetition}.json"
    if native.exists() or not legacy.exists():
        return native
    return legacy


def load_cell(path: Path, concurrency: int, repetition: int) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "concurrency": concurrency,
        "repeat_index": repetition,
        "requests": 32,
        "completed": 32,
        "errors": 0,
        "finish_reasons": {"stop": 32},
        "natural_eos": True,
        "prefix_cache_isolation": True,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {payload.get(key)!r}"
            )
    hashes = payload.get("response_sha256")
    if not isinstance(hashes, list) or len(hashes) != 32:
        raise ValueError(f"{path}: response_sha256 must contain 32 entries")
    cache_salt_prefix = payload.get("cache_salt_prefix")
    if not isinstance(cache_salt_prefix, str) or not cache_salt_prefix:
        raise ValueError(f"{path}: non-empty cache_salt_prefix is required")
    for metric in ("ttft_ms", "tpot_ms"):
        for percentile in ("p50", "p95", "p99"):
            value = payload.get(metric, {}).get(percentile)
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{path}: invalid {metric}.{percentile}")
    return payload


def identity(payload: dict) -> dict:
    return {key: payload.get(key) for key in IDENTITY_KEYS}


def ratio(candidate: float, baseline: float) -> float:
    if baseline <= 0:
        raise ValueError("baseline latency must be positive")
    return candidate / baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--ttft-target-ratio", type=float, default=0.80)
    parser.add_argument("--tpot-target-ratio", type=float, default=0.90)
    parser.add_argument(
        "--p99-risk-ratio",
        type=float,
        default=1.10,
        help="report, but do not silently promote, repeatable P99 tail growth",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for name, value in (
        ("ttft target ratio", args.ttft_target_ratio),
        ("tpot target ratio", args.tpot_target_ratio),
        ("P99 risk ratio", args.p99_risk_ratio),
    ):
        if not 0 < value:
            raise ValueError(f"{name} must be positive")
    if args.ttft_target_ratio > 1 or args.tpot_target_ratio > 1:
        raise ValueError("P95 target ratios must be at most one")

    cells = {}
    artifacts = {}
    reference_identity = None
    performance_pass = True
    tail_risk_clear = True
    for concurrency in CONCURRENCIES:
        baseline_rows = []
        candidate_rows = []
        repeat_hash_mismatches = []
        for repetition in REPETITIONS:
            baseline_path = cell_path(args.baseline_dir, concurrency, repetition)
            candidate_path = cell_path(args.candidate_dir, concurrency, repetition)
            baseline = load_cell(baseline_path, concurrency, repetition)
            candidate = load_cell(candidate_path, concurrency, repetition)
            if identity(baseline) != identity(candidate):
                raise ValueError(
                    f"c{concurrency}-r{repetition}: paired identity mismatch"
                )
            if reference_identity is None:
                reference_identity = identity(baseline)
            elif identity(baseline) != reference_identity:
                raise ValueError(
                    f"c{concurrency}-r{repetition}: matrix identity drift"
                )
            baseline_rows.append(baseline)
            candidate_rows.append(candidate)
            repeat_hash_mismatches.append(
                sum(
                    left != right
                    for left, right in zip(
                        baseline["response_sha256"],
                        candidate["response_sha256"],
                    )
                )
            )
            artifacts[
                f"baseline/c{concurrency}/repeat-{repetition}.json"
            ] = sha256(baseline_path)
            artifacts[
                f"candidate/c{concurrency}/repeat-{repetition}.json"
            ] = sha256(candidate_path)

        def aggregate(rows: list[dict], metric: str, percentile: str) -> float:
            return statistics.median(
                float(row[metric][percentile]) for row in rows
            )

        base_ttft = aggregate(baseline_rows, "ttft_ms", "p95")
        cand_ttft = aggregate(candidate_rows, "ttft_ms", "p95")
        base_tpot = aggregate(baseline_rows, "tpot_ms", "p95")
        cand_tpot = aggregate(candidate_rows, "tpot_ms", "p95")
        ttft_ratio = ratio(cand_ttft, base_ttft)
        tpot_ratio = ratio(cand_tpot, base_tpot)
        cell_pass = (
            ttft_ratio <= args.ttft_target_ratio
            and tpot_ratio <= args.tpot_target_ratio
        )
        performance_pass = performance_pass and cell_pass

        base_ttft_p99 = aggregate(baseline_rows, "ttft_ms", "p99")
        cand_ttft_p99 = aggregate(candidate_rows, "ttft_ms", "p99")
        base_tpot_p99 = aggregate(baseline_rows, "tpot_ms", "p99")
        cand_tpot_p99 = aggregate(candidate_rows, "tpot_ms", "p99")
        ttft_p99_ratio = ratio(cand_ttft_p99, base_ttft_p99)
        tpot_p99_ratio = ratio(cand_tpot_p99, base_tpot_p99)
        cell_tail_risk_clear = (
            ttft_p99_ratio <= args.p99_risk_ratio
            and tpot_p99_ratio <= args.p99_risk_ratio
        )
        tail_risk_clear = tail_risk_clear and cell_tail_risk_clear

        cells[str(concurrency)] = {
            "baseline_median_ttft_p95_ms": base_ttft,
            "candidate_median_ttft_p95_ms": cand_ttft,
            "ttft_p95_ratio": ttft_ratio,
            "ttft_p95_reduction_fraction": 1.0 - ttft_ratio,
            "ttft_p95_speedup": 1.0 / ttft_ratio,
            "baseline_median_tpot_p95_ms": base_tpot,
            "candidate_median_tpot_p95_ms": cand_tpot,
            "tpot_p95_ratio": tpot_ratio,
            "tpot_p95_reduction_fraction": 1.0 - tpot_ratio,
            "tpot_p95_speedup": 1.0 / tpot_ratio,
            "performance_target_met": cell_pass,
            "baseline_median_ttft_p99_ms": base_ttft_p99,
            "candidate_median_ttft_p99_ms": cand_ttft_p99,
            "ttft_p99_ratio": ttft_p99_ratio,
            "baseline_median_tpot_p99_ms": base_tpot_p99,
            "candidate_median_tpot_p99_ms": cand_tpot_p99,
            "tpot_p99_ratio": tpot_p99_ratio,
            "p99_tail_risk_clear": cell_tail_risk_clear,
            "paired_response_hash_mismatches_by_repeat": repeat_hash_mismatches,
        }

    report = {
        "schema": "qwen35-current-p95-acceptance/v1",
        "candidate_id": args.candidate_id,
        "comparison": "fresh same-environment MTP-off control versus candidate",
        "identity": reference_identity,
        "repetitions": 3,
        "aggregation": "median of three per-run percentile values",
        "thresholds": {
            "ttft_p95_candidate_over_baseline_max": args.ttft_target_ratio,
            "tpot_p95_candidate_over_baseline_max": args.tpot_target_ratio,
            "p99_diagnostic_risk_ratio": args.p99_risk_ratio,
        },
        "performance_target_met": performance_pass,
        "p99_tail_risk_clear": tail_risk_clear,
        "quality_gate_required_separately": True,
        "cells": cells,
        "artifact_sha256": artifacts,
        "decision": (
            "performance-target-met-await-quality"
            if performance_pass
            else "iterate"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if performance_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
