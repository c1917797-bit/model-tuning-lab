from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("mxr_gate_v8", HERE / "run_npu_gate_v8.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_v8_command_is_candidate_only_correctness_gate():
    command = GATE.docker_command()
    joined = " ".join(command)
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert "/dev/davinci5" not in joined
    assert "ASCEND_DEVICE_ID=0" in joined
    assert "mxr_npu_probe_v8.py" in joined
    assert command[command.index("--phase") + 1] == "correctness"


def test_v8_immutable_identity():
    SPEC.loader.exec_module(GATE)
    assert str(GATE.gate.RESULT).endswith("/npu-gate-v8")
    assert GATE.gate.CONTAINER == "mxr_qwen36_npu_gate_v8_20260919"


def test_v8_configuration_is_runnable():
    GATE.configure_gate()
    assert GATE.gate.preflight is GATE.previous.previous.preflight
    assert GATE.gate.monitor is GATE.previous.previous.monitor
    assert GATE.gate.docker_command is GATE.docker_command


def test_v8_probe_filters_exact_official_candidates():
    text = (HERE / "mxr_npu_probe_v8.py").read_text(encoding="utf-8")
    assert 'CANDIDATES = ("pto_staged", "pto_mega")' in text
    assert "selected = {name: methods[name] for name in CANDIDATES}" in text
