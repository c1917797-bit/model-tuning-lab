#!/usr/bin/env python3
"""Numerical/compile gate for a single compressed KVarN attention tile."""

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
from qwen36_kvarn_ascend.tile_attention_split import one_tile_attention_split  # noqa: E402
from run_kvarn_triton_dequant_probe import compare, load_equation_probe  # noqa: E402


def run_case(count: int, probe) -> dict:
    generator = torch.Generator(device="cpu").manual_seed(260603458 + count)
    k = (torch.randn((count, probe.G, probe.D), generator=generator) * 0.25).half().to("npu:0")
    v = (torch.randn((count, probe.G, probe.D), generator=generator) * 0.25).half().to("npu:0")
    q = (torch.randn((count, 6, probe.D), generator=generator) * 0.25).half().to("npu:0")
    h = probe.hadamard().half().to("npu:0")
    kr, _ = probe.store_k(k.matmul(h).transpose(-1, -2).contiguous())
    vr, _ = probe.store_v(v.matmul(h))
    got = one_tile_attention_split(
        q, kr["packed"], kr["scale_channel"], kr["zero_channel"], kr["scale_token"],
        vr["packed"], vr["scale_channel"], vr["scale_token"], vr["zero_token"],
    )
    key = probe.restore_k(kr).transpose(-1, -2).half()
    value = probe.restore_v(vr).half()
    reference = torch.softmax(q.float().matmul(key.float().transpose(-1, -2)) / math.sqrt(probe.D), -1)
    reference = reference.matmul(value.float()).half()
    torch.npu.synchronize()
    result = compare(got, reference)
    return {"count": count, "attention": result,
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
    op_path = PROJECT / "plugin" / "qwen36_kvarn_ascend" / "tile_attention_split.py"
    report = {
        "schema": "kvarn-one-tile-ascend-attention/v1",
        "claim": "one-tile compressed attention numeric/compile only; no sink-tail, paging or serving",
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
