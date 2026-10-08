#!/usr/bin/env python3
"""Replay the five r12 cold scored requests from immutable raw evidence."""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path


ROOT = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "quality-context-41984-hotpath-cache10r12-stress-hypic"
)
EVIDENCE = ROOT / "hypic-only/hypic-evidence.jsonl"
EVIDENCE_SHA256 = (
    "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60"
)
EXPECTED_COLD = {
    "77:1": "ready_cache_partial_chunk",
    "77:3": "scored_producer_rematerialization",
    "81:3": "scored_producer_rematerialization",
    "85:2": "scored_producer_rematerialization",
    "88:2": "scored_producer_rematerialization",
}


def expect(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def main() -> int:
    raw = EVIDENCE.read_bytes()
    expect(hashlib.sha256(raw).hexdigest() == EVIDENCE_SHA256,
           "r12 evidence hash changed")
    rows = [json.loads(line) for line in raw.splitlines()]
    by_request: dict[str, list[dict]] = collections.defaultdict(list)
    for event in rows:
        if event.get("request_id"):
            by_request[event["request_id"]].append(event)

    configured = [event for event in rows
                  if event["event"] == "material_cache_configured"]
    expect(bool(configured) and
           all(event.get("max_segments") == 10 for event in configured),
           "cache capacity is not the frozen 10 segments")
    attempts = [event for event in rows if event["event"] ==
                "position_independent_materialization_plan_attempted"]
    materialization_hashes = collections.Counter(
        segment_hash
        for event in attempts
        for segment_hash in event.get("candidate_hashes", [])
    )
    expect(sum(materialization_hashes.values()) == 23
           and len(materialization_hashes) == 19,
           "producer count/unique-segment count drifted")

    samples = sorted((ROOT / "samples").glob("*.json"))
    expect({int(path.stem) for path in samples} ==
           set(range(75, 92)) | {107, 111}, "sample set drifted")
    scored = hot = 0
    cold: dict[str, str] = {}
    repeated_producer_hashes: set[str] = set()
    for path in samples:
        sample = json.loads(path.read_text(encoding="utf-8"))
        expect(len(sample["scores"]) == 3, "scored repetition count drifted")
        for score in sample["scores"]:
            scored += 1
            key = f"{sample['index']}:{score['repetition']}"
            base = score["request_id"] + "-"
            full_ids = [request_id for request_id in by_request
                        if request_id.startswith(base)]
            expect(len(full_ids) == 1, f"{key}: ambiguous request join")
            events = by_request[full_ids[0]]
            worker_pids = {event["pid"] for event in events
                           if event["event"] == "worker_hot_request_verified"}
            if len(worker_pids) == 4:
                hot += 1
                continue
            expect(not worker_pids, f"{key}: partial worker proof")
            reasons = [event.get("reason") for event in events
                       if event["event"] ==
                       "position_independent_prefill_plan_unavailable"]
            producer = [event for event in events if event["event"] ==
                        "position_independent_materialization_plan_attempted"]
            if key == "77:1":
                expect(not producer and reasons == [
                    "partial_prefill_has_no_complete_reusable_segment",
                    "no_hot_rewrite_or_materialization",
                ], "77:1 reason sequence drifted")
                first = next(event for event in events if event["event"] ==
                             "position_independent_prefill_plan_unavailable")
                expect(first["logical_scheduled_tokens"] <
                       sample["segment_ends"][0] and
                       bool(first.get("ready_hashes")),
                       "77:1 no longer has a ready segment but short chunk")
                cold[key] = "ready_cache_partial_chunk"
            else:
                expect(len(producer) == 1 and reasons == [
                    "computed_prefix_not_reusable_boundary"
                ], f"{key}: producer/reason sequence drifted")
                hashes = producer[0]["candidate_hashes"]
                expect(len(hashes) == 1 and
                       materialization_hashes[hashes[0]] == 2,
                       f"{key}: segment is not a repeated producer")
                repeated_producer_hashes.add(hashes[0])
                cold[key] = "scored_producer_rematerialization"

    expect(scored == 57 and hot == 52, "scored/hot coverage drifted")
    expect(cold == EXPECTED_COLD, "cold request classification drifted")
    expect(repeated_producer_hashes ==
           {segment_hash for segment_hash, count in
            materialization_hashes.items() if count == 2},
           "four repeated materializations do not match four cold producers")
    print(json.dumps({
        "schema": "hypic-cache10r12-fallback-audit/v1",
        "evidence_sha256": EVIDENCE_SHA256,
        "scored": scored,
        "four_worker_hot": hot,
        "cold_reasons": cold,
        "max_segments": 10,
        "producer_attempts": 23,
        "unique_producer_segments": 19,
        "repeated_producer_segments": 4,
        "exact_cache_eviction_causality_proven": False,
        "paired_quality_or_performance_verdict": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
