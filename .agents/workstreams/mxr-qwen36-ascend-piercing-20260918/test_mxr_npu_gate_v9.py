from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("mxr_gate_v9", HERE / "run_npu_gate_v9.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_v9_command_is_correctness_only_and_npu4_only():
    command = GATE.docker_command()
    joined = " ".join(command)
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert all(f"/dev/davinci{card}" not in joined for card in (5, 6, 7))
    assert "mxr_npu_probe_v9.py" in joined
    assert command[command.index("--phase") + 1] == "correctness"


def test_v9_configuration_and_identity():
    SPEC.loader.exec_module(GATE)
    GATE.configure_gate()
    assert str(GATE.gate.RESULT).endswith("/npu-gate-v9")
    assert GATE.gate.CONTAINER == "mxr_qwen36_npu_gate_v9_20260919"
    assert GATE.gate.preflight is GATE.previous.previous.preflight


def test_v9_probe_has_evidence_based_state_adapter():
    text = (HERE / "mxr_npu_probe_v9.py").read_text(encoding="utf-8")
    assert "state.to(torch.bfloat16)" in text
    assert '"baseline_state_dtype": "bfloat16"' in text
