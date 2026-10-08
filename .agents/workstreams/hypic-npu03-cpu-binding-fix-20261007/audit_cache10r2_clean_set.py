#!/usr/bin/env python3
"""Re-audit immutable pre-intrusion cache10r2 rows; never claim full quality."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ["HYPIC_HOTPATH_AUDIT_CAMPAIGN"] = "cache10r2"
from hotpath_quality_audit import CAND, frozen_cases, payload_hash, quality, require


EXPECTED_IDS = tuple([*range(53), 54, 55, 56])
EXPECTED = {
    "contract": "9106bfb4a27e6dbd85d88fde76f126a1a9807a889d600e212cb6f9c4705e74c3",
    "arm_result": "d4784bf4c195e05ff483c7e1d8b40e09b2f5894e0b333059b2f39953c79eb767",
    "guard": "e695f7b3823e1d5dbaf87ce9a07b3d25db8b22dc9fc212219fb81f6489ce7975",
    "stop": "d6ad6e3932d7e610d65b0571bbac97bb27fa511fec2d1015208f871adf3af3b6",
    "evidence": "7a577889eda32df5d2f5e33906bd8337d2b94126d31190a224a132dbb21cadf0",
    "sample_manifest": "b9a46e57c3da956f52779303553564036041f0e91f460875caf076ac9b51ca8e",
    "safe_evidence_slice": "0d47c50d2a63c06ae9f4d0ed10ad0a4340899a412982b91eb03c9bb27fc34923",
}
OUT = quality.ROOT / "hotpath-cache10r2-clean-set-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sample_manifest(paths: list[Path]) -> str:
    lines = "".join(f"{quality.sha256(path)}  {path}\n" for path in paths)
    return hashlib.sha256(lines.encode()).hexdigest()


def audit() -> dict:
    root = CAND
    require(root.is_dir(), "candidate root absent")
    paths = sorted((root / "samples").glob("*.json"))
    ids = tuple(int(path.stem) for path in paths)
    require(ids == EXPECTED_IDS and len(paths) == 56,
            "completed sample ID set changed")
    require(sample_manifest(paths) == EXPECTED["sample_manifest"],
            "sample file manifest hash drift")
    artifacts = {
        "contract": root / "contract.json",
        "arm_result": root / "arm-result.json",
        "guard": root / "hypic-only/lane-guard.json",
        "stop": root / "hypic-only/service-stop.json",
        "evidence": root / "hypic-only/hypic-evidence.jsonl",
    }
    for key, path in artifacts.items():
        require(quality.sha256(path) == EXPECTED[key], f"{key} hash drift")
    contract = load(artifacts["contract"])
    result = load(artifacts["arm_result"])
    guard = load(artifacts["guard"])
    stop = load(artifacts["stop"])
    start = load(root / "hypic-only/service-start.json")
    fingerprint = contract["fingerprint"]
    require(contract["arm"] == "hypic-only" and contract["mode"] == "full"
            and contract["sample_indexes"] == list(range(127))
            and contract["repetitions"] == 3 and contract["concurrency"] == 8
            and contract["max_output_tokens"] == 2048
            and fingerprint["physical_npus"] == [0, 1, 2, 3]
            and fingerprint["gpu_memory_utilization"] == 0.85
            and fingerprint["material_cache_max_mb"] == 3584
            and fingerprint["max_materialized_segments"] == 10,
            "quality contract/service identity drift")
    require(result["completed_samples"] == 56 and result["scored_rows"] == 168
            and "lane guard detected foreign" in result["error"],
            "controller failure/completion drift")
    require(guard["samples"] == 507 and not guard["probe_errors"]
            and len(guard["foreign"]) == 2
            and all(item["processes"][0]["container_id"]
                    == "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                    and item["processes"][0]["physical_npu"] == 0
                    for item in guard["foreign"]),
            "foreign-lane evidence drift")
    require(guard["foreign"][0]["processes"][0]["pid"] == 97921
            and guard["foreign"][1]["processes"][0]["pid"] == 101428,
            "foreign PID evidence drift")
    require(sorted(start["worker_pid_by_physical_npu"].values())
            == guard["expected_worker_pids"]
            and start["container_id"] == stop["container_id"]
            and stop["container_removed"] is True
            and stop["owned_npus_released"] is True
            and stop["port_released"] is True
            and stop["lane_available"] is True
            and not stop["service_log_error"],
            "worker/owned-release receipt drift")
    first_foreign = datetime.fromisoformat(guard["foreign"][0]["at_utc"])
    last_file = datetime.fromtimestamp(
        max(path.stat().st_mtime for path in paths), timezone.utc)
    require(last_file < first_foreign, "completed file overlaps first observed intrusion")
    raw_lines = artifacts["evidence"].read_bytes().splitlines(keepends=True)
    event_lines = [(json.loads(line), line) for line in raw_lines if line.strip()]
    require(all(isinstance(event.get("time_ns"), int) for event, _ in event_lines),
            "event timestamp absent")
    cutoff_ns = int(first_foreign.timestamp() * 1_000_000_000)
    safe = [(event, line) for event, line in event_lines
            if event["time_ns"] < cutoff_ns]
    safe_bytes = b"".join(line for _, line in safe)
    require(hashlib.sha256(safe_bytes).hexdigest() == EXPECTED["safe_evidence_slice"],
            "pre-intrusion evidence slice hash drift")
    boundary_ids = {event.get("request_id") for event, _ in safe
                    if event.get("event") == "explicit_segment_boundary_active"}
    hot_workers = {event.get("pid") for event, _ in safe
                   if event.get("event") == "worker_hot_path"}
    verified = sum(int(event.get("verified_hot_requests", 0)) for event, _ in safe
                   if event.get("event") == "complete_hybrid_repair")
    cases, evaluator = frozen_cases()
    require(len(cases) == 127, "frozen LongBench case count drift")
    seen: set[str] = set()
    score_ids: list[str] = []
    correct = 0
    length_limit = 0
    for path in paths:
        row = load(path)
        case = cases[row["index"]]
        for field in ("index", "sample_id", "reference", "prompt_sha256",
                      "prompt_tokens", "difficulty", "length"):
            require(row[field] == case[field], f"{path.name}: {field} drift")
        require(row["arm"] == "hypic-only" and row["mode"] == "full"
                and row["segment_ends"] == [case["boundary"], case["prompt_tokens"]]
                and len(row["warm"]) == 2 and len(row["scores"]) == 3,
                f"{path.name}: protocol/row count drift")
        for warm in row["warm"]:
            require(warm["request_sha256"] == payload_hash(case, 1)
                    and warm["usage"]["prompt_tokens"] == case["prompt_tokens"]
                    and warm["request_id"] not in seen,
                    f"{path.name}: warm request drift")
            seen.add(warm["request_id"])
        for repeat, score in enumerate(row["scores"], 1):
            text = score["response_text"]
            prediction, scored = evaluator.score_case(
                "longbenchv2", text, case["reference"])
            require(score["repetition"] == repeat
                    and score["request_sha256"] == payload_hash(case, 2048)
                    and score["usage"]["prompt_tokens"] == case["prompt_tokens"]
                    and score["response_sha256"] == hashlib.sha256(text.encode()).hexdigest()
                    and score["prediction"] == prediction
                    and score["correct"] is bool(scored)
                    and score["request_id"] not in seen,
                    f"{path.name}: scored request/scorer drift")
            seen.add(score["request_id"])
            score_ids.append(score["request_id"])
            correct += bool(scored)
            length_limit += score["finish_reason"] == "length"
    require(len(seen) == 280 and len(score_ids) == 168 and correct == 95,
            "partial row cardinality/score drift")
    for request_id in score_ids:
        matches = [value for value in boundary_ids
                   if value == request_id or
                   (isinstance(value, str) and value.startswith(request_id + "-"))]
        require(len(matches) == 1, "scored request boundary join failed")
    require(verified >= len(score_ids) and len(hot_workers) == 4,
            "bounded aggregate HYPIC evidence absent")
    return {
        "schema": "hypic-cache10r2-clean-set-audit/v1",
        "original_arm_valid": False,
        "partial_rows_valid": True,
        "full_paired_quality_decision": "not-available",
        "eligible_for_revised_protocol": "pending-user-method-choice",
        "root": str(root), "sample_indices": list(ids),
        "scored_rows": len(score_ids), "correct": correct,
        "length_limit": length_limit, "distinct_request_ids": len(seen),
        "first_foreign_at_utc": first_foreign.isoformat(),
        "last_completed_file_at_utc": last_file.isoformat(),
        "safe_event_lines": len(safe), "safe_verified_hot_requests_aggregate": verified,
        "safe_hot_worker_pids": sorted(hot_workers),
        "per_scored_request_worker_hot_proven": False,
        "hashes": EXPECTED,
    }


def main() -> int:
    report = audit()
    quality.write_json(OUT, report)
    print(json.dumps({"audit": str(OUT), "sample_count": len(report["sample_indices"]),
                      "scored_rows": report["scored_rows"],
                      "partial_rows_valid": report["partial_rows_valid"],
                      "full_paired_quality_decision": report["full_paired_quality_decision"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
