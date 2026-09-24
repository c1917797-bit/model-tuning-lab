#!/usr/bin/env python3
"""Bounded KVarN equation probe on one physical Ascend NPU.

This is an equation-derived diagnostic, not the author's CUDA/Triton backend
and not a vLLM cache integration. The equations and byte order are taken from
huawei-csl/KVarN at 7586257f1c632e63187bfacbbe21ccb51540f7b3:
sinkhorn.py, kvarn_store.py, kvarn_decode.py, and kvarn_attn.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

import torch
import torch_npu  # noqa: F401 - registers the NPU backend


AUTHOR_COMMIT = "7586257f1c632e63187bfacbbe21ccb51540f7b3"
D = 256
G = 128
ITERS = 8
K_BITS = 4
V_BITS = 2


def hadamard() -> torch.Tensor:
    matrix = torch.ones((1, 1), dtype=torch.float32)
    while matrix.shape[0] < D:
        matrix = torch.cat(
            (torch.cat((matrix, matrix), dim=1),
             torch.cat((matrix, -matrix), dim=1)),
            dim=0,
        )
    return matrix / math.sqrt(D)


def imbalance(tile: torch.Tensor) -> torch.Tensor:
    col_std = tile.std(dim=-2)
    row_std = tile.std(dim=-1)
    return (
        col_std.amax(dim=-1) / col_std.amin(dim=-1).clamp_min(1e-8)
        + row_std.amax(dim=-1) / row_std.amin(dim=-1).clamp_min(1e-8)
    )


def balance(tiles: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Author's batched best-so-far log-domain variance normalization."""
    source = tiles.float()
    n, rows, cols = source.shape
    log_col = torch.zeros((n, 1, cols), device=source.device)
    log_row = torch.zeros((n, rows, 1), device=source.device)
    current = source
    best_imbalance = imbalance(current)
    best_col = log_col.exp()
    best_row = log_row.exp()
    for _ in range(ITERS):
        col_std = current.std(dim=1, keepdim=True).clamp(1e-3, 1e3)
        log_col = (log_col + col_std.log()).clamp(-0.3, 10.0)
        current = source / log_col.exp() / log_row.exp()
        row_std = current.std(dim=2, keepdim=True).clamp(1e-3, 1e3)
        log_row = (log_row + row_std.log()).clamp(-0.3, 10.0)
        current = source / log_col.exp() / log_row.exp()
        score = imbalance(current)
        better = (score <= best_imbalance).view(n, 1, 1)
        best_col = torch.where(better, log_col.exp(), best_col)
        best_row = torch.where(better, log_row.exp(), best_row)
        best_imbalance = torch.minimum(best_imbalance, score)
    return source / best_col / best_row, best_col.squeeze(1), best_row.squeeze(2)


