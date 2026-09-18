#!/usr/bin/env python3
"""Retry v12r38 with an exact idle-or-full non-target container guard."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r38_trial",
    HERE / "run_v12r38_padded_attention_reshape_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r38 reshape control")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "padded-attention-reshape-idle-nontarget-npu4-7-v12r39"
)
controller.CONTAINER = (
    "dasc_qwen36_padded_attention_reshape_idle_nontarget_"
    "npu4_7_v12r39_20260918"
)

# v12r38 -> v12r37 -> v12r36.  Keep v12r36's continuous identity,
# start-time, image, target-lane, and physical-canary monitoring, but accept
# the exact known container in either of two coherent states: no NPU process,
# or complete ownership of every non-target NPU.  A partial TP group remains
# a fail-closed resource race.
v12r36 = trial.trial.trial


def idle_or_full_nontarget_verdict(
    snapshot: dict,
    expected_identity: tuple[tuple[int, int], ...] | None,
    expected_started_at: str | None,
) -> dict:
    expected_nontarget_devices = frozenset(
        set(range(8)) - set(controller.NPUS)
    )
    identity = tuple(
        tuple(row) for row in snapshot.get("npu_identity") or []
    )
    devices = {device for device, _pid in identity}
    target_rows = [
        list(row) for row in identity if row[0] in controller.NPUS
    ]
    if not identity:
        device_state = "idle"
    elif devices == expected_nontarget_devices:
        device_state = "full_nontarget"
    else:
        device_state = "unsupported_partial"
    checks = {
        "exact_container_identity": (
            snapshot.get("name") == v12r36.ACTIVE_NONTARGET_NAME
            and snapshot.get("actual_id") == v12r36.ACTIVE_NONTARGET_ID
        ),
        "exact_image_identity": (
            snapshot.get("actual_image_id")
            == v12r36.ACTIVE_NONTARGET_IMAGE_ID
        ),
        "running_unpaused_privileged": (
            snapshot.get("running") is True
            and snapshot.get("paused") is False
            and snapshot.get("privileged") is True
        ),
        "idle_or_full_nontarget_state": device_state in {
            "idle",
            "full_nontarget",
        },
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
        "schema": "mst.dasc.known-nontarget-container/v2",
        **snapshot,
        "physical_target_npus": list(controller.NPUS),
        "expected_nontarget_devices": sorted(expected_nontarget_devices),
        "nontarget_device_state": device_state,
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


v12r36.active_nontarget_verdict = idle_or_full_nontarget_verdict


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
