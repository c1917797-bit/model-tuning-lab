#!/usr/bin/env python3
"""Physical-NPU gate for partitioned KVarN sink/compressed/tail decode."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import torch
import torch_npu  # noqa: F401

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "plugin"))
from qwen36_kvarn_ascend.partial_decode_split import (  # noqa: E402
    combine_partials, compressed_partial, pool_partial,
)
from run_kvarn_triton_dequant_probe import compare, load_equation_probe  # noqa: E402


def run_case(count: int, probe) -> dict:
    generator = torch.Generator(device="cpu").manual_seed(260603458 + count)
    def random(*shape):
        return (torch.randn(shape, generator=generator) * 0.25).half().to("npu:0")

    k = random(count, probe.G, probe.D)
    v = random(count, probe.G, probe.D)
    q = random(count, 6, probe.D)
    h = probe.hadamard().half().to("npu:0")
    h32 = h.float()
    q_rot = q @ h
    kr, _ = probe.store_k(k.matmul(h).transpose(-1, -2).contiguous())
    vr, _ = probe.store_v(v.matmul(h))
    alt_k = random(count, probe.G, probe.D)
    alt_v = random(count, probe.G, probe.D)
    alt_kr, _ = probe.store_k(alt_k.matmul(h).transpose(-1, -2).contiguous())
    alt_vr, _ = probe.store_v(alt_v.matmul(h))
    fields = (
        kr["packed"], kr["scale_channel"], kr["zero_channel"], kr["scale_token"],
        vr["packed"], vr["scale_channel"], vr["scale_token"], vr["zero_token"],
    )
    alt_fields = (
        alt_kr["packed"], alt_kr["scale_channel"], alt_kr["zero_channel"],
        alt_kr["scale_token"], alt_vr["packed"], alt_vr["scale_channel"],
        alt_vr["scale_token"], alt_vr["zero_token"],
    )
    cache_fields = []
    for field, alt_field in zip(fields, alt_fields):
        expanded = torch.zeros((count * 3, *field.shape[1:]), dtype=field.dtype, device=field.device)
        expanded[1::3] = field
        expanded[2::3] = alt_field
        cache_fields.append(expanded)
    pool_k = random(count * 2, probe.G, probe.D)
    pool_v = random(count * 2, probe.G, probe.D)
    block_table = torch.arange(count * 3, dtype=torch.int32, device="npu:0").reshape(count, 3)
    lengths = [257 + (i % 42) for i in range(count)]
    seq_lens = torch.tensor(lengths, dtype=torch.int32, device="npu:0")
    compressed_ids = block_table[:, 1].contiguous()
    alternate_ids = block_table[:, 2].contiguous()
    c_out, c_lse = compressed_partial(q_rot, compressed_ids, tuple(cache_fields))
    pool_q = q_rot.repeat_interleave(2, 0).contiguous()
    pool_slots = torch.arange(count * 2, dtype=torch.int32, device="npu:0")
    swapped_pool_slots = pool_slots.reshape(count, 2).flip(1).reshape(-1).contiguous()
    pool_valid = torch.tensor([n for length in lengths for n in (128, length - 256)],
                              dtype=torch.int32, device="npu:0")
    p_out, p_lse = pool_partial(pool_q, pool_slots, pool_valid, pool_k, pool_v)
    p_out = p_out.reshape(count, 2, 6, probe.D)
    p_lse = p_lse.reshape(count, 2, 6)
    parts = torch.stack((p_out[:, 0], c_out, p_out[:, 1]), 1)
    lses = torch.stack((p_lse[:, 0], c_lse, p_lse[:, 1]), 1)
    got = (combine_partials(parts, lses).float() @ h32).half()

    decoded_k = probe.restore_k(kr).transpose(-1, -2).half()
    decoded_v = probe.restore_v(vr).half()
    alt_decoded_k = probe.restore_k(alt_kr).transpose(-1, -2).half()
    alt_decoded_v = probe.restore_v(alt_vr).half()
    def reference_for(query, use_alt=False):
        expected = []
        for i in range(count):
            tail = lengths[i] - 256
            sink_slot = 2 * i + 1 if use_alt else 2 * i
            tail_slot = 2 * i if use_alt else 2 * i + 1
            middle_k = alt_decoded_k[i] if use_alt else decoded_k[i]
            middle_v = alt_decoded_v[i] if use_alt else decoded_v[i]
            keys_rot = torch.cat((pool_k[sink_slot], middle_k, pool_k[tail_slot, :tail]), 0)
            values_rot = torch.cat((pool_v[sink_slot], middle_v, pool_v[tail_slot, :tail]), 0)
            keys = keys_rot.float() @ h32
            values = values_rot.float() @ h32
            weights = torch.softmax(query[i].float() @ keys.float().T / math.sqrt(probe.D), -1)
            expected.append((weights @ values.float()).half())
        return torch.stack(expected)

    reference = reference_for(q)
    torch.npu.synchronize()
    result = compare(got, reference)
    static_q = q_rot.clone()
    static_pool_q = pool_q.clone()
    compressed_partial(static_q, compressed_ids, tuple(cache_fields))
    pool_partial(static_pool_q, pool_slots, pool_valid, pool_k, pool_v)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        gc_out, gc_lse = compressed_partial(static_q, compressed_ids, tuple(cache_fields))
        gp_out, gp_lse = pool_partial(static_pool_q, pool_slots, pool_valid, pool_k, pool_v)
        gp_out = gp_out.reshape(count, 2, 6, probe.D)
        gp_lse = gp_lse.reshape(count, 2, 6)
        g_parts = torch.stack((gp_out[:, 0], gc_out, gp_out[:, 1]), 1)
        g_lses = torch.stack((gp_lse[:, 0], gc_lse, gp_lse[:, 1]), 1)
        graph_output = (combine_partials(g_parts, g_lses).float() @ h32).half()
    replay_cases = []
    for offset, use_alt in ((0.0, False), (0.125, True)):
        variant_q = (q.float() + offset).half()
        variant_q_rot = variant_q @ h
        static_q.copy_(variant_q_rot)
        static_pool_q.copy_(variant_q_rot.repeat_interleave(2, 0))
        compressed_ids.copy_(alternate_ids if use_alt else block_table[:, 1].contiguous())
        pool_slots.copy_(swapped_pool_slots if use_alt else torch.arange(
            count * 2, dtype=torch.int32, device="npu:0"))
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        first = graph_output.clone()
        graph.replay()
        torch.npu.synchronize()
        stable = bool(torch.equal(first, graph_output))
        replay_result = compare(first, reference_for(variant_q, use_alt))
        replay_cases.append({"query_offset": offset, "alternate_block_and_pool": use_alt,
                             "stable": stable,
                             "attention": replay_result,
                             "pass": stable and replay_result["finite"]
                             and replay_result["max_abs"] <= 0.02})
    return {"count": count, "min_seq_len": min(lengths), "max_seq_len": max(lengths),
            "attention": result, "partials_finite": bool(torch.isfinite(parts).all().item()),
            "lse_finite": bool(torch.isfinite(lses).all().item()),
            "graph_replays": replay_cases,
            "pass": result["finite"] and result["max_abs"] <= 0.02
            and all(case["pass"] for case in replay_cases)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if Path("/results") not in output_dir.parents or output_dir.exists():
        parser.error("output must be a new directory below /results")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("expected container NPU0 mapped to physical NPU4")
    output_dir.mkdir(parents=True)
    probe, probe_hash = load_equation_probe()
    op_path = PROJECT / "plugin" / "qwen36_kvarn_ascend" / "partial_decode_split.py"
    report = {
        "schema": "kvarn-partitioned-decode-ascend/v1",
        "claim": "synthetic 3-block split-softmax numeric gate; not vLLM service or E2E",
        "author_commit": probe.AUTHOR_COMMIT,
        "equation_probe_sha256": probe_hash,
        "operator_sha256": hashlib.sha256(op_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_epoch_s": time.time(), "cases": [],
    }
    try:
        report["npu_name"] = torch.npu.get_device_name(0)
        for count in (1, 16):
            report["cases"].append(run_case(count, probe))
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
