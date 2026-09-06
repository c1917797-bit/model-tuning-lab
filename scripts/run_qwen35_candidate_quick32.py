#!/usr/bin/env python3
"""Run one immutable four-concurrency quick32 candidate matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CONCURRENCIES = (1, 5, 8, 16)
MODEL = "Qwen3-5/Qwen3.5-27B"
DATASET = Path("/cache/cch/query_rewrite.jsonl")
DATASET_SHA256 = (
    "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
)
SCHEMA = "qwen35-candidate-quick32-run/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_cell(path: Path, concurrency: int, repetition: int) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "concurrency": concurrency,
        "repeat_index": repetition,
        "dataset_sha256": DATASET_SHA256,
        "model": MODEL,
        "seed": 1024,
        "requests": 32,
        "completed": 32,
        "errors": 0,
        "natural_eos": True,
        "finish_reasons": {"stop": 32},
        "max_tokens": "per-request model context remainder",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {payload.get(key)!r}"
            )
    hashes = payload.get("response_sha256")
    if not isinstance(hashes, list) or len(hashes) != 32:
        raise ValueError(f"{path}: incomplete response hash set")
    return payload


def write_state(path: Path, state: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def health(base_url: str, timeout: float) -> None:
    with urllib.request.urlopen(
        base_url.rstrip("/") + "/health", timeout=min(timeout, 30)
    ) as response:
        if int(response.status) != 200:
            raise RuntimeError("service health check did not return HTTP 200")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--candidate-mode", required=True)
    parser.add_argument("--device-set", choices=("0-3", "4-7"), default="4-7")
    parser.add_argument("--candidate-config", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument(
        "--benchmark-script",
        type=Path,
        default=Path(__file__).with_name("qwen35_query_rewrite_bench.py"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repetitions < 1:
        raise ValueError("--repetitions must be positive")
    if args.output_root.exists():
        raise FileExistsError(
            f"refusing to reuse candidate directory: {args.output_root}"
        )
    if not args.candidate_config.is_file():
        raise FileNotFoundError(args.candidate_config)
    actual_dataset_hash = sha256(DATASET)
    if actual_dataset_hash != DATASET_SHA256:
        raise ValueError(
            f"dataset SHA256 mismatch: expected {DATASET_SHA256}, "
            f"got {actual_dataset_hash}"
        )
    health(args.base_url, args.timeout)
    args.output_root.mkdir(parents=True)
    state_path = args.output_root / "candidate-run.json"
    state = {
        "schema": SCHEMA,
        "status": "running",
        "comparison_policy": "user-designated-fixed-original-quick32-v3",
        "candidate_id": args.candidate_id,
        "candidate_mode": args.candidate_mode,
        "physical_device_set": args.device_set,
        "candidate_config": str(args.candidate_config),
        "candidate_config_sha256": sha256(args.candidate_config),
        "run_id": args.run_id,
        "model": MODEL,
        "dataset": str(DATASET),
        "dataset_sha256": actual_dataset_hash,
        "request_limit": 32,
        "repetitions": args.repetitions,
        "concurrencies": list(CONCURRENCIES),
        "planned_cells": len(CONCURRENCIES) * args.repetitions,
        "completed_cells": [],
        "failed_cell": None,
        "started_unix_s": time.time(),
        "completed_unix_s": None,
    }
    write_state(state_path, state)
    active_concurrency: int | None = None
    active_repetition: int | None = None
    try:
        for active_concurrency in CONCURRENCIES:
            for active_repetition in range(1, args.repetitions + 1):
                output = (
                    args.output_root
                    / f"c{active_concurrency}-r{active_repetition}.json"
                )
                command = [
                    sys.executable,
                    str(args.benchmark_script),
                    "--base-url",
                    args.base_url,
                    "--model",
                    MODEL,
                    "--dataset",
                    str(DATASET),
                    "--dataset-sha256",
                    actual_dataset_hash,
                    "--concurrency",
                    str(active_concurrency),
                    "--repeat-index",
                    str(active_repetition),
                    "--seed",
                    "1024",
                    "--limit",
                    "32",
                    "--timeout",
                    str(args.timeout),
                    "--output",
                    str(output),
                ]
                subprocess.run(command, check=True)
                validated = validate_cell(
                    output, active_concurrency, active_repetition
                )
                state["completed_cells"].append(
                    {
                        "concurrency": active_concurrency,
                        "repetition": active_repetition,
                        "path": str(output),
                        "sha256": sha256(output),
                        "requests": validated["requests"],
                    }
                )
                write_state(state_path, state)
    except Exception as error:
        state["status"] = "failed"
        state["failed_cell"] = {
            "concurrency": active_concurrency,
            "repetition": active_repetition,
            "error_type": type(error).__name__,
        }
        state["completed_unix_s"] = time.time()
        write_state(state_path, state)
        raise
    state["status"] = "completed"
    state["completed_unix_s"] = time.time()
    write_state(state_path, state)
    print(json.dumps(state, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
