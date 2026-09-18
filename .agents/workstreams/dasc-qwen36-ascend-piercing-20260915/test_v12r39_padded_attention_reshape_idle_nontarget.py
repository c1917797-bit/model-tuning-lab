import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r39_padded_attention_reshape_idle_nontarget.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r39_under_test", MODULE_PATH
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


def test_v12r39_has_immutable_npu4_7_result_identity():
    assert trial.controller.NPUS == (4, 5, 6, 7)
    assert trial.controller.RESULT.name == (
        "padded-attention-reshape-idle-nontarget-npu4-7-v12r39"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_padded_attention_reshape_idle_nontarget_"
        "npu4_7_v12r39_20260918"
    )


def test_v12r39_accepts_exact_stable_idle_container():
    result = trial.idle_or_full_nontarget_verdict(
        _snapshot([]), tuple(), "stable-start"
    )
    assert result["ok"] is True
    assert result["nontarget_device_state"] == "idle"


def test_v12r39_accepts_exact_stable_full_nontarget_container():
    identity = [(0, 100), (1, 101), (2, 102), (3, 103)]
    result = trial.idle_or_full_nontarget_verdict(
        _snapshot(identity), tuple(identity), "stable-start"
    )
    assert result["ok"] is True
    assert result["nontarget_device_state"] == "full_nontarget"


def test_v12r39_rejects_partial_or_target_device_identity():
    partial = trial.idle_or_full_nontarget_verdict(
        _snapshot([(0, 100)]), None, None
    )
    target = trial.idle_or_full_nontarget_verdict(
        _snapshot([(4, 104)]), None, None
    )
    assert partial["ok"] is False
    assert partial["nontarget_device_state"] == "unsupported_partial"
    assert target["ok"] is False
    assert target["checks"]["no_target_npu_process"] is False
