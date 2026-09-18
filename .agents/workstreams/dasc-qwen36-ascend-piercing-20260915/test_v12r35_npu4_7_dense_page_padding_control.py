import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r35_npu4_7_dense_page_padding_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r35_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def dias_task():
    return {
        "namespace": "dias",
        "task": "dias-cont-1",
        "pid": 813165,
        "status": "RUNNING",
    }


def test_v12r35_changes_only_target_lane_identity():
    assert trial.controller.NPUS == (4, 5, 6, 7)
    assert trial.controller.LOCK.name == "dasc-qwen36-npu4-7.lock"
    assert trial.controller.RESULT.name == (
        "dense-page-padding-npu4-7-coexist-v12r35"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_npu4_7_v12r35_20260918"
    )
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
        "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
    }
    assert trial.controller.ENFORCE_EAGER is True


def test_v12r35_allows_dias_on_npu0_3_but_not_npu4_7():
    tasks = [dias_task()]
    identity = trial.trial.dias_identity(tasks)
    allowed = trial.trial.dias_coexistence_verdict(
        tasks,
        {0: {1099613}, 1: {1099614}, 2: {1099615}, 3: {1099616}},
        {},
        identity,
    )
    assert allowed["ok"] is True

    blocked = trial.trial.dias_coexistence_verdict(
        tasks,
        {4: {1099613}},
        {1099613: "0::/dias/dias-cont-1"},
        identity,
    )
    assert blocked["ok"] is False
    assert blocked["target_tasks"][0]["target_pids"] == [1099613]


def test_v12r35_delegates_to_target_lane_controller(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 35)
    assert trial.main() == 35
