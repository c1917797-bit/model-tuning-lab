from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location(
    "mxr_gate_v11", HERE / "run_npu_gate_v11.py"
)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_v11_command_uses_only_physical_npu4():
    command = GATE.docker_command()
    joined = " ".join(command)
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert all(f"/dev/davinci{card}" not in joined for card in (5, 6, 7))
    assert "mxr_npu_probe_v11.py" in joined


def test_v11_identity_and_dependency_are_immutable():
    GATE.configure_gate()
    assert str(GATE.gate.RESULT).endswith("/npu-gate-v11")
    assert GATE.gate.CONTAINER == "mxr_qwen36_npu_gate_v11_20260920"
    assert len(GATE.V8_NUMERICAL_SHA256) == 64


def test_v11_is_candidate_only_and_covers_service_profile_length():
    text = (HERE / "mxr_npu_probe_v11.py").read_text(encoding="utf-8")
    assert 'CANDIDATES = ("pto_staged", "pto_mega")' in text
    assert "LENGTHS = (4096, 16384, 32768)" in text
    assert "v023_triton" not in text
