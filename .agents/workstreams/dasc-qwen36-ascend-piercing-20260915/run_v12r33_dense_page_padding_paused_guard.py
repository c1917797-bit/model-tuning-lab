#!/usr/bin/env python3
"""Retry dense-padding control while pinning one foreign wildcard container paused."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import threading


HERE = Path(__file__).resolve().parent
PAUSED_CONTAINER_NAME = "Maxon4ick_torch_910_dev"
PAUSED_CONTAINER_ID = (
    "321c36f70aac15f2d7be81baba9fdd08ebfa61c0bd1baf4b45e66a417c368ce3"
)

configured = {
    value.strip().lstrip("/")
    for value in os.environ.get("MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE", "").split(",")
    if value.strip()
}
if configured not in (set(), {PAUSED_CONTAINER_NAME}):
    raise RuntimeError(
        "v12r33 accepts exactly one paused unknown-scope container: "
        + PAUSED_CONTAINER_NAME
    )
os.environ["MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE"] = PAUSED_CONTAINER_NAME

spec = importlib.util.spec_from_file_location(
    "dasc_v12r32_trial",
    HERE / "run_v12r32_dense_page_padding_retry.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r32 dense-padding retry")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-paused-guard-v12r33"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_paused_guard_v12r33_20260918"
)

_original_run = controller.run


def paused_container_state() -> dict:
    raw = _original_run(
        ["/usr/bin/docker", "inspect", PAUSED_CONTAINER_NAME],
        check=False,
        timeout=30,
    )
    try:
        item = json.loads(raw)[0]
    except (IndexError, TypeError, json.JSONDecodeError):
        return {
            "ok": False,
            "name": PAUSED_CONTAINER_NAME,
            "expected_id": PAUSED_CONTAINER_ID,
            "error": "container_absent_or_unreadable",
        }
    state = item.get("State") or {}
    host_config = item.get("HostConfig") or {}
    actual_id = str(item.get("Id") or "")
    result = {
        "name": str(item.get("Name") or "").lstrip("/"),
        "expected_id": PAUSED_CONTAINER_ID,
        "actual_id": actual_id,
        "running": state.get("Running") is True,
        "paused": state.get("Paused") is True,
        "privileged": host_config.get("Privileged") is True,
        "started_at": state.get("StartedAt"),
    }
    result["ok"] = (
        result["name"] == PAUSED_CONTAINER_NAME
        and actual_id == PAUSED_CONTAINER_ID
        and result["running"]
        and result["paused"]
        and result["privileged"]
    )
    return result


def record_paused_race(phase: str, state: dict) -> None:
    if controller.RESULT.is_dir():
        controller.atomic_json(
            controller.RESULT / "paused-container-resource-race.json",
            {
                "schema": "mst.dasc.paused-container-race/v1",
                "phase": phase,
                "container": state,
            },
        )


def require_paused_container(phase: str) -> dict:
    state = paused_container_state()
    if not state.get("ok"):
        record_paused_race(phase, state)
        raise RuntimeError(
            "not_run/resource_race: exact wildcard container is not "
            f"continuously paused during {phase}"
        )
    return state


_original_live_resource_state = controller.live_resource_state


def live_resource_state_with_paused_guard() -> tuple[dict, list[str]]:
    state, blockers = _original_live_resource_state()
    paused = paused_container_state()
    state["paused_unknown_scope_container"] = paused
    if not paused.get("ok"):
        blockers.append(
            "exact wildcard container is not running paused with expected identity"
        )
    return state, blockers


controller.live_resource_state = live_resource_state_with_paused_guard

_startup_globals = controller.wait_ready.__globals__
_original_startup_ownership = _startup_globals["validate_startup_ownership"]


def validate_startup_ownership_with_paused_guard() -> dict:
    paused = require_paused_container("startup")
    result = _original_startup_ownership()
    result["paused_unknown_scope_container"] = paused
    controller.atomic_json(
        controller.RESULT / "startup-ownership-last.json", result
    )
    return result


_startup_globals[
    "validate_startup_ownership"
] = validate_startup_ownership_with_paused_guard

_original_post_readiness = controller.validate_post_readiness_ownership


def validate_post_readiness_with_paused_guard() -> dict:
    paused = require_paused_container("post_readiness")
    result = _original_post_readiness()
    if result is None:
        evidence_path = controller.RESULT / "post-readiness-ownership.json"
        if not evidence_path.is_file():
            raise RuntimeError(
                "post-readiness ownership validator returned no result "
                "and wrote no evidence"
            )
        result = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise TypeError(
            "post-readiness ownership validator must return a mapping "
            "or write post-readiness-ownership.json"
        )
    result["paused_unknown_scope_container"] = paused
    controller.atomic_json(
        controller.RESULT / "post-readiness-ownership.json", result
    )
    return result


controller.validate_post_readiness_ownership = (
    validate_post_readiness_with_paused_guard
)


def is_physical_canary_command(args: list[str]) -> bool:
    return (
        len(args) >= 2
        and args[0] == "/usr/bin/python3"
        and Path(args[1]).name == "run_physical_canary.py"
    )


def monitor_paused_container(
    stop: threading.Event, violation: list[dict]
) -> None:
    while not stop.wait(0.5):
        state = paused_container_state()
        if state.get("ok"):
            continue
        violation.append(state)
        record_paused_race("physical_canary", state)
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


def run_with_paused_canary_guard(
    args: list[str], *positional, **keywords
) -> str:
    if not is_physical_canary_command(args):
        return _original_run(args, *positional, **keywords)
    require_paused_container("before_physical_canary")
    stop = threading.Event()
    violation: list[dict] = []
    monitor = threading.Thread(
        target=monitor_paused_container,
        args=(stop, violation),
        name="dasc-v12r33-paused-container-monitor",
        daemon=True,
    )
    monitor.start()
    result = None
    error: BaseException | None = None
    try:
        result = _original_run(args, *positional, **keywords)
    except BaseException as caught:
        error = caught
    finally:
        stop.set()
        monitor.join(timeout=5)
    final_state = paused_container_state()
    if violation or not final_state.get("ok"):
        record_paused_race("after_physical_canary", final_state)
        raise RuntimeError(
            "not_run/resource_race: paused wildcard container changed "
            "state during physical canary"
        ) from error
    if error is not None:
        raise error
    return result


controller.run = run_with_paused_canary_guard


def restore_foreign_container() -> dict:
    state = paused_container_state()
    restored = False
    if (
        state.get("actual_id") == PAUSED_CONTAINER_ID
        and state.get("running")
        and state.get("paused")
    ):
        _original_run(
            ["/usr/bin/docker", "unpause", PAUSED_CONTAINER_NAME],
            check=False,
            timeout=30,
        )
        restored = True
    result = {"before_restore": state, "unpause_requested": restored}
    if controller.RESULT.is_dir():
        controller.atomic_json(
            controller.RESULT / "paused-container-restoration.json", result
        )
    return result


def main() -> int:
    try:
        return trial.main()
    finally:
        restore_foreign_container()


if __name__ == "__main__":
    raise SystemExit(main())
