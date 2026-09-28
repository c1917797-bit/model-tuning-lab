"""Diagnose the immutable A8W4 v1 eager-repeat failure without timing claims."""

import argparse
import json
import os
import traceback
from pathlib import Path

import torch
import torch_npu

from probe_qqq_a8w4_v5 import comparison


def case(m: int, k: int, n: int) -> dict:
    q_a_cpu = torch.randint(-24, 25, (m, k), dtype=torch.int8)
    q_w_cpu = torch.randint(-7, 8, (k, n), dtype=torch.int32)
    s_a_cpu = torch.full((m,), 1 / 32, dtype=torch.float32)
    s_w_cpu = torch.full((n,), 1 / 64, dtype=torch.float32)
    y_offset_cpu = 8 * q_w_cpu.float().sum(0) * s_w_cpu
    expected = (
        (q_a_cpu.float() @ q_w_cpu.float()) * s_a_cpu[:, None] * s_w_cpu[None, :]
    ).bfloat16()
    original = {
        "activation": q_a_cpu.npu(),
        "weight": torch_npu.npu_convert_weight_to_int4pack(q_w_cpu.npu()),
        "activation_scale": s_a_cpu.npu(),
        "weight_scale": torch_npu.npu_trans_quant_param(s_w_cpu.npu()),
        "y_offset": y_offset_cpu.npu(),
    }
    saved = {name: value.clone() for name, value in original.items()}

    def run(inputs: dict) -> torch.Tensor:
        return torch_npu.npu_quant_matmul(
            inputs["activation"],
            inputs["weight"],
            inputs["weight_scale"],
            offset=inputs["y_offset"],
            pertoken_scale=inputs["activation_scale"],
            output_dtype=torch.bfloat16,
        )

    observations = {"shape": {"M": m, "K": k, "N": n}}
    for label, inputs in (("first", original), ("second", original), ("fresh_buffers", saved)):
        output = run(inputs)
        torch.npu.synchronize()
        cpu = output.cpu().clone()
        observations[label] = {
            "versus_reference": comparison(cpu, expected),
            "finite": bool(torch.isfinite(cpu).all().item()),
            "sample": cpu.flatten()[:8].float().tolist(),
        }
        if label == "first":
            first_cpu = cpu
        else:
            observations[label]["versus_first"] = comparison(cpu, first_cpu)
        observations[label]["input_unchanged"] = {
            name: bool(torch.equal(original[name], saved[name])) for name in original
        }
    observations["all_outputs_within_1pct_reference_rms"] = all(
        observations[label]["versus_reference"]["relative_rms"] <= 0.01
        for label in ("first", "second", "fresh_buffers")
    )
    return observations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--physical-npu", required=True, type=int)
    args = parser.parse_args()
    destination = Path(args.output_file)
    if args.physical_npu != 4 or not destination.parent.is_dir() or destination.exists():
        raise ValueError("requires physical NPU4 and a new file in an existing output directory")
    report = {
        "schema": "qqq-a8w4-v5-replay-diagnostic/v2",
        "scope": "input-mutation, explicit-sync, and shape diagnosis of native A8W4; not QQQ or E2E",
        "physical_npu_declared": args.physical_npu,
        "status": "started",
    }
    try:
        torch.npu.set_device(0)
        if torch.npu.device_count() != 1:
            raise RuntimeError("expected exactly one visible NPU")
        torch.manual_seed(20260928)
        report["cases"] = [case(16, 5120, 512), case(16, 5120, 8704)]
        report["status"] = "diagnosed"
    except Exception:
        report["status"] = "failed_to_diagnose"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w") as file:
            json.dump(report, file, indent=2, sort_keys=True)
            file.write("\n")


if __name__ == "__main__":
    main()
