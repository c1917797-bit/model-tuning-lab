#!/usr/bin/env python3
"""Run the v12r28 treatment with exact state-row evidence on every GDN layer."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r28_trial",
    HERE / "run_v12r28_eager_resource_retry.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r28 eager resource retry")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "state-index-eager-all-layers-v12r30"
)
controller.CONTAINER = (
    "dasc_qwen36_state_index_eager_all_layers_v12r30_20260918"
)
controller.PLUGIN_EXTRA_ENV = {
    "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
}

EXPECTED_TP_WORKERS = 4
EXPECTED_STATE_INDICES = {0, 1}


def _find_state_trial(module):
    seen = set()
    while module is not None and id(module) not in seen:
        seen.add(id(module))
        if hasattr(module, "state_index_verdict") and hasattr(
            module, "load_expected_gdn_inventory"
        ):
            return module
        module = getattr(module, "trial", None)
    raise RuntimeError("cannot locate DASC state-index evidence controller")


state_trial = _find_state_trial(trial)
state_trial.EXPECTED_REPRESENTATIVE_LAYERS = 48


def _event_key(row: dict) -> tuple:
    return (
        row.get("pid"),
        row.get("layer"),
        row.get("state_index"),
        row.get("source_block_id"),
        row.get("destination_block_id"),
    )


def _expected_layer_names(expected_inventory: dict) -> set[str]:
    return {
        f"language_model.model.layers.{layer_id}.linear_attn"
        for layer_id in expected_inventory["gdn_layer_ids"]
    }


def full_layer_state_verdict(
    rows: list[dict],
    numerical: dict | None,
    *,
    expected_inventory: dict,
) -> dict:
    expected_layers = _expected_layer_names(expected_inventory)
    expected_pairs = {
        (layer, state_index)
        for layer in expected_layers
        for state_index in EXPECTED_STATE_INDICES
    }
    expected_key_count = (
        EXPECTED_TP_WORKERS * len(expected_layers) * len(EXPECTED_STATE_INDICES)
    )
    copies = [
        row
        for row in rows
        if row.get("event") == "physical_state_copy_materialized"
    ]
    before_rows = [
        row
        for row in rows
        if row.get("event") == "first_resumed_token_state_boundary_before"
    ]
    after_rows = [
        row
        for row in rows
        if row.get("event") == "first_resumed_token_state_boundary_after"
    ]
    copy_mappings = [
        row
        for row in rows
        if row.get("event") == "gdn_running_state_indices_remapped"
        and row.get("copy_remap_active") is True
    ]

    exact_copies = [
        row
        for row in copies
        if row.get("diagnostic_scope") == "all_gdn_layers"
        and row.get("copy_bytes", 0) > 0
        and row.get("source_pointer_block_id") == row.get("source_block_id")
        and row.get("source_after_copy", {}).get("full_sha256")
        == row.get("destination_after_copy", {}).get("full_sha256")
    ]
    copy_by_key = {_event_key(row): row for row in exact_copies}
    before_by_key = {_event_key(row): row for row in before_rows}
    after_by_key = {_event_key(row): row for row in after_rows}
    copy_keys = set(copy_by_key)
    before_keys = set(before_by_key)
    after_keys = set(after_by_key)
    worker_pids = sorted({key[0] for key in copy_keys})
    coverage_by_pid = {
        pid: {(key[1], key[2]) for key in copy_keys if key[0] == pid}
        for pid in worker_pids
    }

    valid_mapping_pids = set()
    for row in copy_mappings:
        representative = row.get("representative_layers") or []
        layer_names = {layer.get("layer") for layer in representative}
        mappings_are_exact = all(
            layer.get("normalized_source_state_indices")
            and layer.get("destination_state_indices")
            and len(layer["normalized_source_state_indices"])
            == len(layer["destination_state_indices"])
            and layer["normalized_source_state_indices"]
            != layer["destination_state_indices"]
            for layer in representative
        )
        if (
            row.get("layer_count") == len(expected_layers)
            and layer_names == expected_layers
            and mappings_are_exact
        ):
            valid_mapping_pids.add(row.get("pid"))

    boundary_metadata_exact = all(
        row.get("normalized_source_state_indices")
        and row.get("destination_state_indices")
        and all(
            value == row.get("source_block_id")
            for value in row["normalized_source_state_indices"]
        )
        and all(
            value == row.get("destination_block_id")
            for value in row["destination_state_indices"]
        )
        and row.get("source_block_id") != row.get("destination_block_id")
        for row in before_rows
    )
    source_unchanged = all(
        before_by_key[key].get("source_before_native", {}).get("full_sha256")
        == after_by_key[key].get("source_after_native", {}).get("full_sha256")
        for key in copy_keys.intersection(before_keys, after_keys)
    )
    destination_updated = all(
        before_by_key[key].get("destination_before_native", {}).get(
            "full_sha256"
        )
        != after_by_key[key].get("destination_after_native", {}).get(
            "full_sha256"
        )
        for key in copy_keys.intersection(before_keys, after_keys)
    )

    checks = {
        "four_tp_workers": len(worker_pids) == EXPECTED_TP_WORKERS,
        "exact_copy_count": (
            len(copies) == len(exact_copies) == len(copy_by_key) == expected_key_count
        ),
        "canonical_layer_state_cartesian_coverage": (
            len(worker_pids) == EXPECTED_TP_WORKERS
            and all(coverage_by_pid[pid] == expected_pairs for pid in worker_pids)
        ),
        "copy_mapping_covers_every_canonical_layer": (
            len(valid_mapping_pids) == EXPECTED_TP_WORKERS
        ),
        "one_before_and_after_pair_per_copy": (
            copy_keys == before_keys == after_keys
            and len(before_rows) == len(before_by_key) == expected_key_count
            and len(after_rows) == len(after_by_key) == expected_key_count
        ),
        "boundary_metadata_matches_copy_rows": (
            len(before_rows) == expected_key_count and boundary_metadata_exact
        ),
        "old_source_rows_unchanged": (
            len(copy_keys) == expected_key_count and source_unchanged
        ),
        "every_destination_row_updated": (
            len(copy_keys) == expected_key_count and destination_updated
        ),
    }
    row_gate_ok = all(checks.values())
    numerical_ok = None if numerical is None else numerical.get("ok") is True
    if not row_gate_ok:
        decision = "full_layer_state_boundary_failed"
    elif numerical_ok is False:
        decision = "full_layer_state_boundary_passed_numerical_failed"
    elif numerical_ok is True:
        decision = "full_layer_state_boundary_and_numerical_passed"
    else:
        decision = "full_layer_state_boundary_passed_numerical_missing"
    return {
        "schema": "mst.dasc.v12r30-full-layer-state-boundary/v1",
        "expected": {
            "tp_workers": EXPECTED_TP_WORKERS,
            "gdn_layers": len(expected_layers),
            "state_indices": sorted(EXPECTED_STATE_INDICES),
            "exact_keys": expected_key_count,
            "layer_names": sorted(expected_layers),
            "checkpoint_inventory": expected_inventory,
        },
        "event_counts": {
            "physical_state_copy_materialized": len(copies),
            "first_resumed_token_state_boundary_before": len(before_rows),
            "first_resumed_token_state_boundary_after": len(after_rows),
            "copy_active_mapping_events": len(copy_mappings),
        },
        "checks": checks,
        "worker_pids": worker_pids,
        "valid_mapping_worker_pids": sorted(valid_mapping_pids),
        "exact_copy_key_count": len(copy_keys),
        "row_gate_ok": row_gate_ok,
        "numerical_canary_available": numerical is not None,
        "numerical_canary_ok": numerical_ok,
        "overall_ok": row_gate_ok and numerical_ok is True,
        "decision": decision,
    }


def validate_full_layer_evidence() -> dict:
    evidence_path = controller.RESULT / "evidence.jsonl"
    rows = [
        json.loads(line)
        for line in evidence_path.read_text(encoding="utf-8").splitlines()
    ]
    numerical_path = controller.RESULT / "physical-canary.json"
    numerical = (
        json.loads(numerical_path.read_text(encoding="utf-8"))
        if numerical_path.is_file()
        else None
    )
    result = full_layer_state_verdict(
        rows,
        numerical,
        expected_inventory=state_trial.load_expected_gdn_inventory(),
    )
    controller.atomic_json(
        controller.RESULT / "full-layer-state-verdict.json", result
    )
    state_trial.refresh_artifact_manifest()
    if not result["row_gate_ok"]:
        raise RuntimeError(
            "v12r30 full-layer state evidence failed: " + result["decision"]
        )
    return result


def preserve_full_layer_verdict_after_failure() -> None:
    if not (controller.RESULT / "evidence.jsonl").is_file():
        return
    try:
        validate_full_layer_evidence()
    except Exception as error:
        (controller.RESULT / "full-layer-state-verdict-error.txt").write_text(
            repr(error) + "\n", encoding="utf-8"
        )
        state_trial.refresh_artifact_manifest()


def main() -> int:
    try:
        exit_code = trial.main()
    except BaseException:
        preserve_full_layer_verdict_after_failure()
        raise
    if "--preflight-only" in sys.argv:
        return exit_code
    if (controller.RESULT / "evidence.jsonl").is_file():
        validate_full_layer_evidence()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
