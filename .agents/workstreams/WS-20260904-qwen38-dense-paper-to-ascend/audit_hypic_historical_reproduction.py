#!/usr/bin/env python3
"""Independent fail-closed audit for the 18-unit HYPIC reproduction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARMS = ("no-cache", "hypic-only")
QUALITY = {"longbenchv2": 127, "gsm8k": 1319}
PERF_CONFIG = {
    "input_tokens": 32768,
    "prefix_tokens": 16384,
    "output_tokens": 1024,
    "requests": 40,
    "concurrency": 16,
    "warmup_requests": 2,
    "ignore_eos": True,
    "segment_ends": [16384, 32768],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def audit_performance(
    root: Path,
    aggregate: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    checked: list[dict[str, Any]] = []
    expected_hashes = {
        item["path"]: item["sha256"]
        for arm in ARMS
        for item in aggregate["performance_runs"][arm]
    }
    for arm in ARMS:
        for run in range(1, 4):
            path = root / arm / f"performance.run{run}.json"
            try:
                payload = load_object(path)
                for key, expected in PERF_CONFIG.items():
                    if payload.get("config", {}).get(key) != expected:
                        errors.append(
                            f"{path}: config {key} does not match frozen ruler"
                        )
                results = payload.get("results")
                if not isinstance(results, list) or len(results) != 40:
                    errors.append(f"{path}: expected 40 measured results")
                    results = []
                indexes = {item.get("index") for item in results if isinstance(item, dict)}
                if indexes != set(range(40)):
                    errors.append(f"{path}: result indexes are not exactly 0..39")
                if any(
                    item.get("ok") is not True
                    or item.get("error") is not None
                    or item.get("output_tokens") != 1024
                    or item.get("finish_reason") != "length"
                    for item in results
                    if isinstance(item, dict)
                ):
                    errors.append(f"{path}: a measured request is not fixed-output success")
                summary = payload.get("summary", {})
                required = {
                    "requests": 40,
                    "successful": 40,
                    "failed": 0,
                    "fixed_output_requests": 40,
                    "fixed_output_verified": True,
                }
                for key, expected in required.items():
                    if summary.get(key) != expected:
                        errors.append(f"{path}: summary {key} != {expected!r}")
                if arm == "hypic-only" and run == 1:
                    if summary.get("hot_path_verified") is not True:
                        errors.append(f"{path}: strict HYPIC hot-path gate is false")
                    if summary.get("hot_path_missing") != []:
                        errors.append(f"{path}: HYPIC hot-path evidence is incomplete")
                    if summary.get("evidence_failures") != []:
                        errors.append(f"{path}: HYPIC evidence failures are present")
                actual_hash = sha256(path)
                if expected_hashes.get(str(path)) != actual_hash:
                    errors.append(f"{path}: aggregate performance hash mismatch")
                checked.append(
                    {
                        "kind": "performance",
                        "arm": arm,
                        "run": run,
                        "path": str(path),
                        "sha256": actual_hash,
                        "requests": len(results),
                    }
                )
            except Exception as exc:
                errors.append(f"{path}: {exc}")
    return checked


def audit_quality(
    root: Path,
    aggregate: dict[str, Any],
    errors: list[str],
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    checked: list[dict[str, Any]] = []
    data_hashes: set[str] = set()
    evaluator_hashes: set[str] = set()
    expected_summary_hashes = {
        item["path"]: item["sha256"]
        for arm in ARMS
        for dataset in QUALITY
        for item in aggregate["quality_runs"][arm][dataset]
    }
    for arm in ARMS:
        for dataset, expected_count in QUALITY.items():
            for run in range(1, 4):
                stem = root / "quality" / arm / f"{dataset}.run{run}"
                summary_path = Path(f"{stem}.summary.json")
                details_path = Path(f"{stem}.jsonl")
                try:
                    summary = load_object(summary_path)
                    required = {
                        "requests": expected_count,
                        "successful": expected_count,
                        "failed": 0,
                        "unique_response_sha256": expected_count,
                    }
                    for key, expected in required.items():
                        if summary.get(key) != expected:
                            errors.append(
                                f"{summary_path}: {key} != {expected!r}"
                            )
                    rows: list[dict[str, Any]] = []
                    with details_path.open("r", encoding="utf-8") as stream:
                        for line_number, line in enumerate(stream, 1):
                            if not line.strip():
                                raise ValueError(f"blank line {line_number}")
                            row = json.loads(line)
                            if not isinstance(row, dict):
                                raise ValueError(f"line {line_number} is not an object")
                            rows.append(row)
                    if len(rows) != expected_count:
                        errors.append(
                            f"{details_path}: {len(rows)} rows != {expected_count}"
                        )
                    indexes = {row.get("index") for row in rows}
                    if indexes != set(range(expected_count)):
                        errors.append(f"{details_path}: indexes are not complete and unique")
                    if any(
                        row.get("ok") is not True or row.get("error") is not None
                        for row in rows
                    ):
                        errors.append(f"{details_path}: failed result row present")
                    response_hashes = [row.get("response_sha256") for row in rows]
                    if any(
                        not isinstance(value, str) or len(value) != 64
                        for value in response_hashes
                    ):
                        errors.append(f"{details_path}: invalid response SHA256")
                    if len(set(response_hashes)) != expected_count:
                        errors.append(f"{details_path}: response SHA256 values not unique")
                    correct = sum(row.get("correct") is True for row in rows)
                    if summary.get("correct") != correct:
                        errors.append(f"{details_path}: correct count disagrees with summary")
                    details_hash = sha256(details_path)
                    if summary.get("details_sha256") != details_hash:
                        errors.append(f"{details_path}: details hash mismatch")
                    summary_hash = sha256(summary_path)
                    if expected_summary_hashes.get(str(summary_path)) != summary_hash:
                        errors.append(f"{summary_path}: aggregate summary hash mismatch")
                    data_hashes.add(str(summary.get("data_sha256")))
                    evaluator_hashes.add(str(summary.get("evaluator_script_sha256")))
                    checked.append(
                        {
                            "kind": "quality",
                            "arm": arm,
                            "dataset": dataset,
                            "run": run,
                            "summary_path": str(summary_path),
                            "summary_sha256": summary_hash,
                            "details_path": str(details_path),
                            "details_sha256": details_hash,
                            "requests": len(rows),
                            "correct": correct,
                        }
                    )
                except Exception as exc:
                    errors.append(f"{stem}: {exc}")
    if len(data_hashes) != len(QUALITY):
        errors.append("quality dataset hashes are not stable per dataset")
    if len(evaluator_hashes) != 1:
        errors.append("quality evaluator hash is not stable across all runs")
    return checked, data_hashes, evaluator_hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    aggregate_path = root / "historical-reproduction-summary.json"
    report_path = root / "HISTORICAL_REPRODUCTION_REPORT.md"
    errors: list[str] = []
    aggregate = load_object(aggregate_path)
    if aggregate.get("status") != "complete":
        errors.append("aggregate status is not complete")
    if aggregate.get("errors") != []:
        errors.append("aggregate contains errors")
    if aggregate.get("historical_direction_reproduced") is not True:
        errors.append("historical performance direction is not reproduced")
    performance = audit_performance(root, aggregate, errors)
    quality, data_hashes, evaluator_hashes = audit_quality(root, aggregate, errors)
    payload = {
        "schema": "hypic-historical-reproduction-audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": not errors,
        "expected_units": 18,
        "accepted_units": len(performance) + len(quality) if not errors else 0,
        "aggregate_path": str(aggregate_path),
        "aggregate_sha256": sha256(aggregate_path),
        "report_path": str(report_path),
        "report_sha256": sha256(report_path),
        "performance": performance,
        "quality": quality,
        "dataset_sha256": sorted(data_hashes),
        "evaluator_sha256": sorted(evaluator_hashes),
        "errors": errors,
    }
    atomic_json(args.output.resolve(), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] and payload["accepted_units"] == 18 else 2


if __name__ == "__main__":
    raise SystemExit(main())
