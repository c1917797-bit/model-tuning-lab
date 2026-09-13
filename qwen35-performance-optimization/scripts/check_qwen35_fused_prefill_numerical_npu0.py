#!/usr/bin/env python3
"""Compare the v0.23 Triton GDN prefill path with the fused torch_npu op."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace

import torch
import torch_npu
import vllm_ascend.ops.triton.fla.chunk as chunk_module
from vllm_ascend.ops.gdn_attn_builder import (
    _build_non_spec_chunked_prefill_metadata,
)
from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
from vllm_ascend.utils import enable_custom_op


def _metrics(reference: torch.Tensor, candidate: torch.Tensor) -> dict[str, float]:
    reference = reference.float().cpu()
    candidate = candidate.float().cpu()
    diff = candidate - reference
    ref_norm = torch.linalg.vector_norm(reference)
    diff_norm = torch.linalg.vector_norm(diff)
    cosine = torch.nn.functional.cosine_similarity(
        reference.flatten(), candidate.flatten(), dim=0
    )
    return {
        "max_abs": float(diff.abs().max()),
        "mean_abs": float(diff.abs().mean()),
        "rmse": float(torch.sqrt(torch.mean(diff.square()))),
        "relative_l2": float(diff_norm / torch.clamp(ref_norm, min=1e-12)),
        "cosine": float(cosine),
    }


def _make_inputs(lengths: list[int], seed: int):
    total = sum(lengths)
    nk, nv, width = 4, 12, 128
    torch.manual_seed(seed)
    q = torch.randn(
        (1, total, nk, width), dtype=torch.bfloat16, device="npu"
    )
    k = torch.randn(
        (1, total, nk, width), dtype=torch.bfloat16, device="npu"
    )
    v = torch.randn(
        (1, total, nv, width), dtype=torch.bfloat16, device="npu"
    )
    g = -torch.rand((1, total, nv), dtype=torch.float32, device="npu")
    beta = torch.rand(
        (1, total, nv), dtype=torch.bfloat16, device="npu"
    )
    state = (
        0.05
        * torch.randn(
            (len(lengths), nv, width, width),
            dtype=torch.bfloat16,
            device="npu",
        )
    ).to(torch.bfloat16)
    cu_seqlens_cpu = torch.tensor(
        [0, *torch.tensor(lengths).cumsum(0).tolist()],
        dtype=torch.int64,
    )
    cu_seqlens = cu_seqlens_cpu.to(device="npu")
    return q, k, v, g, beta, state, cu_seqlens, cu_seqlens_cpu


def _run_case(lengths: list[int], seed: int) -> dict:
    q, k, v, g, beta, state, cu_seqlens, cu_seqlens_cpu = _make_inputs(
        lengths, seed
    )
    scale = q.shape[-1] ** -0.5
    fake_builder = SimpleNamespace(
        vllm_config=SimpleNamespace(
            model_config=SimpleNamespace(
                hf_text_config=SimpleNamespace(linear_num_value_heads=48)
            ),
            parallel_config=SimpleNamespace(tensor_parallel_size=4),
        )
    )
    prebuilt_meta = _build_non_spec_chunked_prefill_metadata(
        fake_builder,
        cu_seqlens_cpu,
        torch.device("npu"),
    )

    old_forward_context = chunk_module.get_forward_context
    old_get_pcp_group = chunk_module.get_pcp_group
    chunk_module.get_forward_context = lambda: SimpleNamespace(
        attn_metadata=None
    )
    chunk_module.get_pcp_group = lambda: SimpleNamespace(world_size=1)
    try:
        reference_out, reference_state = chunk_module.chunk_gated_delta_rule(
            q=q,
            k=k,
            v=v,
            g=g,
            beta=beta,
            scale=scale,
            initial_state=state.transpose(-1, -2).contiguous(),
            output_final_state=True,
            cu_seqlens=cu_seqlens,
            prebuilt_meta=prebuilt_meta,
            head_first=False,
            use_qk_l2norm_in_kernel=True,
        )
        torch.npu.synchronize()
        print(
            json.dumps(
                {"phase": "reference-complete", "lengths": lengths},
                sort_keys=True,
            ),
            flush=True,
        )
    finally:
        chunk_module.get_forward_context = old_forward_context
        chunk_module.get_pcp_group = old_get_pcp_group

    fused_out, fused_state = torch_npu.npu_chunk_gated_delta_rule(
        chunk_module.l2norm_fwd(q).squeeze(0).contiguous(),
        chunk_module.l2norm_fwd(k).squeeze(0).contiguous(),
        v.squeeze(0).contiguous(),
        beta=beta.squeeze(0).contiguous(),
        initial_state=state.contiguous(),
        actual_seq_lengths=torch.diff(cu_seqlens).to(torch.int32),
        scale=scale,
        g=g.squeeze(0).contiguous(),
    )
    torch.npu.synchronize()
    print(
        json.dumps(
            {"phase": "fused-complete", "lengths": lengths},
            sort_keys=True,
        ),
        flush=True,
    )

    output_metrics = _metrics(reference_out.squeeze(0), fused_out)
    state_metrics = _metrics(
        reference_state.transpose(-1, -2).contiguous(), fused_state
    )
    passed = (
        output_metrics["cosine"] >= 0.999
        and output_metrics["relative_l2"] <= 0.05
        and output_metrics["rmse"] <= 0.03
        and state_metrics["cosine"] >= 0.999
        and state_metrics["relative_l2"] <= 0.05
        and state_metrics["rmse"] <= 0.03
    )
    return {
        "lengths": lengths,
        "seed": seed,
        "total_tokens": sum(lengths),
        "shape": {"nk": 4, "nv": 12, "dk": 128, "dv": 128},
        "output": output_metrics,
        "final_state": state_metrics,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        default="64;257;1807",
        help="semicolon-separated cases; comma separates packed sequence lengths",
    )
    parser.add_argument("--seed", type=int, default=20260913)
    args = parser.parse_args()
    cases = [
        [int(value) for value in case.split(",")]
        for case in args.cases.split(";")
    ]
    if any(not lengths or any(length <= 0 for length in lengths) for lengths in cases):
        raise ValueError("all sequence lengths must be positive")

    torch.npu.set_device(0)
    init_device_properties_triton()
    if not enable_custom_op():
        raise RuntimeError("vLLM-Ascend custom operators are unavailable")
    results = [_run_case(lengths, args.seed) for lengths in cases]
    payload = {
        "schema": "qwen35-fused-prefill-numerical/v1",
        "device": "physical-npu0",
        "reference": "vllm-ascend-v0.23-triton-chunk-gated-delta-rule",
        "candidate": "torch_npu.npu_chunk_gated_delta_rule",
        "dtype": "bfloat16",
        "results": results,
        "passed": all(result["passed"] for result in results),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
