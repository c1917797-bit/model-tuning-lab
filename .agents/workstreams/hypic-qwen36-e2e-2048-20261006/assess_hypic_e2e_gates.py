#!/usr/bin/env python3
"""Preregistered semantic and service-performance progression gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def validate_performance_record(record: dict, arm: str, index: int) -> dict:
    """Reject an incomplete or protocol-drifted raw run before reusing it."""
    config = record.get("config", {})
    expected_config = {
        "base_url": "http://127.0.0.1:8223",
        "model": "qwen36-hypic-e2e-2048",
        "input_tokens": 32768,
        "prefix_tokens": 16384,
        "output_tokens": 1024,
        "requests": 40,
        "concurrency": 16,
        "warmup_requests": 2,
        "ignore_eos": True,
        "segment_boundary_transport": "vllm_xargs.hypic_segment_ends",
        "segment_ends": [16384, 32768],
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise ValueError(f"{arm} run{index}: protocol mismatch: {key}")

    rows = record.get("results")
    warmups = record.get("warmup_results")
    if not isinstance(rows, list) or len(rows) != 40:
        raise ValueError(f"{arm} run{index}: expected 40 raw request rows")
    if not isinstance(warmups, list) or len(warmups) != 2:
        raise ValueError(f"{arm} run{index}: expected two raw warmup rows")
    if sorted(row.get("index") for row in rows) != list(range(40)):
        raise ValueError(f"{arm} run{index}: request indexes are incomplete")
    if sorted(row.get("index") for row in warmups) != [-2, -1]:
        raise ValueError(f"{arm} run{index}: warmup indexes are incomplete")
    for row, expected_tokens in [
        *((row, 1024) for row in rows),
        *((row, 1) for row in warmups),
    ]:
        digest = row.get("output_sha256")
        if not (
            row.get("ok") is True
            and row.get("error") is None
            and row.get("finish_reason") == "length"
            and row.get("requested_output_tokens") == expected_tokens
            and row.get("output_tokens") == expected_tokens
            and isinstance(digest, str)
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
            and isinstance(row.get("ttft_ms"), (int, float))
            and math.isfinite(row["ttft_ms"])
            and row["ttft_ms"] > 0
            and isinstance(row.get("duration_s"), (int, float))
            and math.isfinite(row["duration_s"])
            and row["duration_s"] > 0
        ):
            raise ValueError(f"{arm} run{index}: invalid raw request or warmup")

    summary = record.get("summary", {})
    expected_summary = {
        "requests": 40,
        "successful": 40,
        "failed": 0,
        "expected_output_tokens": 40960,
        "output_tokens": 40960,
        "fixed_output_requests": 40,
        "fixed_output_verified": True,
        "finish_reasons": {"length": 40},
        "measured_concurrency": 16,
        "measured_waves": 3,
        "output_token_completion_ratio": 1.0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ValueError(f"{arm} run{index}: summary mismatch: {key}")
    for key in (
        "ttft_p95_ms", "tpot_p95_ms", "output_tokens_per_second",
        "benchmark_duration_s",
    ):
        value = summary.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{arm} run{index}: invalid metric: {key}")
    throughput = 40960 / summary["benchmark_duration_s"]
    if not math.isclose(summary["output_tokens_per_second"], throughput, rel_tol=1e-6):
        raise ValueError(f"{arm} run{index}: throughput does not match duration")
    if arm == "hypic-only" and index == 1 and summary.get("hot_path_verified") is not True:
        raise ValueError("HYPIC treatment run1: hot path not verified")
    return summary


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
            summary = validate_performance_record(record, arm, index)
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
    parser.add_argument("gate", choices=("canary", "performance", "validate-performance"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--path", type=Path)
    parser.add_argument("--arm", choices=("no-cache", "hypic-only"))
    parser.add_argument("--run-index", type=int)
    args = parser.parse_args()
    if args.gate == "validate-performance":
        if args.path is None or args.arm is None or args.run_index not in (1, 2, 3):
            parser.error("validate-performance requires --path, --arm, and --run-index 1-3")
        validate_performance_record(read(args.path), args.arm, args.run_index)
        print(f"verified {args.arm} run{args.run_index}: {args.path}")
        return 0
    if args.root is None:
        parser.error(f"{args.gate} requires --root")
    if args.gate == "canary":
        passed = assess_canary(args.root)
    else:
        passed = assess_performance(args.root)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