def quantize_rows(tile: torch.Tensor, bits: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    lower = tile.amin(dim=-1, keepdim=True)
    upper = tile.amax(dim=-1, keepdim=True)
    scale = ((upper - lower) / ((1 << bits) - 1)).clamp_min(1e-10)
    values = ((tile - lower) / scale).round().clamp(0, (1 << bits) - 1).to(torch.uint8)
    return values, scale.squeeze(-1), lower.squeeze(-1)


def pack(values: torch.Tensor, bits: int) -> torch.Tensor:
    count = 8 // bits
    width = values.shape[-1]
    assert width % count == 0
    parts = values.reshape(*values.shape[:-1], width // count, count)
    packed = parts[..., 0].clone()
    for index in range(1, count):
        packed = packed | (parts[..., index] << (index * bits))
    return packed


def unpack(packed: torch.Tensor, bits: int, width: int) -> torch.Tensor:
    count = 8 // bits
    mask = (1 << bits) - 1
    parts = [(packed >> (index * bits)) & mask for index in range(count)]
    return torch.stack(parts, dim=-1).reshape(*packed.shape[:-1], width)


def store_k(tile: torch.Tensor) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    balanced, per_token, per_channel = balance(tile)
    values, rtn_scale, rtn_zero = quantize_rows(balanced, K_BITS)
    record = {
        "packed": pack(values, K_BITS),
        "scale_channel": (per_channel * rtn_scale).half(),
        "zero_channel": (per_channel * rtn_zero).half(),
        "scale_token": per_token.half(),
    }
    return record, values


def store_v(tile: torch.Tensor) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    balanced, per_channel, per_token = balance(tile)
    values, rtn_scale, rtn_zero = quantize_rows(balanced, V_BITS)
    record = {
        "packed": pack(values, V_BITS),
        "scale_channel": per_channel.half(),
        "scale_token": (per_token * rtn_scale).half(),
        "zero_token": (per_token * rtn_zero).half(),
    }
    return record, values


def restore_k(record: dict[str, torch.Tensor]) -> torch.Tensor:
    values = unpack(record["packed"], K_BITS, G).float()
    return (
        (values * record["scale_channel"].float().unsqueeze(-1)
         + record["zero_channel"].float().unsqueeze(-1))
        * record["scale_token"].float().unsqueeze(-2)
    )


def restore_v(record: dict[str, torch.Tensor]) -> torch.Tensor:
    values = unpack(record["packed"], V_BITS, D).float()
    return (
        (values * record["scale_token"].float().unsqueeze(-1)
         + record["zero_token"].float().unsqueeze(-1))
        * record["scale_channel"].float().unsqueeze(-2)
    )


def attention(
    query_rotated: torch.Tensor,
    key_rotated: torch.Tensor,
    value_rotated: torch.Tensor,
    h: torch.Tensor,
) -> torch.Tensor:
    scores = torch.matmul(query_rotated.float(), key_rotated.float()) / math.sqrt(D)
    weights = torch.softmax(scores, dim=-1)
    return torch.matmul(weights, value_rotated.float()).matmul(h.float())


def to_cpu(record: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {name: value.cpu() for name, value in record.items()}


def compare(left: torch.Tensor, right: torch.Tensor) -> dict[str, float]:
    left = left.float().cpu()
    right = right.float().cpu()
    difference = left - right
    return {
        "max_abs": float(difference.abs().max()),
        "rms": float(difference.square().mean().sqrt()),
        "cosine": float(torch.nn.functional.cosine_similarity(
            left.reshape(1, -1), right.reshape(1, -1)
        ).item()),
    }


def run_case(batch: int, device: torch.device, h_cpu: torch.Tensor) -> dict:
    generator = torch.Generator(device="cpu").manual_seed(260603458 + batch)
    k_cpu = (torch.randn((batch, G, D), generator=generator) * 0.25).bfloat16()
    v_cpu = (torch.randn((batch, G, D), generator=generator) * 0.25).bfloat16()
    q_cpu = (torch.randn((batch, 6, D), generator=generator) * 0.25).bfloat16()
    h16_cpu = h_cpu.half()
    h16_npu = h16_cpu.to(device)

    def pipeline(target: torch.device, h16: torch.Tensor):
        key = k_cpu.to(target).half()
        value = v_cpu.to(target).half()
        query = q_cpu.to(target).half()
        k_rotated = key.matmul(h16).transpose(-1, -2).contiguous()
        v_rotated = value.matmul(h16)
        q_rotated = query.matmul(h16)
        k_record, k_values = store_k(k_rotated)
        v_record, v_values = store_v(v_rotated)
        k_restored = restore_k(k_record)
        v_restored = restore_v(v_record)
        result = attention(q_rotated, k_restored, v_restored, h16)
        dense_result = attention(q_rotated, k_rotated, v_rotated, h16)
        return (k_record, v_record, k_values, v_values, q_rotated,
                k_restored, v_restored, result, dense_result)

    cpu = pipeline(torch.device("cpu"), h16_cpu)
    npu = pipeline(device, h16_npu)
    torch.npu.synchronize()
    k_record, v_record, k_values, v_values, q_rotated, k_restored, v_restored, output, dense = npu
    cpu_k_record, cpu_v_record, _, _, _, _, _, cpu_output, _ = cpu
    roundtrip_k = torch.equal(unpack(k_record["packed"], K_BITS, G), k_values)
    roundtrip_v = torch.equal(unpack(v_record["packed"], V_BITS, D), v_values)
    shared_k = to_cpu(k_record)
    shared_v = to_cpu(v_record)
    shared_q = q_rotated.cpu()
    shared_reference = attention(
        shared_q, restore_k(shared_k), restore_v(shared_v), h16_cpu
    )
    metrics = {
        "batch": batch,
        "packed_k_bytes": k_record["packed"].numel(),
        "packed_v_bytes": v_record["packed"].numel(),
        "k_pack_roundtrip_exact": roundtrip_k,
        "v_pack_roundtrip_exact": roundtrip_v,
        "k_packed_cpu_npu_mismatch": int(
            (cpu_k_record["packed"] != shared_k["packed"]).sum()
        ),
        "v_packed_cpu_npu_mismatch": int(
            (cpu_v_record["packed"] != shared_v["packed"]).sum()
        ),
        "shared_state_output": compare(output, shared_reference),
        "independent_cpu_npu_output": compare(output, cpu_output),
        "quantized_vs_dense_output": compare(output, dense),
        "finite": all(torch.isfinite(t).all().item() for t in
                      (k_restored, v_restored, output, dense)),
    }
    metrics["pass"] = (
        roundtrip_k and roundtrip_v and metrics["finite"]
        and metrics["shared_state_output"]["max_abs"] <= 0.002
        and metrics["shared_state_output"]["cosine"] >= 0.99999
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    result_root = Path("/results").resolve()
    if result_root not in output_dir.parents or output_dir.exists():
        parser.error("output must be a new directory below /results")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("expected exactly container NPU 0, mapped to physical NPU 4")
    output_dir.mkdir(parents=True)
    device = torch.device("npu:0")
    h_cpu = hadamard()
    started = time.time()
    report = {
        "schema": "kvarn-tile-npu-equation-probe/v1",
        "claim": "synthetic author-equation/NPU smoke only; no vLLM integration or E2E gain",
        "author_commit": AUTHOR_COMMIT,
        "geometry": {"head_dim": D, "group": G, "k_bits": K_BITS,
                     "v_bits": V_BITS, "balance_iterations": ITERS},
        "input_dtype": "bfloat16",
        "internal_rotation_dtype": "float16",
        "torch_version": torch.__version__,
        "npu_name": None,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_epoch_s": started,
        "cases": [],
    }
    try:
        report["npu_name"] = torch.npu.get_device_name(0)
        for batch in (1, 16):
            report["cases"].append(run_case(batch, device, h_cpu))
        report["status"] = "passed" if all(c["pass"] for c in report["cases"]) else "failed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        report["finished_epoch_s"] = time.time()
        (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "output_dir": str(output_dir)}), flush=True)
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
