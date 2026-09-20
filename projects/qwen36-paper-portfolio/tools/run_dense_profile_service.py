#!/usr/bin/env python3
"""Launch the unchanged Qwen3.6 dense service with bounded NPU profiling."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


CAPTURE_SIZES = [
    1, 4, 8, 12, 16, 24, 32, 48, 56, 64, 72, 84, 96, 108, 112, 128,
    160, 172, 196, 200, 212, 232, 272, 288, 312, 328, 344, 360, 384,
    400, 416, 432, 448, 480, 512,
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8230)
    parser.add_argument("--profile-steps", type=int, default=30)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    allowed = Path("/results").resolve()
    if allowed not in output.parents or output.exists():
        parser.error("use a new directory below /results")
    if args.profile_steps != 30:
        parser.error("the frozen diagnostic protocol requires exactly 30 steps")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        parser.error("expected audited container devices 0,1,2,3")
    output.mkdir(parents=True)
    profiler_config = {
        "profiler": "torch",
        "torch_profiler_dir": str(output / "traces"),
        "torch_profiler_with_stack": False,
        "torch_profiler_with_memory": False,
        "torch_profiler_record_shapes": True,
        "ignore_frontend": True,
        "delay_iterations": 0,
        "max_iterations": 30,
    }
    compilation = {
        "cudagraph_capture_sizes": CAPTURE_SIZES,
        "cudagraph_mode": "FULL_DECODE_ONLY",
    }
    command = [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        "/models/Qwen3.6-27B",
        "--served-model-name",
        "qwen36-dense-profile",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--data-parallel-size",
        "1",
        "--tensor-parallel-size",
        "4",
        "--max-model-len",
        "40960",
        "--max-num-batched-tokens",
        "40960",
        "--max-num-seqs",
        "16",
        "--gpu-memory-utilization",
        "0.9",
        "--no-enable-prefix-caching",
        "--compilation-config",
        json.dumps(compilation),
        "--trust-remote-code",
        "--async-scheduling",
        "--profiler-config",
        json.dumps(profiler_config),
    ]
    source_hashes: dict[str, str] = {}
    for package, relatives in {
        "vllm": ("profiler/wrapper.py", "config/profiler.py"),
        "vllm_ascend": (
            "profiler/torch_npu_profiler.py",
            "worker/worker.py",
            "ops/gdn.py",
        ),
    }.items():
        root = Path(importlib.util.find_spec(package).origin).parent
        for relative in relatives:
            path = root / relative
            source_hashes[str(path)] = digest(path)
    manifest = {
        "schema": "qwen36-dense-profile-service/v1",
        "variant": "qwen36-dense",
        "command": command,
        "profiler_config": profiler_config,
        "compilation_config": compilation,
        "source_sha256": source_hashes,
        "wrapper_sha256": digest(Path(__file__)),
        "created_epoch_s": time.time(),
        "physical_npu_contract": [4, 5, 6, 7],
        "container_npu_namespace": [0, 1, 2, 3],
        "claim": "single-arm diagnostic profile; not a throughput benchmark",
    }
    (output / "service-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    with (output / "service.log").open("x") as log:
        child = subprocess.Popen(
            command, env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT
        )
        (output / "service.pid").write_text(str(child.pid) + "\n")

        def stop(signum, _frame):
            if child.poll() is None:
                child.send_signal(signum)

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        print(json.dumps({"service_pid": child.pid, "output_dir": str(output)}), flush=True)
        code = child.wait()
    (output / "service-exit.json").write_text(
        json.dumps({"exit_code": code, "epoch_s": time.time()}) + "\n"
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
