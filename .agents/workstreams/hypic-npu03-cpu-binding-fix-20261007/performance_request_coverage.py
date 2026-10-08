#!/usr/bin/env python3
"""Join measured completion IDs to four-worker post-repair evidence."""

from __future__ import annotations

from collections import defaultdict


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def diagnose_request_coverage(
    measured: list[dict], events: list[dict], expected_worker_pids: set[int],
) -> dict:
    require(len(measured) == 40
            and sorted(row.get("index") for row in measured) == list(range(40)),
            "measured completion row cardinality drift")
    ids = [row.get("request_id") for row in measured]
    require(all(isinstance(value, str) and value.startswith("cmpl-")
                for value in ids) and len(ids) == len(set(ids)),
            "measured completion IDs are missing, malformed or duplicated")
    require(len(expected_worker_pids) == 4,
            "physical TP4 worker namespace identity absent")
    boundaries = {
        row["request_id"] for row in events
        if row.get("event") == "explicit_segment_boundary_active"
        and isinstance(row.get("request_id"), str)
    }
    hot: dict[str, set[int]] = defaultdict(set)
    for event in events:
        if (event.get("event") == "worker_hot_request_verified"
                and isinstance(event.get("request_id"), str)
                and type(event.get("pid")) is int
                and type(event.get("skipped_prefix_tokens")) is int
                and event["skipped_prefix_tokens"] > 0
                and event.get("complete_hybrid_repair_validated") is True):
            hot[event["request_id"]].add(event["pid"])
    issues = []
    joined = {}
    for row in measured:
        api_id = row["request_id"]
        matches = {value for value in boundaries
                   if value == api_id or value.startswith(api_id + "-")}
        if len(matches) != 1:
            issues.append({"index": row["index"], "request_id": api_id,
                           "reason": "missing-or-ambiguous-boundary",
                           "boundary_match_count": len(matches)})
            continue
        internal = next(iter(matches))
        joined[api_id] = internal
        observed = hot.get(internal, set())
        if observed != expected_worker_pids:
            issues.append({"index": row["index"], "request_id": api_id,
                           "internal_request_id": internal,
                           "reason": "four-worker-post-repair-missing",
                           "observed_worker_pids": sorted(observed)})
    require(len(set(joined.values())) == len(joined),
            "measured IDs ambiguously share one scheduler request")
    return {
        "schema": "hypic-performance-request-coverage/v1",
        "measured_requests": 40,
        "boundary_joined_requests": len(joined),
        "four_worker_verified_requests": 40 - len(issues),
        "issue_count": len(issues),
        "issues": issues,
    }
