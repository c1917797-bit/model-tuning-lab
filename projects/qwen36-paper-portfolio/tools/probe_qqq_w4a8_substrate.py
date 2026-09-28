"""One-card native INT4 matmul gate; not a QQQ or service benchmark."""
import argparse
import json
import os
import statistics
import traceback
from pathlib import Path

import torch
import torch_npu


def rel_rms(a, b):
    a, b = a.float(), b.float()
    return float(((a - b).square().mean() / b.square().mean().clamp_min(1e-20)).sqrt().item())


def time_calls(fn, warmups, calls, rounds):
    for _ in range(warmups):
        fn()
    torch.npu.synchronize()
    samples = []
    for _ in range(rounds):
        start = torch.npu.Event(enable_timing=True)
        end = torch.npu.Event(enable_timing=True)
        start.record()
        for _ in range(calls):
            fn()
        end.record()
        torch.npu.synchronize()
        samples.append(float(start.elapsed_time(end)) / calls)
    return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-file", required=True)
    ap.add_argument("--physical-npu", type=int, required=True)
    ap.add_argument("--warmups", type=int, default=10)
    ap.add_argument("--calls", type=int, default=60)
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()
    path = Path(args.output_file)
    if args.physical_npu not in range(4, 8) or not path.parent.is_dir() or path.exists():
        raise ValueError("invalid physical NPU or result destination")
    result = {
        "schema": "qqq-native-substrate/v1",
        "scope": "synthetic real-shape operator investment gate, not QQQ, E2E, or task accuracy",
        "physical_npu_declared": args.physical_npu,
        "status": "started",
    }
    try:
        torch.npu.set_device(0)
        visible = torch.npu.device_count()
        if visible != 1:
            raise RuntimeError(f"expected one visible NPU, got {visible}")
        torch.manual_seed(20260928)
        device = "npu:0"
        m, k, n, group = 16, 5120, 8704, 128
        x = (torch.randn(m, k, device=device) * 0.25).bfloat16()
        w = torch.randint(-7, 8, (k, n), device=device, dtype=torch.int32)
        scale = torch.full((k // group, n), 1 / 64, device=device, dtype=torch.bfloat16)
        packed = torch_npu.npu_convert_weight_to_int4pack(w)
        dense_w = (w.reshape(k // group, group, n).bfloat16() * scale[:, None, :]).reshape(k, n)
        quant = lambda: torch_npu.npu_weight_quant_batchmatmul(
            x, packed, antiquant_scale=scale, antiquant_group_size=group
        )
        dense = lambda: x @ dense_w
        q, d = quant(), dense()
        torch.npu.synchronize()
        error = rel_rms(q, d)
        result.update(
            shape={"M": m, "K": k, "N": n, "group": group},
            packed_dtype=str(packed.dtype),
            eager_vs_dequant_bf16_relative_rms=error,
            finite=bool(torch.isfinite(q).all().item()),
            torch_npu_version=torch_npu.__version__,
        )
        if not result["finite"] or error > 0.01:
            raise AssertionError(f"native quantized-output mismatch: {error}")
        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_y = quant()
        torch.npu.synchronize()
        x_new = (torch.randn(m, k, device=device) * 0.25).bfloat16()
        x.copy_(x_new)
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        replay = graph_y.clone()
        eager = quant()
        torch.npu.synchronize()
        result["graph_vs_eager_bitwise"] = bool(torch.equal(replay, eager))
        result["graph_vs_eager_relative_rms"] = rel_rms(replay, eager)
        if not result["graph_vs_eager_bitwise"]:
            raise AssertionError("native graph/eager mismatch")
        q_ms = time_calls(quant, args.warmups, args.calls, args.rounds)
        d_ms = time_calls(dense, args.warmups, args.calls, args.rounds)
        result.update(
            status="passed",
            quant_ms_per_call=q_ms,
            bf16_ms_per_call=d_ms,
            local_ratio_bf16_over_quant=statistics.median(d_ms) / statistics.median(q_ms),
        )
    except Exception:
        result["status"] = "failed"
        result["traceback"] = traceback.format_exc()
        raise
    finally:
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w") as file:
            json.dump(result, file, indent=2, sort_keys=True)
            file.write("\n")


if __name__ == "__main__":
    main()
