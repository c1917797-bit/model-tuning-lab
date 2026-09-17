import importlib.util
import hashlib
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("run_v12r20_state_index_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r20_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)

EXPECTED_INVENTORY = {
    "model_config_path": "/test/config.json",
    "model_config_sha256": "config-sha",
    "selector_manifest_path": "/test/selector.json",
    "selector_manifest_sha256": "manifest-sha",
    "hidden_layer_count": 64,
    "gdn_layer_count": 48,
    "gdn_layer_ids": [
        index for index in range(64) if (index + 1) % 4 != 0
    ],
}


def verdict(rows, numerical):
    return trial.state_index_verdict(
        rows,
        numerical,
        expected_inventory=EXPECTED_INVENTORY,
    )


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
                "event": "gdn_running_state_indices_remapped",
                "pid": pid,
                "layer_count": 48,
                "representative_layers": [
                    {
                        "source_state_indices": [7],
                        "destination_state_indices": [9],
                    },
                    {
                        "source_state_indices": [7],
                        "destination_state_indices": [9],
                    },
                ],
            }
        )
        for layer in ("layers.0", "layers.47"):
            for state_index in (0, 1):
                rows.append(
                    {
                        "event": "physical_state_copy_materialized",
                        "pid": pid,
                        "layer": layer,
                        "state_index": state_index,
                        "source_block_id": 7,
                        "destination_block_id": 9,
                        "source_pointer_block_id": 7,
                        "copy_bytes": 128,
                        "source_after_copy": {"full_sha256": "same"},
                        "destination_after_copy": {
                            "full_sha256": "same"
                        },
                    }
                )
                rows.append(
                    {
                        "event": (
                            "first_resumed_token_state_boundary_before"
                        ),
                        "pid": pid,
                        "layer": layer,
                        "state_index": state_index,
                        "source_block_id": 7,
                        "destination_block_id": 9,
                        "source_before_native": {"full_sha256": "old"},
                        "destination_before_native": {
                            "full_sha256": "copied"
                        },
                    }
                )
                rows.append(
                    {
                        "event": (
                            "first_resumed_token_state_boundary_after"
                        ),
                        "pid": pid,
                        "layer": layer,
                        "state_index": state_index,
                        "source_block_id": 7,
                        "destination_block_id": 9,
                        "source_after_native": {"full_sha256": "old"},
                        "destination_after_native": {
                            "full_sha256": "updated"
                        },
                    }
                )
    return rows


def test_state_index_verdict_accepts_exact_row_transition():
    result = verdict(complete_rows(), {"ok": True})
    assert result["row_gate_ok"] is True
    assert result["numerical_canary_ok"] is True
    assert result["overall_ok"] is True
    assert result["decision"] == "state_row_fix_and_numerical_canary_passed"


def test_state_index_verdict_separates_row_success_from_numerical_failure():
    result = verdict(complete_rows(), {"ok": False})
    assert result["row_gate_ok"] is True
    assert result["overall_ok"] is False
    assert result["decision"] == (
        "state_row_fix_executed_but_numerical_canary_failed"
    )


def test_state_index_verdict_rejects_old_source_mutation():
    rows = complete_rows()
    rows[-1]["source_after_native"]["full_sha256"] = "changed"
    result = verdict(rows, {"ok": True})
    assert result["row_gate_ok"] is False
    assert result["decision"] == "native_execution_still_mutated_old_source_row"


def test_state_index_verdict_rejects_partial_state_or_layer_coverage():
    rows = complete_rows()
    rows = [
        row
        for row in rows
        if not (
            row.get("pid") == 21
            and row.get("layer") == "layers.47"
            and row.get("state_index") == 0
        )
    ]
    result = verdict(rows, {"ok": True})
    assert result["row_gate_ok"] is False
    assert result["decision"] == "physical_copy_coverage_incomplete"


def test_state_index_verdict_rejects_unpaired_exact_copy():
    rows = complete_rows()
    removed = False
    filtered = []
    for row in rows:
        if (
            not removed
            and row.get("event")
            == "first_resumed_token_state_boundary_after"
        ):
            removed = True
            continue
        filtered.append(row)
    result = verdict(filtered, {"ok": True})
    assert result["row_gate_ok"] is False
    assert result["decision"] == (
        "native_boundary_does_not_match_every_exact_copy"
    )


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
    monkeypatch.setattr(
        trial,
        "load_expected_gdn_inventory",
        lambda: EXPECTED_INVENTORY,
    )
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


def test_expected_inventory_is_derived_from_checkpoint_and_manifest(tmp_path):
    layer_types = [
        "full_attention" if (index + 1) % 4 == 0 else "linear_attention"
        for index in range(8)
    ]
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "text_config": {
                    "num_hidden_layers": 8,
                    "layer_types": layer_types,
                }
            }
        ),
        encoding="utf-8",
    )
    config_sha256 = hashlib.sha256(config_path.read_bytes()).hexdigest()
    manifest_path = tmp_path / "selector.json"
    manifest_path.write_text(
        json.dumps(
            {
                "model_config_sha256": config_sha256,
                "layer_count": 6,
                "layers": [
                    {"layer": index}
                    for index, layer_type in enumerate(layer_types)
                    if layer_type == "linear_attention"
                ],
            }
        ),
        encoding="utf-8",
    )

    result = trial.load_expected_gdn_inventory(config_path, manifest_path)

    assert result["hidden_layer_count"] == 8
    assert result["gdn_layer_count"] == 6
    assert result["gdn_layer_ids"] == [0, 1, 2, 4, 5, 6]


def test_expected_inventory_rejects_manifest_from_different_checkpoint(
    tmp_path,
):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "text_config": {
                    "num_hidden_layers": 4,
                    "layer_types": [
                        "linear_attention",
                        "linear_attention",
                        "linear_attention",
                        "full_attention",
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "selector.json"
    manifest_path.write_text(
        json.dumps(
            {
                "model_config_sha256": "wrong-checkpoint",
                "layer_count": 3,
                "layers": [
                    {"layer": 0},
                    {"layer": 1},
                    {"layer": 2},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="model-config hash mismatch"):
        trial.load_expected_gdn_inventory(config_path, manifest_path)
