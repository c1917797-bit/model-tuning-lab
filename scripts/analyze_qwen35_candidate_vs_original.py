#!/usr/bin/env python3
"""Compare a repeated quick32 candidate with the immutable frozen baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

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


def cell_path(
    root: Path,
    concurrency: int,
    repeat_index: int = 1,
    *,
    original: bool = False,
) -> Path:
    legacy = root / f"c{concurrency}-r{repeat_index}.json"
    if original:
        return legacy
    matrix_native = root / f"c{concurrency}" / f"repeat-{repeat_index}.json"
    if matrix_native.exists() or not legacy.exists():
        return matrix_native
    return legacy


def load_cell(
    root: Path,
    concurrency: int,
    repeat_index: int = 1,
    *,
    original: bool,
    require_success: bool = True,
) -> dict:
    path = cell_path(
        root, concurrency, repeat_index, original=original
    )
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
        "repeat_index": repeat_index,
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
        for percentile in ("p50", "p95", "p99"):
            value = row.get(metric, {}).get(percentile)
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{path}: invalid {metric}.{percentile}")
    return row


def load_quality_decision(path: Path, candidate_id: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema": "qwen35-quality-human-decision/v1",
        "candidate_id": candidate_id,
        "dataset_sha256": EXPECTED_IDENTITY["dataset_sha256"],
        "control_scope": "same-runtime-retained-cumulative-control",
        "decision": "pass",
        "material_regressions": 0,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {payload.get(key)!r}"
            )
    samples = payload.get("samples")
    if not isinstance(samples, int) or samples < 32:
        raise ValueError(f"{path}: samples must be at least 32")
    if payload.get("equivalent_samples") != samples:
        raise ValueError(f"{path}: every sample must be equivalent")
    if not payload.get("reviewer") or not payload.get("reviewed_at_utc"):
        raise ValueError(f"{path}: reviewer and reviewed_at_utc are required")
    verified_artifacts = {}
    for name in ("baseline_capture", "candidate_capture", "comparison"):
        record = payload.get(name)
        if not isinstance(record, dict):
            raise ValueError(f"{path}: missing {name} artifact")
        artifact_path = Path(str(record.get("path", "")))
        expected_sha256 = record.get("sha256")
        if not artifact_path.is_file():
            raise ValueError(f"{path}: missing {name} file {artifact_path}")
        actual_sha256 = digest_file(artifact_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"{path}: {name} SHA256 mismatch; "
                f"expected {expected_sha256}, got {actual_sha256}"
            )
        verified_artifacts[name] = {
            "path": str(artifact_path),
            "sha256": actual_sha256,
        }
    comparison = json.loads(
        Path(verified_artifacts["comparison"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    if comparison.get("schema") != "qwen35-quality-paired-comparison/v1":
        raise ValueError(f"{path}: invalid paired comparison schema")
    if comparison.get("dataset_sha256") != EXPECTED_IDENTITY["dataset_sha256"]:
        raise ValueError(f"{path}: paired comparison dataset mismatch")
    if comparison.get("samples") != samples:
        raise ValueError(f"{path}: paired comparison sample count mismatch")
    expected_differences = samples - int(comparison.get("exact_matches", -1))
    if payload.get("reviewed_differences") != expected_differences:
        raise ValueError(f"{path}: not every differing response was reviewed")
    return {
        "path": str(path),
        "sha256": digest_file(path),
        "samples": samples,
        "equivalent_samples": payload["equivalent_samples"],
        "material_regressions": payload["material_regressions"],
        "reviewed_differences": payload["reviewed_differences"],
        "reviewer": payload["reviewer"],
        "reviewed_at_utc": payload["reviewed_at_utc"],
        "artifacts": verified_artifacts,
    }


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
    parser.add_argument("--target-ratio", type=float, default=2.0 / 3.0)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--p99-max-ratio",
        type=float,
        default=1.0,
        help="maximum candidate/baseline ratio for median per-run P99",
    )
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
    parser.add_argument(
        "--quality-decision",
        type=Path,
        help="paired human quality decision used when exact hashes drift",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 < args.target_ratio <= 1:
        raise ValueError("target ratio must be in (0, 1]")
    if args.repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if args.p99_max_ratio <= 0:
        raise ValueError("P99 maximum ratio must be positive")

    cells: dict[str, dict] = {}
    artifact_sha256: dict[str, str] = {}
    correctness_pass = True
    performance_pass = True
    runtime_pass = True
    for concurrency in CONCURRENCIES:
        original_path = cell_path(
            args.original_dir, concurrency, 1, original=True
        )
        original = load_cell(
            args.original_dir, concurrency, 1, original=True
        )
        artifact_sha256[f"original/c{concurrency}-r1.json"] = digest_file(
            original_path
        )
        repetitions = []
        missing_paths = []
        for repeat_index in range(1, args.repetitions + 1):
            candidate_path = cell_path(
                args.candidate_dir, concurrency, repeat_index
            )
            if not candidate_path.exists():
                missing_paths.append(str(candidate_path))
                continue
            candidate = load_cell(
                args.candidate_dir,
                concurrency,
                repeat_index,
                original=False,
                require_success=not args.allow_incomplete,
            )
            candidate_success = (
                candidate.get("errors") == 0
                and candidate.get("completed") == 32
                and candidate.get("finish_reasons") == {"stop": 32}
                and len(candidate["response_sha256"]) == 32
            )
            mismatches = sum(
                left != right
                for left, right in zip(
                    original["response_sha256"],
                    candidate["response_sha256"],
                )
            )
            repetitions.append(
                {
                    "repeat_index": repeat_index,
                    "success": candidate_success,
                    "response_hash_mismatches": mismatches,
                    "ttft_p50_ms": float(candidate["ttft_ms"]["p50"]),
                    "tpot_p50_ms": float(candidate["tpot_ms"]["p50"]),
                    "ttft_p95_ms": float(candidate["ttft_ms"]["p95"]),
                    "tpot_p95_ms": float(candidate["tpot_ms"]["p95"]),
                    "ttft_p99_ms": float(candidate["ttft_ms"]["p99"]),
                    "tpot_p99_ms": float(candidate["tpot_ms"]["p99"]),
                }
            )
            artifact_sha256[
                f"candidate/c{concurrency}-r{repeat_index}.json"
            ] = digest_file(candidate_path)
        if missing_paths:
            if not args.allow_incomplete:
                raise FileNotFoundError(missing_paths[0])
            runtime_pass = False
            performance_pass = False
            correctness_pass = False
            cells[str(concurrency)] = {
                "status": "not-run",
                "measurement_valid": False,
                "runtime_gate_met": False,
                "performance_target_met": False,
                "correctness_exact_hash_match": None,
                "missing_artifacts": missing_paths,
                "repetitions": repetitions,
            }
            continue
        candidate_success = all(row["success"] for row in repetitions)
        runtime_pass = runtime_pass and candidate_success
        mismatches = sum(
            row["response_hash_mismatches"] for row in repetitions
        )
        cell_correct = mismatches == 0 if candidate_success else None
        correctness_pass = correctness_pass and bool(cell_correct)
        original_ttft_p50 = float(original["ttft_ms"]["p50"])
        candidate_ttft_p50 = median(
            row["ttft_p50_ms"] for row in repetitions
        )
        original_tpot_p50 = float(original["tpot_ms"]["p50"])
        candidate_tpot_p50 = median(
            row["tpot_p50_ms"] for row in repetitions
        )
        original_ttft = float(original["ttft_ms"]["p95"])
        candidate_ttft = median(row["ttft_p95_ms"] for row in repetitions)
        original_tpot = float(original["tpot_ms"]["p95"])
        candidate_tpot = median(row["tpot_p95_ms"] for row in repetitions)
        original_ttft_p99 = float(original["ttft_ms"]["p99"])
        candidate_ttft_p99 = median(
            row["ttft_p99_ms"] for row in repetitions
        )
        original_tpot_p99 = float(original["tpot_ms"]["p99"])
        candidate_tpot_p99 = median(
            row["tpot_p99_ms"] for row in repetitions
        )
        ttft_ratio = candidate_ttft / original_ttft
        tpot_ratio = candidate_tpot / original_tpot
        ttft_p99_ratio = candidate_ttft_p99 / original_ttft_p99
        tpot_p99_ratio = candidate_tpot_p99 / original_tpot_p99
        p99_guard_met = (
            ttft_p99_ratio <= args.p99_max_ratio
            and tpot_p99_ratio <= args.p99_max_ratio
        )
        cell_performance_pass = candidate_success and (
            ttft_ratio <= args.target_ratio
            and tpot_ratio <= args.target_ratio
            and p99_guard_met
        )
        performance_pass = performance_pass and cell_performance_pass
        cells[str(concurrency)] = {
            "status": "complete" if candidate_success else "failed",
            "measurement_valid": candidate_success,
            "runtime_gate_met": candidate_success,
            "repetitions": repetitions,
            "original_ttft_p50_ms": original_ttft_p50,
            "candidate_median_ttft_p50_ms": candidate_ttft_p50,
            "ttft_p50_ratio": candidate_ttft_p50 / original_ttft_p50,
            "original_tpot_p50_ms": original_tpot_p50,
            "candidate_median_tpot_p50_ms": candidate_tpot_p50,
            "tpot_p50_ratio": candidate_tpot_p50 / original_tpot_p50,
            "original_ttft_p95_ms": original_ttft,
            "candidate_median_ttft_p95_ms": candidate_ttft,
            "ttft_p95_ratio": ttft_ratio,
            "ttft_p95_improvement_x": original_ttft / candidate_ttft,
            "original_tpot_p95_ms": original_tpot,
            "candidate_median_tpot_p95_ms": candidate_tpot,
            "tpot_p95_ratio": tpot_ratio,
            "tpot_p95_improvement_x": original_tpot / candidate_tpot,
            "original_ttft_p99_ms": original_ttft_p99,
            "candidate_median_ttft_p99_ms": candidate_ttft_p99,
            "ttft_p99_ratio": ttft_p99_ratio,
            "original_tpot_p99_ms": original_tpot_p99,
            "candidate_median_tpot_p99_ms": candidate_tpot_p99,
            "tpot_p99_ratio": tpot_p99_ratio,
            "p99_guard_met": p99_guard_met,
            "response_hash_mismatches_observed": mismatches,
            # Preserve the v1 complete-cell field for existing consumers. Partial
            # cells additionally carry the explicit observed qualifier above.
            "response_hash_mismatches": mismatches if candidate_success else None,
            "correctness_exact_hash_match": cell_correct,
            "performance_target_met": cell_performance_pass,
        }

    candidate_run = None
    candidate_run_path = args.candidate_run
    if candidate_run_path is None:
        for manifest_name in ("matrix-run.json", "candidate-run.json"):
            default_candidate_run = args.candidate_dir / manifest_name
            if default_candidate_run.exists():
                candidate_run_path = default_candidate_run
                break
    if candidate_run_path is not None and candidate_run_path.exists():
        candidate_run = json.loads(candidate_run_path.read_text(encoding="utf-8"))
        artifact_sha256["candidate/candidate-run.json"] = digest_file(
            candidate_run_path
        )

    quality_decision = None
    quality_pass = correctness_pass
    if args.quality_decision is not None:
        quality_decision = load_quality_decision(
            args.quality_decision, args.candidate_id
        )
        artifact_sha256["quality/decision.json"] = quality_decision["sha256"]
        quality_pass = True
    final_target_met = runtime_pass and quality_pass and performance_pass
    if not runtime_pass:
        decision = "reject-runtime-failure"
        exit_status = 4
    elif not performance_pass:
        decision = "iterate"
        exit_status = 2
    elif not quality_pass:
        decision = "hold-quality-unproven"
        exit_status = 3
    elif final_target_met:
        decision = "final-target-met"
        exit_status = 0
    else:
        raise AssertionError("unreachable decision state")
    report = {
        "schema": "qwen35-candidate-vs-fixed-original-decision/v2",
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
        "repetitions": args.repetitions,
        "aggregation": "median of per-run P95/P99 values",
        "p99_max_ratio": args.p99_max_ratio,
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
            correctness_pass if runtime_pass else None
        ),
        "quality_gate_met": quality_pass if runtime_pass else None,
        "quality_decision": quality_decision,
        "correctness_gate_status": (
            "not-evaluable-runtime-failure"
            if not runtime_pass
            else "paired-human-review-pass"
            if quality_decision is not None
            else "exact-hash-reproducible"
            if correctness_pass
            else "paired-human-review-required"
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
