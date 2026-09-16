#!/usr/bin/env python3
"""Exact-prompt dense prefix-hit control for the v12r11 DASC failure."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r12_dense", HERE / "run_v12r12_dense_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r12 dense controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-exact-prefix-control-v12r13"
)
controller.CONTAINER = "dasc_qwen36_dense_exact_prefix_v12r13_20260916"


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
