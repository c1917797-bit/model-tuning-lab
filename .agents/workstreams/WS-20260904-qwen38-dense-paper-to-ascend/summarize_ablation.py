#!/usr/bin/env python3
"""Validate a frozen G1-G4 result set and report three-run statistics."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


GROUPS = {
    "G1": {"native_optimization": False, "drrqr": False},
    "G2": {"native_optimization": True, "drrqr": False},
    "G3": {"native_optimization": False, "drrqr": True},
    "G4": {"native_optimization": True, "drrqr": True},
}
METRICS = ("ttft_ms", "tpot_ms", "ott_ms", "throughput_tps", "batch_delay_ms")
LOWER_IS_BETTER = {"ttft_ms", "tpot_ms", "ott_ms", "batch_delay_ms"}
GLOBAL_BINDING_FIELDS = (
    "frozen_inputs_sha256",
    "invariant_config_sha256",
    "treatment_matrix_sha256",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def mean_std(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def relative_improvement(metric: str, baseline: float, treatment: float) -> float:
    if baseline == 0:
        raise ValueError(f"baseline is zero for {metric}")
    if metric in LOWER_IS_BETTER:
        return 100.0 * (baseline - treatment) / baseline
    return 100.0 * (treatment - baseline) / baseline


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-repetitions", type=int, default=3)
    parser.add_argument("--expected-models", type=int, default=2)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.results)
    errors = []
    valid = []
    global_bindings: dict[str, set[str]] = {
        field: set() for field in GLOBAL_BINDING_FIELDS
    }
    repetitions: dict[tuple[str, str, str], set[int]] = defaultdict(set)
    cell_row_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    checkpoint_bindings: dict[tuple[str, str], set[str]] = defaultdict(set)
    service_config_bindings: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    service_instance_bindings: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for index, row in enumerate(rows, 1):
        group = row.get("group")
        if group not in GROUPS:
            errors.append(f"row {index}: unknown group {group!r}")
            continue
        for switch, expected in GROUPS[group].items():
            if row.get(switch) is not expected:
                errors.append(
                    f"row {index}: {group} requires {switch}={expected}"
                )
        if row.get("classification") != "warm":
            continue
        if row.get("model") is None or row.get("dataset") is None:
            errors.append(f"row {index}: warm row requires model and dataset")
            continue
        if not args.fixture_mode:
            if row.get("phase") != "performance":
                errors.append(f"row {index}: phase must be performance")
                continue
            evidence_hash_fields = (
                "checkpoint_manifest_sha256",
                "service_config_sha256",
            )
            malformed = [
                field
                for field in evidence_hash_fields
                if not SHA256_RE.fullmatch(str(row.get(field)))
            ]
            if malformed:
                errors.append(
                    f"row {index}: non-canonical evidence hashes: "
                    + ", ".join(malformed)
                )
                continue
            if not str(row.get("service_instance_id", "")).strip():
                errors.append(f"row {index}: service_instance_id is empty")
                continue
        try:
            run_index = int(row["run_index"])
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append(f"row {index}: run_index must be an integer")
            continue
        metrics_valid = True
        for metric in METRICS:
            try:
                value = float(row[metric])
            except (KeyError, TypeError, ValueError, OverflowError):
                errors.append(f"row {index}: {metric} must be present and numeric")
                metrics_valid = False
                continue
            if not math.isfinite(value):
                errors.append(f"row {index}: {metric} must be finite")
                metrics_valid = False
            elif metric == "throughput_tps" and value <= 0:
                errors.append(f"row {index}: throughput_tps must be positive")
                metrics_valid = False
            elif metric != "throughput_tps" and value < 0:
                errors.append(f"row {index}: {metric} must be non-negative")
                metrics_valid = False
        if not metrics_valid:
            continue
        for field in GLOBAL_BINDING_FIELDS:
            value = str(row.get(field))
            global_bindings[field].add(value)
            if not args.fixture_mode and not SHA256_RE.fullmatch(value):
                errors.append(
                    f"row {index}: {field} must be 64 lowercase hexadecimal characters"
                )
        key = (group, str(row.get("model")), str(row.get("dataset")))
        if not args.fixture_mode:
            checkpoint_bindings[(group, key[1])].add(
                str(row["checkpoint_manifest_sha256"])
            )
            service_config_bindings[key].add(str(row["service_config_sha256"]))
            service_instance_bindings[key].add(str(row["service_instance_id"]))
        repetitions[key].add(run_index)
        cell_row_counts[key] += 1
        valid.append(row)

    for field, values in global_bindings.items():
        if not args.fixture_mode and (len(values) != 1 or "None" in values):
            errors.append(f"all warm rows must share exactly one non-empty {field}")
    if not args.fixture_mode:
        for key, values in sorted(checkpoint_bindings.items()):
            if len(values) != 1:
                errors.append(
                    f"{key}: checkpoint_manifest_sha256 changed across rows"
                )
        for key, values in sorted(service_config_bindings.items()):
            if len(values) != 1:
                errors.append(f"{key}: service_config_sha256 changed across runs")
        for key, values in sorted(service_instance_bindings.items()):
            if len(values) != 1:
                errors.append(f"{key}: service_instance_id changed across runs")
    expected_runs = set(range(1, args.expected_repetitions + 1))
    for key, observed in sorted(repetitions.items()):
        if observed != expected_runs or cell_row_counts[key] != len(expected_runs):
            errors.append(
                f"{key}: repetitions {sorted(observed)} with "
                f"{cell_row_counts[key]} rows != {sorted(expected_runs)}"
            )

    by_cell: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        by_cell[(row["group"], str(row["model"]), str(row["dataset"]))].append(row)

    models = sorted({model for _, model, _ in by_cell})
    datasets = sorted({dataset for _, _, dataset in by_cell})
    if len(models) < args.expected_models:
        errors.append(
            f"model count {len(models)} is less than required {args.expected_models}"
        )
    for model in models:
        for dataset in datasets:
            for group in GROUPS:
                if (group, model, dataset) not in by_cell:
                    errors.append(f"missing cell: {(group, model, dataset)}")

    summary_cells = []
    baseline_means: dict[tuple[str, str, str], float] = {}
    for (group, model, dataset), cell_rows in sorted(by_cell.items()):
        metric_summary = {}
        for metric in METRICS:
            values = [
                float(row[metric])
                for row in cell_rows
                if row.get(metric) is not None
                and math.isfinite(float(row[metric]))
            ]
            if values:
                metric_summary[metric] = mean_std(values)
                if group == "G1":
                    baseline_means[(model, dataset, metric)] = metric_summary[metric]["mean"]
        quality_values = [
            float(row["quality_score"])
            for row in cell_rows
            if row.get("quality_score") is not None
        ]
        quality = mean_std(quality_values) if quality_values else None
        summary_cells.append(
            {
                "group": group,
                "model": model,
                "dataset": dataset,
                "runs": len(cell_rows),
                "metrics": metric_summary,
                "quality": quality,
            }
        )

    for cell in summary_cells:
        improvements = {}
        if cell["group"] != "G1":
            for metric, stats in cell["metrics"].items():
                key = (cell["model"], cell["dataset"], metric)
                if key in baseline_means:
                    improvements[metric] = relative_improvement(
                        metric, baseline_means[key], stats["mean"]
                    )
        cell["relative_improvement_percent_vs_G1"] = improvements

    report = {
        "schema": "paper-to-ascend-ablation-summary/v1",
        "valid": not errors,
        "errors": errors,
        "expected_repetitions": args.expected_repetitions,
        "expected_models": args.expected_models,
        "required_metrics": list(METRICS),
        "fixture_mode": args.fixture_mode,
        "global_bindings": {
            field: next(iter(values), None)
            for field, values in global_bindings.items()
        },
        "service_config_bindings": (
            {
                "|".join(key): next(iter(values), None)
                for key, values in sorted(service_config_bindings.items())
            }
            if not args.fixture_mode
            else None
        ),
        "checkpoint_manifest_bindings": (
            {
                "|".join(key): next(iter(values), None)
                for key, values in sorted(checkpoint_bindings.items())
            }
            if not args.fixture_mode
            else None
        ),
        "frozen_inputs_sha256": next(
            iter(global_bindings["frozen_inputs_sha256"]), None
        ),
        "cells": summary_cells,
        "quality_gate_note": (
            "This tool reports statistics; it does not declare accuracy lossless. "
            "Apply measured-noise, deterministic-canary, per-dataset and category gates."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_name(args.output.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
