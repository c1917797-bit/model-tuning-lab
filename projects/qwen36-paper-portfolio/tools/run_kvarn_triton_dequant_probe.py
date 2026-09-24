#!/usr/bin/env python3
"""Validate plugin KVarN dequant against pinned author-parity tile equations.

This is a one-NPU operator gate, not a serving, throughput, or task-accuracy run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import torch
import torch_npu  # noqa: F401


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "plugin"))
from qwen36_kvarn_ascend import dequantize_packed_tiles  # noqa: E402


def load_equation_probe():
    path = Path(__file__).with_name("run_kvarn_tile_npu_probe.py")
    spec = importlib.util.spec_from_file_location("kvarn_tile_equations", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("missing KVarN tile equation probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def pack_record(k: dict, v: dict, count: int) -> torch.Tensor:
    fields = (
        k["packed"], k["scale_channel"], k["zero_channel"],
        k["scale_token"], v["packed"], v["scale_channel"],
        v["scale_token"], v["zero_token"],
    )
    byte_fields = [x.contiguous().view(torch.uint8).reshape(count, -1)
                   for x in fields]
    record = torch.cat(byte_fields, dim=1)
    if record.shape[1] != 26880:
        raise AssertionError(f"unexpected raw tile bytes {record.shape[1]}")
    pad = torch.zeros((count, 32768 - record.shape[1]),
                      dtype=torch.uint8, device=record.device)
    return torch.cat((record, pad), dim=1).contiguous()


def compare(actual: torch.Tensor, expected: torch.Tensor) -> dict:
    a, e = actual.cpu(), expected.cpu()
    delta = (a.float() - e.float()).abs()
    return {
        "max_abs": float(delta.max()),
        "mismatch_count": int((a != e).sum()),
        "finite": bool(torch.isfinite(a).all()),
        "exact": bool(torch.equal(a, e)),
    }


def run_case(count: int, probe) -> dict:
    generator = torch.Generator(device="cpu").manual_seed(260603458 + count)
    k = (torch.randn((count, probe.G, probe.D), generator=generator) * 0.25).half().to("npu:0")
    v = (torch.randn((count, probe.G, probe.D), generator=generator) * 0.25).half().to("npu:0")
    h = probe.hadamard().half().to("npu:0")
    k_rot = k.matmul(h).transpose(-1, -2).contiguous()
    v_rot = v.matmul(h)
    k_record, _ = probe.store_k(k_rot)
    v_record, _ = probe.store_v(v_rot)
    packed = pack_record(k_record, v_record, count)
    got_k, got_v = dequantize_packed_tiles(packed)
    torch.npu.synchronize()
    k_expected = probe.restore_k(k_record).transpose(-1, -2).half()
    v_expected = probe.restore_v(v_record).half()
    metrics = {"count": count, "k": compare(got_k, k_expected),
               "v": compare(got_v, v_expected)}
    metrics["pass"] = all(
        metrics[arm]["finite"] and metrics[arm]["max_abs"] <= 0.002
        for arm in ("k", "v")
    )
    return metrics


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
    kernel_path = PROJECT / "plugin" / "qwen36_kvarn_ascend" / "tile_dequant.py"
    report = {
        "schema": "kvarn-triton-ascend-dequant-operator/v1",
        "claim": "K4/V2 dequant operator against author-matched packed tile; no serving gain",
        "author_commit": probe.AUTHOR_COMMIT,
        "equation_probe_sha256": probe_hash,
        "operator_sha256": hashlib.sha256(kernel_path.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_epoch_s": time.time(),
        "cases": [],
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
