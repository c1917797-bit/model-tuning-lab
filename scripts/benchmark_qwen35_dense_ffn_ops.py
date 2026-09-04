#!/usr/bin/env python3
"""Benchmark BF16 Qwen3.5 dense FFN layout choices on one Ascend NPU.

Use real layer-0 weights and the TP4 rank-0 shards observed in profiling:
gate/up [8704, 5120], down [5120, 4352]. Quantization is out of scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import time
from pathlib import Path
from typing import Any, Callable


WEIGHT_KEYS = {
    "gate": "model.language_model.layers.0.mlp.gate_proj.weight",
    "up": "model.language_model.layers.0.mlp.up_proj.weight",
    "down": "model.language_model.layers.0.mlp.down_proj.weight",
}
MEASURED_VARIANTS = ("nd", "gate_up_nz", "down_nz", "both_nz")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--m-values", default="1,5,8,16")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--min-geomean-speedup", type=float, default=1.05)
    parser.add_argument("--max-cell-regression", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=1024)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def evaluate_decision(
    cells: list[dict[str, Any]],
    min_geomean_speedup: float = 1.05,
    max_cell_regression: float = 0.02,
) -> dict[str, Any]:
    """Promote only a correct, robust, and economically useful layout."""
    m_values = sorted({int(cell["m"]) for cell in cells if cell["variant"] == "nd"})
    candidates: list[dict[str, Any]] = []
    for variant in sorted({cell["variant"] for cell in cells} - {"nd"}):
        variant_cells = [cell for cell in cells if cell["variant"] == variant]
        complete = sorted(int(cell["m"]) for cell in variant_cells) == m_values
        ok = complete and all(
            cell.get("status") == "ok"
            and cell.get("correctness", {}).get("allclose", False)
            for cell in variant_cells
        )
        speedups = [
            float(cell["speedup_vs_nd"])
            for cell in variant_cells
            if cell.get("status") == "ok" and "speedup_vs_nd" in cell
        ]
        geomean = geometric_mean(speedups) if ok else None
        no_material_regression = bool(
            ok
            and all(
                speedup >= (1.0 - max_cell_regression)
                for speedup in speedups
            )
        )
        eligible = bool(
            no_material_regression
            and geomean is not None
            and geomean >= min_geomean_speedup
        )
        candidates.append(
            {
                "variant": variant,
                "complete": complete,
                "correct_and_runnable": ok,
                "geomean_speedup": geomean,
                "minimum_cell_speedup": min(speedups) if speedups else None,
                "eligible_for_e2e": eligible,
            }
        )
    eligible = [item for item in candidates if item["eligible_for_e2e"]]
    winner = (
        max(eligible, key=lambda item: item["geomean_speedup"])
        if eligible
        else None
    )
    return {
        "decision": (
            "promote-layout-to-e2e" if winner else "reject-built-in-layout-lane"
        ),
        "winner": winner["variant"] if winner else None,
        "min_geomean_speedup": min_geomean_speedup,
        "max_cell_regression": max_cell_regression,
        "candidates": candidates,
    }


def load_tp4_rank0_weights(model_dir: Path):
    import torch
    from safetensors import safe_open

    index_path = model_dir / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index["weight_map"]
    loaded = {}
    for name, key in WEIGHT_KEYS.items():
        shard_path = model_dir / weight_map[key]
        with safe_open(shard_path, framework="pt", device="cpu") as handle:
            loaded[name] = handle.get_tensor(key)

    hidden = int(loaded["gate"].shape[1])
    full_intermediate = int(loaded["gate"].shape[0])
    if full_intermediate % 4:
        raise ValueError(f"intermediate size is not TP4 divisible: {full_intermediate}")
    local_intermediate = full_intermediate // 4
    gate = loaded["gate"][:local_intermediate].contiguous()
    up = loaded["up"][:local_intermediate].contiguous()
    down = loaded["down"][:, :local_intermediate].contiguous()
    gate_up = torch.cat((gate, up), dim=0).contiguous()
    if gate_up.shape != (2 * local_intermediate, hidden):
        raise ValueError(f"unexpected gate/up shard shape: {gate_up.shape}")
    if down.shape != (hidden, local_intermediate):
        raise ValueError(f"unexpected down shard shape: {down.shape}")
    if gate_up.dtype != torch.bfloat16 or down.dtype != torch.bfloat16:
        raise TypeError(
            f"expected BF16 model weights, got {gate_up.dtype} and {down.dtype}"
        )
    return gate_up, down, index_path


def correctness_metrics(reference, candidate) -> dict[str, Any]:
    import torch

    ref = reference.float()
    got = candidate.float()
    delta = (got - ref).abs()
    denominator = ref.abs().clamp_min(1e-5)
    cosine = torch.nn.functional.cosine_similarity(
        ref.reshape(1, -1), got.reshape(1, -1), dim=1
    ).item()
    return {
        "allclose": bool(torch.allclose(got, ref, rtol=0.02, atol=0.02)),
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
        "max_relative_clamped": float((delta / denominator).max().item()),
        "cosine": float(cosine),
    }


def time_callable(
    function: Callable[[], Any],
    synchronize: Callable[[], None],
    warmup: int,
    iterations: int,
) -> float:
    for _ in range(warmup):
        function()
    synchronize()
    start = time.perf_counter_ns()
    for _ in range(iterations):
        function()
    synchronize()
    return (time.perf_counter_ns() - start) / iterations / 1000.0


def main() -> int:
    args = parse_args()
    m_values = [int(value) for value in args.m_values.split(",")]
    if not m_values or any(value <= 0 for value in m_values):
        raise ValueError("--m-values must contain positive integers")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    import torch
    import torch_npu

    torch.manual_seed(args.seed)
    torch.npu.set_device("npu:0")
    torch.npu.config.allow_internal_format = True
    synchronize = torch.npu.synchronize

    gate_up_cpu, down_cpu, index_path = load_tp4_rank0_weights(args.model_dir)
    gate_up_nd = gate_up_cpu.to("npu")
    down_nd = down_cpu.to("npu")
    gate_up_nz = torch_npu.npu_format_cast(gate_up_nd, 29)
    down_nz = torch_npu.npu_format_cast(down_nd, 29)
    synchronize()
    actual_formats = {
        "gate_up_nd": int(torch_npu.get_npu_format(gate_up_nd)),
        "down_nd": int(torch_npu.get_npu_format(down_nd)),
        "gate_up_nz": int(torch_npu.get_npu_format(gate_up_nz)),
        "down_nz": int(torch_npu.get_npu_format(down_nz)),
    }
    if actual_formats["gate_up_nz"] != 29 or actual_formats["down_nz"] != 29:
        raise RuntimeError(
            "NZ format request was not honored; refusing a no-op comparison: "
            f"{actual_formats}"
        )

    layouts = {
        "nd": (gate_up_nd, down_nd),
        "gate_up_nz": (gate_up_nz, down_nd),
        "down_nz": (gate_up_nd, down_nz),
        "both_nz": (gate_up_nz, down_nz),
    }

    def eager_ffn(x, gate_up_weight, down_weight):
        gate_up = torch.nn.functional.linear(x, gate_up_weight)
        activated = torch_npu.npu_swiglu(gate_up, dim=-1)
        return torch.nn.functional.linear(activated, down_weight)

    cells: list[dict[str, Any]] = []
    for m_index, m in enumerate(m_values):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(args.seed + m)
        x = torch.randn(
            (m, gate_up_nd.shape[1]),
            generator=generator,
            dtype=torch.bfloat16,
        ).to("npu")
        reference = eager_ffn(x, gate_up_nd, down_nd)
        synchronize()

        cell_by_variant: dict[str, dict[str, Any]] = {}
        for variant, (gate_up_weight, down_weight) in layouts.items():
            output = eager_ffn(x, gate_up_weight, down_weight)
            synchronize()
            cell_by_variant[variant] = {
                "m": m,
                "variant": variant,
                "status": "ok",
                "weight_formats": {
                    "gate_up": int(torch_npu.get_npu_format(gate_up_weight)),
                    "down": int(torch_npu.get_npu_format(down_weight)),
                },
                "correctness": correctness_metrics(reference, output),
                "repeat_us": [],
            }

        for repeat in range(args.repeats):
            offset = (m_index + repeat) % len(MEASURED_VARIANTS)
            order = MEASURED_VARIANTS[offset:] + MEASURED_VARIANTS[:offset]
            for variant in order:
                gate_up_weight, down_weight = layouts[variant]
                elapsed_us = time_callable(
                    lambda gu=gate_up_weight, dw=down_weight: eager_ffn(x, gu, dw),
                    synchronize,
                    args.warmup,
                    args.iterations,
                )
                cell_by_variant[variant]["repeat_us"].append(elapsed_us)

        baseline_us = statistics.median(cell_by_variant["nd"]["repeat_us"])
        for variant in MEASURED_VARIANTS:
            cell = cell_by_variant[variant]
            cell["median_us"] = statistics.median(cell["repeat_us"])
            cell["min_us"] = min(cell["repeat_us"])
            cell["max_us"] = max(cell["repeat_us"])
            cell["speedup_vs_nd"] = baseline_us / cell["median_us"]
            cells.append(cell)

        control: dict[str, Any] = {
            "m": m,
            "variant": "npu_ffn_bf16_swiglu",
            "status": "not-run",
        }
        try:
            weight1 = gate_up_nd.transpose(0, 1).contiguous()
            weight2 = down_nd.transpose(0, 1).contiguous()
            output = torch_npu.npu_ffn(
                x, weight1, weight2, "swiglu", inner_precise=0
            )
            synchronize()
            control.update(
                {
                    "status": "ok",
                    "correctness": correctness_metrics(reference, output),
                    "repeat_us": [
                        time_callable(
                            lambda: torch_npu.npu_ffn(
                                x,
                                weight1,
                                weight2,
                                "swiglu",
                                inner_precise=0,
                            ),
                            synchronize,
                            args.warmup,
                            args.iterations,
                        )
                        for _ in range(args.repeats)
                    ],
                }
            )
            control["median_us"] = statistics.median(control["repeat_us"])
            control["speedup_vs_nd"] = baseline_us / control["median_us"]
        except Exception as error:
            control.update(
                {
                    "status": "unsupported",
                    "error_type": type(error).__name__,
                    "error": str(error)[:4000],
                }
            )
        cells.append(control)

    decision = evaluate_decision(
        cells,
        min_geomean_speedup=args.min_geomean_speedup,
        max_cell_regression=args.max_cell_regression,
    )
    report = {
        "schema_version": 1,
        "benchmark": "qwen35-dense-ffn-bf16-layout",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "resource_boundary": {
            "host": platform.node(),
            "physical_npu": 4,
            "container_visible_npu": 0,
            "forbidden_physical_npus": [0, 1, 2, 3],
        },
        "software": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "torch_npu": torch_npu.__version__,
            "image": "quay.io/ascend/vllm-ascend:v0.23.0",
        },
        "model": {
            "path": str(args.model_dir),
            "index_sha256": sha256_file(index_path),
            "weight_keys": WEIGHT_KEYS,
            "tp_size": 4,
            "tp_rank": 0,
            "dtype": "bfloat16",
            "gate_up_shape": list(gate_up_nd.shape),
            "down_shape": list(down_nd.shape),
        },
        "protocol": {
            "m_values": m_values,
            "warmup": args.warmup,
            "iterations": args.iterations,
            "repeats": args.repeats,
            "seed": args.seed,
            "timing": "host-perf-counter-with-npu-synchronize",
            "variant_order": "rotated-per-repeat",
            "actual_weight_formats": actual_formats,
        },
        "environment": {
            name: os.environ.get(name)
            for name in (
                "ASCEND_RT_VISIBLE_DEVICES",
                "OMP_NUM_THREADS",
                "TASK_QUEUE_ENABLE",
            )
        },
        "cells": cells,
        "decision": decision,
    }
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "decision": decision["decision"],
                "winner": decision["winner"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
