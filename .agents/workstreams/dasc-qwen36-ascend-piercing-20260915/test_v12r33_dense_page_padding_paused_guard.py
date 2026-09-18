import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "run_v12r33_dense_page_padding_paused_guard.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r33_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def inspect_payload(*, paused=True, container_id=None):
    return json.dumps(
        [
            {
                "Id": container_id or trial.PAUSED_CONTAINER_ID,
                "Name": "/" + trial.PAUSED_CONTAINER_NAME,
                "State": {
                    "Running": True,
                    "Paused": paused,
                    "StartedAt": "2026-09-18T11:34:00Z",
                },
                "HostConfig": {"Privileged": True},
            }
        ]
    )


def test_v12r33_keeps_treatment_and_uses_new_identity():
    assert trial.controller.RESULT.name == (
        "dense-page-padding-paused-guard-v12r33"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_paused_guard_v12r33_20260918"
    )
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
        "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
    }
    assert trial.controller.ENFORCE_EAGER is True


def test_paused_container_requires_exact_id_and_paused_state(monkeypatch):
    monkeypatch.setattr(
        trial,
        "_original_run",
        lambda *args, **kwargs: inspect_payload(),
    )
    state = trial.paused_container_state()
    assert state["ok"] is True
    assert state["paused"] is True

    monkeypatch.setattr(
        trial,
        "_original_run",
        lambda *args, **kwargs: inspect_payload(paused=False),
    )
    assert trial.paused_container_state()["ok"] is False

    monkeypatch.setattr(
        trial,
        "_original_run",
        lambda *args, **kwargs: inspect_payload(container_id="wrong"),
    )
    assert trial.paused_container_state()["ok"] is False


def test_preflight_blocks_when_exact_container_is_not_paused(monkeypatch):
    monkeypatch.setattr(
        trial,
        "_original_live_resource_state",
        lambda: ({"running_dias_containerd_tasks": []}, []),
    )
    monkeypatch.setattr(
        trial,
        "paused_container_state",
        lambda: {"ok": False, "paused": False},
    )
    state, blockers = trial.live_resource_state_with_paused_guard()
    assert state["paused_unknown_scope_container"]["paused"] is False
    assert blockers == [
        "exact wildcard container is not running paused with expected identity"
    ]


def test_require_paused_container_records_resource_race(monkeypatch, tmp_path):
    trial.controller.RESULT = tmp_path
    monkeypatch.setattr(
        trial,
        "paused_container_state",
        lambda: {"ok": False, "error": "container_absent_or_unreadable"},
    )
    with pytest.raises(RuntimeError, match="not_run/resource_race"):
        trial.require_paused_container("startup")
    record = json.loads(
        (tmp_path / "paused-container-resource-race.json").read_text()
    )
    assert record["phase"] == "startup"


def test_restore_unpauses_only_exact_paused_container(monkeypatch, tmp_path):
    trial.controller.RESULT = tmp_path
    calls = []
    monkeypatch.setattr(
        trial,
        "paused_container_state",
        lambda: {
            "ok": True,
            "actual_id": trial.PAUSED_CONTAINER_ID,
            "running": True,
            "paused": True,
        },
    )
    monkeypatch.setattr(
        trial,
        "_original_run",
        lambda args, **kwargs: calls.append(args) or trial.PAUSED_CONTAINER_NAME,
    )
    result = trial.restore_foreign_container()
    assert result["unpause_requested"] is True
    assert calls == [
        ["/usr/bin/docker", "unpause", trial.PAUSED_CONTAINER_NAME]
    ]
    assert (tmp_path / "paused-container-restoration.json").is_file()

