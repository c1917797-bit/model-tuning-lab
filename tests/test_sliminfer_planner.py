import pytest

from sliminfer_ascend.planner import (
    LayerPruningSpec,
    aggregate_rank_scores,
    build_layer_plan,
    prompt_block_ids,
    selection_digest,
    select_active_blocks,
)


def _descending_scores(blocks):
    return {block: float(-block) for block in blocks}


def test_prompt_block_ids_cover_partial_last_block():
    assert prompt_block_ids(1) == (0,)
    assert prompt_block_ids(64) == (0,)
    assert prompt_block_ids(65) == (0, 1)


def test_fixed_12k_budget_on_32k_prompt_keeps_exact_block_count_and_edges():
    blocks = prompt_block_ids(32768)
    selected = select_active_blocks(
        blocks,
        _descending_scores(blocks),
        keep_tokens=12 * 1024,
    )
    assert len(blocks) == 512
    assert len(selected) == 192
    assert selected[0] == 0
    assert selected[-1] == 511


def test_ties_are_deterministic_and_independent_of_mapping_order():
    blocks = (0, 1, 2, 3, 4, 5)
    forward = {block: 1.0 for block in blocks}
    reverse = dict(reversed(tuple(forward.items())))
    expected = (0, 1, 2, 5)
    assert select_active_blocks(blocks, forward, keep_tokens=4, block_size=1) == expected
    assert select_active_blocks(blocks, reverse, keep_tokens=4, block_size=1) == expected


def test_tp_scores_are_mean_reduced_before_selection():
    rank_scores = [
        {0: 0.0, 1: 8.0, 2: 1.0, 3: 0.0},
        {0: 0.0, 1: 0.0, 2: 9.0, 3: 0.0},
        {0: 0.0, 1: 0.0, 2: 9.0, 3: 0.0},
        {0: 0.0, 1: 8.0, 2: 1.0, 3: 0.0},
    ]
    reduced = aggregate_rank_scores(rank_scores)
    assert reduced == {0: 0.0, 1: 4.0, 2: 5.0, 3: 0.0}
    assert select_active_blocks((0, 1, 2, 3), reduced, keep_tokens=3, block_size=1) == (
        0,
        2,
        3,
    )


def test_tp_score_identity_mismatch_fails_closed():
    with pytest.raises(ValueError, match="block IDs differ"):
        aggregate_rank_scores([{0: 1.0, 1: 2.0}, {0: 1.0, 2: 2.0}])


def test_qwen36_staged_plan_is_monotonic():
    blocks = prompt_block_ids(32768)
    specs = (
        LayerPruningSpec(19, 12 * 1024),
        LayerPruningSpec(39, 6 * 1024),
        LayerPruningSpec(59, 4 * 1024),
    )
    scores = {
        19: _descending_scores(blocks),
        39: _descending_scores(blocks),
        59: _descending_scores(blocks),
    }
    plan = build_layer_plan(32768, specs, scores)
    assert [len(plan[layer]) for layer in (19, 39, 59)] == [192, 96, 64]
    assert set(plan[59]) <= set(plan[39]) <= set(plan[19])


def test_digest_is_request_local_and_canonical():
    plan_a = {39: (3, 2), 19: (1, 0)}
    plan_b = {19: (0, 1), 39: (2, 3)}
    assert selection_digest("request-a", plan_a) == selection_digest("request-a", plan_b)
    assert selection_digest("request-a", plan_a) != selection_digest("request-b", plan_a)


def test_missing_or_nonfinite_scores_fail_closed():
    with pytest.raises(ValueError, match="missing scores"):
        select_active_blocks((0, 1), {0: 1.0}, keep_tokens=1, block_size=1)
    with pytest.raises(ValueError, match="non-finite"):
        select_active_blocks((0, 1), {0: 1.0, 1: float("nan")}, keep_tokens=1, block_size=1)
