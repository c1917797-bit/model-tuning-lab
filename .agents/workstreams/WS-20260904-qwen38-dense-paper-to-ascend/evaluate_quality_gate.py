#!/usr/bin/env python3
"""Evaluate the A/B/C quality gate for a complete G1-G4 result JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


GROUPS = ("G1", "G2", "G3", "G4")
GROUP_SWITCHES = {
    "G1": {"native_optimization": False, "drrqr": False},
    "G2": {"native_optimization": True, "drrqr": False},
    "G3": {"native_optimization": False, "drrqr": True},
    "G4": {"native_optimization": True, "drrqr": True},
}
EXPECTED_DATASETS = {"NIAH+", "LongBench v2", "GSM8K", "CEval"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GLOBAL_BINDING_FIELDS = (
    "frozen_inputs_sha256",
    "invariant_config_sha256",
    "treatment_matrix_sha256",
)
ROW_EVIDENCE_HASH_FIELDS = (
    "checkpoint_manifest_sha256",
    "service_config_sha256",
    "per_sample_artifact_sha256",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--noise-threshold-pp", required=True, type=float)
    parser.add_argument("--noise-evidence", required=True, type=Path)
    parser.add_argument("--expected-repetitions", type=int, default=3)
    parser.add_argument("--minimum-models", type=int, default=2)
    parser.add_argument(
        "--expected-dataset",
        action="append",
        help="Repeat to override the default exact four-dataset suite (fixtures only).",
    )
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    if args.noise_threshold_pp < 0:
        raise ValueError("--noise-threshold-pp must be non-negative")
    if not args.noise_evidence.is_file() or args.noise_evidence.stat().st_size <= 0:
        raise ValueError("--noise-evidence must be an existing non-empty file")
    if args.expected_dataset and not args.fixture_mode:
        raise ValueError("--expected-dataset override requires --fixture-mode")
    expected_datasets = set(args.expected_dataset or EXPECTED_DATASETS)
    if not expected_datasets:
        raise ValueError("expected dataset set must not be empty")
    if args.minimum_models < 2:
        raise ValueError("--minimum-models must be at least 2")
    try:
        noise_document = json.loads(args.noise_evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid --noise-evidence JSON: {exc}") from exc
    if not isinstance(noise_document, dict):
        raise ValueError("--noise-evidence must contain one JSON object")
    try:
        evidence_noise_threshold = float(noise_document["noise_threshold_pp"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "--noise-evidence requires numeric noise_threshold_pp"
        ) from exc
    if (
        not math.isfinite(args.noise_threshold_pp)
        or not math.isfinite(evidence_noise_threshold)
        or evidence_noise_threshold < 0
    ):
        raise ValueError("noise thresholds must be finite and non-negative")
    if not math.isclose(
        args.noise_threshold_pp,
        evidence_noise_threshold,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(
            "--noise-threshold-pp must equal the value in --noise-evidence"
        )
    if args.fixture_mode:
        if noise_document.get("fixture_only") is not True:
            raise ValueError("fixture mode requires fixture_only noise evidence")
    elif noise_document.get("fixture_only") is not False:
        raise ValueError("production mode rejects fixture-only noise evidence")

    rows = [
        row
        for row in read_jsonl(args.results)
        if row.get("classification") == "warm"
    ]
    errors = []
    cells: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    global_bindings: dict[str, set[str]] = {
        field: set() for field in GLOBAL_BINDING_FIELDS
    }
    checkpoint_bindings: dict[tuple[str, str], set[str]] = defaultdict(set)
    service_bindings: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    service_instance_bindings: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    canary_input_bindings: dict[tuple[str, str], set[str]] = defaultdict(set)
    for index, row in enumerate(rows, 1):
        missing = [
            field
            for field in (
                "group",
                "model",
                "dataset",
                "run_index",
                "quality_score",
                "deterministic_canary_sha256",
            )
            if row.get(field) is None
        ]
        if missing:
            errors.append(f"warm row {index}: missing {', '.join(missing)}")
            continue
        if not args.fixture_mode:
            production_missing = [
                field
                for field in (
                    *GLOBAL_BINDING_FIELDS,
                    "deterministic_canary_input_sha256",
                    *ROW_EVIDENCE_HASH_FIELDS,
                    "phase",
                    "service_instance_id",
                    "native_optimization",
                    "drrqr",
                    "per_sample_artifact",
                )
                if row.get(field) is None
            ]
            if production_missing:
                errors.append(
                    f"warm row {index}: missing production evidence "
                    + ", ".join(production_missing)
                )
                continue
            if row["phase"] != "quality":
                errors.append(f"warm row {index}: phase must be quality")
                continue
            if not str(row["service_instance_id"]).strip():
                errors.append(f"warm row {index}: service_instance_id is empty")
                continue
            if row["group"] not in GROUP_SWITCHES:
                errors.append(f"warm row {index}: unknown group {row['group']!r}")
                continue
            switch_mismatches = [
                field
                for field, expected in GROUP_SWITCHES[row["group"]].items()
                if row[field] is not expected
            ]
            if switch_mismatches:
                errors.append(
                    f"warm row {index}: group switch mismatch: "
                    + ", ".join(switch_mismatches)
                )
                continue
        if (
            "deterministic_canary_output_tokens" not in row
            and not args.fixture_mode
        ):
            errors.append(
                f"warm row {index}: missing deterministic_canary_output_tokens"
            )
            continue
        try:
            canary_tokens = int(
                row.get("deterministic_canary_output_tokens", 512)
            )
            quality_score = float(row["quality_score"])
        except (TypeError, ValueError, OverflowError) as exc:
            errors.append(f"warm row {index}: invalid numeric field: {exc}")
            continue
        if not math.isfinite(quality_score):
            errors.append(f"warm row {index}: quality_score must be finite")
            continue
        canary_sha256 = str(row["deterministic_canary_sha256"])
        if not args.fixture_mode and not SHA256_RE.fullmatch(canary_sha256):
            errors.append(
                f"warm row {index}: deterministic_canary_sha256 must be "
                "64 lowercase hexadecimal characters"
            )
            continue
        if not args.fixture_mode:
            malformed_hash_fields = [
                field
                for field in (
                    *GLOBAL_BINDING_FIELDS,
                    "deterministic_canary_input_sha256",
                    *ROW_EVIDENCE_HASH_FIELDS,
                )
                if not SHA256_RE.fullmatch(str(row[field]))
            ]
            if malformed_hash_fields:
                errors.append(
                    f"warm row {index}: non-canonical evidence SHA256 fields: "
                    + ", ".join(malformed_hash_fields)
                )
                continue
            if not str(row["per_sample_artifact"]).strip():
                errors.append(f"warm row {index}: per_sample_artifact is empty")
                continue
        if args.fixture_mode:
            invalid_canary_tokens = canary_tokens < 0 or canary_tokens > 512
        else:
            invalid_canary_tokens = canary_tokens != 512
        if invalid_canary_tokens:
            errors.append(
                f"warm row {index}: deterministic canary output tokens "
                f"{canary_tokens} must be "
                + ("within 0..512 in fixture mode" if args.fixture_mode else "exactly 512")
            )
            continue
        cell_key = (row["group"], str(row["model"]), str(row["dataset"]))
        cells[cell_key].append(row)
        if not args.fixture_mode:
            for field in GLOBAL_BINDING_FIELDS:
                global_bindings[field].add(str(row[field]))
            checkpoint_bindings[
                (str(row["group"]), str(row["model"]))
            ].add(str(row["checkpoint_manifest_sha256"]))
            service_bindings[cell_key].add(str(row["service_config_sha256"]))
            service_instance_bindings[cell_key].add(
                str(row["service_instance_id"])
            )
            canary_input_bindings[
                (str(row["model"]), str(row["dataset"]))
            ].add(str(row["deterministic_canary_input_sha256"]))

    if not args.fixture_mode:
        for field, values in global_bindings.items():
            if len(values) != 1:
                errors.append(
                    f"all warm rows must share exactly one {field}; "
                    f"observed={sorted(values)}"
                )
        for key, values in sorted(checkpoint_bindings.items()):
            if len(values) != 1:
                errors.append(
                    f"{key}: checkpoint_manifest_sha256 changed across rows"
                )
        for key, values in sorted(service_bindings.items()):
            if len(values) != 1:
                errors.append(f"{key}: service_config_sha256 changed across runs")
        for key, values in sorted(service_instance_bindings.items()):
            if len(values) != 1:
                errors.append(f"{key}: service_instance_id changed across runs")
        for key, values in sorted(canary_input_bindings.items()):
            if len(values) != 1:
                errors.append(
                    f"{key}: deterministic_canary_input_sha256 changed "
                    "across groups or runs"
                )

    models = sorted({key[1] for key in cells})
    datasets = sorted({key[2] for key in cells})
    if len(models) < args.minimum_models:
        errors.append(
            f"quality gate requires at least {args.minimum_models} models; observed={models}"
        )
    if set(datasets) != expected_datasets:
        errors.append(
            f"quality datasets must be exactly {sorted(expected_datasets)}; observed={datasets}"
        )
    expected_runs = set(range(1, args.expected_repetitions + 1))
    recomputed_noise_threshold = None
    if not args.fixture_mode:
        if noise_document.get("schema") != "paper-to-ascend-g1-noise/v1":
            errors.append("noise evidence schema must be paper-to-ascend-g1-noise/v1")
        if noise_document.get("method") != "max_within_cell_range_pp":
            errors.append("noise evidence method must be max_within_cell_range_pp")
        if noise_document.get("expected_repetitions") != args.expected_repetitions:
            errors.append(
                "noise evidence expected_repetitions differs from quality gate"
            )
        if noise_document.get("source_quality_results_sha256") != sha256(
            args.results
        ):
            errors.append(
                "noise evidence source quality-results SHA256 differs "
                "from --results"
            )
        quality_binding_values = {
            field: next(iter(values), None)
            for field, values in global_bindings.items()
        }
        if noise_document.get("global_bindings") != quality_binding_values:
            errors.append("noise evidence global bindings differ from quality rows")
        observations = noise_document.get("observations")
        if not isinstance(observations, list):
            errors.append("noise evidence observations must be a list")
        else:
            noise_cells: dict[tuple[str, str], list[tuple[int, float]]] = defaultdict(list)
            for index, observation in enumerate(observations, 1):
                try:
                    if observation.get("group") != "G1":
                        raise ValueError("group must be G1")
                    key = (str(observation["model"]), str(observation["dataset"]))
                    run_index = int(observation["run_index"])
                    score = float(observation["quality_score"])
                    if not math.isfinite(score):
                        raise ValueError("quality_score must be finite")
                    noise_cells[key].append((run_index, score))
                except (AttributeError, KeyError, TypeError, ValueError, OverflowError) as exc:
                    errors.append(f"noise observation {index}: {exc}")
            expected_noise_scope = {
                (model, dataset) for model in models for dataset in datasets
            }
            if set(noise_cells) != expected_noise_scope:
                errors.append(
                    "noise evidence model/dataset scope differs from quality rows"
                )
            quality_g1_cells = {
                (model, dataset): sorted(
                    (
                        int(row["run_index"]),
                        float(row["quality_score"]),
                    )
                    for row in cells.get(("G1", model, dataset), [])
                )
                for model, dataset in expected_noise_scope
            }
            for key in sorted(expected_noise_scope):
                observed_pairs = sorted(noise_cells.get(key, []))
                if observed_pairs != quality_g1_cells[key]:
                    errors.append(
                        f"noise {key}: observations differ from quality G1 rows"
                    )
            ranges = []
            for key, values in sorted(noise_cells.items()):
                runs = [run for run, _ in values]
                scores = [score for _, score in values]
                if (
                    set(runs) != expected_runs
                    or len(values) != len(expected_runs)
                ):
                    errors.append(
                        f"noise {key}: repetitions {sorted(set(runs))} with "
                        f"{len(values)} rows != {sorted(expected_runs)}"
                    )
                    continue
                ranges.append(max(scores) - min(scores))
            if ranges:
                recomputed_noise_threshold = max(ranges)
                if not math.isclose(
                    recomputed_noise_threshold,
                    evidence_noise_threshold,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                ):
                    errors.append(
                        "noise_threshold_pp does not equal recomputed "
                        "max within-cell G1 range"
                    )
    for model in models:
        for dataset in datasets:
            for group in GROUPS:
                key = (group, model, dataset)
                if key not in cells:
                    errors.append(f"missing quality cell: {key}")
                    continue
                observed = {int(row["run_index"]) for row in cells[key]}
                if observed != expected_runs or len(cells[key]) != len(expected_runs):
                    errors.append(
                        f"{key}: repetitions {sorted(observed)} with "
                        f"{len(cells[key])} rows != {sorted(expected_runs)}"
                    )

    decisions = []
    for model in models:
        for dataset in datasets:
            baseline = cells.get(("G1", model, dataset))
            if not baseline:
                continue
            baseline_scores = [float(row["quality_score"]) for row in baseline]
            baseline_canaries = {
                str(row["deterministic_canary_sha256"]) for row in baseline
            }
            baseline_canary_stable = len(baseline_canaries) == 1
            baseline_mean = statistics.fmean(baseline_scores)
            for group in GROUPS[1:]:
                treatment = cells.get((group, model, dataset))
                if not treatment:
                    continue
                treatment_scores = [
                    float(row["quality_score"]) for row in treatment
                ]
                treatment_canaries = {
                    str(row["deterministic_canary_sha256"]) for row in treatment
                }
                shared_discrete = bool(
                    set(baseline_scores).intersection(treatment_scores)
                )
                treatment_mean = statistics.fmean(treatment_scores)
                delta_pp = treatment_mean - baseline_mean
                within_noise = abs(delta_pp) <= args.noise_threshold_pp
                canary_stable = len(treatment_canaries) == 1
                canary_equal = (
                    baseline_canary_stable
                    and canary_stable
                    and baseline_canaries == treatment_canaries
                )
                passed = shared_discrete and within_noise and canary_equal
                decisions.append(
                    {
                        "model": model,
                        "dataset": dataset,
                        "group": group,
                        "condition_A_shared_discrete_score": shared_discrete,
                        "condition_B_delta_pp": delta_pp,
                        "condition_B_within_measured_noise": within_noise,
                        "condition_C_baseline_zero_variance": baseline_canary_stable,
                        "condition_C_treatment_zero_variance": canary_stable,
                        "condition_C_exactly_equal_to_G1": canary_equal,
                        "passed": passed,
                    }
                )

    gate_passed = not errors and bool(decisions) and all(
        item["passed"] for item in decisions
    )
    report = {
        "schema": "paper-to-ascend-quality-gate/v1",
        "passed": gate_passed,
        "noise_threshold_pp": args.noise_threshold_pp,
        "noise_evidence_path": str(args.noise_evidence.resolve()),
        "noise_evidence_sha256": sha256(args.noise_evidence),
        "noise_method": noise_document.get("method"),
        "recomputed_noise_threshold_pp": recomputed_noise_threshold,
        "minimum_models": args.minimum_models,
        "expected_datasets": sorted(expected_datasets),
        "fixture_mode": args.fixture_mode,
        "global_bindings": (
            {
                field: next(iter(values), None)
                for field, values in global_bindings.items()
            }
            if not args.fixture_mode
            else None
        ),
        "service_config_bindings": (
            {
                "|".join(key): next(iter(values), None)
                for key, values in sorted(service_bindings.items())
            }
            if not args.fixture_mode
            else None
        ),
        "checkpoint_manifest_bindings": (
            {
                "|".join(key): next(iter(values), None)
                for key, values in sorted(checkpoint_bindings.items())
            }
            if not args.fixture_mode
            else None
        ),
        "errors": errors,
        "decisions": decisions,
        "allowed_claim": (
            (
                "fixture-only quality gate pass"
                if args.fixture_mode
                else "accuracy lossless within measured NPU noise on this frozen suite"
            )
            if gate_passed
            else None
        ),
    }
    atomic_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if gate_passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
