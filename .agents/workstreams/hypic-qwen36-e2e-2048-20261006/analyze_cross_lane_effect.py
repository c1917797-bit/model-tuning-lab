#!/usr/bin/env python3
"""Read-only retrospective decomposition of HYPIC effects across NPU lanes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


PROTOCOL = {
    "input_tokens": 32768,
    "prefix_tokens": 16384,
    "output_tokens": 1024,
    "requests": 40,
    "concurrency": 16,
    "warmup_requests": 2,
    "ignore_eos": True,
    "segment_ends": [16384, 32768],
}
METRICS = (
    "ttft_mean_ms",
    "tpot_weighted_ms",
    "ttft_p95_ms",
    "tpot_p95_ms",
    "output_tokens_per_second",
    "benchmark_duration_s",
)


def read_run(root: Path, arm: str, index: int) -> tuple[dict, str]:
    path = root / arm / f"performance.run{index}.json"
    raw = path.read_bytes()
    record = json.loads(raw)
    config = record["config"]
    for key, expected in PROTOCOL.items():
        if config.get(key) != expected:
            raise ValueError(f"{path}: protocol drift in {key}")
    rows = record["results"]
    summary = record["summary"]
    if (
        len(rows) != 40
        or sorted(row.get("index") for row in rows) != list(range(40))
        or any(row.get("ok") is not True or row.get("output_tokens") != 1024 for row in rows)
        or summary.get("successful") != 40
        or summary.get("failed") != 0
        or summary.get("fixed_output_verified") is not True
    ):
        raise ValueError(f"{path}: incomplete fixed-output run")
    for key in METRICS:
        value = summary.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{path}: invalid {key}")
    return summary, hashlib.sha256(raw).hexdigest()


def summarize(root: Path, arms: tuple[str, ...]) -> dict:
    result = {"artifact_root": str(root.resolve()), "arms": {}}
    for arm in arms:
        runs = [read_run(root, arm, index) for index in (1, 2, 3)]
        result["arms"][arm] = {
            "sha256": [digest for _, digest in runs],
            "mean": {
                key: statistics.mean(row[key] for row, _ in runs) for key in METRICS
            },
            "per_run": {
                key: [row[key] for row, _ in runs] for key in METRICS
            },
        }
    return result


def saving(summary: dict, metric: str) -> float:
    base = summary["arms"]["no-cache"]["mean"][metric]
    treatment = summary["arms"]["hypic-only"]["mean"][metric]
    return base - treatment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--successful-root", required=True, type=Path)
    parser.add_argument("--current-root", required=True, type=Path)
    parser.add_argument("--earlier-baseline-root", required=True, type=Path)
    args = parser.parse_args()
    successful = summarize(args.successful_root, ("no-cache", "hypic-only"))
    current = summarize(args.current_root, ("no-cache", "hypic-only"))
    earlier = summarize(args.earlier_baseline_root, ("no-cache",))
    comparisons = {}
    for metric in ("ttft_mean_ms", "tpot_weighted_ms", "benchmark_duration_s"):
        old = saving(successful, metric)
        new = saving(current, metric)
        comparisons[metric] = {
            "successful_absolute_saving": old,
            "current_absolute_saving": new,
            "saving_difference_current_minus_successful": new - old,
            "baseline_penalty_current_minus_successful":
                current["arms"]["no-cache"]["mean"][metric]
                - successful["arms"]["no-cache"]["mean"][metric],
            "treatment_penalty_current_minus_successful":
                current["arms"]["hypic-only"]["mean"][metric]
                - successful["arms"]["hypic-only"]["mean"][metric],
        }
    result = {
        "schema": "hypic-cross-lane-effect-retrospective/v1",
        "status": "descriptive-not-a-preregistered-acceptance-gate",
        "successful_npu4_7": successful,
        "current_npu0_3": current,
        "earlier_npu0_3_baseline": earlier,
        "absolute_effect_comparison": comparisons,
        "interpretation_boundary": (
            "An observed common latency penalty is not proof of its hardware, "
            "HCCL, CPU/NUMA, or software root cause. Do not pool baselines, "
            "change the frozen service gate, or claim paired 2048 quality."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
