"""Strict summarizer for Tail-Replay full-group runtime evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable


DEFAULT_GROUPS = tuple(range(0, 64, 4))
DEFAULT_RATIOS = (0.05, 0.10)


def _aggregate(values: Iterable[float]) -> dict[str, float | int | None]:
    materialized = [float(value) for value in values]
    if not materialized:
        return {"count": 0, "min": None, "mean": None, "max": None}
    return {
        "count": len(materialized),
        "min": min(materialized),
        "mean": fmean(materialized),
        "max": max(materialized),
    }


def _unique_index(
    events: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...],
    errors: list[str],
    label: str,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    counts = Counter(tuple(event.get(field) for field in key_fields) for event in events)
    duplicates = sorted(key for key, count in counts.items() if count != 1)
    if duplicates:
        errors.append(f"{label} duplicate keys: {duplicates}")
    return {
        tuple(event.get(field) for field in key_fields): event
        for event in events
    }


def _metric_values(
    events: list[dict[str, Any]],
    *,
    metric: str,
    state_kind: str | None = None,
) -> list[float]:
    values = []
    for event in events:
        if state_kind is None:
            values.append(float(event["output"][metric]))
        else:
            values.extend(
                float(state[state_kind][metric]) for state in event["states"]
            )
    return values


def summarize_events(
    events: list[dict[str, Any]],
    *,
    expected_ranks: tuple[int, ...] = (0, 1, 2, 3),
    expected_groups: tuple[int, ...] = DEFAULT_GROUPS,
    expected_ratios: tuple[float, ...] = DEFAULT_RATIOS,
) -> dict[str, Any]:
    errors: list[str] = []
    exact = [
        event for event in events
        if event.get("event") == "group_oracle_exact_result"
    ]
    tails = [
        event for event in events
        if event.get("event") == "group_oracle_tail_result"
    ]
    preservation = [
        event for event in events
        if event.get("event") == "group_oracle_live_cache_preservation"
    ]
    attempts = [
        event for event in events
        if event.get("event") == "group_oracle_attempt"
    ]
    exact_index = _unique_index(
        exact,
        key_fields=("distributed_rank", "start_layer"),
        errors=errors,
        label="exact",
    )
    tail_index = _unique_index(
        tails,
        key_fields=("distributed_rank", "start_layer", "replay_ratio"),
        errors=errors,
        label="tail",
    )
    preservation_index = _unique_index(
        preservation,
        key_fields=("distributed_rank", "start_layer"),
        errors=errors,
        label="cache-preservation",
    )
    attempt_index = _unique_index(
        attempts,
        key_fields=("distributed_rank", "start_layer"),
        errors=errors,
        label="attempt",
    )

    expected_exact = {
        (rank, group) for rank in expected_ranks for group in expected_groups
    }
    expected_tail = {
        (rank, group, ratio)
        for rank in expected_ranks
        for group in expected_groups
        for ratio in expected_ratios
    }
    for label, actual, expected in (
        ("exact", set(exact_index), expected_exact),
        ("tail", set(tail_index), expected_tail),
        ("cache-preservation", set(preservation_index), expected_exact),
        ("attempt", set(attempt_index), expected_exact),
    ):
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            errors.append(f"{label} missing keys: {missing}")
        if extra:
            errors.append(f"{label} unexpected keys: {extra}")

    failed_exact = sorted(
        key for key, event in exact_index.items()
        if not bool(event.get("harness_passed"))
    )
    if failed_exact:
        errors.append(f"exact harness failures: {failed_exact}")
    mutated = sorted(
        key for key, event in preservation_index.items()
        if not bool(event.get("cache_preserved"))
    )
    if mutated:
        errors.append(f"live cache mutation: {mutated}")
    nonfinite = []
    for key, event in exact_index.items():
        if not bool(event["output"].get("all_finite")):
            nonfinite.append(("exact-output", key))
        for state in event["states"]:
            for kind in ("conv", "recurrent"):
                if not bool(state[kind].get("all_finite")):
                    nonfinite.append((f"exact-{kind}", key, state["layer_idx"]))
    for key, event in tail_index.items():
        if not bool(event["output"].get("all_finite")):
            nonfinite.append(("tail-output", key))
        for state in event["states"]:
            for kind in ("conv", "recurrent"):
                if not bool(state[kind].get("all_finite")):
                    nonfinite.append((f"tail-{kind}", key, state["layer_idx"]))
    if nonfinite:
        errors.append(f"nonfinite metrics: {nonfinite}")

    tail_summary = {}
    for ratio in expected_ratios:
        ratio_events = [
            event for event in tails
            if float(event.get("replay_ratio")) == ratio
        ]
        tail_summary[str(ratio)] = {
            "result_rows": len(ratio_events),
            "output_relative_l2": _aggregate(
                _metric_values(ratio_events, metric="relative_l2")
            ),
            "output_cosine": _aggregate(
                _metric_values(ratio_events, metric="cosine")
            ),
            "conv_state_relative_l2": _aggregate(
                _metric_values(
                    ratio_events, metric="relative_l2", state_kind="conv"
                )
            ),
            "recurrent_state_relative_l2": _aggregate(
                _metric_values(
                    ratio_events, metric="relative_l2", state_kind="recurrent"
                )
            ),
        }

    source_identities = {
        (
            event.get("gdn_forward_source_path"),
            event.get("gdn_forward_source_sha256"),
        )
        for event in attempts
    }
    missing_identities = [
        identity for identity in source_identities
        if not identity[0] or not identity[1]
    ]
    if missing_identities:
        errors.append(f"missing source identities: {missing_identities}")
    source_identities = sorted(
        source_identities, key=lambda identity: (str(identity[0]), str(identity[1]))
    )
    return {
        "schema": "tail-replay-full-group-summary/v1",
        "ok": not errors,
        "errors": errors,
        "expected": {
            "ranks": list(expected_ranks),
            "group_start_layers": list(expected_groups),
            "replay_ratios": list(expected_ratios),
        },
        "counts": {
            "runtime_events": len(events),
            "attempts": len(attempts),
            "exact_results": len(exact),
            "tail_results": len(tails),
            "cache_preservation_results": len(preservation),
        },
        "source_identities": [
            {"path": path, "sha256": sha256}
            for path, sha256 in source_identities
        ],
        "exact": {
            "all_harness_passed": not failed_exact,
            "output_relative_l2": _aggregate(
                _metric_values(exact, metric="relative_l2")
            ),
            "conv_state_relative_l2": _aggregate(
                _metric_values(exact, metric="relative_l2", state_kind="conv")
            ),
            "recurrent_state_relative_l2": _aggregate(
                _metric_values(
                    exact, metric="relative_l2", state_kind="recurrent"
                )
            ),
        },
        "tail": tail_summary,
        "live_cache_bitwise_preserved": not mutated,
    }


def summarize_file(
    input_path: Path,
    output_path: Path,
    *,
    expected_ranks: tuple[int, ...],
    expected_groups: tuple[int, ...],
    expected_ratios: tuple[float, ...],
) -> dict[str, Any]:
    events = [
        json.loads(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = summarize_events(
        events,
        expected_ranks=expected_ranks,
        expected_groups=expected_groups,
        expected_ratios=expected_ratios,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _int_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(item) for item in raw.split(",") if item)


def _float_tuple(raw: str) -> tuple[float, ...]:
    return tuple(float(item) for item in raw.split(",") if item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ranks", default="0,1,2,3")
    parser.add_argument(
        "--groups", default=",".join(str(group) for group in DEFAULT_GROUPS)
    )
    parser.add_argument("--ratios", default="0.05,0.10")
    args = parser.parse_args()
    summary = summarize_file(
        args.input,
        args.output,
        expected_ranks=_int_tuple(args.ranks),
        expected_groups=_int_tuple(args.groups),
        expected_ratios=_float_tuple(args.ratios),
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
