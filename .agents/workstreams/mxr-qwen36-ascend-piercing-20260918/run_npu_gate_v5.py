#!/usr/bin/env python3
"""Immutable v5 MXR gate after completing v0.23 worker initialization."""
from pathlib import Path

import run_npu_gate_v4 as previous


gate = previous.gate
BASE_DOCKER_COMMAND = previous.docker_command

gate.RESULT = Path("/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v5")
gate.CONTAINER = "mxr_qwen36_npu_gate_v5_20260919"


def docker_command() -> list[str]:
    command = BASE_DOCKER_COMMAND()
    old_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe_v4.py"
    )
    new_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe_v5.py"
    )
    command[command.index(old_probe)] = new_probe
    return command


def configure_gate() -> None:
    gate.preflight = previous.preflight
    gate.docker_command = docker_command
    gate.monitor = previous.monitor


if __name__ == "__main__":
    configure_gate()
    raise SystemExit(gate.main())
