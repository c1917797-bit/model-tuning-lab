"""One-card Ascend ABI probe for batching two Ada-KV selected-support FIAs.

This checks whether the deployed native TND FIA can replace two per-request
decode launches with one variable-length grouped launch. It is not a service
integration, performance claim, or final numerical acceptance test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
import torch_npu


def metrics(actual: torch.Tensor, expected: torch.Tensor) -> dict:
    a, b = actual.float().flatten(), expected.float().flatten()
    delta = a - b
    rms = delta.square().mean().sqrt()
    base = b.square().mean().sqrt()
    return {"relative_rms": float((rms / base).item()),
            "max_abs": float(delta.abs().max().item()),
            "cosine": float(torch.nn.functional.cosine_similarity(a, b, dim=0).item())}


def fia(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor,
        q_ends: list[int], kv_ends: list[int]) -> torch.Tensor:
    output, _ = torch_npu.npu_fused_infer_attention_score(
        query=q, key=k, value=v, input_layout="TND",
        actual_seq_lengths=q_ends, actual_seq_lengths_kv=kv_ends,
        num_key_value_heads=1, num_heads=6, scale=256 ** -0.5,
        sparse_mode=0)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    if output.exists() or output.parent != Path("/results"):
        parser.error("use a new direct child of /results")
    torch.manual_seed(20260925)
    torch.npu.set_device(0)
    shapes = ((2200, 1888), (2049, 3073), (64, 96))
    cases = []
    for n0, n1 in shapes:
        q = torch.randn((2, 6, 256), device="npu:0", dtype=torch.bfloat16)
        k = torch.randn((n0 + n1, 1, 256), device="npu:0", dtype=torch.bfloat16)
        v = torch.randn_like(k)
        single = torch.cat((fia(q[:1], k[:n0], v[:n0], [1], [n0]),
                            fia(q[1:], k[n0:], v[n0:], [1], [n1])), dim=0)
        grouped = fia(q, k, v, [1, 2], [n0, n0 + n1])
        repeated = fia(q, k, v, [1, 2], [n0, n0 + n1])
        values = metrics(grouped, single)
        values.update({"kv_lengths": [n0, n1],
                       "grouped_shape": list(grouped.shape),
                       "finite": bool(torch.isfinite(grouped).all().item()),
                       "repeat_bitwise": bool(torch.equal(grouped, repeated))})
        cases.append(values)
    valid = all(case["finite"] and case["repeat_bitwise"]
                and case["relative_rms"] <= 0.005
                and case["cosine"] >= 0.99998 for case in cases)
    report = {"schema": "adakv-grouped-native-fia-abi/v1",
              "torch": torch.__version__, "torch_npu": torch_npu.__version__,
              "device": torch.npu.get_device_name(0), "cases": cases,
              "pass": valid,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    if not valid:
        raise RuntimeError("grouped native FIA ABI gate failed")


if __name__ == "__main__":
    main()
