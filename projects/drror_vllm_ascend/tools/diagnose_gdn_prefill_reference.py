#!/usr/bin/env python3
"""One failing dense prefill K-normalizer diagnosis; never replay admission."""
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

# CPU evidence admission must precede explicit NPU initialization.
os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import torch

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path("/drrqr-results")
REPLAY_SHA = "28c735121249e37fbbc6d03436e6b10a659f72152a3cdfe7370633615b4fa9f9"
DATA = {
    "audit": ("gdn-teacher-capture-v2-audit-v2/report.json",
              "88ad45924021635e3d485b57ad14c7cf3e993836eb9dee5a3e465d0da0994777"),
    "manifest": ("gdn-teacher-inputs-v1/manifest.json",
                 "5fb48269fb6919af73040938d35ba82090ae820a41ee61dc440183acf3ec1b12"),
    "capture": ("gdn-teacher-capture-v2/teacher-capture/teacher-0.rank0.layer0.step0.pt",
                "2d319dcd86605441e030c6dbf1f2cf121ebf9a72cb569c25b6893c9a859d0f09"),
    "failed_replay": ("gdn-teacher-replay-v1/dense128.teacher-0.rank0.layer0.step0.pt",
                      "9d5c91ea9ebfd262294e09cb152aa09f33e81faf169327cebdcfb1e7aa7e03d8"),
}
L2_PATH = "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/l2norm.py"
L2_SHA = "07657e33f2240cf39e8dec9991d00022181b43946a8c1497c6c236bf4c230126"
TRITON_PATH = "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py"
TRITON_SHA = "f94d81f163f0076e8243990dd687f7ec8d42ce1ed30d67eea3155bf1c3a073a4"


