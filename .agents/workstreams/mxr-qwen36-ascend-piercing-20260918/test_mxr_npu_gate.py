from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("mxr_gate", HERE / "run_npu_gate_v1.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_parse_top_ignores_header():
    assert GATE.parse_top("PID\n11\n--\n22\n") == {11, 22}


def test_ownership_accepts_only_mapped_owned_pid():
    snapshot = {4: {101}, 5: set(), 6: set(), 7: set()}
    assert GATE.ownership_verdict(snapshot, {101})["ok"]


def test_ownership_rejects_foreign_and_unmapped():
    foreign = {4: {101, 102}, 5: set(), 6: set(), 7: set()}
    assert not GATE.ownership_verdict(foreign, {101})["ok"]
    unmapped = {4: {101}, 5: {201}, 6: set(), 7: set()}
    assert not GATE.ownership_verdict(unmapped, {101})["ok"]


def test_docker_command_maps_only_physical_npu4():
    joined = " ".join(GATE.docker_command())
    assert "/dev/davinci4:/dev/davinci0" in joined
    assert "/dev/davinci5" not in joined
    assert "/dev/davinci6" not in joined
    assert "/dev/davinci7" not in joined
    assert "ASCEND_RT_VISIBLE_DEVICES=0" in joined
    assert "--phase all" in joined
