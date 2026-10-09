#!/usr/bin/env python3
"""Independent r14 c1 subset audit; never replaces the frozen r13 verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from r14_variability_adapter import INDEXES, TOKENS, SOURCE_COMMIT, configure


# Configure the unchanged historical service source before importing its
# read-only audit helpers. This changes Python memory only, not old files.
controller = configure("no-cache")
quality = controller.quality
from analyze_r13_response_variability import bucket_summary  # noqa: E402
from hotpath_quality_audit import (  # noqa: E402
    frozen_cases, frozen_pair_seam, payload_hash, require,
)
from verify_hotpath_request_coverage import (  # noqa: E402
    audit_coverage, load_worker_namespace_pids,
)


BASE = quality.QROOT
CAND = quality.ROOT / "quality-context-41984-hotpath-cache10r14-variability-hypic"
OUT = quality.ROOT / "hotpath-quality-cache10r14-variability-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_arm(root: Path, arm: str, cases: list[dict], evaluator: object) -> dict:
    require(root.is_dir(), f"{arm}: r14 root absent")
    contract = load(root / "contract.json")
    result = load(root / "arm-result.json")
    start = load(root / arm / "service-start.json")
    stop = load(root / arm / "service-stop.json")
    guard = load(root / arm / "lane-guard.json")
    require(contract["arm"] == arm and contract["mode"] == "variability"
            and contract["sample_indexes"] == list(INDEXES)
            and contract["repetitions"] == 3 and contract["concurrency"] == 1
            and contract["warm_requests_per_sample"] == 2
            and contract["max_output_tokens"] == 2048
            and contract["temperature"] == contract["seed"] == 0
            and contract["ignore_eos"] is False
            and contract["enable_thinking"] is False,
            f"{arm}: r14 contract drift")
    require(contract["evaluator_sha256"] == quality.EVALUATOR_SHA
            and contract["dataset_sha256"] == quality.DATASETS["longbenchv2"][2]
            and contract["baseline_row_sha256"] == controller.BASELINE_SHA256,
            f"{arm}: frozen input drift")
    require(result["error"] is None and result["completed_samples"] == 3
            and result["scored_rows"] == 9 and result["contract"] == contract,
            f"{arm}: controller not fully valid")
    require(start["fingerprint"] == contract["fingerprint"],
            f"{arm}: service fingerprint drift")
    workers = start["worker_pid_by_physical_npu"]
    require(set(workers) == {"0", "1", "2", "3"}
            and len(set(workers.values())) == 4
            and sorted(workers.values()) == guard["expected_worker_pids"],
            f"{arm}: physical worker identity drift")
    require(guard["samples"] > 0 and not guard["foreign"]
            and not guard["probe_errors"], f"{arm}: isolation not clean")
    require(start["container_id"] == stop["container_id"]
            and stop["container_removed"] and stop["owned_npus_released"]
            and stop["port_released"] and stop["lane_available"]
            and not stop["foreign_npu_processes"]
            and not stop["service_log_error"],
            f"{arm}: exact owned release unproven")
    require(result["service_stop_sha256"] == quality.sha256(root / arm / "service-stop.json")
            and result["lane_guard_sha256"] == quality.sha256(root / arm / "lane-guard.json"),
            f"{arm}: release/guard hash drift")
    attestation_path = root / arm / f"source-attestation.{start['container_id'][:12]}.json"
    attestation = load(attestation_path)
    source_root = Path(contract["fingerprint"]["plugin_source_root"])
    source = quality.python_source_digest(source_root / "hypic_vllm_ascend")
    prior_root = quality.QROOT
    try:
        quality.QROOT = root
        _, expected_binds, _, expected_command = quality.spec(arm)
    finally:
        quality.QROOT = prior_root
    require(start.get("source_attestation_sha256") == quality.sha256(attestation_path)
            and load(root / arm / "source-attestation.json") == attestation
            and attestation.get("schema") == "hypic-serving-source-attestation/v1"
            and attestation.get("container_id") == start["container_id"]
            and attestation.get("image") == contract["fingerprint"]["image"]
            and attestation.get("selected_source_commit") == SOURCE_COMMIT
            and attestation.get("selected_source_root") == str(source_root)
            and attestation.get("container_import_file")
                == "/opt/hypic/hypic_vllm_ascend/__init__.py"
            and attestation.get("python_files") == source["python_files"]
            and attestation.get("python_tree_sha256") == source["python_tree_sha256"]
            and sorted(attestation.get("actual_binds", [])) == sorted(expected_binds)
            and attestation.get("actual_command") == ["bash", "-lc", expected_command],
            f"{arm}: source attestation drift")
    samples: dict[int, dict[int, dict]] = {}
    ids: set[str] = set()
    scored_ids: list[str] = []
    correct = 0
    for item in cases:
        index = item["index"]
        row = load(root / "samples" / f"{index:03d}.json")
        require(all(row[key] == item[key] for key in
                    ("index", "sample_id", "reference", "prompt_sha256",
                     "prompt_tokens", "difficulty", "length"))
                and row["arm"] == arm and row["mode"] == "variability"
                and row["segment_ends"] == [item["boundary"], item["prompt_tokens"]]
                and len(row["warm"]) == 2 and len(row["scores"]) == 3,
                f"{arm}: sample {index} identity drift")
        for warm in row["warm"]:
            require(warm["request_sha256"] == payload_hash(item, 1)
                    and warm["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= warm["usage"]["completion_tokens"] <= 1
                    and warm["request_id"] not in ids,
                    f"{arm}: sample {index} warm drift")
            ids.add(warm["request_id"])
        scores = {}
        for repetition, scored in enumerate(row["scores"], 1):
            response = scored["response_text"]
            prediction, is_correct = evaluator.score_case(
                "longbenchv2", response, item["reference"])
            require(scored["repetition"] == repetition
                    and scored["request_sha256"] == payload_hash(item, 2048)
                    and scored["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= scored["usage"]["completion_tokens"] <= 2048
                    and scored["response_sha256"]
                        == hashlib.sha256(response.encode()).hexdigest()
                    and scored["prediction"] == prediction
                    and scored["correct"] is bool(is_correct)
                    and scored["request_id"] not in ids,
                    f"{arm}: sample {index}:{repetition} score drift")
            ids.add(scored["request_id"])
            scored_ids.append(scored["request_id"])
            correct += bool(is_correct)
            scores[repetition] = scored
        samples[index] = scores
    require(len(list((root / "samples").glob("*.json"))) == 3
            and len(ids) == 15 and len(scored_ids) == 9,
            f"{arm}: request cardinality drift")
    evidence = root / arm / "hypic-evidence.jsonl"
    events = [json.loads(line) for line in evidence.read_text().splitlines() if line] if evidence.exists() else []
    if evidence.exists():
        require(result["hypic_evidence_sha256"] == quality.sha256(evidence),
                f"{arm}: evidence hash drift")
    if arm == "hypic-only":
        namespace_pids = load_worker_namespace_pids(root, start)
        coverage = audit_coverage(scored_ids, events, namespace_pids)
        require(coverage["four_worker_post_repair_verified_requests"] == 9,
                "r14 candidate strict hot coverage incomplete")
    else:
        require(not any(event.get("event") == "worker_hot_path" for event in events),
                "r14 baseline emitted HYPIC worker hot event")
        coverage = None
    return {
        "summary": {"root": str(root),
                    "contract_sha256": quality.sha256(root / "contract.json"),
                    "arm_result_sha256": quality.sha256(root / "arm-result.json"),
                    "source_attestation_sha256": quality.sha256(attestation_path),
                    "container_id": start["container_id"],
                    "guard_samples": guard["samples"], "scored_rows": 9,
                    "correct": correct, "request_hot_coverage": coverage},
        "fingerprint": contract["fingerprint"], "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true",
                        help="read-only terminal baseline admission before candidate")
    args = parser.parse_args()
    if not args.baseline_only:
        require(not OUT.exists(), "r14 audit output exists; never overwrite")
    all_cases, evaluator = frozen_cases()
    cases = [all_cases[index] for index in INDEXES]
    require(tuple(item["prompt_tokens"] for item in cases) == TOKENS,
            "r14 predeclared lengths drift")
    seam = frozen_pair_seam()
    baseline = audit_arm(BASE, "no-cache", cases, evaluator)
    if args.baseline_only:
        print(json.dumps({"schema": "hypic-cache10r14-baseline-admission/v1",
                          "valid": True, "scope": "baseline only; no quality decision",
                          "pair_seam": seam, "baseline": baseline["summary"]},
                         sort_keys=True))
        return 0
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator)
    require(baseline["fingerprint"] == candidate["fingerprint"],
            "r14 arms differ beyond HYPIC switch")
    fp = baseline["fingerprint"]
    require(fp.get("source_commit") == SOURCE_COMMIT
            and fp.get("physical_npus") == [0, 1, 2, 3]
            and fp.get("gpu_memory_utilization") == 0.85
            and fp.get("material_cache_max_mb") == 3584
            and fp.get("max_materialized_segments") == 10
            and fp.get("max_output_tokens") == 2048,
            "r14 source/device/cache fingerprint drift")
    within_base, within_cand, cross = [], [], []
    for index in INDEXES:
        left, right = baseline["samples"][index], candidate["samples"][index]
        for a, b in ((1, 2), (1, 3), (2, 3)):
            within_base.append((left[a], left[b]))
            within_cand.append((right[a], right[b]))
        for repetition in (1, 2, 3):
            require(left[repetition]["request_sha256"]
                    == right[repetition]["request_sha256"],
                    f"r14 paired request drift {index}:{repetition}")
            cross.append((left[repetition], right[repetition]))
    report = {
        "schema": "hypic-cache10r14-variability-diagnostic/v1",
        "evidence_valid": True,
        "scope": "three predeclared LongBench-v2 samples x3 each arm, c1, max2048; diagnostic only",
        "r13_quality_decision_unchanged": "REJECT_OR_QUALIFY",
        "sample_indexes": list(INDEXES), "prompt_tokens": list(TOKENS),
        "pair_seam": seam, "baseline": baseline["summary"],
        "candidate": candidate["summary"],
        "within_baseline": bucket_summary(within_base),
        "within_candidate": bucket_summary(within_cand),
        "cross_arm": bucket_summary(cross),
        "causal_root_proven": False,
    }
    quality.write_json(OUT, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
