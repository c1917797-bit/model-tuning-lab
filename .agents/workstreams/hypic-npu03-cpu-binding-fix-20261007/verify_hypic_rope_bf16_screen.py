"""Reproduce the strict HYPIC RoPE round-trip numerical screen on CPU.

This is a source-path and arithmetic diagnostic, not an NPU or quality verdict.
The candidate widens computation only; canonical storage remains BF16.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--model-config", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.plugin_root))
    import torch
    from hypic_vllm_ascend.patches import attention

    config = json.loads(args.model_config.read_text(encoding="utf-8"))
    text_config = config["text_config"]
    head_dim = int(text_config["head_dim"])
    rotary_dim = int(head_dim * float(text_config["partial_rotary_factor"]))
    half = rotary_dim // 2
    theta_base = float(text_config["rope_parameters"]["rope_theta"])
    assert head_dim == 256 and rotary_dim == 64
    assert text_config["dtype"] == "bfloat16"

    torch.manual_seed(17)
    key = torch.randn(
        1024,
        min(4, int(text_config["num_key_value_heads"])),
        head_dim,
        dtype=torch.bfloat16,
    )
    inv_freq = 1.0 / (
        theta_base ** (torch.arange(half, dtype=torch.float32) / half)
    )
    cache = torch.zeros(16385, rotary_dim, dtype=torch.float32)
    anchors = (1, 128, 4096, 16384)
    for anchor in anchors:
        angle = anchor * inv_freq
        cache[anchor] = torch.cat((angle.cos(), angle.sin()))
    attention._ROPE_GEOMETRY = attention._RopeGeometry(
        cache, rotary_dim, head_dim, True, "synthetic-config-matched"
    )

    rows = []
    for anchor in anchors:
        canonical = attention._anchor_rope(key, anchor, inverse=True)
        restored = attention._anchor_rope(canonical, anchor, inverse=False)

        cos_half, sin_half = cache[anchor].view(2, -1).unbind(0)
        cos = torch.cat((cos_half, cos_half)).view(1, 1, -1)
        sin = torch.cat((sin_half, sin_half)).view(1, 1, -1)
        widened_canonical = attention._apply_neox_rotary(
            key.float(), cos, -sin
        ).to(key.dtype)
        widened_restored = attention._apply_neox_rotary(
            widened_canonical.float(), cos, sin
        ).to(key.dtype)

        assert torch.equal(restored[..., rotary_dim:], key[..., rotary_dim:])
        assert torch.equal(
            widened_restored[..., rotary_dim:], key[..., rotary_dim:]
        )
        current_error = (
            restored[..., :rotary_dim].float()
            - key[..., :rotary_dim].float()
        ).abs()
        widened_error = (
            widened_restored[..., :rotary_dim].float()
            - key[..., :rotary_dim].float()
        ).abs()
        current_mae = float(current_error.mean())
        widened_mae = float(widened_error.mean())
        assert current_mae > widened_mae > 0
        rows.append(
            {
                "anchor": anchor,
                "current_mae": current_mae,
                "widened_compute_bf16_storage_mae": widened_mae,
                "current_changed_fraction": float(
                    (current_error > 0).float().mean()
                ),
                "widened_changed_fraction": float(
                    (widened_error > 0).float().mean()
                ),
            }
        )
    print(
        json.dumps(
            {
                "scope": "CPU synthetic RoPE cache, actual plugin function",
                "model_head_dim": head_dim,
                "rotary_dim": rotary_dim,
                "rope_theta": theta_base,
                "key_dtype": str(key.dtype),
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
