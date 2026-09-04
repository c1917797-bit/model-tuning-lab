#!/usr/bin/env python3
"""Run the frozen 4-concurrency x 3-repetition query_rewrite matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from render_qwen35_runtime import render

SCHEMA = "qwen35-query-rewrite-matrix-run/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan(config: dict, output_root: Path) -> list[dict]:
    benchmark = config["benchmark"]
    cells = []
    for concurrency in benchmark["concurrency"]:
        for repetition in range(1, int(benchmark["repetitions"]) + 1):
            cells.append(
                {
                    "concurrency": int(concurrency),
                    "repetition": repetition,
                    "output": output_root
                    / f"c{concurrency}"
                    / f"repeat-{repetition}.json",
                }
            )
    if len(cells) != 12 or len({str(cell["output"]) for cell in cells}) != 12:
        raise ValueError("frozen benchmark must produce 12 unique cells")
    return cells


def validate_cell(
    path: Path,
    *,
    concurrency: int,
    repetition: int,
    dataset_sha256: str,
    model: str,
) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "concurrency": concurrency,
        "repeat_index": repetition,
        "dataset_sha256": dataset_sha256,
        "model": model,
        "errors": 0,
        "natural_eos": True,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {payload.get(key)!r}"
            )
    if payload.get("completed") != payload.get("requests"):
        raise ValueError(f"{path}: incomplete request set")
    if payload.get("finish_reasons") != {"stop": payload["requests"]}:
        raise ValueError(f"{path}: non-stop completion detected")
    hashes = payload.get("response_sha256")
    if not isinstance(hashes, list) or len(hashes) != payload["requests"]:
        raise ValueError(f"{path}: incomplete response hash set")
    return payload


def write_state(path: Path, state: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--variant", choices=("baseline", "candidate"), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument(
        "--benchmark-script",
        type=Path,
        default=Path(__file__).with_name("qwen35_query_rewrite_bench.py"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to reuse matrix directory: {args.output_root}")
    runtime = render(args.config)
    benchmark = runtime["benchmark"]
    dataset = Path(benchmark["dataset"])
    actual_dataset_hash = sha256(dataset)
    if actual_dataset_hash != benchmark["dataset_sha256"]:
        raise ValueError(
            "dataset SHA256 mismatch: "
            f"expected {benchmark['dataset_sha256']}, got {actual_dataset_hash}"
        )
    health(args.base_url, args.timeout)
    cells = plan(runtime, args.output_root)
    model = runtime["argv"][runtime["argv"].index("--served-model-name") + 1]
    args.output_root.mkdir(parents=True)
    state_path = args.output_root / "matrix-run.json"
    state = {
        "schema": SCHEMA,
        "status": "running",
        "performance_evidence": True,
        "variant": args.variant,
        "run_id": args.run_id,
        "base_url": args.base_url,
        "runtime_source_sha256": runtime["source_sha256"],
        "runtime_sha256": runtime["runtime_sha256"],
        "dataset": str(dataset),
        "dataset_sha256": actual_dataset_hash,
        "planned_cells": 12,
        "completed_cells": [],
        "failed_cell": None,
        "started_unix_s": time.time(),
        "completed_unix_s": None,
    }
    write_state(state_path, state)
    try:
        for cell in cells:
            cell["output"].parent.mkdir(parents=True, exist_ok=True)
            command = [
                sys.executable,
                str(args.benchmark_script),
                "--base-url",
                args.base_url,
                "--model",
                model,
                "--dataset",
                str(dataset),
                "--dataset-sha256",
                actual_dataset_hash,
                "--concurrency",
                str(cell["concurrency"]),
                "--repeat-index",
                str(cell["repetition"]),
                "--timeout",
                str(args.timeout),
                "--output",
                str(cell["output"]),
            ]
            subprocess.run(command, check=True)
            validated = validate_cell(
                cell["output"],
                concurrency=cell["concurrency"],
                repetition=cell["repetition"],
                dataset_sha256=actual_dataset_hash,
                model=model,
            )
            state["completed_cells"].append(
                {
                    "concurrency": cell["concurrency"],
                    "repetition": cell["repetition"],
                    "path": str(cell["output"]),
                    "sha256": sha256(cell["output"]),
                    "requests": validated["requests"],
                }
            )
            write_state(state_path, state)
    except Exception as error:
        state["status"] = "failed"
        state["failed_cell"] = {
            "concurrency": cell["concurrency"],
            "repetition": cell["repetition"],
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
