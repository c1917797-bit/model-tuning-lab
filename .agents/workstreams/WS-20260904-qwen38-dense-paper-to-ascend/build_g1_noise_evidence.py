#!/usr/bin/env python3
"""Build reproducible condition-B noise evidence from warm G1 quality rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


EXPECTED_DATASETS = {"NIAH+", "LongBench v2", "GSM8K", "CEval"}
BINDING_FIELDS = (
    "frozen_inputs_sha256",
    "invariant_config_sha256",
    "treatment_matrix_sha256",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: row must be an object")
            rows.append(value)
    return rows


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-repetitions", type=int, default=3)
    parser.add_argument("--minimum-models", type=int, default=2)
    args = parser.parse_args()
    if args.expected_repetitions != 3:
        raise ValueError("production noise evidence requires exactly 3 repetitions")
    if args.minimum_models < 2:
        raise ValueError("--minimum-models must be at least 2")
    if not args.quality_results.is_file():
        raise ValueError("--quality-results must be an existing regular file")

    errors = []
    cells: dict[tuple[str, str], list[tuple[int, float]]] = defaultdict(list)
    bindings: dict[str, set[str]] = {field: set() for field in BINDING_FIELDS}
    for index, row in enumerate(read_jsonl(args.quality_results), 1):
        if row.get("classification") != "warm" or row.get("group") != "G1":
            continue
        try:
            model = str(row["model"])
            dataset = str(row["dataset"])
            run_index = int(row["run_index"])
            score = float(row["quality_score"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            errors.append(f"row {index}: invalid G1 identity/score: {exc}")
            continue
        if not model or not dataset or not math.isfinite(score):
            errors.append(f"row {index}: model/dataset/quality_score is invalid")
            continue
        malformed = []
        for field in BINDING_FIELDS:
            value = str(row.get(field))
            bindings[field].add(value)
            if not SHA256_RE.fullmatch(value):
                malformed.append(field)
        if malformed:
            errors.append(
                f"row {index}: non-canonical binding hashes: {', '.join(malformed)}"
            )
            continue
        cells[(model, dataset)].append((run_index, score))

    models = {model for model, _ in cells}
    datasets = {dataset for _, dataset in cells}
    if len(models) < args.minimum_models:
        errors.append(
            f"G1 noise evidence requires at least {args.minimum_models} models"
        )
    if datasets != EXPECTED_DATASETS:
        errors.append(
            f"G1 datasets must be exactly {sorted(EXPECTED_DATASETS)}; "
            f"observed={sorted(datasets)}"
        )
    expected_scope = {
        (model, dataset) for model in models for dataset in EXPECTED_DATASETS
    }
    if set(cells) != expected_scope:
        errors.append("G1 model/dataset matrix is incomplete")
    for field, values in bindings.items():
        if len(values) != 1:
            errors.append(f"G1 rows must share exactly one {field}")

    expected_runs = set(range(1, args.expected_repetitions + 1))
    observations = []
    ranges = []
    for key, values in sorted(cells.items()):
        runs = [run for run, _ in values]
        scores = [score for _, score in values]
        if set(runs) != expected_runs or len(values) != len(expected_runs):
            errors.append(
                f"{key}: repetitions {sorted(set(runs))} with {len(values)} "
                f"rows != {sorted(expected_runs)}"
            )
            continue
        ranges.append(max(scores) - min(scores))
        for run_index, score in sorted(values):
            observations.append(
                {
                    "group": "G1",
                    "model": key[0],
                    "dataset": key[1],
                    "run_index": run_index,
                    "quality_score": score,
                }
            )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    report = {
        "schema": "paper-to-ascend-g1-noise/v1",
        "fixture_only": False,
        "method": "max_within_cell_range_pp",
        "expected_repetitions": args.expected_repetitions,
        "noise_threshold_pp": max(ranges),
        "source_quality_results": str(args.quality_results.resolve()),
        "source_quality_results_sha256": file_sha256(args.quality_results),
        "global_bindings": {
            field: next(iter(values)) for field, values in bindings.items()
        },
        "observations": observations,
    }
    atomic_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
