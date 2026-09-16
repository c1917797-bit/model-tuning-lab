#!/usr/bin/env python3
"""Head-256 chunked-prefill fallback successor; software checks are not NPU proof."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r10_trial", HERE / "run_v12r10_once.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r10 controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "request-owned-head256-prefill-v12r11"
)
controller.CONTAINER = "dasc_qwen36_head256_prefill_v12r11_20260916"


if __name__ == "__main__":
    raise SystemExit(trial.main())
