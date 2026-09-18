#!/usr/bin/env python3
"""v12r25 retry with a distinct evidence root for idle-scope coexistence."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r25_trial",
    HERE / "run_v12r25_ascend_block_scale_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r25 Ascend block-scale controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "ascend-block-scale-idle-scope-v12r26"
)
controller.CONTAINER = (
    "dasc_qwen36_ascend_block_scale_idle_scope_v12r26_20260918"
)


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
