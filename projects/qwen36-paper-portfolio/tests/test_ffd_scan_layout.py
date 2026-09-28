"""Protect the FFD block/token axis contract before any NPU service launch."""

from __future__ import annotations

import torch

from qwen36_ffd_probe.patch import _scan_scores, _selection_masks


def test_scan_scores_keep_block_axis_before_token_axis() -> None:
    query = torch.arange(6 * 4, dtype=torch.float32).reshape(6, 4) / 10
    blocks = torch.arange(3 * 5 * 4, dtype=torch.float32).reshape(3, 5, 4) / 20
    scores = _scan_scores(query, blocks, 0.5)
    assert tuple(scores.shape) == (6, 3, 5)
    assert torch.allclose(scores[2, 1, 4], (query[2] * blocks[1, 4]).sum() * 0.5)
    assert tuple(scores.amax(dim=-1).shape) == (6, 3)


def test_author_kv_group_or_expands_to_all_query_heads() -> None:
    keep = torch.tensor([[True, False, False], [False, True, False]])
    per_head, union, union_tokens = _selection_masks(keep, 4, 2)
    assert per_head.shape == (2, 14)
    assert union.tolist() == [True, True, False]
    assert union_tokens.tolist() == [True] * 8 + [False] * 4 + [True] * 2
    assert per_head[0, 4:8].tolist() == [False] * 4
    assert per_head[1, 0:4].tolist() == [False] * 4
    assert per_head[:, -2:].all().item()


def test_subblock_union_keeps_axis_order_and_unquantized_tail() -> None:
    # One 128-token Q2 block selected in eight 16-token subblocks.
    # The tail can exceed SBS because it belongs to the next, unsealed block.
    keep = torch.zeros((2, 8), dtype=torch.bool)
    keep[0, 1] = True
    keep[1, 6] = True
    per_head, union, union_tokens = _selection_masks(keep, 16, 111)
    assert union.tolist() == [False, True, False, False, False, False, True, False]
    assert per_head.shape == (2, 239)
    assert union_tokens.shape == (239,)
    assert union_tokens[:128].sum().item() == 32
    assert union_tokens[128:].all().item()
    assert not per_head[0, 6 * 16 : 7 * 16].any().item()
    assert not per_head[1, 1 * 16 : 2 * 16].any().item()


def test_subblock_score_view_preserves_block_then_token_order() -> None:
    query = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    blocks = torch.arange(2 * 8 * 2, dtype=torch.float32).reshape(2, 8, 2)
    scan = _scan_scores(query, blocks, 1.0)
    subblocks = scan.reshape(2, 4, 4)
    assert subblocks[0, 0].tolist() == scan[0, 0, :4].tolist()
    assert subblocks[0, 1].tolist() == scan[0, 0, 4:].tolist()
    assert subblocks[0, 2].tolist() == scan[0, 1, :4].tolist()
