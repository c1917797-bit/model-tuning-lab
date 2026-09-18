#!/usr/bin/env python3
"""v12r21 startup guard plus GDN kernel-to-manager block normalization."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r21_trial",
    HERE / "run_v12r21_startup_guard_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r21 startup-guard controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "kernel-block-normalization-v12r22"
)
controller.CONTAINER = "dasc_qwen36_kernel_normalization_v12r22_20260918"


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
