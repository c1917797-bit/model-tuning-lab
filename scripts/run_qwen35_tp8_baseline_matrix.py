#!/usr/bin/env python3
"""Run the repeated TP8/DP1 query_rewrite baseline matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CONCURRENCIES = (1, 5, 8, 16)
DATASET = Path("/cache/cch/query_rewrite.jsonl")
DATASET_SHA256 = "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
MODEL = "Qwen3-5/Qwen3.5-27B"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--benchmark-script", type=Path, default=Path(__file__).with_name("qwen35_query_rewrite_bench.py"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to reuse output directory: {args.output_root}")
    if args.repetitions < 1:
        raise ValueError("repetitions must be positive")
    if sha256(DATASET) != DATASET_SHA256:
        raise ValueError("query_rewrite dataset SHA256 mismatch")
    with urllib.request.urlopen(args.base_url.rstrip("/") + "/health", timeout=30) as response:
        if response.status != 200:
            raise RuntimeError("service health check failed")

    args.output_root.mkdir(parents=True)
    state_path = args.output_root / "baseline-run.json"
    state = {
        "schema": "qwen35-query-rewrite-tp8-baseline-run/v1",
        "status": "running",
        "run_id": args.run_id,
        "model": MODEL,
        "dataset": str(DATASET),
        "dataset_sha256": DATASET_SHA256,
        "physical_devices": list(range(8)),
        "tensor_parallel_size": 8,
        "data_parallel_size": 1,
        "quantization": None,
        "concurrencies": list(CONCURRENCIES),
        "repetitions": args.repetitions,
        "completed_cells": [],
        "started_unix_s": time.time(),
    }
    write_json(state_path, state)
    cells: dict[int, list[dict]] = {item: [] for item in CONCURRENCIES}

    try:
        for repeat in range(1, args.repetitions + 1):
            for concurrency in CONCURRENCIES:
                output = args.output_root / f"c{concurrency}-r{repeat}.json"
                command = [
                    sys.executable, str(args.benchmark_script),
                    "--base-url", args.base_url,
                    "--model", MODEL,
                    "--dataset", str(DATASET),
                    "--dataset-sha256", DATASET_SHA256,
                    "--concurrency", str(concurrency),
                    "--repeat-index", str(repeat),
                    "--seed", "1024",
                    "--limit", "32",
                    "--timeout", str(args.timeout),
                    "--output", str(output),
                ]
                subprocess.run(command, check=True)
                payload = json.loads(output.read_text(encoding="utf-8"))
                expected = {
                    "schema": "qwen35-query-rewrite-benchmark/v1",
                    "concurrency": concurrency,
                    "repeat_index": repeat,
                    "requests": 32,
                    "completed": 32,
                    "errors": 0,
                    "natural_eos": True,
                    "finish_reasons": {"stop": 32},
                }
                for key, value in expected.items():
                    if payload.get(key) != value:
                        raise ValueError(f"{output}: {key} mismatch")
                cells[concurrency].append(payload)
                state["completed_cells"].append({
                    "concurrency": concurrency,
                    "repeat_index": repeat,
                    "path": str(output),
                    "sha256": sha256(output),
                })
                write_json(state_path, state)
    except Exception as error:
        state["status"] = "failed"
        state["error_type"] = type(error).__name__
        state["completed_unix_s"] = time.time()
        write_json(state_path, state)
        raise

    summary = {
        "schema": "qwen35-query-rewrite-tp8-baseline-summary/v1",
        "aggregation": "median across repetitions of each cell-level value; latency uses each repetition's request-level p50",
        "cells": {},
    }
    for concurrency, reports in cells.items():
        summary["cells"][str(concurrency)] = {
            "ttft_p50_ms": statistics.median(report["ttft_ms"]["p50"] for report in reports),
            "tpot_p50_ms": statistics.median(report["tpot_ms"]["p50"] for report in reports),
            "e2e_p50_ms": statistics.median(report["e2e_ms"]["p50"] for report in reports),
            "request_throughput_rps": statistics.median(report["request_throughput"] for report in reports),
            "output_token_throughput_tps": statistics.median(report["output_token_throughput"] for report in reports),
            "repeat_files": [str(args.output_root / f"c{concurrency}-r{repeat}.json") for repeat in range(1, args.repetitions + 1)],
        }
    write_json(args.output_root / "baseline-summary.json", summary)
    state["status"] = "completed"
    state["completed_unix_s"] = time.time()
    state["summary_sha256"] = sha256(args.output_root / "baseline-summary.json")
    write_json(state_path, state)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
