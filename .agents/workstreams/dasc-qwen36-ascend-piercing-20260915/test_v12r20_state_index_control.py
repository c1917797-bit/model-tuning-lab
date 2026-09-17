import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("run_v12r20_state_index_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r20_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r20_has_distinct_immutable_identity():
    assert trial.controller.RESULT.name == "state-index-all-heads-v12r20"
    assert trial.controller.CONTAINER == "dasc_qwen36_state_index_v12r20_20260917"
    assert (
        trial.controller.PLUGIN_MODE
        == "physical-cache-native-all-heads-state-index"
    )


def complete_rows():
    rows = []
    for pid in (21, 22, 23, 24):
        rows.append(
            {
                "event": "physical_state_copy_materialized",
                "pid": pid,
                "layer": "layers.0",
                "state_index": 1,
                "source_block_id": 7,
                "destination_block_id": 9,
                "source_pointer_block_id": 7,
                "copy_bytes": 128,
                "source_after_copy": {"full_sha256": "same"},
                "destination_after_copy": {"full_sha256": "same"},
            }
        )
        rows.append(
            {
                "event": "gdn_running_state_indices_remapped",
                "pid": pid,
                "representative_layers": [
                    {
                        "source_state_indices": [7],
                        "destination_state_indices": [9],
                    }
                ],
            }
        )
        rows.append(
            {
                "event": "first_resumed_token_state_boundary_before",
                "pid": pid,
                "layer": "layers.0",
                "state_index": 1,
                "source_block_id": 7,
                "destination_block_id": 9,
                "source_before_native": {"full_sha256": "old"},
                "destination_before_native": {"full_sha256": "copied"},
            }
        )
        rows.append(
            {
                "event": "first_resumed_token_state_boundary_after",
                "pid": pid,
                "layer": "layers.0",
                "state_index": 1,
                "source_block_id": 7,
                "destination_block_id": 9,
                "source_after_native": {"full_sha256": "old"},
                "destination_after_native": {"full_sha256": "updated"},
            }
        )
    return rows


def test_state_index_verdict_accepts_exact_row_transition():
    result = trial.state_index_verdict(complete_rows(), {"ok": True})
    assert result["row_gate_ok"] is True
    assert result["numerical_canary_ok"] is True
    assert result["overall_ok"] is True
    assert result["decision"] == "state_row_fix_and_numerical_canary_passed"


def test_state_index_verdict_separates_row_success_from_numerical_failure():
    result = trial.state_index_verdict(complete_rows(), {"ok": False})
    assert result["row_gate_ok"] is True
    assert result["overall_ok"] is False
    assert result["decision"] == (
        "state_row_fix_executed_but_numerical_canary_failed"
    )


def test_state_index_verdict_rejects_old_source_mutation():
    rows = complete_rows()
    rows[-1]["source_after_native"]["full_sha256"] = "changed"
    result = trial.state_index_verdict(rows, {"ok": True})
    assert result["row_gate_ok"] is False
    assert result["decision"] == "native_execution_still_mutated_old_source_row"


def test_numerical_failure_still_writes_state_index_verdict(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(trial.controller, "RESULT", tmp_path)
    (tmp_path / "evidence.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in complete_rows()),
        encoding="utf-8",
    )
    (tmp_path / "physical-canary.json").write_text(
        json.dumps({"ok": False}), encoding="utf-8"
    )

    def fail():
        raise RuntimeError("strict numerical gate failed")

    monkeypatch.setattr(trial.trial, "main", fail)
    with pytest.raises(RuntimeError, match="strict numerical gate failed"):
        trial.main()

    result = json.loads(
        (tmp_path / "state-index-verdict.json").read_text(encoding="utf-8")
    )
    assert result["row_gate_ok"] is True
    assert result["overall_ok"] is False
    manifest = json.loads(
        (tmp_path / "artifacts.sha256.json").read_text(encoding="utf-8")
    )
    assert "state-index-verdict.json" in manifest
    assert "artifacts.sha256.json" not in manifest
