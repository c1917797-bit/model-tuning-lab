#!/usr/bin/env python3
"""One-shot MXR gate with UDA admission and teardown-safe PID monitoring."""
from __future__ import annotations

from pathlib import Path
import re
import threading
import time

import run_npu_gate_v1 as gate


BASE_PREFLIGHT = gate.preflight
BASE_DOCKER_COMMAND = gate.docker_command
UDA_DEVICE = Path("/proc/uda/udevice")
UDA_HEADER_RE = re.compile(r"^udevid\s+(\d+)\b")
UDA_OWNER_RE = re.compile(r"has used by container, ns id\s+(\d+)")

gate.RESULT = Path("/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v4")
gate.CONTAINER = "mxr_qwen36_npu_gate_v4_20260919"


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
    base_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe.py"
    )
    new_probe = (
        "/workspace/model-tuning-lab/.agents/workstreams/"
        "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe_v4.py"
    )
    command[command.index(base_probe)] = new_probe
    return command


def container_running() -> bool:
    output = gate.run(
        ["/usr/bin/docker", "inspect", "-f", "{{.State.Running}}", gate.CONTAINER],
        check=False,
    )
    return output.strip() == "true"


def monitor(stop: threading.Event, violations: list[dict]) -> None:
    while not stop.wait(0.5):
        try:
            if not container_running():
                # Ignore the bounded launch/teardown interval. Admission and
                # the final snapshot independently cover those two edges.
                continue
            verdict = gate.ownership_verdict(gate.target_snapshot(), gate.container_pids())
            if not verdict["ok"]:
                # Recheck once so Docker task removal cannot turn a just-exited
                # owned PID into a false foreign-process violation.
                time.sleep(0.25)
                if not container_running():
                    continue
                verdict = gate.ownership_verdict(gate.target_snapshot(), gate.container_pids())
        except BaseException as error:
            verdict = {"ok": False, "error": repr(error), "error_type": type(error).__name__}
        if verdict["ok"]:
            continue
        violations.append(verdict)
        gate.atomic_json(gate.RESULT / "resource-race.json", verdict)
        gate.run(
            ["/usr/bin/docker", "stop", "--time", "1", gate.CONTAINER],
            check=False,
            timeout=10,
        )
        return


def configure_gate() -> None:
    gate.preflight = preflight
    gate.docker_command = docker_command
    gate.monitor = monitor


if __name__ == "__main__":
    configure_gate()
    raise SystemExit(gate.main())
