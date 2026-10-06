#!/usr/bin/env python3
"""Preregistered semantic and service-performance progression gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def assess_canary(root: Path) -> bool:
    paths = {
        arm: root / arm / "semantic-canary.json"
        for arm in ("no-cache", "hypic-only")
    }
    runs = {arm: read(path) for arm, path in paths.items()}
    failures = []
    for arm, run in runs.items():
        if run.get("schema") != "hypic-active-semantic-canary/v1":
            failures.append(f"{arm}: schema")
        if run.get("answer_contains_key") is not True:
            failures.append(f"{arm}: answer key")
        if run.get("input_tokens") != 32768:
            failures.append(f"{arm}: input length")
        if run.get("request") != {
            "max_tokens": 32, "temperature": 0, "seed": 0,
            "ignore_eos": False,
        }:
            failures.append(f"{arm}: request protocol")
    for key in ("prompt_token_sha256", "public_segment_token_sha256"):
        if runs["no-cache"].get(key) != runs["hypic-only"].get(key):
            failures.append(f"prompt mismatch: {key}")
    baseline = " ".join(runs["no-cache"].get("response_text", "").split())
    treatment = " ".join(runs["hypic-only"].get("response_text", "").split())
    if baseline != treatment:
        failures.append("deterministic canary response mismatch")
    result = {
        "schema": "hypic-e2e-canary-gate/v1",
        "passed": not failures,
        "failures": failures,
        "response_equal": baseline == treatment,
        "response_sha256": {
            arm: runs[arm].get("response_text_sha256") for arm in runs
        },
        "artifact_sha256": {
            arm: hashlib.sha256(paths[arm].read_bytes()).hexdigest()
            for arm in paths
        },
    }
    write(root / "canary-gate.json", result)
    print(json.dumps(result, sort_keys=True))
    return result["passed"]


def assess_performance(root: Path) -> bool:
    metrics = {
        "ttft_p95_ms": ("lower", 30.0),
        "tpot_p95_ms": ("lower", 10.0),
        "output_tokens_per_second": ("higher", 20.0),
        "benchmark_duration_s": ("lower", 15.0),
    }
    summaries = {}
    hashes = {}
    for arm in ("no-cache", "hypic-only"):
        summaries[arm] = []
        hashes[arm] = []
        for index in (1, 2, 3):
            path = root / arm / f"performance.run{index}.json"
            record = read(path)
            summary = record["summary"]
            if not (
                summary.get("successful") == 40
                and summary.get("failed") == 0
                and summary.get("fixed_output_verified") is True
            ):
                raise ValueError(f"incomplete performance run: {path}")
            summaries[arm].append(summary)
            hashes[arm].append(hashlib.sha256(path.read_bytes()).hexdigest())
    evaluated = {}
    failures = []
    for name, (direction, minimum) in metrics.items():
        base = statistics.median(float(row[name]) for row in summaries["no-cache"])
        candidate = statistics.median(
            float(row[name]) for row in summaries["hypic-only"]
        )
        if base <= 0 or candidate <= 0:
            raise ValueError(f"nonpositive metric: {name}")
        improvement = (
            (base - candidate) / base if direction == "lower"
            else (candidate - base) / base
        ) * 100.0
        passed = improvement >= minimum
        evaluated[name] = {
            "baseline_median": base,
            "treatment_median": candidate,
            "improvement_percent": improvement,
            "minimum_percent": minimum,
            "passed": passed,
        }
        if not passed:
            failures.append(name)
    result = {
        "schema": "hypic-e2e-performance-gate/v1",
        "passed": not failures,
        "failures": failures,
        "metrics": evaluated,
        "run_sha256": hashes,
    }
    write(root / "performance-gate.json", result)
    print(json.dumps(result, sort_keys=True))
    return result["passed"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=("canary", "performance"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if args.gate == "canary":
        passed = assess_canary(args.root)
    else:
        passed = assess_performance(args.root)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
