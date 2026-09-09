#!/usr/bin/env python3
"""Replay aligned DRRQR widths against the frozen captured dense GDN teacher.

This is a local numerical and trajectory-fidelity screen. It can admit a
full-layer sensitivity study, but it is not model accuracy, endpoint timing,
throughput, or final joint acceptance.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import statistics
import sys
import time
import traceback

import torch


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = Path("/drrqr-results")
CAPTURED_PATH = ROOT / "tools/replay_gdn_teacher_captured_reference.py"
CAPTURED_SHA256 = "acf2942bff22926e15a2e310e9629175fcbc6d002c2d947ae026cb4829f31bb4"
VARIANT_DK = {
    "dense128": 128,
    "energy48": 48,
    "energy64": 64,
    "energy80": 80,
}
FIDELITY_KEYS = tuple(
    variant + "_relative_l2" for variant in ("energy48", "energy64", "energy80")
)
CLAIM = (
    "Captured-dense-reference local trajectory fidelity for aligned "
    "energy-selector Dk48/Dk64/Dk80. Not exact StrongRRQR reproduction, "
    "full-model accuracy, timing, throughput, or portability acceptance."
)


def require(value, message):
    if not value:
        raise ValueError(message)


def checksum(path):
    digest = __import__("hashlib").sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_captured_reference():
    require(
        CAPTURED_PATH.is_file() and not CAPTURED_PATH.is_symlink(),
        "captured-reference helper must be a regular file",
    )
    require(
        checksum(CAPTURED_PATH) == CAPTURED_SHA256,
        "captured-reference helper changed",
    )
    spec = importlib.util.spec_from_file_location(
        "width_curve_captured_reference", CAPTURED_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_width_plan_doc(plan, expected_dk, baseline):
    require(expected_dk in (48, 64, 80), "width outside aligned protocol")
    shared = (
        "schema",
        "target_model_id",
        "source_config_sha256",
        "source_index_sha256",
        "old_head_k_dim",
        "selection_objective",
        "num_key_heads",
        "num_value_heads",
        "head_v_dim",
        "conv_kernel_dim",
        "hidden_size",
        "layer_types",
        "model_type",
    )
    for key in shared:
        require(plan.get(key) == baseline.get(key), "width plan differs: " + key)
    require(
        plan.get("schema") == "ascend-drrqr-plan/v1"
        and plan.get("old_head_k_dim") == 128
        and plan.get("target_head_k_dim") == expected_dk
        and plan.get("selection_objective") == "energy-kernel"
        and plan.get("pruning_ratio") == 1.0 - expected_dk / 128.0,
        "width plan geometry/objective mismatch",
    )
    provenance = plan.get("provenance")
    baseline_provenance = baseline.get("provenance")
    require(
        isinstance(provenance, dict) and isinstance(baseline_provenance, dict),
        "width plan provenance missing",
    )
    require(
        provenance.get("calibration_sha256")
        == baseline_provenance.get("calibration_sha256"),
        "width plan calibration changed",
    )
    selection = provenance.get("selection")
    baseline_selection = baseline_provenance.get("selection")
    require(
        isinstance(selection, dict) and isinstance(baseline_selection, dict),
        "width plan selection provenance missing",
    )
    for key in (
        "schema",
        "selection_objective",
        "capture_file_count",
        "capture_manifest_sha256",
    ):
        require(
            selection.get(key) == baseline_selection.get(key),
            "width plan selection provenance differs: " + key,
        )
    if expected_dk != 64:
        require(
            provenance.get("paper_exact_selection") is False,
            "new energy plan must explicitly state non-paper-exact selection",
        )

    layer_types = plan["layer_types"]
    linear_layers = {
        str(layer)
        for layer, kind in enumerate(layer_types)
        if kind == "linear_attention"
    }
    keep_indices = plan.get("keep_indices")
    require(
        isinstance(keep_indices, dict)
        and set(keep_indices) == linear_layers
        and len(linear_layers) == 48,
        "width plan must cover all 48 linear-attention layers",
    )
    for layer, values in keep_indices.items():
        require(
            isinstance(values, list)
            and len(values) == 16 * expected_dk
            and all(type(value) is int for value in values),
            "width plan coordinate count/type mismatch: layer " + layer,
        )
        for head in range(16):
            selected = values[head * expected_dk : (head + 1) * expected_dk]
            lower, upper = head * 128, (head + 1) * 128
            require(
                selected == sorted(selected)
                and len(set(selected)) == expected_dk
                and all(lower <= value < upper for value in selected),
                "width plan coordinates cross/duplicate a head: layer " + layer,
            )
    return plan


def bind_width_plan(path, expected_sha256, expected_dk, baseline, captured):
    plan = captured.bound_json(path, expected_sha256)
    validate_width_plan_doc(plan, expected_dk, baseline)
    return plan


def keep_for(plan, layer, rank, dk):
    require(
        layer in range(64) and type(rank) is int and 0 <= rank < 4,
        "layer/rank outside width protocol",
    )
    raw = plan["keep_indices"].get(str(layer))
    require(
        isinstance(raw, list) and len(raw) == 16 * dk,
        "width plan layer coordinate count mismatch",
    )
    all_keep = torch.tensor(raw, dtype=torch.int64).reshape(16, dk)
    global_heads = torch.arange(rank * 4, rank * 4 + 4)
    local = all_keep[global_heads] - global_heads[:, None] * 128
    require(
        tuple(local.shape) == (4, dk)
        and bool(((local >= 0) & (local < 128)).all()),
        "head-local coordinate conversion failed",
    )
    return local.contiguous()


def select_qk(tensor, keep, dk):
    require(
        tensor.ndim >= 2
        and tuple(tensor.shape[-2:]) == (4, 128)
        and keep.dtype == torch.int64
        and tuple(keep.shape) == (4, dk)
        and tensor.device == keep.device,
        "head-local Q/K selection shape/device mismatch",
    )
    indices = keep.reshape((1,) * (tensor.ndim - 2) + (4, dk))
    return tensor.gather(
        -1, indices.expand(*tensor.shape[:-2], 4, dk)
    ).contiguous()


def data_from(record, keep, dk):
    tensors = record["tensors"]
    q, k = tensors["raw_q"], tensors["raw_k"]
    if dk != 128:
        q, k = select_qk(q, keep, dk), select_qk(k, keep, dk)
    return {
        "q": q.clone(),
        "k": k.clone(),
        "v": tensors["raw_v"].clone(),
        "g": tensors["g"].clone(),
        "beta": tensors["beta"].clone(),
        "r": torch.ones(12, dtype=torch.float32),
        "z": tensors["z"].clone(),
        "weight": tensors["norm_weight"].clone(),
        "lengths": torch.tensor([0, 1], dtype=torch.int32),
        "indices": torch.zeros(1, dtype=torch.int32),
    }


def finite_bytes(tensor, replay):
    return replay.exact(tensor, tensor)


def fidelity_screen(rows, layers):
    expected = {
        (f"teacher-{sequence}", rank, layer, position)
        for sequence in range(2)
        for rank in range(4)
        for layer in layers
        for position in range(136)
    }
    lookup = {}
    for row in rows:
        key = (
            row["sequence_id"],
            row["rank"],
            row["layer"],
            row["position"],
        )
        require(
            key in expected and key not in lookup,
            "fidelity coordinate missing/duplicate/outside protocol",
        )
        require(
            all(
                type(row[name]) in (float, int)
                and math.isfinite(row[name])
                and row[name] >= 0
                for name in FIDELITY_KEYS
            ),
            "nonfinite width fidelity",
        )
        lookup[key] = row
    require(set(lookup) == expected, "complete width-curve token fidelity required")

    def summary(values):
        result = {
            name.removesuffix("_relative_l2") + "_mean": statistics.fmean(
                item[name] for item in values
            )
            for name in FIDELITY_KEYS
        }
        result["energy80_over_energy64_with_floor"] = result[
            "energy80_mean"
        ] / max(result["energy64_mean"], 1e-6)
        return result

    overall = summary(rows)
    monotonic = (
        overall["energy80_mean"]
        <= overall["energy64_mean"]
        <= overall["energy48_mean"]
    )
    groups = []
    for sequence_id, rank, layer in sorted({key[:3] for key in expected}):
        for window, positions in (
            ("all", range(136)),
            ("prefill_late", range(64, 128)),
            ("decode_late", range(132, 136)),
        ):
            value = summary(
                [lookup[sequence_id, rank, layer, position] for position in positions]
            )
            groups.append(
                {
                    "sequence_id": sequence_id,
                    "rank": rank,
                    "layer": layer,
                    "window": window,
                    **value,
                    "passed": value["energy80_over_energy64_with_floor"] <= 1.05,
                }
            )
    return {
        "passed": (
            monotonic
            and overall["energy80_over_energy64_with_floor"] <= 0.85
            and all(item["passed"] for item in groups)
        ),
        "overall": overall,
        "aggregate_monotonic_48_64_80": monotonic,
        "groups": groups,
        "denominator_floor": 1e-6,
        "energy80_global_ratio_limit": 0.85,
        "energy80_group_window_ratio_limit": 1.05,
        "aggregation": (
            "equal-weight per-token relative-L2 across local 12 x 128 post-RMS"
        ),
        "late_windows": {
            "prefill_late": [64, 127],
            "decode_late": [132, 135],
        },
    }


def run_trajectory(
    records,
    variant,
    keep,
    runtime,
    group,
    output_dir,
    report,
    save,
    phase,
    replay,
):
    dk = VARIANT_DK[variant]
    row = {
        "sequence_id": group[0],
        "rank": group[1],
        "layer": group[2],
        "variant": variant,
        "dk": dk,
        "passed": False,
        "steps": [],
        "graph_warmups": 3,
    }
    report["trajectories"].append(row)
    graph = None
    token_rows = []
    try:
        phase("trajectory_prefill", group=list(group), variant=variant)
        data_cpu = data_from(records[0], keep, dk)
        data = {key: value.to("npu:0") for key, value in data_cpu.items()}
        result, eager_state = replay.prefill(data, dk, False, runtime)
        torch.npu.synchronize()

        def record_step(
            step,
            actual,
            graph_state=None,
            graph_result=None,
            state_initial=None,
        ):
            teacher = records[step]["tensors"]
            checks = {
                "output_finite": finite_bytes(actual["output"], replay),
                "post_rms_finite": finite_bytes(actual["norm"], replay),
                "full_state_finite": finite_bytes(eager_state, replay),
                "beta_product_cpu_bytes": replay.exact(
                    actual["product"], data_cpu["beta"]
                ),
                "beta_bf16_cpu_bytes": replay.exact(
                    actual["beta"], data_cpu["beta"]
                ),
            }
            if variant == "dense128":
                checks.update(
                    output_capture_bytes=replay.exact(
                        actual["output"],
                        teacher["operator_output"].reshape(-1, 12, 128),
                    ),
                    full_state_capture_bytes=replay.exact(
                        eager_state, teacher["state_final"]
                    ),
                    post_rms_capture_bytes=replay.exact(
                        actual["norm"],
                        teacher["norm_output"].reshape(-1, 12, 128),
                    ),
                )
                if state_initial is not None:
                    checks["state_initial_capture_bytes"] = replay.exact(
                        state_initial, teacher["state_initial"]
                    )
                if step:
                    checks.update(
                        query_capture_bytes=replay.exact(
                            actual["q"], teacher["query"]
                        ),
                        key_capture_bytes=replay.exact(
                            actual["k"], teacher["key"]
                        ),
                    )
            if graph_result is not None:
                checks["graph_eager_full_state_bytes"] = replay.exact(
                    graph_state, eager_state
                )
                for key in actual:
                    checks["graph_eager_" + key + "_bytes"] = replay.exact(
                        graph_result[key], actual[key]
                    )
                checks["graph_persistent_metadata"] = row[
                    "graph_tracked_metadata"
                ] == {
                    key: runtime.probe.metadata(value)
                    for key, value in tracked_tensors.items()
                }
            passed = all(checks.values())
            payload = {
                "schema": "drrqr-width-curve-trajectory/v1",
                "group": list(group),
                "variant": variant,
                "step": step,
                "state_layout": "N,Nv,Dv,Dk",
                "state": replay.cpu(eager_state),
                "tensors": {
                    key: replay.cpu(value) for key, value in actual.items()
                },
                "graph_state": (
                    replay.cpu(graph_state) if graph_state is not None else None
                ),
                "checks": checks,
                "passed": passed,
            }
            filename = (
                f"{variant}.{group[0]}.rank{group[1]}."
                f"layer{group[2]}.step{step}.pt"
            )
            row["steps"].append(
                {
                    "step": step,
                    "phase": "prefill" if step == 0 else "decode",
                    "checks": checks,
                    "passed": passed,
                    "archive": replay.archive(output_dir / filename, payload),
                }
            )
            save()
            require(passed, "width numerical/graph gate failed; no retry")
            errors = replay.token_errors(actual["norm"], teacher["norm_output"])
            start = 0 if step == 0 else 127 + step
            token_rows.extend(
                {
                    "position": start + offset,
                    "relative_l2": value,
                }
                for offset, value in enumerate(errors)
            )

        record_step(0, result, state_initial=torch.zeros_like(eager_state))
        graph_state = eager_state.clone()
        graph_initial = eager_state.clone()
        data_cpu = data_from(records[1], keep, dk)
        data = {key: value.to("npu:0") for key, value in data_cpu.items()}
        phase("graph_warmup", group=list(group), variant=variant)
        for _ in range(3):
            replay.operation(data, graph_state, dk, False, runtime)
            torch.npu.synchronize()
        phase("graph_capture", group=list(group), variant=variant)
        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_result = replay.operation(data, graph_state, dk, False, runtime)
        torch.npu.synchronize()
        graph_state.copy_(graph_initial)
        torch.npu.synchronize()
        tracked_tensors = {
            **{"input." + key: value for key, value in data.items()},
            **{"result." + key: value for key, value in graph_result.items()},
            "eager_state": eager_state,
            "graph_state": graph_state,
        }
        row["graph_tracked_metadata"] = {
            key: runtime.probe.metadata(value)
            for key, value in tracked_tensors.items()
        }
        for step in range(1, 9):
            phase(
                "trajectory_decode",
                group=list(group),
                variant=variant,
                step=step,
            )
            data_cpu = data_from(records[step], keep, dk)
            for key, value in data_cpu.items():
                data[key].copy_(value)
            state_initial = eager_state.clone()
            result = replay.operation(data, eager_state, dk, False, runtime)
            graph.replay()
            torch.npu.synchronize()
            record_step(
                step,
                result,
                graph_state,
                graph_result,
                state_initial,
            )
        require(
            len(token_rows) == 136 and len(row["steps"]) == 9,
            "complete 136-token trajectory required",
        )
        row["passed"] = True
        return token_rows
    except BaseException as error:
        row.update(
            passed=False,
            error=repr(error),
            traceback=traceback.format_exc(),
        )
        raise
    finally:
        original_error = sys.exc_info()[1]
        if graph is not None:
            try:
                graph.reset()
                row["graph_reset"] = True
            except BaseException as error:
                row.update(
                    passed=False,
                    graph_reset=False,
                    graph_cleanup_error=repr(error),
                )
                if original_error is None:
                    raise
        save()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "audit-report",
        "manifest",
        "energy-plan",
        "retained-stats",
        "plan-dk48",
        "plan-dk80",
        "output-dir",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in (
        "audit-sha256",
        "manifest-sha256",
        "plan-dk48-sha256",
        "plan-dk80-sha256",
    ):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--max-seconds", type=int, default=5400)
    args = parser.parse_args(argv)

    require(
        os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
        "audited four-device namespace required; replay uses logical npu0",
    )
    require(1 <= args.max_seconds <= 5400, "bounded 1..5400-second replay")
    output = args.output_dir
    require(
        output.is_absolute()
        and output == output.resolve()
        and RESULT_ROOT in output.parents
        and not output.exists(),
        "fresh canonical output below /drrqr-results required",
    )
    output.mkdir(parents=False, exist_ok=False)
    report = {
        "schema": "drrqr-captured-teacher-width-curve/v1",
        "status": "failed",
        "claim": CLAIM,
        "script_sha256": checksum(__file__),
        "captured_reference_helper_sha256": CAPTURED_SHA256,
        "phase": "input_binding",
        "created_unix_ns": time.time_ns(),
        "trajectories": [],
        "source_sha256": {},
        "dense_capture_gate_passed": False,
        "candidate_numerical_gate_passed": False,
        "full_layer_capture_admitted": False,
        "performance_admitted": False,
        "task_accuracy_admitted": False,
        "protocol": {
            "variants": list(VARIANT_DK),
            "groups": 0,
            "input_tokens": 128,
            "decode_steps": 8,
            "prefill": "eager from private zero state",
            "decode": "three warmups plus NPUGraph and eager byte comparison",
            "reference": "immutable captured dense operator output/state/post-RMS",
            "energy80_global_improvement_minimum": 0.15,
            "energy80_group_window_regression_limit": 0.05,
            "aggregate_monotonic_widths": [48, 64, 80],
            "max_seconds": args.max_seconds,
            "retry_count": 0,
        },
    }
    deadline = time.monotonic() + args.max_seconds

    def save():
        temporary = output / "report.json.tmp"
        temporary.write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output / "report.json")

    def phase(name, **details):
        report.update(phase=name, active=details)
        save()
        if time.monotonic() > deadline:
            raise TimeoutError("fixed width-curve replay budget exceeded")

    def interrupted(signum, _frame):
        raise InterruptedError("width replay interrupted by signal " + str(signum))

    previous = {
        sig: signal.signal(sig, interrupted)
        for sig in (signal.SIGTERM, signal.SIGINT)
    }
    runtime = None
    current_variant = None
    save()
    try:
        captured = load_captured_reference()
        replay = captured.load_replay()
        bound = replay.bind_inputs(args)
        report["protocol"]["groups"] = 2 * 4 * len(bound.layers)
        report["protocol"]["layers"] = list(bound.layers)
        plans = {
            64: bind_width_plan(
                args.energy_plan,
                replay.PLAN_SHA256,
                64,
                bound.plan,
                captured,
            ),
            48: bind_width_plan(
                args.plan_dk48,
                args.plan_dk48_sha256,
                48,
                bound.plan,
                captured,
            ),
            80: bind_width_plan(
                args.plan_dk80,
                args.plan_dk80_sha256,
                80,
                bound.plan,
                captured,
            ),
        }
        report["bindings"] = {
            **bound.binding,
            "width_plans": {
                str(dk): {
                    "path": str(
                        args.energy_plan
                        if dk == 64
                        else args.plan_dk48
                        if dk == 48
                        else args.plan_dk80
                    ),
                    "sha256": (
                        replay.PLAN_SHA256
                        if dk == 64
                        else args.plan_dk48_sha256
                        if dk == 48
                        else args.plan_dk80_sha256
                    ),
                }
                for dk in (48, 64, 80)
            },
        }
        phase("runtime_init")
        runtime = replay.init_runtime(report, lambda name: phase(name))
        require(
            report["operator_schema"] == bound.receipt["native_schema"],
            "native schema differs from teacher",
        )
        groups = [
            (f"teacher-{sequence}", rank, layer)
            for sequence in range(2)
            for rank in range(4)
            for layer in bound.layers
        ]
        fidelity = {}
        for variant, dk in VARIANT_DK.items():
            current_variant = variant
            if variant != "dense128":
                require(
                    report["dense_capture_gate_passed"],
                    "complete dense capture gate precedes candidate attribution",
                )
            for group in groups:
                phase("load_group", group=list(group), variant=variant)
                records = []
                for step in range(9):
                    entry = bound.entries[(*group, step)]
                    record, _ = bound.audit.load_record(
                        bound.capture / entry["file"], entry["sha256"]
                    )
                    records.append(record)
                keep = None if dk == 128 else keep_for(
                    plans[dk], group[2], group[1], dk
                )
                errors = run_trajectory(
                    records,
                    variant,
                    keep,
                    runtime,
                    group,
                    output,
                    report,
                    save,
                    phase,
                    replay,
                )
                if variant != "dense128":
                    for item in errors:
                        key = (*group, item["position"])
                        fidelity.setdefault(key, {})[
                            variant + "_relative_l2"
                        ] = item["relative_l2"]
            if variant == "dense128":
                report["dense_capture_gate_passed"] = True
                save()
        require(
            len(report["trajectories"]) == len(VARIANT_DK) * 2 * 4 * len(bound.layers)
            and all(row["passed"] for row in report["trajectories"]),
            "all dense and width trajectories must complete",
        )
        report["candidate_numerical_gate_passed"] = True
        rows = [
            {
                "sequence_id": key[0],
                "rank": key[1],
                "layer": key[2],
                "position": key[3],
                **value,
            }
            for key, value in sorted(fidelity.items())
        ]
        report["fidelity"] = fidelity_screen(rows, bound.layers)
        fidelity_path = output / "token-fidelity.json"
        with fidelity_path.open("x", encoding="utf-8") as stream:
            json.dump(rows, stream, allow_nan=False)
        report["token_fidelity"] = {
            "path": str(fidelity_path),
            "sha256": checksum(fidelity_path),
        }
        report["full_layer_capture_admitted"] = report["fidelity"]["passed"]
        report["status"] = (
            "width_curve_pass"
            if report["fidelity"]["passed"]
            else "width_curve_failed"
        )
        report["phase"] = "complete"
    except BaseException as error:
        report.update(
            status=(
                "blocked_dense_capture_replay"
                if current_variant == "dense128"
                else "failed_candidate_numerical"
                if current_variant
                else "failed_admission"
            ),
            error=repr(error),
            traceback=traceback.format_exc(),
        )
    finally:
        if runtime is not None:
            try:
                report["loaded_libraries"] = (
                    captured.validated_runtime_libraries(runtime)
                )
                report["runtime_evidence_scope"] = (
                    "Mapped-file hashes plus same-process semantic dense-capture "
                    "replay; not same-name ACLNN symbol ownership proof."
                )
            except BaseException as error:
                report["library_observation_error"] = repr(error)
                if report["status"] in ("width_curve_pass", "width_curve_failed"):
                    report["status"] = "failed_runtime_evidence"
                    report["full_layer_capture_admitted"] = False
        report["completed_unix_ns"] = time.time_ns()
        save()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    print(
        json.dumps(
            {"status": report["status"], "report": str(output / "report.json")}
        ),
        flush=True,
    )
    return 0 if report["status"] == "width_curve_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
