"""One-card dynamic-A8W4 numerical and local-cost gate, not a service result."""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--physical-npu", required=True, type=int)
    args = parser.parse_args()
    destination = Path(args.output_file)
    if args.physical_npu != 4 or not destination.parent.is_dir() or destination.exists():
        raise ValueError("requires physical NPU4 and a new result file")
    report = {
        "schema": "qqq-a8w4-dynamic-pipeline/v4",
        "scope": "per-token quantization plus native A8W4 operator only; local timing is not E2E QQQ benefit",
        "physical_npu_declared": 4,
        "status": "started",
        "numeric_gate": {"quant_oracle_relative_rms_max": 0.01, "replay_relative_rms_max": 0.0001},
    }
    try:
        torch.npu.set_device(0)
        if torch.npu.device_count() != 1:
            raise RuntimeError("expected exactly one visible NPU")
        torch.manual_seed(20260928)
        m, k, n = 16, 5120, 8704
        report["shape"] = {"M": m, "K": k, "N": n}
        x_cpu = (torch.randn(m, k) * 0.25).bfloat16()
        q_w_cpu = torch.randint(-7, 8, (k, n), dtype=torch.int32)
        s_w_cpu = torch.full((n,), 1 / 64, dtype=torch.float32)
        y_offset_cpu = 8 * q_w_cpu.float().sum(0) * s_w_cpu
        x = x_cpu.npu()
        packed = torch_npu.npu_convert_weight_to_int4pack(q_w_cpu.npu())
        s_w = torch_npu.npu_trans_quant_param(s_w_cpu.npu())
        y_offset = y_offset_cpu.npu()
        dense_weight = (q_w_cpu.float() * s_w_cpu[None, :]).bfloat16().npu()

        q_probe, s_probe = torch_npu.npu_dynamic_quant(x)
        torch.npu.synchronize()
        q_cpu = q_probe.cpu().clone()
        s_cpu = s_probe.cpu().float().reshape(m).clone()
        report["dynamic_quant"] = {
            "activation_dtype": str(q_probe.dtype),
            "scale_dtype": str(s_probe.dtype),
            "scale_shape": list(s_probe.shape),
            "scale_min": float(s_cpu.min().item()),
            "scale_max": float(s_cpu.max().item()),
            "activation_reconstruction_relative_rms": float(
                (((q_cpu.float() * s_cpu[:, None] - x_cpu.float()).square().mean())
                 / x_cpu.float().square().mean().clamp_min(1e-20)).sqrt().item()
            ),
        }
        quant_oracle = (
            (q_cpu.float() @ q_w_cpu.float()) * s_cpu[:, None] * s_w_cpu[None, :]
        ).bfloat16()

        def candidate() -> torch.Tensor:
            q, scale = torch_npu.npu_dynamic_quant(x)
            return torch_npu.npu_quant_matmul(
                q,
                packed,
                s_w,
                offset=y_offset,
                pertoken_scale=scale.reshape(m),
                output_dtype=torch.bfloat16,
            )

        def dense() -> torch.Tensor:
            return x @ dense_weight

        first = candidate()
        torch.npu.synchronize()
        first_cpu = first.cpu().clone()
        second = candidate()
        torch.npu.synchronize()
        second_cpu = second.cpu().clone()
        dense_cpu = dense().cpu()
        report["candidate_vs_quant_oracle"] = comparison(first_cpu, quant_oracle)
        report["candidate_vs_bf16_dense"] = comparison(first_cpu, dense_cpu)
        report["candidate_eager_repeat"] = comparison(second_cpu, first_cpu)
        report["source_bf16_unchanged"] = bool(torch.equal(x.cpu(), x_cpu))
        report["finite"] = bool(torch.isfinite(first_cpu).all().item())

        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_output = candidate()
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        replay_first = graph_output.cpu().clone()
        graph.replay()
        torch.npu.synchronize()
        replay_second = graph_output.cpu().clone()
        report["graph_vs_eager"] = comparison(replay_first, first_cpu)
        report["graph_repeat"] = comparison(replay_second, replay_first)
        report["source_bf16_unchanged_after_graph"] = bool(torch.equal(x.cpu(), x_cpu))
        report["numeric_gate_passed"] = bool(
            report["finite"] and report["source_bf16_unchanged_after_graph"]
            and report["candidate_vs_quant_oracle"]["relative_rms"] <= 0.01
            and all(report[key]["relative_rms"] <= 0.0001 for key in
                    ("candidate_eager_repeat", "graph_vs_eager", "graph_repeat"))
        )
        if not report["numeric_gate_passed"]:
            report["status"] = "numeric_gate_failed"
            raise AssertionError("dynamic-A8W4 pipeline numerical gate failed")

        candidate_ms = time_calls(candidate, warmups=5, calls=20, rounds=3)
        dense_ms = time_calls(dense, warmups=5, calls=20, rounds=3)
        report["local_operator_sequence_timing"] = {
            "candidate_ms_per_call": candidate_ms,
            "bf16_ms_per_call": dense_ms,
            "median_dense_over_candidate": statistics.median(dense_ms) / statistics.median(candidate_ms),
            "warning": "diagnostic operator sequence, not critical path or E2E throughput",
        }
        report["status"] = "passed_local_gate"
    except Exception:
        if report["status"] == "started":
            report["status"] = "failed"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w") as file:
            json.dump(report, file, indent=2, sort_keys=True)
            file.write("\n")


if __name__ == "__main__":
    main()
