#!/usr/bin/env python3
"""Retry the v12r27 eager boundary control after a startup resource race."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r27_trial",
    HERE / "run_v12r27_eager_boundary_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r27 eager-boundary controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "state-index-eager-boundary-v12r28"
)
controller.CONTAINER = (
    "dasc_qwen36_state_index_eager_boundary_v12r28_20260918"
)


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
