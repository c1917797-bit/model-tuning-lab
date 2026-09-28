"""Screen dynamic A8W4 graph cost by shape; never interpret as E2E gain."""

import argparse
import json
import os
import statistics
import traceback
from pathlib import Path

import torch
import torch_npu

from probe_qqq_a8w4_v5 import comparison
from probe_qqq_w4a8_substrate import time_calls


def measure_case(m, k, n, packed, scale, offset, dense_weight):
    x_cpu = (torch.randn(m, k) * 0.25).bfloat16()
    x = x_cpu.npu()

    def candidate():
        q, token_scale = torch_npu.npu_dynamic_quant(x)
        return torch_npu.npu_quant_matmul(
            q, packed, scale, offset=offset,
            pertoken_scale=token_scale.reshape(m), output_dtype=torch.bfloat16,
        )

    def dense():
        return x @ dense_weight

    eager_candidate = candidate().cpu().clone()
    eager_dense = dense().cpu().clone()
    graph_candidate = torch.npu.NPUGraph()
    with torch.npu.graph(graph_candidate):
        graph_candidate_output = candidate()
    graph_dense = torch.npu.NPUGraph()
    with torch.npu.graph(graph_dense):
        graph_dense_output = dense()
    torch.npu.synchronize()
    graph_candidate.replay()
    graph_dense.replay()
    torch.npu.synchronize()
    candidate_replay = graph_candidate_output.cpu().clone()
    dense_replay = graph_dense_output.cpu().clone()
    graph_candidate.replay()
    torch.npu.synchronize()
    candidate_replay_two = graph_candidate_output.cpu().clone()
    report = {
        "shape": {"M": m, "K": k, "N": n},
        "candidate_vs_dense": comparison(eager_candidate, eager_dense),
        "candidate_graph_vs_eager": comparison(candidate_replay, eager_candidate),
        "candidate_graph_repeat": comparison(candidate_replay_two, candidate_replay),
        "dense_graph_vs_eager": comparison(dense_replay, eager_dense),
        "source_activation_unchanged": bool(torch.equal(x.cpu(), x_cpu)),
    }
    report["numeric_screen_passed"] = bool(
        report["source_activation_unchanged"]
        and report["candidate_vs_dense"]["relative_rms"] <= 0.02
        and report["candidate_graph_vs_eager"]["relative_rms"] <= 0.0001
        and report["candidate_graph_repeat"]["relative_rms"] <= 0.0001
    )
    if not report["numeric_screen_passed"]:
        return report
    timings = {}
    for label, fn in (
        ("candidate_eager", candidate),
        ("dense_eager", dense),
        ("candidate_graph", graph_candidate.replay),
        ("dense_graph", graph_dense.replay),
    ):
        timings[label] = time_calls(fn, warmups=5, calls=20, rounds=3)
    report["local_timing_ms_per_call"] = timings
    report["median_dense_over_candidate_eager"] = (
        statistics.median(timings["dense_eager"]) / statistics.median(timings["candidate_eager"])
    )
    report["median_dense_over_candidate_graph"] = (
        statistics.median(timings["dense_graph"]) / statistics.median(timings["candidate_graph"])
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--physical-npu", required=True, type=int)
    args = parser.parse_args()
    destination = Path(args.output_file)
    if args.physical_npu != 4 or not destination.parent.is_dir() or destination.exists():
        raise ValueError("requires physical NPU4 and a new result file")
    report = {
        "schema": "qqq-a8w4-graph-cost/v5",
        "scope": "local synthetic shape investment gate only; no QQQ calibration, E2E, or task accuracy",
        "physical_npu_declared": 4,
        "status": "started",
    }
    try:
        torch.npu.set_device(0)
        if torch.npu.device_count() != 1:
            raise RuntimeError("expected exactly one visible NPU")
        torch.manual_seed(20260928)
        k, n = 5120, 8704
        q_w_cpu = torch.randint(-7, 8, (k, n), dtype=torch.int32)
        s_w_cpu = torch.full((n,), 1 / 64, dtype=torch.float32)
        packed = torch_npu.npu_convert_weight_to_int4pack(q_w_cpu.npu())
        scale = torch_npu.npu_trans_quant_param(s_w_cpu.npu())
        offset = (8 * q_w_cpu.float().sum(0) * s_w_cpu).npu()
        dense_weight = (q_w_cpu.float() * s_w_cpu[None, :]).bfloat16().npu()
        report["cases"] = [
            measure_case(m, k, n, packed, scale, offset, dense_weight)
            for m in (16, 256)
        ]
        report["status"] = "screened"
    except Exception:
        report["status"] = "failed"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w") as file:
            json.dump(report, file, indent=2, sort_keys=True)
            file.write("\n")


if __name__ == "__main__":
    main()
