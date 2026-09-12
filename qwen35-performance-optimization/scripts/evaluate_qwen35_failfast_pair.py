#!/usr/bin/env python3
"""Evaluate one paired Qwen3.5 fail-fast benchmark cell.

This is the early gate used before spending NPU time on the full c1/c5/c8/c16
three-repeat matrix. It intentionally depends only on the Python standard
library so the host does not need unittest, pytest, or GitHub CLI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


IDENTITY_KEYS = (
    "schema",
    "model",
    "dataset_sha256",
    "requests",
    "max_tokens",
    "seed",
    "concurrency",
    "repeat_index",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "qwen35-query-rewrite-benchmark/v1":
        raise ValueError(f"{path}: unexpected schema {payload.get('schema')!r}")
    expected_requests = payload.get("requests")
    if not isinstance(expected_requests, int) or expected_requests <= 0:
        raise ValueError(f"{path}: invalid requests")
    if payload.get("completed") != expected_requests:
        raise ValueError(f"{path}: completed must equal requests")
    if payload.get("errors") != 0:
        raise ValueError(f"{path}: errors must be zero")
    if payload.get("finish_reasons") != {"stop": expected_requests}:
        raise ValueError(f"{path}: all requests must finish with stop")
    if payload.get("natural_eos") is not True:
        raise ValueError(f"{path}: natural_eos must be true")
    hashes = payload.get("response_sha256")
    if not isinstance(hashes, list) or len(hashes) != expected_requests:
        raise ValueError(f"{path}: response_sha256 length mismatch")
    for metric in ("ttft_ms", "tpot_ms", "e2e_ms"):
        p95 = payload.get(metric, {}).get("p95")
        if not isinstance(p95, (int, float)) or p95 <= 0:
            raise ValueError(f"{path}: invalid {metric}.p95")
    return payload


def identity(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload.get(key) for key in IDENTITY_KEYS}


def reduction(control: float, candidate: float) -> float:
    if control <= 0:
        raise ValueError("control latency must be positive")
    return (control - candidate) / control


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--ttft-min-reduction", type=float, default=0.20)
    parser.add_argument("--tpot-min-reduction", type=float, default=0.10)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    control = load(args.control)
    candidate = load(args.candidate)
    if identity(control) != identity(candidate):
        raise ValueError("control/candidate identity mismatch")

    control_hashes = control["response_sha256"]
    candidate_hashes = candidate["response_sha256"]
    compared = min(len(control_hashes), len(candidate_hashes))
    matched = sum(
        left == right for left, right in zip(control_hashes, candidate_hashes)
    )

    cells: dict[str, Any] = {}
    for metric, threshold in (
        ("ttft_ms", args.ttft_min_reduction),
        ("tpot_ms", args.tpot_min_reduction),
    ):
        c95 = float(control[metric]["p95"])
        v95 = float(candidate[metric]["p95"])
        gain = reduction(c95, v95)
        cells[metric] = {
            "control_p95_ms": c95,
            "candidate_p95_ms": v95,
            "reduction_fraction": gain,
            "reduction_percent": gain * 100.0,
            "target_reduction_fraction": threshold,
            "target_met": gain >= threshold,
        }

    performance_pass = all(cell["target_met"] for cell in cells.values())
    report = {
        "schema": "qwen35-failfast-pair-decision/v1",
        "candidate_id": args.candidate_id,
        "control": str(args.control),
        "candidate": str(args.candidate),
        "control_sha256": sha256(args.control),
        "candidate_sha256": sha256(args.candidate),
        "identity": identity(control),
        "completed": control["completed"],
        "natural_eos": True,
        "metrics": cells,
        "response_hash_equal_count": matched,
        "response_hash_compared_count": compared,
        "response_hash_all_equal": matched == compared,
        "performance_target_met": performance_pass,
        "quality_gate_required_separately": True,
        "decision": "advance-to-quality-canary" if performance_pass else "iterate",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if performance_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
