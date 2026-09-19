#!/usr/bin/env python3
"""Second immutable MXR NPU gate after the UDA owner was released.

The controller logic remains frozen in run_npu_gate_v1. This entry point
changes only the result root and disposable container name so the failed first
attempt can never be overwritten.
"""
from pathlib import Path

import run_npu_gate_v1 as gate


gate.RESULT = Path("/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v2")
gate.CONTAINER = "mxr_qwen36_npu_gate_v2_20260919"


if __name__ == "__main__":
    raise SystemExit(gate.main())
