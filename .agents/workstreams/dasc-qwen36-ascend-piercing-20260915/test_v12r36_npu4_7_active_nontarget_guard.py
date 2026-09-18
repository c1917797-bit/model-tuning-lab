import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r36_npu4_7_active_nontarget_guard.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r36_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def snapshot(*, actual_id=None, identity=None, started_at="start-a"):
    identity = identity or [(0, 10), (1, 11), (2, 12), (3, 13)]
    return {
        "name": trial.ACTIVE_NONTARGET_NAME,
        "expected_id": trial.ACTIVE_NONTARGET_ID,
        "actual_id": actual_id or trial.ACTIVE_NONTARGET_ID,
        "expected_image_id": trial.ACTIVE_NONTARGET_IMAGE_ID,
        "actual_image_id": trial.ACTIVE_NONTARGET_IMAGE_ID,
        "running": True,
        "paused": False,
        "privileged": True,
        "started_at": started_at,
        "container_host_pids": [10, 11, 12, 13],
        "owned_npu_processes": {
            str(device): [pid] for device, pid in identity
        },
        "npu_identity": identity,
    }


def test_v12r36_changes_only_result_and_owned_container_identity():
    assert trial.controller.NPUS == (4, 5, 6, 7)
    assert trial.controller.RESULT.name == (
        "dense-page-padding-npu4-7-active-nontarget-v12r36"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_npu4_7_v12r36_20260918"
    )
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
        "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
    }
    assert trial.controller.ENFORCE_EAGER is True


def test_active_nontarget_verdict_requires_exact_stable_mapping():
    base = snapshot()
    identity = tuple(tuple(row) for row in base["npu_identity"])
    passing = trial.active_nontarget_verdict(base, identity, "start-a")
    assert passing["ok"] is True

    target_pid = trial.active_nontarget_verdict(
        snapshot(identity=[(0, 10), (1, 11), (2, 12), (4, 14)]),
        None,
        None,
    )
    assert target_pid["ok"] is False
    assert target_pid["target_npu_processes"] == [[4, 14]]

    drift = trial.active_nontarget_verdict(
        snapshot(identity=[(0, 10), (1, 11), (2, 12), (3, 99)]),
        identity,
        "start-a",
    )
    assert drift["ok"] is False
    assert drift["checks"]["npu_process_identity_stable"] is False


def test_live_state_records_strict_coexistence(monkeypatch):
    monkeypatch.setattr(
        trial,
        "_v12r35_live_resource_state",
        lambda: ({"base": True}, []),
    )
    monkeypatch.setattr(
        trial,
        "current_active_nontarget",
        lambda **_kwargs: {"ok": True, "strict": True},
    )
    state, blockers = trial.live_resource_state_with_active_nontarget()
    assert blockers == []
    assert state["authorized_active_nontarget_unknown_scope"] == {
        "ok": True,
        "strict": True,
    }


def test_monitor_fails_closed_when_observation_raises(monkeypatch, tmp_path):
    trial.controller.RESULT = tmp_path
    stopped = []
    monkeypatch.setattr(
        trial,
        "current_active_nontarget",
        lambda: (_ for _ in ()).throw(RuntimeError("probe failed")),
    )
    monkeypatch.setattr(
        trial,
        "_original_run",
        lambda args, **kwargs: stopped.append(args) or "",
    )
    violation = []
    trial.monitor_active_nontarget(trial.threading.Event(), violation)
    assert violation[0]["monitor_error_type"] == "RuntimeError"
    assert stopped == [
        [
            "/usr/bin/docker",
            "stop",
            "--time",
            "1",
            trial.controller.CONTAINER,
        ]
    ]
    stored = json.loads(
        (tmp_path / "active-nontarget-resource-race.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored["phase"] == "physical_canary"


def test_v12r36_delegates_to_v12r35(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 36)
    assert trial.main() == 36
