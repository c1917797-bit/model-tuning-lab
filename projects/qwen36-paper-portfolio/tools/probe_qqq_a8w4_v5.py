"""One-shot native A8W4 arithmetic gate for QQQ; not a QQQ model benchmark."""

import argparse
import json
import os
import traceback
from pathlib import Path

import torch
import torch_npu


def relative_rms(actual: torch.Tensor, reference: torch.Tensor) -> float:
    a = actual.float()
    b = reference.float()
    return float(((a - b).square().mean() / b.square().mean().clamp_min(1e-20)).sqrt().item())


def comparison(actual: torch.Tensor, reference: torch.Tensor) -> dict:
    a = actual.float()
    b = reference.float()
    return {
        "bitwise_equal": bool(torch.equal(actual, reference)),
        "max_abs": float((a - b).abs().max().item()),
        "relative_rms": relative_rms(actual, reference),
        "different_elements": int(torch.count_nonzero(actual != reference).item()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--physical-npu", required=True, type=int)
    args = parser.parse_args()
    destination = Path(args.output_file)
    if args.physical_npu != 4 or not destination.parent.is_dir() or destination.exists():
        raise ValueError("requires physical NPU4 and a new file in an existing output directory")

    result = {
        "schema": "qqq-a8w4-v5-substrate/v1",
        "scope": "native INT8-activation/packed-INT4-weight arithmetic only; not QQQ calibration, service, throughput, or task accuracy",
        "physical_npu_declared": args.physical_npu,
        "status": "started",
        "formula": "s_a[m] * sum_k(q_a[m,k] * q_w[k,n] * s_w[n])",
        "y_offset": "8 * sum_k(q_w[k,n] * s_w[n]), per CANN9.1 A8W4 contract",
        "numeric_gate": {
            "vs_fp32_reference_relative_rms_max": 0.01,
            "repeat_and_graph_relative_rms_max": 0.0001,
        },
    }
    try:
        torch.npu.set_device(0)
        if torch.npu.device_count() != 1:
            raise RuntimeError(f"expected exactly one visible NPU, got {torch.npu.device_count()}")
        torch.manual_seed(20260928)
        m, k, n = 16, 5120, 8704
        result["shape"] = {"M": m, "K": k, "N": n}
        result["torch_npu_version"] = torch_npu.__version__
        result["operator_schema"] = str(torch._C._get_schema("npu::npu_quant_matmul", ""))

        q_a_cpu = torch.randint(-24, 25, (m, k), dtype=torch.int8)
        q_w_cpu = torch.randint(-7, 8, (k, n), dtype=torch.int32)
        s_a_cpu = torch.full((m,), 1 / 32, dtype=torch.float32)
        s_w_cpu = torch.full((n,), 1 / 64, dtype=torch.float32)
        y_offset_cpu = 8 * q_w_cpu.float().sum(0) * s_w_cpu
        expected = (
            (q_a_cpu.float() @ q_w_cpu.float())
            * s_a_cpu[:, None]
            * s_w_cpu[None, :]
        ).bfloat16()

        q_a = q_a_cpu.npu()
        q_w = q_w_cpu.npu()
        packed = torch_npu.npu_convert_weight_to_int4pack(q_w)
        s_a = s_a_cpu.npu()
        s_w_packed = torch_npu.npu_trans_quant_param(s_w_cpu.npu())
        y_offset = y_offset_cpu.npu()
        result["packed_weight_shape"] = list(packed.shape)
        result["packed_weight_dtype"] = str(packed.dtype)
        result["transformed_scale_dtype"] = str(s_w_packed.dtype)

        def native() -> torch.Tensor:
            return torch_npu.npu_quant_matmul(
                q_a,
                packed,
                s_w_packed,
                offset=y_offset,
                pertoken_scale=s_a,
                output_dtype=torch.bfloat16,
            )

        first = native()
        second = native()
        torch.npu.synchronize()
        result["finite"] = bool(torch.isfinite(first).all().item())
        result["eager_vs_reference"] = comparison(first.cpu(), expected)
        result["eager_repeat"] = comparison(second.cpu(), first.cpu())

        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_output = native()
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        replay = graph_output.clone()
        result["graph_vs_eager"] = comparison(replay.cpu(), first.cpu())

        result["numeric_gate_passed"] = bool(
            result["finite"]
            and result["eager_vs_reference"]["relative_rms"] <= 0.01
            and result["eager_repeat"]["relative_rms"] <= 0.0001
            and result["graph_vs_eager"]["relative_rms"] <= 0.0001
        )
        result["status"] = "passed" if result["numeric_gate_passed"] else "failed"
        if not result["numeric_gate_passed"]:
            raise AssertionError("native A8W4 numerical gate failed; inspect immutable metrics")
    except Exception:
        result["status"] = "failed"
        result["traceback"] = traceback.format_exc()
        raise
    finally:
        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w") as file:
            json.dump(result, file, indent=2, sort_keys=True)
            file.write("\n")


if __name__ == "__main__":
    main()
