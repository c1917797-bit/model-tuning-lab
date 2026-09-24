#!/usr/bin/env python3
"""Diagnostic only: full partitioned decode launch cost on one Ascend NPU.

No dense service comparison is made here. This determines whether the
split-per-block compiler workaround merits full vLLM cache integration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

import torch
import torch_npu  # noqa: F401

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "plugin"))
from qwen36_kvarn_ascend.partial_decode_split import (  # noqa: E402
    combine_partials, compressed_partial, pool_partial,
)

BATCH = 16
GROUP = 128
D = 256
HEADS = 6
WARMUPS = 5
REPEATS = 20


def hadamard() -> torch.Tensor:
    h = torch.ones((1, 1), dtype=torch.float32)
    while h.shape[0] < D:
        h = torch.cat((torch.cat((h, h), 1), torch.cat((h, -h), 1)), 0)
    return (h / math.sqrt(D)).half().to("npu:0")


def measure(blocks_per_request: int) -> dict:
    count = BATCH * blocks_per_request
    device = "npu:0"
    q = torch.randn((BATCH, HEADS, D), dtype=torch.float16, device=device) * 0.25
    h = hadamard()
    kq = torch.randint(0, 16, (count, D * GROUP // 2), dtype=torch.uint8, device=device)
    kc = torch.full((count, D), 0.01, dtype=torch.float16, device=device)
    kz = torch.zeros_like(kc)
    kr = torch.ones((count, GROUP), dtype=torch.float16, device=device)
    vq = torch.randint(0, 4, (count, GROUP * D // 4), dtype=torch.uint8, device=device)
    vc = torch.full((count, D), 0.01, dtype=torch.float16, device=device)
    vr = torch.ones((count, GROUP), dtype=torch.float16, device=device)
    vz = torch.zeros_like(vr)
    fields = (kq, kc, kz, kr, vq, vc, vr, vz)
    block_ids = torch.arange(count, dtype=torch.int32, device=device)
    pool_k = torch.randn((BATCH * 2, GROUP, D), dtype=torch.float16, device=device) * 0.25
    pool_v = torch.randn_like(pool_k) * 0.25
    pool_slots = torch.arange(BATCH * 2, dtype=torch.int32, device=device)
    pool_valid = torch.tensor([n for _ in range(BATCH) for n in (GROUP, 32)],
                              dtype=torch.int32, device=device)

    def forward():
        q_rot = q @ h
        cq = q_rot.repeat_interleave(blocks_per_request, 0).contiguous()
        pq = q_rot.repeat_interleave(2, 0).contiguous()
        co, cl = compressed_partial(cq, block_ids, fields)
        po, pl = pool_partial(pq, pool_slots, pool_valid, pool_k, pool_v)
        co = co.reshape(BATCH, blocks_per_request, HEADS, D)
        cl = cl.reshape(BATCH, blocks_per_request, HEADS)
        po = po.reshape(BATCH, 2, HEADS, D)
        pl = pl.reshape(BATCH, 2, HEADS)
        outputs = torch.cat((po[:, 0:1], co, po[:, 1:2]), 1)
        lses = torch.cat((pl[:, 0:1], cl, pl[:, 1:2]), 1)
        return (combine_partials(outputs, lses).float() @ h.float()).half()

    for _ in range(WARMUPS):
        forward()
    torch.npu.synchronize()
    times_ms = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        output = forward()
        torch.npu.synchronize()
        times_ms.append((time.perf_counter() - start) * 1000)
    return {
        "batch": BATCH, "compressed_blocks_per_request": blocks_per_request,
        "context_tokens_approx": GROUP * (blocks_per_request + 1) + 32,
        "compressed_bytes": sum(t.numel() * t.element_size() for t in fields),
        "output_finite": bool(torch.isfinite(output).all().item()),
        "median_ms": statistics.median(times_ms),
        "min_ms": min(times_ms), "max_ms": max(times_ms),
        "all_ms": times_ms,
    }


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
    operator = PROJECT / "plugin/qwen36_kvarn_ascend/partial_decode_split.py"
    report = {
        "schema": "kvarn-partitioned-latency-diagnostic/v1",
        "claim": "NPU launch-cost diagnostic only; not a dense comparison or E2E claim",
        "operator_sha256": hashlib.sha256(operator.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_epoch_s": time.time(), "cases": [],
    }
    try:
        report["npu_name"] = torch.npu.get_device_name(0)
        for blocks in (1, 16, 64, 128):
            report["cases"].append(measure(blocks))
        report["status"] = "passed" if all(c["output_finite"] for c in report["cases"]) else "failed"
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
