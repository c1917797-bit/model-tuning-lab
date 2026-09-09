#!/usr/bin/env python3
"""Replay DRRQR variants against a frozen captured dense GDN teacher.

This is a local trajectory-fidelity screen.  It does not replace the preserved
independent-FP32-oracle failure, model accuracy, or endpoint performance.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

import torch


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = Path("/drrqr-results")
REPLAY_PATH = ROOT / "tools/replay_gdn_teacher.py"
REPLAY_SHA256 = "28c735121249e37fbbc6d03436e6b10a659f72152a3cdfe7370633615b4fa9f9"
ORIGINAL_REPORT_SHA256 = "eb6aa7e8af0234554951b01a808da566fda02994317519a500357b3d586ba79b"
ORIGINAL_SCRIPT_SHA256 = "46fdfe7894e087cd47c10327b683dfc081a041afdcea400c87485c5918087e95"
SYNTHETIC_SUMMARY_SHA256 = "0a85bd97bf75080eb0b28683be49bcac6184db51a8ba84bd2ae39ec4ef646c00"
SYNTHETIC_RAW_SHA256 = "d548c37e94594082819628e0052acaca8e5df94f304dd3969e74c56523dc6baf"
VARIANTS = ("dense128", "energy64", "beta64")
CLAIM = (
    "Captured-dense-reference local trajectory fidelity for energy64 and fixed "
    "retained-key beta64. Not an independent dense arithmetic oracle, exact "
    "StrongRRQR reproduction, full-model accuracy, timing, or throughput."
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


def bound_json(path, expected_sha256):
    path = Path(path)
    require(path.is_absolute() and path.is_file() and not path.is_symlink(),
            "bound JSON must be an absolute regular non-symlink file")
    observed = checksum(path)
    require(observed == expected_sha256,
            f"bound JSON changed: {path}: {observed} != {expected_sha256}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "bound JSON root must be an object")
    return value


def load_replay():
    require(REPLAY_PATH.is_file() and not REPLAY_PATH.is_symlink(),
            "frozen replay helper must be a regular file")
    require(checksum(REPLAY_PATH) == REPLAY_SHA256, "frozen replay helper changed")
    spec = importlib.util.spec_from_file_location("captured_reference_replay", REPLAY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_prior_evidence(original_path, synthetic_path):
    original = bound_json(original_path, ORIGINAL_REPORT_SHA256)
    require(original.get("script_sha256") == ORIGINAL_SCRIPT_SHA256,
            "original failed replay script identity changed")
    require(original.get("dense_gate_passed") is False
            and original.get("candidate_numerical_gate_passed") is False,
            "original failed replay was reclassified")
    trajectories = original.get("trajectories")
    require(isinstance(trajectories, list) and len(trajectories) == 1,
            "original failure must contain exactly its first dense trajectory")
    first = trajectories[0]
    require(first.get("variant") == "dense128"
            and first.get("sequence_id") == "teacher-0"
            and first.get("rank") == 0 and first.get("layer") == 0,
            "original failure coordinate changed")
    steps = first.get("steps")
    require(isinstance(steps, list) and len(steps) == 1 and steps[0].get("step") == 0,
            "original failure step changed")
    metrics = steps[0].get("metrics", {})
    require(metrics.get("full_state_cpu", {}).get("passed") is False,
            "original independent FP32 state failure must remain failed")
    for name in ("output_capture", "full_state_capture", "post_rms_capture"):
        require(metrics.get(name, {}).get("passed") is True,
                "original dense capture reproduction evidence changed: " + name)

    synthetic = bound_json(synthetic_path, SYNTHETIC_SUMMARY_SHA256)
    require(synthetic.get("schema") == "drrqr-retained-key-beta-probe/v1"
            and synthetic.get("status") == "synthetic_retained_key_beta_implementation_pass"
            and synthetic.get("raw_sha256") == SYNTHETIC_RAW_SHA256,
            "synthetic beta implementation gate is not the frozen pass")
    cases = synthetic.get("cases")
    require(isinstance(cases, list) and len(cases) == 4
            and all(row.get("status") == "passed"
                    and row.get("all_checks_passed") is True for row in cases),
            "all four synthetic beta cases must remain passed")
    return {
        "original_failed_replay": {
            "path": str(original_path), "sha256": ORIGINAL_REPORT_SHA256,
            "preserved_failure": "independent FP32 dense prefill state tolerance",
        },
        "synthetic_beta_gate": {
            "path": str(synthetic_path), "sha256": SYNTHETIC_SUMMARY_SHA256,
            "raw_sha256": SYNTHETIC_RAW_SHA256,
        },
    }


def validated_runtime_libraries(runtime):
    libraries = runtime.probe.loaded_libraries()
    require(isinstance(libraries, list) and libraries,
            "mapped runtime library evidence is empty")
    for item in libraries:
        require(isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and Path(item["path"]).is_absolute()
                and isinstance(item.get("sha256"), str)
                and len(item["sha256"]) == 64,
                "mapped runtime library evidence is malformed")
    require(any("libcust_opapi" in item["path"] for item in libraries),
            "mapped native opapi evidence is absent")
    return libraries


def finite_bytes(tensor, replay):
    return replay.exact(tensor, tensor)


def run_trajectory(records, variant, keep, r12, runtime, group, output_dir,
                   report, save, phase, replay):
    dk = 128 if variant == "dense128" else 64
    compensated = variant == "beta64"
    row = {
        "sequence_id": group[0], "rank": group[1], "layer": group[2],
        "variant": variant, "dk": dk, "passed": False, "steps": [],
        "r12": r12.tolist() if compensated else None, "graph_warmups": 3,
    }
    report["trajectories"].append(row)
    graph = None
    token_rows = []
    try:
        phase("trajectory_prefill", group=list(group), variant=variant)
        data_cpu = replay.data_from(records[0], keep, r12, dk)
        data = {key: value.to("npu:0") for key, value in data_cpu.items()}
        result, eager_state = replay.prefill(data, dk, compensated, runtime)
        torch.npu.synchronize()

        def record_step(step, actual, graph_state=None, graph_result=None,
                        state_initial=None):
            phase_name = "prefill" if step == 0 else "decode"
            teacher = records[step]["tensors"]
            product_cpu, beta_cpu = (
                replay.beta_product(data_cpu["beta"], data_cpu["r"])
                if compensated else (data_cpu["beta"], data_cpu["beta"])
            )
            checks = {
                "output_finite": finite_bytes(actual["output"], replay),
                "post_rms_finite": finite_bytes(actual["norm"], replay),
                "full_state_finite": finite_bytes(eager_state, replay),
                "beta_product_cpu_bytes": replay.exact(actual["product"], product_cpu),
                "beta_bf16_cpu_bytes": replay.exact(actual["beta"], beta_cpu),
            }
            metrics = {}
            if variant == "dense128":
                expected_output = teacher["operator_output"].reshape(-1, 12, 128)
                expected_norm = teacher["norm_output"].reshape(-1, 12, 128)
                expected_state = teacher["state_final"]
                metrics = {
                    "output_capture": replay.metrics(actual["output"], expected_output, phase_name),
                    "full_state_capture": replay.metrics(eager_state, expected_state, phase_name),
                    "post_rms_capture": replay.metrics(actual["norm"], expected_norm, phase_name),
                }
                checks.update(
                    output_capture_bytes=replay.exact(actual["output"], expected_output),
                    full_state_capture_bytes=replay.exact(eager_state, expected_state),
                    post_rms_capture_bytes=replay.exact(actual["norm"], expected_norm),
                )
                if state_initial is not None:
                    checks["state_initial_capture_bytes"] = replay.exact(
                        state_initial, teacher["state_initial"])
                if step:
                    checks.update(
                        query_capture_bytes=replay.exact(actual["q"], teacher["query"]),
                        key_capture_bytes=replay.exact(actual["k"], teacher["key"]),
                    )
            if graph_result is not None:
                checks["graph_eager_full_state_bytes"] = replay.exact(
                    graph_state, eager_state)
                for key in actual:
                    checks["graph_eager_" + key + "_bytes"] = replay.exact(
                        graph_result[key], actual[key])
                checks["graph_persistent_metadata"] = row["graph_tracked_metadata"] == {
                    key: runtime.probe.metadata(value)
                    for key, value in tracked_tensors.items()
                }
            passed = all(checks.values()) and all(
                value["passed"] for value in metrics.values())
            payload = {
                "schema": "drrqr-captured-reference-trajectory/v1",
                "group": list(group), "variant": variant, "step": step,
                "state_layout": "N,Nv,Dv,Dk", "state": replay.cpu(eager_state),
                "tensors": {key: replay.cpu(value) for key, value in actual.items()},
                "graph_state": replay.cpu(graph_state) if graph_state is not None else None,
                "metrics": metrics, "checks": checks, "passed": passed,
            }
            filename = (
                f"{variant}.{group[0]}.rank{group[1]}."
                f"layer{group[2]}.step{step}.pt"
            )
            item = {
                "step": step, "phase": phase_name, "metrics": metrics,
                "checks": checks, "passed": passed,
                "archive": replay.archive(output_dir / filename, payload),
            }
            row["steps"].append(item)
            save()
            require(passed, "captured-reference numerical/graph gate failed; no retry")
            errors = replay.token_errors(actual["norm"], teacher["norm_output"])
            start = 0 if step == 0 else 127 + step
            token_rows.extend(
                {"position": start + offset, "relative_l2": value}
                for offset, value in enumerate(errors)
            )

        zero_state = torch.zeros_like(eager_state)
        record_step(0, result, state_initial=zero_state)
        graph_state = eager_state.clone()
        graph_initial = eager_state.clone()
        data_cpu = replay.data_from(records[1], keep, r12, dk)
        data = {key: value.to("npu:0") for key, value in data_cpu.items()}
        phase("graph_warmup", group=list(group), variant=variant)
        for _ in range(3):
            replay.operation(data, graph_state, dk, compensated, runtime)
            torch.npu.synchronize()
        phase("graph_capture", group=list(group), variant=variant)
        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_result = replay.operation(data, graph_state, dk, compensated, runtime)
        torch.npu.synchronize()
        graph_state.copy_(graph_initial)
        torch.npu.synchronize()
        tracked_tensors = {
            **{"input." + key: value for key, value in data.items()},
            **{"result." + key: value for key, value in graph_result.items()},
            "eager_state": eager_state, "graph_state": graph_state,
        }
        row["graph_tracked_metadata"] = {
            key: runtime.probe.metadata(value) for key, value in tracked_tensors.items()
        }
        for step in range(1, 9):
            phase("trajectory_decode", group=list(group), variant=variant, step=step)
            data_cpu = replay.data_from(records[step], keep, r12, dk)
            for key, value in data_cpu.items():
                data[key].copy_(value)
            state_initial = eager_state.clone()
            result = replay.operation(data, eager_state, dk, compensated, runtime)
            graph.replay()
            torch.npu.synchronize()
            record_step(step, result, graph_state, graph_result, state_initial)
        require(len(token_rows) == 136 and len(row["steps"]) == 9,
                "complete 136-token trajectory required")
        row["passed"] = True
        return token_rows
    except BaseException as error:
        row.update(passed=False, error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        original_error = sys.exc_info()[1]
        if graph is not None:
            try:
                graph.reset()
                row["graph_reset"] = True
            except BaseException as error:
                row.update(passed=False, graph_reset=False,
                           graph_cleanup_error=repr(error))
                if original_error is None:
                    raise
        save()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "audit-report", "manifest", "energy-plan", "retained-stats",
        "original-report", "synthetic-summary", "output-dir",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("audit-sha256", "manifest-sha256"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--max-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    replay = load_replay()
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
            "audited four-device namespace required; replay uses logical npu0")
    require(1 <= args.max_seconds <= 1800, "bounded 1..1800-second replay")
    output = args.output_dir
    require(output.is_absolute() and output == output.resolve()
            and RESULT_ROOT in output.parents and not output.exists(),
            "fresh canonical output below /drrqr-results required")
    output.mkdir(parents=False, exist_ok=False)
    report = {
        "schema": "drrqr-captured-reference-replay/v1", "status": "failed",
        "claim": CLAIM, "script_sha256": checksum(__file__),
        "replay_helper_sha256": REPLAY_SHA256, "phase": "prior_evidence",
        "created_unix_ns": time.time_ns(), "trajectories": [],
        "source_sha256": {},
        "dense_capture_gate_passed": False,
        "candidate_numerical_gate_passed": False,
        "performance_admitted": False, "task_accuracy_admitted": False,
        "protocol": {
            "variants": list(VARIANTS), "groups": 48, "input_tokens": 128,
            "decode_steps": 8, "prefill": "eager from private zero state",
            "decode": "three warmups plus NPUGraph and eager byte comparison",
            "reference": "immutable captured dense operator output/state/post-RMS",
            "independent_fp32_oracle": "preserved historical failure; excluded from this distinct gate",
            "fidelity_global_ratio_limit": 0.9,
            "fidelity_group_window_ratio_limit": 1.05,
            "max_seconds": args.max_seconds, "retry_count": 0,
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
            raise TimeoutError("fixed replay budget exceeded")

    def interrupted(signum, _frame):
        raise InterruptedError("replay interrupted by signal " + str(signum))

    previous = {
        sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)
    }
    runtime = None
    current_variant = None
    save()
    try:
        report["prior_evidence"] = validate_prior_evidence(
            args.original_report, args.synthetic_summary)
        bound = replay.bind_inputs(args)
        report["bindings"] = bound.binding
        phase("runtime_init")
        runtime = replay.init_runtime(report, lambda name: phase(name))
        require(report["operator_schema"] == bound.receipt["native_schema"],
                "native schema differs from teacher")
        groups = [
            (f"teacher-{sequence}", rank, layer)
            for sequence in range(2) for rank in range(4) for layer in replay.LAYERS
        ]
        fidelity = {}
        for variant in VARIANTS:
            current_variant = variant
            if variant != "dense128":
                require(report["dense_capture_gate_passed"],
                        "complete dense capture gate precedes candidate attribution")
            for group in groups:
                phase("load_group", group=list(group), variant=variant)
                records = []
                for step in range(9):
                    entry = bound.entries[(*group, step)]
                    record, _ = bound.audit.load_record(
                        bound.capture / entry["file"], entry["sha256"])
                    records.append(record)
                keep, _, r12 = replay.coefficients(
                    bound.plan, bound.stats, group[2], group[1])
                errors = run_trajectory(
                    records, variant, keep, r12, runtime, group, output,
                    report, save, phase, replay)
                if variant != "dense128":
                    for item in errors:
                        key = (*group, item["position"])
                        fidelity.setdefault(key, {})[
                            variant + "_relative_l2"] = item["relative_l2"]
            if variant == "dense128":
                report["dense_capture_gate_passed"] = True
                save()
        require(len(report["trajectories"]) == 144
                and all(row["passed"] for row in report["trajectories"]),
                "all dense and candidate trajectories must complete")
        report["candidate_numerical_gate_passed"] = True
        rows = [
            {
                "sequence_id": key[0], "rank": key[1], "layer": key[2],
                "position": key[3], **value,
            }
            for key, value in sorted(fidelity.items())
        ]
        report["fidelity"] = replay.fidelity_screen(rows)
        fidelity_path = output / "token-fidelity.json"
        with fidelity_path.open("x", encoding="utf-8") as stream:
            json.dump(rows, stream, allow_nan=False)
        report["token_fidelity"] = {
            "path": str(fidelity_path), "sha256": checksum(fidelity_path),
        }
        report["status"] = (
            "local_fidelity_screen_pass"
            if report["fidelity"]["passed"] else "local_fidelity_screen_failed"
        )
        report["phase"] = "complete"
    except BaseException as error:
        report.update(
            status=(
                "blocked_dense_capture_replay" if current_variant == "dense128"
                else "failed_candidate_numerical" if current_variant
                else "failed_admission"
            ),
            error=repr(error), traceback=traceback.format_exc(),
        )
    finally:
        if runtime is not None:
            try:
                report["loaded_libraries"] = validated_runtime_libraries(runtime)
                report["runtime_evidence_scope"] = (
                    "Mapped-file hashes plus same-process semantic dense-capture replay; "
                    "not same-name ACLNN symbol ownership proof."
                )
            except BaseException as error:
                report["library_observation_error"] = repr(error)
                if report["status"] == "local_fidelity_screen_pass":
                    report["status"] = "failed_runtime_evidence"
        report["completed_unix_ns"] = time.time_ns()
        save()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    print(json.dumps({"status": report["status"], "report": str(output / "report.json")}))
    return 0 if report["status"] == "local_fidelity_screen_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
