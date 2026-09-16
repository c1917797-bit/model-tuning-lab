#!/usr/bin/env python3
"""Native-cache all-head control: bypass the request-owned dense bridge."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r16_trial", HERE / "run_v12r16_all_heads_bridge_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r16 all-heads controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "native-all-heads-control-v12r17"
)
controller.CONTAINER = "dasc_qwen36_native_all_heads_v12r17_20260916"
controller.PLUGIN_MODE = "physical-cache-native-all-heads"


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
