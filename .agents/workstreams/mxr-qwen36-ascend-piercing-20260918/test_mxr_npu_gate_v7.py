from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("mxr_gate_v7", HERE / "run_npu_gate_v7.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_v7_command_uses_platform_order_probe():
    joined = " ".join(GATE.docker_command())
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert "/dev/davinci5" not in joined
    assert "ASCEND_DEVICE_ID=0" in joined
    assert "mxr_npu_probe_v7.py" in joined


def test_v7_immutable_identity():
    SPEC.loader.exec_module(GATE)
    assert str(GATE.gate.RESULT).endswith("/npu-gate-v7")
    assert GATE.gate.CONTAINER == "mxr_qwen36_npu_gate_v7_20260919"
