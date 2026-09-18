#!/usr/bin/env python3
"""One-variable all-head control that restores the dense cache-page padding."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r30_trial",
    HERE / "run_v12r30_full_layer_state_diagnostic.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r30 full-layer diagnostic")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-page-padding-identity-v12r31"
)
controller.CONTAINER = (
    "dasc_qwen36_dense_page_padding_identity_v12r31_20260918"
)
controller.PLUGIN_EXTRA_ENV = {
    "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
    "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
}
controller.CANARY_EXTRA_ARGS = ("--allow-dense-pages",)

EXPECTED_TP_WORKERS = 4
EXPECTED_GDN_LAYERS = 48


def dense_padding_verdict(rows: list[dict]) -> dict:
    physical = [
        row for row in rows if row.get("event") == "physical_cache_bound"
    ]
    keys = {(row.get("pid"), row.get("layer")) for row in physical}
    pids = sorted({row.get("pid") for row in physical})
    expected_rows = EXPECTED_TP_WORKERS * EXPECTED_GDN_LAYERS
    exact_rows = [
        row
        for row in physical
        if row.get("native_all_heads") is True
        and row.get("page_padding_preserved") is True
        and row.get("compact_page_bytes") == row.get("dense_page_bytes")
        and row.get("reserved_page_bytes") == row.get("dense_page_bytes")
        and isinstance(row.get("payload_page_bytes"), int)
        and isinstance(row.get("reserved_page_bytes"), int)
        and row["payload_page_bytes"] < row["reserved_page_bytes"]
        and row.get("padding_bytes_per_page")
        == row["reserved_page_bytes"] - row["payload_page_bytes"]
        and row.get("payload_fits_reserved_page") is True
        and row.get("allocation_matches_spec") is False
        and isinstance(row.get("num_blocks"), int)
        and row["num_blocks"] > 0
        and row.get("payload_bytes")
        == row["payload_page_bytes"] * row["num_blocks"]
        and row.get("reserved_bytes")
        == row["reserved_page_bytes"] * row["num_blocks"]
    ]
    checks = {
        "four_tp_workers": len(pids) == EXPECTED_TP_WORKERS,
        "exact_pid_layer_cartesian_rows": (
            len(physical) == len(keys) == expected_rows
        ),
        "every_row_preserves_dense_padding": len(exact_rows) == expected_rows,
    }
    return {
        "schema": "mst.dasc.v12r31-dense-page-padding-control/v1",
        "expected_tp_workers": EXPECTED_TP_WORKERS,
        "expected_gdn_layers": EXPECTED_GDN_LAYERS,
        "expected_physical_rows": expected_rows,
        "physical_rows": len(physical),
        "exact_rows": len(exact_rows),
        "worker_pids": pids,
        "checks": checks,
        "ok": all(checks.values()),
    }


def validate_dense_padding_evidence() -> dict:
    rows = [
        json.loads(line)
        for line in (controller.RESULT / "evidence.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    result = dense_padding_verdict(rows)
    controller.atomic_json(
        controller.RESULT / "dense-page-padding-verdict.json", result
    )
    trial.state_trial.refresh_artifact_manifest()
    if not result["ok"]:
        raise RuntimeError("v12r31 dense page-padding evidence failed")
    return result


controller.validate_allocation_evidence = validate_dense_padding_evidence


def preserve_dense_padding_verdict_after_failure() -> None:
    if not (controller.RESULT / "evidence.jsonl").is_file():
        return
    try:
        validate_dense_padding_evidence()
    except Exception as error:
        (controller.RESULT / "dense-page-padding-verdict-error.txt").write_text(
            repr(error) + "\n", encoding="utf-8"
        )
        trial.state_trial.refresh_artifact_manifest()


def main() -> int:
    try:
        exit_code = trial.main()
    except BaseException:
        preserve_dense_padding_verdict_after_failure()
        raise
    if "--preflight-only" in sys.argv:
        return exit_code
    if (controller.RESULT / "evidence.jsonl").is_file():
        validate_dense_padding_evidence()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
