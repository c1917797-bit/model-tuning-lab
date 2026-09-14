from __future__ import annotations

import pytest

from tools.summarize_sliminfer_shadow import AuditError, audit_events


RANKS = {0, 1, 2, 3}


def _events():
    events = [
        {
            "event": "selection_shadow_patch_installed",
            "distributed_rank": rank,
        }
        for rank in RANKS
    ]
    selected_by_layer = {
        19: list(range(192)),
        39: list(range(96)),
        59: list(range(64)),
    }
    input_by_layer = {19: 256, 39: 192, 59: 96}
    for rank in RANKS:
        for layer in (19, 39, 59):
            selected = selected_by_layer[layer]
            events.append(
                {
                    "event": "selection_shadow_layer",
                    "distributed_rank": rank,
                    "forward_serial": 3,
                    "request_index": 0,
                    "request_tokens": 16384,
                    "layer_index": layer,
                    "input_block_count": input_by_layer[layer],
                    "selected_block_count": len(selected),
                    "selected_blocks": selected,
                    "selection_sha256": f"selection-{layer}",
                    "score_sha256": f"score-{layer}",
                }
            )
    return events


def test_audit_accepts_complete_identical_tp4_staged_selection():
    summary = audit_events(_events(), expected_ranks=RANKS, min_request_tokens=8192)
    assert summary["status"] == "passed"
    assert summary["pruning_observed"] is True
    assert summary["request_count"] == 1
    assert [
        item["selected_block_count"] for item in summary["requests"][0]["layers"]
    ] == [192, 96, 64]


def test_audit_rejects_rank_selection_disagreement():
    events = _events()
    target = next(
        item
        for item in events
        if item.get("event") == "selection_shadow_layer"
        and item["distributed_rank"] == 3
        and item["layer_index"] == 39
    )
    target["selected_blocks"] = target["selected_blocks"][:-1]
    with pytest.raises(AuditError, match="disagrees"):
        audit_events(events, expected_ranks=RANKS, min_request_tokens=8192)


def test_audit_rejects_missing_rank_and_non_pruning_activation():
    missing = [
        item
        for item in _events()
        if not (
            item.get("event") == "selection_shadow_layer"
            and item["distributed_rank"] == 2
            and item["layer_index"] == 59
        )
    ]
    with pytest.raises(AuditError, match="has ranks"):
        audit_events(missing, expected_ranks=RANKS, min_request_tokens=8192)

    non_pruning = _events()
    for item in non_pruning:
        if item.get("event") == "selection_shadow_layer":
            item["input_block_count"] = item["selected_block_count"]
    with pytest.raises(AuditError, match="no block reduction"):
        audit_events(non_pruning, expected_ranks=RANKS, min_request_tokens=8192)
