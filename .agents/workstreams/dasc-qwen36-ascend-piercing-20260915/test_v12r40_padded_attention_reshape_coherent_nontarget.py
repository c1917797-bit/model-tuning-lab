import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r40_padded_attention_reshape_coherent_nontarget.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r40_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def _snapshot(identity: list[tuple[int, int]]) -> dict:
    return {
        "name": trial.v12r36.ACTIVE_NONTARGET_NAME,
        "actual_id": trial.v12r36.ACTIVE_NONTARGET_ID,
        "actual_image_id": trial.v12r36.ACTIVE_NONTARGET_IMAGE_ID,
        "running": True,
        "paused": False,
        "privileged": True,
        "started_at": "stable-start",
        "npu_identity": identity,
    }


def test_v12r40_has_immutable_npu4_7_result_identity():
    assert trial.controller.NPUS == (4, 5, 6, 7)
    assert trial.controller.RESULT.name == (
        "padded-attention-reshape-coherent-nontarget-npu4-7-v12r40"
    )


def test_v12r40_accepts_idle_to_full_nontarget_transition():
    idle = trial.coherent_nontarget_verdict(
        _snapshot([]), ((0, 1),), "stable-start"
    )
    full = trial.coherent_nontarget_verdict(
        _snapshot([(0, 10), (1, 11), (2, 12), (3, 13)]),
        tuple(),
        "stable-start",
    )
    assert idle["ok"] is True
    assert idle["nontarget_device_state"] == "idle"
    assert full["ok"] is True
    assert full["nontarget_device_state"] == "full_nontarget"


def test_v12r40_rejects_partial_or_target_processes():
    partial = trial.coherent_nontarget_verdict(
        _snapshot([(0, 10), (1, 11)]), None, None
    )
    target = trial.coherent_nontarget_verdict(
        _snapshot([(4, 14)]), None, None
    )
    assert partial["ok"] is False
    assert partial["checks"]["coherent_nontarget_state"] is False
    assert target["ok"] is False
    assert target["checks"]["no_target_npu_process"] is False
