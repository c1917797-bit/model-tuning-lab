#!/usr/bin/env python3
"""Run v12r35 while one exact wildcard container owns only NPU0-3.

The exception is deliberately narrower than a generic container allowlist.
The container identity, image, start time, and NPU-visible PID/device mapping
are frozen at preflight and monitored throughout the physical canary.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r35_trial",
    HERE / "run_v12r35_npu4_7_dense_page_padding_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r35 target-lane control")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-npu4-7-active-nontarget-v12r36"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_npu4_7_v12r36_20260918"
)

ACTIVE_NONTARGET_NAME = "combine-only-ep4_nk"
ACTIVE_NONTARGET_ID = (
    "15e12705d163911aedb992bb1edf17bd7044870459eeca0cb0bb1e0ad6d09e30"
)
ACTIVE_NONTARGET_IMAGE_ID = controller.IMAGE_ID
EXPECTED_NONTARGET_DEVICES = frozenset(set(range(8)) - set(controller.NPUS))

v12r34 = trial.trial
v12r33 = v12r34.trial
_original_run = controller.run
_expected_npu_identity: tuple[tuple[int, int], ...] | None = None
_expected_started_at: str | None = None
_guard_lock = threading.Lock()


def exact_container_snapshot() -> dict:
    raw = _original_run(
        ["/usr/bin/docker", "inspect", ACTIVE_NONTARGET_NAME],
        check=False,
        timeout=30,
    )
    try:
        item = json.loads(raw)[0]
    except (IndexError, TypeError, json.JSONDecodeError):
        return {
            "name": ACTIVE_NONTARGET_NAME,
            "expected_id": ACTIVE_NONTARGET_ID,
            "error": "container_absent_or_unreadable",
        }
    top = _original_run(
        ["/usr/bin/docker", "top", ACTIVE_NONTARGET_NAME, "-eo", "pid"],
        check=False,
        timeout=30,
    )
    host_pids = {
        int(line.strip())
        for line in top.splitlines()[1:]
        if line.strip().isdigit()
    }
    raw_npu = _original_run(
        ["/usr/local/bin/npu-smi", "info"], timeout=30
    )
    rows = controller.npu_process_rows(raw_npu)
    owned_rows = {
        device: sorted(pids.intersection(host_pids))
        for device, pids in rows.items()
        if pids.intersection(host_pids)
    }
    state = item.get("State") or {}
    host_config = item.get("HostConfig") or {}
    return {
        "name": str(item.get("Name") or "").lstrip("/"),
        "expected_id": ACTIVE_NONTARGET_ID,
        "actual_id": str(item.get("Id") or ""),
        "expected_image_id": ACTIVE_NONTARGET_IMAGE_ID,
        "actual_image_id": str(item.get("Image") or ""),
        "running": state.get("Running") is True,
        "paused": state.get("Paused") is True,
        "privileged": host_config.get("Privileged") is True,
        "started_at": str(state.get("StartedAt") or ""),
        "container_host_pids": sorted(host_pids),
        "owned_npu_processes": {
            str(device): pids for device, pids in sorted(owned_rows.items())
        },
        "npu_identity": sorted(
            (device, pid) for device, pids in owned_rows.items() for pid in pids
        ),
    }


def active_nontarget_verdict(
    snapshot: dict,
    expected_identity: tuple[tuple[int, int], ...] | None,
    expected_started_at: str | None,
) -> dict:
    identity = tuple(tuple(row) for row in snapshot.get("npu_identity") or [])
    devices = {device for device, _pid in identity}
    target_rows = [list(row) for row in identity if row[0] in controller.NPUS]
    checks = {
        "exact_container_identity": (
            snapshot.get("name") == ACTIVE_NONTARGET_NAME
            and snapshot.get("actual_id") == ACTIVE_NONTARGET_ID
        ),
        "exact_image_identity": (
            snapshot.get("actual_image_id") == ACTIVE_NONTARGET_IMAGE_ID
        ),
        "running_unpaused_privileged": (
            snapshot.get("running") is True
            and snapshot.get("paused") is False
            and snapshot.get("privileged") is True
        ),
        "all_nontarget_devices_owned": devices == EXPECTED_NONTARGET_DEVICES,
        "no_target_npu_process": not target_rows,
        "npu_process_identity_stable": (
            expected_identity is None or identity == expected_identity
        ),
        "container_start_time_stable": (
            expected_started_at is None
            or snapshot.get("started_at") == expected_started_at
        ),
    }
    return {
        "schema": "mst.dasc.active-nontarget-container/v1",
        **snapshot,
        "physical_target_npus": list(controller.NPUS),
        "expected_nontarget_devices": sorted(EXPECTED_NONTARGET_DEVICES),
        "expected_npu_identity": (
            None
            if expected_identity is None
            else [list(row) for row in expected_identity]
        ),
        "expected_started_at": expected_started_at,
        "target_npu_processes": target_rows,
        "checks": checks,
        "ok": all(checks.values()),
    }


def current_active_nontarget(*, establish: bool = False) -> dict:
    global _expected_npu_identity, _expected_started_at
    snapshot = exact_container_snapshot()
    with _guard_lock:
        if establish and _expected_npu_identity is None:
            candidate = active_nontarget_verdict(snapshot, None, None)
            if candidate["ok"]:
                _expected_npu_identity = tuple(
                    tuple(row) for row in snapshot["npu_identity"]
                )
                _expected_started_at = snapshot["started_at"]
        expected_identity = _expected_npu_identity
        expected_started_at = _expected_started_at
    return active_nontarget_verdict(
        snapshot, expected_identity, expected_started_at
    )


def record_resource_race(phase: str, payload: dict) -> None:
    if controller.RESULT.is_dir():
        controller.atomic_json(
            controller.RESULT / "active-nontarget-resource-race.json",
            {
                "schema": "mst.dasc.active-nontarget-resource-race/v1",
                "phase": phase,
                **payload,
            },
        )


def require_active_nontarget(phase: str, *, establish: bool = False) -> dict:
    state = current_active_nontarget(establish=establish)
    if not state["ok"]:
        record_resource_race(phase, {"active_nontarget_container": state})
        raise RuntimeError(
            "not_run/resource_race: exact active non-target container "
            f"guard failed during {phase}"
        )
    return state


# v12r21's generic wildcard guard still owns startup validation. Extend its
# name set only after v12r33 has enforced its exact Maxon configuration, then
# add the stronger identity/PID/device guard below.
_startup_globals = controller.wait_ready.__globals__
_original_authorized_names = _startup_globals[
    "authorized_idle_unknown_scope_names"
]


def authorized_unknown_scope_names() -> set[str]:
    return set(_original_authorized_names()) | {ACTIVE_NONTARGET_NAME}


_startup_globals[
    "authorized_idle_unknown_scope_names"
] = authorized_unknown_scope_names

_v12r35_live_resource_state = controller.live_resource_state


def live_resource_state_with_active_nontarget() -> tuple[dict, list[str]]:
    state, blockers = _v12r35_live_resource_state()
    coexistence = current_active_nontarget(establish=True)
    state["authorized_active_nontarget_unknown_scope"] = coexistence
    if not coexistence["ok"]:
        blockers.append(
            "exact active non-target wildcard container guard failed"
        )
    return state, blockers


controller.live_resource_state = live_resource_state_with_active_nontarget

_v12r35_startup_ownership = _startup_globals["validate_startup_ownership"]


def validate_startup_ownership_with_active_nontarget() -> dict:
    before = require_active_nontarget("startup_before_ownership")
    result = _v12r35_startup_ownership()
    after = require_active_nontarget("startup_after_ownership")
    result["active_nontarget_container_before"] = before
    result["active_nontarget_container"] = after
    controller.atomic_json(
        controller.RESULT / "startup-ownership-last.json", result
    )
    return result


_startup_globals[
    "validate_startup_ownership"
] = validate_startup_ownership_with_active_nontarget

_v12r35_post_readiness = controller.validate_post_readiness_ownership


def validate_post_readiness_with_active_nontarget() -> dict:
    before = require_active_nontarget("post_readiness_before_ownership")
    result = _v12r35_post_readiness()
    after = require_active_nontarget("post_readiness_after_ownership")
    result["active_nontarget_container_before"] = before
    result["active_nontarget_container"] = after
    controller.atomic_json(
        controller.RESULT / "post-readiness-ownership.json", result
    )
    return result


controller.validate_post_readiness_ownership = (
    validate_post_readiness_with_active_nontarget
)

_v12r35_run = controller.run


def monitor_active_nontarget(
    stop: threading.Event, violation: list[dict]
) -> None:
    while not stop.wait(0.5):
        try:
            state = current_active_nontarget()
            if state["ok"]:
                continue
            payload = {"active_nontarget_container": state}
        except BaseException as error:
            payload = {
                "monitor_error": repr(error),
                "monitor_error_type": type(error).__name__,
            }
        violation.append(payload)
        record_resource_race("physical_canary", payload)
        _original_run(
            [
                "/usr/bin/docker",
                "stop",
                "--time",
                "1",
                controller.CONTAINER,
            ],
            check=False,
            timeout=10,
        )
        return


def run_with_active_nontarget_guard(
    args: list[str], *positional, **keywords
) -> str:
    if not v12r33.is_physical_canary_command(args):
        return _v12r35_run(args, *positional, **keywords)
    require_active_nontarget("before_physical_canary")
    stop = threading.Event()
    violation: list[dict] = []
    monitor = threading.Thread(
        target=monitor_active_nontarget,
        args=(stop, violation),
        name="dasc-v12r36-active-nontarget-monitor",
        daemon=True,
    )
    monitor.start()
    result = None
    error: BaseException | None = None
    try:
        result = _v12r35_run(args, *positional, **keywords)
    except BaseException as caught:
        error = caught
    finally:
        stop.set()
        monitor.join(timeout=5)
    final_state = current_active_nontarget()
    if violation or not final_state["ok"]:
        payload = {
            "active_nontarget_container": final_state,
            "monitor_violations": violation,
        }
        record_resource_race("after_physical_canary", payload)
        raise RuntimeError(
            "not_run/resource_race: active non-target container changed "
            "during physical canary"
        ) from error
    if error is not None:
        raise error
    return result


controller.run = run_with_active_nontarget_guard


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
