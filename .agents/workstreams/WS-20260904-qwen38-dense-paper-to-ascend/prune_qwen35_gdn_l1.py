#!/usr/bin/env python3
"""Data-free L1 Q/K dimension pruning for Qwen3.5 packed GDN weights.

Adapts the official LinearAttentionPruning L1 criterion to Qwen3.5's packed
in_proj_qkv + packed depthwise conv layout. For each GDN layer, score each Q/K
output channel as sum(abs(Q row)) + sum(abs(K row)), choose top-k channels per
key head, sort selected indices within each head, then slice the same channels
from Q, K and their corresponding packed conv channels. V and all other tensors
are unchanged.

This is a post-training, no-finetuning treatment. Source checkpoint is never
modified; destination should begin as a hardlink copy and changed shards are
atomically replaced.
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


def l1_keep_from_packed_qkv(
    w: torch.Tensor, num_heads: int, old_dim: int, new_dim: int
) -> torch.Tensor:
    qk_width = num_heads * old_dim
    if tuple(w.shape[:1]) != (2 * qk_width + 6144,):
        # Keep the check explicit for this checkpoint; do not silently assume layout.
        if w.shape[0] <= 2 * qk_width:
            raise ValueError(f"unexpected packed qkv shape {tuple(w.shape)}")
    q = w[:qk_width].float()
    k = w[qk_width : 2 * qk_width].float()
    scores = q.abs().sum(dim=1) + k.abs().sum(dim=1)
    scores = scores.view(num_heads, old_dim)
    keeps = []
    for h in range(num_heads):
        idx = torch.topk(scores[h], new_dim, largest=True).indices
        idx = torch.sort(idx).values + h * old_dim
        keeps.append(idx)
    return torch.cat(keeps).long()


def prune_packed(t: torch.Tensor, qk_width: int, keep: torch.Tensor) -> torch.Tensor:
    q = t[:qk_width].index_select(0, keep)
    k = t[qk_width : 2 * qk_width].index_select(0, keep)
    rest = t[2 * qk_width :]
    return torch.cat((q, k, rest), dim=0).contiguous()


def layer_id(name: str) -> int:
    return int(name.split(".layers.", 1)[1].split(".", 1)[0])


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
    if not (0 < new_dim < old_dim):
        raise ValueError((old_dim, new_dim))
    if qk_width != 2048:
        raise ValueError(f"unexpected source Q/K width {qk_width}")

    index = json.loads((src / "model.safetensors.index.json").read_text())
    wm = index["weight_map"]
    shards = sorted(set(wm.values()))
    manifest = {
        "kind": "official-paper-l1-data-free-adapted-to-qwen35-packed-gdn",
        "source": str(src),
        "destination": str(dst),
        "num_key_heads": num_heads,
        "old_head_k_dim": old_dim,
        "new_head_k_dim": new_dim,
        "changed_shards": [],
        "changed_tensors": [],
        "keep_indices_by_layer": {},
    }

    # QKV and conv tensors for one layer are not guaranteed to live in the
    # same safetensors shard in Qwen3.5. Build the complete layer->keep map
    # first, then perform shard rewriting in a second pass.
    global_keeps: dict[int, torch.Tensor] = {}
    for shard in shards:
        qkv_names = [
            k for k, v in wm.items()
            if v == shard and k.endswith(".linear_attn.in_proj_qkv.weight")
        ]
        if not qkv_names:
            continue
        with safe_open(src / shard, framework="pt", device="cpu") as f:
            for name in qkv_names:
                lid = layer_id(name)
                keep = l1_keep_from_packed_qkv(
                    f.get_tensor(name), num_heads, old_dim, new_dim
                )
                global_keeps[lid] = keep
                manifest["keep_indices_by_layer"][str(lid)] = keep.tolist()

    if len(global_keeps) != 48:
        raise RuntimeError(
            f"expected 48 GDN keep maps, found {len(global_keeps)}"
        )

    for shard in shards:
        names = [k for k, v in wm.items() if v == shard]
        qkv_names = [n for n in names if n.endswith(".linear_attn.in_proj_qkv.weight")]
        conv_names = [n for n in names if n.endswith(".linear_attn.conv1d.weight")]
        if not qkv_names and not conv_names:
            continue

        src_shard, dst_shard = src / shard, dst / shard
        tensors: dict[str, torch.Tensor] = {}
        with safe_open(src_shard, framework="pt", device="cpu") as f:
            metadata = f.metadata()
            # Copy all tensors, slicing only packed QKV/conv tensors.
            for name in f.keys():
                t = f.get_tensor(name)
                if name.endswith(".linear_attn.in_proj_qkv.weight") or name.endswith(".linear_attn.conv1d.weight"):
                    lid = layer_id(name)
                    keep = global_keeps.get(lid)
                    if keep is None:
                        raise RuntimeError(f"missing keep indices for layer {lid} in shard {shard}")
                    before = list(t.shape)
                    t = prune_packed(t, qk_width, keep)
                    manifest["changed_tensors"].append({
                        "name": name, "shard": shard, "before": before, "after": list(t.shape)
                    })
                tensors[name] = t

        tmp = dst_shard.with_name(dst_shard.name + ".tmp")
        save_file(tensors, tmp, metadata=metadata)
        os.replace(tmp, dst_shard)
        manifest["changed_shards"].append(shard)
        print(f"rewrote {shard}: qkv={len(qkv_names)} conv={len(conv_names)}", flush=True)
        del tensors

    dst_cfg = json.loads((src / "config.json").read_text())
    dst_cfg["text_config"]["linear_key_head_dim"] = new_dim
    atomic_json(dst / "config.json", dst_cfg)
    index_out = json.loads((src / "model.safetensors.index.json").read_text())
    if "metadata" in index_out and "total_size" in index_out["metadata"]:
        index_out["metadata"]["total_size"] = sum((dst / s).stat().st_size for s in shards)
    atomic_json(dst / "model.safetensors.index.json", index_out)
    atomic_json(dst / "l1_pruning_manifest.json", manifest)
    print(json.dumps({
        "changed_shards": len(manifest["changed_shards"]),
        "changed_tensors": len(manifest["changed_tensors"]),
        "layers": len(manifest["keep_indices_by_layer"]),
        "new_head_k_dim": new_dim,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
