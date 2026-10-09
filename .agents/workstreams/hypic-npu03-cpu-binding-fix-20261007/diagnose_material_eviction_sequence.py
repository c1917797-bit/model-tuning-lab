#!/usr/bin/env python3
"""Read-only event-order addendum for completed HYPIC scored requests.

This is descriptive diagnosis, never a quality or strict-hot acceptance gate.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from diagnose_partial_hotpath_coverage import diagnose
from verify_hotpath_request_coverage import load_worker_namespace_pids


def classify_issue(issue: dict, events: list[dict]) -> dict:
    """Join one cold scored ID to its scheduler material transitions."""
    rid = issue.get("internal_request_id")
    plans = [event for event in events if
             event.get("event") == "position_independent_prefill_plan_unavailable"
             and event.get("request_id") == rid]
    result = {"index": issue["index"], "repetition": issue["repetition"],
              "internal_request_id": rid, "classification": "unresolved"}
    if len(plans) != 1 or type(plans[0].get("time_ns")) is not int:
        result["reason"] = "missing_or_ambiguous_plan_event"
        return result
    plan = plans[0]
    hashes = plan.get("candidate_hashes")
    if not isinstance(hashes, list) or not hashes or not all(
        isinstance(value, str) for value in hashes
    ):
        result["reason"] = "candidate_hashes_unavailable"
        return result
    transitions = []
    for candidate in hashes:
        history = []
        for event in events:
            if event.get("event") != "materialization_report" or type(
                event.get("time_ns")
            ) is not int or event["time_ns"] >= plan["time_ns"]:
                continue
            ready = candidate in (event.get("ready_hashes") or [])
            evicted = candidate in (event.get("evicted_hashes") or [])
            if ready != evicted:
                history.append((event["time_ns"], "ready" if ready else "evicted"))
        history.sort()
        transitions.append({
            "candidate_hash": candidate,
            "last_prior": {"time_ns": history[-1][0], "state": history[-1][1]}
            if history else None,
            "ever_ready_before_reject": any(state == "ready" for _, state in history),
        })
    result.update({
        "plan_reason": plan.get("reason"),
        "plan_time_ns": plan["time_ns"],
        "computed_tokens": plan.get("computed_tokens"),
        "ready_hashes_at_reject": plan.get("ready_hashes"),
        "transitions": transitions,
    })
    if (plan.get("reason") == "computed_prefix_not_reusable_boundary"
            and type(plan.get("computed_tokens")) is int
            and plan["computed_tokens"] > 0
            and plan.get("ready_hashes") == []
            and all(item["ever_ready_before_reject"] and
                    item["last_prior"] is not None and
                    item["last_prior"]["state"] == "evicted"
                    for item in transitions)):
        result["classification"] = "evicted_before_partial_prefill_rejection"
    return result


def diagnose_root(root: Path) -> dict:
    contract = json.loads((root / "contract.json").read_text(encoding="utf-8"))
    if (contract.get("arm") != "hypic-only" or contract.get("mode") != "full"
            or contract.get("max_output_tokens") != 2048
            or contract.get("repetitions") != 3
            or len(contract.get("sample_indexes", ())) != 127):
        raise RuntimeError("not the frozen full quality contract")
    rows = [json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((root / "samples").glob("*.json"))]
    start = json.loads((root / "hypic-only/service-start.json").read_text())
    workers = load_worker_namespace_pids(root, start)
    events = [json.loads(line) for line in
              (root / "hypic-only/hypic-evidence.jsonl").read_text().splitlines()
              if line.strip()]
    partial = diagnose(rows, events, workers)
    classifications = [classify_issue(item, events) for item in partial["issues"]]
    return {
        "schema": "hypic-material-eviction-sequence-diagnostic/v1",
        "acceptance": "not_applicable_to_partial_samples",
        "completed_samples": partial["completed_samples"],
        "scored_requests": partial["scored_requests"],
        "four_worker_verified_requests": partial["four_worker_verified_requests"],
        "issue_count": partial["issue_count"],
        "classifications": dict(Counter(item["classification"] for item in classifications)),
        "issues": classifications,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(diagnose_root(args.root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
