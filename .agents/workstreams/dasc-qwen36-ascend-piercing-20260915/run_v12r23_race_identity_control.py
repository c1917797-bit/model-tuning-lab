#!/usr/bin/env python3
"""v12r22 numerical trial with fail-closed foreign-PID identity capture."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r22_trial",
    HERE / "run_v12r22_kernel_block_normalization_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r22 normalization controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "kernel-block-normalization-race-guard-v12r23"
)
controller.CONTAINER = (
    "dasc_qwen36_kernel_normalization_v12r23_20260918"
)


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
