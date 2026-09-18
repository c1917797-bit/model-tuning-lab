#!/usr/bin/env python3
"""One-shot MXR/PTO numerical and target-shape timing probe on Ascend.

This program is intentionally independent of the final plugin adapter. It
imports one exact official source snapshot and produces admission evidence.
Timing is never executed when the numerical gate fails.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Callable


H = 12
HG = 4
D = 128
C_PTO = 128
CORRECTNESS_LENGTHS = (128, 192, 256)
TIMING_LENGTHS = (4096, 16384)
FROB_REL_LIMIT = 2.0e-3
RMSE_OVER_MEAN_LIMIT = 2.0e-2
R2_MIN = 0.999
MIN_CLEAR_SPEEDUP = 1.10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_metrics(actual, expected) -> dict:
    import torch

    if tuple(actual.shape) != tuple(expected.shape):
        return {
            "ok": False,
            "shape_actual": list(actual.shape),
            "shape_expected": list(expected.shape),
            "reason": "shape_mismatch",
        }
    actual64 = actual.detach().double().cpu()
    expected64 = expected.detach().double().cpu()
    finite = bool(torch.isfinite(actual64).all() and torch.isfinite(expected64).all())
    diff = actual64 - expected64
    abs_diff = diff.abs().flatten()
    ref = expected64.flatten()
    ref_norm = float(torch.linalg.vector_norm(ref))
    frob = float(torch.linalg.vector_norm(diff.flatten())) / max(ref_norm, 1.0e-30)
    rmse = float(torch.sqrt(torch.mean(diff.flatten() ** 2)))
    mean_ref_abs = float(ref.abs().mean())
    ratio = rmse / max(mean_ref_abs, 1.0e-30)
    centered = ref - ref.mean()
    ss_tot = float(torch.sum(centered**2))
    ss_res = float(torch.sum(diff.flatten() ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, 1.0e-30)
    result = {
        "finite": finite,
        "max_abs": float(abs_diff.max()),
        "mean_abs": float(abs_diff.mean()),
        "p99_abs": float(torch.quantile(abs_diff, 0.99)),
        "frob_relative": frob,
        "rmse_over_mean_ref_abs": ratio,
        "r2": r2,
        "limits": {
            "frob_relative": FROB_REL_LIMIT,
            "rmse_over_mean_ref_abs": RMSE_OVER_MEAN_LIMIT,
            "r2_min": R2_MIN,
        },
    }
    result["ok"] = bool(
        finite
        and frob <= FROB_REL_LIMIT
        and ratio <= RMSE_OVER_MEAN_LIMIT
        and r2 >= R2_MIN
    )
    return result


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def configure_imports(source_root: Path, pto_lib: Path, compiled_dir: Path) -> None:
    os.environ["PTO_LIB_PATH"] = str(pto_lib)
    os.environ["GDN_COMPILED_DIR"] = str(compiled_dir)
    os.environ["PTO_MEMORY_MODEL"] = "MEMORY_BASE"
    sys.path.insert(0, str(source_root))
    # Avoid importing an unrelated site-packages tests namespace.
    for name in tuple(sys.modules):
        if name == "tests" or name.startswith("tests."):
            del sys.modules[name]


def make_inputs(torch, device, length: int, seed: int):
    torch.manual_seed(seed)
    torch.npu.manual_seed(seed)
    functional = importlib.import_module("torch.nn.functional")
    q = functional.normalize(
        torch.randn(1, length, HG, D, dtype=torch.float16, device=device), p=2, dim=-1
    )
    k = functional.normalize(
        torch.randn(1, length, HG, D, dtype=torch.float16, device=device), p=2, dim=-1
    )
    v = torch.randn(1, length, H, D, dtype=torch.float16, device=device)
    beta = torch.rand(1, length, H, dtype=torch.float16, device=device)
    g = functional.logsigmoid(
        torch.randn(1, length, H, dtype=torch.float32, device=device)
    )
    cu32 = torch.tensor([0, length], dtype=torch.int32, device=device)
    return q, k, v, g, beta, cu32


def load_implementations():
    import torch
    from megagdn_pto.fast_inverse import load_tri_inverse
    from megagdn_pto.mega_kernel import run_mega_kernel
    from tests.ref_gdn import RefGDN
    from tests.test_gdn_e2e import pto_pipeline
    from vllm_ascend.ops.triton.fla.chunk import chunk_gated_delta_rule as baseline
    from vllm_ascend.ops.triton.fla.solve_tril import solve_tril as baseline_solve

    tri_inverse = load_tri_inverse()

    def staged(q, k, v, g, beta, cu32, state):
        return pto_pipeline(
            q,
            k,
            v,
            g,
            beta,
            cu32,
            H,
            HG,
            D**-0.5,
            tri_inverse,
            initial_state=state,
            return_final_state=True,
        )

    def mega(q, k, v, g, beta, cu32, state):
        return run_mega_kernel(
            q,
            k,
            v,
            g,
            beta,
            cu32,
            chunk_size=C_PTO,
            scale=D**-0.5,
            key_heads=HG,
            initial_state=state,
            return_final_state=True,
        )

    def triton(q, k, v, g, beta, cu32, state):
        return baseline(
            q,
            k,
            v,
            g,
            beta,
            scale=D**-0.5,
            initial_state=state,
            output_final_state=True,
            cu_seqlens=cu32.long(),
            prebuilt_meta=None,
            head_first=False,
            use_qk_l2norm_in_kernel=False,
        )

    return torch, RefGDN, tri_inverse, baseline_solve, {
        "v023_triton": triton,
        "pto_staged": staged,
        "pto_mega": mega,
    }


def run_correctness(torch, RefGDN, methods: dict[str, Callable], device) -> dict:
    inputs = [
        make_inputs(torch, device, length, 1701 + index)
        for index, length in enumerate(CORRECTNESS_LENGTHS)
    ]
    torch.manual_seed(991)
    initial = (
        0.01 * torch.randn(1, H, D, D, device=device, dtype=torch.float16)
    ).contiguous()
    ref = RefGDN(torch.double)
    ref_state = initial.cpu()
    reference = []
    for q, k, v, g, beta, _cu32 in inputs:
        out, state = ref.run_full_pipeline(
            q.cpu(),
            k.cpu(),
            v.cpu(),
            g.cpu(),
            beta.cpu(),
            None,
            H,
            HG,
            D**-0.5,
            initial_state=ref_state,
            return_final_state=True,
        )
        reference.append((out, state))
        ref_state = state

    results = {}
    all_ok = True
    for name, method in methods.items():
        state = initial.clone()
        steps = []
        for index, ((q, k, v, g, beta, cu32), (ref_out, ref_state_out)) in enumerate(
            zip(inputs, reference)
        ):
            out, state = method(q, k, v, g, beta, cu32, state)
            torch.npu.synchronize()
            output_metrics = tensor_metrics(out, ref_out)
            state_metrics = tensor_metrics(state, ref_state_out)
            step_ok = bool(output_metrics["ok"] and state_metrics["ok"])
            steps.append(
                {
                    "step": index,
                    "length": int(q.shape[1]),
                    "output": output_metrics,
                    "final_state": state_metrics,
                    "ok": step_ok,
                }
            )
            all_ok = all_ok and step_ok

        q, k, v, g, beta, cu32 = inputs[0]
        first = method(q, k, v, g, beta, cu32, initial.clone())
        second = method(q, k, v, g, beta, cu32, initial.clone())
        torch.npu.synchronize()
        deterministic = bool(
            torch.equal(first[0], second[0]) and torch.equal(first[1], second[1])
        )
        all_ok = all_ok and deterministic
        results[name] = {
            "steps": steps,
            "bitwise_replay": deterministic,
            "ok": bool(deterministic and all(step["ok"] for step in steps)),
        }

    return {
        "schema": "mst.mxr.numerical-gate/v1",
        "shape": {"H": H, "Hg": HG, "D": D, "chunk_pto": C_PTO},
        "lengths": list(CORRECTNESS_LENGTHS),
        "methods": results,
        "ok": all_ok,
    }


def timed_ms(torch, function: Callable, warmup: int = 5, repeats: int = 20) -> dict:
    for _ in range(warmup):
        function()
    torch.npu.synchronize()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        function()
        torch.npu.synchronize()
        samples.append((time.perf_counter() - start) * 1000.0)
    ordered = sorted(samples)
    return {
        "warmup": warmup,
        "repeats": repeats,
        "median_ms": statistics.median(samples),
        "mean_ms": statistics.fmean(samples),
        "min_ms": ordered[0],
        "p20_ms": ordered[math.floor(0.20 * (len(ordered) - 1))],
        "p80_ms": ordered[math.floor(0.80 * (len(ordered) - 1))],
        "p95_ms": ordered[math.floor(0.95 * (len(ordered) - 1))],
    }


def make_triangular_input(torch, device, length: int, chunk: int = 64):
    torch.manual_seed(773)
    values = 0.01 * torch.randn(1, length, H, chunk, dtype=torch.float16, device=device)
    row = torch.arange(length, device=device).remainder(chunk)
    col = torch.arange(chunk, device=device)
    mask = col.unsqueeze(0) < row.unsqueeze(1)
    return values * mask.unsqueeze(0).unsqueeze(2)


def run_timing(torch, tri_inverse, baseline_solve, methods, device) -> dict:
    from megagdn_pto.fast_inverse import solve_tril as mxr_solve

    by_length = {}
    tri_by_length = {}
    for length in TIMING_LENGTHS:
        q, k, v, g, beta, cu32 = make_inputs(torch, device, length, 2800 + length)
        state = torch.zeros(1, H, D, D, device=device, dtype=torch.float16)
        method_rows = {}
        for name, method in methods.items():
            method_rows[name] = timed_ms(
                torch,
                lambda method=method: method(q, k, v, g, beta, cu32, state),
            )
        baseline_ms = method_rows["v023_triton"]["median_ms"]
        for name, row in method_rows.items():
            row["speedup_vs_v023_triton"] = baseline_ms / row["median_ms"]
        by_length[str(length)] = method_rows

        tri_input = make_triangular_input(torch, device, length, 64)
        tri_cu32 = torch.tensor([0, length], dtype=torch.int32, device=device)
        baseline_row = timed_ms(
            torch,
            lambda: baseline_solve(
                tri_input,
                cu_seqlens=tri_cu32.long(),
                output_dtype=torch.float16,
            ),
        )
        mxr_row = timed_ms(
            torch,
            lambda: mxr_solve(tri_input, tri_cu32, 64, H, tri_inverse),
        )
        mxr_row["speedup_vs_v023_solve_tril"] = baseline_row["median_ms"] / mxr_row["median_ms"]
        tri_by_length[str(length)] = {
            "v023_solve_tril": baseline_row,
            "mxr_solve_tril": mxr_row,
        }

    full_candidates = ("pto_staged", "pto_mega")
    full_clear = all(
        max(rows[name]["speedup_vs_v023_triton"] for name in full_candidates)
        >= MIN_CLEAR_SPEEDUP
        for rows in by_length.values()
    )
    tri_clear = all(
        rows["mxr_solve_tril"]["speedup_vs_v023_solve_tril"] >= MIN_CLEAR_SPEEDUP
        for rows in tri_by_length.values()
    )
    return {
        "schema": "mst.mxr.target-shape-timing/v1",
        "shape": {"H": H, "Hg": HG, "D": D},
        "lengths": list(TIMING_LENGTHS),
        "minimum_clear_speedup": MIN_CLEAR_SPEEDUP,
        "triangular_inverse": tri_by_length,
        "full_gdn": by_length,
        "triangular_inverse_clear_advantage": tri_clear,
        "full_gdn_clear_advantage": full_clear,
        "ok": bool(tri_clear and full_clear),
    }


def environment_manifest(torch, source_root: Path, pto_lib: Path, compiled_dir: Path) -> dict:
    libraries = []
    for path in sorted(compiled_dir.glob("*.so")):
        libraries.append({"path": str(path), "sha256": sha256(path), "size": path.stat().st_size})
    return {
        "schema": "mst.mxr.npu-runtime/v1",
        "python": sys.version,
        "torch": torch.__version__,
        "torch_npu": getattr(importlib.import_module("torch_npu"), "__version__", "unknown"),
        "device": torch.npu.get_device_name(0),
        "source_root": str(source_root),
        "pto_lib": str(pto_lib),
        "pto_memory_model": os.environ["PTO_MEMORY_MODEL"],
        "compiled_libraries": libraries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--pto-lib", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--phase", choices=("correctness", "timing", "all"), default="all")
    args = parser.parse_args()
    if not args.output_dir.is_dir():
        raise RuntimeError("output directory must already exist")
    for name in ("numerical-gate.json", "target-shape-timing.json", "runtime-manifest.json"):
        if (args.output_dir / name).exists():
            raise RuntimeError(f"refusing to overwrite {name}")

    configure_imports(args.source_root, args.pto_lib, args.output_dir / "compiled")
    import torch
    import torch_npu  # noqa: F401

    torch.npu.set_device(0)
    device = torch.device("npu:0")
    torch, RefGDN, tri_inverse, baseline_solve, methods = load_implementations()

    numerical = None
    if args.phase in {"correctness", "all"}:
        numerical = run_correctness(torch, RefGDN, methods, device)
        atomic_json(args.output_dir / "numerical-gate.json", numerical)
        if not numerical["ok"]:
            atomic_json(
                args.output_dir / "runtime-manifest.json",
                environment_manifest(torch, args.source_root, args.pto_lib, args.output_dir / "compiled"),
            )
            return 3

    if args.phase in {"timing", "all"}:
        timing = run_timing(torch, tri_inverse, baseline_solve, methods, device)
        atomic_json(args.output_dir / "target-shape-timing.json", timing)

    atomic_json(
        args.output_dir / "runtime-manifest.json",
        environment_manifest(torch, args.source_root, args.pto_lib, args.output_dir / "compiled"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
