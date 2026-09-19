from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("mxr_gate_v4", HERE / "run_npu_gate_v4.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_v4_command_keeps_canary_and_probe_in_one_device_scoped_container():
    joined = " ".join(GATE.docker_command())
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert "/dev/davinci5" not in joined
    assert "/dev/davinci6" not in joined
    assert "/dev/davinci7" not in joined
    assert "ASCEND_DEVICE_ID=0" in joined
    assert "mxr_npu_probe_v4.py" in joined


def test_v4_uses_new_immutable_identity():
    assert str(GATE.gate.RESULT).endswith("/npu-gate-v4")
    assert GATE.gate.CONTAINER == "mxr_qwen36_npu_gate_v4_20260919"
