#!/usr/bin/env python3
"""Run the v12r36 guarded control on the currently idle NPU0-3 lane."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r36_trial",
    HERE / "run_v12r36_npu4_7_active_nontarget_guard.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r36 active non-target guard")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.NPUS = (0, 1, 2, 3)
controller.LOCK = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/controllers/"
    "dasc-qwen36-npu0-3.lock"
)
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-npu0-3-active-nontarget-v12r37"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_npu0_3_v12r37_20260918"
)


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
