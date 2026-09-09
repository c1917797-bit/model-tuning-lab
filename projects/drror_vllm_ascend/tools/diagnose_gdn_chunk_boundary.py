#!/usr/bin/env python3
"""CPU-only fixed S64 BF16 boundary counterfactual; not a replacement gate."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import torch

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path("/drrqr-results")
OUTPUT = RESULTS / "gdn-prefill-boundary-reference-v1"
SOURCES = {
    "gdn_golden_parity": "1a2d1a61040a58a6f0c1d90cdbf0fc17058f3273eaef8b3d1b80116c97d92cb9",
    "validate_gdn_teacher_capture": "a3e55fdb31f60894853532602628780a488901310a6717d22fde0983833e0efb",
}
INPUTS = {
    "audit": ("gdn-teacher-capture-v2-audit-v2/report.json",
              "88ad45924021635e3d485b57ad14c7cf3e993836eb9dee5a3e465d0da0994777"),
    "manifest": ("gdn-teacher-inputs-v1/manifest.json",
                 "5fb48269fb6919af73040938d35ba82090ae820a41ee61dc440183acf3ec1b12"),
    "capture": ("gdn-teacher-capture-v2/teacher-capture/teacher-0.rank0.layer0.step0.pt",
                "2d319dcd86605441e030c6dbf1f2cf121ebf9a72cb569c25b6893c9a859d0f09"),
    "failed_replay": ("gdn-teacher-replay-v1/dense128.teacher-0.rank0.layer0.step0.pt",
                      "9d5c91ea9ebfd262294e09cb152aa09f33e81faf169327cebdcfb1e7aa7e03d8"),
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_helper(name):
    path = ROOT / "tools" / (name + ".py")
    require(path == path.resolve() and path.is_file() and sha(path) == SOURCES[name],
            "frozen helper identity changed: " + name)
    spec = importlib.util.spec_from_file_location("boundary_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cpu_only():
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD") == "0"
            and not any(x.startswith(("torch_npu", "vllm_ascend")) for x in sys.modules),
            "CPU-only process must not import NPU/runtime modules")


def state_metrics(actual, reference, golden, original_mask=None):
    result = golden._tensor_metrics(actual, reference, 0.01, 0.01)
    require(result["finite"], "state comparison must be finite")
    bad = (actual - reference).abs() > (0.01 + 0.01 * reference.abs())
    result.update(rtol=0.01, atol=0.01, exceeded_elements=int(bad.sum()),
                  exceeded_by_value_head=bad.sum((0, 2, 3)).tolist(),
                  exceeded_coordinates=bad.nonzero().tolist())
    if original_mask is not None:
        result.update(original_violations_still_exceeded=int((bad & original_mask).sum()),
                      original_violations_resolved=int((~bad & original_mask).sum()),
                      new_violations=int((bad & ~original_mask).sum()))
    return result, bad


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    cpu_only()
    out = args.output_dir
    require(out == OUTPUT and out == out.resolve() and not out.exists(),
            "only this never-existing canonical output directory is admitted")
    out.mkdir(parents=False, exist_ok=False)
    report = {"schema": "gdn-chunk-boundary-diagnosis/v1", "status": "failed_diagnosis",
              "claim": "diagnosis_only_not_admission", "script_sha256": sha(__file__),
              "created_unix_ns": time.time_ns(), "phase": "cpu_admission",
              "group": ["teacher-0", 0, 0, 0], "npu_calls": 0,
              "goal_link": "Explain the existing dense-reference gate before DRRQR beta attribution; "
                           "not task accuracy, throughput or candidate admission.",
              "protocol": {"tokens": 128, "boundary_after_token_count": 64,
                           "only_changed_operation": "S64.to(bfloat16).to(float32)",
                           "rtol": 0.01, "atol": 0.01, "retry_count": 0,
                           "input_state": "independent CPU FP32 zeros",
                           "not_executed": ["NPU", "native operators", "model", "candidate", "graph"]}}
    def save():
        partial = out / "report.json.tmp"
        partial.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        partial.replace(out / "report.json")
    def interrupted(signum, frame):
        raise InterruptedError("CPU diagnosis interrupted by signal " + str(signum))
    handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    save()
    try:
        audit = load_helper("validate_gdn_teacher_capture")
        golden = load_helper("gdn_golden_parity")
        require((golden.PREFILL_RTOL, golden.PREFILL_ATOL) == (0.01, 0.01), "original gates changed")
        report["sources"] = {str(ROOT / "tools" / (name + ".py")): value for name, value in SOURCES.items()}
        report["inputs"] = {name: {"path": str(RESULTS / path), "sha256": value}
                            for name, (path, value) in INPUTS.items()}
        receipt = audit.bound_json(RESULTS / INPUTS["audit"][0], INPUTS["audit"][1])
        manifest = audit.bound_json(RESULTS / INPUTS["manifest"][0], INPUTS["manifest"][1])
        audit.check_manifest(manifest)
        require(receipt.get("schema") == audit.AUDIT_SCHEMA
                and receipt.get("status") == "dense_teacher_evidence_validated_local_only"
                and receipt.get("auditor_sha256") == SOURCES["validate_gdn_teacher_capture"]
                and receipt.get("manifest") == report["inputs"]["manifest"], "passed audit binding")
        entries = [x for x in receipt["files"] if (x["sequence_id"], x["rank"], x["layer"], x["step"])
                   == ("teacher-0", 0, 0, 0)]
        require(len(entries) == 1 and entries[0]["sha256"] == INPUTS["capture"][1]
                and entries[0]["file"] == Path(INPUTS["capture"][0]).name, "exact capture audit row")
        capture, _ = audit.load_record(RESULTS / INPUTS["capture"][0], INPUTS["capture"][1])
        old, _ = audit.load_record(RESULTS / INPUTS["failed_replay"][0], INPUTS["failed_replay"][1])
        require((capture["sequence_id"], capture["rank"], capture["layer"], capture["step"])
                == ("teacher-0", 0, 0, 0) and capture["manifest_sha256"] == INPUTS["manifest"][1]
                and capture["input_ids"] == manifest["sequences"][0]["input_ids"]
                and old["schema"] == "drrqr-real-teacher-trajectory/v1"
                and old["group"] == ["teacher-0", 0, 0] and old["step"] == 0
                and old["variant"] == "dense128" and old["passed"] is False, "fixed failed group")
        t = capture["tensors"]
        for key, shape, dtype in [("raw_q", (1, 128, 4, 128), torch.bfloat16),
                ("raw_k", (1, 128, 4, 128), torch.bfloat16), ("raw_v", (1, 128, 12, 128), torch.bfloat16),
                ("g", (1, 128, 12), torch.float32), ("beta", (1, 128, 12), torch.bfloat16)]:
            audit.check_tensor(t[key], shape, (dtype,))
        zero = torch.zeros((1, 12, 128, 128), dtype=torch.float32)
        require(audit.equal_bytes(t["state_initial"], zero) and audit.equal_bytes(t["state_final"], old["state"]),
                "zero start and unchanged native target")
        q, k = golden._cpu_l2norm(t["raw_q"]).reshape(128, 4, 128), golden._cpu_l2norm(t["raw_k"]).reshape(128, 4, 128)
        v, beta, g = t["raw_v"].reshape(128, 12, 128), t["beta"].reshape(128, 12), t["g"].reshape(128, 12)
        def recurrence(start, end, state):
            return golden._decode_golden(q[start:end], k[start:end], v[start:end], state, beta[start:end],
                128 ** -0.5, torch.tensor([end-start], dtype=torch.int32),
                torch.zeros(end-start, dtype=torch.int32), g[start:end])
        original_output, original_state = recurrence(0, 128, zero.clone())
        report["original_reference_state_bytes"] = audit.equal_bytes(original_state, old["cpu_reference_state"])
        report["original_reference_output_bytes"] = audit.equal_bytes(original_output, old["cpu_reference_output"])
        require(report["original_reference_state_bytes"] and report["original_reference_output_bytes"],
                "old CPU reference bytes not reproduced")
        report["native_vs_original"], original_bad = state_metrics(old["state"], original_state, golden)
        require(int(original_bad.sum()) == 43 and not report["native_vs_original"]["allclose"],
                "original 43 violations not reproduced")
        first_output, state64 = recurrence(0, 64, zero.clone())
        unchanged_second_output, split_state = recurrence(64, 128, state64.clone())
        report["split_without_rounding_state_bytes"] = audit.equal_bytes(split_state, original_state)
        report["split_without_rounding_output_bytes"] = audit.equal_bytes(
            torch.cat((first_output, unchanged_second_output)), original_output)
        require(report["split_without_rounding_state_bytes"] and report["split_without_rounding_output_bytes"],
                "splitting itself changed reference; single-boundary diagnosis invalid")
        report["phase"] = "one_boundary_round_trip"
        save()
        rounded64 = state64.to(torch.bfloat16).to(torch.float32)
        second_output, boundary_state = recurrence(64, 128, rounded64)
        report["native_vs_boundary"], _ = state_metrics(old["state"], boundary_state, golden, original_bad)
        report["boundary_rounding_max_abs"] = float((rounded64 - state64).abs().max())
        report["boundary_rounding_changed_elements"] = int((rounded64 != state64).sum())
        archive = out / "boundary-reference.pt"
        with archive.open("xb") as stream:
            torch.save({"schema": report["schema"], "original_state": original_state,
                        "boundary_state": boundary_state, "state64_fp32": state64,
                        "state64_bf16_roundtrip": rounded64, "original_cpu_output": original_output,
                        "boundary_cpu_output": torch.cat((first_output, second_output))}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        report["archive"] = {"path": str(archive), "sha256": sha(archive), "size_bytes": archive.stat().st_size}
        cpu_only()
        report.update(status="completed_diagnosis_only_not_admission", phase="complete",
            cpu_only_verified=True, torch=torch.__version__, cpu_threads=torch.get_num_threads(),
            boundary_alone_sufficient_under_original_gate=report["native_vs_boundary"]["allclose"],
            interpretation="One S64 BF16 round-trip counterfactual only; not a simulation of all chunk "
                           "rounding, not a replacement golden reference. Old replay remains failed; "
                           "no candidate executed or admitted.")
    except BaseException as error:
        report.update(status="failed_diagnosis", error=repr(error), traceback=traceback.format_exc())
    finally:
        report["completed_unix_ns"] = time.time_ns()
        save()
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    print(json.dumps({"status": report["status"], "report": str(out / "report.json"),
        "boundary_alone_sufficient_under_original_gate": report.get("boundary_alone_sufficient_under_original_gate")}),
        flush=True)
    return 0 if report["status"] == "completed_diagnosis_only_not_admission" else 1


if __name__ == "__main__":
    sys.exit(main())
