#!/usr/bin/env python3
"""Immutable v11 candidate-only full-GDN timing gate."""
from pathlib import Path
import hashlib

import run_npu_gate_v10 as previous


gate = previous.gate
BASE_DOCKER_COMMAND = previous.docker_command
V8_NUMERICAL = Path(
    "/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v8/numerical-gate.json"
)
V8_NUMERICAL_SHA256 = "ab112ae3ee4e2cf91af2399ccf18f65caf159831998f99b976dad7eff3dafa2c"

gate.RESULT = Path("/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v11")
gate.CONTAINER = "mxr_qwen36_npu_gate_v11_20260920"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_correctness_dependency() -> None:
    if sha256(V8_NUMERICAL) != V8_NUMERICAL_SHA256:
        raise RuntimeError("immutable v8 numerical dependency mismatch")


def docker_command() -> list[str]:
    command = BASE_DOCKER_COMMAND()
    old_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe_v10.py"
    )
    new_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe_v11.py"
    )
    command[command.index(old_probe)] = new_probe
    return command


def configure_gate() -> None:
    previous.configure_gate()
    gate.docker_command = docker_command


if __name__ == "__main__":
    verify_correctness_dependency()
    configure_gate()
    raise SystemExit(gate.main())
