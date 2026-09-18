import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "run_v12r32_dense_page_padding_retry.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r32_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r32_retries_identical_treatment_in_a_new_root():
    assert trial.controller.RESULT.name == (
        "dense-page-padding-identity-retry-v12r32"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_identity_v12r32_20260918"
    )
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
        "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
    }
    assert trial.controller.ENFORCE_EAGER is True


def test_parse_containerd_tasks_ignores_header_and_preserves_status():
    rows = trial.parse_containerd_tasks(
        "TASK PID STATUS\n"
        "dias-cont-1 419834 STOPPED\n"
        "dias-cont-2 512000 RUNNING\n",
        namespace="dias",
    )
    assert rows == [
        {
            "namespace": "dias",
            "task": "dias-cont-1",
            "pid": 419834,
            "status": "STOPPED",
        },
        {
            "namespace": "dias",
            "task": "dias-cont-2",
            "pid": 512000,
            "status": "RUNNING",
        },
    ]


def test_preflight_blocks_running_dias_task(monkeypatch):
    monkeypatch.setattr(
        trial,
        "_original_live_resource_state",
        lambda: ({"npu_process_devices": []}, []),
    )
    monkeypatch.setattr(
        trial,
        "running_dias_tasks",
        lambda: [
            {
                "namespace": "dias",
                "task": "dias-cont-1",
                "pid": 419834,
                "status": "RUNNING",
            }
        ],
    )
    state, blockers = trial.live_resource_state_with_dias_guard()
    assert state["running_dias_containerd_tasks"][0]["task"] == "dias-cont-1"
    assert blockers == [
        "running DIAS containerd tasks with independent NPU access: dias-cont-1"
    ]


def test_startup_guard_preserves_failure_evidence(monkeypatch, tmp_path):
    trial.controller.RESULT = tmp_path
    monkeypatch.setattr(
        trial,
        "_original_startup_ownership",
        lambda: {"ok": True, "foreign_process_pids": []},
    )
    monkeypatch.setattr(
        trial,
        "running_dias_tasks",
        lambda: [
            {
                "namespace": "dias",
                "task": "dias-cont-1",
                "pid": 419834,
                "status": "RUNNING",
            }
        ],
    )
    with pytest.raises(RuntimeError, match="running DIAS tasks"):
        trial.validate_startup_ownership_with_dias_guard()
    assert (tmp_path / "startup-ownership-last.json").is_file()
    assert (tmp_path / "startup-resource-race.json").is_file()
