#!/usr/bin/env python3
"""Gate per-value-head Dv coordinate plans on frozen GDN captures.

The tool keeps the frozen energy-Dk64 key plan, fits one static coordinate set
per value head and one scalar per layer on capture indices 0-11, publishes that
lock, and only then loads indices 12-15.  It is a CPU admission screen only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback

import torch
import torch.nn.functional as F


SCHEMA = "drrqr-per-head-value-width-heldout/v1"
BASE_ANALYZER_SHA256 = "8d56fbe4fa992acd2384cd736045c1c28d2914e8d23f8e720e6f5c71833725c8"


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load_base():
    path = Path(__file__).resolve().with_name(
        "analyze_drrqr_value_width_heldout.py"
    )
    require(path.is_file() and not path.is_symlink(), "regular base analyzer")
    require(digest(path) == BASE_ANALYZER_SHA256, "base analyzer SHA256")
    spec = importlib.util.spec_from_file_location(
        "drrqr_frozen_value_width_base", path
    )
    require(spec is not None and spec.loader is not None, "base import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def select_head_coordinates(score, width, base):
    require(
        score.shape == (base.VALUE_HEADS, base.VALUE_WIDTH)
        and torch.isfinite(score).all(),
        "finite per-head value-coordinate score",
    )
    order = torch.argsort(score, dim=-1, descending=True, stable=True)
    selected = order[:, :width].sort(dim=-1).values
    require(
        selected.shape == (base.VALUE_HEADS, width)
        and all(row.unique().numel() == width for row in selected),
        f"exact Dv{width} coordinates for every value head",
    )
    return selected


def gather_per_head(value, selected, base):
    require(
        value.ndim == 3
        and value.shape[1:] == (base.VALUE_HEADS, base.VALUE_WIDTH),
        f"global value geometry: {tuple(value.shape)}",
    )
    require(
        selected.ndim == 2 and selected.shape[0] == base.VALUE_HEADS,
        f"per-head coordinate geometry: {tuple(selected.shape)}",
    )
    index = selected[None, :, :].expand(value.shape[0], -1, -1)
    return torch.gather(value, -1, index)


def candidate_post_full(bundle, selected, base):
    operator = gather_per_head(bundle["baseline_operator"], selected, base)
    z = gather_per_head(bundle["z"], selected, base)
    weight = bundle["weight"][selected]
    normalized = operator.float() * torch.rsqrt(
        operator.float().square().mean(dim=-1, keepdim=True) + base.EPS
    )
    selected_post = normalized * weight.float() * F.silu(z.float())
    selected_post = selected_post.to(torch.bfloat16).float()
    full = torch.zeros_like(bundle["dense"])
    index = selected[None, :, :].expand(full.shape[0], -1, -1)
    full.scatter_(-1, index, selected_post)
    require(
        torch.isfinite(full).all() and torch.isfinite(selected_post).all(),
        "finite per-head value-width post-RMS tensor",
    )
    return full, selected_post


def add_retained_metrics(bucket, width, bundle, candidate_selected, selected, base):
    dense_selected = gather_per_head(bundle["dense"], selected, base)
    baseline_selected = gather_per_head(bundle["baseline"], selected, base)
    baseline_error = baseline_selected - dense_selected
    candidate_error = candidate_selected - dense_selected
    row = bucket["widths"][width]
    row["baseline_retained_error2"] += float(baseline_error.square().sum())
    row["candidate_retained_error2"] += float(candidate_error.square().sum())
    row["retained_elements"] += dense_selected.numel()
    for head in range(base.VALUE_HEADS):
        row["head_baseline_error2"][head] += float(
            baseline_error[:, head].square().sum()
        )
        row["head_candidate_error2"][head] += float(
            candidate_error[:, head].square().sum()
        )


def fit_layer(capture, layer, plan, weight, helper, base):
    bundles = []
    score = torch.zeros(
        base.VALUE_HEADS, base.VALUE_WIDTH, dtype=torch.float64
    )
    formula = base.formula_metrics_zero()
    column_norm2 = weight.square().sum(dim=0).reshape(
        base.VALUE_HEADS, base.VALUE_WIDTH
    ).double()
    for sequence in base.FIT_INDICES:
        bundle = base.load_global_sequence(
            capture, sequence, layer, plan, helper
        )
        base.add_formula_metrics(formula, bundle["formula"])
        score += (
            bundle["baseline"].double().square() * column_norm2[None, :, :]
        ).sum(dim=0)
        bundles.append(bundle)
    selections = {
        width: select_head_coordinates(score, width, base)
        for width in base.WIDTHS
    }
    fit = base.metric_bucket()
    scalar_terms = {
        width: {"candidate2": 0.0, "candidate_teacher": 0.0, "teacher2": 0.0}
        for width in base.WIDTHS
    }
    for bundle in bundles:
        candidates = {}
        for width in base.WIDTHS:
            candidate, selected_post = candidate_post_full(
                bundle, selections[width], base
            )
            candidates[width] = candidate
            add_retained_metrics(
                fit,
                width,
                bundle,
                selected_post,
                selections[width],
                base,
            )
        dense = base.flattened(bundle["dense"])
        baseline_delta = base.flattened(bundle["baseline"] - bundle["dense"])
        rows = [dense, baseline_delta]
        rows.extend(base.flattened(candidates[width]) for width in base.WIDTHS)
        projected = torch.mm(torch.cat(rows, dim=0), weight.t())
        tokens = dense.shape[0]
        teacher = projected[:tokens]
        fit["baseline_projected_error2"] += float(
            projected[tokens:2 * tokens].square().sum()
        )
        fit["projected_elements"] += projected[tokens:2 * tokens].numel()
        offset = 2 * tokens
        for width in base.WIDTHS:
            candidate = projected[offset:offset + tokens]
            offset += tokens
            terms = scalar_terms[width]
            terms["candidate2"] += float(candidate.square().sum())
            terms["candidate_teacher"] += float((candidate * teacher).sum())
            terms["teacher2"] += float(teacher.square().sum())
    result = {
        "formula": base.finalize_formula_metrics(formula),
        "baseline_projected_error2": fit["baseline_projected_error2"],
        "projected_elements": fit["projected_elements"],
        "widths": {},
    }
    for width in base.WIDTHS:
        terms = scalar_terms[width]
        scalar = terms["candidate_teacher"] / max(terms["candidate2"], 1e-30)
        scalar = min(base.SCALAR_MAX, max(base.SCALAR_MIN, scalar))
        error2 = (
            scalar * scalar * terms["candidate2"]
            - 2.0 * scalar * terms["candidate_teacher"]
            + terms["teacher2"]
        )
        result["widths"][width] = {
            "selected": selections[width].tolist(),
            "scalar": scalar,
            "candidate_projected_error2": max(error2, 0.0),
            "projected_error_ratio": math.sqrt(
                max(error2, 0.0)
                / max(fit["baseline_projected_error2"], 1e-30)
            ),
            "retained_post_rms": base.finish_retained(fit["widths"][width]),
        }
    return result


def coordinate_lock_is_exact(value, width, base):
    return (
        isinstance(value, list)
        and len(value) == base.VALUE_HEADS
        and all(
            isinstance(row, list)
            and len(row) == width
            and len(set(row)) == width
            and all(isinstance(item, int) and 0 <= item < base.VALUE_WIDTH
                    for item in row)
            for row in value
        )
    )


def run(args):
    base, base_path = load_base()
    base.candidate_post_full = (
        lambda bundle, selected, helper:
        candidate_post_full(bundle, selected, base)
    )
    base.add_retained_metrics = (
        lambda bucket, width, bundle, candidate_selected, selected:
        add_retained_metrics(
            bucket, width, bundle, candidate_selected, selected, base
        )
    )

    capture_root = args.capture_root.resolve()
    audit_path = args.capture_audit.resolve()
    baseline_plan_path = args.baseline_plan.resolve()
    helper_source = args.helper_source.resolve()
    output_dir = args.output_dir.resolve()
    require(
        str(output_dir).startswith("/drrqr-results/")
        and not output_dir.exists()
        and not output_dir.is_symlink(),
        "fresh output below /drrqr-results required",
    )
    require(1 <= args.threads <= 64, "CPU thread bound")
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    helper = base.load_helper(helper_source)
    capture, capture_audit, plan = helper.validate_inputs(
        capture_root, audit_path, baseline_plan_path
    )
    model_root, model_index_path, model_index = base.validate_model(
        args.model_root
    )

    output_dir.mkdir(parents=False, exist_ok=False)
    base.publish(output_dir / "started.json", {
        "schema": SCHEMA,
        "status": "running",
        "claim": "CPU fit/held-out admission screen only.",
        "fit_indices": list(base.FIT_INDICES),
        "heldout_indices": list(base.HELDOUT_INDICES),
        "heldout_loaded": False,
        "threads": args.threads,
        "script_sha256": digest(__file__),
        "base_analyzer_sha256": digest(base_path),
        "helper_sha256": base.HELPER_SHA256,
        "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
        "baseline_plan_sha256": helper.BASELINE_PLAN_SHA256,
        "model_index_sha256": digest(model_index_path),
        "started_unix_ns": time.time_ns(),
    })

    fit_layers = {}
    weight_identities = {}
    for layer in base.LAYERS:
        weight, identity = base.load_out_projection(
            model_root, layer, model_index
        )
        weight_identities[str(layer)] = identity
        value = fit_layer(capture, layer, plan, weight, helper, base)
        fit_layers[str(layer)] = {
            "formula": value["formula"],
            "baseline_projected_error2": value["baseline_projected_error2"],
            "projected_elements": value["projected_elements"],
            "widths": {
                str(width): value["widths"][width] for width in base.WIDTHS
            },
        }
        del weight
    fit = base.aggregate_split(fit_layers)
    require(
        fit["formula"]["relative_l2"] <= 0.01,
        "dense post-RMS formula calibration on fit split",
    )
    layer_lock = {
        str(layer): {
            str(width): {
                "selected": fit_layers[str(layer)]["widths"][str(width)][
                    "selected"
                ],
                "scalar": fit_layers[str(layer)]["widths"][str(width)]["scalar"],
            }
            for width in base.WIDTHS
        }
        for layer in base.LAYERS
    }
    base.publish(output_dir / "fit-lock.json", {
        "schema": SCHEMA,
        "status": "fit_locked_before_heldout_load",
        "selection_scope": "one_static_coordinate_set_per_value_head",
        "scalar_scope": "one_scalar_per_layer",
        "fit_indices": list(base.FIT_INDICES),
        "heldout_indices_not_loaded": list(base.HELDOUT_INDICES),
        "widths": list(base.WIDTHS),
        "layer_lock": layer_lock,
        "weight_identities": weight_identities,
        "model_index_sha256": digest(model_index_path),
        "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
        "baseline_plan_sha256": helper.BASELINE_PLAN_SHA256,
        "locked_unix_ns": time.time_ns(),
    })

    heldout_layers = {}
    for layer in base.LAYERS:
        weight, identity = base.load_out_projection(
            model_root, layer, model_index
        )
        require(
            identity == weight_identities[str(layer)],
            f"stable checkpoint tensor identity for layer {layer}",
        )
        value = base.heldout_layer(
            capture, layer, plan, weight, layer_lock[str(layer)], helper
        )
        heldout_layers[str(layer)] = {
            "formula": value["formula"],
            "baseline_projected_error2": value["baseline_projected_error2"],
            "projected_elements": value["projected_elements"],
            "widths": {
                str(width): value["widths"][width] for width in base.WIDTHS
            },
        }
        del weight
    heldout = base.aggregate_split(heldout_layers)
    require(
        heldout["formula"]["relative_l2"] <= 0.01,
        "dense post-RMS formula calibration on heldout split",
    )

    gates = {}
    for width in base.WIDTHS:
        row = heldout["widths"][str(width)]
        scalars = [
            layer_lock[str(layer)][str(width)]["scalar"]
            for layer in base.LAYERS
        ]
        coordinate_sets = [
            layer_lock[str(layer)][str(width)]["selected"]
            for layer in base.LAYERS
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
                all(base.SCALAR_MIN <= value <= base.SCALAR_MAX
                    for value in scalars),
            "all_per_head_coordinate_counts_exact":
                all(coordinate_lock_is_exact(value, width, base)
                    for value in coordinate_sets),
        }
        gates[str(width)]["all"] = all(gates[str(width)].values())
    admitted_width = next(
        (width for width in base.WIDTHS if gates[str(width)]["all"]), None
    )
    status = (
        "admitted_to_plugin_implementation"
        if admitted_width is not None else "rejected"
    )
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "Representative-layer CPU output-fidelity screen only. Passing "
            "admits one plugin implementation and target-NPU numerical gate; "
            "it does not establish NPU correctness, endpoint speedup, task "
            "accuracy, paper-exact StrongRRQR reproduction, or portability."
        ),
        "candidate": (
            "frozen energy-Dk64 plus static per-value-head aligned "
            "value/state-width coordinates"
        ),
        "paper_exact_strong_rrqr": False,
        "fit_indices": list(base.FIT_INDICES),
        "heldout_indices": list(base.HELDOUT_INDICES),
        "heldout_loaded_only_after_fit_lock": True,
        "fit_lock_sha256": digest(output_dir / "fit-lock.json"),
        "selection_scope": "one_static_coordinate_set_per_value_head",
        "scalar_scope": "one_scalar_per_layer",
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
            f"Implement only Dv{admitted_width} in the plugin and require "
            "native prefill/decode multi-step state plus NPUGraph numerical "
            "gates."
            if admitted_width is not None
            else "Reject per-head value/state-width coordinates; do not "
                 "integrate, benchmark, run task accuracy, or tune nearby "
                 "selectors."
        ),
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "base_analyzer_path": str(base_path),
            "base_analyzer_sha256": digest(base_path),
            "helper_path": str(helper_source),
            "helper_sha256": base.HELPER_SHA256,
            "python": sys.version,
            "torch": torch.__version__,
            "safetensors": getattr(sys.modules["safetensors"], "__version__", None),
            "threads": args.threads,
        },
        "completed_unix_ns": time.time_ns(),
    }
    base.publish(output_dir / "report.json", report)
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
        report = run(args)
    except Exception as error:
        base, _ = load_base()
        output_dir = args.output_dir.resolve()
        failure_path = output_dir / "failure.json"
        if (
            str(output_dir).startswith("/drrqr-results/")
            and output_dir.is_dir()
            and not failure_path.exists()
        ):
            base.publish(failure_path, {
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
            str(width): {
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
            for width in (64, 48)
        },
    }, indent=2))


if __name__ == "__main__":
    main()
