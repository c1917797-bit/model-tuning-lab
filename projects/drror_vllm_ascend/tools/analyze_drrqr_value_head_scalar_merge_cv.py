#!/usr/bin/env python3
"""Cross-validate a one-of-three scalar value-head merge for energy-Dk64.

Each key head keeps one complete Dv128 value head.  The three original output
projection blocks are folded into the retained block with three bounded
calibration scalars.  The script uses only indices 0-11 in predeclared
cross-validation folds.  Passing admits a fresh teacher capture, not NPU or
endpoint claims.
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


SCHEMA = "drrqr-value-head-scalar-merge-cv/v1"
BASE_ANALYZER_SHA256 = "8d56fbe4fa992acd2384cd736045c1c28d2914e8d23f8e720e6f5c71833725c8"
VALUE_WIDTH_REPORT_SHA256 = "f9dba2a1735b6379116a798ae7523200bc8c5688f4d64cb374353e175a81e121"
VALUE_HEADS = 48
KEY_HEADS = 16
GROUP_SIZE = 3
TARGET_VALUE_HEADS = 16
CONTROL_VALUE_HEADS = 32
HEAD_DIM = 128
SCALAR_MIN = -2.0
SCALAR_MAX = 2.0
FOLDS = (
    ((1, 2, 4, 5, 7, 8, 10, 11), (0, 3, 6, 9)),
    ((0, 2, 3, 5, 6, 8, 9, 11), (1, 4, 7, 10)),
    ((0, 1, 3, 4, 6, 7, 9, 10), (2, 5, 8, 11)),
)


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
    require(path.is_file() and not path.is_symlink(), f"regular JSON: {path}")
    return json.loads(path.read_bytes())


def load_base():
    path = Path(__file__).resolve().with_name(
        "analyze_drrqr_value_width_heldout.py"
    )
    require(path.is_file() and not path.is_symlink(), "regular base analyzer")
    require(digest(path) == BASE_ANALYZER_SHA256, "base analyzer SHA256")
    spec = importlib.util.spec_from_file_location(
        "drrqr_value_head_merge_base", path
    )
    require(spec is not None and spec.loader is not None, "base import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def source_identity(path, fragments):
    path = Path(path).resolve()
    require(path.is_file() and not path.is_symlink(), f"regular source: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [fragment for fragment in fragments if fragment not in text]
    require(not missing, f"missing source contract in {path}: {missing}")
    return {
        "path": str(path),
        "sha256": digest(path),
        "required_fragments": list(fragments),
    }


def cost_ceiling(report, target_heads):
    require(target_heads in (CONTROL_VALUE_HEADS, TARGET_VALUE_HEADS),
            "bounded value-head candidate")
    removed = (VALUE_HEADS - target_heads) / VALUE_HEADS
    components = {}
    total_credit = 0.0
    for name, row in report["trace_contract"]["component_rank_means"].items():
        rule = row["scaling_rule"]
        if rule == "all_value":
            fraction = removed
        elif rule == "qkv_value_share":
            fraction = removed * (1536 / 2048)
        elif rule == "qkvz_value_share":
            fraction = removed * (3072 / 3584)
        elif rule == "one_of_three_value_slices":
            fraction = removed / 3
        else:
            raise ValueError(f"unknown scaling rule: {rule}")
        credit = row["rank_mean_kernel_sum_ms"] / 30.0 * fraction
        total_credit += credit
        components[name] = {
            "reduction_fraction": fraction,
            "optimistic_tpot_credit_ms": credit,
        }
    cost = report["cost_model"]
    ceiling_tpot = cost["energy_dk64_tpot_ms"] - total_credit
    ceiling_tps = (
        cost["energy_dk64_output_tps"]
        * cost["energy_dk64_tpot_ms"]
        / ceiling_tpot
    )
    gain = (
        ceiling_tps / cost["frozen_dense_output_tps"] - 1.0
    ) * 100.0
    return {
        "value_heads": target_heads,
        "removed_fraction": removed,
        "components": components,
        "optimistic_tpot_credit_ms": total_credit,
        "optimistic_tpot_ceiling_ms": ceiling_tpot,
        "optimistic_output_tps_ceiling": ceiling_tps,
        "optimistic_gain_vs_dense_percent": gain,
        "crosses_fixed_target":
            ceiling_tps >= cost["fixed_target_output_tps"],
    }


def load_split(capture, indices, layer, plan, helper, base):
    rows = [
        base.load_global_sequence(capture, index, layer, plan, helper)
        for index in indices
    ]
    formula = base.formula_metrics_zero()
    for row in rows:
        base.add_formula_metrics(formula, row["formula"])
    weights = [row["weight"] for row in rows]
    require(all(torch.equal(weights[0], item) for item in weights[1:]),
            "stable norm weight within split")
    return {
        "dense": torch.cat([row["dense"] for row in rows], dim=0),
        "baseline": torch.cat([row["baseline"] for row in rows], dim=0),
        "formula": base.finalize_formula_metrics(formula),
    }


def fit_layer(bundle, weight, base):
    dense = bundle["dense"].double()
    baseline = bundle["baseline"].double()
    require(dense.shape[1:] == (VALUE_HEADS, HEAD_DIM), "fit geometry")
    column_norm2 = weight.double().square().sum(dim=0).reshape(
        VALUE_HEADS, HEAD_DIM
    )
    groups = {}
    for group in range(KEY_HEADS):
        heads = tuple(range(group * GROUP_SIZE, (group + 1) * GROUP_SIZE))
        choices = []
        for representative in heads:
            source = baseline[:, representative, :]
            scalars = []
            score = 0.0
            for head in heads:
                importance = column_norm2[head][None, :]
                denominator = float((source.square() * importance).sum())
                numerator = float(
                    (source * dense[:, head, :] * importance).sum()
                )
                scalar = numerator / max(denominator, 1e-30)
                scalar = min(SCALAR_MAX, max(SCALAR_MIN, scalar))
                residual = scalar * source - dense[:, head, :]
                score += float((residual.square() * importance).sum())
                scalars.append(scalar)
            choices.append({
                "representative": representative,
                "scalars": scalars,
                "fit_weighted_error2": score,
            })
        selected = min(
            choices,
            key=lambda item: (item["fit_weighted_error2"],
                              item["representative"]),
        )
        groups[str(group)] = {
            "heads": list(heads),
            **selected,
        }
    return groups


def validate_lock(groups):
    require(set(groups) == {str(index) for index in range(KEY_HEADS)},
            "exact key-head group coverage")
    representatives = []
    for group in range(KEY_HEADS):
        item = groups[str(group)]
        heads = list(range(group * GROUP_SIZE, (group + 1) * GROUP_SIZE))
        require(item["heads"] == heads, f"group {group} heads")
        require(item["representative"] in heads, f"group {group} representative")
        require(len(item["scalars"]) == GROUP_SIZE, f"group {group} scalars")
        require(
            all(
                math.isfinite(value) and SCALAR_MIN <= value <= SCALAR_MAX
                for value in item["scalars"]
            ),
            f"group {group} scalar bounds",
        )
        representatives.append(item["representative"])
    require(len(set(representatives)) == TARGET_VALUE_HEADS,
            "one retained value head per key head")


def evaluate_layer(bundle, weight, groups, base):
    validate_lock(groups)
    dense = bundle["dense"].float()
    baseline = bundle["baseline"].float()
    require(dense.shape[1:] == (VALUE_HEADS, HEAD_DIM), "evaluation geometry")
    reconstructed = torch.empty_like(dense)
    reduced = []
    merged_blocks = []
    for group in range(KEY_HEADS):
        item = groups[str(group)]
        representative = item["representative"]
        source = baseline[:, representative, :]
        reduced.append(source)
        merged = torch.zeros(
            weight.shape[0], HEAD_DIM, dtype=weight.dtype
        )
        for offset, head in enumerate(item["heads"]):
            scalar = item["scalars"][offset]
            reconstructed[:, head, :] = scalar * source
            start = head * HEAD_DIM
            merged += scalar * weight[:, start:start + HEAD_DIM]
        merged_blocks.append(merged)
    reduced_value = torch.cat(reduced, dim=-1)
    reduced_weight = torch.cat(merged_blocks, dim=-1)
    dense_output = torch.mm(base.flattened(dense), weight.t())
    baseline_output = torch.mm(base.flattened(baseline), weight.t())
    candidate_output = torch.mm(reduced_value, reduced_weight.t())
    require(
        torch.isfinite(candidate_output).all()
        and torch.isfinite(reconstructed).all(),
        "finite merged outputs",
    )
    baseline_delta = baseline_output - dense_output
    candidate_delta = candidate_output - dense_output
    baseline_feature_delta = baseline - dense
    candidate_feature_delta = reconstructed - dense
    return {
        "formula": bundle["formula"],
        "baseline_projected_error2": float(baseline_delta.square().sum()),
        "candidate_projected_error2": float(candidate_delta.square().sum()),
        "projected_elements": baseline_delta.numel(),
        "baseline_feature_error2": float(
            baseline_feature_delta.square().sum()
        ),
        "candidate_feature_error2": float(
            candidate_feature_delta.square().sum()
        ),
        "feature_elements": baseline_feature_delta.numel(),
        "projected_error_ratio": math.sqrt(
            float(candidate_delta.square().sum())
            / max(float(baseline_delta.square().sum()), 1e-30)
        ),
        "feature_error_ratio": math.sqrt(
            float(candidate_feature_delta.square().sum())
            / max(float(baseline_feature_delta.square().sum()), 1e-30)
        ),
    }


def aggregate(folds, base):
    totals = {
        "baseline_projected_error2": 0.0,
        "candidate_projected_error2": 0.0,
        "projected_elements": 0,
        "baseline_feature_error2": 0.0,
        "candidate_feature_error2": 0.0,
        "feature_elements": 0,
    }
    formula = base.formula_metrics_zero()
    fold_ratios = []
    layer_fold_ratios = []
    for fold in folds:
        fold_baseline = 0.0
        fold_candidate = 0.0
        for layer in base.LAYERS:
            row = fold["layers"][str(layer)]
            base.add_formula_metrics(formula, {
                key: row["formula"][key] for key in formula
            })
            for key in totals:
                totals[key] += row[key]
            fold_baseline += row["baseline_projected_error2"]
            fold_candidate += row["candidate_projected_error2"]
            layer_fold_ratios.append(row["projected_error_ratio"])
        fold_ratios.append(
            math.sqrt(fold_candidate / max(fold_baseline, 1e-30))
        )
    return {
        **totals,
        "formula": base.finalize_formula_metrics(formula),
        "aggregate_projected_error_ratio": math.sqrt(
            totals["candidate_projected_error2"]
            / max(totals["baseline_projected_error2"], 1e-30)
        ),
        "aggregate_feature_error_ratio": math.sqrt(
            totals["candidate_feature_error2"]
            / max(totals["baseline_feature_error2"], 1e-30)
        ),
        "fold_projected_error_ratios": fold_ratios,
        "worst_fold_projected_error_ratio": max(fold_ratios),
        "layer_fold_projected_error_ratios": layer_fold_ratios,
        "layer_fold_ratio_at_most_1_10_fraction": (
            sum(value <= 1.10 for value in layer_fold_ratios)
            / len(layer_fold_ratios)
        ),
        "worst_layer_fold_projected_error_ratio": max(layer_fold_ratios),
    }


def run(args):
    base, base_path = load_base()
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
    helper = base.load_helper(args.helper_source)
    capture, capture_audit, plan = helper.validate_inputs(
        args.capture_root, args.capture_audit, args.baseline_plan
    )
    model_root, model_index_path, model_index = base.validate_model(
        args.model_root
    )
    value_report = read_json(args.value_width_report)
    require(
        digest(args.value_width_report) == VALUE_WIDTH_REPORT_SHA256,
        "value-width report SHA256",
    )
    require(
        value_report.get("schema") == "drrqr-two-sided-value-width-admission/v1",
        "value-width report schema",
    )
    costs = {
        str(heads): cost_ceiling(value_report, heads)
        for heads in (CONTROL_VALUE_HEADS, TARGET_VALUE_HEADS)
    }
    require(not costs["32"]["crosses_fixed_target"], "Nv32 cost control")
    require(costs["16"]["crosses_fixed_target"], "Nv16 cost admission")
    sources = {
        "upstream_gdn": source_identity(args.upstream_gdn_source, (
            "self.num_v_heads = config.linear_num_value_heads",
            "self.in_proj_ba = self.create_ba_proj(",
            "self.dt_bias = nn.Parameter(",
            "self.A_log = nn.Parameter(",
            "self.out_proj = RowParallelLinear(",
        )),
        "ascend_gdn": source_identity(args.ascend_gdn_source, (
            "DeviceOperator.fused_gdn_gating(self.A_log, a, b, self.dt_bias)",
            "torch.ops._C_ascend.npu_recurrent_gated_delta_rule(",
            "self.num_v_heads // self.tp_size",
        )),
        "recurrent_tiling": source_identity(args.recurrent_tiling_source, (
            "tilingData_.nv = valueShape.GetDim(DIM_1);",
            "tilingData_.nv % tilingData_.nk != 0",
        )),
    }

    output_dir.mkdir(parents=False, exist_ok=False)
    base.publish(output_dir / "started.json", {
        "schema": SCHEMA,
        "status": "running",
        "claim": "Reused-corpus CPU cross-validation screen only.",
        "folds": [
            {"fit": list(fit), "validation": list(validation)}
            for fit, validation in FOLDS
        ],
        "validation_loaded": False,
        "script_sha256": digest(__file__),
        "base_analyzer_sha256": digest(base_path),
        "value_width_report_sha256": digest(args.value_width_report),
        "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
        "baseline_plan_sha256": helper.BASELINE_PLAN_SHA256,
        "model_index_sha256": digest(model_index_path),
        "threads": args.threads,
        "started_unix_ns": time.time_ns(),
    })

    folds = []
    weight_identities = {}
    for fold_index, (fit_indices, validation_indices) in enumerate(FOLDS):
        layer_lock = {}
        for layer in base.LAYERS:
            weight, identity = base.load_out_projection(
                model_root, layer, model_index
            )
            if str(layer) in weight_identities:
                require(
                    identity == weight_identities[str(layer)],
                    f"stable checkpoint identity layer {layer}",
                )
            else:
                weight_identities[str(layer)] = identity
            fit_bundle = load_split(
                capture, fit_indices, layer, plan, helper, base
            )
            require(
                fit_bundle["formula"]["relative_l2"] <= 0.01,
                f"fit formula layer {layer}",
            )
            layer_lock[str(layer)] = fit_layer(
                fit_bundle, weight, base
            )
            validate_lock(layer_lock[str(layer)])
            del fit_bundle, weight
        lock_path = output_dir / f"fold-{fold_index}-lock.json"
        base.publish(lock_path, {
            "schema": SCHEMA,
            "status": "fit_locked_before_fold_validation_load",
            "fold": fold_index,
            "fit_indices": list(fit_indices),
            "validation_indices_not_loaded": list(validation_indices),
            "scalar_bounds": [SCALAR_MIN, SCALAR_MAX],
            "layer_lock": layer_lock,
            "weight_identities": weight_identities,
            "locked_unix_ns": time.time_ns(),
        })

        layers = {}
        for layer in base.LAYERS:
            weight, identity = base.load_out_projection(
                model_root, layer, model_index
            )
            require(
                identity == weight_identities[str(layer)],
                f"evaluation checkpoint identity layer {layer}",
            )
            validation_bundle = load_split(
                capture, validation_indices, layer, plan, helper, base
            )
            require(
                validation_bundle["formula"]["relative_l2"] <= 0.01,
                f"validation formula layer {layer}",
            )
            layers[str(layer)] = evaluate_layer(
                validation_bundle, weight, layer_lock[str(layer)], base
            )
            del validation_bundle, weight
        folds.append({
            "fold": fold_index,
            "fit_indices": list(fit_indices),
            "validation_indices": list(validation_indices),
            "lock_path": str(lock_path),
            "lock_sha256": digest(lock_path),
            "layers": layers,
        })

    summary = aggregate(folds, base)
    gates = {
        "nv16_optimistic_cost_crosses_fixed_target":
            costs["16"]["crosses_fixed_target"],
        "dense_formula_relative_l2_at_most_0_01":
            summary["formula"]["relative_l2"] <= 0.01,
        "aggregate_projected_error_ratio_at_most_1_10":
            summary["aggregate_projected_error_ratio"] <= 1.10,
        "worst_fold_projected_error_ratio_at_most_1_20":
            summary["worst_fold_projected_error_ratio"] <= 1.20,
        "aggregate_feature_error_ratio_at_most_1_10":
            summary["aggregate_feature_error_ratio"] <= 1.10,
        "layer_fold_ratio_at_most_1_10_fraction_at_least_0_75":
            summary["layer_fold_ratio_at_most_1_10_fraction"] >= 0.75,
        "worst_layer_fold_projected_error_ratio_at_most_1_50":
            summary["worst_layer_fold_projected_error_ratio"] <= 1.50,
        "all_locks_exact":
            len(folds) == len(FOLDS)
            and all(len(fold["layers"]) == len(base.LAYERS) for fold in folds),
    }
    gates["all"] = all(gates.values())
    status = (
        "admitted_to_fresh_teacher_capture"
        if gates["all"] else "rejected"
    )
    report = {
        "schema": SCHEMA,
        "status": status,
        "claim": (
            "Reused-corpus CPU cross-validation and optimistic profile-cost "
            "screen only. Passing admits a new untouched teacher capture; it "
            "does not prove NPU correctness, endpoint performance, task "
            "accuracy, paper-exact StrongRRQR reproduction, or portability."
        ),
        "candidate": (
            "energy-Dk64 plus one-of-three complete-Dv128 value-head scalar "
            "merge, reducing global Nv48 to Nv16"
        ),
        "paper_exact_strong_rrqr": False,
        "gradient_or_task_label_training": False,
        "folds": folds,
        "summary": summary,
        "gates": gates,
        "cost_model": costs,
        "foldability": {
            "retained_head_dim": HEAD_DIM,
            "rms_denominator_changed": False,
            "global_key_heads": KEY_HEADS,
            "global_value_heads_before": VALUE_HEADS,
            "global_value_heads_after": TARGET_VALUE_HEADS,
            "tp_size": 4,
            "local_key_heads": 4,
            "local_value_heads_after": 4,
            "native_nv_multiple_of_nk": True,
            "static_cut_points": [
                "V and Z projection rows",
                "A and B projection rows",
                "A_log and dt_bias entries",
                "value convolution channels",
                "recurrent state value-head axis",
                "core output value-head axis",
                "folded output-projection blocks",
            ],
            "runtime_dynamic_gather": False,
        },
        "attribution_required_before_endpoint": [
            "Dk128/Nv48",
            "Dk64/Nv48",
            "Dk128/Nv16",
            "Dk64/Nv16",
        ],
        "decision": (
            "Collect a fresh untouched teacher corpus before any plugin or NPU "
            "candidate implementation."
            if gates["all"]
            else "Reject the scalar value-head merge; do not implement, run "
                 "NPU, benchmark an endpoint, run task accuracy, or tune "
                 "nearby scalar/head choices."
        ),
        "inputs": {
            "capture_root": str(Path(args.capture_root).resolve()),
            "capture_audit": str(Path(args.capture_audit).resolve()),
            "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
            "capture_archive_set_sha256": capture_audit["archive_set_sha256"],
            "baseline_plan": str(Path(args.baseline_plan).resolve()),
            "baseline_plan_sha256": helper.BASELINE_PLAN_SHA256,
            "value_width_report": str(Path(args.value_width_report).resolve()),
            "value_width_report_sha256": digest(args.value_width_report),
            "model_root": str(model_root),
            "model_index": str(model_index_path),
            "model_index_sha256": digest(model_index_path),
            "out_projection_tensors": weight_identities,
        },
        "sources": sources,
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "base_analyzer_path": str(base_path),
            "base_analyzer_sha256": digest(base_path),
            "helper_path": str(Path(args.helper_source).resolve()),
            "helper_sha256": base.HELPER_SHA256,
            "python": sys.version,
            "torch": torch.__version__,
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
    parser.add_argument("--value-width-report", type=Path, required=True)
    parser.add_argument("--upstream-gdn-source", type=Path, required=True)
    parser.add_argument("--ascend-gdn-source", type=Path, required=True)
    parser.add_argument("--recurrent-tiling-source", type=Path, required=True)
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
        "cost_nv16": report["cost_model"]["16"],
        "summary": {
            "projected_error_ratio":
                report["summary"]["aggregate_projected_error_ratio"],
            "feature_error_ratio":
                report["summary"]["aggregate_feature_error_ratio"],
            "worst_fold":
                report["summary"]["worst_fold_projected_error_ratio"],
            "passing": report["gates"]["all"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
