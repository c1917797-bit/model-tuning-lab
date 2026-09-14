from __future__ import annotations

from copy import deepcopy

from tail_replay_ascend.group_summary import summarize_events


def _metric(value=0.0):
    return {
        "all_finite": True,
        "relative_l2": value,
        "cosine": 1.0 - value,
    }


def _events():
    events = []
    for rank in (0, 1):
        events.append(
            {
                "event": "group_oracle_attempt",
                "distributed_rank": rank,
                "start_layer": 0,
                "gdn_forward_source_path": "/runtime/gdn.py",
                "gdn_forward_source_sha256": "abc",
            }
        )
        events.append(
            {
                "event": "group_oracle_exact_result",
                "distributed_rank": rank,
                "start_layer": 0,
                "harness_passed": True,
                "output": _metric(),
                "states": [
                    {"layer_idx": idx, "conv": _metric(), "recurrent": _metric()}
                    for idx in range(3)
                ],
            }
        )
        for ratio, value in ((0.05, 0.4), (0.10, 0.3)):
            events.append(
                {
                    "event": "group_oracle_tail_result",
                    "distributed_rank": rank,
                    "start_layer": 0,
                    "replay_ratio": ratio,
                    "output": _metric(value),
                    "states": [
                        {
                            "layer_idx": idx,
                            "conv": _metric(),
                            "recurrent": _metric(value),
                        }
                        for idx in range(3)
                    ],
                }
            )
        events.append(
            {
                "event": "group_oracle_live_cache_preservation",
                "distributed_rank": rank,
                "start_layer": 0,
                "cache_preserved": True,
            }
        )
    return events


def test_group_summary_accepts_complete_exact_controlled_matrix():
    summary = summarize_events(
        _events(),
        expected_ranks=(0, 1),
        expected_groups=(0,),
        expected_ratios=(0.05, 0.10),
    )
    assert summary["ok"] is True
    assert summary["errors"] == []
    assert summary["counts"]["exact_results"] == 2
    assert summary["counts"]["tail_results"] == 4
    assert summary["tail"]["0.05"]["output_relative_l2"]["mean"] == 0.4
    assert summary["tail"]["0.1"]["recurrent_state_relative_l2"]["count"] == 6
    assert summary["live_cache_bitwise_preserved"] is True


def test_group_summary_rejects_missing_or_mutating_evidence():
    events = deepcopy(_events())
    events = [
        event
        for event in events
        if not (
            event["event"] == "group_oracle_tail_result"
            and event["distributed_rank"] == 1
            and event["replay_ratio"] == 0.10
        )
    ]
    for event in events:
        if (
            event["event"] == "group_oracle_live_cache_preservation"
            and event["distributed_rank"] == 0
        ):
            event["cache_preserved"] = False
    summary = summarize_events(
        events,
        expected_ranks=(0, 1),
        expected_groups=(0,),
        expected_ratios=(0.05, 0.10),
    )
    assert summary["ok"] is False
    assert any("tail missing keys" in error for error in summary["errors"])
    assert any("live cache mutation" in error for error in summary["errors"])
