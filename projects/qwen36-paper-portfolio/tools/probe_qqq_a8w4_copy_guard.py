"""Test a copy-guard for the observed native A8W4 activation mutation."""

import argparse
import json
import os
import traceback
from pathlib import Path

import torch
import torch_npu

from probe_qqq_a8w4_v5 import comparison


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--physical-npu", required=True, type=int)
    args = parser.parse_args()
    destination = Path(args.output_file)
    if args.physical_npu != 4 or not destination.parent.is_dir() or destination.exists():
        raise ValueError("requires physical NPU4 and a new result file")
    report = {
        "schema": "qqq-a8w4-copy-guard/v3",
        "scope": "native A8W4 input-preservation, numerical and graph gate; not QQQ model or E2E",
        "physical_npu_declared": 4,
        "status": "started",
        "numeric_gate": {"reference_relative_rms_max": 0.01, "replay_relative_rms_max": 0.0001},
    }
    try:
        torch.npu.set_device(0)
        if torch.npu.device_count() != 1:
            raise RuntimeError("expected exactly one visible NPU")
        torch.manual_seed(20260928)
        m, k, n = 16, 5120, 8704
        report["shape"] = {"M": m, "K": k, "N": n}
        q_a_cpu = torch.randint(-24, 25, (m, k), dtype=torch.int8)
        q_w_cpu = torch.randint(-7, 8, (k, n), dtype=torch.int32)
        s_a_cpu = torch.full((m,), 1 / 32, dtype=torch.float32)
        s_w_cpu = torch.full((n,), 1 / 64, dtype=torch.float32)
        offset_cpu = 8 * q_w_cpu.float().sum(0) * s_w_cpu
        reference = (
            (q_a_cpu.float() @ q_w_cpu.float()) * s_a_cpu[:, None] * s_w_cpu[None, :]
        ).bfloat16()
        pristine = q_a_cpu.npu()
        packed = torch_npu.npu_convert_weight_to_int4pack(q_w_cpu.npu())
        s_a = s_a_cpu.npu()
        s_w = torch_npu.npu_trans_quant_param(s_w_cpu.npu())
        offset = offset_cpu.npu()

        def kernel(activation: torch.Tensor) -> torch.Tensor:
            return torch_npu.npu_quant_matmul(
                activation,
                packed,
                s_w,
                offset=offset,
                pertoken_scale=s_a,
                output_dtype=torch.bfloat16,
            )

        sacrificed = pristine.clone()
        unguarded = kernel(sacrificed)
        torch.npu.synchronize()
        difference = sacrificed.cpu().to(torch.int16) - q_a_cpu.to(torch.int16)
        report["raw_input_mutation"] = {
            "changed_elements": int(torch.count_nonzero(difference).item()),
            "delta_min": int(difference.min().item()),
            "delta_max": int(difference.max().item()),
            "delta_values_first_16": difference.unique().tolist()[:16],
            "first_output_vs_reference": comparison(unguarded.cpu(), reference),
        }

        def guarded() -> torch.Tensor:
            return kernel(pristine.clone())

        eager_first = guarded()
        torch.npu.synchronize()
        eager_first_cpu = eager_first.cpu().clone()
        eager_second = guarded()
        torch.npu.synchronize()
        eager_second_cpu = eager_second.cpu().clone()
        report["eager_first_vs_reference"] = comparison(eager_first_cpu, reference)
        report["eager_second_vs_reference"] = comparison(eager_second_cpu, reference)
        report["eager_repeat"] = comparison(eager_second_cpu, eager_first_cpu)
        report["source_activation_unchanged_after_eager"] = bool(torch.equal(pristine.cpu(), q_a_cpu))

        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_output = guarded()
        torch.npu.synchronize()
        graph.replay()
        torch.npu.synchronize()
        replay_first_cpu = graph_output.cpu().clone()
        graph.replay()
        torch.npu.synchronize()
        replay_second_cpu = graph_output.cpu().clone()
        report["graph_first_vs_reference"] = comparison(replay_first_cpu, reference)
        report["graph_repeat"] = comparison(replay_second_cpu, replay_first_cpu)
        report["graph_vs_eager"] = comparison(replay_first_cpu, eager_first_cpu)
        report["source_activation_unchanged_after_graph"] = bool(torch.equal(pristine.cpu(), q_a_cpu))

        report["numeric_gate_passed"] = bool(
            report["source_activation_unchanged_after_graph"]
            and all(
                report[key]["relative_rms"] <= 0.01
                for key in (
                    "eager_first_vs_reference",
                    "eager_second_vs_reference",
                    "graph_first_vs_reference",
                )
            )
            and all(
                report[key]["relative_rms"] <= 0.0001
                for key in ("eager_repeat", "graph_repeat", "graph_vs_eager")
            )
        )
        report["status"] = "passed" if report["numeric_gate_passed"] else "failed"
        if not report["numeric_gate_passed"]:
            raise AssertionError("copy-guard native A8W4 gate failed")
    except Exception:
        report["status"] = "failed"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644), "w") as file:
            json.dump(report, file, indent=2, sort_keys=True)
            file.write("\n")


if __name__ == "__main__":
    main()
