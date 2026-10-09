"""Reproduce the strict HYPIC RoPE round-trip numerical screen on CPU.

This is a source-path and arithmetic diagnostic, not an NPU or quality verdict.
The candidate widens computation only; canonical storage remains BF16.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--model-config", type=Path, required=True)
    args = parser.parse_args()

    assert hashlib.sha256(args.model_config.read_bytes()).hexdigest() == (
        "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
    )
    source_commit = subprocess.check_output(
        ["git", "-C", str(args.plugin_root), "rev-parse", "HEAD"], text=True
    ).strip()
    assert source_commit == "c12060cd47e7575ead059983d7a8bb4704165c98"
    source_status = subprocess.check_output(
        ["git", "-C", str(args.plugin_root), "status", "--porcelain"],
        text=True,
    )
    assert not source_status
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
    relocation_rows = []
    for source_anchor, target_anchor in ((1, 4096), (128, 4096), (4096, 16384)):
        source_key = attention._anchor_rope(key, source_anchor, inverse=False)
        direct_target = attention._anchor_rope(key, target_anchor, inverse=False)
        canonical = attention._anchor_rope(
            source_key, source_anchor, inverse=True
        )
        relocated = attention._anchor_rope(
            canonical, target_anchor, inverse=False
        )

        source_cos_half, source_sin_half = cache[source_anchor].view(2, -1).unbind(0)
        target_cos_half, target_sin_half = cache[target_anchor].view(2, -1).unbind(0)
        source_cos = torch.cat((source_cos_half, source_cos_half)).view(1, 1, -1)
        source_sin = torch.cat((source_sin_half, source_sin_half)).view(1, 1, -1)
        target_cos = torch.cat((target_cos_half, target_cos_half)).view(1, 1, -1)
        target_sin = torch.cat((target_sin_half, target_sin_half)).view(1, 1, -1)
        widened_canonical = attention._apply_neox_rotary(
            source_key.float(), source_cos, -source_sin
        ).to(key.dtype)
        widened_relocated = attention._apply_neox_rotary(
            widened_canonical.float(), target_cos, target_sin
        ).to(key.dtype)

        assert torch.equal(relocated[..., rotary_dim:], direct_target[..., rotary_dim:])
        assert torch.equal(
            widened_relocated[..., rotary_dim:], direct_target[..., rotary_dim:]
        )
        current_error = (
            relocated[..., :rotary_dim].float()
            - direct_target[..., :rotary_dim].float()
        ).abs()
        widened_error = (
            widened_relocated[..., :rotary_dim].float()
            - direct_target[..., :rotary_dim].float()
        ).abs()
        current_mae = float(current_error.mean())
        widened_mae = float(widened_error.mean())
        assert current_mae < widened_mae
        relocation_rows.append(
            {
                "source_anchor": source_anchor,
                "target_anchor": target_anchor,
                "current_mae_to_direct_target": current_mae,
                "widened_mae_to_direct_target": widened_mae,
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
                "relocation_rows": relocation_rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
