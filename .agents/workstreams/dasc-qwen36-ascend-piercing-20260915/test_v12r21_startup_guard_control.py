import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "run_v12r21_startup_guard_control.py"
)
SPEC = importlib.util.spec_from_file_location("run_v12r21_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def container(
    name,
    *,
    privileged,
    devices=None,
    env=None,
    running=True,
):
    return {
        "Id": f"id-{name}",
        "Name": f"/{name}",
        "State": {
            "Running": running,
            "StartedAt": "2026-09-17T00:00:00Z",
        },
        "HostConfig": {
            "Privileged": privileged,
            "Devices": devices or [],
        },
        "Config": {
            "Image": "test-image",
            "Env": env or [],
        },
    }


def test_v12r21_keeps_state_index_algorithm_and_changes_immutable_identity():
    assert trial.controller.PLUGIN_MODE == (
        "physical-cache-native-all-heads-state-index"
    )
    assert trial.controller.RESULT.name == "state-index-startup-guard-v12r21"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_state_index_v12r21_20260917"
    )


def test_privileged_container_without_device_scope_is_wildcard_contender():
    rows = trial.unknown_device_scope_containers(
        [container("alltoall", privileged=True)]
    )
    assert rows == [
        {
            "name": "alltoall",
            "id": "id-alltoall",
            "image": "test-image",
            "started_at": "2026-09-17T00:00:00Z",
            "classification": "unknown_device_scope",
            "claim": "wildcard_npu_contender",
        }
    ]


def test_explicit_mapping_or_visible_declaration_proves_scope():
    mapped = container(
        "mapped",
        privileged=True,
        devices=[{"PathOnHost": "/dev/davinci4"}],
    )
    declared = container(
        "declared",
        privileged=True,
        env=["ASCEND_RT_VISIBLE_DEVICES=4,5,6,7"],
    )
    ordinary = container("ordinary", privileged=False)
    stopped = container("stopped", privileged=True, running=False)
    assert trial.unknown_device_scope_containers(
        [mapped, declared, ordinary, stopped]
    ) == []


def test_owned_container_can_be_excluded_from_unknown_scope_check():
    item = container(trial.controller.CONTAINER, privileged=True)
    assert trial.unknown_device_scope_containers(
        [item], excluded_names={trial.controller.CONTAINER}
    ) == []


def test_guarded_preflight_blocks_unknown_scope_container(monkeypatch):
    monkeypatch.delenv("MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE", raising=False)
    monkeypatch.setattr(
        trial,
        "_original_live_resource_state",
        lambda: ({"container_claims": {}}, []),
    )
    monkeypatch.setattr(
        trial,
        "running_container_inspects",
        lambda: [container("alltoall", privileged=True)],
    )
    state, blockers = trial.guarded_live_resource_state()
    assert state["unknown_device_scope_policy"] == (
        "block_as_wildcard_npu_contender"
    )
    assert state["unknown_device_scope_containers"][0]["name"] == "alltoall"
    assert blockers == [
        "running privileged containers with unknown device scope: alltoall"
    ]


def test_guarded_preflight_allows_only_exact_named_idle_contenders(monkeypatch):
    monkeypatch.setenv(
        "MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE",
        "alltoall,Maxon",
    )
    monkeypatch.setattr(
        trial,
        "_original_live_resource_state",
        lambda: ({"container_claims": {}}, []),
    )
    monkeypatch.setattr(
        trial,
        "running_container_inspects",
        lambda: [
            container("alltoall", privileged=True),
            container("Maxon", privileged=True),
            container("late", privileged=True),
        ],
    )
    state, blockers = trial.guarded_live_resource_state()
    assert state["unknown_device_scope_policy"] == (
        "exact_name_idle_coexistence_with_pid_guard"
    )
    assert [
        row["name"]
        for row in state["authorized_idle_unknown_scope_containers"]
    ] == ["Maxon", "alltoall"]
    assert [
        row["name"]
        for row in state["unexpected_unknown_device_scope_containers"]
    ] == ["late"]
    assert blockers == [
        "running privileged containers with unknown device scope: late"
    ]


def test_idle_coexistence_name_validation_is_fail_closed(monkeypatch):
    monkeypatch.setenv(
        "MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE",
        "valid-name,../../broad",
    )
    with pytest.raises(ValueError, match="invalid idle unknown-scope"):
        trial.authorized_idle_unknown_scope_names()


def test_startup_verdict_detects_foreign_pid_and_unknown_scope():
    rows = {
        4: {101},
        5: {102, 902},
        6: {103},
        7: {104},
    }
    unknown = trial.unknown_device_scope_containers(
        [container("late", privileged=True)]
    )
    verdict = trial.startup_ownership_verdict(
        rows, {101, 102, 103, 104}, unknown
    )
    assert verdict["foreign_process_pids"] == [902]
    assert verdict["unknown_device_scope_containers"][0]["name"] == "late"
    assert verdict["ok"] is False


def test_startup_verdict_allows_named_idle_container_but_not_foreign_pid():
    unknown = trial.unknown_device_scope_containers(
        [container("alltoall", privileged=True)]
    )
    idle = trial.startup_ownership_verdict(
        {4: set(), 5: set(), 6: set(), 7: set()},
        set(),
        unknown,
        {"alltoall"},
    )
    assert idle["ok"] is True
    assert idle["authorized_idle_unknown_scope_containers"] == unknown
    raced = trial.startup_ownership_verdict(
        {4: {902}, 5: set(), 6: set(), 7: set()},
        set(),
        unknown,
        {"alltoall"},
    )
    assert raced["foreign_process_pids"] == [902]
    assert raced["ok"] is False


def test_startup_verdict_accepts_only_owned_workers():
    rows = {
        4: {101},
        5: {102},
        6: {103},
        7: {104},
    }
    verdict = trial.startup_ownership_verdict(
        rows, {101, 102, 103, 104, 999}, []
    )
    assert verdict["foreign_process_pids"] == []
    assert verdict["ok"] is True


def test_readiness_does_not_swallow_final_ownership_failure(monkeypatch):
    monkeypatch.setattr(
        trial.controller,
        "run",
        lambda args, **kwargs: "true\n",
    )

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        trial.urllib.request,
        "urlopen",
        lambda *args, **kwargs: Response(),
    )
    calls = 0

    def validate():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("not_run/resource_race during startup")
        return {"ok": True}

    monkeypatch.setattr(trial, "validate_startup_ownership", validate)
    with pytest.raises(RuntimeError, match="not_run/resource_race"):
        trial.guarded_wait_ready()
    assert calls == 2
