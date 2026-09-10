#!/usr/bin/env python3
"""Gate dense-prefill to energy-Dk64 decode transition on frozen GDN traces.

The candidate uses the captured dense prefill state exactly, gathers the frozen
energy-Dk64 columns once, and then replays only decode at Dk64.  The comparator
runs the same Dk64 coordinates through prefill and decode.  This CPU screen is
not NPU performance or task accuracy.
"""

from __future__ import annotations

import argparse
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
    rms_gated,
    validate_inputs,
    zero_metrics,
)


SCHEMA = "drrqr-dense-prefill-dk64-decode/v1"
DEVELOPMENT_INDICES = tuple(range(12))


def _advance(state, item, selected):
    q = normalize(item["q"].index_select(-1, selected))
    k = normalize(item["k"].index_select(-1, selected))
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
        outputs.append(
            (
                torch.einsum("hdk,k->hd", state, q[token])
                * (TARGET ** -0.5)
            ).to(torch.bfloat16).float()
        )
    return state, torch.stack(outputs)


def initialize_decode_state(records, head, selected, dense_prefill):
    if len(records) != 9 or records[0]["step"] != 0:
        raise ValueError("one prefill plus eight decode records required")
    selected = torch.as_tensor(selected, dtype=torch.long)
    if selected.shape != (TARGET,) or selected.unique().numel() != TARGET:
        raise ValueError("exact Dk64 coordinates required")
    prefill = head_tensors(records[0], head)
    first_decode = head_tensors(records[1], head)
    if not torch.equal(prefill["state_final"], first_decode["state_initial"]):
        raise ValueError("prefill/decode dense state transition identity")
    if dense_prefill:
        return prefill["state_final"].float().index_select(-1, selected).clone()
    state = torch.zeros(
        VALUE_HEADS_PER_KEY_HEAD, WIDTH, TARGET, dtype=torch.float32
    )
    state, _ = _advance(state, prefill, selected)
    return state


def replay_decode(records, head, selected, dense_prefill):
    selected = torch.as_tensor(selected, dtype=torch.long)
    state = initialize_decode_state(records, head, selected, dense_prefill)
    metrics = zero_metrics()
    for record in records[1:]:
        item = head_tensors(record, head)
        state, outputs = _advance(state, item, selected)
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
    return metrics


def evaluate_decode_from_sequences(sequences, head, selected, dense_prefill):
    metrics = zero_metrics()
    for records in sequences:
        add_metrics(
            metrics, replay_decode(records, head, selected, dense_prefill)
        )
    return finalize_metrics(metrics)


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
        "claim": "CPU decode-fidelity screen only; no NPU or endpoint claim.",
        "development_indices": list(DEVELOPMENT_INDICES),
        "prohibited_as_fresh_admission": [12, 13, 14, 15],
        "script_sha256": digest(__file__),
        "started_unix_ns": time.time_ns(),
    })

    baseline_rows = []
    candidate_rows = []
    head_results = {}
    for layer in LAYERS:
        for rank in range(4):
            sequences = [
                load_sequence(capture, sequence, rank, layer)
                for sequence in DEVELOPMENT_INDICES
            ]
            for head in range(4):
                key = f"layer{layer}.rank{rank}.head{head}"
                selected = local_baseline_indices(plan, layer, rank, head)
                baseline_metrics = evaluate_decode_from_sequences(
                    sequences, head, selected, dense_prefill=False
                )
                candidate_metrics = evaluate_decode_from_sequences(
                    sequences, head, selected, dense_prefill=True
                )
                ratio = (
                    candidate_metrics["post_rms_relative_l2"]
                    / max(baseline_metrics["post_rms_relative_l2"], 1e-30)
                )
                baseline_rows.append({"metrics": baseline_metrics})
                candidate_rows.append({"metrics": candidate_metrics})
                head_results[key] = {
                    "energy_all_phase": baseline_metrics,
                    "dense_prefill_dk64_decode": candidate_metrics,
                    "post_rms_ratio": ratio,
                    "selected": selected.tolist(),
                }

    baseline = aggregate(baseline_rows, "metrics")
    candidate = aggregate(candidate_rows, "metrics")
    ratios = [head_results[key]["post_rms_ratio"] for key in sorted(head_results)]
    post_improvement = 1.0 - (
        candidate["post_rms_relative_l2"]
        / max(baseline["post_rms_relative_l2"], 1e-30)
    )
    state_improvement = 1.0 - (
        candidate["state_relative_l2"]
        / max(baseline["state_relative_l2"], 1e-30)
    )
    gates = {
        "dense_prefill_exact_by_construction": True,
        "single_transition_before_decode": True,
        "exact_frozen_energy_plan": digest(baseline_plan_path)
            == BASELINE_PLAN_SHA256,
        "aligned_dk64": TARGET == 64 and TARGET % 16 == 0,
        "decode_post_rms_improvement_at_least_20_percent":
            post_improvement >= 0.20,
        "decode_state_relative_l2_nonworse":
            candidate["state_relative_l2"] <= baseline["state_relative_l2"],
        "at_least_75_percent_heads_nonworse":
            sum(value <= 1.0 for value in ratios) >= 72,
        "no_head_worse_over_5_percent": max(ratios) <= 1.05,
    }
    status = "admitted_to_fresh_capture" if all(gates.values()) else "rejected"
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "CPU decode-fidelity screen over development indices 0-11 only. "
            "Passing admits fresh calibration capture, not NPU replay, endpoint "
            "performance, task accuracy or portability."
        ),
        "capture_root": str(capture_root),
        "capture_audit_sha256": CAPTURE_AUDIT_SHA256,
        "archive_set_sha256": ARCHIVE_SET_SHA256,
        "baseline_plan": str(baseline_plan_path),
        "baseline_plan_sha256": BASELINE_PLAN_SHA256,
        "development_indices": list(DEVELOPMENT_INDICES),
        "prohibited_as_fresh_admission": [12, 13, 14, 15],
        "energy_all_phase": baseline,
        "dense_prefill_dk64_decode": candidate,
        "head_results": head_results,
        "decode_post_rms_improvement": post_improvement,
        "decode_state_improvement": state_improvement,
        "nonworse_heads": sum(value <= 1.0 for value in ratios),
        "total_heads": len(ratios),
        "worst_head_ratio": max(ratios),
        "gates": gates,
        "decision": (
            "Collect a new untouched admission set for DPDT."
            if status == "admitted_to_fresh_capture"
            else (
                "Reject DPDT v1; do not collect more data, use an NPU, integrate, "
                "benchmark endpoints or run task accuracy."
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
        args.capture_root, args.capture_audit, args.baseline_plan, args.output_dir
    )
    print(json.dumps({
        "status": report["status"],
        "decode_post_rms_improvement": report["decode_post_rms_improvement"],
        "decode_state_improvement": report["decode_state_improvement"],
        "nonworse_heads": report["nonworse_heads"],
        "worst_head_ratio": report["worst_head_ratio"],
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
