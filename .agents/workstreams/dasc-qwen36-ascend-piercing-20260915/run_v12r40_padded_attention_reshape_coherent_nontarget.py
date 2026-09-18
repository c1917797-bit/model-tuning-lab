#!/usr/bin/env python3
"""Retry v12r39 while allowing coherent non-target service transitions."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r39_trial",
    HERE / "run_v12r39_padded_attention_reshape_idle_nontarget.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r39 reshape control")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "padded-attention-reshape-coherent-nontarget-npu4-7-v12r40"
)
controller.CONTAINER = (
    "dasc_qwen36_padded_attention_reshape_coherent_nontarget_"
    "npu4_7_v12r40_20260918"
)
v12r36 = trial.v12r36


def coherent_nontarget_verdict(
    snapshot: dict,
    expected_identity: tuple[tuple[int, int], ...] | None,
    expected_started_at: str | None,
) -> dict:
    del expected_identity
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
        "coherent_nontarget_state": device_state in {
            "idle",
            "full_nontarget",
        },
        "no_target_npu_process": not target_rows,
        "container_start_time_stable": (
            expected_started_at is None
            or snapshot.get("started_at") == expected_started_at
        ),
    }
    return {
        "schema": "mst.dasc.known-nontarget-container/v3",
        **snapshot,
        "physical_target_npus": list(controller.NPUS),
        "expected_nontarget_devices": sorted(expected_nontarget_devices),
        "nontarget_device_state": device_state,
        "allowed_state_transitions": [
            "idle_to_full_nontarget",
            "full_nontarget_to_idle",
        ],
        "expected_npu_identity": "coherent_state_only",
        "expected_started_at": expected_started_at,
        "target_npu_processes": target_rows,
        "checks": checks,
        "ok": all(checks.values()),
    }


v12r36.active_nontarget_verdict = coherent_nontarget_verdict


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
