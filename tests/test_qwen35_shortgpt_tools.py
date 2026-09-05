#!/usr/bin/env python3
"""Dependency-free regression checks for the ShortGPT host tools."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_qwen35_shortgpt_bi import (
    compress_layers,
    load_records,
    summarize,
)
from scripts.collect_qwen35_shortgpt_bi import load_questions
from scripts.freeze_qwen35_shortgpt_layer_set import freeze


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        dataset = Path(directory) / "data.jsonl"
        dataset.write_text(
            '{"question":"first","answer":"a"}\n'
            '{"question":"second","answer":"b"}\n',
            encoding="utf-8",
        )
        assert load_questions(dataset, 1) == ["first"]

        path = Path(directory) / "rank-0.jsonl"
        with path.open("w", encoding="utf-8") as stream:
            for observation in range(8):
                for layer in range(8):
                    influence = (layer + 1) / 1000 + observation / 1e7
                    stream.write(
                        json.dumps(
                            {
                                "layer": layer,
                                "layer_type": (
                                    "full_attention"
                                    if layer % 4 == 3
                                    else "linear_attention"
                                ),
                                "sample_tokens": 32,
                                "influence_sum": influence * 32,
                                "influence_mean": influence,
                            }
                        )
                        + "\n"
                    )
        records = load_records([path], expected_layers=8)
        report = summarize(
            records,
            expected_layers=8,
            stability_splits=4,
            candidate_sizes=[2, 4],
            min_observations=8,
            min_spearman=0.99,
        )
        assert report["ready_to_freeze"]
        assert (
            report["candidate_sets_lowest_global_influence"][0]["layers"]
            == [0, 1]
        )

        analysis = Path(directory) / "analysis.json"
        report["schema"] = "qwen35-shortgpt-bi-analysis/v1"
        report["expected_layers"] = 64
        report["candidate_sets_lowest_global_influence"].append(
            {
                "removed_layer_count": 8,
                "layers": list(range(8)),
                "env_spec": "0-7",
            }
        )
        analysis.write_text(json.dumps(report), encoding="utf-8")
        frozen = freeze(analysis, 8)
        assert frozen["status"] == "frozen"
        assert frozen["layers"] == list(range(8))
        assert frozen["env_spec"] == "0-7"

    assert compress_layers([1, 2, 3, 5, 8, 9]) == "1-3,5,8-9"
    print("PASS: Qwen3.5 ShortGPT host tools")


if __name__ == "__main__":
    main()
