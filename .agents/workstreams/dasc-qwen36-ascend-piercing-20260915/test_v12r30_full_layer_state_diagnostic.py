import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r30_full_layer_state_diagnostic.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r30_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


INVENTORY = {
    "gdn_layer_count": 3,
    "gdn_layer_ids": [0, 2, 3],
}


def complete_rows():
    rows = []
    layers = sorted(trial._expected_layer_names(INVENTORY))
    for pid in (21, 22, 23, 24):
        rows.append(
            {
                "event": "gdn_running_state_indices_remapped",
                "pid": pid,
                "layer_count": len(layers),
                "copy_remap_active": True,
                "representative_layers": [
                    {
                        "layer": layer,
                        "normalized_source_state_indices": [7],
                        "destination_state_indices": [9],
                    }
                    for layer in layers
                ],
            }
        )
        for layer in layers:
            for state_index in (0, 1):
                common = {
                    "pid": pid,
                    "layer": layer,
                    "state_index": state_index,
                    "source_block_id": 7,
                    "destination_block_id": 9,
                }
                rows.append(
                    {
                        **common,
                        "event": "physical_state_copy_materialized",
                        "diagnostic_scope": "all_gdn_layers",
                        "source_pointer_block_id": 7,
                        "copy_bytes": 128,
                        "source_after_copy": {"full_sha256": "copied"},
                        "destination_after_copy": {"full_sha256": "copied"},
                    }
                )
                rows.append(
                    {
                        **common,
                        "event": "first_resumed_token_state_boundary_before",
                        "normalized_source_state_indices": [7],
                        "destination_state_indices": [9],
                        "source_before_native": {"full_sha256": "source"},
                        "destination_before_native": {"full_sha256": "copied"},
                    }
                )
                rows.append(
                    {
                        **common,
                        "event": "first_resumed_token_state_boundary_after",
                        "source_after_native": {"full_sha256": "source"},
                        "destination_after_native": {"full_sha256": "updated"},
                    }
                )
    return rows


def verdict(rows=None, numerical=None):
    return trial.full_layer_state_verdict(
        complete_rows() if rows is None else rows,
        {"ok": False} if numerical is None else numerical,
        expected_inventory=INVENTORY,
    )


def test_v12r30_has_distinct_identity_and_diagnostic_only_switch():
    assert trial.controller.RESULT.name == "state-index-eager-all-layers-v12r30"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_state_index_eager_all_layers_v12r30_20260918"
    )
    assert trial.controller.ENFORCE_EAGER is True
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1"
    }
    assert trial.state_trial.EXPECTED_REPRESENTATIVE_LAYERS == 48


def test_v12r30_launch_injects_full_layer_scope_without_graph(monkeypatch):
    captured = []

    def fake_run(args, **kwargs):
        captured.append(list(args))
        return "container-id\n"

    monkeypatch.setattr(trial.controller, "run", fake_run)
    assert trial.controller.launch() == "container-id"
    args = captured[-1]
    assert "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS=1" in args
    assert "--enforce-eager" in args
    assert "--compilation-config" not in args


def test_full_layer_verdict_accepts_exact_cartesian_rows_separately_from_numerical():
    result = verdict()
    assert result["expected"]["exact_keys"] == 24
    assert result["exact_copy_key_count"] == 24
    assert result["row_gate_ok"] is True
    assert result["numerical_canary_ok"] is False
    assert result["overall_ok"] is False
    assert result["decision"] == (
        "full_layer_state_boundary_passed_numerical_failed"
    )


def test_full_layer_verdict_rejects_missing_middle_layer():
    rows = [
        row
        for row in complete_rows()
        if not (row.get("pid") == 21 and ".layers.2." in row.get("layer", ""))
    ]
    result = verdict(rows)
    assert result["row_gate_ok"] is False
    assert result["checks"]["canonical_layer_state_cartesian_coverage"] is False


def test_full_layer_verdict_rejects_one_unchanged_destination():
    rows = complete_rows()
    target = next(
        row
        for row in rows
        if row.get("event") == "first_resumed_token_state_boundary_after"
    )
    target["destination_after_native"]["full_sha256"] = "copied"
    result = verdict(rows)
    assert result["row_gate_ok"] is False
    assert result["checks"]["every_destination_row_updated"] is False


def test_full_layer_verdict_rejects_duplicate_boundary_event():
    rows = complete_rows()
    rows.append(
        next(
            dict(row)
            for row in rows
            if row.get("event") == "first_resumed_token_state_boundary_before"
        )
    )
    result = verdict(rows)
    assert result["row_gate_ok"] is False
    assert result["checks"]["one_before_and_after_pair_per_copy"] is False
