#!/usr/bin/env python3
"""Gate analytic tail-dot compensation for energy-Dk64 GDN recurrence.

The recurrent state update is byte-identical to frozen energy-Dk64.  A fixed
16-dimensional Walsh-Hadamard sketch of the 64 discarded Q/K coordinates
estimates the missing instantaneous q-dot-k coefficient and corrects only the
operator output.  The sketch is data-independent and can be folded into Q/K
projection weights.  This CPU screen is not NPU performance or task accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

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
    finalize_metrics,
    head_tensors,
    load_sequence,
    local_baseline_indices,
    normalize,
    publish,
    require,
    rms_gated,
    validate_inputs,
    zero_metrics,
)


SCHEMA = "drrqr-tail-dot-recurrent-compensation/v1"
DEVELOPMENT_INDICES = tuple(range(12))
TAIL_WIDTH = WIDTH - TARGET
SKETCH_WIDTH = 16
EPS = 1e-6


def walsh_hadamard(size=TAIL_WIDTH):
    require(size > 0 and size & (size - 1) == 0, "power-of-two tail width")
    value = torch.ones(1, 1, dtype=torch.float32)
    while value.shape[0] < size:
        value = torch.cat(
            (
                torch.cat((value, value), dim=1),
                torch.cat((value, -value), dim=1),
            ),
            dim=0,
        )
    return value * (size ** -0.5)


def sketch_matrix(key):
    """Return a deterministic 64x16 scaled orthoprojector."""
    base = walsh_hadamard()
    column_order = sorted(
        range(TAIL_WIDTH),
        key=lambda index: hashlib.sha256(
            f"{key}:column:{index}".encode("utf-8")
        ).digest(),
    )
    columns = column_order[:SKETCH_WIDTH]
    signs = torch.tensor(
        [
            1.0
            if hashlib.sha256(
                f"{key}:row:{index}".encode("utf-8")
            ).digest()[0] & 1 == 0
            else -1.0
            for index in range(TAIL_WIDTH)
        ],
        dtype=torch.float32,
    )
    # sqrt(64 / 16) makes dot products and squared norms unbiased for an
    # isotropic random 16-dimensional subspace.
    return signs[:, None] * base[:, columns] * math.sqrt(
        TAIL_WIDTH / SKETCH_WIDTH
    )


def coordinate_sets(selected):
    selected = torch.as_tensor(selected, dtype=torch.long)
    require(
        selected.shape == (TARGET,)
        and selected.unique().numel() == TARGET
        and int(selected.min()) >= 0
        and int(selected.max()) < WIDTH,
        "exact local Dk64 coordinates",
    )
    mask = torch.ones(WIDTH, dtype=torch.bool)
    mask[selected] = False
    discarded = torch.arange(WIDTH, dtype=torch.long)[mask]
    require(discarded.shape == (TAIL_WIDTH,), "exact discarded coordinates")
    return selected, discarded


def qk_coefficients(raw_q, raw_k, selected, sketch):
    """Return the existing Dk64 coefficient and sketched dense estimate."""
    selected, discarded = coordinate_sets(selected)
    require(
        raw_q.shape == raw_k.shape
        and raw_q.ndim == 2
        and raw_q.shape[-1] == WIDTH,
        "raw Q/K geometry",
    )
    require(
        sketch.shape == (TAIL_WIDTH, SKETCH_WIDTH),
        "tail sketch geometry",
    )
    q_selected = raw_q.float().index_select(-1, selected)
    k_selected = raw_k.float().index_select(-1, selected)
    q64 = normalize(q_selected)
    k64 = normalize(k_selected)
    coefficient64 = (
        (q64 * k64).sum(dim=-1) * (TARGET ** -0.5)
    )

    q_sketch = raw_q.float().index_select(-1, discarded) @ sketch
    k_sketch = raw_k.float().index_select(-1, discarded) @ sketch
    numerator = (q_selected * k_selected).sum(dim=-1)
    numerator = numerator + (q_sketch * k_sketch).sum(dim=-1)
    q_norm2 = q_selected.square().sum(dim=-1) + q_sketch.square().sum(dim=-1)
    k_norm2 = k_selected.square().sum(dim=-1) + k_sketch.square().sum(dim=-1)
    denominator = torch.sqrt(q_norm2.clamp_min(EPS) * k_norm2.clamp_min(EPS))
    estimated_dense = numerator / denominator * (WIDTH ** -0.5)
    return q64, k64, coefficient64, estimated_dense


def advance_record(state, item, selected, sketch=None):
    raw_q = item["q"]
    raw_k = item["k"]
    if sketch is None:
        q = normalize(raw_q.index_select(-1, selected))
        k = normalize(raw_k.index_select(-1, selected))
        coefficient64 = estimated_dense = None
    else:
        q, k, coefficient64, estimated_dense = qk_coefficients(
            raw_q, raw_k, selected, sketch
        )
    outputs = []
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
        output = torch.einsum("hdk,k->hd", state, q[token])
        output = output * (TARGET ** -0.5)
        if sketch is not None:
            delta = estimated_dense[token] - coefficient64[token]
            output = output + beta[:, None] * residual * delta
        outputs.append(output.to(torch.bfloat16).float())
    return state, torch.stack(outputs)


def accumulate_record(metrics, state, outputs, item, selected):
    for token, output in enumerate(outputs):
        expected = item["operator"][token].float()
        post = rms_gated(output, item["z"][token], item["weight"])
        expected_post = item["norm_output"][token].float()
        metrics["operator_error2"] += float((output - expected).square().sum())
        metrics["operator_reference2"] += float(expected.square().sum())
        metrics["operator_elements"] += expected.numel()
        metrics["post_rms_error2"] += float((post - expected_post).square().sum())
        metrics["post_rms_reference2"] += float(expected_post.square().sum())
        metrics["post_rms_elements"] += expected_post.numel()
    expected_state = item["state_final"].float().index_select(-1, selected)
    state_error2 = float((state - expected_state).square().sum())
    state_reference2 = float(expected_state.square().sum())
    metrics["state_error2"] += state_error2
    metrics["state_reference2"] += state_reference2
    metrics["state_elements"] += expected_state.numel()
    metrics["max_state_checkpoint_relative_l2"] = max(
        metrics["max_state_checkpoint_relative_l2"],
        math.sqrt(state_error2 / max(state_reference2, 1e-30)),
    )


def replay_pair(records, head, selected, key):
    selected, _ = coordinate_sets(selected)
    baseline_state = torch.zeros(
        VALUE_HEADS_PER_KEY_HEAD, WIDTH, TARGET, dtype=torch.float32
    )
    candidate_state = baseline_state.clone()
    sketch = sketch_matrix(key)
    metrics = {
        "baseline_prefill": zero_metrics(),
        "baseline_decode": zero_metrics(),
        "candidate_prefill": zero_metrics(),
        "candidate_decode": zero_metrics(),
    }
    state_bitwise = True
    finite = True
    for record in records:
        item = head_tensors(record, head)
        baseline_state, baseline_outputs = advance_record(
            baseline_state, item, selected
        )
        candidate_state, candidate_outputs = advance_record(
            candidate_state, item, selected, sketch
        )
        state_bitwise = state_bitwise and torch.equal(
            baseline_state, candidate_state
        )
        finite = finite and bool(
            torch.isfinite(candidate_state).all()
            and torch.isfinite(candidate_outputs).all()
        )
        phase = "prefill" if record["step"] == 0 else "decode"
        accumulate_record(
            metrics[f"baseline_{phase}"],
            baseline_state,
            baseline_outputs,
            item,
            selected,
        )
        accumulate_record(
            metrics[f"candidate_{phase}"],
            candidate_state,
            candidate_outputs,
            item,
            selected,
        )
    return {
        name: finalize_metrics(value) for name, value in metrics.items()
    } | {
        "state_bitwise_identical": state_bitwise,
        "finite": finite,
    }


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
    publish(
        output_dir / "started.json",
        {
            "schema": SCHEMA,
            "status": "running",
            "claim": "CPU fidelity screen only; no NPU or endpoint claim.",
            "development_indices": list(DEVELOPMENT_INDICES),
            "prohibited_indices": [12, 13, 14, 15],
            "script_sha256": digest(__file__),
            "started_unix_ns": time.time_ns(),
        },
    )

    rows = []
    head_results = {}
    all_state_bitwise = True
    all_finite = True
    for layer in LAYERS:
        for rank in range(4):
            sequences = [
                load_sequence(capture, sequence, rank, layer)
                for sequence in DEVELOPMENT_INDICES
            ]
            for head in range(4):
                key = f"layer{layer}.rank{rank}.head{head}"
                selected = local_baseline_indices(plan, layer, rank, head)
                per_head = []
                for records in sequences:
                    per_head.append(replay_pair(records, head, selected, key))
                combined = {}
                for name in (
                    "baseline_prefill",
                    "baseline_decode",
                    "candidate_prefill",
                    "candidate_decode",
                ):
                    raw = zero_metrics()
                    for item in per_head:
                        add_metrics(raw, item[name])
                    # add_metrics expects raw accumulators, while replay_pair
                    # returns finalized dictionaries that retain those fields.
                    combined[name] = finalize_metrics(raw)
                state_bitwise = all(
                    item["state_bitwise_identical"] for item in per_head
                )
                finite = all(item["finite"] for item in per_head)
                ratio = (
                    combined["candidate_decode"]["post_rms_relative_l2"]
                    / max(
                        combined["baseline_decode"]["post_rms_relative_l2"],
                        1e-30,
                    )
                )
                combined["decode_post_rms_ratio"] = ratio
                combined["state_bitwise_identical"] = state_bitwise
                combined["finite"] = finite
                combined["selected"] = selected.tolist()
                head_results[key] = combined
                rows.append(combined)
                all_state_bitwise = all_state_bitwise and state_bitwise
                all_finite = all_finite and finite

    aggregate_metrics = {}
    for name in (
        "baseline_prefill",
        "baseline_decode",
        "candidate_prefill",
        "candidate_decode",
    ):
        aggregate_metrics[name] = aggregate(rows, name)
    ratios = [head_results[key]["decode_post_rms_ratio"] for key in sorted(head_results)]
    decode_improvement = 1.0 - (
        aggregate_metrics["candidate_decode"]["post_rms_relative_l2"]
        / max(
            aggregate_metrics["baseline_decode"]["post_rms_relative_l2"],
            1e-30,
        )
    )
    prefill_ratio = (
        aggregate_metrics["candidate_prefill"]["post_rms_relative_l2"]
        / max(
            aggregate_metrics["baseline_prefill"]["post_rms_relative_l2"],
            1e-30,
        )
    )
    gates = {
        "exact_frozen_energy_plan": digest(baseline_plan_path)
        == BASELINE_PLAN_SHA256,
        "aligned_dk64_and_tail16": TARGET == 64
        and TARGET % 16 == 0
        and SKETCH_WIDTH == 16,
        "persistent_state_half_dense": TARGET / WIDTH == 0.5,
        "qk_projection_at_most_five_eighths_dense": (
            TARGET + SKETCH_WIDTH
        )
        / WIDTH
        <= 0.625,
        "state_bitwise_identical_to_energy_dk64": all_state_bitwise,
        "finite_outputs_and_state": all_finite,
        "decode_post_rms_improvement_at_least_15_percent": decode_improvement
        >= 0.15,
        "prefill_post_rms_nonworse": prefill_ratio <= 1.0,
        "at_least_75_percent_heads_nonworse": sum(
            value <= 1.0 for value in ratios
        )
        >= 72,
        "no_head_worse_over_5_percent": max(ratios) <= 1.05,
    }
    status = "admitted_to_fresh_capture" if all(gates.values()) else "rejected"
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "CPU fidelity screen over development indices 0-11 only. Passing "
            "admits a new untouched capture, not NPU replay, endpoint "
            "performance, task accuracy or portability."
        ),
        "capture_root": str(capture_root),
        "capture_audit_sha256": CAPTURE_AUDIT_SHA256,
        "archive_set_sha256": ARCHIVE_SET_SHA256,
        "baseline_plan": str(baseline_plan_path),
        "baseline_plan_sha256": BASELINE_PLAN_SHA256,
        "development_indices": list(DEVELOPMENT_INDICES),
        "prohibited_indices": [12, 13, 14, 15],
        "transform": {
            "family": "deterministic-signed-walsh-hadamard",
            "tail_width": TAIL_WIDTH,
            "sketch_width": SKETCH_WIDTH,
            "data_fitted": False,
            "statically_foldable_into_qk_projection": True,
        },
        "cost_model": {
            "persistent_state_ratio_vs_dense": TARGET / WIDTH,
            "qk_projection_width_ratio_vs_dense": (
                TARGET + SKETCH_WIDTH
            )
            / WIDTH,
            "extra_persistent_state_elements": 0,
        },
        **aggregate_metrics,
        "head_results": head_results,
        "decode_post_rms_improvement": decode_improvement,
        "prefill_post_rms_ratio": prefill_ratio,
        "nonworse_heads": sum(value <= 1.0 for value in ratios),
        "total_heads": len(ratios),
        "worst_head_ratio": max(ratios),
        "gates": gates,
        "decision": (
            "Collect a new untouched admission capture for TDRC."
            if status == "admitted_to_fresh_capture"
            else (
                "Reject TDRC v1; do not use an NPU, integrate, benchmark "
                "endpoints or run task accuracy."
            )
        ),
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "python": sys.version,
            "torch": torch.__version__,
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
        args.capture_root,
        args.capture_audit,
        args.baseline_plan,
        args.output_dir,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "decode_post_rms_improvement": report[
                    "decode_post_rms_improvement"
                ],
                "prefill_post_rms_ratio": report["prefill_post_rms_ratio"],
                "nonworse_heads": report["nonworse_heads"],
                "worst_head_ratio": report["worst_head_ratio"],
            },
            indent=2,
        )
    )
    return report


if __name__ == "__main__":
    main()
