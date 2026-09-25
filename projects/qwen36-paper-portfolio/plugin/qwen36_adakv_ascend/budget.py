"""Cross-TP-rank GQA budget seam for an Ada-KV-derived cache policy.

This module does not evict KV or patch vLLM. In TP4 Qwen3.6, each worker has
one KV head, so a global four-head budget requires exchanging the per-head
observation scores. The caller must provide scores *after* GQA-group averaging
and paper-compatible pooling. Use only at a prefill/eviction boundary, not on
every decode token.
"""

from __future__ import annotations

import torch
import torch.distributed as dist


def allocate_global_head_budget(
    local_scores: torch.Tensor,
    base_capacity: int,
    floor_ratio: float,
    *,
    group=None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return local budget, all-head budgets, and unsafeguarded selected counts.

    `local_scores` is [batch, eligible_old_tokens] for one KV head per rank.
    The score all-gather and global Top-K reproduce the essential official
    `AdaptiveSnapKVCluster.update_kv_gqa` allocation for this TP topology.
    The author's `torch.round(count * (1-floor_ratio) + floor_capacity)` can
    change the exact total budget by rounding; this function reports both
    counts and budgets instead of silently correcting the author formula.
    """
    if local_scores.ndim != 2 or not local_scores.is_floating_point():
        raise ValueError("local_scores must be a floating [batch, tokens] tensor")
    if not 0 <= floor_ratio <= 1:
        raise ValueError("floor_ratio must lie in [0, 1]")
    batch, tokens = local_scores.shape
    if batch < 1 or not 0 < base_capacity <= tokens:
        raise ValueError("base_capacity must lie in [1, eligible_old_tokens]")
    if not dist.is_available() or not dist.is_initialized():
        raise RuntimeError("a live distributed TP process group is required")

    world = dist.get_world_size(group)
    rank = dist.get_rank(group)
    gathered = torch.empty((world * batch, tokens), dtype=local_scores.dtype, device=local_scores.device)
    dist.all_gather_into_tensor(gathered, local_scores.contiguous(), group=group)
    by_request = gathered.view(world, batch, tokens).permute(1, 0, 2).contiguous()
    selected = torch.topk(by_request.reshape(batch, world * tokens), k=world * base_capacity, dim=-1).indices
    selected_head = torch.div(selected, tokens, rounding_mode="floor")
    counts = torch.zeros((batch, world), dtype=torch.int64, device=local_scores.device)
    counts.scatter_add_(1, selected_head, torch.ones_like(selected_head, dtype=torch.int64))

    floor_capacity = int(base_capacity * floor_ratio)
    budgets = torch.round(counts.float() * (1.0 - floor_ratio) + floor_capacity).to(torch.int32)
    return budgets[:, rank], budgets, counts
