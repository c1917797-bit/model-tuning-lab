#!/usr/bin/env python3
"""Validate and summarize the historical-ruler HYPIC reproduction."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARMS = ("no-cache", "hypic-only")
PERF_METRICS = (
    "ttft_mean_ms",
    "tpot_mean_ms",
    "output_tokens_per_second",
    "benchmark_duration_s",
)
QUALITY = {"longbenchv2": 127, "gsm8k": 1319}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def require_finite(value: Any, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{label}: expected finite value")
    return numeric


def perf_run(path: Path, arm: str, run_index: int) -> dict[str, Any]:
    data = load_json(path)
    config = data.get("config", {})
    expected = {
        "input_tokens": 32768,
        "prefix_tokens": 16384,
        "output_tokens": 1024,
        "requests": 40,
        "concurrency": 16,
        "warmup_requests": 2,
        "ignore_eos": True,
        "segment_ends": [16384, 32768],
    }
    for key, wanted in expected.items():
        if config.get(key) != wanted:
            raise ValueError(
                f"{path}: config {key}={config.get(key)!r}, expected {wanted!r}"
            )
    summary = data.get("summary", {})
    if (
        summary.get("requests") != 40
        or summary.get("successful") != 40
        or summary.get("failed") != 0
        or summary.get("fixed_output_verified") is not True
    ):
        raise ValueError(f"{path}: incomplete fixed-output performance run")
    if arm == "hypic-only" and run_index == 1:
        if summary.get("hot_path_verified") is not True:
            raise ValueError(f"{path}: HYPIC run1 did not pass the hot-path gate")
    metrics = {
        key: require_finite(summary.get(key), f"{path}:{key}")
        for key in PERF_METRICS
    }
    return {
        "path": str(path),
        "sha256": sha256(path),
        "metrics": metrics,
        "hot_path_verified": summary.get("hot_path_verified"),
        "hot_path_missing": summary.get("hot_path_missing", []),
    }


def quality_run(
    path: Path,
    dataset: str,
    quality_max_out_len: int,
) -> dict[str, Any]:
    data = load_json(path)
    samples = QUALITY[dataset]
    if (
        data.get("successful") != samples
        or data.get("failed") != 0
        or data.get("requests") != samples
        or data.get("max_out_len") != quality_max_out_len
        or data.get("ignore_eos") is not False
    ):
        raise ValueError(f"{path}: incomplete quality run")
    accuracy = require_finite(data.get("accuracy_pct"), f"{path}:accuracy_pct")
    return {
        "path": str(path),
        "sha256": sha256(path),
        "accuracy_pct": accuracy,
        "correct": int(data["correct"]),
        "successful": int(data["successful"]),
        "failed": int(data["failed"]),
        "details_sha256": data.get("details_sha256"),
        "data_sha256": data.get("data_sha256"),
        "evaluator_script_sha256": data.get("evaluator_script_sha256"),
        "max_out_len": int(data["max_out_len"]),
        "finish_reasons": data.get("finish_reasons", {}),
    }


def aggregate(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "population_stddev": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--quality-max-out-len", type=int, default=1024)
    args = parser.parse_args()
    tensor_parallel = int(os.environ.get("HYPIC_TP_SIZE", "4"))
    host_npu_first = int(os.environ.get("HYPIC_HOST_NPU_FIRST", "0"))
    host_npu_last = int(os.environ.get("HYPIC_HOST_NPU_LAST", "3"))
    host_npu_lane = f"NPU{host_npu_first}-{host_npu_last}"

    errors: list[str] = []
    performance: dict[str, list[dict[str, Any]]] = {}
    quality: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for arm in ARMS:
        performance[arm] = []
        for run_index in range(1, 4):
            path = args.root / arm / f"performance.run{run_index}.json"
            if not path.is_file():
                errors.append(f"missing {path}")
                continue
            try:
                performance[arm].append(perf_run(path, arm, run_index))
            except Exception as exc:
                errors.append(str(exc))

        quality[arm] = {}
        for dataset in QUALITY:
            quality[arm][dataset] = []
            for run_index in range(1, 4):
                path = (
                    args.root
                    / "quality"
                    / arm
                    / f"{dataset}.run{run_index}.summary.json"
                )
                if not path.is_file():
                    errors.append(f"missing {path}")
                    continue
                try:
                    quality[arm][dataset].append(
                        quality_run(path, dataset, args.quality_max_out_len)
                    )
                except Exception as exc:
                    errors.append(str(exc))

    perf_aggregate: dict[str, dict[str, dict[str, float]]] = {}
    for arm in ARMS:
        perf_aggregate[arm] = {}
        if len(performance[arm]) == 3:
            for metric in PERF_METRICS:
                perf_aggregate[arm][metric] = aggregate(
                    [item["metrics"][metric] for item in performance[arm]]
                )

    relative: dict[str, float] = {}
    if all(len(performance[arm]) == 3 for arm in ARMS):
        for metric in PERF_METRICS:
            baseline = perf_aggregate["no-cache"][metric]["mean"]
            treatment = perf_aggregate["hypic-only"][metric]["mean"]
            relative[metric] = (treatment / baseline - 1.0) * 100.0

    quality_aggregate: dict[str, dict[str, dict[str, float]]] = {
        arm: {} for arm in ARMS
    }
    quality_delta: dict[str, float] = {}
    for dataset in QUALITY:
        for arm in ARMS:
            if len(quality[arm][dataset]) == 3:
                quality_aggregate[arm][dataset] = aggregate(
                    [item["accuracy_pct"] for item in quality[arm][dataset]]
                )
        if all(dataset in quality_aggregate[arm] for arm in ARMS):
            quality_delta[dataset] = (
                quality_aggregate["hypic-only"][dataset]["mean"]
                - quality_aggregate["no-cache"][dataset]["mean"]
            )

    reference = load_json(args.reference)
    historical = reference["reported_measurements"]
    historical_change = {
        "ttft_mean_ms": float(historical["ttft_ms"]["reported_change_pct"]),
        "tpot_mean_ms": float(historical["tpot_ms"]["reported_change_pct"]),
        "output_tokens_per_second": float(
            historical["output_tokens_per_second"]["reported_change_pct"]
        ),
        "benchmark_duration_s": float(
            historical["batch_duration_s"]["reported_change_pct"]
        ),
    }
    direction_reproduced = bool(relative) and (
        relative["ttft_mean_ms"] < 0
        and relative["tpot_mean_ms"] < 0
        and relative["output_tokens_per_second"] > 0
        and relative["benchmark_duration_s"] < 0
    )

    complete = (
        all(len(performance[arm]) == 3 for arm in ARMS)
        and all(
            len(quality[arm][dataset]) == 3
            for arm in ARMS
            for dataset in QUALITY
        )
        and not errors
    )
    report = {
        "schema": "hypic-historical-reproduction-summary/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if complete else "in-progress",
        "scope": {
            "model": "Qwen3.6-27B",
            "tensor_parallel": tensor_parallel,
            "baseline": "no prefix cache, HYPIC off",
            "treatment": "no prefix cache, HYPIC on",
            "performance_shape": "32768 input / 16384 shared / 1024 output / 40 requests / concurrency 16",
            "quality_datasets": ["LongBench-v2", "GSM8K"],
            "quality_max_output_tokens": args.quality_max_out_len,
            "ceval": "operator-excluded",
            "niah_plus": "authoritative files absent",
        },
        "performance_runs": performance,
        "performance_aggregate": perf_aggregate,
        "relative_change_percent": relative,
        "historical_reported_change_percent": historical_change,
        "historical_direction_reproduced": direction_reproduced,
        "quality_runs": quality,
        "quality_aggregate": quality_aggregate,
        "quality_delta_percentage_points": quality_delta,
        "errors": errors,
        "interpretation": (
            "Complete same-denominator workload reproduction on Qwen3.6-27B TP4; "
            "do not claim identical absolute values to Qwen3.5-27B TP2."
            if complete
            else "Collection is incomplete; no final reproduction claim is authorized."
        ),
    }
    args.root.mkdir(parents=True, exist_ok=True)
    output_json = args.root / "historical-reproduction-summary.json"
    temporary = output_json.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(output_json)

    lines = [
        "# HYPIC Historical-Ruler Reproduction",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Current target: Qwen3.6-27B, TP{tensor_parallel}, host {host_npu_lane}.",
        "",
    ]
    if relative:
        lines.extend(
            [
                "## Performance",
                "",
                "| Metric | No-cache mean | HYPIC-only mean | Change | Historical change |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for metric in PERF_METRICS:
            base = perf_aggregate["no-cache"][metric]["mean"]
            treat = perf_aggregate["hypic-only"][metric]["mean"]
            lines.append(
                f"| {metric} | {base:.6f} | {treat:.6f} | "
                f"{relative[metric]:+.4f}% | {historical_change[metric]:+.4f}% |"
            )
        lines.extend(
            [
                "",
                f"Historical direction reproduced: **{direction_reproduced}**.",
                "",
            ]
        )
    if quality_delta:
        lines.extend(
            [
                "## Quality",
                "",
                "| Dataset | No-cache mean | HYPIC-only mean | Delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for dataset in QUALITY:
            if dataset not in quality_delta:
                continue
            lines.append(
                f"| {dataset} | "
                f"{quality_aggregate['no-cache'][dataset]['mean']:.6f}% | "
                f"{quality_aggregate['hypic-only'][dataset]['mean']:.6f}% | "
                f"{quality_delta[dataset]:+.6f} pp |"
            )
        lines.append("")
    if errors:
        lines.extend(["## Pending or invalid evidence", ""])
        lines.extend(f"- {item}" for item in errors)
        lines.append("")
    lines.append(
        "Absolute equality with the employee Qwen3.5-27B TP2 result is outside "
        "this operator-selected Qwen3.6-27B TP4 scope."
    )
    (args.root / "HISTORICAL_REPRODUCTION_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    if complete or args.allow_incomplete:
        print(json.dumps({"status": report["status"], "errors": len(errors)}))
        return 0
    for item in errors:
        print(item)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
