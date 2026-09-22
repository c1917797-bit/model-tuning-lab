#!/usr/bin/env python3
"""NPU bridge gate: deferred DeltaLog state into native mixed-batch decode."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import torch
import torch_npu  # noqa: F401 - registers the NPU backend

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugin"))
from qwen36_deltalog_plugin.patch import _flush_slots  # noqa: E402
from deltalog_candidate_npu_probe import (  # noqa: E402
    allocate_state,
    candidate_step,
    make_inputs,
    materialize_selected,
    native_step,
    normalized_max_error,
    relative_l2,
)

OUTPUT_LIMIT = 0.00303
STATE_LIMIT = 7.92e-7


def _clone_state(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {name: tensor.clone() for name, tensor in state.items()}


def _bridge(state: dict[str, torch.Tensor], indices: torch.Tensor) -> None:
    layer = SimpleNamespace(kv_cache=(None, state["base"]), prefix="mixed-fallback-probe")
    _flush_slots(torch, layer, state, indices, "not_pure_decode")


def _case(batch: int, graph_mode: bool) -> dict[str, object]:
    slots = batch + 4
    generator = torch.Generator().manual_seed(260815533 + batch)
    initial = (torch.randn((slots, 12, 128, 128), generator=generator) * 0.005).float()
    candidate = allocate_state(initial)
    native = initial.to("npu:0")
    seq = torch.cat((torch.zeros(1, dtype=torch.int32),
                     torch.ones(batch, dtype=torch.int32))).to("npu:0")
    for step in range(5):
        inputs = make_inputs(batch, slots, step, generator)
        candidate_step(candidate, inputs, seq)
        native_step(native, inputs, seq)
    torch.npu.synchronize()

    # Include both live and unused slots; the latter must remain untouched.
    selected = inputs["indices"][: max(1, batch // 2)].clone()
    selected64 = selected.long()
    logical_before = materialize_selected(candidate, selected64).clone()
    native_before = native.index_select(0, selected64).clone()
    original = _clone_state(candidate)
    pointers = {name: tensor.untyped_storage().data_ptr()
                for name, tensor in candidate.items()}

    if graph_mode:
        warm = _clone_state(candidate)
        for _ in range(2):
            _bridge(warm, selected)
            torch.npu.synchronize()
            for name in warm:
                warm[name].copy_(original[name])
            torch.npu.synchronize()
        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            _bridge(candidate, selected)
        torch.npu.synchronize()
        for name in candidate:
            candidate[name].copy_(original[name])
        torch.npu.synchronize()
        graph.replay()
    else:
        _bridge(candidate, selected)
    torch.npu.synchronize()

    base_error = relative_l2(candidate["base"].index_select(0, selected64), logical_before)
    native_error = relative_l2(candidate["base"].index_select(0, selected64), native_before)
    chosen = torch.zeros(slots, dtype=torch.bool, device="npu:0")
    chosen.index_fill_(0, selected64, True)
    untouched = bool(all(torch.equal(candidate[name][~chosen], original[name][~chosen])
                         for name in candidate))
    metadata_zero = bool(all(torch.count_nonzero(candidate[name].index_select(0, selected64)) == 0
                             for name in ("decay", "length")))
    payload_untouched = bool(all(torch.equal(candidate[name].index_select(0, selected64),
                                            original[name].index_select(0, selected64))
                                 for name in ("k_log", "u_log", "lambda_log")))
    pointer_stable = pointers == {name: tensor.untyped_storage().data_ptr()
                                  for name, tensor in candidate.items()}
    finite = bool(torch.isfinite(candidate["base"]).all())
    follow = make_inputs(batch, slots, 6, generator)
    follow["indices"] = selected
    follow = {name: tensor[: selected.numel()] if name != "indices" else tensor
              for name, tensor in follow.items()}
    follow_seq = torch.cat((torch.zeros(1, dtype=torch.int32),
                            torch.ones(selected.numel(), dtype=torch.int32))).to("npu:0")
    actual = native_step(candidate["base"], follow, follow_seq)
    expected = native_step(native, follow, follow_seq)
    torch.npu.synchronize()
    output_error = normalized_max_error(actual, expected)
    passed = (base_error <= 1e-7 and native_error <= STATE_LIMIT
              and output_error <= OUTPUT_LIMIT and untouched and metadata_zero
              and payload_untouched
              and pointer_stable and finite)
    return {"batch": batch, "mode": "npugraph" if graph_mode else "eager",
            "selected_slots": int(selected.numel()), "base_relative_l2": base_error,
            "native_state_relative_l2": native_error,
            "next_output_normalized_error": output_error,
            "untouched_slots_bitwise": untouched, "selected_metadata_zero": metadata_zero,
            "selected_payload_unchanged": payload_untouched,
            "storage_pointers_stable": pointer_stable, "finite": finite,
            "passed": passed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    library = args.library.resolve(strict=True)
    torch.ops.load_library(str(library))
    cases = [_case(batch, graph_mode) for graph_mode in (False, True)
             for batch in (1, 16)]
    report = {"schema": "qwen36-deltalog-mixed-fallback-gate/v1",
              "library": str(library),
              "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
              "device": "container npu:0; physical mapping must be proven externally",
              "cases": cases, "passed": all(case["passed"] for case in cases)}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
