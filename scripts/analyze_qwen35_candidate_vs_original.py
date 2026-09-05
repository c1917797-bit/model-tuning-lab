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


def load_cell(
    root: Path,
    concurrency: int,
    *,
    original: bool,
    require_success: bool = True,
) -> dict:
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
        "natural_eos": True,
        **EXPECTED_IDENTITY,
    }
    if require_success:
        expected["errors"] = 0
    for key, value in expected.items():
        if row.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {row.get(key)!r}"
            )
    if require_success and row.get("completed") != 32:
        raise ValueError(f"{path}: completed must be 32")
    if require_success and row.get("finish_reasons") != {"stop": 32}:
        raise ValueError(f"{path}: all requests must terminate naturally")
    hashes = row.get("response_sha256")
    expected_hashes = 32 if require_success else row.get("completed")
    if (
        not isinstance(hashes, list)
        or not isinstance(expected_hashes, int)
        or len(hashes) != expected_hashes
    ):
        raise ValueError(f"{path}: invalid response hash set")
    for metric in ("ttft_ms", "tpot_ms", "e2e_ms"):
        value = row.get(metric, {}).get("p50")
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{path}: invalid {metric}.p50")
    return row


def load_reference_quality(path: Path, row: dict) -> dict:
    quality = row.get("reference_quality")
    if not isinstance(quality, dict):
        raise ValueError(f"{path}: missing reference_quality")
    if quality.get("reference_field") != "answer":
        raise ValueError(f"{path}: reference_quality must use answer")
    result = {
        "raw_exact_matches": quality.get("raw_exact_matches"),
        "normalized_whitespace_exact_matches": quality.get(
            "normalized_whitespace_exact_matches"
        ),
    }
    for key, value in result.items():
        if not isinstance(value, int) or not 0 <= value <= 32:
            raise ValueError(f"{path}: invalid reference_quality.{key}")
    similarity = quality.get("normalized_character_similarity")
    if not isinstance(similarity, dict):
        raise ValueError(
            f"{path}: missing normalized_character_similarity"
        )
    for metric in ("mean", "p50"):
        value = similarity.get(metric)
        if (
            not isinstance(value, (int, float))
            or not 0.0 <= float(value) <= 1.0
        ):
            raise ValueError(
                f"{path}: invalid normalized_character_similarity.{metric}"
            )
        result[f"similarity_{metric}"] = float(value)
    return result


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
    parser.add_argument(
        "--semantic-control-dir",
        type=Path,
        help=(
            "same-runtime unpruned control containing privacy-safe aggregate "
            "reference-quality metrics"
        ),
    )
    parser.add_argument(
        "--max-mean-similarity-drop", type=float, default=0.02
    )
    parser.add_argument(
        "--max-p50-similarity-drop", type=float, default=0.02
    )
    parser.add_argument("--max-exact-match-drop", type=int, default=1)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="emit a reject-runtime-failure decision for partial matrices",
    )
    parser.add_argument(
        "--candidate-run",
        type=Path,
        help="optional candidate-run.json status manifest",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 < args.target_ratio <= 1:
        raise ValueError("target ratio must be in (0, 1]")
    if not 0 <= args.max_mean_similarity_drop <= 1:
        raise ValueError("mean similarity drop must be in [0, 1]")
    if not 0 <= args.max_p50_similarity_drop <= 1:
        raise ValueError("p50 similarity drop must be in [0, 1]")
    if not 0 <= args.max_exact_match_drop <= 32:
        raise ValueError("exact-match drop must be in [0, 32]")

    cells: dict[str, dict] = {}
    artifact_sha256: dict[str, str] = {}
    correctness_pass = True
    exact_hash_pass = True
    semantic_quality_pass = True
    semantic_control_enabled = args.semantic_control_dir is not None
    performance_pass = True
    runtime_pass = True
    for concurrency in CONCURRENCIES:
        original_path = cell_path(args.original_dir, concurrency)
        candidate_path = cell_path(args.candidate_dir, concurrency)
        original = load_cell(args.original_dir, concurrency, original=True)
        artifact_sha256[f"original/c{concurrency}-r1.json"] = digest_file(
            original_path
        )
        if not candidate_path.exists():
            if not args.allow_incomplete:
                raise FileNotFoundError(candidate_path)
            runtime_pass = False
            performance_pass = False
            correctness_pass = False
            semantic_quality_pass = False
            cells[str(concurrency)] = {
                "status": "not-run",
                "measurement_valid": False,
                "runtime_gate_met": False,
                "performance_target_met": False,
                "correctness_exact_hash_match": None,
            }
            continue
        candidate = load_cell(
            args.candidate_dir,
            concurrency,
            original=False,
            require_success=not args.allow_incomplete,
        )
        candidate_success = (
            candidate.get("errors") == 0
            and candidate.get("completed") == 32
            and candidate.get("finish_reasons") == {"stop": 32}
            and len(candidate["response_sha256"]) == 32
        )
        runtime_pass = runtime_pass and candidate_success
        mismatches = sum(
            left != right
            for left, right in zip(
                original["response_sha256"], candidate["response_sha256"]
            )
        )
        cell_exact = mismatches == 0 if candidate_success else None
        exact_hash_pass = exact_hash_pass and bool(cell_exact)
        semantic_quality = None
        if semantic_control_enabled and candidate_success:
            control_path = cell_path(args.semantic_control_dir, concurrency)
            control = load_cell(
                args.semantic_control_dir,
                concurrency,
                original=False,
            )
            control_quality = load_reference_quality(control_path, control)
            candidate_quality = load_reference_quality(
                candidate_path, candidate
            )
            mean_drop = (
                control_quality["similarity_mean"]
                - candidate_quality["similarity_mean"]
            )
            p50_drop = (
                control_quality["similarity_p50"]
                - candidate_quality["similarity_p50"]
            )
            raw_exact_drop = (
                control_quality["raw_exact_matches"]
                - candidate_quality["raw_exact_matches"]
            )
            normalized_exact_drop = (
                control_quality["normalized_whitespace_exact_matches"]
                - candidate_quality[
                    "normalized_whitespace_exact_matches"
                ]
            )
            cell_semantic_pass = (
                mean_drop <= args.max_mean_similarity_drop
                and p50_drop <= args.max_p50_similarity_drop
                and raw_exact_drop <= args.max_exact_match_drop
                and normalized_exact_drop <= args.max_exact_match_drop
            )
            semantic_quality_pass = (
                semantic_quality_pass and cell_semantic_pass
            )
            semantic_quality = {
                "control": control_quality,
                "candidate": candidate_quality,
                "mean_similarity_drop": mean_drop,
                "p50_similarity_drop": p50_drop,
                "raw_exact_match_drop": raw_exact_drop,
                "normalized_exact_match_drop": normalized_exact_drop,
                "gate_met": cell_semantic_pass,
            }
            artifact_sha256[
                f"semantic-control/c{concurrency}-r1.json"
            ] = digest_file(control_path)
            cell_correct = cell_semantic_pass
        else:
            cell_correct = cell_exact
        correctness_pass = correctness_pass and cell_correct
        original_ttft = float(original["ttft_ms"]["p50"])
        candidate_ttft = float(candidate["ttft_ms"]["p50"])
        original_tpot = float(original["tpot_ms"]["p50"])
        candidate_tpot = float(candidate["tpot_ms"]["p50"])
        ttft_ratio = candidate_ttft / original_ttft
        tpot_ratio = candidate_tpot / original_tpot
        cell_performance_pass = candidate_success and (
            ttft_ratio <= args.target_ratio
            and tpot_ratio <= args.target_ratio
        )
        performance_pass = performance_pass and cell_performance_pass
        cells[str(concurrency)] = {
            "status": "complete" if candidate_success else "failed",
            "measurement_valid": candidate_success,
            "runtime_gate_met": candidate_success,
            "completed_requests": candidate.get("completed"),
            "errors": candidate.get("errors"),
            "error_types": candidate.get("error_types", []),
            "error_reasons": candidate.get("error_reasons", {}),
            "original_ttft_p50_ms": original_ttft,
            "candidate_ttft_p50_ms": candidate_ttft,
            "ttft_ratio": ttft_ratio,
            "ttft_improvement_x": original_ttft / candidate_ttft,
            "original_tpot_p50_ms": original_tpot,
            "candidate_tpot_p50_ms": candidate_tpot,
            "tpot_ratio": tpot_ratio,
            "tpot_improvement_x": original_tpot / candidate_tpot,
            "response_hash_mismatches_observed": mismatches,
            # Preserve the v1 complete-cell field for existing consumers. Partial
            # cells additionally carry the explicit observed qualifier above.
            "response_hash_mismatches": mismatches if candidate_success else None,
            "correctness_exact_hash_match": cell_exact,
            "semantic_quality": semantic_quality,
            "correctness_gate_met": cell_correct,
            "performance_target_met": cell_performance_pass,
        }
        artifact_sha256[f"candidate/c{concurrency}-r1.json"] = digest_file(
            candidate_path
        )

    candidate_run = None
    candidate_run_path = args.candidate_run
    if candidate_run_path is None:
        default_candidate_run = args.candidate_dir / "candidate-run.json"
        if default_candidate_run.exists():
            candidate_run_path = default_candidate_run
    if candidate_run_path is not None and candidate_run_path.exists():
        candidate_run = json.loads(candidate_run_path.read_text(encoding="utf-8"))
        artifact_sha256["candidate/candidate-run.json"] = digest_file(
            candidate_run_path
        )

    final_target_met = runtime_pass and correctness_pass and performance_pass
    if not runtime_pass:
        decision = "reject-runtime-failure"
        exit_status = 4
    elif not correctness_pass:
        decision = (
            "hold-semantic-quality-regression"
            if semantic_control_enabled
            else "hold-exact-hash-drift"
        )
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
        "semantic_control_dir": (
            str(args.semantic_control_dir)
            if args.semantic_control_dir is not None
            else None
        ),
        "semantic_quality_thresholds": (
            {
                "max_mean_similarity_drop": args.max_mean_similarity_drop,
                "max_p50_similarity_drop": args.max_p50_similarity_drop,
                "max_exact_match_drop": args.max_exact_match_drop,
            }
            if semantic_control_enabled
            else None
        ),
        "runtime_gate_met": runtime_pass,
        "runtime_gate_status": (
            "complete-matrix" if runtime_pass else "partial-or-failed-matrix"
        ),
        "candidate_run_status": (
            candidate_run.get("status") if candidate_run is not None else None
        ),
        "candidate_failed_cell": (
            candidate_run.get("failed_cell") if candidate_run is not None else None
        ),
        "correctness_exact_hash_match": (
            exact_hash_pass if runtime_pass else None
        ),
        "semantic_quality_gate_met": (
            semantic_quality_pass
            if runtime_pass and semantic_control_enabled
            else None
        ),
        "correctness_gate_status": (
            "not-evaluable-runtime-failure"
            if not runtime_pass
            else "same-runtime-reference-quality-within-bounds"
            if semantic_control_enabled and correctness_pass
            else "semantic-quality-regression"
            if semantic_control_enabled
            else "exact-hash-reproducible"
            if exact_hash_pass
            else "semantic-business-check-required"
        ),
        "exact_hash_evidence_boundary": (
            "A fixed-runtime NPU4-7 control also differs from the immutable "
            "original. Cross-run response hashes are a reproducibility "
            "diagnostic, not sufficient evidence of semantic regression."
        ),
        "semantic_quality_evidence_boundary": (
            "When semantic_control_dir is set, the correctness gate compares "
            "privacy-safe aggregate answer similarity and exact-match counts "
            "with an unpruned control from the same runtime. No question, "
            "reference answer, or response text is written to artifacts."
            if semantic_control_enabled
            else None
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
