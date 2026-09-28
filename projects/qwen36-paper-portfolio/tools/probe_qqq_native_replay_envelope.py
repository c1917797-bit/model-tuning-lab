"""Diagnose native eager/graph variation after the immutable v1 bitwise failure."""
import argparse
import json
import os
import traceback
from pathlib import Path

import torch
import torch_npu


def compare(a, b):
    a32, b32 = a.float(), b.float()
    diff = (a32 - b32).abs()
    return {
        "bitwise": bool(torch.equal(a, b)),
        "different_elements": int((a != b).sum().item()),
        "elements": a.numel(),
        "max_abs": float(diff.max().item()),
        "relative_rms": float((diff.square().mean() / b32.square().mean().clamp_min(1e-20)).sqrt().item()),
    }


def snapshot(fn):
    out = fn()
    torch.npu.synchronize()
    return out.clone()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-file", required=True)
    ap.add_argument("--physical-npu", type=int, required=True)
    args = ap.parse_args()
    path = Path(args.output_file)
    if args.physical_npu not in range(4, 8) or not path.parent.is_dir() or path.exists():
        raise ValueError("invalid physical NPU or result destination")
    result = {
        "schema": "qqq-native-replay-envelope/v1",
        "scope": "native stateless matmul numerical diagnostic only, no speed or QQQ claim",
        "physical_npu_declared": args.physical_npu,
        "status": "started",
    }
    try:
        torch.npu.set_device(0)
        if torch.npu.device_count() != 1:
            raise RuntimeError("exactly one visible NPU required")
        torch.manual_seed(20260928)
        m, k, n, group = 16, 5120, 8704, 128
        x = (torch.randn(m, k, device="npu:0") * 0.25).bfloat16()
        w = torch.randint(-7, 8, (k, n), device="npu:0", dtype=torch.int32)
        scale = torch.full((k // group, n), 1 / 64, device="npu:0", dtype=torch.bfloat16)
        packed = torch_npu.npu_convert_weight_to_int4pack(w)
        dense_w = (w.reshape(k // group, group, n).bfloat16() * scale[:, None, :]).reshape(k, n)
        quant = lambda: torch_npu.npu_weight_quant_batchmatmul(
            x, packed, antiquant_scale=scale, antiquant_group_size=group
        )
        dense = lambda: x @ dense_w
        q_first = snapshot(quant)
        d_first = snapshot(dense)
        q_second = snapshot(quant)
        d_second = snapshot(dense)
        q_graph = torch.npu.NPUGraph()
        with torch.npu.graph(q_graph):
            q_graph_y = quant()
        d_graph = torch.npu.NPUGraph()
        with torch.npu.graph(d_graph):
            d_graph_y = dense()
        torch.npu.synchronize()
        q_graph.replay()
        q_replay1 = snapshot(lambda: q_graph_y)
        q_graph.replay()
        q_replay2 = snapshot(lambda: q_graph_y)
        d_graph.replay()
        d_replay1 = snapshot(lambda: d_graph_y)
        d_graph.replay()
        d_replay2 = snapshot(lambda: d_graph_y)
        x_new = (torch.randn(m, k, device="npu:0") * 0.25).bfloat16()
        x.copy_(x_new)
        torch.npu.synchronize()
        q_graph.replay()
        q_changed = snapshot(lambda: q_graph_y)
        q_changed_eager = snapshot(quant)
        d_graph.replay()
        d_changed = snapshot(lambda: d_graph_y)
        d_changed_eager = snapshot(dense)
        result.update({
            "status": "measured",
            "shape": {"M": m, "K": k, "N": n, "group": group},
            "quant_eager_repeat": compare(q_second, q_first),
            "quant_graph_repeat": compare(q_replay2, q_replay1),
            "quant_graph_vs_eager_same_x": compare(q_replay1, q_first),
            "quant_changed_x_graph_vs_eager": compare(q_changed, q_changed_eager),
            "dense_eager_repeat": compare(d_second, d_first),
            "dense_graph_repeat": compare(d_replay2, d_replay1),
            "dense_graph_vs_eager_same_x": compare(d_replay1, d_first),
            "dense_changed_x_graph_vs_eager": compare(d_changed, d_changed_eager),
            "quant_vs_dequant_bf16": compare(q_first, d_first),
            "torch_npu_version": torch_npu.__version__,
        })
        tensors = [q_first, q_second, q_replay1, q_replay2, q_changed,
                   d_first, d_second, d_replay1, d_replay2, d_changed]
        if not all(bool(torch.isfinite(t).all().item()) for t in tensors):
            raise AssertionError("non-finite native output")
        result["status"] = "passed_diagnostic"
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
