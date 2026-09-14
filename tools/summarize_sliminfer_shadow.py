#!/usr/bin/env python3
"""Fail-closed audit of a SlimInfer TP selection-shadow evidence stream."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Iterable


BOUNDARIES = (19, 39, 59)


class AuditError(RuntimeError):
    pass


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AuditError(f"invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(item, dict):
            raise AuditError(f"line {line_number} is not a JSON object")
        events.append(item)
    if not events:
        raise AuditError("evidence stream is empty")
    return events


def _rank(item: dict[str, Any]) -> int:
    value = item.get("distributed_rank")
    if not isinstance(value, int):
        raise AuditError("selection evidence is missing an integer distributed_rank")
    return value


def audit_events(
    events: Iterable[dict[str, Any]],
    *,
    expected_ranks: set[int],
    min_request_tokens: int,
    require_semantic: bool = False,
) -> dict[str, Any]:
    if not expected_ranks:
        raise AuditError("expected_ranks must not be empty")
    if min_request_tokens <= 0:
        raise AuditError("min_request_tokens must be positive")

    materialized = list(events)
    patch_events = [
        item
        for item in materialized
        if item.get("event") == "selection_shadow_patch_installed"
    ]
    patch_pids = {item.get("pid") for item in patch_events}
    if (
        len(patch_events) != len(expected_ranks)
        or len(patch_pids) != len(expected_ranks)
        or not all(isinstance(pid, int) for pid in patch_pids)
    ):
        raise AuditError(
            "patch installation must cover one distinct worker process per "
            f"expected rank; events={len(patch_events)}, pids={sorted(patch_pids, key=str)}"
        )

    grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for item in materialized:
        if item.get("event") != "selection_shadow_layer":
            continue
        request_tokens = item.get("request_tokens")
        if not isinstance(request_tokens, int) or request_tokens < min_request_tokens:
            continue
        key = (
            int(item["forward_serial"]),
            int(item["request_index"]),
            request_tokens,
        )
        grouped[key].append(item)
    if not grouped:
        raise AuditError("no qualifying selection-shadow request was found")

    request_summaries: list[dict[str, Any]] = []
    pruning_observed = False
    for key, request_events in sorted(grouped.items()):
        by_layer: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for item in request_events:
            by_layer[int(item["layer_index"])].append(item)
        if tuple(sorted(by_layer)) != BOUNDARIES:
            raise AuditError(f"request {key} does not contain all boundary layers")

        previous_selected: set[int] | None = None
        layer_summaries: list[dict[str, Any]] = []
        for layer in BOUNDARIES:
            items = by_layer[layer]
            ranks = {_rank(item) for item in items}
            if ranks != expected_ranks or len(items) != len(expected_ranks):
                raise AuditError(
                    f"request {key} layer {layer} has ranks {sorted(ranks)}"
                )
            for field in ("selection_sha256", "score_sha256", "selected_blocks"):
                canonical = {
                    json.dumps(item[field], sort_keys=True, separators=(",", ":"))
                    for item in items
                }
                if len(canonical) != 1:
                    raise AuditError(
                        f"request {key} layer {layer} disagrees on {field}"
                    )
            reference = items[0]
            if require_semantic:
                required = {
                    "mode": "semantic-prefill",
                    "score_block_identity": "compact-remapped-to-absolute",
                    "compact_block_remap_applied": True,
                    "staged_compact_semantics_proven": True,
                    "keep_sink_block": True,
                    "keep_recent_block": True,
                    "runtime_mutation": False,
                }
                mismatch = [
                    field
                    for field, expected in required.items()
                    if reference.get(field) != expected
                ]
                if mismatch:
                    raise AuditError(
                        f"request {key} layer {layer} lacks semantic selection proof: {mismatch}"
                    )
            selected = {int(block) for block in reference["selected_blocks"]}
            if len(selected) != int(reference["selected_block_count"]):
                raise AuditError(f"request {key} layer {layer} has duplicate blocks")
            if require_semantic:
                final_block = (key[2] - 1) // int(reference["block_size"])
                if 0 not in selected or final_block not in selected:
                    raise AuditError(
                        f"request {key} layer {layer} dropped sink or recent block"
                    )
            if previous_selected is not None and not selected <= previous_selected:
                raise AuditError(
                    f"request {key} layer {layer} is not monotonically shrinking"
                )
            previous_selected = selected
            input_count = int(reference["input_block_count"])
            selected_count = len(selected)
            pruning_observed = pruning_observed or selected_count < input_count
            layer_summaries.append(
                {
                    "layer_index": layer,
                    "input_block_count": input_count,
                    "selected_block_count": selected_count,
                    "selection_sha256": reference["selection_sha256"],
                    "score_sha256": reference["score_sha256"],
                }
            )
        request_summaries.append(
            {
                "forward_serial": key[0],
                "request_index": key[1],
                "request_tokens": key[2],
                "layers": layer_summaries,
            }
        )

    if not pruning_observed:
        raise AuditError("selection hook ran, but no block reduction was observed")
    semantic_compactions: list[dict[str, Any]] = []
    if require_semantic:
        for layer in BOUNDARIES:
            items = [
                item
                for item in materialized
                if item.get("event") == "semantic_prefill_compacted"
                and item.get("layer_index") == layer
            ]
            ranks = {_rank(item) for item in items}
            if ranks != expected_ranks or len(items) != len(expected_ranks):
                raise AuditError(
                    f"semantic compaction layer {layer} has ranks {sorted(ranks)}"
                )
            if any(item.get("runtime_mutation") is not True for item in items):
                raise AuditError(f"semantic compaction layer {layer} lacks mutation proof")
            row_pairs = {
                (int(item["input_rows"]), int(item["output_rows"]))
                for item in items
            }
            if len(row_pairs) != 1:
                raise AuditError(f"semantic compaction layer {layer} row counts disagree")
            input_rows, output_rows = next(iter(row_pairs))
            if output_rows >= input_rows:
                raise AuditError(f"semantic compaction layer {layer} did not reduce rows")
            semantic_compactions.append(
                {
                    "layer_index": layer,
                    "input_rows": input_rows,
                    "output_rows": output_rows,
                }
            )
        complete = [
            item
            for item in materialized
            if item.get("event") == "semantic_prefill_complete"
        ]
        ranks = {_rank(item) for item in complete}
        if ranks != expected_ranks or len(complete) != len(expected_ranks):
            raise AuditError(f"semantic completion has ranks {sorted(ranks)}")
        if any(item.get("runtime_mutation") is not True for item in complete):
            raise AuditError("semantic completion lacks mutation proof")
    return {
        "schema": "sliminfer-selection-shadow-audit/v1",
        "status": "passed",
        "expected_ranks": sorted(expected_ranks),
        "patch_worker_pids": sorted(patch_pids),
        "min_request_tokens": min_request_tokens,
        "request_count": len(request_summaries),
        "pruning_observed": True,
        "semantic_required": require_semantic,
        "semantic_compactions": semantic_compactions,
        "requests": request_summaries,
    }


def _parse_ranks(value: str) -> set[int]:
    try:
        ranks = {int(item) for item in value.split(",") if item}
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ranks must be comma-separated integers") from exc
    if not ranks:
        raise argparse.ArgumentTypeError("at least one rank is required")
    return ranks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-ranks", type=_parse_ranks, default={0, 1, 2, 3})
    parser.add_argument("--min-request-tokens", type=int, default=8192)
    parser.add_argument("--require-semantic", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        summary = audit_events(
            load_events(args.evidence),
            expected_ranks=args.expected_ranks,
            min_request_tokens=args.min_request_tokens,
            require_semantic=args.require_semantic,
        )
    except (AuditError, OSError, KeyError, TypeError, ValueError) as exc:
        parser.exit(2, f"FAILED: {exc}\n")

    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        if args.output.exists():
            parser.exit(2, f"FAILED: output already exists: {args.output}\n")
        args.output.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
