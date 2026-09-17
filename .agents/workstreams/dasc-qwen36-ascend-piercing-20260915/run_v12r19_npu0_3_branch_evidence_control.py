#!/usr/bin/env python3
"""NPU0-3 lane for the unchanged v12r19 branch-evidence candidate."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r19_trial", HERE / "run_v12r19_branch_evidence_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r19 branch-evidence controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.NPUS = (0, 1, 2, 3)
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "branch-evidence-all-heads-v12r19-npu0-3"
)
controller.CONTAINER = "dasc_qwen36_branch_evidence_v12r19_npu0_3_20260917"


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
