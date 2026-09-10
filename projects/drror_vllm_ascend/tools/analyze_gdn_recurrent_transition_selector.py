#!/usr/bin/env python3
"""Fit and gate a recurrent-transition Dk64 selector on frozen GDN captures.

Indices 0-11 alone determine one global saliency weight tuple and all selected
coordinates.  The tool publishes that lock before it loads indices 12-15.
This is a CPU numerical screen, never endpoint performance or task accuracy.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import torch
import torch.nn.functional as F


SCHEMA = "drrqr-recurrent-transition-selector/v1"
CAPTURE_SCHEMA = "gdn-sensitivity-calibration-v1"
AUDIT_SCHEMA = "gdn-sensitivity-capture-audit/v1"
CAPTURE_AUDIT_SHA256 = "edfc6780adde0dff36f1fd3872452f0d2ad77541e06ac500de3eb3ec72e5b2a5"
ARCHIVE_SET_SHA256 = "d630cd31f77f6a1ef29b29daac4106aff3f8af493c001ff4d7678f1af2e3ab20"
MANIFEST_SHA256 = "6281f7613379daa65af4e70ead89e32fc33290a39124a4bcb7425bb7ff0e38c1"
BASELINE_PLAN_SHA256 = "b1fcb727d3e58be66cc24148e30a5a1722d3bdc0914784f01cad02f11f741b8c"
LAYERS = (0, 12, 25, 38, 50, 62)
FIT_INDICES = tuple(range(12))
HELDOUT_INDICES = tuple(range(12, 16))
CONFIGURATIONS = (
    ("energy", 0.0, 0.0, 0.0),
    ("read-low", 0.1, 0.0, 0.0),
    ("read", 0.5, 0.0, 0.0),
    ("read-strong", 2.0, 0.0, 0.0),
    ("write", 0.0, 0.5, 0.0),
    ("feedback", 0.0, 0.0, 0.5),
    ("balanced-low", 0.1, 0.1, 0.1),
    ("balanced", 0.5, 0.25, 0.25),
    ("balanced-strong", 1.0, 1.0, 1.0),
    ("read-feedback", 0.5, 0.0, 0.25),
)
WIDTH = 128
TARGET = 64
VALUE_HEADS_PER_KEY_HEAD = 3
EPS = 1e-6


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"regular JSON required: {path}")
    return json.loads(path.read_bytes())


def publish(path, document):
    path = Path(path)
    require(path.is_absolute() and not path.exists() and not path.is_symlink(),
            f"fresh absolute output required: {path}")
    partial = path.with_name(path.name + ".partial")
    require(not partial.exists() and not partial.is_symlink(), "stale partial output")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def normalize(value):
    return F.normalize(value.float(), p=2.0, dim=-1, eps=EPS).to(torch.bfloat16).float()


def rms_gated(value, z, weight):
    value = value.float()
    normalized = value * torch.rsqrt(value.square().mean(dim=-1, keepdim=True) + EPS)
    return normalized * weight.float() * F.silu(z.float())


def load_record(capture, sequence, rank, layer, step):
    path = capture / (
        f"calibration-{sequence:02d}.rank{rank}.layer{layer}.step{step}.pt"
    )
    require(path.is_file() and not path.is_symlink(), f"missing record {path.name}")
    value = torch.load(path, map_location="cpu", weights_only=True)
    require(
        value.get("schema") == CAPTURE_SCHEMA
        and value.get("manifest_sha256") == MANIFEST_SHA256
        and value.get("sequence_id") == f"calibration-{sequence:02d}"
        and value.get("rank") == rank
        and value.get("layer") == layer
        and value.get("step") == step,
        f"record identity {path.name}",
    )
    return value


def head_tensors(record, head):
    tensors = record["tensors"]
    start = head * VALUE_HEADS_PER_KEY_HEAD
    stop = start + VALUE_HEADS_PER_KEY_HEAD
    prefill = record["step"] == 0
    q = tensors["raw_q"].reshape(-1, 4, WIDTH)[:, head]
    k = tensors["raw_k"].reshape(-1, 4, WIDTH)[:, head]
    v = tensors["raw_v"].reshape(-1, 12, WIDTH)[:, start:stop]
    g = tensors["g"].reshape(-1, 12)[:, start:stop]
    beta = tensors["beta"].reshape(-1, 12)[:, start:stop]
    operator = tensors["operator_output"].reshape(-1, 12, WIDTH)[:, start:stop]
    z = tensors["z"].reshape(-1, 12, WIDTH)[:, start:stop]
    norm_output = tensors["norm_output"].reshape(-1, 12, WIDTH)[:, start:stop]
    state_initial = tensors["state_initial"][0, start:stop]
    state_final = tensors["state_final"][0, start:stop]
    require(
        q.shape[-1] == k.shape[-1] == WIDTH
        and v.shape[-2:] == (VALUE_HEADS_PER_KEY_HEAD, WIDTH)
        and state_initial.shape == state_final.shape
            == (VALUE_HEADS_PER_KEY_HEAD, WIDTH, WIDTH)
        and operator.shape == z.shape == norm_output.shape
        and (q.shape[0] == 128 if prefill else q.shape[0] == 1),
        "head tensor geometry",
    )
    return {
        "q": q, "k": k, "v": v, "g": g, "beta": beta,
        "operator": operator, "z": z, "norm_output": norm_output,
        "weight": tensors["norm_weight"].reshape(WIDTH),
        "state_initial": state_initial, "state_final": state_final,
    }


def zero_metrics():
    return {
        "operator_error2": 0.0, "operator_reference2": 0.0,
        "post_rms_error2": 0.0, "post_rms_reference2": 0.0,
        "state_error2": 0.0, "state_reference2": 0.0,
        "operator_elements": 0, "post_rms_elements": 0, "state_elements": 0,
        "max_state_checkpoint_relative_l2": 0.0,
    }


def add_metrics(target, source):
    for key in target:
        if key.startswith("max_"):
            target[key] = max(target[key], source[key])
        else:
            target[key] += source[key]


def finalize_metrics(metrics):
    result = dict(metrics)
    for name in ("operator", "post_rms", "state"):
        error = metrics[f"{name}_error2"]
        reference = metrics[f"{name}_reference2"]
        result[f"{name}_relative_l2"] = math.sqrt(error / max(reference, 1e-30))
        result[f"{name}_rmse"] = math.sqrt(error / max(metrics[f"{name}_elements"], 1))
    return result


def replay(records, head, selected):
    selected = torch.as_tensor(selected, dtype=torch.long)
    require(selected.shape == (TARGET,) and selected.unique().numel() == TARGET,
            "Dk64 selected coordinates")
    state = torch.zeros(
        VALUE_HEADS_PER_KEY_HEAD, WIDTH, TARGET, dtype=torch.float32
    )
    metrics = zero_metrics()
    for step, record in enumerate(records):
        item = head_tensors(record, head)
        q = normalize(item["q"].index_select(-1, selected))
        k = normalize(item["k"].index_select(-1, selected))
        scale = TARGET ** -0.5
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
            output = torch.einsum("hdk,k->hd", state, q[token]) * scale
            output = output.to(torch.bfloat16).float()
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


def replay_dense(records, head):
    state = torch.zeros(
        VALUE_HEADS_PER_KEY_HEAD, WIDTH, WIDTH, dtype=torch.float32
    )
    metrics = zero_metrics()
    selected = torch.arange(WIDTH)
    for record in records:
        item = head_tensors(record, head)
        q = normalize(item["q"])
        k = normalize(item["k"])
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
                * (WIDTH ** -0.5)
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


def load_sequence(capture, sequence, rank, layer):
    return [
        load_record(capture, sequence, rank, layer, step)
        for step in range(9)
    ]


def score_terms_from_sequences(sequences, head):
    q_energy = torch.zeros(WIDTH)
    k_energy = torch.zeros(WIDTH)
    read = torch.zeros(WIDTH)
    write = torch.zeros(WIDTH)
    feedback = torch.zeros(WIDTH)
    for records in sequences:
        for record in records:
            item = head_tensors(record, head)
            q = normalize(item["q"])
            k = normalize(item["k"])
            q_energy += q.square().sum(dim=0)
            k_energy += k.square().sum(dim=0)
            checkpoint_q = q[-1]
            read += (
                item["state_final"].float()
                * checkpoint_q[None, None, :]
            ).square().sum(dim=(0, 1))
            if record["step"] == 0:
                write += item["state_final"].float().square().sum(dim=(0, 1))
            else:
                alpha = item["g"][0].float().exp()
                beta = item["beta"][0].float()
                decayed = alpha[:, None, None] * item["state_initial"].float()
                delta = item["state_final"].float() - decayed
                write += delta.square().sum(dim=(0, 1))
                feedback += (
                    beta[:, None, None]
                    * decayed
                    * k[0][None, None, :]
                ).square().sum(dim=(0, 1))
    def unit(value):
        return value / value.sum().clamp_min(1e-30)
    return {
        "q_energy": q_energy,
        "k_energy": k_energy,
        "energy": unit(q_energy + k_energy),
        "read": unit(read),
        "write": unit(write),
        "feedback": unit(feedback),
    }


def score_terms(capture, indices, rank, layer, head):
    sequences = [
        load_sequence(capture, sequence, rank, layer)
        for sequence in indices
    ]
    return score_terms_from_sequences(sequences, head)


def local_baseline_indices(plan, layer, rank, head):
    global_head = rank * 4 + head
    lower, upper = global_head * WIDTH, (global_head + 1) * WIDTH
    selected = [
        value - lower
        for value in plan["keep_indices"][str(layer)]
        if lower <= value < upper
    ]
    require(len(selected) == TARGET and len(set(selected)) == TARGET,
            "energy baseline head coverage")
    return torch.tensor(sorted(selected), dtype=torch.long)


def choose_indices(terms, baseline, weights, max_swaps=8, floor_ratio=0.98):
    _, read_weight, write_weight, feedback_weight = weights
    score = (
        terms["energy"]
        + read_weight * terms["read"]
        + write_weight * terms["write"]
        + feedback_weight * terms["feedback"]
    )
    baseline_q = float(terms["q_energy"][baseline].sum())
    baseline_k = float(terms["k_energy"][baseline].sum())
    mask = torch.zeros(WIDTH, dtype=torch.bool)
    mask[baseline] = True
    removals = baseline[torch.argsort(score[baseline], stable=True)]
    additions = torch.arange(WIDTH)[~mask]
    additions = additions[torch.argsort(
        score[additions], descending=True, stable=True
    )]
    for swaps in range(max_swaps, -1, -1):
        selected = baseline.clone()
        if swaps:
            removed = set(removals[:swaps].tolist())
            retained = torch.tensor(
                [value for value in baseline.tolist() if value not in removed],
                dtype=baseline.dtype,
            )
            selected = torch.cat((retained, additions[:swaps]))
        selected = selected.sort().values
        q_ratio = float(terms["q_energy"][selected].sum()) / max(baseline_q, 1e-30)
        k_ratio = float(terms["k_energy"][selected].sum()) / max(baseline_k, 1e-30)
        if q_ratio >= floor_ratio and k_ratio >= floor_ratio:
            return selected, {
                "swaps": swaps, "q_energy_ratio": q_ratio,
                "k_energy_ratio": k_ratio,
                "removed": sorted(set(baseline.tolist()) - set(selected.tolist())),
                "added": sorted(set(selected.tolist()) - set(baseline.tolist())),
            }
    raise AssertionError("zero-swap baseline must satisfy its own energy floor")


def select_for_configuration(terms, baseline, configuration):
    if configuration[0] != "energy":
        return choose_indices(terms, baseline, configuration)
    return baseline.clone(), {
        "swaps": 0,
        "q_energy_ratio": 1.0,
        "k_energy_ratio": 1.0,
        "removed": [],
        "added": [],
    }


def evaluate_indices_from_sequences(sequences, head, selected):
    metrics = zero_metrics()
    for records in sequences:
        add_metrics(metrics, replay(records, head, selected))
    return finalize_metrics(metrics)


def evaluate_dense_from_sequences(sequences, head):
    metrics = zero_metrics()
    for records in sequences:
        add_metrics(metrics, replay_dense(records, head))
    return finalize_metrics(metrics)


def evaluate_indices(capture, indices, rank, layer, head, selected):
    sequences = [
        load_sequence(capture, sequence, rank, layer)
        for sequence in indices
    ]
    return evaluate_indices_from_sequences(sequences, head, selected)


def evaluate_dense(capture, indices, rank, layer, head):
    sequences = [
        load_sequence(capture, sequence, rank, layer)
        for sequence in indices
    ]
    return evaluate_dense_from_sequences(sequences, head)


def aggregate(rows, key):
    result = zero_metrics()
    for row in rows:
        add_metrics(result, row[key])
    return finalize_metrics(result)


def lock_fit_configuration(train):
    baseline = train["energy"]["metrics"]
    eligible = [
        name for name, *_ in CONFIGURATIONS
        if name != "energy"
        and train[name]["changed_heads"] > 0
        and train[name]["metrics"]["state_relative_l2"]
            <= baseline["state_relative_l2"]
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda name: (
            train[name]["metrics"]["post_rms_relative_l2"],
            train[name]["metrics"]["operator_relative_l2"],
            name,
        ),
    )


def validate_inputs(capture_root, audit_path, baseline_plan_path):
    require(digest(audit_path) == CAPTURE_AUDIT_SHA256, "capture audit SHA256")
    audit = read_json(audit_path)
    require(
        audit.get("schema") == AUDIT_SCHEMA
        and audit.get("status") == "passed"
        and audit.get("archive_count") == 3456
        and audit.get("archive_set_sha256") == ARCHIVE_SET_SHA256
        and audit.get("manifest_sha256") == MANIFEST_SHA256,
        "capture audit admission",
    )
    require(digest(baseline_plan_path) == BASELINE_PLAN_SHA256,
            "baseline plan SHA256")
    plan = read_json(baseline_plan_path)
    require(
        plan.get("schema") == "ascend-drrqr-plan/v1"
        and plan.get("selection_objective") == "energy-kernel"
        and plan.get("old_head_k_dim") == WIDTH
        and plan.get("target_head_k_dim") == TARGET
        and plan.get("num_key_heads") == 16,
        "energy-Dk64 baseline plan",
    )
    capture = capture_root / "teacher-capture"
    require(capture.is_dir() and not capture.is_symlink(), "capture tensor directory")
    return capture, audit, plan


def run(capture_root, audit_path, baseline_plan_path, output_dir):
    capture_root = Path(capture_root).resolve()
    audit_path = Path(audit_path).resolve()
    baseline_plan_path = Path(baseline_plan_path).resolve()
    output_dir = Path(output_dir).resolve()
    require(
        str(output_dir).startswith("/drrqr-results/")
        and not output_dir.exists()
        and not output_dir.is_symlink(),
        "fresh output below /drrqr-results required",
    )
    capture, capture_audit, plan = validate_inputs(
        capture_root, audit_path, baseline_plan_path
    )
    output_dir.mkdir(parents=False, exist_ok=False)
    receipt = {
        "schema": SCHEMA, "status": "running",
        "claim": "CPU recurrence-aware representative-layer screen only.",
        "fit_indices": list(FIT_INDICES),
        "heldout_indices": list(HELDOUT_INDICES),
        "heldout_loaded": False,
        "script_sha256": digest(__file__),
        "started_unix_ns": time.time_ns(),
    }
    publish(output_dir / "started.json", receipt)

    rows_by_config = defaultdict(list)
    selections = {name: {} for name, *_ in CONFIGURATIONS}
    selection_meta = {name: {} for name, *_ in CONFIGURATIONS}
    dense_fit_rows = []
    for layer in LAYERS:
        for rank in range(4):
            fit_sequences = [
                load_sequence(capture, sequence, rank, layer)
                for sequence in FIT_INDICES
            ]
            for head in range(4):
                key = f"layer{layer}.rank{rank}.head{head}"
                terms = score_terms_from_sequences(fit_sequences, head)
                baseline = local_baseline_indices(plan, layer, rank, head)
                dense_fit = evaluate_dense_from_sequences(fit_sequences, head)
                dense_fit_rows.append(dense_fit)
                for config in CONFIGURATIONS:
                    name = config[0]
                    selected, meta = select_for_configuration(
                        terms, baseline, config
                    )
                    metrics = evaluate_indices_from_sequences(
                        fit_sequences, head, selected
                    )
                    selections[name][key] = selected.tolist()
                    selection_meta[name][key] = meta
                    rows_by_config[name].append({
                        "key": key, "metrics": metrics, "selection": meta,
                    })

    dense_fit = aggregate(
        [{"metrics": value} for value in dense_fit_rows], "metrics"
    )
    require(
        dense_fit["operator_relative_l2"] <= 0.005
        and dense_fit["post_rms_relative_l2"] <= 0.01
        and dense_fit["state_relative_l2"] <= 0.005,
        "dense recurrence/RMS formula calibration on fit split",
    )
    train = {}
    for config in CONFIGURATIONS:
        name = config[0]
        metrics = aggregate(rows_by_config[name], "metrics")
        head_values = [
            row["metrics"]["post_rms_relative_l2"]
            for row in rows_by_config[name]
        ]
        train[name] = {
            "weights": {
                "read": config[1], "write": config[2], "feedback": config[3]
            },
            "metrics": metrics,
            "head_post_rms_relative_l2": head_values,
            "changed_heads": sum(
                row["selection"]["swaps"] > 0 for row in rows_by_config[name]
            ),
            "total_swaps": sum(
                row["selection"]["swaps"] for row in rows_by_config[name]
            ),
            "minimum_q_energy_ratio": min(
                row["selection"]["q_energy_ratio"] for row in rows_by_config[name]
            ),
            "minimum_k_energy_ratio": min(
                row["selection"]["k_energy_ratio"] for row in rows_by_config[name]
            ),
        }
    locked_name = lock_fit_configuration(train)
    lock = {
        "schema": SCHEMA,
        "status": (
            "fit_locked_before_heldout_load"
            if locked_name is not None
            else "rejected_before_heldout_load"
        ),
        "fit_indices": list(FIT_INDICES),
        "heldout_indices_not_loaded": list(HELDOUT_INDICES),
        "configuration": locked_name,
        "weights": train[locked_name]["weights"] if locked_name is not None else None,
        "selections": selections[locked_name] if locked_name is not None else {},
        "selection_metadata": (
            selection_meta[locked_name] if locked_name is not None else {}
        ),
        "baseline_plan_sha256": BASELINE_PLAN_SHA256,
        "capture_audit_sha256": CAPTURE_AUDIT_SHA256,
        "locked_unix_ns": time.time_ns(),
    }
    publish(output_dir / "fit-lock.json", lock)

    if locked_name is None:
        report = {
            "schema": SCHEMA,
            "status": "rejected",
            "claim": (
                "Fit-only CPU recurrence screen. No non-energy configuration "
                "preserved fit-state fidelity, so held-out data was not loaded."
            ),
            "capture_root": str(capture_root),
            "capture_audit_sha256": CAPTURE_AUDIT_SHA256,
            "archive_set_sha256": ARCHIVE_SET_SHA256,
            "baseline_plan": str(baseline_plan_path),
            "baseline_plan_sha256": BASELINE_PLAN_SHA256,
            "fit_indices": list(FIT_INDICES),
            "heldout_indices": list(HELDOUT_INDICES),
            "heldout_loaded": False,
            "fit_lock_sha256": digest(output_dir / "fit-lock.json"),
            "locked_configuration": None,
            "dense_formula_calibration": {"fit": dense_fit, "heldout": None},
            "train_configurations": train,
            "heldout": None,
            "heldout_head_post_rms_ratios": None,
            "heldout_post_rms_improvement": None,
            "heldout_state_improvement": None,
            "heldout_nonworse_heads": None,
            "heldout_worst_head_ratio": None,
            "gates": {"locked_non_energy_configuration": False},
            "decision": (
                "Reject RTS v1 before held-out evaluation; do not integrate, "
                "benchmark, or run task accuracy."
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

    heldout_rows = {"energy": [], locked_name: []}
    dense_heldout_rows = []
    for layer in LAYERS:
        for rank in range(4):
            heldout_sequences = [
                load_sequence(capture, sequence, rank, layer)
                for sequence in HELDOUT_INDICES
            ]
            for head in range(4):
                key = f"layer{layer}.rank{rank}.head{head}"
                baseline = local_baseline_indices(plan, layer, rank, head)
                candidate = torch.tensor(lock["selections"][key])
                dense_heldout_rows.append(
                    evaluate_dense_from_sequences(heldout_sequences, head)
                )
                heldout_rows["energy"].append({
                    "key": key,
                    "metrics": evaluate_indices_from_sequences(
                        heldout_sequences, head, baseline
                    ),
                })
                heldout_rows[locked_name].append({
                    "key": key,
                    "metrics": evaluate_indices_from_sequences(
                        heldout_sequences, head, candidate
                    ),
                })
    dense_heldout = aggregate(
        [{"metrics": value} for value in dense_heldout_rows], "metrics"
    )
    require(
        dense_heldout["operator_relative_l2"] <= 0.005
        and dense_heldout["post_rms_relative_l2"] <= 0.01
        and dense_heldout["state_relative_l2"] <= 0.005,
        "dense recurrence/RMS formula calibration on heldout split",
    )
    heldout = {
        name: aggregate(rows, "metrics")
        for name, rows in heldout_rows.items()
    }
    baseline_post = heldout["energy"]["post_rms_relative_l2"]
    candidate_post = heldout[locked_name]["post_rms_relative_l2"]
    baseline_state = heldout["energy"]["state_relative_l2"]
    candidate_state = heldout[locked_name]["state_relative_l2"]
    head_ratios = []
    for baseline_row, candidate_row in zip(
        heldout_rows["energy"], heldout_rows[locked_name], strict=True
    ):
        require(baseline_row["key"] == candidate_row["key"], "heldout head ordering")
        head_ratios.append(
            candidate_row["metrics"]["post_rms_relative_l2"]
            / max(baseline_row["metrics"]["post_rms_relative_l2"], 1e-30)
        )
    improvement = 1.0 - candidate_post / max(baseline_post, 1e-30)
    gates = {
        "locked_non_energy_configuration": locked_name != "energy",
        "heldout_post_rms_improvement_at_least_10_percent": improvement >= 0.10,
        "heldout_state_relative_l2_nonworse": candidate_state <= baseline_state,
        "at_least_75_percent_heads_nonworse":
            sum(value <= 1.0 for value in head_ratios) >= 72,
        "no_head_worse_over_5_percent": max(head_ratios) <= 1.05,
        "all_energy_floors_passed":
            train[locked_name]["minimum_q_energy_ratio"] >= 0.98
            and train[locked_name]["minimum_k_energy_ratio"] >= 0.98,
        "all_selected_widths_exactly_64":
            all(len(value) == TARGET and len(set(value)) == TARGET
                for value in lock["selections"].values()),
    }
    status = "admitted_to_native_npu_replay" if all(gates.values()) else "rejected"
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "Representative-layer CPU recurrence screen only. Passing admits "
            "native-NPU replay; it does not establish endpoint performance, "
            "task accuracy, or portability."
        ),
        "capture_root": str(capture_root),
        "capture_audit_sha256": CAPTURE_AUDIT_SHA256,
        "archive_set_sha256": ARCHIVE_SET_SHA256,
        "baseline_plan": str(baseline_plan_path),
        "baseline_plan_sha256": BASELINE_PLAN_SHA256,
        "fit_indices": list(FIT_INDICES),
        "heldout_indices": list(HELDOUT_INDICES),
        "heldout_loaded_only_after_fit_lock": True,
        "fit_lock_sha256": digest(output_dir / "fit-lock.json"),
        "locked_configuration": locked_name,
        "dense_formula_calibration": {
            "fit": dense_fit, "heldout": dense_heldout,
        },
        "train_configurations": train,
        "heldout": heldout,
        "heldout_head_post_rms_ratios": head_ratios,
        "heldout_post_rms_improvement": improvement,
        "heldout_state_improvement":
            1.0 - candidate_state / max(baseline_state, 1e-30),
        "heldout_nonworse_heads": sum(value <= 1.0 for value in head_ratios),
        "heldout_worst_head_ratio": max(head_ratios),
        "gates": gates,
        "decision": (
            "Proceed to a separate native-NPU eager/state/NPUGraph replay."
            if status == "admitted_to_native_npu_replay"
            else "Reject RTS v1; do not integrate, benchmark, or run task accuracy."
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
        "locked_configuration": report["locked_configuration"],
        "heldout_post_rms_improvement": report["heldout_post_rms_improvement"],
        "heldout_state_improvement": report["heldout_state_improvement"],
        "heldout_nonworse_heads": report["heldout_nonworse_heads"],
        "heldout_worst_head_ratio": report["heldout_worst_head_ratio"],
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
