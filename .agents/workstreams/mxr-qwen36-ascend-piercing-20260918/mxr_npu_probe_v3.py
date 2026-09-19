#!/usr/bin/env python3
"""Run the real NPU canary and MXR gate in one process/container namespace."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import mxr_npu_probe as probe


def output_dir_from_argv() -> Path:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--output-dir", required=True, type=Path)
    args, _unknown = parser.parse_known_args()
    return args.output_dir


def run_canary(output_dir: Path) -> dict:
    import torch
    import torch_npu  # noqa: F401

    path = output_dir / "canary.json"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite {path}")
    torch.npu.set_device(0)
    device = torch.device("npu:0")
    values = torch.arange(1, 33, dtype=torch.float32, device=device)
    observed = float((values * values).sum().cpu())
    torch.npu.synchronize()
    expected = 11440.0
    result = {
        "schema": "mst.mxr.in-container-canary/v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "logical_device": 0,
        "device": torch.npu.get_device_name(0),
        "operation": "sum(square(arange(1, 33)))",
        "expected": expected,
        "observed": observed,
        "ok": observed == expected,
    }
    probe.atomic_json(path, result)
    if not result["ok"]:
        raise RuntimeError(f"NPU canary mismatch: {result}")
    return result


if __name__ == "__main__":
    output_dir = output_dir_from_argv()
    if not output_dir.is_dir():
        raise RuntimeError("output directory must already exist")
    run_canary(output_dir)
    raise SystemExit(probe.main())
