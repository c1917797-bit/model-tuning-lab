#!/usr/bin/env python3
"""Bounded dense teacher capture service, explicitly eager and calibration-only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import sys
import time

ROOT = Path("/cache/cch/drror_vllm_ascend")
RESULT_ROOT = Path("/drrqr-results")
MODEL = "/cache/austinov/Qwen3.8-27B"
WORKER = ROOT / "tools/gdn_teacher_capture_worker.py"
WORKER_CLASS = "gdn_teacher_capture_worker.GdnTeacherCaptureWorker"
SHARED_SHA256 = "6d0091efb55adbf3acb6eec20f1c9c2d8f53844202018d11acb5f2ffa1f023f3"
HASH = re.compile(r"^[0-9a-f]{64}$")
PLUGIN_VERSION = "0.1.11"
# These native libraries do not share the plugin's "0"/"1" convention.
# In particular, CANN 9.1 libhccl reports an unset default of "false" and
# rejects "0". Preserve native defaults by removing both overrides, rather
# than guessing a common explicit false value for HCCL and LCCL.
UNSET_RUNTIME_FLAGS = ("HCCL_DETERMINISTIC", "LCCL_DETERMINISTIC")
MODEL_HASHES = {
    "config.json": "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab",
    "model.safetensors.index.json": "77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df",
}


def load_shared():
    path = Path(__file__).resolve().with_name("run_layerwise_service.py")
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHARED_SHA256:
        raise ValueError("shared lifecycle/provenance helper identity changed; re-review required")
    spec = importlib.util.spec_from_file_location("gdn_teacher_shared_service", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_shared()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--build-manifest-sha256", required=True)
    parser.add_argument("--reference-manifest-sha256", required=True)
    parser.add_argument("--worker-sha256", required=True)
    parser.add_argument("--capture-manifest", type=Path, required=True)
    parser.add_argument("--capture-manifest-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-service-seconds", type=int, default=1800)
    parser.add_argument("--term-grace-seconds", type=int, default=30)
    args = parser.parse_args(argv)
    args.plugin_version = PLUGIN_VERSION
    for name in ("build_manifest_sha256", "reference_manifest_sha256", "worker_sha256",
                 "capture_manifest_sha256"):
        if not HASH.fullmatch(getattr(args, name)):
            parser.error(name + " must be an explicit lowercase SHA256")
    if not 1 <= args.max_service_seconds <= 1800:
        parser.error("capture service budget must be between 1 and 1800 seconds")
    if not 1 <= args.term_grace_seconds <= 30:
        parser.error("TERM grace must be between 1 and 30 seconds")
    for name in ("build_manifest", "capture_manifest", "output_dir"):
        if not getattr(args, name).is_absolute():
            parser.error(name + " must be absolute")
    return parser, args


def service_command(executable=None):
    return [
        executable or sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL, "--host", "0.0.0.0", "--port", "6666",
        "--served-model-name", "qwen3.8", "--trust-remote-code",
        "--dtype", "bfloat16", "--tensor-parallel-size", "4",
        "--max-model-len", "4096", "--max-num-batched-tokens", "4096",
        "--max-num-seqs", "1", "--gpu-memory-utilization", "0.9",
        "--no-enable-prefix-caching", "--enforce-eager",
        "--worker-cls", WORKER_CLASS,
    ]


def service_environment(args, output, inherited=None):
    env = dict(os.environ if inherited is None else inherited)
    if env.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        raise ValueError("expected the audited four-device container namespace")
    # An inherited repository import path could silently replace the installed wheel.
    entries = [entry for entry in env.get("PYTHONPATH", "").split(os.pathsep) if entry]
    if any(Path(entry).resolve() == ROOT.resolve() for entry in entries):
        raise ValueError("repository root on PYTHONPATH would shadow the installed wheel")
    if env.get("DRRQR_DIAGNOSTIC_DETERMINISM") not in (None, "0"):
        raise ValueError("determinism experiments are not part of teacher capture")
    inherited_flags = {key: value for key, value in env.items()
                       if key.startswith(("VLLM_ASCEND_DRRQR_", "DRRQR_", "VLLM_ASCEND_ENABLE_",
                                          "VLLM_BATCH_INVARIANT", "HCCL_", "LCCL_"))}
    for key in list(env):
        if key.startswith(("VLLM_ASCEND_DRRQR_", "DRRQR_")):
            del env[key]
    for key in UNSET_RUNTIME_FLAGS:
        env.pop(key, None)
    disabled = {
        "VLLM_ASCEND_DRRQR_ENABLE": "0",
        "VLLM_ASCEND_DRRQR_CAPTURE_ENABLE": "0",
        "VLLM_ASCEND_DRRQR_CONV_LAYOUT": "0",
        "VLLM_ASCEND_DRRQR_PREFILL_MC2": "0",
        "VLLM_ASCEND_DRRQR_PREFILL_MC2_MIXED": "0",
        "VLLM_ASCEND_ENABLE_NZ": "0",
        "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE": "0",
        "VLLM_ASCEND_ENABLE_FLASHCOMM1": "0",
        "VLLM_ASCEND_ENABLE_FLASHCOMM": "0",
        "VLLM_BATCH_INVARIANT": "0",
        "DRRQR_DIAGNOSTIC_DETERMINISM": "0",
    }
    observer = {
        "DRRQR_GDN_TEACHER_MANIFEST": str(args.capture_manifest.resolve()),
        "DRRQR_GDN_TEACHER_MANIFEST_SHA256": args.capture_manifest_sha256,
        "DRRQR_GDN_TEACHER_DIR": str(output / "teacher-capture"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    env.update(disabled)
    env.update(observer)
    env["PYTHONPATH"] = str(WORKER.parent) + (os.pathsep + os.pathsep.join(entries) if entries else "")
    return env, disabled, observer, inherited_flags


def main(argv=None):
    parser, args = parse_args(argv)
    if Path(__file__).resolve().parent != ROOT / "tools":
        parser.error("run this launcher from the plugin repository tools directory")
    output = args.output_dir.resolve()
    if RESULT_ROOT.resolve() not in output.parents or output.exists():
        parser.error("choose a fresh directory below /drrqr-results")
    if WORKER.is_symlink() or WORKER.resolve() != ROOT / "tools/gdn_teacher_capture_worker.py":
        raise ValueError("observer worker must be the explicit non-symlink repository tool")
    if shared.digest(WORKER) != args.worker_sha256:
        raise ValueError("observer worker identity differs")
    capture_manifest = shared.read_bound_json(args.capture_manifest, args.capture_manifest_sha256)
    env, disabled, observer, inherited = service_environment(args, output)
    provenance = shared.verify_build(args)
    runtime = shared.verify_runtime(args.reference_manifest_sha256)
    model_hashes = {name: shared.digest(Path(MODEL) / name) for name in MODEL_HASHES}
    if model_hashes != MODEL_HASHES:
        raise ValueError("original checkpoint metadata identity differs")
    command = service_command()
    # This is a collision check, never permission to replace an existing owner.
    with socket.socket() as probe:
        probe.bind(("0.0.0.0", 6666))
    output.mkdir(parents=True, exist_ok=False)
    (output / "teacher-capture").mkdir(exist_ok=False)
    manifest = {
        "schema": "drrqr-gdn-teacher-service/v1", **provenance, **runtime,
        "variant": "dense128", "model": MODEL, "model_metadata_sha256": model_hashes,
        "shared_hf_head_k_dim": 128,
        "tensor_parallel_size": 4, "command": command,
        "calibration_only": True, "enforce_eager": True, "profiler_config": None,
        "worker": str(WORKER), "worker_class": WORKER_CLASS,
        "worker_sha256": args.worker_sha256,
        "capture_manifest": str(args.capture_manifest.resolve()),
        "capture_manifest_sha256": args.capture_manifest_sha256,
        "capture_manifest_schema": capture_manifest.get("schema"),
        "disabled_optimization_flags": disabled, "observer_flags": observer,
        "unset_runtime_flags": {key: None for key in UNSET_RUNTIME_FLAGS},
        "native_determinism_policy": "HCCL/LCCL overrides absent from child environment; "
                                     "native defaults, not explicit zero/false settings",
        "inherited_runtime_environment": inherited,
        "common_optimizations": "disabled for this teacher-math capture only",
        "request_policy": {
            "enable_thinking": False,
            "enforcement": "bound collector must send no-thinking chat_template_kwargs or "
                           "the equivalent frozen raw-token prompt; launcher does not rewrite requests",
        },
        "wrapper_sha256": shared.digest(Path(__file__)),
        "shared_helper_sha256": SHARED_SHA256,
        "created_epoch_s": time.time(), "max_service_seconds": args.max_service_seconds,
        "term_grace_seconds": args.term_grace_seconds,
        "stop_request_path": str(output / "stop.request"),
        "physical_npu_contract": [4, 5, 6, 7], "container_npu_namespace": [0, 1, 2, 3],
        "physical_mapping_verification": "external parent preflight required before launch",
        "claim": "Dense eager teacher capture only; no graph, performance or task-accuracy admission. "
                 "Capture validity requires worker/collector reports, not launcher success.",
    }
    shared.write_record(output / "service-manifest.json", manifest)
    return shared.run_service(command, env, output, args.max_service_seconds, args.term_grace_seconds)


if __name__ == "__main__":
    sys.exit(main())
