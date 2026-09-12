#!/usr/bin/env python3
"""Audit a two-sided Dk64/value-width DRRQR extension before fidelity work.

This tool consumes frozen source, checkpoint, profile, baseline, and capture
evidence.  It deliberately computes an optimistic endpoint ceiling: each
width-dependent kernel contribution is assumed to scale linearly and every
saved kernel microsecond is assumed to reduce TPOT.  The result may admit a
cheap held-out numerical screen; it is never a performance prediction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import struct


SCHEMA = "drrqr-two-sided-value-width-admission/v1"
PROFILE_SCHEMA = "drrqr-profile-timeline-summary/v1"
PROFILE_COMPARISON_SCHEMA = "drrqr-paired-profile/v1"
BASELINE_SCHEMA = "drrqr-frozen-baseline/v1"
SCREEN_SCHEMA = "drrqr-dk64-dense-common-optimized-screen/v1"
CAPTURE_SCHEMA = "drrqr-gdn-rich-state-calibration-summary/v1"
DECODE_STEPS = 30
TP_SIZE = 4
DK = 64
DV = 128
WIDTHS = (96, 80, 64, 48, 32)


COMPONENTS = {
    "qkvz_projection": {
        "type": "MatMulV2",
        "shape": "16,5120;3584,5120",
        "expected_count_per_rank": 1920,
        "linear_layer_fraction": 48 / 64,
        "scale": "qkvz_value_share",
        "expected_rank_mean_ms": 83.100735,
    },
    "output_projection": {
        "type": "MatMulV2",
        "shape": "16,1536;5120,1536",
        "expected_count_per_rank": 1920,
        "linear_layer_fraction": 48 / 64,
        "scale": "all_value",
        "expected_rank_mean_ms": 39.85987875,
    },
    "recurrent": {
        "type": "RecurrentGatedDeltaRule",
        "shape": None,
        "expected_count_per_rank": 1440,
        "linear_layer_fraction": 1.0,
        "scale": "all_value",
        "expected_rank_mean_ms": 55.04681,
    },
    "causal_conv": {
        "type": "CausalConv1d",
        "shape": None,
        "expected_count_per_rank": 1440,
        "linear_layer_fraction": 1.0,
        "scale": "qkv_value_share",
        "expected_rank_mean_ms": 27.89932,
    },
    "rms_norm": {
        "type": "_layer_norm_fwd_1pass_kernel_npu",
        "shape": None,
        "expected_count_per_rank": 1440,
        "linear_layer_fraction": 1.0,
        "scale": "all_value",
        "expected_rank_mean_ms": 7.91812,
    },
    "packed_concat": {
        "type": "ConcatD",
        "shape": "4096;4096;24576",
        "expected_count_per_rank": 1440,
        "linear_layer_fraction": 1.0,
        "scale": "qkv_value_share",
        "expected_rank_mean_ms": 21.657215,
    },
    "qkv_slices": {
        "type": "Slice",
        "shape": "16,2048;2;2",
        "expected_count_per_rank": 4320,
        "linear_layer_fraction": 1.0,
        "scale": "one_of_three_value_slices",
        "expected_rank_mean_ms": 11.80838,
    },
    "qkvz_split": {
        "type": "Slice",
        "shape": "16,3584;2;2",
        "expected_count_per_rank": 1440,
        "linear_layer_fraction": 1.0,
        "scale": "qkvz_value_share",
        "expected_rank_mean_ms": 4.197305,
    },
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def regular(path: str | Path) -> Path:
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"regular file required: {path}")
    return path


def digest(path: str | Path) -> str:
    result = hashlib.sha256()
    with regular(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path: str | Path) -> dict:
    return json.loads(regular(path).read_bytes())


def publish(path: str | Path, document: dict) -> None:
    path = Path(path)
    require(path.is_absolute(), "output must be absolute")
    require(not path.exists() and not path.is_symlink(), f"fresh output required: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    require(not partial.exists() and not partial.is_symlink(), f"stale partial: {partial}")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def source_identity(path: str | Path, required_fragments: tuple[str, ...]) -> dict:
    path = regular(path)
    text = path.read_text(encoding="utf-8")
    missing = [fragment for fragment in required_fragments if fragment not in text]
    require(not missing, f"source contract missing from {path}: {missing}")
    return {"path": str(path), "sha256": digest(path), "required_fragments": list(required_fragments)}


def safetensors_header(path: str | Path) -> tuple[dict, str]:
    path = regular(path)
    with path.open("rb") as stream:
        raw_size = stream.read(8)
        require(len(raw_size) == 8, "truncated safetensors header size")
        size = struct.unpack("<Q", raw_size)[0]
        require(0 < size < 128 * 1024 * 1024, f"invalid safetensors header size: {size}")
        raw_header = stream.read(size)
        require(len(raw_header) == size, "truncated safetensors header")
    return json.loads(raw_header), hashlib.sha256(raw_size + raw_header).hexdigest()


def checkpoint_shapes(path: str | Path) -> tuple[dict, str]:
    header, header_sha256 = safetensors_header(path)
    expected = {
        "model.language_model.layers.0.linear_attn.conv1d.weight": [10240, 1, 4],
        "model.language_model.layers.0.linear_attn.in_proj_qkv.weight": [10240, 5120],
        "model.language_model.layers.0.linear_attn.in_proj_z.weight": [6144, 5120],
        "model.language_model.layers.0.linear_attn.norm.weight": [128],
        "model.language_model.layers.0.linear_attn.out_proj.weight": [5120, 6144],
    }
    actual = {}
    for name, shape in expected.items():
        require(name in header, f"checkpoint tensor missing: {name}")
        actual[name] = header[name].get("shape")
        require(actual[name] == shape, f"checkpoint shape mismatch for {name}: {actual[name]}")
    return actual, header_sha256


def normalized_shape(value: str) -> str:
    return value.strip().strip('"')


def extract_profile_costs(profile: dict) -> tuple[dict, list[dict]]:
    require(profile.get("schema") == PROFILE_SCHEMA, "profile schema")
    require(profile.get("status") == "eight_traces_validated", "profile status")
    require(profile.get("variant") == "dk64", "profile variant")
    records = [record for record in profile.get("records", []) if record.get("phase") == "decode"]
    require(len(records) == TP_SIZE, f"four decode traces required, got {len(records)}")
    require({record.get("rank") for record in records} == set(range(TP_SIZE)), "decode rank coverage")
    per_rank = []
    aggregates = {name: [] for name in COMPONENTS}
    for record in sorted(records, key=lambda item: item["rank"]):
        csv_path = regular(Path(record["trace_dir"]) / "ASCEND_PROFILER_OUTPUT" / "kernel_details.csv")
        actual_csv_sha = digest(csv_path)
        require(
            actual_csv_sha == record["sha256"]["kernel_details.csv"],
            f"kernel CSV identity for rank {record['rank']}",
        )
        rank_result = {"rank": record["rank"], "kernel_csv": str(csv_path), "kernel_csv_sha256": actual_csv_sha}
        rows = []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows.extend(csv.DictReader(stream))
        for name, contract in COMPONENTS.items():
            matches = [
                row
                for row in rows
                if row["Type"] == contract["type"]
                and (
                    contract["shape"] is None
                    or normalized_shape(row["Input Shapes"]) == contract["shape"]
                )
            ]
            require(
                len(matches) == contract["expected_count_per_rank"],
                f"{name} count rank {record['rank']}: {len(matches)}",
            )
            raw_ms = sum(float(row["Duration(us)"]) for row in matches) / 1000.0
            attributed_ms = raw_ms * contract["linear_layer_fraction"]
            rank_result[name] = {
                "raw_count": len(matches),
                "raw_kernel_sum_ms": raw_ms,
                "attributed_kernel_sum_ms": attributed_ms,
            }
            aggregates[name].append(attributed_ms)
        per_rank.append(rank_result)

    means = {}
    for name, values in aggregates.items():
        mean = sum(values) / len(values)
        expected = COMPONENTS[name]["expected_rank_mean_ms"]
        require(math.isclose(mean, expected, rel_tol=0.0, abs_tol=1e-6), f"{name} mean {mean} != {expected}")
        means[name] = {
            "rank_mean_kernel_sum_ms": mean,
            "rank_values_ms": values,
            "expected_count_per_rank": COMPONENTS[name]["expected_count_per_rank"],
            "linear_layer_fraction": COMPONENTS[name]["linear_layer_fraction"],
            "scaling_rule": COMPONENTS[name]["scale"],
        }
    return means, per_rank


def reduction_fraction(rule: str, width: int) -> float:
    removed = (DV - width) / DV
    require(0.0 < removed < 1.0, f"candidate Dv: {width}")
    if rule == "all_value":
        return removed
    if rule == "qkv_value_share":
        # Dk64 TP-local packed QKV is 256 Q + 256 K + 1536 V.
        return removed * (1536 / 2048)
    if rule == "qkvz_value_share":
        # Dk64 TP-local QKVZ is 256 Q + 256 K + 1536 V + 1536 Z.
        return removed * (3072 / 3584)
    if rule == "one_of_three_value_slices":
        return removed / 3
    raise ValueError(f"unknown scaling rule: {rule}")


def width_ceiling(width: int, costs: dict, dense_tps: float, target_tps: float, dk64_tps: float, dk64_tpot: float) -> dict:
    credits = {}
    total_credit = 0.0
    for name, item in costs.items():
        fraction = reduction_fraction(item["scaling_rule"], width)
        credit = item["rank_mean_kernel_sum_ms"] / DECODE_STEPS * fraction
        credits[name] = {"reduction_fraction": fraction, "optimistic_tpot_credit_ms": credit}
        total_credit += credit
    ceiling_tpot = dk64_tpot - total_credit
    require(ceiling_tpot > 0.0, "positive ceiling TPOT")
    ceiling_tps = dk64_tps * dk64_tpot / ceiling_tpot
    gain = (ceiling_tps / dense_tps - 1.0) * 100.0
    return {
        "dv": width,
        "components": credits,
        "optimistic_tpot_credit_ms": total_credit,
        "optimistic_tpot_ceiling_ms": ceiling_tpot,
        "optimistic_output_tps_ceiling": ceiling_tps,
        "optimistic_gain_vs_dense_percent": gain,
        "margin_over_ten_percent_target_points": gain - 10.0,
        "crosses_fixed_target": ceiling_tps >= target_tps,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-summary", required=True)
    parser.add_argument("--profile-comparison", required=True)
    parser.add_argument("--frozen-baseline", required=True)
    parser.add_argument("--candidate-screen", required=True)
    parser.add_argument("--model-config", required=True)
    parser.add_argument("--checkpoint-shard", required=True)
    parser.add_argument("--checkpoint-index", required=True)
    parser.add_argument("--capture-summary", required=True)
    parser.add_argument("--upstream-gdn-source", required=True)
    parser.add_argument("--ascend-gdn-source", required=True)
    parser.add_argument("--recurrent-tiling-source", required=True)
    parser.add_argument("--prefill-source", required=True)
    parser.add_argument("--plugin-plan-source", required=True)
    parser.add_argument("--model-loader-source", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = read_json(args.profile_summary)
    comparison = read_json(args.profile_comparison)
    baseline = read_json(args.frozen_baseline)
    screen = read_json(args.candidate_screen)
    config_root = read_json(args.model_config)
    capture = read_json(args.capture_summary)
    require(comparison.get("schema") == PROFILE_COMPARISON_SCHEMA and comparison.get("status") == "diagnostic_pair_validated", "profile comparison identity")
    require(baseline.get("schema") == BASELINE_SCHEMA, "baseline schema")
    require(screen.get("schema") == SCREEN_SCHEMA and screen.get("status") == "single_pair_complete", "screen identity")
    require(capture.get("schema") == CAPTURE_SCHEMA and capture.get("status") == "capture_complete_and_independent_audit_passed", "capture identity")

    text_config = config_root.get("text_config", config_root)
    model_contract = {
        "architecture": config_root.get("architectures"),
        "hidden_size": text_config.get("hidden_size"),
        "layers": text_config.get("num_hidden_layers"),
        "linear_layers": text_config.get("layer_types", []).count("linear_attention"),
        "full_attention_layers": text_config.get("layer_types", []).count("full_attention"),
        "key_heads": text_config.get("linear_num_key_heads"),
        "value_heads": text_config.get("linear_num_value_heads"),
        "original_dk": text_config.get("linear_key_head_dim"),
        "original_dv": text_config.get("linear_value_head_dim"),
    }
    require(model_contract == {
        "architecture": ["Qwen3_5ForConditionalGeneration"],
        "hidden_size": 5120,
        "layers": 64,
        "linear_layers": 48,
        "full_attention_layers": 16,
        "key_heads": 16,
        "value_heads": 48,
        "original_dk": 128,
        "original_dv": 128,
    }, f"model contract: {model_contract}")

    shapes, shard_header_sha = checkpoint_shapes(args.checkpoint_shard)
    costs, per_rank = extract_profile_costs(profile)
    dense = baseline["performance"]
    dense_tps = float(dense["output_tokens_per_second"])
    target_tps = float(dense["ten_percent_target_tokens_per_second"])
    dk64_tps = float(screen["summary"]["output_tokens_per_second"]["dk64"])
    dk64_tpot = float(screen["summary"]["tpot_mean_ms"]["dk64"])
    require(math.isclose(target_tps, dense_tps * 1.1, rel_tol=0.0, abs_tol=1e-9), "fixed ten-percent target")
    require(math.isclose(screen["summary"]["output_tokens_per_second"]["dense"], dense_tps, rel_tol=0.0, abs_tol=1e-9), "screen versus frozen dense")
    target_tpot = dk64_tpot * dk64_tps / target_tps
    required_tpot_reduction = dk64_tpot - target_tpot
    ceilings = [width_ceiling(width, costs, dense_tps, target_tps, dk64_tps, dk64_tpot) for width in WIDTHS]
    crossing = [item for item in ceilings if item["crosses_fixed_target"]]
    require(crossing and crossing[0]["dv"] == 64, f"first target-crossing width: {crossing}")

    source_audit = {
        "upstream_gdn": source_identity(args.upstream_gdn_source, ("self.head_v_dim", "self.value_dim", "RMSNormGated", "RowParallelLinear")),
        "ascend_gdn": source_identity(args.ascend_gdn_source, ("self.head_v_dim", "self.value_dim", "core_attn_out", "qwen_gdn_attention_core")),
        "native_recurrent_tiling": source_identity(args.recurrent_tiling_source, ("tilingData_.dv = valueShape.GetDim", "aDv = CeilAlign(tilingData_.dv", "tilingData_.dv > 512")),
        "prefill": source_identity(args.prefill_source, ("head_v_dim", "V = head_v_dim", "BV = triton.next_power_of_2(V)")),
        "active_plugin_plan": source_identity(args.plugin_plan_source, ("linear_value_head_dim", '("in_proj_qkv", "conv1d")')),
        "model_loader": source_identity(args.model_loader_source, ("in_proj_qkv", "in_proj_z")),
    }
    plugin_text = regular(args.plugin_plan_source).read_text(encoding="utf-8")
    require("out_proj" not in plugin_text and "norm.weight" not in plugin_text and "in_proj_z" not in plugin_text, "Dv transform unexpectedly active in plugin plan")

    protocol = capture["protocol"]
    split = capture["selector_split"]
    require(protocol["sequences"] == 16 and protocol["decode_steps"] == 8 and protocol["ranks"] == [0, 1, 2, 3], "capture protocol")
    require(split["fit_indices"] == list(range(12)) and split["untouched_admission_indices"] == list(range(12, 16)), "capture split")
    require(capture["coverage"]["state_trajectories"] == 384 and capture["coverage"]["byte_exact_decode_state_transitions"] == 3072, "capture coverage")

    inputs = {}
    for name in (
        "profile_summary", "profile_comparison", "frozen_baseline", "candidate_screen",
        "model_config", "checkpoint_index", "capture_summary",
    ):
        path = regular(getattr(args, name))
        inputs[name] = {"path": str(path), "sha256": digest(path)}
    checkpoint_path = regular(args.checkpoint_shard)
    inputs["checkpoint_shard"] = {
        "path": str(checkpoint_path),
        "size_bytes": checkpoint_path.stat().st_size,
        "header_sha256": shard_header_sha,
        "binding": "Tensor shapes are read from this shard header; whole-model file assignment is bound by checkpoint_index SHA256.",
    }

    document = {
        "schema": SCHEMA,
        "status": "accepted_for_heldout_fidelity_screen",
        "claim_boundary": "Source, checkpoint-geometry, existing-profile optimistic ceiling, and corpus admission only. No candidate weights, NPU execution, endpoint performance, task accuracy, or portability result.",
        "inputs": inputs,
        "model_contract": model_contract,
        "checkpoint_cut_points": shapes,
        "source_audit": source_audit,
        "foldability_audit": {
            "result": "structurally_foldable_candidate_with_changed_reduced_rms_semantics",
            "cut_points": ["V and Z projection rows", "matching packed causal-convolution rows", "FP32 recurrent state Dv rows", "RMSNorm value coordinates", "output-projection columns"],
            "no_dense_reconstruction_requirement": "The GDN recurrence is row-separable across Dv. A selected value row uses shared Q/K and its own V/state row, so deleted Dv rows need not be reconstructed before recurrent update or read.",
            "changed_semantics": "RMSNorm couples retained coordinates through its denominator; reduced-Dv normalization is an approximation and must be judged on untouched output-projected held-out data.",
            "shared_norm_weight_constraint": "The checkpoint norm weight is shared across value heads. Start with one layer-shared Dv coordinate set; a per-head set requires explicitly folding original gamma into matching output-projection columns and a separate proof.",
            "existing_implementation": False,
            "implementation_requirement": "Extend the plugin-owned weight transform, cache/state geometry, graph identity, and possibly the prefill adapter only after held-out admission.",
        },
        "trace_contract": {
            "ranks": 4,
            "decode_steps": DECODE_STEPS,
            "linear_layers": 48,
            "full_attention_layers": 16,
            "per_rank": per_rank,
            "component_rank_means": costs,
            "warning": "Kernel sums overlap conceptually with end-to-end scheduling and are not a critical path. Proportional width scaling and full TPOT conversion are deliberately optimistic admission assumptions.",
        },
        "cost_model": {
            "frozen_dense_output_tps": dense_tps,
            "fixed_target_output_tps": target_tps,
            "energy_dk64_output_tps": dk64_tps,
            "energy_dk64_tpot_ms": dk64_tpot,
            "reciprocal_tpot_at_fixed_target_ms": target_tpot,
            "required_tpot_reduction_ms": required_tpot_reduction,
            "widths": ceilings,
            "arithmetic_correction": "For TP-local Dk64, Q+K=512 and V+Z=3072. Dv128 to Dv64 changes total QKVZ width 3584 to 2048, a 42.857142857 percent reduction, not 46.153846154 percent.",
        },
        "corpus_admission": {
            "result": "sufficient_for_bounded_heldout_screen",
            "fit_indices": split["fit_indices"],
            "heldout_indices": split["untouched_admission_indices"],
            "layers": protocol["layers"],
            "available_signals": ["raw V", "Z", "operator output", "post-RMS output", "norm weight", "initial/final FP32 state"],
            "checkpoint_signal": "Output-projection columns are available from the bound checkpoint and must be used so admission measures block-output fidelity, not state error alone.",
        },
        "decision": {
            "outcome": "accepted_for_heldout_fidelity_screen",
            "primary_width": 64,
            "headroom_control_width": 48,
            "cost_rejected_widths": [96, 80],
            "bounded_out_width": 32,
            "reason": "Dv64 is the first descending aligned width whose corrected optimistic ceiling crosses the fixed target. Dv48 is retained only as a headroom control; Dv32 is not admitted in this bounded screen.",
            "stop_rule": "Reject value-side structural reduction if neither locked Dv64 nor Dv48 passes the predeclared untouched output-projected fidelity and per-head robustness gates. Do not implement cache, operators, endpoint service, or accuracy on rejection.",
        },
        "attribution_contract": {
            "required_endpoint_arms": ["Dk128/Dv128 frozen dense", "Dk64/Dv128 energy DRRQR", "Dk128/DvX value-width control", "Dk64/DvX two-sided candidate"],
            "claim_rule": "Call the result a DRRQR extension only when the combined arm preserves an identifiable Dk64 contribution; report paper-exact StrongRRQR as false.",
        },
        "portability_contract": {
            "logical_geometry": "Dk/Dv selection and checkpoint coordinate order are independent of physical tiles.",
            "alignment": "Admitted widths are multiples of 16; native recurrent tiling derives Dv from tensors and aligns it to 16.",
            "backend": "Existing production prefill/decode/cache support is not assumed. Capability dispatch and fallback stay explicit, and every implementation requires environment-specific NPU numerical and paired endpoint evidence.",
        },
        "next_gate": {
            "name": "drrqr-two-sided-value-width-heldout-v1",
            "scope": "Fit candidate coordinate plans on captures 0-11 only, freeze them, then compare Dv64 and Dv48 against Dk64/Dv128 on untouched captures 12-15 using post-RMS and output-projected error plus per-head robustness.",
            "npu_used": False,
            "endpoint_used": False,
            "accuracy_used": False,
        },
    }
    publish(args.output, document)
    print(json.dumps({
        "status": document["status"],
        "output": str(Path(args.output)),
        "primary": next(item for item in ceilings if item["dv"] == 64),
        "required_tpot_reduction_ms": required_tpot_reduction,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
