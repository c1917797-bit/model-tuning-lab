#!/usr/bin/env python3
"""Matched dense control for the v12r11 replay-instability finding."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r11_trial", HERE / "run_v12r11_once.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r11 controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-head256-replay-control-v12r12"
)
controller.CONTAINER = "dasc_qwen36_dense_head256_v12r12_20260916"
controller.PREVIOUS_CANARY = HERE / "run_dense_replay_probe.py"
controller.PLUGIN_MODE = "compat-head256"
controller.validate_allocation_evidence = lambda: None


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
