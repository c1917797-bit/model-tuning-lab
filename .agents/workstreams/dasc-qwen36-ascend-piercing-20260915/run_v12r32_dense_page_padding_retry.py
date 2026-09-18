#!/usr/bin/env python3
"""Retry v12r31 with a fail-closed DIAS containerd-task race guard."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r31_trial",
    HERE / "run_v12r31_dense_page_padding_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r31 dense-padding control")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-identity-retry-v12r32"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_identity_v12r32_20260918"
)


def parse_containerd_tasks(raw: str, *, namespace: str) -> list[dict]:
    rows = []
    for line in raw.splitlines():
        values = line.split()
        if len(values) < 3 or values[0] == "TASK":
            continue
        rows.append(
            {
                "namespace": namespace,
                "task": values[0],
                "pid": int(values[1]),
                "status": values[2],
            }
        )
    return rows


def running_dias_tasks() -> list[dict]:
    raw = controller.run(
        ["/usr/local/bin/ctr", "-n", "dias", "tasks", "list"],
        check=False,
        timeout=30,
    )
    return [
        row
        for row in parse_containerd_tasks(raw, namespace="dias")
        if row["status"] == "RUNNING"
    ]


_original_live_resource_state = controller.live_resource_state


def live_resource_state_with_dias_guard() -> tuple[dict, list[str]]:
    state, blockers = _original_live_resource_state()
    tasks = running_dias_tasks()
    state["running_dias_containerd_tasks"] = tasks
    if tasks:
        blockers.append(
            "running DIAS containerd tasks with independent NPU access: "
            + ", ".join(row["task"] for row in tasks)
        )
    return state, blockers


controller.live_resource_state = live_resource_state_with_dias_guard

_startup_globals = controller.wait_ready.__globals__
_original_startup_ownership = _startup_globals["validate_startup_ownership"]


def validate_startup_ownership_with_dias_guard() -> dict:
    result = _original_startup_ownership()
    tasks = running_dias_tasks()
    result["running_dias_containerd_tasks"] = tasks
    result["ok"] = result.get("ok") is True and not tasks
    controller.atomic_json(
        controller.RESULT / "startup-ownership-last.json", result
    )
    if tasks:
        controller.atomic_json(
            controller.RESULT / "startup-resource-race.json", result
        )
        raise RuntimeError(
            "not_run/resource_race during startup: running DIAS tasks="
            + ", ".join(row["task"] for row in tasks)
        )
    return result


_startup_globals[
    "validate_startup_ownership"
] = validate_startup_ownership_with_dias_guard


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