def load_replay():
    import hashlib
    path = ROOT / "tools/replay_gdn_teacher.py"
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != REPLAY_SHA:
        raise ValueError("frozen replay helper changed")
    spec = importlib.util.spec_from_file_location("prefill_diagnosis_replay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(actual, reference, helper, original_mask=None):
    result = helper.metrics(actual, reference, "prefill")
    bad = (actual - reference).abs() > (0.01 + 0.01 * reference.abs())
    result.update(exceeded_elements=int(bad.sum()), exceeded_by_value_head=bad.sum((0, 2, 3)).tolist(),
                  exceeded_coordinates=bad.nonzero().tolist())
    if original_mask is not None:
        result.update(original_violations_still_exceeded=int((bad & original_mask).sum()),
                      new_violations=int((bad & ~original_mask).sum()))
    return result, bad


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    h = load_replay()
    h.require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
              "requires externally audited physical4..7 container mapping; logical0 only")
    out = args.output_dir
    h.require(out.is_absolute() and out == out.resolve() and RESULTS in out.parents
              and not out.exists(), "fresh canonical directory below /drrqr-results required")
    out.mkdir(parents=False, exist_ok=False)
    report = {"schema": "gdn-prefill-reference-diagnosis/v1", "status": "failed_diagnosis",
              "claim": "diagnosis_only_not_admission", "script_sha256": h.checksum(__file__),
              "group": ["teacher-0", 0, 0, 0], "phase": "cpu_admission",
              "created_unix_ns": time.time_ns(), "npu_l2_calls_started": 0,
              "protocol": {"rtol": 0.01, "atol": 0.01, "retry_count": 0,
                           "new_numerical_execution": "one Ascend prefill l2norm(raw_K); CPU recurrence twice",
                           "not_executed": ["model", "chunk", "native recurrence", "candidate", "graph"],
                           "deadline": "parent enforces bounded own-process timeout"},
              "goal_link": "Explain dense reference gate before DRRQR beta-compensation attribution; "
                           "no threshold change or performance/task-accuracy claim."}
    def save():
        temporary = out / "report.json.tmp"
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        temporary.replace(out / "report.json")
    def interrupted(signum, frame):
        raise InterruptedError("diagnosis interrupted by signal " + str(signum))
    handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    probe = None
    save()
    try:
        audit = h.load_tool("validate_gdn_teacher_capture", h.AUDITOR_SHA256)
        golden = h.load_tool("gdn_golden_parity", h.GOLDEN_SHA256)
        probe = h.load_tool("gdn_retained_energy_probe", h.PROBE_SHA256)
        report["bindings"] = {key: {"path": str(RESULTS / path), "sha256": sha}
                              for key, (path, sha) in DATA.items()}
        receipt = audit.bound_json(RESULTS / DATA["audit"][0], DATA["audit"][1])
        manifest = audit.bound_json(RESULTS / DATA["manifest"][0], DATA["manifest"][1])
        audit.check_manifest(manifest)
        h.require(receipt.get("status") == "dense_teacher_evidence_validated_local_only"
                  and receipt.get("schema") == audit.AUDIT_SCHEMA
                  and receipt.get("auditor_sha256") == h.AUDITOR_SHA256
                  and receipt["manifest"] == report["bindings"]["manifest"], "passed audit binding")
        rows = [r for r in receipt["files"] if (r["sequence_id"], r["rank"], r["layer"], r["step"])
                == ("teacher-0", 0, 0, 0)]
        h.require(len(rows) == 1 and rows[0]["sha256"] == DATA["capture"][1]
                  and rows[0]["file"] == Path(DATA["capture"][0]).name, "audited capture binding")
        capture, _ = audit.load_record(RESULTS / DATA["capture"][0], DATA["capture"][1])
        old, _ = audit.load_record(RESULTS / DATA["failed_replay"][0], DATA["failed_replay"][1])
        t = capture["tensors"]
        h.require(capture["manifest_sha256"] == DATA["manifest"][1]
                  and capture["input_ids"] == manifest["sequences"][0]["input_ids"]
                  and old["group"] == ["teacher-0", 0, 0] and old["step"] == 0
                  and old["variant"] == "dense128" and old["passed"] is False, "fixed failed group")
        for key, shape, dtype in [("raw_q", (1, 128, 4, 128), torch.bfloat16),
                ("raw_k", (1, 128, 4, 128), torch.bfloat16), ("raw_v", (1, 128, 12, 128), torch.bfloat16),
                ("g", (1, 128, 12), torch.float32), ("beta", (1, 128, 12), torch.bfloat16)]:
            audit.check_tensor(t[key], shape, (dtype,))
        h.require(h.exact(t["state_initial"], torch.zeros((1, 12, 128, 128)))
                  and h.exact(old["state"], t["state_final"]), "zero start / captured native state")
        q_cpu, k_cpu = golden._cpu_l2norm(t["raw_q"]), golden._cpu_l2norm(t["raw_k"])
        def reference(key):
            return golden._decode_golden(q_cpu.reshape(128, 4, 128), key.reshape(128, 4, 128),
                t["raw_v"].reshape(128, 12, 128), torch.zeros((1, 12, 128, 128), dtype=torch.float32),
                t["beta"].reshape(128, 12), 128 ** -0.5, torch.tensor([128], dtype=torch.int32),
                torch.zeros(128, dtype=torch.int32), t["g"].reshape(128, 12))[1]
        original = reference(k_cpu)
        report["original_reference_state_bytes"] = h.exact(original, old["cpu_reference_state"])
        h.require(report["original_reference_state_bytes"], "CPU recomputation changed; diagnosis invalid")
        report["native_vs_original_cpu"], bad = summarize(old["state"], original, h)
        h.require(int(bad.sum()) == 43 and not report["native_vs_original_cpu"]["passed"],
                  "original 43-element failure did not reproduce")
        report["source_sha256"] = {str(ROOT / "tools/replay_gdn_teacher.py"): REPLAY_SHA,
            str(ROOT / "tools/gdn_golden_parity.py"): h.GOLDEN_SHA256,
            str(ROOT / "tools/validate_gdn_teacher_capture.py"): h.AUDITOR_SHA256,
            str(ROOT / "tools/gdn_retained_energy_probe.py"): h.PROBE_SHA256,
            L2_PATH: L2_SHA, TRITON_PATH: TRITON_SHA}
        for path, expected in report["source_sha256"].items():
            h.require(h.checksum(path) == expected, "source changed: " + path)
        report["plugin_isolation"] = probe.disable_plugin()
        report["phase"] = "npu_initialization"
        save()
        import torch_npu
        from vllm_ascend.ops.triton import triton_utils
        from vllm_ascend.ops.triton.fla import l2norm
        h.require(Path(l2norm.__file__).resolve() == Path(L2_PATH)
                  and Path(triton_utils.__file__).resolve() == Path(TRITON_PATH), "actual source dispatch")
        torch_npu.npu.set_compile_mode(jit_compile=False)
        torch.npu.set_device(0)
        triton_utils.init_device_properties_triton()
        report.update(torch=torch.__version__, torch_npu=torch_npu.__version__,
                      logical_device=0, physical_device="4; external container-mapping audit required",
                      runtime_loading="standard imports may register libraries; no native operator call")
        report["phase"] = "one_k_normalization"
        report["npu_l2_calls_started"] = 1
        save()
        actual_k = l2norm.l2norm_fwd(t["raw_k"].to("npu:0"))
        torch.npu.synchronize()
        actual_k = h.cpu(actual_k)
        report["npu_l2_calls_completed"] = 1
        report["actual_k_archive"] = h.archive(out / "actual-k.pt", {"actual_k": actual_k})
        audit.check_tensor(actual_k, (1, 128, 4, 128), (torch.bfloat16,))
        report["k_bytes_equal"] = h.exact(actual_k, k_cpu)
        different = actual_k.view(torch.int16) != k_cpu.view(torch.int16)
        report["k_different_elements_by_key_head"] = different.sum((0, 1, 3)).tolist()
        adjusted = reference(actual_k)
        report["native_vs_actual_k_cpu"], _ = summarize(old["state"], adjusted, h, bad)
        report["references_archive"] = h.archive(out / "references.pt",
            {"cpu_k": k_cpu, "original_state": original, "actual_k_reference_state": adjusted})
        report.update(status="completed_diagnosis_only_not_admission", phase="complete",
                      interpretation="Only tests whether actual BF16 K normalization is sufficient to explain "
                                     "this saved state discrepancy. Old replay remains failed; no new admission.")
    except BaseException as error:
        report.update(status="failed_diagnosis", error=repr(error), traceback=traceback.format_exc())
    finally:
        if probe is not None:
            try:
                report["mapped_libraries"] = probe.loaded_libraries()
                report["library_scope"] = "mapped-file identity only; not ACLNN symbol or device-binary resolution"
            except BaseException as error:
                report.update(status="failed_diagnosis", library_error=repr(error))
        report["completed_unix_ns"] = time.time_ns()
        save()
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    print(json.dumps({"status": report["status"], "report": str(out / "report.json")}), flush=True)
    return 0 if report["status"] == "completed_diagnosis_only_not_admission" else 1


if __name__ == "__main__":
    sys.exit(main())
