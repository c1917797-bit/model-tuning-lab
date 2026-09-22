"""Paper-derived GQA SparQ selection and an explicitly distinct page variant.

This module does not claim an optimized Ascend kernel. The token selector
implements the GQA rule in SparQ Attention, arXiv:2312.04985v6, Section 4:
group query magnitudes for top-r dimensions, sum per-query approximate
attention scores for top-k support. The page selector aggregates that score
mass by native KV page and always retains the current (possibly partial) page.
"""

from __future__ import annotations

import math

import torch


def gqa_sparq_token_scores(
    query: torch.Tensor,
    keys: torch.Tensor,
    *,
    rank: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return top-r dimensions and summed approximate probabilities.

    query: [group_size, head_dim]; keys: [sequence_length, head_dim].
    Both are for a single local KV head. Scores are not full-attention scores.
    """
    if query.ndim != 2 or keys.ndim != 2 or query.shape[1] != keys.shape[1]:
        raise ValueError("expected query [G,D] and keys [S,D] with equal D")
    if keys.shape[0] < 1 or not 1 <= rank <= query.shape[1]:
        raise ValueError("invalid sequence length or top-r rank")
    q = query.float()
    k = keys.float()
    dimensions = torch.topk(q.abs().sum(dim=0), rank, sorted=False).indices
    q_short = q.index_select(-1, dimensions)
    k_short = k.index_select(-1, dimensions)
    coverage = q_short.abs().sum(-1) / q.abs().sum(-1).clamp_min(1e-12)
    temperature = torch.sqrt(query.shape[-1] * coverage.clamp_min(1e-12))
    per_head = torch.softmax((q_short @ k_short.T) / temperature[:, None], dim=-1)
    return dimensions, per_head.sum(dim=0)


def select_sparq_pages(
    query: torch.Tensor,
    keys: torch.Tensor,
    block_table: torch.Tensor,
    *,
    block_size: int,
    rank: int,
    token_budget: int,
    page_budget: int,
    recent_tokens: int = 0,
) -> dict[str, torch.Tensor | int]:
    """Select page IDs for one request and expose paper-token support recall.

    The keys must already be in logical sequence order and exclude invalid tail
    entries. The caller maps physical KV cache pages into this order. The page
    output changes the paper's token-level support and must not be labelled
    faithful SparQ token selection in a serving result.
    """
    seq_len = keys.shape[0]
    if block_size < 1 or not 1 <= token_budget <= seq_len:
        raise ValueError("invalid block size or token budget")
    num_pages = math.ceil(seq_len / block_size)
    if block_table.ndim != 1 or block_table.numel() < num_pages:
        raise ValueError("block table does not cover the sequence")
    if not 1 <= page_budget <= num_pages or not 0 <= recent_tokens <= seq_len:
        raise ValueError("invalid page budget or recent span")

    dimensions, scores = gqa_sparq_token_scores(query, keys, rank=rank)
    token_priority = scores.clone()
    if recent_tokens:
        token_priority[-recent_tokens:] += query.shape[0]
    paper_tokens = torch.topk(token_priority, token_budget, sorted=False).indices

    padded_scores = torch.nn.functional.pad(
        scores, (0, num_pages * block_size - seq_len)
    )
    page_mass = padded_scores.reshape(num_pages, block_size).sum(dim=-1)
    if page_budget == 1:
        chosen = torch.tensor([num_pages - 1], dtype=torch.long, device=scores.device)
    else:
        other = torch.topk(
            page_mass[:-1], page_budget - 1, sorted=False
        ).indices
        latest = torch.tensor([num_pages - 1], dtype=torch.long, device=scores.device)
        chosen = torch.cat((other, latest)).sort().values

    physical_pages = block_table.index_select(0, chosen)
    membership = (paper_tokens[:, None] // block_size == chosen[None, :]).any(dim=-1)
    retained_paper_tokens = membership.sum()
    tail_length = seq_len - (num_pages - 1) * block_size
    selected_length = (page_budget - 1) * block_size + tail_length
    return {
        "top_r_dimensions": dimensions,
        "paper_top_k_tokens": paper_tokens,
        "selected_logical_pages": chosen,
        "selected_physical_pages": physical_pages,
        "selected_length": selected_length,
        "retained_paper_top_k_tokens": retained_paper_tokens,
    }
