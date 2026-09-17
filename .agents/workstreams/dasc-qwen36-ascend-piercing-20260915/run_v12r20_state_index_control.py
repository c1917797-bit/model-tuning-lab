#!/usr/bin/env python3
"""All-head state-row control for the first cache-hit resumed token."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r19_trial", HERE / "run_v12r19_branch_evidence_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r19 branch-evidence controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "state-index-all-heads-v12r20"
)
controller.CONTAINER = "dasc_qwen36_state_index_v12r20_20260917"
controller.PLUGIN_MODE = "physical-cache-native-all-heads-state-index"


def _event_key(row: dict) -> tuple:
    return (
        row.get("pid"),
        row.get("layer"),
        row.get("state_index"),
        row.get("source_block_id"),
        row.get("destination_block_id"),
    )


def state_index_verdict(rows: list[dict], numerical: dict | None) -> dict:
    copies = [
        row
        for row in rows
        if row.get("event") == "physical_state_copy_materialized"
    ]
    mappings = [
        row
        for row in rows
        if row.get("event") == "gdn_running_state_indices_remapped"
    ]
    before = {
        _event_key(row): row
        for row in rows
        if row.get("event") == "first_resumed_token_state_boundary_before"
    }
    after = {
        _event_key(row): row
        for row in rows
        if row.get("event") == "first_resumed_token_state_boundary_after"
    }

    copy_exact = [
        row
        for row in copies
        if row.get("source_pointer_block_id") == row.get("source_block_id")
        and row.get("source_after_copy", {}).get("full_sha256")
        == row.get("destination_after_copy", {}).get("full_sha256")
        and row.get("copy_bytes", 0) > 0
    ]
    changed_mappings = []
    for row in mappings:
        representative = row.get("representative_layers") or []
        if any(
            layer.get("source_state_indices")
            != layer.get("destination_state_indices")
            for layer in representative
        ):
            changed_mappings.append(row)

    matched_keys = sorted(set(before).intersection(after))
    source_unchanged = []
    destination_changed = []
    for key in matched_keys:
        before_row = before[key]
        after_row = after[key]
        if (
            before_row.get("source_before_native", {}).get("full_sha256")
            == after_row.get("source_after_native", {}).get("full_sha256")
        ):
            source_unchanged.append(key)
        if (
            before_row.get("destination_before_native", {}).get(
                "full_sha256"
            )
            != after_row.get("destination_after_native", {}).get(
                "full_sha256"
            )
        ):
            destination_changed.append(key)

    copy_pids = sorted({row.get("pid") for row in copy_exact})
    mapping_pids = sorted({row.get("pid") for row in changed_mappings})
    boundary_pids = sorted({key[0] for key in matched_keys})
    destination_change_pids = sorted({key[0] for key in destination_changed})
    checks = {
        "copy_materialized_exactly_on_all_four_tp_workers": len(copy_pids) == 4,
        "state_index_changed_on_all_four_tp_workers": len(mapping_pids) == 4,
        "before_after_boundary_pairs_on_all_four_tp_workers": (
            len(boundary_pids) == 4 and bool(matched_keys)
        ),
        "old_source_rows_unchanged": (
            bool(matched_keys) and len(source_unchanged) == len(matched_keys)
        ),
        "destination_rows_updated_on_all_four_tp_workers": (
            len(destination_change_pids) == 4
        ),
    }
    row_gate_ok = all(checks.values())
    numerical_ok = None if numerical is None else numerical.get("ok") is True
    if not checks["copy_materialized_exactly_on_all_four_tp_workers"]:
        decision = "physical_copy_missing_or_not_exact"
    elif not checks["state_index_changed_on_all_four_tp_workers"]:
        decision = "running_state_index_not_changed_on_all_workers"
    elif not checks["before_after_boundary_pairs_on_all_four_tp_workers"]:
        decision = "first_resumed_token_boundary_missing"
    elif not checks["old_source_rows_unchanged"]:
        decision = "native_execution_still_mutated_old_source_row"
    elif not checks["destination_rows_updated_on_all_four_tp_workers"]:
        decision = "native_execution_did_not_update_destination_row"
    elif numerical_ok is False:
        decision = "state_row_fix_executed_but_numerical_canary_failed"
    elif numerical_ok is True:
        decision = "state_row_fix_and_numerical_canary_passed"
    else:
        decision = "state_row_fix_executed_but_numerical_result_missing"

    return {
        "schema": "mst.dasc.v12r20-state-index/v1",
        "event_counts": {
            "physical_state_copy_materialized": len(copies),
            "gdn_running_state_indices_remapped": len(mappings),
            "first_resumed_token_state_boundary_before": len(before),
            "first_resumed_token_state_boundary_after": len(after),
        },
        "checks": checks,
        "copy_worker_pids": copy_pids,
        "mapping_worker_pids": mapping_pids,
        "boundary_worker_pids": boundary_pids,
        "destination_change_worker_pids": destination_change_pids,
        "matched_boundary_count": len(matched_keys),
        "row_gate_ok": row_gate_ok,
        "numerical_canary_available": numerical is not None,
        "numerical_canary_ok": numerical_ok,
        "overall_ok": row_gate_ok and numerical_ok is True,
        "decision": decision,
    }


def refresh_artifact_manifest() -> None:
    manifest = controller.RESULT / "artifacts.sha256.json"
    files = {
        str(path.relative_to(controller.RESULT)): controller.sha256(path)
        for path in controller.RESULT.rglob("*")
        if path.is_file() and path != manifest
    }
    controller.atomic_json(manifest, files)


def validate_state_index_evidence() -> dict:
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
    result = state_index_verdict(rows, numerical)
    controller.atomic_json(controller.RESULT / "state-index-verdict.json", result)
    refresh_artifact_manifest()
    if not result["row_gate_ok"]:
        raise RuntimeError(f"v12r20 state-row evidence failed: {result['decision']}")
    return result


def preserve_state_index_verdict_after_failure() -> None:
    if not (controller.RESULT / "evidence.jsonl").is_file():
        return
    try:
        validate_state_index_evidence()
    except Exception as error:
        (controller.RESULT / "state-index-verdict-error.txt").write_text(
            repr(error) + "\n", encoding="utf-8"
        )
        refresh_artifact_manifest()


def main() -> int:
    try:
        exit_code = trial.main()
    except BaseException:
        preserve_state_index_verdict_after_failure()
        raise
    if "--preflight-only" in sys.argv:
        return exit_code
    if (controller.RESULT / "evidence.jsonl").is_file():
        validate_state_index_evidence()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
