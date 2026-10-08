#!/usr/bin/env python3
"""Fail-closed audit for a *revised*, user-approved exact-ID quality partition.

This does not turn the interrupted original candidate into a valid full arm.
It combines only independently verified pre-intrusion rows with three new,
clean, exact-ID services. Never call its result an original single-service
quality verdict.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["HYPIC_HOTPATH_AUDIT_CAMPAIGN"] = "cache10r2"
from audit_cache10r2_clean_set import (
    EXPECTED_IDS, OUT as CLEAN_RECEIPT, audit as audit_clean_set,
    sample_manifest,
)
from hotpath_quality_audit import (
    EXPECTED, REPEATS, audit_arm, decide, frozen_cases, frozen_pair_seam,
    load_json, quality, require,
)


CLEAN_RECEIPT_SHA = "99f2578adddd041f7a84fe441a1ac02b754b2c1a8217054e80e855b67e7f55bd"
ROOT = quality.ROOT
ORIGINAL = ROOT / "quality-context-41984-hotpath-cache10r2-full-hypic"
ROOTS = {
    ("no-cache", "0"): ROOT / "quality-context-41984-hotpath-cache10split-baseline-shard0",
    ("no-cache", "1"): ROOT / "quality-context-41984-hotpath-cache10split-baseline-shard1",
    ("hypic-only", "1"): ROOT / "quality-context-41984-hotpath-cache10split-hypic-shard1",
}
OUT = ROOT / "hotpath-quality-cache10split-independent-audit.json"


def sample_paths(root: Path, ids: tuple[int, ...]) -> list[Path]:
    return [root / "samples" / f"{index:03d}.json" for index in ids]


def request_ids(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        sample = load_json(path)
        rows = [*sample["warm"], *sample["scores"]]
        for row in rows:
            request_id = row["request_id"]
            require(isinstance(request_id, str) and request_id not in ids,
                    f"duplicate or invalid request ID in {path}")
            ids.add(request_id)
    require(len(ids) == len(paths) * 5, "warm/scored request cardinality drift")
    return ids


def original_partial(cases: list[dict]) -> dict:
    require(quality.sha256(CLEAN_RECEIPT) == CLEAN_RECEIPT_SHA,
            "clean-set receipt hash drift")
    receipt = audit_clean_set()
    require(receipt == load_json(CLEAN_RECEIPT)
            and tuple(receipt["sample_indices"]) == EXPECTED_IDS
            and receipt["partial_rows_valid"] is True
            and receipt["original_arm_valid"] is False,
            "original partial evidence changed or overclaimed")
    rows = []
    for item in cases:
        sample = load_json(ORIGINAL / "samples" / f"{item['index']:03d}.json")
        for score in sample["scores"]:
            rows.append({
                "index": item["index"], "repetition": score["repetition"],
                "request_id": score["request_id"], "correct": score["correct"],
                "prediction": score["prediction"],
                "finish_reason": score["finish_reason"],
                "completion_tokens": score["usage"]["completion_tokens"],
                "difficulty": item["difficulty"], "length": item["length"],
            })
    require(len(rows) == 56 * REPEATS, "original clean row count drift")
    contract = load_json(ORIGINAL / "contract.json")
    start = load_json(ORIGINAL / "hypic-only/service-start.json")
    return {
        "root": str(ORIGINAL), "rows": rows,
        "correct": receipt["correct"], "length_limit": receipt["length_limit"],
        "scored_rows": len(rows), "fingerprint": contract["fingerprint"],
        "container_id": start["container_id"],
        "sample_manifest_sha256": receipt["hashes"]["sample_manifest"],
        "receipt_sha256": CLEAN_RECEIPT_SHA,
        "original_arm_valid": False,
        "partial_rows_valid_before_first_foreign": True,
        "per_scored_request_worker_hot_proven": False,
    }


def split_arm(arm: str, shard: str, cases: list[dict], evaluator: object) -> dict:
    root = ROOTS[arm, shard]
    result = audit_arm(root, arm, cases, evaluator, expected=len(cases))
    contract = load_json(root / "contract.json")
    require(contract.get("split_shard") == shard
            and contract.get("clean_set_receipt_sha256") == CLEAN_RECEIPT_SHA
            and contract["sample_identity"] == [
                {key: item[key] for key in
                 ("index", "sample_id", "prompt_sha256", "prompt_tokens", "boundary")}
                for item in cases
            ], f"{arm}/{shard}: split contract identity drift")
    paths = sample_paths(root, tuple(item["index"] for item in cases))
    result["sample_manifest_sha256"] = sample_manifest(paths)
    result["service_start_sha256"] = quality.sha256(root / arm / "service-start.json")
    result["lane_guard_sha256"] = quality.sha256(root / arm / "lane-guard.json")
    result["service_stop_sha256"] = quality.sha256(root / arm / "service-stop.json")
    result["hypic_evidence_sha256"] = (
        quality.sha256(root / arm / "hypic-evidence.jsonl")
        if (root / arm / "hypic-evidence.jsonl").exists() else None
    )
    result["split_shard"] = shard
    return result


def combine(left: dict, right: dict) -> dict:
    rows = [*left["rows"], *right["rows"]]
    keys = [(row["index"], row["repetition"]) for row in rows]
    require(len(rows) == EXPECTED * REPEATS
            and len(set(keys)) == EXPECTED * REPEATS
            and set(keys) == {(i, r) for i in range(EXPECTED)
                              for r in range(1, REPEATS + 1)},
            "revised arm missing/duplicate scored unit")
    return {
        "rows": rows,
        "correct": sum(row["correct"] for row in rows),
        "length_limit": sum(row["finish_reason"] == "length" for row in rows),
        "fingerprint": left["fingerprint"],
        "container_id": (left["container_id"], right["container_id"]),
    }


def main() -> int:
    seam = frozen_pair_seam()
    cases, evaluator = frozen_cases()
    shard0_ids = set(EXPECTED_IDS)
    shard0 = [item for item in cases if item["index"] in shard0_ids]
    shard1 = [item for item in cases if item["index"] not in shard0_ids]
    require(len(shard0) == 56 and len(shard1) == 71
            and [item["index"] for item in shard0] == list(EXPECTED_IDS),
            "prospective partition drift")
    clean = original_partial(shard0)
    base0 = split_arm("no-cache", "0", shard0, evaluator)
    base1 = split_arm("no-cache", "1", shard1, evaluator)
    cand1 = split_arm("hypic-only", "1", shard1, evaluator)
    arms = (clean, base0, base1, cand1)
    fingerprint = clean["fingerprint"]
    require(all(arm["fingerprint"] == fingerprint for arm in arms)
            and fingerprint["physical_npus"] == [0, 1, 2, 3]
            and fingerprint["gpu_memory_utilization"] == 0.85
            and fingerprint["material_cache_max_mb"] == 3584
            and fingerprint["max_materialized_segments"] == 10,
            "four-service frozen identity mismatch")
    require(len({arm["container_id"] for arm in arms}) == 4,
            "service identity reused")
    all_paths = [
        *sample_paths(ORIGINAL, EXPECTED_IDS),
        *sample_paths(ROOTS["no-cache", "0"], EXPECTED_IDS),
        *sample_paths(ROOTS["no-cache", "1"], tuple(item["index"] for item in shard1)),
        *sample_paths(ROOTS["hypic-only", "1"], tuple(item["index"] for item in shard1)),
    ]
    all_ids = set()
    for path_group in (
        all_paths[:56], all_paths[56:112], all_paths[112:183],
        all_paths[183:],
    ):
        ids = request_ids(path_group)
        require(not (all_ids & ids), "request ID reused across services")
        all_ids |= ids
    require(len(all_ids) == EXPECTED * 2 * 5,
            "revised pair request cardinality drift")
    baseline = combine(base0, base1)
    candidate = combine(clean, cand1)
    decision = decide(baseline, candidate)
    report = {
        "schema": "hypic-hotpath-cache10split-quality-audit/v1",
        "method": "revised-multi-service-exact-id-partition",
        "revised_protocol_evidence_valid": True,
        "original_single_service_protocol_equivalent": False,
        "original_interrupted_candidate_arm_valid": False,
        "per_scored_request_worker_hot_proven": False,
        "frozen_pair_seam": seam,
        "four_service_fingerprint": fingerprint,
        "baseline": [dict((k, v) for k, v in arm.items() if k != "rows")
                     for arm in (base0, base1)],
        "candidate": [dict((k, v) for k, v in arm.items() if k != "rows")
                      for arm in (clean, cand1)],
        "request_ids": len(all_ids),
        "scored_rows_per_arm": EXPECTED * REPEATS,
        "score_rule": decision,
        "scope": "LongBench-v2 explicit-boundary c8, 2048 output cap, physical NPU0-3",
        "forbidden_claims": [
            "original single-service full quality pass",
            "per-scored-request worker-hot coverage",
            "GSM8K quality or universal losslessness",
        ],
    }
    quality.write_json(OUT, report)
    print(json.dumps({
        "audit": str(OUT), "method": report["method"],
        "score_rule": decision["decision"],
        "baseline_correct": baseline["correct"],
        "candidate_correct": candidate["correct"],
        "original_protocol_equivalent": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
