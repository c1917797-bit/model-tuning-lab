#!/usr/bin/env python3
"""Validate and summarize the frozen four-concurrency Qwen3.5 A/B matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

CONCURRENCIES = (1, 5, 8, 16)
REPETITIONS = (1, 2, 3)
REQUIRED_IDENTITY = (
    "model",
    "dataset_sha256",
    "requests",
    "max_tokens",
    "seed",
)


def load_cell(root: Path, concurrency: int, repetition: int) -> dict:
    path = root / f"c{concurrency}-r{repetition}.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("schema") != "qwen35-query-rewrite-benchmark/v1":
        raise ValueError(f"{path}: unsupported schema")
    if row.get("concurrency") != concurrency:
        raise ValueError(f"{path}: concurrency mismatch")
    if row.get("repeat_index") != repetition:
        raise ValueError(f"{path}: repeat index mismatch")
    if row.get("errors") != 0:
        raise ValueError(f"{path}: benchmark contains request errors")
    if row.get("completed") != row.get("requests"):
        raise ValueError(f"{path}: incomplete request set")
    for metric in ("ttft_ms", "tpot_ms", "e2e_ms"):
        if not isinstance(row.get(metric, {}).get("p50"), (int, float)):
            raise ValueError(f"{path}: missing {metric}.p50")
    hashes = row.get("response_sha256")
    if not isinstance(hashes, list) or len(hashes) != row["requests"]:
        raise ValueError(f"{path}: invalid response hash set")
    return row


def identity(row: dict) -> dict:
    return {key: row.get(key) for key in REQUIRED_IDENTITY}


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--target-ratio", type=float, default=0.5)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 < args.target_ratio <= 1:
        raise ValueError("target ratio must be in (0, 1]")
    baseline: dict[int, list[dict]] = {}
    candidate: dict[int, list[dict]] = {}
    manifest: dict[str, str] = {}
    reference_identity: dict | None = None
    correctness_pass = True
    for concurrency in CONCURRENCIES:
        baseline[concurrency] = []
        candidate[concurrency] = []
        for repetition in REPETITIONS:
            baseline_path = args.baseline_dir / f"c{concurrency}-r{repetition}.json"
            candidate_path = args.candidate_dir / f"c{concurrency}-r{repetition}.json"
            base_row = load_cell(args.baseline_dir, concurrency, repetition)
            cand_row = load_cell(args.candidate_dir, concurrency, repetition)
            base_identity = identity(base_row)
            cand_identity = identity(cand_row)
            if base_identity != cand_identity:
                raise ValueError(
                    f"c{concurrency}-r{repetition}: A/B identity mismatch"
                )
            if reference_identity is None:
                reference_identity = base_identity
            elif reference_identity != base_identity:
                raise ValueError(
                    f"c{concurrency}-r{repetition}: matrix identity drift"
                )
            if base_row["response_sha256"] != cand_row["response_sha256"]:
                correctness_pass = False
            baseline[concurrency].append(base_row)
            candidate[concurrency].append(cand_row)
            manifest[f"baseline/c{concurrency}-r{repetition}.json"] = (
                digest_file(baseline_path)
            )
            manifest[f"candidate/c{concurrency}-r{repetition}.json"] = (
                digest_file(candidate_path)
            )

    cells: dict[str, dict] = {}
    final_target_met = correctness_pass
    for concurrency in CONCURRENCIES:
        base_ttft = statistics.median(
            float(row["ttft_ms"]["p50"]) for row in baseline[concurrency]
        )
        cand_ttft = statistics.median(
            float(row["ttft_ms"]["p50"]) for row in candidate[concurrency]
        )
        base_tpot = statistics.median(
            float(row["tpot_ms"]["p50"]) for row in baseline[concurrency]
        )
        cand_tpot = statistics.median(
            float(row["tpot_ms"]["p50"]) for row in candidate[concurrency]
        )
        ttft_ratio = cand_ttft / base_ttft
        tpot_ratio = cand_tpot / base_tpot
        cell_pass = (
            ttft_ratio <= args.target_ratio
            and tpot_ratio <= args.target_ratio
        )
        final_target_met = final_target_met and cell_pass
        cells[str(concurrency)] = {
            "baseline_ttft_p50_ms": base_ttft,
            "candidate_ttft_p50_ms": cand_ttft,
            "ttft_ratio": ttft_ratio,
            "ttft_improvement_x": base_ttft / cand_ttft,
            "baseline_tpot_p50_ms": base_tpot,
            "candidate_tpot_p50_ms": cand_tpot,
            "tpot_ratio": tpot_ratio,
            "tpot_improvement_x": base_tpot / cand_tpot,
            "target_met": cell_pass,
        }

    report = {
        "schema": "qwen35-query-rewrite-ab-decision/v1",
        "identity": reference_identity,
        "target_ratio": args.target_ratio,
        "correctness_exact_hash_match": correctness_pass,
        "cells": cells,
        "final_target_met": final_target_met,
        "artifact_sha256": manifest,
        "decision": "final-target-met" if final_target_met else "iterate",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if final_target_met else 2


if __name__ == "__main__":
    raise SystemExit(main())
