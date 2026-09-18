import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r37_npu0_3_active_nontarget_guard.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r37_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def active_snapshot(identity):
    return {
        "name": trial.trial.ACTIVE_NONTARGET_NAME,
        "expected_id": trial.trial.ACTIVE_NONTARGET_ID,
        "actual_id": trial.trial.ACTIVE_NONTARGET_ID,
        "expected_image_id": trial.trial.ACTIVE_NONTARGET_IMAGE_ID,
        "actual_image_id": trial.trial.ACTIVE_NONTARGET_IMAGE_ID,
        "running": True,
        "paused": False,
        "privileged": True,
        "started_at": "start-a",
        "container_host_pids": [pid for _device, pid in identity],
        "owned_npu_processes": {
            str(device): [pid] for device, pid in identity
        },
        "npu_identity": identity,
    }


def test_v12r37_switches_only_target_lane_identity():
    assert trial.controller.NPUS == (0, 1, 2, 3)
    assert trial.controller.LOCK.name == "dasc-qwen36-npu0-3.lock"
    assert trial.controller.RESULT.name == (
        "dense-page-padding-npu0-3-active-nontarget-v12r37"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_npu0_3_v12r37_20260918"
    )
    assert trial.controller.ENFORCE_EAGER is True


def test_v12r37_accepts_exact_container_only_on_npu4_7():
    identity = [(4, 40), (5, 50), (6, 60), (7, 70)]
    result = trial.trial.active_nontarget_verdict(
        active_snapshot(identity),
        tuple(identity),
        "start-a",
    )
    assert result["ok"] is True
    assert result["expected_nontarget_devices"] == [4, 5, 6, 7]

    crossed = [(0, 10), (5, 50), (6, 60), (7, 70)]
    result = trial.trial.active_nontarget_verdict(
        active_snapshot(crossed), None, None
    )
    assert result["ok"] is False
    assert result["target_npu_processes"] == [[0, 10]]


def test_v12r37_delegates_to_v12r36(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 37)
    assert trial.main() == 37
