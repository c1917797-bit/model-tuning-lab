import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r34_npu0_3_dense_page_padding_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r34_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def dias_task(pid=813165):
    return {
        "namespace": "dias",
        "task": "dias-cont-1",
        "pid": pid,
        "status": "RUNNING",
    }


def test_v12r34_changes_only_lane_and_environment_identity():
    assert trial.controller.NPUS == (0, 1, 2, 3)
    assert trial.controller.LOCK.name == "dasc-qwen36-npu0-3.lock"
    assert trial.controller.RESULT.name == (
        "dense-page-padding-npu0-3-coexist-v12r34"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_npu0_3_v12r34_20260918"
    )
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
        "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
    }
    assert trial.controller.ENFORCE_EAGER is True


def test_dias_coexistence_allows_stable_task_on_nontarget_lane():
    tasks = [dias_task()]
    identity = trial.dias_identity(tasks)
    result = trial.dias_coexistence_verdict(
        tasks,
        {4: {875811}, 5: {875812}, 6: {875813}, 7: {875814}},
        {},
        identity,
    )
    assert result["ok"] is True
    assert result["target_tasks"] == []


def test_dias_coexistence_rejects_target_pid_and_identity_drift():
    tasks = [dias_task(pid=900000)]
    original_identity = trial.dias_identity([dias_task()])
    result = trial.dias_coexistence_verdict(
        tasks,
        {0: {901000}},
        {901000: "0::/dias/dias-cont-1"},
        original_identity,
    )
    assert result["ok"] is False
    assert result["checks"]["no_dias_process_on_target_npus"] is False
    assert result["checks"]["task_identity_stable"] is False
    assert result["target_tasks"][0]["target_pids"] == [901000]


def test_dias_coexistence_rejects_unexpected_task_name():
    tasks = [
        dias_task(),
        {
            "namespace": "dias",
            "task": "dias-cont-2",
            "pid": 999999,
            "status": "RUNNING",
        },
    ]
    result = trial.dias_coexistence_verdict(tasks, {}, {}, None)
    assert result["ok"] is False
    assert result["unexpected_task_names"] == ["dias-cont-2"]


def test_target_runtime_requires_owned_workers_and_bounded_hbm_growth():
    passing = trial.target_runtime_verdict(
        {0: {10}, 1: {11}, 2: {12}, 3: {13}},
        {10, 11, 12, 13},
        {0: 25000, 1: 25001, 2: 25002, 3: 25003},
        {0: 24000, 1: 24000, 2: 24000, 3: 24000},
    )
    assert passing["ok"] is True

    foreign = trial.target_runtime_verdict(
        {0: {10, 99}, 1: {11}, 2: {12}, 3: {13}},
        {10, 11, 12, 13},
        {0: 25000, 1: 25001, 2: 25002, 3: 25003},
        {0: 24000, 1: 24000, 2: 24000, 3: 24000},
    )
    assert foreign["ok"] is False
    assert foreign["foreign_process_pids"] == [99]

    hbm_growth = trial.target_runtime_verdict(
        {0: {10}, 1: {11}, 2: {12}, 3: {13}},
        {10, 11, 12, 13},
        {0: 29000, 1: 25001, 2: 25002, 3: 25003},
        {0: 24000, 1: 24000, 2: 24000, 3: 24000},
    )
    assert hbm_growth["ok"] is False
    assert hbm_growth["excessive_hbm_growth_devices"] == [0]


def test_monitor_fails_closed_when_observation_raises(monkeypatch, tmp_path):
    trial.controller.RESULT = tmp_path
    stopped = []
    monkeypatch.setattr(
        trial,
        "current_dias_coexistence",
        lambda: (_ for _ in ()).throw(RuntimeError("probe failed")),
    )
    monkeypatch.setattr(
        trial.trial,
        "_original_run",
        lambda args, **kwargs: stopped.append(args) or "",
    )
    violation = []
    trial.monitor_npu0_3(trial.threading.Event(), violation)

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
        (tmp_path / "npu0-3-resource-race.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored["phase"] == "physical_canary"
