"""One-shot AscendC GDN affine-composition diagnostic; no model serving."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import torch
    import torch_npu
    import vllm_ascend.ops  # noqa: F401 - registers the pinned Ascend operators
    from vllm_ascend.ops.triton.fla.utils import prepare_chunk_indices
    from hypic_vllm_ascend.patches.gdn import _ascendc_gdn_h

    torch.manual_seed(19)
    torch.npu.set_device(0)
    device = torch.device("npu:0")
    # The host guard must see the owned PID before the short kernel sequence.
    time.sleep(5)

    key_heads, value_heads, tokens, dim = 4, 12, 64, 128
    def sampled(shape: tuple[int, ...], *, scale: float, dtype: torch.dtype):
        return (torch.randn(shape, dtype=torch.float32) * scale).to(
            dtype=dtype, device=device
        ).contiguous()

    key = sampled((1, key_heads, tokens, dim), scale=0.02, dtype=torch.bfloat16)
    w = sampled((1, value_heads, tokens, dim), scale=0.02, dtype=torch.bfloat16)
    u = sampled((1, value_heads, tokens, dim), scale=0.02, dtype=torch.bfloat16)
    gate_cpu = (
        -0.01 * torch.arange(1, tokens + 1, dtype=torch.float32)
    ).view(1, 1, tokens).expand(1, value_heads, tokens).contiguous()
    gate = gate_cpu.to(device=device)
    initial = sampled(
        (1, value_heads, dim, dim), scale=0.01, dtype=torch.float32
    )
    zero = torch.zeros_like(initial)
    identity = torch.eye(dim, dtype=torch.float32, device=device).view(
        1, 1, dim, dim
    ).expand(1, value_heads, dim, dim).contiguous()
    chunk_indices = prepare_chunk_indices(
        torch.tensor([0, tokens], dtype=torch.int64), 64
    )
    metadata = SimpleNamespace(
        cu_seqlens_host=(0, tokens),
        chunk_indices_chunk64_host=tuple(
            int(v) for v in chunk_indices.reshape(-1).tolist()
        ),
    )
    assert len(metadata.chunk_indices_chunk64_host) == 2

    direct = _ascendc_gdn_h(
        key, w, u, gate, initial.clone(), metadata
    )[2]
    zero_final = _ascendc_gdn_h(
        key, w, u, gate, zero, metadata
    )[2]
    transition = _ascendc_gdn_h(
        key, w, torch.zeros_like(u), gate, identity, metadata
    )[2]
    torch.npu.synchronize()
    assert direct is not None and zero_final is not None and transition is not None
    left = torch.matmul(transition.float(), initial.float()) + zero_final.float()
    right = torch.matmul(initial.float(), transition.float()) + zero_final.float()
    torch.npu.synchronize()

    direct_cpu = direct.float().cpu()
    left_cpu = left.float().cpu()
    right_cpu = right.float().cpu()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "initial": initial.float().cpu(),
            "direct": direct_cpu,
            "zero_final": zero_final.float().cpu(),
            "transition": transition.float().cpu(),
            "left_composed": left_cpu,
            "right_composed": right_cpu,
        },
        args.output / "tensors.pt",
    )

    def residual(candidate: torch.Tensor) -> dict[str, float]:
        error = (direct_cpu - candidate).abs()
        return {
            "mae": float(error.mean()),
            "max_abs": float(error.max()),
            "relative_l2": float(
                torch.linalg.vector_norm(direct_cpu - candidate)
                / torch.linalg.vector_norm(direct_cpu).clamp_min(1e-30)
            ),
        }

    result = {
        "schema": "hypic-gdn-affine-npu-probe/v1",
        "source": "pinned vLLM-Ascend AscendC GDN state kernel",
        "device": str(device),
        "device_name": torch.npu.get_device_name(0),
        "torch_version": torch.__version__,
        "torch_npu_version": torch_npu.__version__,
        "shape": {
            "key_heads": key_heads,
            "value_heads": value_heads,
            "tokens": tokens,
            "key_dim": dim,
            "value_dim": dim,
        },
        "seed": 19,
        "chunk_indices": metadata.chunk_indices_chunk64_host,
        "left_transition_times_initial_plus_zero": residual(left_cpu),
        "right_initial_times_transition_plus_zero": residual(right_cpu),
    }
    (args.output / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True), flush=True)
    # Keep the owned device PID observable for the host-side physical guard.
    time.sleep(5)


if __name__ == "__main__":
    main()
