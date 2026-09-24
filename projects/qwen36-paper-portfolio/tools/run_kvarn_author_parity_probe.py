#!/usr/bin/env python3
"""Compare the Ascend equation probe with pinned author PyTorch references.

This is a tile-format/numerical gate, not a vLLM cache or throughput test.
The author checkout is mounted read-only and source is loaded from a fixed Git
commit so sparse-checkout state cannot silently change the tested reference.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

import torch
import torch_npu  # noqa: F401


AUTHOR_COMMIT = "7586257f1c632e63187bfacbbe21ccb51540f7b3"
AUTHOR_ROOT = Path("/author")
PREFIX = "vllm.model_executor.layers.quantization.kvarn"
SOURCES = {
    "sinkhorn": "vllm/model_executor/layers/quantization/kvarn/sinkhorn.py",
    "store": "vllm/v1/attention/ops/kvarn_store.py",
    "decode": "vllm/v1/attention/ops/kvarn_decode.py",
}


def load_author_source(name: str, path: str) -> tuple[types.ModuleType, str]:
    source = subprocess.run(
        ["git", "-C", str(AUTHOR_ROOT), "show", f"{AUTHOR_COMMIT}:{path}"],
        check=True, capture_output=True, timeout=60,
    ).stdout
    module = types.ModuleType(name)
    module.__file__ = f"git:{AUTHOR_COMMIT}:{path}"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module, hashlib.sha256(source).hexdigest()


def load_references() -> tuple[dict[str, types.ModuleType], dict[str, str]]:
    for parent in ("vllm", "vllm.model_executor", "vllm.model_executor.layers",
                   "vllm.model_executor.layers.quantization", PREFIX):
        package = types.ModuleType(parent)
        package.__path__ = []
        sys.modules[parent] = package
    modules = {}
    hashes = {}
    for key in ("sinkhorn", "store", "decode"):
        name = f"{PREFIX}.sinkhorn" if key == "sinkhorn" else f"kvarn_author_{key}"
        modules[key], hashes[key] = load_author_source(name, SOURCES[key])
    return modules, hashes


def diff(left: torch.Tensor, right: torch.Tensor) -> dict[str, float | bool]:
    a, b = left.cpu(), right.cpu()
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {tuple(a.shape)} vs {tuple(b.shape)}")
    delta = a.float() - b.float()
    return {"exact": bool(torch.equal(a, b)),
            "max_abs": float(delta.abs().max())}


def run_case(batch: int, probe, reference: dict[str, types.ModuleType]) -> dict:
    gen = torch.Generator(device="cpu").manual_seed(260603458 + batch)
    k = (torch.randn((batch, probe.G, probe.D), generator=gen) * 0.25).half().to("npu:0")
    v = (torch.randn((batch, probe.G, probe.D), generator=gen) * 0.25).half().to("npu:0")
    h = probe.hadamard().half().to("npu:0")
    tiles = {"k": k.matmul(h).transpose(-1, -2).contiguous(),
             "v": v.matmul(h)}
    fields = {
        "k": {"packed": "q_packed_uint8", "scale_channel": "s_col_K",
              "zero_channel": "zp_K", "scale_token": "s_row_K"},
        "v": {"packed": "q_packed_uint8", "scale_channel": "s_col_V",
              "scale_token": "s_row_V", "zero_token": "zp_V"},
    }
    result = {"batch": batch, "arms": {}}
    for arm, tile in tiles.items():
        ours_balanced, ours_col, ours_row = probe.balance(tile)
        ref_balanced, ref_col, ref_row = reference["sinkhorn"].variance_normalize_batched(
            tile, iterations=probe.ITERS)
        ref_record = getattr(reference["store"],
                             f"kvarn_store_tile_{arm}_batch_from_sinkhorn")(
            ref_balanced, ref_col.squeeze(1), ref_row.squeeze(2),
            probe.K_BITS if arm == "k" else probe.V_BITS)
        our_record, _ = probe.store_k(tile) if arm == "k" else probe.store_v(tile)
        field_diffs = {our_name: diff(our_record[our_name], ref_record[ref_name])
                       for our_name, ref_name in fields[arm].items()}
        decoded = []
        for index in range(batch):
            ref_decode = (reference["decode"].kvarn_dequant_tile_k(
                ref_record["q_packed_uint8"][index], ref_record["s_col_K"][index],
                ref_record["zp_K"][index], ref_record["s_row_K"][index],
                probe.G, probe.K_BITS) if arm == "k" else
                reference["decode"].kvarn_dequant_tile_v(
                    ref_record["q_packed_uint8"][index], ref_record["s_col_V"][index],
                    ref_record["s_row_V"][index], ref_record["zp_V"][index],
                    probe.D, probe.V_BITS))
            ours_decode = (probe.restore_k(our_record)[index] if arm == "k"
                           else probe.restore_v(our_record)[index])
            decoded.append(diff(ours_decode, ref_decode))
        result["arms"][arm] = {
            "balanced": diff(ours_balanced, ref_balanced),
            "column_scale": diff(ours_col, ref_col.squeeze(1)),
            "row_scale": diff(ours_row, ref_row.squeeze(2)),
            "fields": field_diffs,
            "decode_max_abs": max(item["max_abs"] for item in decoded),
            "decode_exact": all(item["exact"] for item in decoded),
        }
    result["pass"] = all(
        all(field["exact"] for field in arm["fields"].values())
        and arm["decode_max_abs"] <= 1e-6
        for arm in result["arms"].values()
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if Path("/results") not in output_dir.parents or output_dir.exists():
        parser.error("output must be a new directory under /results")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("expected container NPU0 mapped to physical NPU4")
    output_dir.mkdir(parents=True)
    probe_path = Path(__file__).with_name("run_kvarn_tile_npu_probe.py")
    spec = importlib.util.spec_from_file_location("kvarn_tile_probe", probe_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import KVarN equation probe")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = {"schema": "kvarn-author-reference-ascend-parity/v1",
              "claim": "pinned author PyTorch tile reference vs Ascend equation probe only",
              "author_commit": AUTHOR_COMMIT,
              "probe_sha256": hashlib.sha256(probe_path.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "started_epoch_s": time.time(), "cases": []}
    try:
        reference, report["author_source_sha256"] = load_references()
        report["npu_name"] = torch.npu.get_device_name(0)
        for batch in (1, 16):
            report["cases"].append(run_case(batch, probe, reference))
        torch.npu.synchronize()
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
