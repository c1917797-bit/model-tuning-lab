#!/usr/bin/env python3
"""Run the v12r26 state-row treatment in eager mode as a graph-boundary control."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r26_trial",
    HERE / "run_v12r26_idle_scope_guard_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r26 idle-scope controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "state-index-eager-boundary-v12r27"
)
controller.CONTAINER = (
    "dasc_qwen36_state_index_eager_boundary_v12r27_20260918"
)
controller.ENFORCE_EAGER = True


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
