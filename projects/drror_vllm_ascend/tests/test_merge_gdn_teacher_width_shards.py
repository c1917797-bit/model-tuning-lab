"""CPU-only tests for deterministic width-shard evidence merging."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "tools/merge_gdn_teacher_width_shards.py"
)
spec = importlib.util.spec_from_file_location("width_merge_under_test", SOURCE)
merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)


def row(variant, value, position=0):
    return {
        "sequence_id": "teacher-0",
        "rank": 0,
        "layer": 0,
        "position": position,
        variant + "_relative_l2": value,
    }


def test_combine_fidelity_rows_joins_three_widths_by_coordinate():
    result = merge.combine_fidelity_rows(
        {
            "energy48": [row("energy48", 0.4)],
            "energy64": [row("energy64", 0.3)],
            "energy80": [row("energy80", 0.2)],
        }
    )
    assert result == [
        {
            "sequence_id": "teacher-0",
            "rank": 0,
            "layer": 0,
            "position": 0,
            "energy48_relative_l2": 0.4,
            "energy64_relative_l2": 0.3,
            "energy80_relative_l2": 0.2,
        }
    ]


def test_combine_fidelity_rows_rejects_wrong_or_duplicate_schema():
    rows = {
        "energy48": [row("energy48", 0.4)],
        "energy64": [row("energy64", 0.3)],
        "energy80": [row("energy80", 0.2)],
    }
    rows["energy48"][0]["unexpected"] = True
    with pytest.raises(ValueError, match="schema differs"):
        merge.combine_fidelity_rows(rows)
