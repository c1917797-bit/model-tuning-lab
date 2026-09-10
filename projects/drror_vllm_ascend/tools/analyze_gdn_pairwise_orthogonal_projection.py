#!/usr/bin/env python3
"""Core numerical machinery for Pairwise Orthonormal Recurrent Projection.

This module deliberately contains no NPU or endpoint benchmark path.  It builds
an at-most-two-sparse orthonormal Dk64 basis from frozen dense GDN trajectories
and replays the reduced recurrence on CPU as an admission pre-screen.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import linear_sum_assignment
import torch

from tools.analyze_gdn_recurrent_transition_selector import (
    ARCHIVE_SET_SHA256,
    BASELINE_PLAN_SHA256,
    CAPTURE_AUDIT_SHA256,
    LAYERS,
    TARGET,
    VALUE_HEADS_PER_KEY_HEAD,
    WIDTH,
    add_metrics,
    aggregate,
    digest,
    evaluate_dense_from_sequences,
    evaluate_indices_from_sequences,
    finalize_metrics,
    head_tensors,
    load_sequence,
    local_baseline_indices,
    normalize,
    publish,
    rms_gated,
    validate_inputs,
    zero_metrics,
)

SCHEMA = "drrqr-pairwise-orthogonal-projection/v1"
CV_FOLDS = (
    {"validation": (0, 3, 6, 9), "train": (1, 2, 4, 5, 7, 8, 10, 11)},
    {"validation": (1, 4, 7, 10), "train": (0, 2, 3, 5, 6, 8, 9, 11)},
    {"validation": (2, 5, 8, 11), "train": (0, 1, 3, 4, 6, 7, 9, 10)},
)


def _normalized_psd(gram: torch.Tensor) -> torch.Tensor:
    gram = gram.to(dtype=torch.float64)
    if gram.shape != (WIDTH, WIDTH):
        raise ValueError(f"expected {WIDTH}x{WIDTH} Gram, got {tuple(gram.shape)}")
    gram = (gram + gram.T) * 0.5
    if not torch.isfinite(gram).all():
        raise ValueError("non-finite Gram")
    trace = float(torch.trace(gram))
    if trace <= 0.0:
        raise ValueError("positive Gram trace required")
    result = gram / trace
    minimum = float(torch.linalg.eigvalsh(result)[0])
    if minimum < -1e-10:
        raise ValueError(f"Gram is not positive semidefinite: {minimum}")
    return result


def transition_gram_components_from_sequences(sequences, head: int):
    """Return additive unnormalized read/feedback/write influence Grams."""
    grams = {
        "read": torch.zeros((WIDTH, WIDTH), dtype=torch.float64),
        "feedback": torch.zeros((WIDTH, WIDTH), dtype=torch.float64),
        "write": torch.zeros((WIDTH, WIDTH), dtype=torch.float64),
    }
    observations = {name: 0 for name in grams}
    for records in sequences:
        for record in records:
            item = head_tensors(record, head)
            q = normalize(item["q"])
            k = normalize(item["k"])

            read_signature = (
                item["state_final"].float() * q[-1][None, None, :]
            ).reshape(-1, WIDTH).double()
            grams["read"] += read_signature.T @ read_signature
            observations["read"] += read_signature.shape[0]

            if record["step"] == 0:
                write_signature = item["state_final"].float()
            else:
                alpha = item["g"][0].float().exp()
                decayed = alpha[:, None, None] * item["state_initial"].float()
                write_signature = item["state_final"].float() - decayed
                feedback_signature = (
                    decayed * k[0][None, None, :]
                ).reshape(-1, WIDTH).double()
                grams["feedback"] += feedback_signature.T @ feedback_signature
                observations["feedback"] += feedback_signature.shape[0]
            write_signature = write_signature.reshape(-1, WIDTH).double()
            grams["write"] += write_signature.T @ write_signature
            observations["write"] += write_signature.shape[0]

    return grams, observations


def combine_transition_gram_components(component_rows) -> tuple[torch.Tensor, dict]:
    grams = {
        name: sum(
            (row[0][name] for row in component_rows),
            torch.zeros((WIDTH, WIDTH), dtype=torch.float64),
        )
        for name in ("read", "feedback", "write")
    }
    observations = {
        name: sum(row[1][name] for row in component_rows)
        for name in grams
    }
    normalized = {name: _normalized_psd(value) for name, value in grams.items()}
    combined = sum(normalized.values(), torch.zeros_like(normalized["read"]))
    combined = (combined + combined.T) * 0.5
    return combined, {
        "component_traces_after_normalization": {
            name: float(torch.trace(value)) for name, value in normalized.items()
        },
        "observations": observations,
        "combined_trace": float(torch.trace(combined)),
    }


def transition_gram_from_sequences(sequences, head: int) -> tuple[torch.Tensor, dict]:
    """Return the fixed equal-weight read/feedback/write influence Gram."""
    return combine_transition_gram_components(
        [transition_gram_components_from_sequences(sequences, head)]
    )


def one_hot_transform(selected: torch.Tensor) -> torch.Tensor:
    selected = torch.as_tensor(selected, dtype=torch.long)
    if selected.shape != (TARGET,) or selected.unique().numel() != TARGET:
        raise ValueError("exactly 64 unique baseline coordinates required")
    if int(selected.min()) < 0 or int(selected.max()) >= WIDTH:
        raise ValueError("baseline coordinate outside Dk128")
    result = torch.zeros((WIDTH, TARGET), dtype=torch.float64)
    result[selected, torch.arange(TARGET)] = 1.0
    return result


def pairwise_transform(
    gram: torch.Tensor, baseline: torch.Tensor
) -> tuple[torch.Tensor, dict]:
    """Pair each energy anchor with one discarded coordinate and keep rank one."""
    gram = _normalized_psd(gram)
    anchors = torch.as_tensor(baseline, dtype=torch.long).sort().values
    if anchors.shape != (TARGET,) or anchors.unique().numel() != TARGET:
        raise ValueError("exactly 64 unique anchors required")
    mask = torch.zeros(WIDTH, dtype=torch.bool)
    mask[anchors] = True
    partners = torch.arange(WIDTH, dtype=torch.long)[~mask]
    if partners.shape != (TARGET,):
        raise AssertionError("Dk128 to Dk64 requires 64 discarded coordinates")

    residual = np.empty((TARGET, TARGET), dtype=np.float64)
    improvement = np.empty_like(residual)
    for row, anchor in enumerate(anchors.tolist()):
        for column, partner in enumerate(partners.tolist()):
            block = gram[[anchor, partner]][:, [anchor, partner]]
            eigenvalues = torch.linalg.eigvalsh(block)
            residual[row, column] = float(eigenvalues[0])
            improvement[row, column] = float(gram[partner, partner]) - residual[row, column]

    # scipy's implementation is deterministic for a fixed dense cost matrix.
    # Sorted anchor/partner arrays make its stable result the declared tie order.
    assigned_rows, assigned_columns = linear_sum_assignment(-improvement)
    if not np.array_equal(assigned_rows, np.arange(TARGET)):
        raise AssertionError("assignment must cover every anchor in order")

    transform = torch.zeros((WIDTH, TARGET), dtype=torch.float64)
    pairs = []
    for output, (row, partner_column) in enumerate(
        zip(assigned_rows.tolist(), assigned_columns.tolist())
    ):
        anchor = int(anchors[row])
        partner = int(partners[partner_column])
        block = gram[[anchor, partner]][:, [anchor, partner]]
        eigenvalues, eigenvectors = torch.linalg.eigh(block)
        direction = eigenvectors[:, 1]
        if float(direction[0]) < 0.0 or (
            float(direction[0]) == 0.0 and float(direction[1]) < 0.0
        ):
            direction = -direction
        transform[anchor, output] = direction[0]
        transform[partner, output] = direction[1]
        pairs.append({
            "anchor": anchor,
            "partner": partner,
            "anchor_coefficient": float(direction[0]),
            "partner_coefficient": float(direction[1]),
            "retained_eigenvalue": float(eigenvalues[1]),
            "residual_eigenvalue": float(eigenvalues[0]),
            "improvement_over_dropping_partner": float(
                improvement[row, partner_column]
            ),
        })

    identity_error = float(
        (transform.T @ transform - torch.eye(TARGET, dtype=torch.float64))
        .abs().max()
    )
    support_counts = (transform.abs() > 0.0).sum(dim=0)
    if identity_error > 1e-12:
        raise AssertionError(f"non-orthonormal transform: {identity_error}")
    if int(support_counts.max()) > 2 or int(support_counts.min()) < 1:
        raise AssertionError("every output must have one or two nonzeros")
    if len({item["partner"] for item in pairs}) != TARGET:
        raise AssertionError("partner assignment is not one-to-one")
    return transform, {
        "pairs": pairs,
        "orthonormal_max_abs_error": identity_error,
        "minimum_support": int(support_counts.min()),
        "maximum_support": int(support_counts.max()),
        "total_pairing_improvement": float(sum(
            item["improvement_over_dropping_partner"] for item in pairs
        )),
    }


def project_and_normalize(raw: torch.Tensor, transform: torch.Tensor) -> torch.Tensor:
    if raw.shape[-1] != WIDTH or transform.shape != (WIDTH, TARGET):
        raise ValueError("projection geometry")
    return normalize(raw.float() @ transform.float())


def replay_projection(records, head: int, transform: torch.Tensor) -> dict:
    transform = transform.float()
    if transform.shape != (WIDTH, TARGET):
        raise ValueError("Dk128 to Dk64 transform required")
    if not torch.isfinite(transform).all():
        raise ValueError("finite transform required")
    state = torch.zeros(
        VALUE_HEADS_PER_KEY_HEAD, WIDTH, TARGET, dtype=torch.float32
    )
    metrics = zero_metrics()
    for record in records:
        item = head_tensors(record, head)
        q = project_and_normalize(item["q"], transform)
        k = project_and_normalize(item["k"], transform)
        for token in range(q.shape[0]):
            alpha = item["g"][token].float().exp()
            beta = item["beta"][token].float()
            state = alpha[:, None, None] * state
            residual = item["v"][token].float() - torch.einsum(
                "hdk,k->hd", state, k[token]
            )
            state = state + (
                beta[:, None, None]
                * residual[:, :, None]
                * k[token][None, None, :]
            )
            output = (
                torch.einsum("hdk,k->hd", state, q[token])
                * (TARGET ** -0.5)
            ).to(torch.bfloat16).float()
            expected = item["operator"][token].float()
            post = rms_gated(output, item["z"][token], item["weight"])
            expected_post = item["norm_output"][token].float()
            metrics["operator_error2"] += float((output - expected).square().sum())
            metrics["operator_reference2"] += float(expected.square().sum())
            metrics["operator_elements"] += expected.numel()
            metrics["post_rms_error2"] += float((post - expected_post).square().sum())
            metrics["post_rms_reference2"] += float(expected_post.square().sum())
            metrics["post_rms_elements"] += expected_post.numel()
        expected_state = torch.einsum(
            "hdk,kr->hdr", item["state_final"].float(), transform
        )
        state_error2 = float((state - expected_state).square().sum())
        state_reference2 = float(expected_state.square().sum())
        metrics["state_error2"] += state_error2
        metrics["state_reference2"] += state_reference2
        metrics["state_elements"] += expected_state.numel()
        metrics["max_state_checkpoint_relative_l2"] = max(
            metrics["max_state_checkpoint_relative_l2"],
            math.sqrt(state_error2 / max(state_reference2, 1e-30)),
        )
    return metrics


def evaluate_projection_from_sequences(sequences, head: int, transform: torch.Tensor):
    metrics = zero_metrics()
    for records in sequences:
        add_metrics(metrics, replay_projection(records, head, transform))
    return finalize_metrics(metrics)


def static_decode_operation_count() -> dict:
    projection = 2 * 4 * TARGET * 3
    removed_per_width = WIDTH - TARGET
    decay = 12 * WIDTH * removed_per_width
    feedback_matvec = 12 * WIDTH * removed_per_width * 2
    state_update = 12 * WIDTH * removed_per_width * 3
    readout = 12 * WIDTH * removed_per_width * 2
    removed = decay + feedback_matvec + state_update + readout
    return {
        "projection_scalar_ops": projection,
        "estimated_recurrent_scalar_ops_removed": removed,
        "projection_over_removed_ratio": projection / removed,
        "claim": "Static arithmetic screen only; not latency or endpoint performance.",
    }


def _aggregate_metric_values(values):
    return aggregate([{"metrics": value} for value in values], "metrics")


def run(capture_root, audit_path, baseline_plan_path, output_dir):
    capture_root = Path(capture_root).resolve()
    audit_path = Path(audit_path).resolve()
    baseline_plan_path = Path(baseline_plan_path).resolve()
    output_dir = Path(output_dir).resolve()
    if (
        not str(output_dir).startswith("/drrqr-results/")
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        raise ValueError("fresh output below /drrqr-results required")
    capture, _, plan = validate_inputs(
        capture_root, audit_path, baseline_plan_path
    )
    output_dir.mkdir(parents=False, exist_ok=False)
    publish(output_dir / "started.json", {
        "schema": SCHEMA,
        "status": "running",
        "claim": (
            "CPU cross-validation over prior calibration rows only; no NPU, "
            "endpoint-performance, task-accuracy or portability claim."
        ),
        "cross_validation": [
            {name: list(values) for name, values in fold.items()}
            for fold in CV_FOLDS
        ],
        "prohibited_as_fresh_admission": [12, 13, 14, 15],
        "script_sha256": digest(__file__),
        "started_unix_ns": time.time_ns(),
    })

    candidate_rows = []
    baseline_rows = []
    dense_rows = []
    fold_candidate_rows = defaultdict(list)
    fold_baseline_rows = defaultdict(list)
    per_head_candidate = defaultdict(list)
    per_head_baseline = defaultdict(list)
    transform_document = {
        "schema": SCHEMA,
        "status": "cross_validation_transforms",
        "baseline_plan_sha256": BASELINE_PLAN_SHA256,
        "folds": [],
    }
    all_transform_gates = []
    for layer in LAYERS:
        for rank in range(4):
            sequences = {
                index: load_sequence(capture, index, rank, layer)
                for index in range(12)
            }
            for head in range(4):
                key = f"layer{layer}.rank{rank}.head{head}"
                per_sequence_components = {
                    index: transition_gram_components_from_sequences(
                        [records], head
                    )
                    for index, records in sequences.items()
                }
                baseline = local_baseline_indices(plan, layer, rank, head)
                baseline_transform = one_hot_transform(baseline)
                baseline_identity = (
                    int((baseline_transform != 0).sum()) == TARGET
                    and torch.equal(
                        baseline_transform[baseline, torch.arange(TARGET)],
                        torch.ones(TARGET, dtype=torch.float64),
                    )
                )
                if not baseline_identity:
                    raise AssertionError("energy baseline transform identity")
                for fold_index, fold in enumerate(CV_FOLDS):
                    train_components = [
                        per_sequence_components[index]
                        for index in fold["train"]
                    ]
                    gram, gram_metadata = combine_transition_gram_components(
                        train_components
                    )
                    transform, transform_metadata = pairwise_transform(
                        gram, baseline
                    )
                    validation_sequences = [
                        sequences[index] for index in fold["validation"]
                    ]
                    candidate_metrics = evaluate_projection_from_sequences(
                        validation_sequences, head, transform
                    )
                    baseline_metrics = evaluate_indices_from_sequences(
                        validation_sequences, head, baseline
                    )
                    dense_metrics = evaluate_dense_from_sequences(
                        validation_sequences, head
                    )
                    candidate_rows.append(candidate_metrics)
                    baseline_rows.append(baseline_metrics)
                    dense_rows.append(dense_metrics)
                    fold_candidate_rows[fold_index].append(candidate_metrics)
                    fold_baseline_rows[fold_index].append(baseline_metrics)
                    per_head_candidate[key].append(candidate_metrics)
                    per_head_baseline[key].append(baseline_metrics)
                    transform_ok = (
                        transform_metadata["orthonormal_max_abs_error"] <= 1e-12
                        and transform_metadata["maximum_support"] <= 2
                        and transform_metadata["minimum_support"] >= 1
                        and len(transform_metadata["pairs"]) == TARGET
                    )
                    all_transform_gates.append(transform_ok)
                    transform_document["folds"].append({
                        "fold": fold_index,
                        "key": key,
                        "train": list(fold["train"]),
                        "validation": list(fold["validation"]),
                        "gram": gram_metadata,
                        "transform": transform_metadata,
                    })

    publish(output_dir / "cv-transforms.json", transform_document)
    candidate = _aggregate_metric_values(candidate_rows)
    baseline = _aggregate_metric_values(baseline_rows)
    dense = _aggregate_metric_values(dense_rows)
    if not (
        dense["operator_relative_l2"] <= 0.005
        and dense["post_rms_relative_l2"] <= 0.01
        and dense["state_relative_l2"] <= 0.005
    ):
        raise ValueError("dense recurrence/RMS formula calibration")

    fold_results = []
    for fold_index in range(len(CV_FOLDS)):
        fold_candidate = _aggregate_metric_values(
            fold_candidate_rows[fold_index]
        )
        fold_baseline = _aggregate_metric_values(
            fold_baseline_rows[fold_index]
        )
        fold_results.append({
            "fold": fold_index,
            "candidate": fold_candidate,
            "energy": fold_baseline,
            "post_rms_improvement": 1.0 - (
                fold_candidate["post_rms_relative_l2"]
                / max(fold_baseline["post_rms_relative_l2"], 1e-30)
            ),
            "state_improvement": 1.0 - (
                fold_candidate["state_relative_l2"]
                / max(fold_baseline["state_relative_l2"], 1e-30)
            ),
        })

    head_ratios = []
    head_results = {}
    for key in sorted(per_head_candidate):
        head_candidate = _aggregate_metric_values(per_head_candidate[key])
        head_baseline = _aggregate_metric_values(per_head_baseline[key])
        ratio = (
            head_candidate["post_rms_relative_l2"]
            / max(head_baseline["post_rms_relative_l2"], 1e-30)
        )
        head_ratios.append(ratio)
        head_results[key] = {
            "candidate": head_candidate,
            "energy": head_baseline,
            "post_rms_ratio": ratio,
        }

    post_rms_improvement = 1.0 - (
        candidate["post_rms_relative_l2"]
        / max(baseline["post_rms_relative_l2"], 1e-30)
    )
    state_improvement = 1.0 - (
        candidate["state_relative_l2"]
        / max(baseline["state_relative_l2"], 1e-30)
    )
    operation_count = static_decode_operation_count()
    gates = {
        "cross_validated_post_rms_improvement_at_least_10_percent":
            post_rms_improvement >= 0.10,
        "cross_validated_state_relative_l2_nonworse":
            candidate["state_relative_l2"] <= baseline["state_relative_l2"],
        "all_fold_post_rms_improvements_positive":
            all(item["post_rms_improvement"] > 0.0 for item in fold_results),
        "at_least_75_percent_heads_nonworse":
            sum(value <= 1.0 for value in head_ratios) >= 72,
        "no_head_worse_over_5_percent": max(head_ratios) <= 1.05,
        "all_transforms_valid": all(all_transform_gates),
        "projection_over_removed_arithmetic_below_10_percent":
            operation_count["projection_over_removed_ratio"] < 0.10,
    }
    status = "admitted_to_fresh_capture" if all(gates.values()) else "rejected"
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "CPU cross-validation on calibration indices 0-11 only. Passing "
            "admits collection of fresh calibration evidence, not NPU replay, "
            "endpoint performance, task accuracy or portability."
        ),
        "capture_root": str(capture_root),
        "capture_audit_sha256": CAPTURE_AUDIT_SHA256,
        "archive_set_sha256": ARCHIVE_SET_SHA256,
        "baseline_plan": str(baseline_plan_path),
        "baseline_plan_sha256": BASELINE_PLAN_SHA256,
        "cross_validation": [
            {name: list(values) for name, values in fold.items()}
            for fold in CV_FOLDS
        ],
        "prohibited_as_fresh_admission": [12, 13, 14, 15],
        "cv_transforms_sha256": digest(output_dir / "cv-transforms.json"),
        "candidate": candidate,
        "energy": baseline,
        "dense_formula_calibration": dense,
        "fold_results": fold_results,
        "head_results": head_results,
        "post_rms_improvement": post_rms_improvement,
        "state_improvement": state_improvement,
        "nonworse_heads": sum(value <= 1.0 for value in head_ratios),
        "total_heads": len(head_ratios),
        "worst_head_ratio": max(head_ratios),
        "static_operation_count": operation_count,
        "gates": gates,
        "decision": (
            "Freeze PORP construction and collect a new untouched admission set."
            if status == "admitted_to_fresh_capture"
            else (
                "Reject PORP v1; do not collect more data, use an NPU, integrate, "
                "benchmark endpoints or run task accuracy."
            )
        ),
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "python": sys.version,
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "completed_unix_ns": time.time_ns(),
    }
    publish(output_dir / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--capture-audit", type=Path, required=True)
    parser.add_argument("--baseline-plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(
        args.capture_root, args.capture_audit, args.baseline_plan, args.output_dir
    )
    print(json.dumps({
        "status": report["status"],
        "post_rms_improvement": report["post_rms_improvement"],
        "state_improvement": report["state_improvement"],
        "nonworse_heads": report["nonworse_heads"],
        "worst_head_ratio": report["worst_head_ratio"],
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
