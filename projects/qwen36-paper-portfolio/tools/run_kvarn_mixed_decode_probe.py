#!/usr/bin/env python3
"""NPU numerical gate for KVarN sink + compressed history + tail decode."""

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
from qwen36_kvarn_ascend.decode_split import mixed_decode_split  # noqa: E402
from run_kvarn_triton_dequant_probe import compare, load_equation_probe  # noqa: E402


def run_case(count: int, probe) -> dict:
    generator = torch.Generator(device="cpu").manual_seed(260603458 + count)
    def random(*shape):
        return (torch.randn(shape, generator=generator) * 0.25).half().to("npu:0")

    k = random(count, probe.G, probe.D)
    v = random(count, probe.G, probe.D)
    q = random(count, 6, probe.D)
    h = probe.hadamard().half().to("npu:0")
    kr, _ = probe.store_k(k.matmul(h).transpose(-1, -2).contiguous())
    vr, _ = probe.store_v(v.matmul(h))
    compressed_fields = (
        kr["packed"], kr["scale_channel"], kr["zero_channel"], kr["scale_token"],
        vr["packed"], vr["scale_channel"], vr["scale_token"], vr["zero_token"],
    )
    cache_fields = []
    for field in compressed_fields:
        expanded = torch.zeros((count * 3, *field.shape[1:]), dtype=field.dtype, device=field.device)
        expanded[1::3] = field
        cache_fields.append(expanded)
    pool_k = random(count * 2, probe.G, probe.D)
    pool_v = random(count * 2, probe.G, probe.D)
    block_table = torch.arange(count * 3, dtype=torch.int32, device="npu:0").reshape(count, 3)
    seq_lens = torch.tensor([257 + (i % 42) for i in range(count)], dtype=torch.int32, device="npu:0")
    slots = torch.tensor([slot for i in range(count) for slot in (2 * i, -1, 2 * i + 1)],
                         dtype=torch.int32, device="npu:0")
    got = mixed_decode_split(q, block_table, seq_lens, slots, *cache_fields,
                             pool_k, pool_v)
    decoded_k = probe.restore_k(kr).transpose(-1, -2).half()
    decoded_v = probe.restore_v(vr).half()
    expected = []
    for i in range(count):
        tail = int(seq_lens[i].item()) - 2 * probe.G
        keys = torch.cat((pool_k[2 * i], decoded_k[i], pool_k[2 * i + 1, :tail]), 0)
        values = torch.cat((pool_v[2 * i], decoded_v[i], pool_v[2 * i + 1, :tail]), 0)
        weights = torch.softmax(q[i].float() @ keys.float().T / math.sqrt(probe.D), -1)
        expected.append((weights @ values.float()).half())
    reference = torch.stack(expected)
    torch.npu.synchronize()
    result = compare(got, reference)
    return {"count": count, "min_seq_len": int(seq_lens.min().item()),
            "max_seq_len": int(seq_lens.max().item()), "attention": result,
            "pass": result["finite"] and result["max_abs"] <= 0.02}


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
    op_path = PROJECT / "plugin" / "qwen36_kvarn_ascend" / "decode_split.py"
    report = {
        "schema": "kvarn-mixed-decode-ascend/v1",
        "claim": "synthetic 3-block sink/compressed/tail attention; no vLLM or E2E",
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
