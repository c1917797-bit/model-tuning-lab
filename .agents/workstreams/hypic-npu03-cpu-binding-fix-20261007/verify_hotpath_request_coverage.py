#!/usr/bin/env python3
"""Fail-closed, read-only request-level HYPIC worker-hot evidence gate.

This checks one narrow activation claim. It does not replace quality scoring,
service fingerprint, continuous isolation, raw-hash or exact-release audits.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


class CoverageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageError(message)


def matching_internal_id(api_id: str, boundary_ids: set[str]) -> str:
    """Join the API response ID to exactly one scheduler-internal request ID."""
    require(api_id.startswith("chatcmpl-"), "scored API request ID is malformed")
    matches = {
        value for value in boundary_ids
        if value == api_id or value.startswith(api_id + "-")
    }
    require(len(matches) == 1, "scored request lacks one unique boundary ID")
    return next(iter(matches))


def audit_coverage(
    scored_ids: list[str],
    events: list[dict],
    expected_worker_pids: set[int],
) -> dict:
    require(len(scored_ids) == len(set(scored_ids)), "duplicate scored request ID")
    require(len(expected_worker_pids) == 4, "expected four distinct TP worker PIDs")
    boundary_ids = {
        row["request_id"] for row in events
        if row.get("event") == "explicit_segment_boundary_active"
        and isinstance(row.get("request_id"), str)
    }
    joined = {
        api_id: matching_internal_id(api_id, boundary_ids)
        for api_id in scored_ids
    }
    require(
        len(set(joined.values())) == len(joined),
        "two scored API IDs joined to one internal request",
    )
    observed: dict[str, set[int]] = defaultdict(set)
    for row in events:
        if row.get("event") != "worker_hot_request_verified":
            continue
        request_id = row.get("request_id")
        pid = row.get("pid")
        skipped = row.get("skipped_prefix_tokens")
        if (
            isinstance(request_id, str)
            and type(pid) is int
            and type(skipped) is int
            and skipped > 0
            and row.get("complete_hybrid_repair_validated") is True
        ):
            observed[request_id].add(pid)
    missing = [
        api_id for api_id, internal_id in joined.items()
        if observed.get(internal_id, set()) != expected_worker_pids
    ]
    require(
        not missing,
        f"{len(missing)}/{len(scored_ids)} scored requests lack four-worker "
        "post-repair hot-path proof; batch counters are not request evidence",
    )
    return {
        "schema": "hypic-scored-request-hotpath-coverage/v1",
        "scored_requests": len(scored_ids),
        "expected_worker_count": len(expected_worker_pids),
        "boundary_joined_requests": len(joined),
        "four_worker_post_repair_verified_requests": len(joined),
        "activation_scope": "each scored request on physical NPU0-3 TP4",
    }


def load_terminal_arm(root: Path) -> tuple[list[str], list[dict], set[int]]:
    require(root.is_dir(), "attempt root absent")
    contract = json.loads((root / "contract.json").read_text(encoding="utf-8"))
    require(
        contract.get("arm") == "hypic-only"
        and contract.get("mode") == "full"
        and contract.get("max_output_tokens") == 2048
        and contract.get("repetitions") == 3,
        "not the frozen full 2048-token candidate contract",
    )
    indexes = contract.get("sample_indexes")
    require(
        isinstance(indexes, list) and len(indexes) == 127
        and len(set(indexes)) == 127,
        "contract is not the complete 127-sample ruler",
    )
    sample_dir = root / "samples"
    actual = {path.name for path in sample_dir.glob("*.json")}
    expected = {f"{index:03d}.json" for index in indexes}
    require(actual == expected, "candidate has missing or extra sample files")
    scored_ids: list[str] = []
    for index in indexes:
        row = json.loads(
            (sample_dir / f"{index:03d}.json").read_text(encoding="utf-8")
        )
        require(row.get("index") == index, "sample index drift")
        scores = row.get("scores")
        require(
            isinstance(scores, list) and len(scores) == 3,
            "sample lacks three scored repetitions",
        )
        for repetition, score in enumerate(scores, 1):
            require(
                score.get("repetition") == repetition
                and isinstance(score.get("request_id"), str),
                "scored repetition or request ID drift",
            )
            scored_ids.append(score["request_id"])
    require(len(scored_ids) == 381, "scored row cardinality drift")
    start = json.loads(
        (root / "hypic-only" / "service-start.json").read_text(encoding="utf-8")
    )
    workers = start.get("worker_pid_by_physical_npu")
    require(
        isinstance(workers, dict) and set(workers) == {"0", "1", "2", "3"},
        "service does not identify physical NPU0-3 workers",
    )
    expected_worker_pids = {int(value) for value in workers.values()}
    require(len(expected_worker_pids) == 4, "TP worker PID identity drift")
    evidence = root / "hypic-only" / "hypic-evidence.jsonl"
    require(evidence.is_file(), "HYPIC evidence file absent")
    events = [
        json.loads(line)
        for line in evidence.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return scored_ids, events, expected_worker_pids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="terminal candidate attempt root")
    args = parser.parse_args()
    try:
        scored_ids, events, workers = load_terminal_arm(args.root)
        report = audit_coverage(scored_ids, events, workers)
    except (CoverageError, OSError, ValueError, KeyError) as exc:
        print(f"UNVERIFIED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
