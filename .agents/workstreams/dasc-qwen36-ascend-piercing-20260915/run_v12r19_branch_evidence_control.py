#!/usr/bin/env python3
"""All-head control with bounded scheduler and Mamba branch evidence."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r18_trial", HERE / "run_v12r18_mixed_lifecycle_fix_control.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r18 lifecycle controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "branch-evidence-all-heads-v12r19"
)
controller.CONTAINER = "dasc_qwen36_branch_evidence_v12r19_20260917"
controller.PLUGIN_MODE = "physical-cache-native-all-heads"


def branch_evidence_verdict(rows: list[dict], numerical: dict | None) -> dict:
    initialized = [
        row
        for row in rows
        if row.get("event") == "scheduler_mamba_lifecycle_initialized"
    ]
    splits = [
        row
        for row in rows
        if row.get("event") == "scheduler_mamba_aligned_split_executed"
    ]
    zeroing = [
        row
        for row in rows
        if row.get("event") == "scheduler_kv_zeroing_branch_executed"
    ]
    copies = [
        row
        for row in rows
        if row.get("event") == "heterogeneous_mamba_copy_branch_executed"
    ]

    valid_initialization = [
        row
        for row in initialized
        if row.get("has_mamba_layers") is True
        and row.get("need_mamba_block_aligned_split") is True
        and row.get("needs_kv_cache_zeroing") is True
        and isinstance(row.get("block_size"), int)
        and row["block_size"] > 0
    ]
    block_sizes = {row["block_size"] for row in valid_initialization}
    material_splits = [
        row
        for row in splits
        if row.get("changed") is True
        and isinstance(row.get("requested_tokens"), int)
        and isinstance(row.get("scheduled_tokens"), int)
        and 0 < row["scheduled_tokens"] < row["requested_tokens"]
        and any(row["scheduled_tokens"] % size == 0 for size in block_sizes)
    ]
    nonempty_zeroing = [
        row
        for row in zeroing
        if row.get("nonempty") is True
        and isinstance(row.get("new_block_count"), int)
        and row["new_block_count"] > 0
    ]
    valid_copies = [
        row
        for row in copies
        if isinstance(row.get("pid"), int)
        and isinstance(row.get("mamba_layer_count"), int)
        and row["mamba_layer_count"] > 0
        and isinstance(row.get("copy_entries_added"), int)
        and row["copy_entries_added"] > 0
    ]
    copy_pids = sorted({row["pid"] for row in valid_copies})

    checks = {
        "scheduler_initialized_with_all_lifecycle_flags": bool(valid_initialization),
        "aligned_split_materially_changed_to_block_boundary": bool(material_splits),
        "zeroing_branch_produced_nonempty_block_set": bool(nonempty_zeroing),
        "mamba_copy_branch_covered_all_four_tp_workers": len(copy_pids) == 4,
    }
    branch_ok = all(checks.values())
    numerical_ok = None if numerical is None else numerical.get("ok") is True
    if not checks["scheduler_initialized_with_all_lifecycle_flags"]:
        decision = "scheduler_lifecycle_initialization_missing_or_invalid"
    elif not checks["aligned_split_materially_changed_to_block_boundary"]:
        decision = "aligned_split_branch_missing_or_not_material"
    elif not checks["zeroing_branch_produced_nonempty_block_set"]:
        decision = "zeroing_branch_missing_or_empty"
    elif not checks["mamba_copy_branch_covered_all_four_tp_workers"]:
        decision = "mamba_copy_branch_missing_or_incomplete_tp_coverage"
    elif numerical_ok is False:
        decision = (
            "lifecycle_branches_executed_but_numerical_canary_failed_"
            "localize_physical_rows_and_first_resumed_token"
        )
    elif numerical_ok is True:
        decision = "lifecycle_and_numerical_canary_passed"
    else:
        decision = "lifecycle_branches_executed_but_numerical_result_missing"

    return {
        "schema": "mst.dasc.v12r19-branch-evidence/v1",
        "event_counts": {
            "scheduler_mamba_lifecycle_initialized": len(initialized),
            "scheduler_mamba_aligned_split_executed": len(splits),
            "scheduler_kv_zeroing_branch_executed": len(zeroing),
            "heterogeneous_mamba_copy_branch_executed": len(copies),
        },
        "checks": checks,
        "block_sizes": sorted(block_sizes),
        "material_split_count": len(material_splits),
        "nonempty_zeroing_count": len(nonempty_zeroing),
        "mamba_copy_worker_pids": copy_pids,
        "branch_evidence_ok": branch_ok,
        "numerical_canary_available": numerical is not None,
        "numerical_canary_ok": numerical_ok,
        "overall_ok": branch_ok and numerical_ok is True,
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


def validate_branch_evidence() -> dict:
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
    result = branch_evidence_verdict(rows, numerical)
    controller.atomic_json(controller.RESULT / "branch-evidence-verdict.json", result)
    refresh_artifact_manifest()
    if not result["branch_evidence_ok"]:
        raise RuntimeError(f"v12r19 branch evidence failed: {result['decision']}")
    return result


def preserve_branch_verdict_after_failure() -> None:
    if not (controller.RESULT / "evidence.jsonl").is_file():
        return
    try:
        validate_branch_evidence()
    except Exception as error:
        (controller.RESULT / "branch-evidence-verdict-error.txt").write_text(
            repr(error) + "\n", encoding="utf-8"
        )
        refresh_artifact_manifest()


def main() -> int:
    try:
        exit_code = trial.main()
    except BaseException:
        preserve_branch_verdict_after_failure()
        raise
    if "--preflight-only" in sys.argv:
        return exit_code
    if (controller.RESULT / "evidence.jsonl").is_file():
        validate_branch_evidence()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
