#!/usr/bin/env python3
"""Strict triangular-inverse correctness and target-shape timing gate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import os

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3
import mxr_npu_probe_v4 as v4  # noqa: F401 - installs v0.23 standalone context


CHUNK = 64
CORRECTNESS_LENGTH = 256


def triangular_correctness(torch, RefGDN, tri_inverse, baseline_solve, device):
    from megagdn_pto.fast_inverse import solve_tril as mxr_solve

    matrix = probe.make_triangular_input(torch, device, CORRECTNESS_LENGTH, CHUNK)
    cu32 = torch.tensor([0, CORRECTNESS_LENGTH], dtype=torch.int32, device=device)
    reference = RefGDN(torch.double).solve_tril(
        matrix.cpu(), CHUNK, [0, CORRECTNESS_LENGTH]
    )
    methods = {
        "v023_solve_tril": lambda: baseline_solve(
            matrix,
            cu_seqlens=cu32.long(),
            output_dtype=torch.float16,
        ),
        "mxr_solve_tril": lambda: mxr_solve(
            matrix, cu32, CHUNK, probe.H, tri_inverse
        ),
    }
    rows = {}
    all_ok = True
    for name, function in methods.items():
        first = function()
        second = function()
        torch.npu.synchronize()
        metrics = probe.tensor_metrics(first, reference)
        replay = bool(torch.equal(first, second))
        ok = bool(metrics["ok"] and replay)
        rows[name] = {
            "result": metrics,
            "bitwise_replay": replay,
            "ok": ok,
        }
        all_ok = all_ok and ok
    return {
        "schema": "mst.mxr.triangular-inverse-numerical/v1",
        "shape": {
            "length": CORRECTNESS_LENGTH,
            "heads": probe.H,
            "chunk": CHUNK,
        },
        "methods": rows,
        "ok": all_ok,
    }


def triangular_timing(torch, tri_inverse, baseline_solve, device):
    from megagdn_pto.fast_inverse import solve_tril as mxr_solve

    lengths = probe.TIMING_LENGTHS
    rows = {}
    for length in lengths:
        matrix = probe.make_triangular_input(torch, device, length, CHUNK)
        cu32 = torch.tensor([0, length], dtype=torch.int32, device=device)
        baseline = probe.timed_ms(
            torch,
            lambda: baseline_solve(
                matrix,
                cu_seqlens=cu32.long(),
                output_dtype=torch.float16,
            ),
        )
        candidate = probe.timed_ms(
            torch,
            lambda: mxr_solve(matrix, cu32, CHUNK, probe.H, tri_inverse),
        )
        candidate["speedup_vs_v023_solve_tril"] = (
            baseline["median_ms"] / candidate["median_ms"]
        )
        rows[str(length)] = {
            "v023_solve_tril": baseline,
            "mxr_solve_tril": candidate,
        }
    clear = all(
        row["mxr_solve_tril"]["speedup_vs_v023_solve_tril"]
        >= probe.MIN_CLEAR_SPEEDUP
        for row in rows.values()
    )
    return {
        "schema": "mst.mxr.triangular-inverse-timing/v1",
        "shape": {"heads": probe.H, "chunk": CHUNK},
        "lengths": list(lengths),
        "minimum_clear_speedup": probe.MIN_CLEAR_SPEEDUP,
        "by_length": rows,
        "clear_advantage": clear,
        "ok": clear,
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--pto-lib", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--phase", choices=("correctness", "timing", "all"), default="all")
    args = parser.parse_args()
    if args.phase != "all":
        raise RuntimeError("v10 is an inseparable correctness-then-timing gate")
    if not args.output_dir.is_dir():
        raise RuntimeError("output directory must already exist")

    from vllm_ascend.utils import bootstrap_custom_op_env, enable_custom_op

    bootstrap_custom_op_env()
    custom_opp_path = os.environ.get("ASCEND_CUSTOM_OPP_PATH", "")
    if not custom_opp_path:
        raise RuntimeError("ASCEND_CUSTOM_OPP_PATH was not established before device initialization")

    v3.run_canary(args.output_dir)
    probe.configure_imports(args.source_root, args.pto_lib, args.output_dir / "compiled")

    import torch
    import torch_npu  # noqa: F401
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton

    custom_ops_enabled = bool(enable_custom_op())
    init_device_properties_triton()
    probe.atomic_json(
        args.output_dir / "worker-bootstrap.json",
        {
            "schema": "mst.mxr.triangular-bootstrap/v1",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "custom_opp_path": custom_opp_path,
            "custom_ops_enabled": custom_ops_enabled,
            "ok": custom_ops_enabled,
        },
    )
    if not custom_ops_enabled:
        raise RuntimeError("v0.23 worker bootstrap incomplete")

    torch.npu.set_device(0)
    device = torch.device("npu:0")
    torch, RefGDN, tri_inverse, baseline_solve, _methods = probe.load_implementations()
    numerical = triangular_correctness(
        torch, RefGDN, tri_inverse, baseline_solve, device
    )
    probe.atomic_json(args.output_dir / "triangular-numerical-gate.json", numerical)
    if not numerical["ok"]:
        return 3
    timing = triangular_timing(torch, tri_inverse, baseline_solve, device)
    probe.atomic_json(args.output_dir / "triangular-target-shape-timing.json", timing)
    probe.atomic_json(
        args.output_dir / "runtime-manifest.json",
        probe.environment_manifest(
            torch, args.source_root, args.pto_lib, args.output_dir / "compiled"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
