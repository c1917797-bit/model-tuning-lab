#!/usr/bin/env python3
"""Gate aligned value/state-width DRRQR candidates on frozen GDN captures.

The tool fits layer-shared Dv64 and Dv48 coordinate sets and one bounded
per-layer scalar on capture indices 0-11.  It publishes that lock before it
loads untouched indices 12-15.  All output comparisons use the exact
checkpoint out-projection weights.  This is a CPU admission screen only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from safetensors import safe_open
import torch


SCHEMA = "drrqr-two-sided-value-width-heldout/v1"
HELPER_SHA256 = "b38c455ec765ef4dea429e29b46f446813a59b39f036b01cf254ad276f0adaac"
MODEL_INDEX_NAME = "model.safetensors.index.json"
LAYERS = (0, 12, 25, 38, 50, 62)
FIT_INDICES = tuple(range(12))
HELDOUT_INDICES = tuple(range(12, 16))
WIDTHS = (64, 48)
KEY_WIDTH = 64
VALUE_WIDTH = 128
LOCAL_KEY_HEADS = 4
LOCAL_VALUE_HEADS = 12
VALUE_HEADS = 48
VALUE_HEADS_PER_KEY_HEAD = 3
HIDDEN_SIZE = 5120
EPS = 1e-6
SCALAR_MIN = 0.5
SCALAR_MAX = 2.0


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def tensor_digest(value):
    raw = value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(raw).hexdigest()


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


def load_helper(path):
    path = Path(path).resolve()
    require(path.is_file() and not path.is_symlink(), "regular helper source required")
    require(digest(path) == HELPER_SHA256, "helper source SHA256")
    spec = importlib.util.spec_from_file_location("drrqr_frozen_replay_helper", path)
    require(spec is not None and spec.loader is not None, "helper import specification")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_out_projection(model_root, layer, index):
    key = f"model.language_model.layers.{layer}.linear_attn.out_proj.weight"
    shard_name = index["weight_map"].get(key)
    require(isinstance(shard_name, str), f"missing checkpoint tensor {key}")
    shard = model_root / shard_name
    require(shard.is_file() and not shard.is_symlink(), f"regular checkpoint shard {shard}")
    with safe_open(str(shard), framework="pt", device="cpu") as stream:
        weight = stream.get_tensor(key)
    require(tuple(weight.shape) == (HIDDEN_SIZE, VALUE_HEADS * VALUE_WIDTH),
            f"out-projection geometry for layer {layer}: {tuple(weight.shape)}")
    require(weight.dtype == torch.bfloat16, f"out-projection dtype for layer {layer}")
    identity = {
        "key": key,
        "shard": shard_name,
        "shard_size": shard.stat().st_size,
        "shape": list(weight.shape),
        "dtype": str(weight.dtype),
        "tensor_sha256": tensor_digest(weight),
    }
    return weight.float().contiguous(), identity


def formula_metrics_zero():
    return {"error2": 0.0, "reference2": 0.0, "elements": 0}


def add_formula_metrics(target, source):
    for key in target:
        target[key] += source[key]


def finalize_formula_metrics(value):
    return {
        **value,
        "relative_l2": math.sqrt(value["error2"] / max(value["reference2"], 1e-30)),
        "rmse": math.sqrt(value["error2"] / max(value["elements"], 1)),
    }


def replay_rank(records, layer, rank, plan, helper):
    states = [
        torch.zeros(
            VALUE_HEADS_PER_KEY_HEAD, VALUE_WIDTH, KEY_WIDTH, dtype=torch.float32
        )
        for _ in range(LOCAL_KEY_HEADS)
    ]
    selections = [
        helper.local_baseline_indices(plan, layer, rank, head)
        for head in range(LOCAL_KEY_HEADS)
    ]
    dense_parts = []
    operator_parts = []
    baseline_parts = []
    z_parts = []
    formula = formula_metrics_zero()
    reference_weight = None
    for record in records:
        tensors = record["tensors"]
        dense_operator = tensors["operator_output"].reshape(
            -1, LOCAL_VALUE_HEADS, VALUE_WIDTH
        ).float()
        dense_post = tensors["norm_output"].reshape(
            -1, LOCAL_VALUE_HEADS, VALUE_WIDTH
        ).float()
        z = tensors["z"].reshape(-1, LOCAL_VALUE_HEADS, VALUE_WIDTH).float()
        weight = tensors["norm_weight"].reshape(VALUE_WIDTH)
        if reference_weight is None:
            reference_weight = weight.clone()
        else:
            require(torch.equal(reference_weight, weight), "stable layer norm weight")
        formula_post = helper.rms_gated(dense_operator, z, weight)
        formula["error2"] += float((formula_post - dense_post).square().sum())
        formula["reference2"] += float(dense_post.square().sum())
        formula["elements"] += dense_post.numel()

        baseline_operator = torch.empty_like(dense_operator)
        for head in range(LOCAL_KEY_HEADS):
            item = helper.head_tensors(record, head)
            selected = selections[head]
            q = helper.normalize(item["q"].index_select(-1, selected))
            k = helper.normalize(item["k"].index_select(-1, selected))
            start = head * VALUE_HEADS_PER_KEY_HEAD
            stop = start + VALUE_HEADS_PER_KEY_HEAD
            state = states[head]
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
                    * (KEY_WIDTH ** -0.5)
                ).to(torch.bfloat16).float()
                baseline_operator[token, start:stop] = output
            states[head] = state
        baseline_post = helper.rms_gated(
            baseline_operator, z, reference_weight
        ).to(torch.bfloat16).float()
        require(
            torch.isfinite(baseline_operator).all()
            and torch.isfinite(baseline_post).all()
            and torch.isfinite(dense_post).all(),
            "finite replay tensors",
        )
        dense_parts.append(dense_post)
        operator_parts.append(baseline_operator)
        baseline_parts.append(baseline_post)
        z_parts.append(z)
    require(reference_weight is not None, "non-empty capture records")
    return {
        "dense": torch.cat(dense_parts, dim=0),
        "baseline_operator": torch.cat(operator_parts, dim=0),
        "baseline": torch.cat(baseline_parts, dim=0),
        "z": torch.cat(z_parts, dim=0),
        "weight": reference_weight.float(),
        "formula": formula,
    }


def load_global_sequence(capture, sequence, layer, plan, helper):
    ranks = []
    formula = formula_metrics_zero()
    token_count = None
    for rank in range(4):
        records = helper.load_sequence(capture, sequence, rank, layer)
        value = replay_rank(records, layer, rank, plan, helper)
        if token_count is None:
            token_count = value["dense"].shape[0]
        require(value["dense"].shape[0] == token_count, "rank token alignment")
        add_formula_metrics(formula, value["formula"])
        ranks.append(value)
    for rank in ranks[1:]:
        require(torch.equal(ranks[0]["weight"], rank["weight"]),
                "tensor-parallel norm-weight identity")
    return {
        "dense": torch.cat([value["dense"] for value in ranks], dim=1),
        "baseline_operator": torch.cat(
            [value["baseline_operator"] for value in ranks], dim=1
        ),
        "baseline": torch.cat([value["baseline"] for value in ranks], dim=1),
        "z": torch.cat([value["z"] for value in ranks], dim=1),
        "weight": ranks[0]["weight"],
        "formula": formula,
    }


def select_coordinates(score, width):
    require(score.shape == (VALUE_WIDTH,) and torch.isfinite(score).all(),
            "finite value-coordinate score")
    order = torch.argsort(score, descending=True, stable=True)
    selected = order[:width].sort().values
    require(selected.numel() == width and selected.unique().numel() == width,
            f"exact Dv{width} layer-shared coordinates")
    return selected


def candidate_post_full(bundle, selected, helper):
    operator = bundle["baseline_operator"].index_select(-1, selected)
    z = bundle["z"].index_select(-1, selected)
    weight = bundle["weight"].index_select(0, selected)
    selected_post = helper.rms_gated(operator, z, weight)
    selected_post = selected_post.to(torch.bfloat16).float()
    full = torch.zeros_like(bundle["dense"])
    full.index_copy_(-1, selected, selected_post)
    require(torch.isfinite(full).all(), "finite value-width post-RMS tensor")
    return full, selected_post


def flattened(value):
    require(value.ndim == 3 and value.shape[1:] == (VALUE_HEADS, VALUE_WIDTH),
            f"global value geometry: {tuple(value.shape)}")
    return value.reshape(value.shape[0], VALUE_HEADS * VALUE_WIDTH)


def metric_bucket():
    return {
        "baseline_projected_error2": 0.0,
        "projected_elements": 0,
        "widths": {
            width: {
                "candidate_projected_error2": 0.0,
                "baseline_retained_error2": 0.0,
                "candidate_retained_error2": 0.0,
                "retained_elements": 0,
                "head_baseline_error2": [0.0] * VALUE_HEADS,
                "head_candidate_error2": [0.0] * VALUE_HEADS,
            }
            for width in WIDTHS
        },
    }


def add_retained_metrics(bucket, width, bundle, candidate_selected, selected):
    dense_selected = bundle["dense"].index_select(-1, selected)
    baseline_selected = bundle["baseline"].index_select(-1, selected)
    baseline_error = baseline_selected - dense_selected
    candidate_error = candidate_selected - dense_selected
    row = bucket["widths"][width]
    row["baseline_retained_error2"] += float(baseline_error.square().sum())
    row["candidate_retained_error2"] += float(candidate_error.square().sum())
    row["retained_elements"] += dense_selected.numel()
    for head in range(VALUE_HEADS):
        row["head_baseline_error2"][head] += float(
            baseline_error[:, head].square().sum()
        )
        row["head_candidate_error2"][head] += float(
            candidate_error[:, head].square().sum()
        )


def finish_retained(row):
    ratio = math.sqrt(
        row["candidate_retained_error2"]
        / max(row["baseline_retained_error2"], 1e-30)
    )
    head_ratios = [
        math.sqrt(candidate / max(baseline, 1e-30))
        for baseline, candidate in zip(
            row["head_baseline_error2"],
            row["head_candidate_error2"],
            strict=True,
        )
    ]
    return {
        "baseline_error2": row["baseline_retained_error2"],
        "candidate_error2": row["candidate_retained_error2"],
        "elements": row["retained_elements"],
        "error_ratio": ratio,
        "head_error_ratios": head_ratios,
    }


def fit_layer(capture, layer, plan, weight, helper):
    bundles = []
    score = torch.zeros(VALUE_WIDTH, dtype=torch.float64)
    formula = formula_metrics_zero()
    column_norm2 = weight.square().sum(dim=0).reshape(
        VALUE_HEADS, VALUE_WIDTH
    ).double()
    for sequence in FIT_INDICES:
        bundle = load_global_sequence(capture, sequence, layer, plan, helper)
        add_formula_metrics(formula, bundle["formula"])
        score += (
            bundle["baseline"].double().square() * column_norm2[None, :, :]
        ).sum(dim=(0, 1))
        bundles.append(bundle)
    selections = {
        width: select_coordinates(score, width)
        for width in WIDTHS
    }
    fit = metric_bucket()
    scalar_terms = {
        width: {"candidate2": 0.0, "candidate_teacher": 0.0, "teacher2": 0.0}
        for width in WIDTHS
    }
    for bundle in bundles:
        candidates = {}
        selected_posts = {}
        for width in WIDTHS:
            candidates[width], selected_posts[width] = candidate_post_full(
                bundle, selections[width], helper
            )
            add_retained_metrics(
                fit, width, bundle, selected_posts[width], selections[width]
            )
        dense = flattened(bundle["dense"])
        baseline_delta = flattened(bundle["baseline"] - bundle["dense"])
        rows = [dense, baseline_delta]
        rows.extend(flattened(candidates[width]) for width in WIDTHS)
        projected = torch.mm(torch.cat(rows, dim=0), weight.t())
        tokens = dense.shape[0]
        teacher = projected[:tokens]
        baseline_projected_delta = projected[tokens:2 * tokens]
        fit["baseline_projected_error2"] += float(
            baseline_projected_delta.square().sum()
        )
        fit["projected_elements"] += baseline_projected_delta.numel()
        offset = 2 * tokens
        for width in WIDTHS:
            candidate = projected[offset:offset + tokens]
            offset += tokens
            terms = scalar_terms[width]
            terms["candidate2"] += float(candidate.square().sum())
            terms["candidate_teacher"] += float((candidate * teacher).sum())
            terms["teacher2"] += float(teacher.square().sum())
    result = {
        "formula": finalize_formula_metrics(formula),
        "baseline_projected_error2": fit["baseline_projected_error2"],
        "projected_elements": fit["projected_elements"],
        "widths": {},
    }
    for width in WIDTHS:
        terms = scalar_terms[width]
        scalar = terms["candidate_teacher"] / max(terms["candidate2"], 1e-30)
        scalar = min(SCALAR_MAX, max(SCALAR_MIN, scalar))
        error2 = (
            scalar * scalar * terms["candidate2"]
            - 2.0 * scalar * terms["candidate_teacher"]
            + terms["teacher2"]
        )
        retained = finish_retained(fit["widths"][width])
        result["widths"][width] = {
            "selected": selections[width].tolist(),
            "scalar": scalar,
            "candidate_projected_error2": max(error2, 0.0),
            "projected_error_ratio": math.sqrt(
                max(error2, 0.0) / max(fit["baseline_projected_error2"], 1e-30)
            ),
            "retained_post_rms": retained,
        }
    return result


def heldout_layer(capture, layer, plan, weight, layer_lock, helper):
    result = metric_bucket()
    formula = formula_metrics_zero()
    for sequence in HELDOUT_INDICES:
        bundle = load_global_sequence(capture, sequence, layer, plan, helper)
        add_formula_metrics(formula, bundle["formula"])
        candidates = {}
        selected_posts = {}
        for width in WIDTHS:
            selected = torch.tensor(
                layer_lock[str(width)]["selected"], dtype=torch.long
            )
            candidates[width], selected_posts[width] = candidate_post_full(
                bundle, selected, helper
            )
            add_retained_metrics(
                result, width, bundle, selected_posts[width], selected
            )
        rows = [flattened(bundle["baseline"] - bundle["dense"])]
        for width in WIDTHS:
            scalar = layer_lock[str(width)]["scalar"]
            rows.append(flattened(scalar * candidates[width] - bundle["dense"]))
        projected = torch.mm(torch.cat(rows, dim=0), weight.t())
        tokens = bundle["dense"].shape[0]
        baseline_delta = projected[:tokens]
        result["baseline_projected_error2"] += float(
            baseline_delta.square().sum()
        )
        result["projected_elements"] += baseline_delta.numel()
        offset = tokens
        for width in WIDTHS:
            candidate_delta = projected[offset:offset + tokens]
            offset += tokens
            result["widths"][width]["candidate_projected_error2"] += float(
                candidate_delta.square().sum()
            )
    return {
        "formula": finalize_formula_metrics(formula),
        "baseline_projected_error2": result["baseline_projected_error2"],
        "projected_elements": result["projected_elements"],
        "widths": {
            width: {
                "candidate_projected_error2":
                    result["widths"][width]["candidate_projected_error2"],
                "projected_error_ratio": math.sqrt(
                    result["widths"][width]["candidate_projected_error2"]
                    / max(result["baseline_projected_error2"], 1e-30)
                ),
                "retained_post_rms": finish_retained(result["widths"][width]),
            }
            for width in WIDTHS
        },
    }


def aggregate_split(layers):
    formula = formula_metrics_zero()
    baseline_projected_error2 = 0.0
    projected_elements = 0
    result = {
        width: {
            "candidate_projected_error2": 0.0,
            "baseline_retained_error2": 0.0,
            "candidate_retained_error2": 0.0,
            "retained_elements": 0,
            "head_layer_error_ratios": [],
            "layer_projected_error_ratios": [],
        }
        for width in WIDTHS
    }
    for layer in LAYERS:
        value = layers[str(layer)]
        add_formula_metrics(formula, {
            key: value["formula"][key] for key in formula
        })
        baseline_projected_error2 += value["baseline_projected_error2"]
        projected_elements += value["projected_elements"]
        for width in WIDTHS:
            row = value["widths"][str(width)]
            retained = row["retained_post_rms"]
            result[width]["candidate_projected_error2"] += (
                row["candidate_projected_error2"]
            )
            result[width]["baseline_retained_error2"] += retained["baseline_error2"]
            result[width]["candidate_retained_error2"] += retained["candidate_error2"]
            result[width]["retained_elements"] += retained["elements"]
            result[width]["head_layer_error_ratios"].extend(
                retained["head_error_ratios"]
            )
            result[width]["layer_projected_error_ratios"].append(
                row["projected_error_ratio"]
            )
    widths = {}
    for width in WIDTHS:
        row = result[width]
        widths[str(width)] = {
            "baseline_projected_error2": baseline_projected_error2,
            "candidate_projected_error2": row["candidate_projected_error2"],
            "projected_elements": projected_elements,
            "aggregate_projected_error_ratio": math.sqrt(
                row["candidate_projected_error2"]
                / max(baseline_projected_error2, 1e-30)
            ),
            "worst_layer_projected_error_ratio": max(
                row["layer_projected_error_ratios"]
            ),
            "layer_projected_error_ratios": row["layer_projected_error_ratios"],
            "baseline_retained_error2": row["baseline_retained_error2"],
            "candidate_retained_error2": row["candidate_retained_error2"],
            "retained_elements": row["retained_elements"],
            "aggregate_retained_post_rms_error_ratio": math.sqrt(
                row["candidate_retained_error2"]
                / max(row["baseline_retained_error2"], 1e-30)
            ),
            "head_layer_error_ratios": row["head_layer_error_ratios"],
            "head_layer_ratio_at_most_1_10_fraction": (
                sum(value <= 1.10 for value in row["head_layer_error_ratios"])
                / len(row["head_layer_error_ratios"])
            ),
            "worst_head_layer_error_ratio": max(
                row["head_layer_error_ratios"]
            ),
        }
    return {
        "formula": finalize_formula_metrics(formula),
        "baseline_projected_error2": baseline_projected_error2,
        "projected_elements": projected_elements,
        "widths": widths,
    }


def validate_model(model_root):
    model_root = Path(model_root).resolve()
    index_path = model_root / MODEL_INDEX_NAME
    index = read_json(index_path)
    require(isinstance(index.get("weight_map"), dict), "checkpoint weight map")
    return model_root, index_path, index


def run(
    capture_root,
    audit_path,
    baseline_plan_path,
    model_root,
    helper_source,
    output_dir,
    threads,
):
    capture_root = Path(capture_root).resolve()
    audit_path = Path(audit_path).resolve()
    baseline_plan_path = Path(baseline_plan_path).resolve()
    helper_source = Path(helper_source).resolve()
    output_dir = Path(output_dir).resolve()
    require(
        str(output_dir).startswith("/drrqr-results/")
        and not output_dir.exists()
        and not output_dir.is_symlink(),
        "fresh output below /drrqr-results required",
    )
    require(1 <= threads <= 64, "CPU thread bound")
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    helper = load_helper(helper_source)
    capture, capture_audit, plan = helper.validate_inputs(
        capture_root, audit_path, baseline_plan_path
    )
    model_root, model_index_path, model_index = validate_model(model_root)

    output_dir.mkdir(parents=False, exist_ok=False)
    publish(output_dir / "started.json", {
        "schema": SCHEMA,
        "status": "running",
        "claim": "CPU fit/held-out admission screen only.",
        "fit_indices": list(FIT_INDICES),
        "heldout_indices": list(HELDOUT_INDICES),
        "heldout_loaded": False,
        "threads": threads,
        "script_sha256": digest(__file__),
        "helper_sha256": HELPER_SHA256,
        "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
        "baseline_plan_sha256": helper.BASELINE_PLAN_SHA256,
        "model_index_sha256": digest(model_index_path),
        "started_unix_ns": time.time_ns(),
    })

    fit_layers = {}
    weight_identities = {}
    for layer in LAYERS:
        weight, identity = load_out_projection(model_root, layer, model_index)
        weight_identities[str(layer)] = identity
        value = fit_layer(capture, layer, plan, weight, helper)
        fit_layers[str(layer)] = {
            "formula": value["formula"],
            "baseline_projected_error2": value["baseline_projected_error2"],
            "projected_elements": value["projected_elements"],
            "widths": {
                str(width): value["widths"][width] for width in WIDTHS
            },
        }
        del weight
    fit = aggregate_split(fit_layers)
    require(
        fit["formula"]["relative_l2"] <= 0.01,
        "dense post-RMS formula calibration on fit split",
    )
    layer_lock = {
        str(layer): {
            str(width): {
                "selected": fit_layers[str(layer)]["widths"][str(width)]["selected"],
                "scalar": fit_layers[str(layer)]["widths"][str(width)]["scalar"],
            }
            for width in WIDTHS
        }
        for layer in LAYERS
    }
    lock = {
        "schema": SCHEMA,
        "status": "fit_locked_before_heldout_load",
        "fit_indices": list(FIT_INDICES),
        "heldout_indices_not_loaded": list(HELDOUT_INDICES),
        "widths": list(WIDTHS),
        "layer_lock": layer_lock,
        "weight_identities": weight_identities,
        "model_index_sha256": digest(model_index_path),
        "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
        "baseline_plan_sha256": helper.BASELINE_PLAN_SHA256,
        "locked_unix_ns": time.time_ns(),
    }
    publish(output_dir / "fit-lock.json", lock)

    heldout_layers = {}
    for layer in LAYERS:
        weight, identity = load_out_projection(model_root, layer, model_index)
        require(identity == weight_identities[str(layer)],
                f"stable checkpoint tensor identity for layer {layer}")
        value = heldout_layer(
            capture, layer, plan, weight, layer_lock[str(layer)], helper
        )
        heldout_layers[str(layer)] = {
            "formula": value["formula"],
            "baseline_projected_error2": value["baseline_projected_error2"],
            "projected_elements": value["projected_elements"],
            "widths": {
                str(width): value["widths"][width] for width in WIDTHS
            },
        }
        del weight
    heldout = aggregate_split(heldout_layers)
    require(
        heldout["formula"]["relative_l2"] <= 0.01,
        "dense post-RMS formula calibration on heldout split",
    )

    gates = {}
    for width in WIDTHS:
        row = heldout["widths"][str(width)]
        scalars = [
            layer_lock[str(layer)][str(width)]["scalar"] for layer in LAYERS
        ]
        coordinate_sets = [
            layer_lock[str(layer)][str(width)]["selected"] for layer in LAYERS
        ]
        gates[str(width)] = {
            "dense_post_rms_formula_relative_l2_at_most_0_01":
                heldout["formula"]["relative_l2"] <= 0.01,
            "aggregate_output_projected_error_ratio_at_most_1_10":
                row["aggregate_projected_error_ratio"] <= 1.10,
            "worst_layer_output_projected_error_ratio_at_most_1_20":
                row["worst_layer_projected_error_ratio"] <= 1.20,
            "aggregate_retained_post_rms_error_ratio_at_most_1_10":
                row["aggregate_retained_post_rms_error_ratio"] <= 1.10,
            "head_layer_ratio_at_most_1_10_fraction_at_least_0_75":
                row["head_layer_ratio_at_most_1_10_fraction"] >= 0.75,
            "worst_head_layer_retained_post_rms_error_ratio_at_most_1_50":
                row["worst_head_layer_error_ratio"] <= 1.50,
            "all_scalars_in_predeclared_bounds":
                all(SCALAR_MIN <= value <= SCALAR_MAX for value in scalars),
            "all_layer_shared_coordinate_counts_exact":
                all(
                    len(value) == width and len(set(value)) == width
                    for value in coordinate_sets
                ),
        }
        gates[str(width)]["all"] = all(gates[str(width)].values())
    admitted_width = next(
        (width for width in WIDTHS if gates[str(width)]["all"]), None
    )
    status = (
        "admitted_to_plugin_implementation"
        if admitted_width is not None
        else "rejected"
    )
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "Representative-layer CPU output-fidelity screen only. Passing admits "
            "one plugin implementation and target-NPU numerical gate; it does not "
            "establish NPU correctness, endpoint speedup, task accuracy, paper-exact "
            "StrongRRQR reproduction, or cross-environment performance."
        ),
        "candidate": "frozen energy-Dk64 plus aligned layer-shared value/state width",
        "paper_exact_strong_rrqr": False,
        "fit_indices": list(FIT_INDICES),
        "heldout_indices": list(HELDOUT_INDICES),
        "heldout_loaded_only_after_fit_lock": True,
        "fit_lock_sha256": digest(output_dir / "fit-lock.json"),
        "admitted_width": admitted_width,
        "fit": fit,
        "heldout": heldout,
        "gates": gates,
        "capture": {
            "root": str(capture_root),
            "audit": str(audit_path),
            "audit_sha256": helper.CAPTURE_AUDIT_SHA256,
            "archive_set_sha256": capture_audit["archive_set_sha256"],
        },
        "baseline_plan": {
            "path": str(baseline_plan_path),
            "sha256": helper.BASELINE_PLAN_SHA256,
        },
        "model": {
            "root": str(model_root),
            "index": str(model_index_path),
            "index_sha256": digest(model_index_path),
            "out_projection_tensors": weight_identities,
        },
        "attribution_required_before_endpoint": [
            "Dk128/Dv128",
            "Dk64/Dv128",
            f"Dk128/Dv{admitted_width}" if admitted_width else "Dk128/DvX",
            f"Dk64/Dv{admitted_width}" if admitted_width else "Dk64/DvX",
        ],
        "decision": (
            f"Implement only Dv{admitted_width} in the plugin and require native "
            "prefill/decode multi-step state plus NPUGraph numerical gates."
            if admitted_width is not None
            else "Reject the value/state-width branch; do not integrate, benchmark, "
                 "run task accuracy, or open a nearby selector loop."
        ),
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "helper_path": str(helper_source),
            "helper_sha256": HELPER_SHA256,
            "python": sys.version,
            "torch": torch.__version__,
            "safetensors": getattr(sys.modules["safetensors"], "__version__", None),
            "threads": threads,
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
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--helper-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=32)
    args = parser.parse_args(argv)
    try:
        report = run(
            args.capture_root,
            args.capture_audit,
            args.baseline_plan,
            args.model_root,
            args.helper_source,
            args.output_dir,
            args.threads,
        )
    except Exception as error:
        output_dir = args.output_dir.resolve()
        failure_path = output_dir / "failure.json"
        if (
            str(output_dir).startswith("/drrqr-results/")
            and output_dir.is_dir()
            and not failure_path.exists()
        ):
            publish(failure_path, {
                "schema": SCHEMA,
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
                "failed_unix_ns": time.time_ns(),
            })
        raise
    print(json.dumps({
        "status": report["status"],
        "admitted_width": report["admitted_width"],
        "heldout": {
            width: {
                "projected_error_ratio":
                    report["heldout"]["widths"][str(width)][
                        "aggregate_projected_error_ratio"
                    ],
                "retained_post_rms_error_ratio":
                    report["heldout"]["widths"][str(width)][
                        "aggregate_retained_post_rms_error_ratio"
                    ],
                "worst_layer_projected_error_ratio":
                    report["heldout"]["widths"][str(width)][
                        "worst_layer_projected_error_ratio"
                    ],
                "passing": report["gates"][str(width)]["all"],
            }
            for width in WIDTHS
        },
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
