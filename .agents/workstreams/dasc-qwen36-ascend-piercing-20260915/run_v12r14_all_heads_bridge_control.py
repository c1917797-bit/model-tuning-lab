#!/usr/bin/env python3
"""All-head control: exercise the DASC state bridge without pruning."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r11_trial", HERE / "run_v12r11_once.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r11 controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "request-owned-all-heads-control-v12r14"
)
controller.CONTAINER = "dasc_qwen36_all_heads_bridge_v12r14_20260916"
controller.W_MAX = "1e-9"


def all_heads_evidence_verdict(rows: list[dict]) -> dict:
    geometry = [row for row in rows if row.get("event") == "tp_geometry_aligned"]
    physical = [row for row in rows if row.get("event") == "physical_cache_bound"]
    geometry_ok = len(geometry) == 4 and all(
        row.get("extra_local_heads") == 0
        and len(row.get("local_counts", [])) == 48
        and set(row["local_counts"]) == {12}
        and row.get("common_counts") == row["local_counts"]
        for row in geometry
    )
    physical_ok = len(physical) == 192 and all(
        row.get("allocation_matches_spec") is True
        and row.get("actual_page_bytes") == row.get("compact_page_bytes")
        and row.get("compact_page_bytes") == row.get("dense_page_bytes")
        for row in physical
    )
    result = {
        "schema": "mst.dasc.all-heads-bridge-control/v1",
        "geometry_rows": len(geometry),
        "physical_rows": len(physical),
        "all_48_layers_retain_12_local_heads_on_4_ranks": geometry_ok,
        "persistent_page_equals_dense_page": physical_ok,
    }
    result["ok"] = geometry_ok and physical_ok
    return result


def validate_all_heads_evidence() -> None:
    rows = [
        json.loads(line)
        for line in (controller.RESULT / "evidence.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    result = all_heads_evidence_verdict(rows)
    controller.atomic_json(controller.RESULT / "all-heads-control.json", result)
    if not result["ok"]:
        raise RuntimeError("all-heads DASC bridge control evidence failed")


def main() -> int:
    exit_code = trial.main()
    if exit_code != 0:
        return exit_code
    validate_all_heads_evidence()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
