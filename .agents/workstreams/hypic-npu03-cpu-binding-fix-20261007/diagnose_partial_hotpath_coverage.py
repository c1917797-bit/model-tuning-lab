#!/usr/bin/env python3
"""Read-only, non-acceptance audit of completed HYPIC quality samples."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from verify_hotpath_request_coverage import (
    CoverageError,
    load_worker_namespace_pids,
    matching_internal_id,
    require,
)


def diagnose(rows: list[dict], events: list[dict], workers: set[int]) -> dict:
    """Diagnose completed rows only; never certify a non-terminal campaign."""
    require(len(workers) == 4, "expected four distinct namespace worker PIDs")
    boundary_ids = {
        event["request_id"] for event in events
        if event.get("event") == "explicit_segment_boundary_active"
        and isinstance(event.get("request_id"), str)
    }
    proof: dict[str, set[int]] = defaultdict(set)
    local_diagnostics: dict[str, list[dict]] = defaultdict(list)
    diagnostic_types = {
        "position_independent_prefill_filter_miss",
        "position_independent_prefill_plan_unavailable",
    }
    for event in events:
        if (event.get("event") in diagnostic_types
                and isinstance(event.get("request_id"), str)):
            local_diagnostics[event["request_id"]].append(event)
        if (
            event.get("event") == "worker_hot_request_verified"
            and type(event.get("pid")) is int
            and type(event.get("skipped_prefix_tokens")) is int
            and event["skipped_prefix_tokens"] > 0
            and event.get("complete_hybrid_repair_validated") is True
            and isinstance(event.get("request_id"), str)
        ):
            proof[event["request_id"]].add(event["pid"])
    indexes: set[int] = set()
    scored: set[str] = set()
    issues: list[dict] = []
    verified = 0
    for row in rows:
        index = row.get("index")
        require(type(index) is int and index not in indexes,
                "duplicate or malformed completed sample index")
        indexes.add(index)
        scores = row.get("scores")
        require(isinstance(scores, list) and len(scores) == 3,
                "completed sample lacks three scored requests")
        for repetition, score in enumerate(scores, 1):
            api_id = score.get("request_id")
            require(score.get("repetition") == repetition
                    and isinstance(api_id, str) and api_id not in scored,
                    "duplicate or malformed scored request")
            scored.add(api_id)
            item = {"index": index, "repetition": repetition,
                    "api_request_id": api_id}
            try:
                internal_id = matching_internal_id(api_id, boundary_ids)
            except CoverageError:
                item["reason"] = "boundary_join_missing_or_ambiguous"
                issues.append(item)
                continue
            observed = proof.get(internal_id, set())
            if observed != workers:
                item["reason"] = "four_worker_post_repair_proof_missing"
                item["internal_request_id"] = internal_id
                item["observed_worker_pids"] = sorted(observed)
                local = local_diagnostics.get(internal_id, [])
                item["request_local_diagnostics"] = {
                    "event_counts": dict(Counter(
                        event["event"] for event in local
                    )),
                    "observed_reasons": sorted({
                        str(event["reason"]) for event in local
                        if event.get("reason") is not None
                    }),
                    "first_event": {
                        key: local[0][key] for key in (
                            "event", "reason", "computed_tokens",
                            "host_computed_tokens", "output_computed_tokens",
                            "request_in_pre_schedule_snapshot",
                            "native_prefix_cache_enabled", "candidate_hashes",
                            "ready_hashes",
                        ) if key in local[0]
                    } if local else None,
                    "causal_status": "unresolved_without_matched_state_audit",
                }
                issues.append(item)
                continue
            verified += 1
    return {
        "schema": "hypic-partial-hotpath-diagnostic/v1",
        "acceptance": "not_applicable_to_partial_samples",
        "completed_samples": len(rows),
        "scored_requests": len(scored),
        "four_worker_verified_requests": verified,
        "issue_count": len(issues),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root
    try:
        contract = json.loads((root / "contract.json").read_text(encoding="utf-8"))
        require(contract.get("arm") == "hypic-only"
                and contract.get("mode") == "full"
                and contract.get("max_output_tokens") == 2048
                and contract.get("repetitions") == 3
                and len(contract.get("sample_indexes", ())) == 127,
                "not the frozen full HYPIC quality contract")
        allowed = set(contract["sample_indexes"])
        sample_paths = sorted((root / "samples").glob("*.json"))
        rows = [json.loads(path.read_text(encoding="utf-8"))
                for path in sample_paths]
        require(all(row.get("index") in allowed for row in rows),
                "completed sample outside frozen contract")
        start = json.loads((root / "hypic-only" / "service-start.json")
                           .read_text(encoding="utf-8"))
        workers = load_worker_namespace_pids(root, start)
        evidence = root / "hypic-only" / "hypic-evidence.jsonl"
        events = [json.loads(line) for line in
                  evidence.read_text(encoding="utf-8").splitlines()
                  if line.strip()]
        report = diagnose(rows, events, workers)
    except (CoverageError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "hypic-partial-hotpath-diagnostic/v1",
                          "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
