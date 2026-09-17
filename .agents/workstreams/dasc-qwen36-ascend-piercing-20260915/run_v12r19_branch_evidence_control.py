#!/usr/bin/env python3
"""All-head control with bounded scheduler and Mamba branch evidence."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r18_trial", HERE / "run_v12r18_mixed_lifecycle_fix_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r18 lifecycle controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "branch-evidence-all-heads-v12r19"
)
controller.CONTAINER = "dasc_qwen36_branch_evidence_v12r19_20260917"
controller.PLUGIN_MODE = "physical-cache-native-all-heads"


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
