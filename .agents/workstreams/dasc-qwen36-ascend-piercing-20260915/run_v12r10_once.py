#!/usr/bin/env python3
"""Paged-attention successor for the headDim=256 graph-capture boundary."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r9_trial", HERE / "run_v12r9_once.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r9 controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "request-owned-pa-head256-v12r10"
)
controller.CONTAINER = "dasc_qwen36_pa_head256_v12r10_20260916"
controller.ADDITIONAL_CONFIG = (
    '{"pa_shape_list":[1,2,4,8,16]}'
)


if __name__ == "__main__":
    raise SystemExit(trial.main())
