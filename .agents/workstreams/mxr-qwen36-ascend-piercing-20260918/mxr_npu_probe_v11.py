#!/usr/bin/env python3
"""Candidate-only full-GDN timing after the immutable v8 numerical gate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import os

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3
import mxr_npu_probe_v4 as v4  # noqa: F401 - installs v0.23 standalone context


LENGTHS = (4096, 16384, 32768)
CANDIDATES = ("pto_staged", "pto_mega")
V8_NUMERICAL_SHA256 = "ab112ae3ee4e2cf91af2399ccf18f65caf159831998f99b976dad7eff3dafa2c"


def candidate_timing(torch, methods, device):
    rows = {}
    for length in LENGTHS:
        q, k, v, g, beta, cu32 = probe.make_inputs(
            torch, device, length, 3900 + length
        )
        state = torch.zeros(
            1, probe.H, probe.D, probe.D, dtype=torch.float16, device=device
        )
        rows[str(length)] = {
            name: probe.timed_ms(
                torch,
                lambda method=method: method(q, k, v, g, beta, cu32, state),
                warmup=3,
                repeats=10,
            )
            for name, method in methods.items()
        }
    return {
        "schema": "mst.mxr.full-gdn-candidate-timing/v1",
        "shape": {
            "H": probe.H,
            "Hg": probe.HG,
            "D": probe.D,
            "chunk_pto": probe.C_PTO,
            "dtype": "float16",
        },
        "lengths": list(LENGTHS),
        "methods": list(CANDIDATES),
        "correctness_dependency": {
            "result": "/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v8/numerical-gate.json",
            "sha256": V8_NUMERICAL_SHA256,
        },
        "by_length": rows,
        "ok": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--pto-lib", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--phase", choices=("correctness", "timing", "all"), default="all"
    )
    args = parser.parse_args()
    if args.phase != "all":
        raise RuntimeError("v11 is an inseparable canary-and-timing gate")
    if not args.output_dir.is_dir():
        raise RuntimeError("output directory must already exist")

    from vllm_ascend.utils import bootstrap_custom_op_env, enable_custom_op

    bootstrap_custom_op_env()
    custom_opp_path = os.environ.get("ASCEND_CUSTOM_OPP_PATH", "")
    if not custom_opp_path:
        raise RuntimeError(
            "ASCEND_CUSTOM_OPP_PATH was not established before device initialization"
        )

    v3.run_canary(args.output_dir)
    probe.configure_imports(
        args.source_root, args.pto_lib, args.output_dir / "compiled"
    )

    import torch
    import torch_npu  # noqa: F401
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton

    custom_ops_enabled = bool(enable_custom_op())
    init_device_properties_triton()
    probe.atomic_json(
        args.output_dir / "worker-bootstrap.json",
        {
            "schema": "mst.mxr.full-gdn-timing-bootstrap/v1",
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
    torch, _RefGDN, _tri_inverse, _baseline_solve, methods = (
        probe.load_implementations()
    )
    selected = {name: methods[name] for name in CANDIDATES}
    timing = candidate_timing(torch, selected, device)
    probe.atomic_json(args.output_dir / "full-gdn-candidate-timing.json", timing)
    probe.atomic_json(
        args.output_dir / "runtime-manifest.json",
        probe.environment_manifest(
            torch, args.source_root, args.pto_lib, args.output_dir / "compiled"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
