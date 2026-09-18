#!/usr/bin/env python3
"""v12r20 state-row control with fail-closed startup ownership guards."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r20_trial", HERE / "run_v12r20_state_index_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r20 state-index controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "state-index-startup-guard-v12r21"
)
controller.CONTAINER = "dasc_qwen36_state_index_v12r21_20260917"

_original_live_resource_state = controller.live_resource_state


def authorized_idle_unknown_scope_names() -> set[str]:
    raw = os.environ.get("MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE", "")
    names = {
        value.strip().lstrip("/")
        for value in raw.split(",")
        if value.strip()
    }
    invalid = sorted(
        name
        for name in names
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) is None
    )
    if invalid:
        raise ValueError(
            "invalid idle unknown-scope container names: "
            + ", ".join(invalid)
        )
    return names


def unknown_device_scope_containers(
    items: list[dict], *, excluded_names: set[str] | None = None
) -> list[dict]:
    """Return running privileged containers whose physical NPU scope is unknown."""
    excluded_names = excluded_names or set()
    result = []
    for item in items:
        name = str(item.get("Name") or "").lstrip("/")
        if name in excluded_names:
            continue
        host_config = item.get("HostConfig") or {}
        state = item.get("State") or {}
        if state.get("Running") is not True or host_config.get("Privileged") is not True:
            continue
        mapped = {
            int(match.group(1))
            for device in host_config.get("Devices") or []
            if (
                match := re.fullmatch(
                    r"/dev/davinci([0-7])", device.get("PathOnHost", "")
                )
            )
        }
        visible_prefix = "ASCEND_RT_VISIBLE_DEVICES="
        visible = next(
            (
                value[len(visible_prefix) :]
                for value in (item.get("Config") or {}).get("Env") or []
                if value.startswith(visible_prefix)
            ),
            None,
        )
        declared = {
            int(value.strip())
            for value in (visible or "").split(",")
            if re.fullmatch(r"[0-7]", value.strip())
        }
        if mapped or declared:
            continue
        result.append(
            {
                "name": name,
                "id": item.get("Id"),
                "image": (item.get("Config") or {}).get("Image"),
                "started_at": state.get("StartedAt"),
                "classification": "unknown_device_scope",
                "claim": "wildcard_npu_contender",
            }
        )
    return sorted(result, key=lambda row: (row["name"], str(row["id"])))


def running_container_inspects() -> list[dict]:
    ids = controller.run(["/usr/bin/docker", "ps", "-q"], timeout=30).split()
    return [
        json.loads(
            controller.run(
                ["/usr/bin/docker", "inspect", container_id], timeout=30
            )
        )[0]
        for container_id in ids
    ]


def guarded_live_resource_state() -> tuple[dict, list[str]]:
    state, blockers = _original_live_resource_state()
    unknown = unknown_device_scope_containers(running_container_inspects())
    authorized_names = authorized_idle_unknown_scope_names()
    authorized = [
        row for row in unknown if row["name"] in authorized_names
    ]
    unexpected = [
        row for row in unknown if row["name"] not in authorized_names
    ]
    state["unknown_device_scope_containers"] = unknown
    state["authorized_idle_unknown_scope_containers"] = authorized
    state["unexpected_unknown_device_scope_containers"] = unexpected
    state["unknown_device_scope_policy"] = (
        "exact_name_idle_coexistence_with_pid_guard"
        if authorized
        else "block_as_wildcard_npu_contender"
    )
    if unexpected:
        blockers.append(
            "running privileged containers with unknown device scope: "
            + ", ".join(row["name"] for row in unexpected)
        )
    return state, blockers


def startup_ownership_verdict(
    rows: dict[int, set[int]],
    owned_pids: set[int],
    unknown_scope: list[dict],
    authorized_unknown_names: set[str] | None = None,
) -> dict:
    authorized_unknown_names = authorized_unknown_names or set()
    target_pids = {
        pid for device in controller.NPUS for pid in rows.get(device, set())
    }
    foreign = sorted(target_pids.difference(owned_pids))
    authorized_unknown = [
        row
        for row in unknown_scope
        if row["name"] in authorized_unknown_names
    ]
    unexpected_unknown = [
        row
        for row in unknown_scope
        if row["name"] not in authorized_unknown_names
    ]
    return {
        "schema": "mst.dasc.startup-ownership/v1",
        "physical_npus": list(controller.NPUS),
        "npu_process_pids": {
            str(device): sorted(rows.get(device, set()))
            for device in controller.NPUS
        },
        "owned_container_host_pids": sorted(owned_pids),
        "foreign_process_pids": foreign,
        "unknown_device_scope_containers": unknown_scope,
        "authorized_idle_unknown_scope_containers": authorized_unknown,
        "unexpected_unknown_device_scope_containers": unexpected_unknown,
        "ok": not foreign and not unexpected_unknown,
    }


def process_identity(pid: int) -> dict:
    root = Path("/proc") / str(pid)
    result = {"pid": pid}
    try:
        status = {}
        for line in (root / "status").read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                if key in {"Name", "Pid", "PPid", "NSpid", "Uid"}:
                    status[key.lower()] = value.strip()
        result["status"] = status
        result["cmdline"] = (
            (root / "cmdline")
            .read_bytes()
            .replace(b"\0", b" ")
            .decode("utf-8", errors="replace")
            .strip()
        )
        result["cgroup"] = (root / "cgroup").read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
        result["exe"] = str((root / "exe").resolve())
    except (FileNotFoundError, ProcessLookupError):
        result["vanished_before_identity_capture"] = True
    except PermissionError as error:
        result["identity_error"] = repr(error)
    return result


def validate_startup_ownership() -> dict:
    raw = controller.run(["/usr/local/bin/npu-smi", "info"], timeout=30)
    rows = controller.npu_process_rows(raw)
    owned = controller.container_host_pids()
    unknown = unknown_device_scope_containers(
        running_container_inspects(),
        excluded_names={controller.CONTAINER},
    )
    result = startup_ownership_verdict(
        rows,
        owned,
        unknown,
        authorized_idle_unknown_scope_names(),
    )
    result["foreign_process_details"] = [
        process_identity(pid)
        for pid in result["foreign_process_pids"]
    ]
    controller.atomic_json(
        controller.RESULT / "startup-ownership-last.json", result
    )
    if not result["ok"]:
        controller.atomic_json(
            controller.RESULT / "startup-resource-race.json", result
        )
        names = [
            row["name"]
            for row in result[
                "unexpected_unknown_device_scope_containers"
            ]
        ]
        raise RuntimeError(
            "not_run/resource_race during startup: "
            f"foreign_pids={result['foreign_process_pids']} "
            f"unknown_scope_containers={names}"
        )
    return result


def guarded_wait_ready() -> None:
    for attempt in range(1, 361):
        state = controller.run(
            [
                "/usr/bin/docker",
                "inspect",
                "--format",
                "{{.State.Running}}",
                controller.CONTAINER,
            ]
        ).strip()
        if state != "true":
            raise RuntimeError("service container exited before readiness")
        validate_startup_ownership()
        ready = False
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{controller.PORT}/v1/models", timeout=5
            ) as response:
                ready = response.status == 200
        except Exception:
            pass
        if ready:
            validate_startup_ownership()
            return
        recent_logs = controller.run(
            [
                "/usr/bin/docker",
                "logs",
                "--tail",
                "200",
                controller.CONTAINER,
            ],
            check=False,
            timeout=30,
        )
        if (
            "EngineCore failed" in recent_logs
            or "NPUModelRunner init failed" in recent_logs
        ):
            validate_startup_ownership()
            raise RuntimeError("service reported a fatal initialization failure")
        if attempt % 6 == 0:
            print(f"waiting for readiness attempt={attempt}/360", flush=True)
        time.sleep(10)
    raise TimeoutError("service did not become ready")


controller.live_resource_state = guarded_live_resource_state
controller.wait_ready = guarded_wait_ready


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
