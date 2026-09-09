#!/usr/bin/env python3
"""Quantify the decode budget for Qwen3.5 SwiGLU -> K4352 MMAR fusion.

This is an offline evidence tool. It reads existing msprof ``op_summary``
CSVs and never touches an NPU. It fails closed when the profile does not have
the expected TP4/Qwen3.5 M=1 call structure.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
from collections import defaultdict


SWIGLU_NAME = "SwiGlu"
K4352_MMAR_NAME = "MatmulAllReduce"
K4352_SHAPE = "1,4352;4352,5120"


def _rank_from_path(path: str) -> str:
    for part in os.path.normpath(path).split(os.sep):
        if part.startswith("rank") and part[4:].isdigit():
            return part
    raise ValueError(f"cannot resolve rank directory from {path}")


def _walk_numbers(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_numbers(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_numbers(child)
    elif isinstance(value, float):
        yield value


def analyze(profile_root: str, layers: int, required_chain_speedup: float) -> dict:
    if layers <= 0:
        raise ValueError("layers must be positive")
    if required_chain_speedup <= 1.0:
        raise ValueError("required_chain_speedup must be greater than 1")

    files = sorted(glob.glob(os.path.join(profile_root, "**", "op_summary*.csv"), recursive=True))
    if not files:
        raise ValueError(f"no op_summary CSVs under {profile_root}")

    totals = defaultdict(lambda: defaultdict(lambda: {"count": 0, "duration_us": 0.0}))
    for path in files:
        rank = _rank_from_path(path)
        with open(path, newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                try:
                    duration_us = float(row["Task Duration(us)"])
                except (KeyError, TypeError, ValueError):
                    continue
                name = row.get("Op Name", "")
                shape = row.get("Input Shapes", "")
                key = None
                if name == SWIGLU_NAME and "1,8704" in shape:
                    key = "swiglu_m1"
                elif name == K4352_MMAR_NAME and K4352_SHAPE in shape:
                    key = "k4352_mmar_m1"
                if key:
                    totals[rank][key]["count"] += 1
                    totals[rank][key]["duration_us"] += duration_us

    if len(totals) != 4:
        raise ValueError(f"expected exactly four TP ranks, found {sorted(totals)}")

    rank_rows = {}
    inferred_steps = None
    for rank in sorted(totals):
        swiglu = totals[rank]["swiglu_m1"]
        mmar = totals[rank]["k4352_mmar_m1"]
        if swiglu["count"] != mmar["count"]:
            raise ValueError(f"{rank}: SwiGLU/MMAR call-count mismatch")
        if mmar["count"] == 0 or mmar["count"] % layers:
            raise ValueError(f"{rank}: M=1 MMAR count is not divisible by {layers} layers")
        steps = mmar["count"] // layers
        if inferred_steps is None:
            inferred_steps = steps
        elif steps != inferred_steps:
            raise ValueError(f"{rank}: decode-step count {steps} differs from {inferred_steps}")

        swiglu_per_step = swiglu["duration_us"] / steps
        mmar_per_step = mmar["duration_us"] / steps
        rank_rows[rank] = {
            "decode_steps": steps,
            "calls_per_step": layers,
            "swiglu_us_per_step": swiglu_per_step,
            "k4352_mmar_us_per_step": mmar_per_step,
            "stock_chain_us_per_step": swiglu_per_step + mmar_per_step,
        }

    slowest_rank = max(rank_rows, key=lambda rank: rank_rows[rank]["stock_chain_us_per_step"])
    slow = rank_rows[slowest_rank]
    target_chain = slow["stock_chain_us_per_step"] / required_chain_speedup
    total_savings = slow["stock_chain_us_per_step"] - target_chain
    activation_only_speedup_ceiling = slow["stock_chain_us_per_step"] / slow["k4352_mmar_us_per_step"]
    non_activation_savings = max(0.0, total_savings - slow["swiglu_us_per_step"])

    result = {
        "schema": "qwen35-dense-tail-budget/v1",
        "profile_root": os.path.abspath(profile_root),
        "tp_size": 4,
        "layers": layers,
        "decode_steps": inferred_steps,
        "required_chain_speedup": required_chain_speedup,
        "ranks": rank_rows,
        "slowest_rank": slowest_rank,
        "max_rank_stock_chain_us_per_step": slow["stock_chain_us_per_step"],
        "max_rank_swiglu_us_per_step": slow["swiglu_us_per_step"],
        "max_rank_k4352_mmar_us_per_step": slow["k4352_mmar_us_per_step"],
        "activation_fraction_of_chain": slow["swiglu_us_per_step"] / slow["stock_chain_us_per_step"],
        "activation_only_speedup_ceiling": activation_only_speedup_ceiling,
        "target_chain_us_per_step": target_chain,
        "required_total_savings_us_per_step": total_savings,
        "required_non_activation_savings_us_per_step": non_activation_savings,
        "required_non_activation_savings_us_per_call": non_activation_savings / layers,
        "decision": (
            "requires-device-boundary-fusion"
            if activation_only_speedup_ceiling + 1e-12 < required_chain_speedup
            else "activation-only-could-reach-gate"
        ),
        "claim_boundary": (
            "Offline kernel-budget evidence only. Summed op durations are not end-to-end TPOT and "
            "MatmulAllReduceMc2AicpuKernel is intentionally excluded because it overlaps MMAR."
        ),
    }
    for value in _walk_numbers(result):
        if not math.isfinite(value):
            raise ValueError("non-finite result")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile_root")
    parser.add_argument("--layers", type=int, default=64)
    parser.add_argument("--required-chain-speedup", type=float, default=1.15)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = analyze(args.profile_root, args.layers, args.required_chain_speedup)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
