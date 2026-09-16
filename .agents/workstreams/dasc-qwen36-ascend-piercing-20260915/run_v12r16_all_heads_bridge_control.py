#!/usr/bin/env python3
"""All-head bridge control with commit-pinned current canary source."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r15_trial", HERE / "run_v12r15_all_heads_bridge_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r15 all-heads controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "request-owned-all-heads-current-canary-v12r16"
)
controller.CONTAINER = "dasc_qwen36_all_heads_current_v12r16_20260916"


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
