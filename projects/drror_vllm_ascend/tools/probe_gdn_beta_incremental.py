#!/usr/bin/env python3
"""Real-input beta-transform diagnostic only; original replay qualification stays failed."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time
import traceback

import torch

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = Path("/drrqr-results")
REPLAY_SOURCE = ROOT / "tools/replay_gdn_teacher.py"
REPLAY_SHA256 = "d864aecf4ca98cbf4b451542d1757e36aa853997055c8d7c653b7f1d4f2faa80"
ORIGINAL_REPLAY = RESULT_ROOT / "gdn-teacher-replay-v1/report.json"
ORIGINAL_REPLAY_SHA256 = "eb6aa7e8af0234554951b01a808da566fda02994317519a500357b3d586ba79b"
ORIGINAL_SCRIPT_SHA256 = "46fdfe7894e087cd47c10327b683dfc081a041afdcea400c87485c5918087e95"
GROUP = ("teacher-0", 0, 0)
LANES = ("A_eager", "B_eager", "A_graph", "B_graph")
SLOTS, DK, DECODE_STEPS = 4, 64, 8
CLAIM = ("Incremental diagnostic only: CPU-prequantized beta versus NPU beta transform on "
         "one fixed real teacher input trajectory. Original FP32-reference qualification failed. "
         "No performance admission, task-accuracy claim, full-model recovery or portable speedup.")


def require(value, reason):
    if not value:
        raise ValueError(reason)


def load_replay():
    raw = REPLAY_SOURCE.read_bytes()
    require(not REPLAY_SOURCE.is_symlink() and hashlib.sha256(raw).hexdigest() == REPLAY_SHA256,
            "frozen replay helper source changed")
    spec = importlib.util.spec_from_file_location("beta_incremental_replay", REPLAY_SOURCE)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    return replay


def original_failure(bound, replay):
    receipt = bound.audit.bound_json(ORIGINAL_REPLAY, ORIGINAL_REPLAY_SHA256)
    for key in ("audit", "manifest", "energy_plan", "retained_stats"):
        require(receipt.get("bindings", {}).get(key) == bound.binding.get(key),
                "diagnostic inputs differ from original replay: " + key)
    require(receipt.get("script_sha256") == ORIGINAL_SCRIPT_SHA256
            and receipt.get("dense_gate_passed") is False
            and receipt.get("candidate_numerical_gate_passed") is False,
            "original replay failure binding")
    trajectories = receipt.get("trajectories", [])
    require(len(trajectories) == 1, "original replay was dense first-group only")
    trajectory = trajectories[0]
    require((trajectory.get("sequence_id"), trajectory.get("rank"), trajectory.get("layer")) == GROUP
            and trajectory.get("variant") == "dense128" and trajectory.get("passed") is False
            and len(trajectory.get("steps", [])) == 1, "original dense trajectory binding")
    step = trajectory["steps"][0]
    require(step.get("step") == 0 and step.get("phase") == "prefill"
            and step.get("metrics", {}).get("full_state_cpu", {}).get("passed") is False,
            "original FP32 reference failure must remain explicit")
    return {"path": str(ORIGINAL_REPLAY), "sha256": ORIGINAL_REPLAY_SHA256,
            "script_sha256": ORIGINAL_SCRIPT_SHA256, "status": receipt.get("status"),
            "qualification_passed": False, "failed_check": "dense128.step0.full_state_cpu",
            "metrics": step["metrics"]["full_state_cpu"]}


def lane_inputs(record, keep, r12, lane, replay):
    require(lane in LANES, "unknown diagnostic lane")
    data = replay.data_from(record, keep, r12, DK)
    # A transforms on CPU before upload. B receives the original BF16 beta
    # and performs exactly replay.operation/prefill's FP32 multiply/BF16 cast.
    require(all(value.device.type == "cpu" for value in data.values()), "CPU source inputs required")
    expected_beta = replay.beta_product(data["beta"], data["r"])[1]
    if lane.startswith("A_"):
        data["beta"] = expected_beta.clone()
    return data, expected_beta


def slot_for_step(step):
    require(type(step) is int and 1 <= step <= DECODE_STEPS, "decode step outside fixed budget")
    return (step - 1) % SLOTS, step % SLOTS


def migrate_own_state(state, step):
    previous, selected = slot_for_step(step)
    # Diagnostic slot relocation, not scheduler replay. Never use a dense
    # capture state or another lane's state as the source.
    state[selected].copy_(state[previous])
    return selected


def tracked_metadata(branch, runtime):
    values = {"state": branch["state"], **{"input." + key: value for key, value in branch["data"].items()}}
    if branch.get("graph_result") is not None:
        values.update({"graph_result." + key: value for key, value in branch["graph_result"].items()})
    return {key: runtime.probe.metadata(value) for key, value in values.items()}


def compare_step(step, branches, expected_beta, expected_product, before,
                 runtime, replay, out, report, save):
    anchor = branches["A_eager"]
    checks, payload_lanes = {}, {}
    for lane in LANES:
        branch, result = branches[lane], branches[lane]["result"]
        lane_checks = {
            "beta_expected_cpu_bytes": replay.exact(result["beta"], expected_beta),
            "beta_A_eager_bytes": replay.exact(result["beta"], anchor["result"]["beta"]),
            "output_A_eager_bytes": replay.exact(result["output"], anchor["result"]["output"]),
            "full_state_A_eager_bytes": replay.exact(branch["state"], anchor["state"]),
            "post_rms_A_eager_bytes": replay.exact(result["norm"], anchor["result"]["norm"]),
        }
        if lane.startswith("B_"):
            lane_checks["beta_product_fp32_cpu_bytes"] = replay.exact(result["product"], expected_product)
        if step:
            lane_checks["persistent_metadata"] = branch["metadata"] == tracked_metadata(branch, runtime)
            lane_checks["unselected_slots_unchanged"] = runtime.probe.unselected_unchanged(
                before[lane], replay.cpu(branch["state"]),
                torch.tensor([step % SLOTS], dtype=torch.int32))
        checks[lane] = lane_checks
        payload_lanes[lane] = {
            "beta": replay.cpu(result["beta"]), "output": replay.cpu(result["output"]),
            "state": replay.cpu(branch["state"]), "post_rms": replay.cpu(result["norm"]),
            "beta_product_fp32": replay.cpu(result["product"]) if lane.startswith("B_") else None,
        }
    passed = all(all(values.values()) for values in checks.values())
    payload = {"schema": "drrqr-beta-incremental-step/v1", "group": list(GROUP), "step": step,
               "lanes": payload_lanes, "checks": checks, "passed": passed,
               "expected_beta_product_fp32": replay.cpu(expected_product),
               "expected_beta_bf16": replay.cpu(expected_beta)}
    archive = replay.archive(out / f"step{step}.pt", payload)
    report["steps"].append({"step": step, "phase": "prefill" if step == 0 else "decode",
                            "state_indices": [step % SLOTS], "checks": checks,
                            "archive": archive, "passed": passed})
    save()  # Failed comparisons are retained before the exception terminates the matrix.
    require(passed, "finite bytewise beta/output/full-state/post-RMS/graph gate failed; no retry")


def run_incremental(records, keep, r12, runtime, replay, out, report, save, phase):
    require(len(records) == 9 and [record["step"] for record in records] == list(range(9)),
            "one complete ordered prefill plus eight decode records")
    branches = {}
    original_error = None
    try:
        for lane in LANES:
            phase("prefill", lane=lane, step=0)
            inputs, expected_beta = lane_inputs(records[0], keep, r12, lane, replay)
            data = {key: value.to("npu:0") for key, value in inputs.items()}
            result, prefix_state = replay.prefill(data, DK, lane.startswith("B_"), runtime)
            arena = torch.zeros((SLOTS, 12, 128, DK), dtype=torch.float32, device="npu:0")
            arena[0:1].copy_(prefix_state)
            branches[lane] = {"state": arena, "result": result, "graph": None,
                              "graph_result": None, "prefill_state": arena.clone()}
            torch.npu.synchronize()
        require(len({branch["state"].data_ptr() for branch in branches.values()}) == 4,
                "four independent private state arenas required")
        expected_product = replay.beta_product(records[0]["tensors"]["beta"], r12)[0]
        compare_step(0, branches, expected_beta, expected_product, {}, runtime, replay, out, report, save)

        for lane in LANES:
            branch = branches[lane]
            inputs, _ = lane_inputs(records[1], keep, r12, lane, replay)
            inputs["indices"].fill_(1)
            branch["data"] = {key: value.to("npu:0") for key, value in inputs.items()}
            if lane.endswith("_graph"):
                phase("graph_warmup", lane=lane)
                migrate_own_state(branch["state"], 1)
                for _ in range(3):
                    replay.operation(branch["data"], branch["state"], DK, lane.startswith("B_"), runtime)
                    torch.npu.synchronize()
                phase("graph_capture", lane=lane)
                branch["graph"] = torch.npu.NPUGraph()
                with torch.npu.graph(branch["graph"]):
                    branch["graph_result"] = replay.operation(
                        branch["data"], branch["state"], DK, lane.startswith("B_"), runtime)
                torch.npu.synchronize()
                branch["state"].copy_(branch["prefill_state"])
                torch.npu.synchronize()
                require(replay.exact(branch["state"], branch["prefill_state"]),
                        "graph warmup/capture state reset failed")
            branch["metadata"] = tracked_metadata(branch, runtime)
        report["persistent_metadata"] = {lane: branch["metadata"] for lane, branch in branches.items()}
        report["graph_prefill_reset_bytes"] = True
        save()

        for step in range(1, 9):
            before = {}
            for lane in LANES:
                branch = branches[lane]
                phase("decode", lane=lane, step=step)
                inputs, expected_beta = lane_inputs(records[step], keep, r12, lane, replay)
                previous, selected = slot_for_step(step)
                inputs["indices"].fill_(selected)
                for key, value in inputs.items():
                    branch["data"][key].copy_(value)
                require(migrate_own_state(branch["state"], step) == selected, "diagnostic slot migration")
                before[lane] = replay.cpu(branch["state"])
                if branch["graph"] is None:
                    branch["result"] = replay.operation(
                        branch["data"], branch["state"], DK, lane.startswith("B_"), runtime)
                else:
                    branch["graph"].replay()
                    branch["result"] = branch["graph_result"]
                torch.npu.synchronize()
            expected_product = replay.beta_product(records[step]["tensors"]["beta"], r12)[0]
            compare_step(step, branches, expected_beta, expected_product, before,
                         runtime, replay, out, report, save)
        require(len(report["steps"]) == 9 and all(step["passed"] for step in report["steps"]),
                "complete incremental matrix required")
        report["incremental_numerical_passed"] = True
    except BaseException as error:
        original_error = error
        raise
    finally:
        cleanup_errors = {}
        for lane, branch in branches.items():
            graph = branch.get("graph")
            if graph is not None:
                try:
                    graph.reset()
                except BaseException as error:
                    cleanup_errors[lane] = repr(error)
        report["graph_cleanup_errors"] = cleanup_errors
        save()
        if cleanup_errors and original_error is None:
            raise RuntimeError("graph cleanup failed: " + repr(cleanup_errors))


def check_original_unchanged(report):
    row = {"path": str(ORIGINAL_REPLAY), "expected_sha256": ORIGINAL_REPLAY_SHA256,
           "sha256": None, "unchanged": False}
    report["original_report_check"] = row
    row["sha256"] = hashlib.sha256(ORIGINAL_REPLAY.read_bytes()).hexdigest()
    row["unchanged"] = row["sha256"] == ORIGINAL_REPLAY_SHA256
    require(row["unchanged"], "original replay report identity changed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("audit-report", "manifest", "energy-plan", "retained-stats", "output-dir"):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("audit-sha256", "manifest-sha256"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args(argv)
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
            "externally audited physical4-7 namespace required; only logical0 is used")
    require(1 <= args.max_seconds <= 600, "bounded diagnostic: 1..600 seconds")
    out = args.output_dir
    require(out.is_absolute() and out == out.resolve() and RESULT_ROOT in out.parents
            and not out.exists(), "fresh canonical diagnostic directory required")
    out.mkdir(parents=False, exist_ok=False)
    report = {
        "schema": "drrqr-beta-incremental-diagnostic/v1", "status": "failed_admission", "claim": CLAIM,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "steps": [], "incremental_numerical_passed": False,
        "original_qualification_passed": False, "performance_admitted": False,
        "helper_sha256": REPLAY_SHA256, "phase": "admission",
        "protocol": {"group": list(GROUP), "dk": DK, "slots": SLOTS, "lanes": list(LANES),
                     "prefill_tokens": 128, "decode_steps": 8, "graph_warmups": 3,
                     "slot_relocation": "own prior slot to step%4 before each decode; not scheduler replay",
                     "beta_A": "CPU FP32(beta_base)*FP32(train_r) then BF16 before NPU upload",
                     "beta_B": "same FP32 multiply/BF16 cast on NPU; decode transform inside graph",
                     "reference": "A_eager; finite byte equality only, no replacement FP32 qualification",
                     "retry_count": 0, "max_seconds": args.max_seconds,
                     "hard_deadline": "parent must enforce an own-process timeout for a stuck native call"},
    }
    deadline = time.monotonic() + args.max_seconds
    def save():
        partial = out / "report.json.tmp"
        partial.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        partial.replace(out / "report.json")
    def phase(name, **details):
        report.update(phase=name, active=details)
        save()
        if time.monotonic() > deadline:
            raise TimeoutError("incremental diagnostic budget exceeded")
    def interrupted(signum, frame):
        raise InterruptedError("diagnostic interrupted by signal " + str(signum))
    handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    replay = runtime = bound = None
    save()
    try:
        replay = load_replay()
        report["script_sha256"] = replay.checksum(__file__)
        bound = replay.bind_inputs(args)  # Reuse all immutable CPU source/tensor/capture admission gates.
        report["bindings"] = bound.binding
        report["original_qualification"] = original_failure(bound, replay)
        records, inputs = [], []
        for step in range(9):
            entry = bound.entries[(*GROUP, step)]
            record, _ = bound.audit.load_record(bound.capture / entry["file"], entry["sha256"])
            require((record["sequence_id"], record["rank"], record["layer"], record["step"]) == (*GROUP, step),
                    "fixed real capture group/step")
            records.append(record)
            inputs.append(entry)
        report["capture_records"] = inputs
        keep, r4, r12 = replay.coefficients(bound.plan, bound.stats, 0, 0)
        report["retained_key_energy"] = {"source": "frozen old rows0..11 train_k_mean only",
                                       "r4": r4.tolist(), "r12": r12.tolist(),
                                       "keep_head_local": keep.tolist()}
        phase("runtime_init")
        runtime = replay.init_runtime(report, lambda name: phase(name))
        require(report["operator_schema"] == bound.receipt["native_schema"], "native schema differs from teacher")
        report["status"] = "failed_incremental_diagnostic"
        run_incremental(records, keep, r12, runtime, replay, out, report, save, phase)
        report["status"] = "incremental_diagnostic_pass_original_qualification_failed"
        report["phase"] = "complete"
    except BaseException as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        if runtime is not None:
            try:
                # The helper saves raw observations before any path/hash validation.
                libraries = runtime.probe.loaded_libraries()
                replay.check_runtime_libraries(libraries, bound.receipt["identities"], report, save)
            except BaseException as error:
                report.update(runtime_evidence_passed=False, library_error=repr(error))
                if report["status"] == "incremental_diagnostic_pass_original_qualification_failed":
                    report["status"] = "failed_runtime_evidence"
        try:
            check_original_unchanged(report)
        except BaseException as error:
            report["original_report_error"] = repr(error)
            if report["status"] == "incremental_diagnostic_pass_original_qualification_failed":
                report["status"] = "failed_original_evidence"
        report["completed_unix_ns"] = time.time_ns()
        save()
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    print(json.dumps({"status": report["status"], "report": str(out / "report.json")}), flush=True)
    return 0 if report["status"] == "incremental_diagnostic_pass_original_qualification_failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
