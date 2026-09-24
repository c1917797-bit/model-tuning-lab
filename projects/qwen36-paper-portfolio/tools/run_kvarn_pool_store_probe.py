#!/usr/bin/env python3
"""Physical-NPU numerical and NPUGraph gate for KVarN staging-pool writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import torch
import torch_npu  # noqa: F401

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "plugin"))
from qwen36_kvarn_ascend.pool_store_split import scatter_pool  # noqa: E402

SENTINEL = -7.0


def check_case(n: int) -> dict:
    torch.manual_seed(260603458 + n)
    k = torch.randn((n, 1, 256), dtype=torch.float16, device="npu:0")
    v = torch.randn_like(k)
    mapping_a = torch.tensor(
        [(5 + i // 128) * 128 + (i % 128)
         if i % 7 != 0 or n == 1 else -1 for i in range(n)],
        dtype=torch.int32, device="npu:0")
    mapping_b = torch.tensor(
        [(7 + i // 128) * 128 + (i % 128)
         if i % 11 != 0 or n == 1 else -1 for i in range(n)],
        dtype=torch.int32, device="npu:0")
    lookup_a = torch.full((12,), -1, dtype=torch.int32, device="npu:0")
    lookup_b = lookup_a.clone()
    lookup_a[5] = 2
    lookup_a[6] = 1
    lookup_b[7] = 3
    lookup_b[8] = 4
    pool_k = torch.full((5, 128, 1, 256), SENTINEL, dtype=torch.float16, device="npu:0")
    pool_v = pool_k.clone()
    static_k = k.clone()
    static_v = v.clone()
    static_mapping = mapping_a.clone()
    static_lookup = lookup_a.clone()

    def reference(mapping, lookup, k_in, v_in):
        expected_k = torch.full_like(pool_k, SENTINEL)
        expected_v = torch.full_like(pool_v, SENTINEL)
        for i, sm in enumerate(mapping.cpu().tolist()):
            if sm < 0:
                continue
            block, position = divmod(sm, 128)
            slot = int(lookup[block].item())
            if slot >= 0:
                expected_k[slot, position, 0] = k_in[i, 0]
                expected_v[slot, position, 0] = v_in[i, 0]
        return expected_k, expected_v

    scatter_pool(static_k, static_v, static_mapping, static_lookup, pool_k, pool_v)
    torch.npu.synchronize()
    eager_k, eager_v = reference(mapping_a, lookup_a, k, v)
    eager = bool(torch.equal(pool_k, eager_k) and torch.equal(pool_v, eager_v))

    pool_k.fill_(SENTINEL)
    pool_v.fill_(SENTINEL)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        scatter_pool(static_k, static_v, static_mapping, static_lookup, pool_k, pool_v)

    replay = []
    for variant, mapping, lookup, offset in (
        ("base", mapping_a, lookup_a, 0.0),
        ("changed_block_and_value", mapping_b, lookup_b, 0.125),
    ):
        changed_k = (k.float() + offset).half()
        changed_v = (v.float() - offset).half()
        static_k.copy_(changed_k)
        static_v.copy_(changed_v)
        static_mapping.copy_(mapping)
        static_lookup.copy_(lookup)
        expected_k, expected_v = reference(mapping, lookup, changed_k, changed_v)
        pool_k.fill_(SENTINEL)
        pool_v.fill_(SENTINEL)
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        first_k = pool_k.clone()
        first_v = pool_v.clone()
        exact = bool(torch.equal(first_k, expected_k) and torch.equal(first_v, expected_v))
        pool_k.fill_(SENTINEL)
        pool_v.fill_(SENTINEL)
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        stable = bool(torch.equal(first_k, pool_k) and torch.equal(first_v, pool_v))
        replay.append({"variant": variant, "exact": exact, "stable": stable})
    return {"tokens": n, "eager_exact": eager, "graph_replays": replay,
            "pass": eager and all(x["exact"] and x["stable"] for x in replay)}


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
    operator = PROJECT / "plugin/qwen36_kvarn_ascend/pool_store_split.py"
    report = {
        "schema": "kvarn-pool-store-ascend/v1",
        "claim": "synthetic slot-mapped store numeric/graph gate; not full lifecycle or E2E",
        "operator_sha256": hashlib.sha256(operator.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_epoch_s": time.time(), "cases": [],
    }
    try:
        report["npu_name"] = torch.npu.get_device_name(0)
        for n in (1, 16, 129):
            report["cases"].append(check_case(n))
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
