#!/usr/bin/env python3
"""Run the unchanged v12r33 dense-padding control on physical NPU0-3.

The existing DIAS task may continue serving on physical NPU4-7. This narrow
coexistence exception is fail-closed: the exact DIAS task set must remain
stable, no DIAS process may appear on NPU0-3, and every process observed on
NPU0-3 after readiness must belong to the owned DASC container.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import threading


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r33_trial",
    HERE / "run_v12r33_dense_page_padding_paused_guard.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r33 paused-guard control")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.NPUS = (0, 1, 2, 3)
controller.LOCK = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/controllers/"
    "dasc-qwen36-npu0-3.lock"
)
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-npu0-3-coexist-v12r34"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_npu0_3_v12r34_20260918"
)

ALLOWED_DIAS_TASK_NAMES = frozenset({"dias-cont-1"})
RUNTIME_HBM_GROWTH_LIMIT_MIB = 4096

v12r32 = trial.trial
_original_running_dias_tasks = v12r32.running_dias_tasks
_expected_dias_identity: tuple[tuple[str, str, int, str], ...] | None = None
_post_readiness_hbm: dict[int, int] | None = None
_guard_lock = threading.Lock()


def dias_identity(tasks: list[dict]) -> tuple[tuple[str, str, int, str], ...]:
    return tuple(
        sorted(
            (
                str(row.get("namespace") or ""),
                str(row.get("task") or ""),
                int(row.get("pid") or 0),
                str(row.get("status") or ""),
            )
            for row in tasks
        )
    )


def pid_cgroup(pid: int) -> str:
    try:
        return (Path("/proc") / str(pid) / "cgroup").read_text(
            encoding="utf-8", errors="replace"
        )
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return ""


def dias_target_tasks(
    tasks: list[dict],
    rows: dict[int, set[int]],
    cgroups: dict[int, str],
) -> list[dict]:
    target_pids = {
        pid for device in controller.NPUS for pid in rows.get(device, set())
    }
    result = []
    for row in tasks:
        namespace = str(row.get("namespace") or "")
        task = str(row.get("task") or "")
        marker = f"/{namespace}/{task}"
        pids = sorted(
            pid for pid in target_pids if marker in cgroups.get(pid, "")
        )
        if pids:
            result.append({**row, "target_pids": pids})
    return result


def dias_coexistence_verdict(
    tasks: list[dict],
    rows: dict[int, set[int]],
    cgroups: dict[int, str],
    expected_identity: tuple[tuple[str, str, int, str], ...] | None,
) -> dict:
    identity = dias_identity(tasks)
    unexpected = sorted(
        {
            str(row.get("task") or "")
            for row in tasks
            if str(row.get("task") or "") not in ALLOWED_DIAS_TASK_NAMES
        }
    )
    target_tasks = dias_target_tasks(tasks, rows, cgroups)
    identity_stable = expected_identity is None or identity == expected_identity
    checks = {
        "only_authorized_task_names": not unexpected,
        "no_dias_process_on_target_npus": not target_tasks,
        "task_identity_stable": identity_stable,
    }
    return {
        "schema": "mst.dasc.dias-nontarget-coexistence/v1",
        "physical_npus": list(controller.NPUS),
        "allowed_task_names": sorted(ALLOWED_DIAS_TASK_NAMES),
        "tasks": tasks,
        "identity": [list(row) for row in identity],
        "expected_identity": (
            None
            if expected_identity is None
            else [list(row) for row in expected_identity]
        ),
        "unexpected_task_names": unexpected,
        "target_tasks": target_tasks,
        "checks": checks,
        "ok": all(checks.values()),
    }


def current_dias_coexistence(*, establish: bool = False) -> dict:
    global _expected_dias_identity
    tasks = _original_running_dias_tasks()
    raw = trial._original_run(
        ["/usr/local/bin/npu-smi", "info"], timeout=30
    )
    rows = controller.npu_process_rows(raw)
    target_pids = {
        pid for device in controller.NPUS for pid in rows.get(device, set())
    }
    cgroups = {pid: pid_cgroup(pid) for pid in target_pids}
    with _guard_lock:
        if establish and _expected_dias_identity is None:
            _expected_dias_identity = dias_identity(tasks)
        expected = _expected_dias_identity
    return dias_coexistence_verdict(tasks, rows, cgroups, expected)


def running_dias_tasks_on_target_npus() -> list[dict]:
    tasks = _original_running_dias_tasks()
    raw = trial._original_run(
        ["/usr/local/bin/npu-smi", "info"], timeout=30
    )
    rows = controller.npu_process_rows(raw)
    target_pids = {
        pid for device in controller.NPUS for pid in rows.get(device, set())
    }
    cgroups = {pid: pid_cgroup(pid) for pid in target_pids}
    return dias_target_tasks(tasks, rows, cgroups)


# Narrow v12r32's DIAS blocker to the target lane. The complete task inventory
# and stable-identity exception remain recorded; no target-card process is
# allowlisted.
v12r32.running_dias_tasks = running_dias_tasks_on_target_npus

_v12r33_live_resource_state = controller.live_resource_state


def live_resource_state_with_npu0_3_coexistence() -> tuple[dict, list[str]]:
    state, blockers = _v12r33_live_resource_state()
    coexistence = current_dias_coexistence(establish=True)
    state["dias_non_target_coexistence"] = coexistence
    if not coexistence["ok"]:
        blockers.append(
            "DIAS non-target coexistence guard failed: "
            + ", ".join(
                name
                for name, passed in coexistence["checks"].items()
                if not passed
            )
        )
    return state, blockers


controller.live_resource_state = live_resource_state_with_npu0_3_coexistence


def record_resource_race(phase: str, payload: dict) -> None:
    if controller.RESULT.is_dir():
        controller.atomic_json(
            controller.RESULT / "target-lane-resource-race.json",
            {
                "schema": "mst.dasc.target-lane-resource-race/v1",
                "phase": phase,
                **payload,
            },
        )


def require_dias_coexistence(phase: str) -> dict:
    state = current_dias_coexistence()
    if not state["ok"]:
        record_resource_race(phase, {"dias_non_target_coexistence": state})
        raise RuntimeError(
            "not_run/resource_race: DIAS non-target coexistence changed "
            f"during {phase}"
        )
    return state


_startup_globals = controller.wait_ready.__globals__
_v12r33_startup_ownership = _startup_globals["validate_startup_ownership"]


def validate_startup_ownership_with_npu0_3_guard() -> dict:
    before = require_dias_coexistence("startup_before_ownership")
    result = _v12r33_startup_ownership()
    after = require_dias_coexistence("startup_after_ownership")
    result["dias_non_target_coexistence_before"] = before
    result["dias_non_target_coexistence"] = after
    controller.atomic_json(
        controller.RESULT / "startup-ownership-last.json", result
    )
    return result


_startup_globals[
    "validate_startup_ownership"
] = validate_startup_ownership_with_npu0_3_guard


def target_runtime_verdict(
    rows: dict[int, set[int]],
    owned_pids: set[int],
    hbm: dict[int, int],
    baseline_hbm: dict[int, int] | None,
) -> dict:
    target_pids = {
        pid for device in controller.NPUS for pid in rows.get(device, set())
    }
    missing = [device for device in controller.NPUS if not rows.get(device)]
    foreign = sorted(target_pids.difference(owned_pids))
    growth = {}
    if baseline_hbm is not None:
        growth = {
            device: hbm.get(device, -1) - baseline_hbm.get(device, -1)
            for device in controller.NPUS
        }
    excessive_growth = sorted(
        device
        for device, delta in growth.items()
        if delta > RUNTIME_HBM_GROWTH_LIMIT_MIB
    )
    checks = {
        "owned_process_on_every_target": not missing,
        "no_foreign_target_process": not foreign,
        "runtime_hbm_growth_bounded": not excessive_growth,
    }
    return {
        "schema": "mst.dasc.target-lane-runtime-ownership/v1",
        "physical_npus": list(controller.NPUS),
        "npu_process_pids": {
            str(device): sorted(rows.get(device, set()))
            for device in controller.NPUS
        },
        "owned_container_host_pids": sorted(owned_pids),
        "missing_process_devices": missing,
        "foreign_process_pids": foreign,
        "hbm_mib": {
            str(device): hbm.get(device) for device in controller.NPUS
        },
        "baseline_hbm_mib": (
            None
            if baseline_hbm is None
            else {
                str(device): baseline_hbm.get(device)
                for device in controller.NPUS
            }
        ),
        "hbm_growth_mib": {
            str(device): delta for device, delta in growth.items()
        },
        "hbm_growth_limit_mib": RUNTIME_HBM_GROWTH_LIMIT_MIB,
        "excessive_hbm_growth_devices": excessive_growth,
        "checks": checks,
        "ok": all(checks.values()),
    }


def current_target_runtime() -> dict:
    raw, hbm, _ = controller.npu_snapshot()
    rows = controller.npu_process_rows(raw)
    owned = controller.container_host_pids()
    return target_runtime_verdict(rows, owned, hbm, _post_readiness_hbm)


_v12r33_post_readiness = controller.validate_post_readiness_ownership


def validate_post_readiness_with_npu0_3_guard() -> dict:
    global _post_readiness_hbm
    coexistence = require_dias_coexistence("post_readiness_before_ownership")
    result = _v12r33_post_readiness()
    raw, hbm, _ = controller.npu_snapshot()
    rows = controller.npu_process_rows(raw)
    owned = controller.container_host_pids()
    runtime = target_runtime_verdict(rows, owned, hbm, None)
    if not runtime["ok"]:
        record_resource_race(
            "post_readiness", {"target_runtime": runtime}
        )
        raise RuntimeError(
            "not_run/resource_race: target NPU ownership changed "
            "at post-readiness"
        )
    _post_readiness_hbm = {
        device: hbm[device] for device in controller.NPUS
    }
    runtime["baseline_hbm_mib"] = {
        str(device): _post_readiness_hbm[device]
        for device in controller.NPUS
    }
    result["dias_non_target_coexistence"] = coexistence
    result["npu0_3_runtime_ownership"] = runtime
    controller.atomic_json(
        controller.RESULT / "post-readiness-ownership.json", result
    )
    return result


controller.validate_post_readiness_ownership = (
    validate_post_readiness_with_npu0_3_guard
)

_v12r33_run = controller.run


def monitor_npu0_3(
    stop: threading.Event, violation: list[dict]
) -> None:
    while not stop.wait(0.5):
        try:
            coexistence = current_dias_coexistence()
            runtime = current_target_runtime()
            if coexistence["ok"] and runtime["ok"]:
                continue
            payload = {
                "dias_non_target_coexistence": coexistence,
                "target_runtime": runtime,
            }
        except BaseException as error:
            payload = {
                "monitor_error": repr(error),
                "monitor_error_type": type(error).__name__,
            }
        violation.append(payload)
        record_resource_race("physical_canary", payload)
        trial._original_run(
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


def run_with_npu0_3_guard(
    args: list[str], *positional, **keywords
) -> str:
    if not trial.is_physical_canary_command(args):
        return _v12r33_run(args, *positional, **keywords)
    require_dias_coexistence("before_physical_canary")
    initial_runtime = current_target_runtime()
    if not initial_runtime["ok"]:
        record_resource_race(
            "before_physical_canary",
            {"target_runtime": initial_runtime},
        )
        raise RuntimeError(
            "not_run/resource_race: target NPU ownership invalid "
            "before physical canary"
        )
    stop = threading.Event()
    violation: list[dict] = []
    monitor = threading.Thread(
        target=monitor_npu0_3,
        args=(stop, violation),
        name="dasc-target-lane-monitor",
        daemon=True,
    )
    monitor.start()
    result = None
    error: BaseException | None = None
    try:
        result = _v12r33_run(args, *positional, **keywords)
    except BaseException as caught:
        error = caught
    finally:
        stop.set()
        monitor.join(timeout=5)
    final_coexistence = current_dias_coexistence()
    final_runtime = current_target_runtime()
    if (
        violation
        or not final_coexistence["ok"]
        or not final_runtime["ok"]
    ):
        payload = {
            "dias_non_target_coexistence": final_coexistence,
            "target_runtime": final_runtime,
            "monitor_violations": violation,
        }
        record_resource_race("after_physical_canary", payload)
        raise RuntimeError(
            "not_run/resource_race: target NPU ownership changed "
            "during physical canary"
        ) from error
    if error is not None:
        raise error
    return result


controller.run = run_with_npu0_3_guard


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
