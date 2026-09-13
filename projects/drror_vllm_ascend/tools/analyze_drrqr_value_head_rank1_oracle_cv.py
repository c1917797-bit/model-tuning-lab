#!/usr/bin/env python3
"""Cross-validate a generous rank-1 value-state representation oracle.

For each global key head, the three energy-Dk64 value-head operator outputs are
projected onto one fit-locked orthogonal head-axis direction.  Validation still
uses the original three Z gates, RMS weight and output-projection blocks.  This
is deliberately more expressive than an implementable Nv16 path: failure
rejects the representation before dynamics/operator work, while success admits
only an early-dynamics foldability audit.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import torch


SCHEMA = "drrqr-value-head-rank1-oracle-cv/v1"
BASE_SHA256 = "8d56fbe4fa992acd2384cd736045c1c28d2914e8d23f8e720e6f5c71833725c8"
MERGE_REPORT_SHA256 = "d61cd9619f95a2e83fc5a51027974ae9720b81fe24ac9f7a3da6846456b49c10"
OPEN_TPOT_GAP_MS = 3.181664712
VALUE_HEADS = 48
KEY_HEADS = 16
HEADS_PER_GROUP = 3
VALUE_WIDTH = 128
FOLDS = (
    ((1, 2, 4, 5, 7, 8, 10, 11), (0, 3, 6, 9)),
    ((0, 2, 3, 5, 6, 8, 9, 11), (1, 4, 7, 10)),
    ((0, 1, 3, 4, 6, 7, 9, 10), (2, 5, 8, 11)),
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def publish(path, document):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def load_base():
    path = Path(__file__).with_name("analyze_drrqr_value_width_heldout.py")
    require(path.is_file() and digest(path) == BASE_SHA256, "base analyzer identity")
    spec = importlib.util.spec_from_file_location("drrqr_rank1_oracle_base", path)
    require(spec is not None and spec.loader is not None, "base analyzer import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def load_split(capture, indices, layer, plan, helper, base):
    values = [
        base.load_global_sequence(capture, index, layer, plan, helper)
        for index in indices
    ]
    formula = base.formula_metrics_zero()
    for value in values:
        base.add_formula_metrics(formula, value["formula"])
        require(
            torch.equal(values[0]["weight"], value["weight"]),
            "stable layer norm weight across sequences",
        )
    return {
        "dense": torch.cat([value["dense"] for value in values], dim=0),
        "baseline_operator": torch.cat(
            [value["baseline_operator"] for value in values], dim=0
        ),
        "baseline": torch.cat([value["baseline"] for value in values], dim=0),
        "z": torch.cat([value["z"] for value in values], dim=0),
        "weight": values[0]["weight"],
        "formula": formula,
    }


def canonical_direction(vector):
    vector = vector.float()
    pivot = int(torch.argmax(vector.abs()).item())
    if float(vector[pivot]) < 0.0:
        vector = -vector
    return vector


def fit_layer(bundle):
    groups = []
    operator = bundle["baseline_operator"]
    require(
        operator.ndim == 3
        and tuple(operator.shape[1:]) == (VALUE_HEADS, VALUE_WIDTH),
        "global baseline operator geometry",
    )
    for group in range(KEY_HEADS):
        start = group * HEADS_PER_GROUP
        stop = start + HEADS_PER_GROUP
        samples = (
            operator[:, start:stop]
            .permute(0, 2, 1)
            .reshape(-1, HEADS_PER_GROUP)
            .double()
        )
        gram = torch.mm(samples.t(), samples)
        eigenvalues, eigenvectors = torch.linalg.eigh(gram)
        direction = canonical_direction(eigenvectors[:, -1])
        total = float(eigenvalues.clamp_min(0).sum())
        retained = float(eigenvalues[-1].clamp_min(0))
        groups.append(
            {
                "group": group,
                "direction": [float(value) for value in direction],
                "fit_operator_energy_fraction": retained / max(total, 1e-30),
            }
        )
    return groups


def validate_lock(groups):
    require(len(groups) == KEY_HEADS, "one direction per key-head group")
    for group, item in enumerate(groups):
        require(item["group"] == group, "ordered key-head groups")
        direction = item["direction"]
        require(len(direction) == HEADS_PER_GROUP, "rank-1 direction geometry")
        norm = math.sqrt(sum(value * value for value in direction))
        require(
            all(math.isfinite(value) for value in direction)
            and abs(norm - 1.0) <= 1e-5,
            "finite unit rank-1 direction",
        )
        require(
            math.isfinite(item["fit_operator_energy_fraction"])
            and 0.0 <= item["fit_operator_energy_fraction"] <= 1.0 + 1e-8,
            "valid fit energy fraction",
        )


def evaluate_layer(bundle, weight, groups, helper, base):
    validate_lock(groups)
    baseline_operator = bundle["baseline_operator"]
    candidate_operator = torch.empty_like(baseline_operator)
    for item in groups:
        group = item["group"]
        start = group * HEADS_PER_GROUP
        stop = start + HEADS_PER_GROUP
        direction = torch.tensor(
            item["direction"], dtype=baseline_operator.dtype
        )
        value = baseline_operator[:, start:stop]
        latent = torch.einsum("thd,h->td", value, direction)
        candidate_operator[:, start:stop] = torch.einsum(
            "td,h->thd", latent, direction
        )

    candidate_post = helper.rms_gated(
        candidate_operator, bundle["z"], bundle["weight"]
    ).to(torch.bfloat16).float()
    require(
        torch.isfinite(candidate_operator).all()
        and torch.isfinite(candidate_post).all(),
        "finite oracle reconstruction",
    )
    dense_flat = base.flattened(bundle["dense"])
    baseline_flat = base.flattened(bundle["baseline"])
    candidate_flat = base.flattened(candidate_post)
    dense_output = torch.mm(dense_flat, weight.t())
    baseline_output = torch.mm(baseline_flat, weight.t())
    candidate_output = torch.mm(candidate_flat, weight.t())
    return {
        "formula": base.finalize_formula_metrics(bundle["formula"]),
        "baseline_projected_error2": float(
            (baseline_output - dense_output).square().sum()
        ),
        "candidate_projected_error2": float(
            (candidate_output - dense_output).square().sum()
        ),
        "projected_elements": dense_output.numel(),
        "baseline_feature_error2": float(
            (baseline_flat - dense_flat).square().sum()
        ),
        "candidate_feature_error2": float(
            (candidate_flat - dense_flat).square().sum()
        ),
        "feature_elements": dense_flat.numel(),
        "operator_reconstruction_error2": float(
            (candidate_operator - baseline_operator).square().sum()
        ),
        "operator_reference2": float(baseline_operator.square().sum()),
        "operator_elements": baseline_operator.numel(),
    }


def aggregate(folds):
    total = {
        "formula_error2": 0.0,
        "formula_reference2": 0.0,
        "formula_elements": 0,
        "baseline_projected_error2": 0.0,
        "candidate_projected_error2": 0.0,
        "projected_elements": 0,
        "baseline_feature_error2": 0.0,
        "candidate_feature_error2": 0.0,
        "feature_elements": 0,
        "operator_reconstruction_error2": 0.0,
        "operator_reference2": 0.0,
        "operator_elements": 0,
    }
    layer_ratios = []
    fold_ratios = []
    for fold in folds:
        fold_base = 0.0
        fold_candidate = 0.0
        for value in fold["layers"].values():
            formula = value["formula"]
            total["formula_error2"] += formula["error2"]
            total["formula_reference2"] += formula["reference2"]
            total["formula_elements"] += formula["elements"]
            for key in (
                "baseline_projected_error2",
                "candidate_projected_error2",
                "projected_elements",
                "baseline_feature_error2",
                "candidate_feature_error2",
                "feature_elements",
                "operator_reconstruction_error2",
                "operator_reference2",
                "operator_elements",
            ):
                total[key] += value[key]
            fold_base += value["baseline_projected_error2"]
            fold_candidate += value["candidate_projected_error2"]
            layer_ratios.append(
                math.sqrt(
                    value["candidate_projected_error2"]
                    / max(value["baseline_projected_error2"], 1e-30)
                )
            )
        fold_ratios.append(math.sqrt(fold_candidate / max(fold_base, 1e-30)))
    return {
        **total,
        "formula_relative_l2": math.sqrt(
            total["formula_error2"] / max(total["formula_reference2"], 1e-30)
        ),
        "projected_error_ratio": math.sqrt(
            total["candidate_projected_error2"]
            / max(total["baseline_projected_error2"], 1e-30)
        ),
        "feature_error_ratio": math.sqrt(
            total["candidate_feature_error2"]
            / max(total["baseline_feature_error2"], 1e-30)
        ),
        "operator_reconstruction_relative_l2": math.sqrt(
            total["operator_reconstruction_error2"]
            / max(total["operator_reference2"], 1e-30)
        ),
        "fold_projected_error_ratios": fold_ratios,
        "worst_fold_projected_error_ratio": max(fold_ratios),
        "layer_fold_projected_error_ratios": layer_ratios,
        "layer_fold_ratio_at_most_1_10_fraction": (
            sum(value <= 1.10 for value in layer_ratios) / len(layer_ratios)
        ),
        "worst_layer_fold_projected_error_ratio": max(layer_ratios),
    }


def run(args):
    base, base_path = load_base()
    require(
        VALUE_HEADS == base.VALUE_HEADS
        and VALUE_WIDTH == base.VALUE_WIDTH
        and KEY_HEADS * HEADS_PER_GROUP == VALUE_HEADS,
        "base geometry identity",
    )
    helper = base.load_helper(args.helper_source)
    capture, capture_audit, plan = helper.validate_inputs(
        args.capture_root, args.capture_audit, args.baseline_plan
    )
    merge_report = read_json(args.merge_report)
    require(
        digest(args.merge_report) == MERGE_REPORT_SHA256,
        "scalar-merge report identity",
    )
    require(
        merge_report.get("schema") == "drrqr-value-head-scalar-merge-cv/v1"
        and merge_report.get("status") == "rejected",
        "scalar-merge decision identity",
    )
    cost = merge_report["cost_model"]["16"]
    components = cost["components"]
    generous_post_source_credit = sum(
        components[name]["optimistic_tpot_credit_ms"]
        for name in ("recurrent", "rms_norm", "output_projection", "packed_concat")
    )
    output_dir = Path(args.output_dir).resolve()
    require(
        str(output_dir).startswith("/drrqr-results/")
        and not output_dir.exists()
        and not output_dir.is_symlink(),
        "fresh output below /drrqr-results required",
    )
    output_dir.mkdir(parents=True)
    started = {
        "schema": SCHEMA,
        "started_unix_ns": time.time_ns(),
        "script_sha256": digest(__file__),
        "base_analyzer_sha256": digest(base_path),
        "merge_report_sha256": digest(args.merge_report),
        "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
        "capture_archive_set_sha256": capture_audit["archive_set_sha256"],
        "folds": [
            {"fit": list(fit), "validation": list(validation)}
            for fit, validation in FOLDS
        ],
    }
    publish(output_dir / "started.json", started)

    model_root, model_index_path, model_index = base.validate_model(
        args.model_root
    )
    folds = []
    projection_identity = {}
    for fold_index, (fit_indices, validation_indices) in enumerate(FOLDS):
        layer_locks = {}
        for layer in base.LAYERS:
            fit_bundle = load_split(
                capture, fit_indices, layer, plan, helper, base
            )
            layer_locks[str(layer)] = fit_layer(fit_bundle)
        lock = {
            "schema": SCHEMA + "/fit-lock",
            "fold": fold_index,
            "fit_indices": list(fit_indices),
            "validation_indices_not_loaded": list(validation_indices),
            "layers": layer_locks,
        }
        lock_path = output_dir / f"fold-{fold_index}-lock.json"
        publish(lock_path, lock)
        lock_sha256 = digest(lock_path)
        locked = read_json(lock_path)
        require(locked == lock and digest(lock_path) == lock_sha256, "exact fit lock")

        layers = {}
        for layer in base.LAYERS:
            weight, identity = base.load_out_projection(
                model_root, layer, model_index
            )
            projection_identity[str(layer)] = identity
            validation_bundle = load_split(
                capture, validation_indices, layer, plan, helper, base
            )
            value = evaluate_layer(
                validation_bundle,
                weight,
                locked["layers"][str(layer)],
                helper,
                base,
            )
            value["projected_error_ratio"] = math.sqrt(
                value["candidate_projected_error2"]
                / max(value["baseline_projected_error2"], 1e-30)
            )
            value["feature_error_ratio"] = math.sqrt(
                value["candidate_feature_error2"]
                / max(value["baseline_feature_error2"], 1e-30)
            )
            layers[str(layer)] = value
        folds.append(
            {
                "fold": fold_index,
                "fit_indices": list(fit_indices),
                "validation_indices": list(validation_indices),
                "lock_path": str(lock_path),
                "lock_sha256": lock_sha256,
                "layers": layers,
            }
        )

    summary = aggregate(folds)
    gates = {
        "all_locks_exact": len(folds) == len(FOLDS)
        and all(len(fold["layers"]) == len(base.LAYERS) for fold in folds),
        "dense_formula_relative_l2_at_most_0_01":
            summary["formula_relative_l2"] <= 0.01,
        "aggregate_projected_error_ratio_at_most_1_10":
            summary["projected_error_ratio"] <= 1.10,
        "aggregate_feature_error_ratio_at_most_1_10":
            summary["feature_error_ratio"] <= 1.10,
        "worst_fold_projected_error_ratio_at_most_1_20":
            summary["worst_fold_projected_error_ratio"] <= 1.20,
        "layer_fold_ratio_at_most_1_10_fraction_at_least_0_75":
            summary["layer_fold_ratio_at_most_1_10_fraction"] >= 0.75,
        "worst_layer_fold_projected_error_ratio_at_most_1_50":
            summary["worst_layer_fold_projected_error_ratio"] <= 1.50,
    }
    gates["all"] = all(gates.values())
    report = {
        "schema": SCHEMA,
        "status": (
            "admitted_to_early_dynamics_foldability_audit"
            if gates["all"] else "rejected"
        ),
        "completed_unix_ns": time.time_ns(),
        "candidate": (
            "fit-locked rank-1 projection across each three-value-head "
            "energy-Dk64 operator-state group"
        ),
        "claim": (
            "Reused-corpus CPU representation oracle only. It retains the "
            "original three Z gates, RMS applications and output blocks and "
            "reconstructs from all three Dk64 operator outputs. Passing does "
            "not establish an implementable recurrence, NPU correctness, "
            "endpoint performance, accuracy, paper-exact StrongRRQR or portability."
        ),
        "paper_exact_strong_rrqr": False,
        "gradient_or_task_label_training": False,
        "oracle_favors_candidate": [
            "uses all three energy-Dk64 operator outputs to form the latent state",
            "uses original per-head Z gates and RMS weight",
            "expands back to 48 heads before the exact checkpoint output projection",
            "does not charge encoding, reconstruction or altered dynamics error",
        ],
        "cost_boundary": {
            "open_tpot_gap_ms": OPEN_TPOT_GAP_MS,
            "nv16_full_path_optimistic_output_tps_ceiling":
                cost["optimistic_output_tps_ceiling"],
            "nv16_full_path_crosses_fixed_target": cost["crosses_fixed_target"],
            "generous_post_value_source_credit_ms": generous_post_source_credit,
            "generous_post_value_source_shortfall_ms":
                OPEN_TPOT_GAP_MS - generous_post_source_credit,
            "post_value_source_route_crosses_gap":
                generous_post_source_credit >= OPEN_TPOT_GAP_MS,
            "interpretation": (
                "Even perfect removal of recurrent, post-RMS, output-projection "
                "and packed-concat cost after retaining dense value-source work "
                "does not close the gap. A successful representation oracle "
                "would still require a separately valid pre-convolution/projection "
                "dynamics fold."
            ),
        },
        "summary": summary,
        "gates": gates,
        "folds": folds,
        "decision": (
            "Proceed only to an early-dynamics foldability audit; do not run NPU."
            if gates["all"]
            else "Reject the grouped rank-1 value-state representation before "
            "early-dynamics design, NPU, endpoint or accuracy work."
        ),
        "inputs": {
            "capture_root": str(Path(args.capture_root).resolve()),
            "capture_audit_sha256": helper.CAPTURE_AUDIT_SHA256,
            "capture_archive_set_sha256": capture_audit["archive_set_sha256"],
            "baseline_plan": str(Path(args.baseline_plan).resolve()),
            "baseline_plan_sha256": digest(args.baseline_plan),
            "merge_report": str(Path(args.merge_report).resolve()),
            "merge_report_sha256": digest(args.merge_report),
            "model_root": str(model_root),
            "model_index": str(model_index_path),
            "model_index_sha256": digest(model_index_path),
            "out_projection_tensors": projection_identity,
        },
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "base_analyzer_path": str(base_path.resolve()),
            "base_analyzer_sha256": digest(base_path),
            "helper_path": str(Path(args.helper_source).resolve()),
            "helper_sha256": digest(args.helper_source),
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "threads": torch.get_num_threads(),
        },
    }
    publish(output_dir / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--capture-audit", type=Path, required=True)
    parser.add_argument("--baseline-plan", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--helper-source", type=Path, required=True)
    parser.add_argument("--merge-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=32)
    args = parser.parse_args(argv)
    require(1 <= args.threads <= 64, "CPU thread bound")
    torch.set_num_threads(args.threads)
    report = run(args)
    print(
        json.dumps(
            {
                "status": report["status"],
                "cost_boundary": report["cost_boundary"],
                "summary": {
                    "projected_error_ratio":
                        report["summary"]["projected_error_ratio"],
                    "feature_error_ratio":
                        report["summary"]["feature_error_ratio"],
                    "operator_reconstruction_relative_l2":
                        report["summary"]["operator_reconstruction_relative_l2"],
                    "worst_fold":
                        report["summary"]["worst_fold_projected_error_ratio"],
                    "passing": report["gates"]["all"],
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
