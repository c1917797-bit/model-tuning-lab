#!/usr/bin/env python3
"""Build a Qwen3.5 GDN key-dimension speed-oracle checkpoint.

This is intentionally NOT a quality-preserving pruning method.  It keeps the
first `new_head_k_dim` channels of every Q/K head, applying the SAME per-head
indices to Q and K, and exists only to measure the hardware upside of a truly
narrower recurrent state before investing in DRRQR calibration.

The source checkpoint is never modified. The destination is expected to be a
hardlink copy of the source; modified shards/config/index are always written to
temporary files and atomically replaced so source hardlinks remain intact.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file


def atomic_json(path: Path, obj: object) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def make_keep(num_heads: int, old_dim: int, new_dim: int) -> torch.Tensor:
    if not (0 < new_dim <= old_dim):
        raise ValueError((old_dim, new_dim))
    return torch.tensor(
        [h * old_dim + d for h in range(num_heads) for d in range(new_dim)],
        dtype=torch.long,
    )


def prune_packed_qkv(t: torch.Tensor, qk_width: int, keep: torch.Tensor) -> torch.Tensor:
    if t.shape[0] <= 2 * qk_width:
        raise ValueError(f"packed qkv axis too small: {tuple(t.shape)} qk_width={qk_width}")
    q = t[:qk_width].index_select(0, keep)
    k = t[qk_width : 2 * qk_width].index_select(0, keep)
    v = t[2 * qk_width :]
    return torch.cat((q, k, v), dim=0).contiguous()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--new-head-k-dim", type=int, default=64)
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    cfg = json.loads((src / "config.json").read_text())
    text = cfg["text_config"]
    old_dim = int(text["linear_key_head_dim"])
    num_heads = int(text["linear_num_key_heads"])
    new_dim = int(args.new_head_k_dim)
    qk_width = num_heads * old_dim
    keep = make_keep(num_heads, old_dim, new_dim)

    if old_dim == new_dim:
        raise ValueError("new dimension must differ from source dimension")
    if qk_width != 2048:
        raise ValueError(f"unexpected source Q/K width: {qk_width}; refuse implicit layout assumption")

    idx_path = src / "model.safetensors.index.json"
    index = json.loads(idx_path.read_text())
    wm = index["weight_map"]
    shards = sorted(set(wm.values()))
    manifest = {
        "kind": "speed-oracle-fixed-first-channels-not-quality-evidence",
        "source": str(src),
        "destination": str(dst),
        "num_key_heads": num_heads,
        "old_head_k_dim": old_dim,
        "new_head_k_dim": new_dim,
        "old_qk_width": qk_width,
        "new_qk_width": num_heads * new_dim,
        "changed_shards": [],
        "changed_tensors": [],
    }

    for shard in shards:
        names = [k for k, v in wm.items() if v == shard]
        targets = [
            n for n in names
            if n.endswith(".linear_attn.in_proj_qkv.weight")
            or n.endswith(".linear_attn.conv1d.weight")
        ]
        if not targets:
            continue

        src_shard = src / shard
        dst_shard = dst / shard
        tensors: dict[str, torch.Tensor] = {}
        with safe_open(src_shard, framework="pt", device="cpu") as f:
            metadata = f.metadata()
            for name in f.keys():
                t = f.get_tensor(name)
                if name in targets:
                    before = list(t.shape)
                    t = prune_packed_qkv(t, qk_width, keep)
                    after = list(t.shape)
                    manifest["changed_tensors"].append(
                        {"name": name, "shard": shard, "before": before, "after": after}
                    )
                tensors[name] = t

        tmp = dst_shard.with_name(dst_shard.name + ".tmp")
        save_file(tensors, tmp, metadata=metadata)
        os.replace(tmp, dst_shard)
        manifest["changed_shards"].append(shard)
        print(f"rewrote {shard}: targets={len(targets)}", flush=True)
        del tensors

    # Break config/index hardlinks atomically. Keep all model semantics unchanged
    # except the actual GDN key head dimension and index total-size bookkeeping.
    dst_cfg = json.loads((src / "config.json").read_text())
    dst_cfg["text_config"]["linear_key_head_dim"] = new_dim
    atomic_json(dst / "config.json", dst_cfg)

    index_out = json.loads(idx_path.read_text())
    if "metadata" in index_out and "total_size" in index_out["metadata"]:
        index_out["metadata"]["total_size"] = sum((dst / s).stat().st_size for s in shards)
    atomic_json(dst / "model.safetensors.index.json", index_out)
    atomic_json(dst / "speed_oracle_manifest.json", manifest)

    print(json.dumps({
        "changed_shards": len(manifest["changed_shards"]),
        "changed_tensors": len(manifest["changed_tensors"]),
        "new_head_k_dim": new_dim,
        "packed_width_expected": 2 * num_heads * new_dim + int(text["linear_num_value_heads"]) * int(text["linear_value_head_dim"]),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
