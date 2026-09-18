#!/usr/bin/env python3
"""Run the unchanged dense-padding control on currently idle NPU4-7."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r34_trial",
    HERE / "run_v12r34_npu0_3_dense_page_padding_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r34 target-lane guard")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.NPUS = (4, 5, 6, 7)
controller.LOCK = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/controllers/"
    "dasc-qwen36-npu4-7.lock"
)
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-npu4-7-coexist-v12r35"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_npu4_7_v12r35_20260918"
)


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
