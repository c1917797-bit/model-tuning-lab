#!/usr/bin/env python3
"""Compare one quick32 candidate with the immutable user-designated baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CONCURRENCIES = (1, 5, 8, 16)
DEFAULT_ORIGINAL_DIR = Path(
    "/cache/austinov/eval-runs/"
    "exp-20260904-qwen35-query-rewrite-3x-e2e/"
    "tp4-dev-decodegraph/quick32-v3"
)
ORIGINAL_SHA256 = {
    1: "ac39bc922b43d9472fe41f89bae25a0190cf20817147230f8725f151e3ce413a",
    5: "68d2a3020bb52594e13560dd608afca1d611d61a37383aa94062bfe78784f7ae",
    8: "4f9799a128128b1e34dca498256833c45f52373cd2486b4acd9298030d7d58ce",
    16: "085c0a43a7a720ba42f1d83bf2ebacebb64e515d24bb3f040eabd5c046f777e4",
}
EXPECTED_IDENTITY = {
    "model": "Qwen3-5/Qwen3.5-27B",
    "dataset_sha256": (
        "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
    ),
    "requests": 32,
    "max_tokens": "per-request model context remainder",
    "seed": 1024,
}


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_path(root: Path, concurrency: int) -> Path:
    return root / f"c{concurrency}-r1.json"


def load_cell(root: Path, concurrency: int, *, original: bool) -> dict:
    path = cell_path(root, concurrency)
    if original:
        actual_digest = digest_file(path)
        expected_digest = ORIGINAL_SHA256[concurrency]
        if actual_digest != expected_digest:
            raise ValueError(
                f"{path}: immutable original SHA256 mismatch; "
                f"expected {expected_digest}, got {actual_digest}"
            )
    row = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "concurrency": concurrency,
        "repeat_index": 1,
        "errors": 0,
        "natural_eos": True,
        **EXPECTED_IDENTITY,
    }
    for key, value in expected.items():
        if row.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {row.get(key)!r}"
            )
    if row.get("completed") != 32:
        raise ValueError(f"{path}: completed must be 32")
    if row.get("finish_reasons") != {"stop": 32}:
        raise ValueError(f"{path}: all requests must terminate naturally")
    hashes = row.get("response_sha256")
    if not isinstance(hashes, list) or len(hashes) != 32:
        raise ValueError(f"{path}: invalid response hash set")
    for metric in ("ttft_ms", "tpot_ms", "e2e_ms"):
        value = row.get(metric, {}).get("p50")
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{path}: invalid {metric}.p50")
    return row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--original-dir", type=Path, default=DEFAULT_ORIGINAL_DIR
    )
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument(
        "--candidate-device-set", choices=("0-3", "4-7"), default="4-7"
    )
    parser.add_argument("--target-ratio", type=float, default=0.5)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 < args.target_ratio <= 1:
        raise ValueError("target ratio must be in (0, 1]")

    cells: dict[str, dict] = {}
    artifact_sha256: dict[str, str] = {}
    correctness_pass = True
    performance_pass = True
    for concurrency in CONCURRENCIES:
        original_path = cell_path(args.original_dir, concurrency)
        candidate_path = cell_path(args.candidate_dir, concurrency)
        original = load_cell(args.original_dir, concurrency, original=True)
        candidate = load_cell(args.candidate_dir, concurrency, original=False)
        mismatches = sum(
            left != right
            for left, right in zip(
                original["response_sha256"], candidate["response_sha256"]
            )
        )
        cell_correct = mismatches == 0
        correctness_pass = correctness_pass and cell_correct
        original_ttft = float(original["ttft_ms"]["p50"])
        candidate_ttft = float(candidate["ttft_ms"]["p50"])
        original_tpot = float(original["tpot_ms"]["p50"])
        candidate_tpot = float(candidate["tpot_ms"]["p50"])
        ttft_ratio = candidate_ttft / original_ttft
        tpot_ratio = candidate_tpot / original_tpot
        cell_performance_pass = (
            ttft_ratio <= args.target_ratio
            and tpot_ratio <= args.target_ratio
        )
        performance_pass = performance_pass and cell_performance_pass
        cells[str(concurrency)] = {
            "original_ttft_p50_ms": original_ttft,
            "candidate_ttft_p50_ms": candidate_ttft,
            "ttft_ratio": ttft_ratio,
            "ttft_improvement_x": original_ttft / candidate_ttft,
            "original_tpot_p50_ms": original_tpot,
            "candidate_tpot_p50_ms": candidate_tpot,
            "tpot_ratio": tpot_ratio,
            "tpot_improvement_x": original_tpot / candidate_tpot,
            "response_hash_mismatches": mismatches,
            "correctness_exact_hash_match": cell_correct,
            "performance_target_met": cell_performance_pass,
        }
        artifact_sha256[f"original/c{concurrency}-r1.json"] = digest_file(
            original_path
        )
        artifact_sha256[f"candidate/c{concurrency}-r1.json"] = digest_file(
            candidate_path
        )

    final_target_met = correctness_pass and performance_pass
    if not correctness_pass:
        decision = "hold-exact-hash-drift"
        exit_status = 3
    elif final_target_met:
        decision = "final-target-met"
        exit_status = 0
    else:
        decision = "iterate"
        exit_status = 2
    report = {
        "schema": "qwen35-candidate-vs-fixed-original-decision/v1",
        "comparison_policy": "user-designated-fixed-original-quick32-v3",
        "candidate_id": args.candidate_id,
        "candidate_physical_device_set": args.candidate_device_set,
        "original_physical_device_set": "0-3",
        "identity": EXPECTED_IDENTITY,
        "original_runtime_caveat": (
            "quick32-v3 forced enable_matmul_allreduce=false; candidates may "
            "intentionally change runtime configuration. The user designated "
            "these immutable artifacts as the common performance denominator."
        ),
        "target_ratio": args.target_ratio,
        "correctness_exact_hash_match": correctness_pass,
        "correctness_gate_status": (
            "exact-hash-reproducible"
            if correctness_pass
            else "semantic-business-check-required"
        ),
        "exact_hash_evidence_boundary": (
            "A fixed-runtime NPU4-7 control also differs from the immutable "
            "original. Cross-run response hashes are a reproducibility "
            "diagnostic, not sufficient evidence of semantic regression."
        ),
        "performance_target_met": performance_pass,
        "final_target_met": final_target_met,
        "cells": cells,
        "artifact_sha256": artifact_sha256,
        "decision": decision,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
