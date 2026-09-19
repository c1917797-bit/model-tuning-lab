from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("mxr_gate_v3", HERE / "run_npu_gate_v3.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_parse_uda_claims_distinguishes_free_and_owned_devices():
    text = """udevid 4 type(davinci entity near real)
        has os device

udevid 5 type(davinci entity near real)
        has os device
        has used by container, ns id 17
"""
    assert GATE.parse_uda_claims(text) == {5: 17}


def test_v3_command_maps_only_physical_npu4_and_uses_same_container_probe():
    joined = " ".join(GATE.docker_command())
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert "/dev/davinci5" not in joined
    assert "/dev/davinci6" not in joined
    assert "/dev/davinci7" not in joined
    assert "ASCEND_RT_VISIBLE_DEVICES=0" in joined
    assert "ASCEND_DEVICE_ID=0" in joined
    assert "mxr_npu_probe_v3.py" in joined
