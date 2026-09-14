from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from sliminfer_ascend.planner import selection_digest, select_active_blocks
from sliminfer_ascend.shadow_score import (
    remap_compact_block_scores,
    semantic_block_scores,
)


def _tensor(values):
    return torch.tensor(values, dtype=torch.float32)


def test_hand_computed_single_rank_score():
    q = _tensor([[[1.0]], [[2.0]], [[3.0]], [[4.0]]])
    k = _tensor([[[1.0]], [[2.0]], [[3.0]], [[4.0]]])
    (result,) = semantic_block_scores(
        q, k, (0, 4), block_size=4, unit_size=2, query_window=2
    )
    assert result.unit_scores == pytest.approx((5.25, 12.25))
    assert result.block_scores == pytest.approx({0: 12.25})


def test_gqa_key_heads_are_repeated_over_matching_query_heads():
    q = _tensor([[[1.0], [2.0]]])
    k = _tensor([[[3.0]]])
    (result,) = semantic_block_scores(q, k, (0, 1), block_size=1, unit_size=1)
    assert result.unit_scores == pytest.approx((4.5,))


def test_tp_sum_happens_before_unit_max():
    q = _tensor([[[1.0]], [[1.0]]])
    k = _tensor([[[10.0]], [[0.0]]])

    def add_rank_one(local):
        return local + _tensor([0.0, 12.0])

    (result,) = semantic_block_scores(
        q,
        k,
        (0, 2),
        block_size=2,
        unit_size=1,
        query_window=1,
        reduce_sum=add_rank_one,
        global_query_heads=2,
    )
    assert result.unit_scores == pytest.approx((5.0, 6.0))
    assert result.block_scores == pytest.approx({0: 6.0})


def test_request_boundaries_prevent_cross_request_query_mixing():
    q = _tensor([[[1.0]], [[2.0]], [[100.0]], [[200.0]]])
    k = _tensor([[[1.0]], [[1.0]], [[1.0]], [[1.0]]])
    first, second = semantic_block_scores(
        q, k, (0, 2, 4), block_size=2, unit_size=1, query_window=2
    )
    assert first.unit_scores == pytest.approx((1.5, 1.5))
    assert second.unit_scores == pytest.approx((150.0, 150.0))
    assert first.token_start == 0 and first.token_end == 2
    assert second.token_start == 2 and second.token_end == 4


def test_partial_unit_and_partial_final_block_are_scored():
    q = torch.ones((5, 1, 1), dtype=torch.float32)
    k = _tensor([[[1.0]], [[3.0]], [[5.0]], [[7.0]], [[11.0]]])
    (result,) = semantic_block_scores(
        q, k, (0, 5), block_size=4, unit_size=3, query_window=1
    )
    assert result.unit_scores == pytest.approx((3.0, 7.0, 11.0))
    assert result.block_scores == pytest.approx({0: 7.0, 1: 11.0})


def test_invalid_shapes_nonfinite_values_and_boundaries_fail_closed():
    q = torch.ones((2, 2, 1), dtype=torch.float32)
    k = torch.ones((2, 1, 1), dtype=torch.float32)
    with pytest.raises(ValueError, match="strictly increasing"):
        semantic_block_scores(q, k, (0, 0, 2))
    with pytest.raises(ValueError, match="token counts"):
        semantic_block_scores(q, k[:1], (0, 2))
    with pytest.raises(ValueError, match="divisible"):
        semantic_block_scores(torch.ones((2, 3, 1)), torch.ones((2, 2, 1)), (0, 2))
    q[0, 0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        semantic_block_scores(q, k, (0, 2))


def test_collective_contract_fails_closed():
    q = torch.ones((2, 1, 1), dtype=torch.float32)
    k = torch.ones((2, 1, 1), dtype=torch.float32)
    with pytest.raises(ValueError, match="required"):
        semantic_block_scores(q, k, (0, 2), reduce_sum=lambda value: value)
    with pytest.raises(ValueError, match="vector shape"):
        semantic_block_scores(
            q,
            k,
            (0, 2),
            unit_size=1,
            reduce_sum=lambda value: value[:1],
            global_query_heads=2,
        )


def test_scores_feed_deterministic_sink_and_topk_selection():
    q = torch.ones((4, 1, 1), dtype=torch.float32)
    k = _tensor([[[0.0]], [[3.0]], [[2.0]], [[0.0]]])
    (result,) = semantic_block_scores(
        q, k, (0, 4), block_size=1, unit_size=1, query_window=1
    )
    selected = select_active_blocks(
        (0, 1, 2, 3), result.block_scores, keep_tokens=3, block_size=1
    )
    assert selected == (0, 1, 3)
    assert selection_digest("request-a", {19: selected}) == selection_digest(
        "request-a", {19: (3, 1, 0)}
    )


def test_compact_scores_remap_to_noncontiguous_absolute_blocks():
    remapped = remap_compact_block_scores(
        {0: 9.0, 1: 7.0, 2: 8.0},
        (0, 2, 5),
        prompt_tokens=6 * 64,
        compact_tokens=3 * 64,
    )
    assert remapped == {0: 9.0, 2: 7.0, 5: 8.0}
    selected = select_active_blocks(
        (0, 2, 5), remapped, keep_tokens=2, block_size=1
    )
    assert selected == (0, 5)


def test_compact_score_remap_accounts_for_partial_original_final_block():
    assert remap_compact_block_scores(
        {0: 1.0, 1: 2.0},
        (0, 5),
        prompt_tokens=321,
        compact_tokens=65,
    ) == {0: 1.0, 5: 2.0}


@pytest.mark.parametrize(
    ("scores", "blocks", "prompt_tokens", "compact_tokens", "message"),
    [
        ({0: 1.0, 2: 2.0}, (0, 2), 192, 128, "contiguous ordinals"),
        ({0: 1.0, 1: 2.0}, (0, 0), 192, 128, "strictly increasing"),
        ({0: 1.0}, (3,), 192, 64, "outside the prompt"),
        ({0: 1.0, 1: 2.0}, (0, 2), 129, 128, "exactly cover"),
    ],
)
def test_compact_score_remap_fails_closed_on_identity_mismatch(
    scores, blocks, prompt_tokens, compact_tokens, message
):
    with pytest.raises(ValueError, match=message):
        remap_compact_block_scores(
            scores,
            blocks,
            prompt_tokens=prompt_tokens,
            compact_tokens=compact_tokens,
        )
