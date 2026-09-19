#!/usr/bin/env python3
"""Race-hardened one-shot MXR gate after the verified UDA release.

This controller fails closed on host UDA procfs ownership and runs the real
tensor canary plus MXR probe in one physical-NPU4 container namespace.
"""
from __future__ import annotations

from pathlib import Path
import re

import run_npu_gate_v1 as gate


BASE_PREFLIGHT = gate.preflight
BASE_DOCKER_COMMAND = gate.docker_command
UDA_DEVICE = Path("/proc/uda/udevice")
UDA_HEADER_RE = re.compile(r"^udevid\s+(\d+)\b")
UDA_OWNER_RE = re.compile(r"has used by container, ns id\s+(\d+)")

gate.RESULT = Path("/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v3")
gate.CONTAINER = "mxr_qwen36_npu_gate_v3_20260919"


def parse_uda_claims(text: str) -> dict[int, int]:
    claims: dict[int, int] = {}
    current: int | None = None
    for line in text.splitlines():
        header = UDA_HEADER_RE.match(line)
        if header:
            current = int(header.group(1))
            continue
        owner = UDA_OWNER_RE.search(line)
        if current is not None and owner:
            claims[current] = int(owner.group(1))
    return claims


def preflight() -> dict:
    result = BASE_PREFLIGHT()
    try:
        text = UDA_DEVICE.read_text(encoding="utf-8")
        claims = parse_uda_claims(text)
        error = None
    except OSError as exception:
        claims = {}
        error = f"{type(exception).__name__}: {exception}"
    target_claims = {
        str(card): claims[card] for card in gate.PHYSICAL_NPUS if card in claims
    }
    result["uda"] = {
        "path": str(UDA_DEVICE),
        "all_container_claims": {str(card): ns_id for card, ns_id in sorted(claims.items())},
        "target_claims": target_claims,
        "read_error": error,
    }
    result["checks"]["uda_table_readable"] = error is None
    result["checks"]["uda_target_free"] = error is None and not target_claims
    result["ok"] = all(result["checks"].values())
    return result


def docker_command() -> list[str]:
    command = BASE_DOCKER_COMMAND()
    image_index = command.index(gate.IMAGE)
    command[image_index:image_index] = ["-e", "ASCEND_DEVICE_ID=0"]
    old_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe.py"
    )
    new_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe_v3.py"
    )
    command[command.index(old_probe)] = new_probe
    return command


def configure_gate() -> None:
    gate.preflight = preflight
    gate.docker_command = docker_command


if __name__ == "__main__":
    configure_gate()
    raise SystemExit(gate.main())
