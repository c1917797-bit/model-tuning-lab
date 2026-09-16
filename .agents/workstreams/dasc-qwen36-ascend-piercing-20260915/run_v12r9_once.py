#!/usr/bin/env python3
"""Explicit-dummy-scope successor; software checks are not NPU proof."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import json

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dasc_v12r9_engine", HERE / "run_v12r6_once.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC controller")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)
controller.RESULT = Path("/cache/cch/dasc-qwen36-ascend-20260915/request-owned-dummy-scope-v12r9")
controller.CONTAINER = "dasc_qwen36_dummy_scope_v12r9_20260916"
controller.SUPERSEDED_REASON = None
controller.BLOCK_ON_IDLE_CONTAINER_CLAIMS = False
original_validate = controller.validate_allocation_evidence


def validate_layer_cohorts(rows, *, expected_ranks=4, expected_layers=48):
    events = ("physical_cache_bound", "request_active_state_initialized", "request_active_state_continued")
    cohorts = {event: {} for event in events}
    for row in rows:
        event = row.get("event")
        if event not in cohorts:
            continue
        pid, layer = row.get("pid"), row.get("layer")
        if not isinstance(pid, int) or not isinstance(layer, str) or not layer:
            raise ValueError("missing PID/layer identity in lifecycle evidence")
        layers = cohorts[event].setdefault(pid, set())
        if layer in layers:
            raise ValueError("duplicate PID/layer lifecycle evidence")
        layers.add(layer)
    physical = cohorts[events[0]]
    if len(physical) != expected_ranks:
        raise ValueError("incomplete TP rank coverage")
    layer_sets = list(physical.values())
    if any(len(layers) != expected_layers for layers in layer_sets):
        raise ValueError("incomplete linear-layer coverage")
    if any(layers != layer_sets[0] for layers in layer_sets):
        raise ValueError("TP ranks disagree on layer identities")
    for event in events[1:]:
        if cohorts[event] != physical:
            raise ValueError(f"incomplete per-layer lifecycle coverage: {event}")
    return {"ok": True, "rank_count": len(physical), "layers_per_rank": expected_layers}


def validate_allocation_evidence():
    original_validate()
    rows = [json.loads(line) for line in (controller.RESULT / "evidence.jsonl").read_text().splitlines()]
    try:
        result = validate_layer_cohorts(rows)
    except ValueError as error:
        controller.atomic_json(controller.RESULT / "layer-lifecycle-coverage.json", {"ok": False, "error": str(error)})
        raise
    controller.atomic_json(controller.RESULT / "layer-lifecycle-coverage.json", result)


controller.validate_allocation_evidence = validate_allocation_evidence


def main():
    subprocess.run(["/usr/bin/git", "merge-base", "--is-ancestor", "8899d8d", "HEAD"], cwd=controller.REPO, check=True)
    return controller.main()


if __name__ == "__main__":
    raise SystemExit(main())
