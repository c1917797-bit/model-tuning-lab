from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("mxr_gate_v10", HERE / "run_npu_gate_v10.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_v10_command_is_all_phase_and_npu4_only():
    command = GATE.docker_command()
    joined = " ".join(command)
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert all(f"/dev/davinci{card}" not in joined for card in (5, 6, 7))
    assert "mxr_npu_probe_v10.py" in joined
    assert command[command.index("--phase") + 1] == "all"


def test_v10_configuration_and_identity():
    GATE.configure_gate()
    assert str(GATE.gate.RESULT).endswith("/npu-gate-v10")
    assert GATE.gate.CONTAINER == "mxr_qwen36_npu_gate_v10_20260919"
    assert GATE.gate.preflight is GATE.previous.previous.preflight


def test_v10_keeps_correctness_before_timing():
    text = (HERE / "mxr_npu_probe_v10.py").read_text(encoding="utf-8")
    numerical = text.index("numerical = triangular_correctness")
    guard = text.index('if not numerical["ok"]')
    timing = text.index("timing = triangular_timing")
    assert numerical < guard < timing
