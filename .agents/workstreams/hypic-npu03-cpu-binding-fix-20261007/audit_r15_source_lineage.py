#!/usr/bin/env python3
"""Independent bounded r15 source-lineage audit; never reclassifies r13."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from r15_source_lineage_adapter import INDEXES, SOURCES, TOKENS, configure


controller = configure("original")
quality = controller.quality
from hotpath_quality_audit import frozen_cases, payload_hash, require  # noqa: E402


ROOTS = {
    source: quality.ROOT / f"quality-context-41984-hotpath-cache10r15-source-{source}"
    for source in SOURCES
}
OUT = quality.ROOT / "hypic-r15-source-lineage-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_arm(source: str, cases: list[dict], evaluator: object) -> dict:
    root = ROOTS[source]
    source_root, source_commit = SOURCES[source]
    require(root.is_dir(), f"{source}: root absent")
    contract = load(root / "contract.json")
    result = load(root / "arm-result.json")
    start = load(root / "hypic-only" / "service-start.json")
    stop_path = root / "hypic-only" / "service-stop.json"
    guard_path = root / "hypic-only" / "lane-guard.json"
    stop, guard = load(stop_path), load(guard_path)
    fp = contract["fingerprint"]
    require(contract["arm"] == "hypic-only"
            and contract["mode"] == "source-lineage"
            and contract["sample_indexes"] == list(INDEXES)
            and contract["repetitions"] == 3
            and contract["concurrency"] == 8
            and contract["warm_requests_per_sample"] == 2
            and contract["max_output_tokens"] == 2048
            and contract["temperature"] == contract["seed"] == 0
            and contract["ignore_eos"] is False
            and contract["enable_thinking"] is False
            and contract["dataset_sha256"] == quality.DATASETS["longbenchv2"][2]
            and contract["evaluator_sha256"] == quality.EVALUATOR_SHA
            and contract["baseline_row_sha256"] == controller.BASELINE_SHA256,
            f"{source}: frozen request contract drift")
    require(fp["source_commit"] == source_commit
            and fp["plugin_source_root"] == source_root
            and fp["physical_npus"] == [0, 1, 2, 3]
            and fp["image"] == quality.IMAGE
            and fp["gpu_memory_utilization"] == 0.85
            and fp["material_cache_max_mb"] == 3584
            and fp["max_materialized_segments"] == 10,
            f"{source}: source/service fingerprint drift")
    require(result["contract"] == contract
            and result["completed_samples"] == len(INDEXES)
            and result["scored_rows"] == 3 * len(INDEXES)
            and result["error"] in (
                None, "RuntimeError: candidate scored boundary/hot coverage incomplete"),
            f"{source}: incomplete controller or unexpected error")
    require(start["fingerprint"] == fp, f"{source}: service identity drift")
    workers = start["worker_pid_by_physical_npu"]
    require(set(workers) == {"0", "1", "2", "3"}
            and len(set(workers.values())) == 4
            and sorted(workers.values()) == guard["expected_worker_pids"],
            f"{source}: physical worker map drift")
    require(guard["samples"] > 0 and not guard["foreign"]
            and not guard["probe_errors"],
            f"{source}: continuous isolation unproven")
    require(start["container_id"] == stop["container_id"]
            and stop["container_removed"]
            and stop["owned_npus_released"]
            and stop["port_released"]
            and not stop["foreign_npu_processes"]
            and not stop["service_log_error"],
            f"{source}: exact owned release unproven")
    require(result["service_stop_sha256"] == quality.sha256(stop_path)
            and result["lane_guard_sha256"] == quality.sha256(guard_path),
            f"{source}: guard/release hashes drift")

    att_path = root / "hypic-only" / (
        f"source-attestation.{start['container_id'][:12]}.json")
    att = load(att_path)
    source_tree = quality.python_source_digest(Path(source_root) / "hypic_vllm_ascend")
    old_env = (os.environ.get("HYPIC_QUALITY_PLUGIN_REPO"),
               os.environ.get("HYPIC_QUALITY_PLUGIN_COMMIT"))
    old_qroot = quality.QROOT
    try:
        os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = source_root
        os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = source_commit
        quality.QROOT = root
        _, expected_binds, _, expected_command = quality.spec("hypic-only")
    finally:
        quality.QROOT = old_qroot
        for key, value in zip(("HYPIC_QUALITY_PLUGIN_REPO",
                               "HYPIC_QUALITY_PLUGIN_COMMIT"), old_env):
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    require(start["source_attestation_sha256"] == quality.sha256(att_path)
            and load(root / "hypic-only" / "source-attestation.json") == att
            and att["container_id"] == start["container_id"]
            and att["selected_source_commit"] == source_commit
            and att["selected_source_root"] == source_root
            and att["python_files"] == source_tree["python_files"]
            and att["python_tree_sha256"] == source_tree["python_tree_sha256"]
            and sorted(att["actual_binds"]) == sorted(expected_binds)
            and att["actual_command"] == ["bash", "-lc", expected_command],
            f"{source}: live source attestation drift")

    rows: dict[int, list[dict]] = {}
    request_ids: set[str] = set()
    score_count = 0
    length_count = 0
    for item in cases:
        index = item["index"]
        row = load(root / "samples" / f"{index:03d}.json")
        require(all(row[key] == item[key] for key in
                    ("index", "sample_id", "reference", "prompt_sha256",
                     "prompt_tokens", "difficulty", "length"))
                and row["segment_ends"] == [item["boundary"], item["prompt_tokens"]]
                and len(row["warm"]) == 2 and len(row["scores"]) == 3,
                f"{source}: sample {index} identity drift")
        for warm in row["warm"]:
            require(warm["request_sha256"] == payload_hash(item, 1)
                    and warm["request_id"] not in request_ids,
                    f"{source}: warm request drift {index}")
            request_ids.add(warm["request_id"])
        for repetition, scored in enumerate(row["scores"], 1):
            response = scored["response_text"]
            prediction, correct = evaluator.score_case(
                "longbenchv2", response, item["reference"])
            require(scored["repetition"] == repetition
                    and scored["request_sha256"] == payload_hash(item, 2048)
                    and scored["response_sha256"]
                        == hashlib.sha256(response.encode()).hexdigest()
                    and scored["prediction"] == prediction
                    and scored["correct"] is bool(correct)
                    and scored["request_id"] not in request_ids
                    and scored["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= scored["usage"]["completion_tokens"] <= 2048,
                    f"{source}: scored response drift {index}:{repetition}")
            request_ids.add(scored["request_id"])
            score_count += bool(correct)
            length_count += scored["finish_reason"] == "length"
        rows[index] = row["scores"]
    require(len(list((root / "samples").glob("*.json"))) == len(INDEXES)
            and len(request_ids) == len(INDEXES) * 5,
            f"{source}: request cardinality drift")
    evidence = root / "hypic-only" / "hypic-evidence.jsonl"
    require(evidence.exists()
            and result["hypic_evidence_sha256"] == quality.sha256(evidence),
            f"{source}: mechanism evidence hash drift")
    return {
        "fingerprint": fp, "rows": rows,
        "summary": {
            "source_commit": source_commit, "root": str(root),
            "contract_sha256": quality.sha256(root / "contract.json"),
            "arm_result_sha256": quality.sha256(root / "arm-result.json"),
            "source_attestation_sha256": quality.sha256(att_path),
            "guard_samples": guard["samples"], "scored_rows": len(INDEXES) * 3,
            "correct": score_count, "length_finishes": length_count,
            "controller_error": result["error"],
            "aggregate_verified_hot_requests":
                result.get("events", {}).get("verified_hot_requests"),
            "request_level_proof":
                "not available in original source" if source == "original"
                else "requires separate request-ID join",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-only", action="store_true")
    args = parser.parse_args()
    all_cases, evaluator = frozen_cases()
    cases = [all_cases[index] for index in INDEXES]
    require(tuple(item["prompt_tokens"] for item in cases) == TOKENS,
            "predeclared sample lengths drift")
    original = audit_arm("original", cases, evaluator)
    if args.original_only:
        print(json.dumps({"valid": True, "scope": "original arm only",
                          "original": original["summary"]}, sort_keys=True))
        return 0
    require(not OUT.exists(), "r15 audit output exists; never overwrite")
    current = audit_arm("current", cases, evaluator)
    first = dict(original["fingerprint"])
    second = dict(current["fingerprint"])
    for field in ("source_commit", "plugin_source_root"):
        first.pop(field)
        second.pop(field)
    require(first == second, "arms differ beyond declared plugin source")
    paired = []
    for index in INDEXES:
        left, right = original["rows"][index], current["rows"][index]
        require(all(a["request_sha256"] == b["request_sha256"]
                    for a, b in zip(left, right)),
                f"paired request bytes differ at sample {index}")
        paired.append({
            "index": index,
            "original_correct": sum(bool(row["correct"]) for row in left),
            "current_correct": sum(bool(row["correct"]) for row in right),
            "original_length": sum(row["finish_reason"] == "length" for row in left),
            "current_length": sum(row["finish_reason"] == "length" for row in right),
        })
    report = {
        "schema": "hypic-r15-source-lineage-diagnostic/v1",
        "evidence_valid": True, "diagnostic_only": True,
        "r13_quality_decision_unchanged": "REJECT_OR_QUALIFY",
        "sample_indexes": list(INDEXES),
        "original": original["summary"], "current": current["summary"],
        "paired_samples": paired, "causal_root_proven": False,
    }
    quality.write_json(OUT, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
