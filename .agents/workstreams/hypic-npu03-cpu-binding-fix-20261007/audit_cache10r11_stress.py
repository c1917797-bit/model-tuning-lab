#!/usr/bin/env python3
"""Independent, read-only terminal r11 stress gate; never a paired quality verdict."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from diagnose_partial_hotpath_coverage import diagnose
from hotpath_quality_audit import frozen_cases, payload_hash
from verify_hotpath_request_coverage import (
    CoverageError,
    audit_coverage,
    load_worker_namespace_pids,
    matching_internal_id,
    require,
)

ROOT = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "quality-context-41984-hotpath-cache10r11-stress-hypic"
)
PLUGIN_ROOT = "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008"
PLUGIN_COMMIT = "62b0d4a89234ffaa69855427e0c0dad0ba3e9e41"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MODEL_INDEX_SHA = "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b"
EVALUATOR_SHA = "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
DATASET_SHA = "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a"
INDEXES = (*range(75, 92), 107, 111)
DIAGNOSTIC_EVENTS = {
    "position_independent_prefill_filter_miss",
    "position_independent_prefill_plan_unavailable",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    try:
        cases, evaluator = frozen_cases()
        contract = read_json(ROOT / "contract.json")
        result = read_json(ROOT / "arm-result.json")
        start = read_json(ROOT / "hypic-only/service-start.json")
        stop = read_json(ROOT / "hypic-only/service-stop.json")
        guard = read_json(ROOT / "hypic-only/lane-guard.json")
        fp = contract["fingerprint"]
        require(contract.get("arm") == "hypic-only"
                and contract.get("mode") == "stress"
                and contract.get("sample_indexes") == list(INDEXES)
                and contract.get("repetitions") == 3
                and contract.get("concurrency") == 8
                and contract.get("warm_requests_per_sample") == 2
                and contract.get("max_output_tokens") == 2048
                and contract.get("temperature") == contract.get("seed") == 0
                and contract.get("ignore_eos") is False
                and contract.get("enable_thinking") is False
                and contract.get("evaluator_sha256") == EVALUATOR_SHA
                and contract.get("dataset_sha256") == DATASET_SHA,
                "r11 stress ruler drift")
        expected_identity = [{key: cases[index][key] for key in
                              ("index", "sample_id", "prompt_sha256",
                               "prompt_tokens", "boundary")}
                             for index in INDEXES]
        require(contract.get("sample_identity") == expected_identity,
                "r11 frozen sample identity drift")
        require(fp.get("source_commit") == PLUGIN_COMMIT
                and fp.get("plugin_source_root") == PLUGIN_ROOT
                and fp.get("image") == IMAGE
                and fp.get("model_index_sha256") == MODEL_INDEX_SHA
                and fp.get("evaluator_sha256") == EVALUATOR_SHA
                and fp.get("cpuset") == "112-191"
                and fp.get("physical_npus") == [0, 1, 2, 3]
                and fp.get("gpu_memory_utilization") == 0.85
                and fp.get("material_cache_max_mb") == 3584
                and fp.get("max_materialized_segments") == 10
                and fp.get("max_model_len") == 41984,
                "r11 source/device/cache fingerprint drift")
        controller_error = result.get("error")
        require(controller_error in {
                    None,
                    "RuntimeError: candidate scored boundary/hot coverage incomplete",
                }
                and result.get("completed_samples") == len(INDEXES)
                and result.get("scored_rows") == len(INDEXES) * 3
                and start.get("fingerprint") == fp,
                "r11 controller did not complete the frozen stress or has an unexpected error")
        require(start.get("container_id") == stop.get("container_id")
                == guard.get("owned_container_id")
                and stop.get("container_removed") is True
                and stop.get("owned_npus_released") is True
                and stop.get("port_released") is True
                and stop.get("lane_available") is True
                and not stop.get("foreign_npu_processes")
                and not stop.get("service_log_error")
                and guard.get("samples", 0) > 0
                and not guard.get("foreign")
                and not guard.get("probe_errors")
                and sorted(start["worker_pid_by_physical_npu"].values())
                    == guard.get("expected_worker_pids"),
                "r11 isolation or exact release unproven")
        require(result.get("service_stop_sha256") == sha256(ROOT / "hypic-only/service-stop.json")
                and result.get("lane_guard_sha256") == sha256(ROOT / "hypic-only/lane-guard.json"),
                "r11 terminal receipt hash drift")
        sample_paths = sorted((ROOT / "samples").glob("*.json"))
        require([p.name for p in sample_paths]
                == [f"{index:03d}.json" for index in INDEXES],
                "r11 sample set missing or extra")
        rows = [read_json(path) for path in sample_paths]
        all_ids: set[str] = set()
        scored_ids: list[str] = []
        correct = 0
        finishes: Counter[str] = Counter()
        for index, row in zip(INDEXES, rows):
            case = cases[index]
            require(row.get("index") == index
                    and row.get("arm") == "hypic-only"
                    and row.get("mode") == "stress"
                    and row.get("segment_ends") == [case["boundary"], case["prompt_tokens"]],
                    f"r11 sample {index} identity or segment drift")
            for key in ("sample_id", "reference", "prompt_sha256",
                        "prompt_tokens", "difficulty", "length"):
                require(row.get(key) == case[key],
                        f"r11 sample {index} {key} drift")
            require(len(row.get("warm", ())) == 2
                    and len(row.get("scores", ())) == 3,
                    f"r11 sample {index} request cardinality drift")
            for warm in row["warm"]:
                rid = warm.get("request_id")
                require(isinstance(rid, str) and rid not in all_ids
                        and warm.get("request_sha256") == payload_hash(case, 1)
                        and warm["usage"]["prompt_tokens"] == case["prompt_tokens"]
                        and 0 <= warm["usage"]["completion_tokens"] <= 1,
                        f"r11 sample {index} warm payload drift")
                all_ids.add(rid)
            for repetition, score in enumerate(row["scores"], 1):
                rid = score.get("request_id")
                response = score.get("response_text")
                require(score.get("repetition") == repetition
                        and isinstance(rid, str) and rid not in all_ids
                        and score.get("request_sha256") == payload_hash(case, 2048)
                        and score["usage"]["prompt_tokens"] == case["prompt_tokens"]
                        and 0 <= score["usage"]["completion_tokens"] <= 2048
                        and score.get("finish_reason") in {"stop", "length"}
                        and isinstance(response, str)
                        and score.get("response_sha256") == hashlib.sha256(response.encode()).hexdigest(),
                        f"r11 sample {index} scored payload/response drift")
                prediction, expected_correct = evaluator.score_case(
                    "longbenchv2", response, case["reference"]
                )
                require(score.get("prediction") == prediction
                        and score.get("correct") is bool(expected_correct),
                        f"r11 sample {index} scorer drift")
                all_ids.add(rid)
                scored_ids.append(rid)
                correct += bool(expected_correct)
                finishes[str(score.get("finish_reason"))] += 1
        require(len(all_ids) == len(INDEXES) * 5
                and len(scored_ids) == len(INDEXES) * 3,
                "r11 request uniqueness drift")
        evidence = ROOT / "hypic-only/hypic-evidence.jsonl"
        require(result.get("hypic_evidence_sha256") == sha256(evidence),
                "r11 evidence hash drift")
        events = [json.loads(line) for line in evidence.read_text().splitlines()
                  if line.strip()]
        workers = load_worker_namespace_pids(ROOT, start)
        diagnostic = diagnose(rows, events, workers)
        manifest = hashlib.sha256()
        for path in sample_paths:
            manifest.update(path.name.encode() + b"\0"
                            + sha256(path).encode() + b"\n")
        identity = {
            "schema": "hypic-r11-stress-audit/v1",
            "not_quality_verdict": True,
            "samples": len(rows),
            "scored_rows": len(scored_ids),
            "correct": correct,
            "finish_reasons": dict(finishes),
            "guard_samples": guard["samples"],
            "controller_error": controller_error,
            "contract_sha256": sha256(ROOT / "contract.json"),
            "arm_result_sha256": sha256(ROOT / "arm-result.json"),
            "evidence_sha256": sha256(evidence),
            "sample_manifest_sha256": manifest.hexdigest(),
            "service_stop_sha256": sha256(ROOT / "hypic-only/service-stop.json"),
            "lane_guard_sha256": sha256(ROOT / "hypic-only/lane-guard.json"),
        }
        if diagnostic["issue_count"]:
            print(json.dumps({**identity, "stress_pass": False,
                              "reason": "scored-request-hot-path-proof-missing",
                              "diagnostic": diagnostic}, sort_keys=True))
            return 2
        coverage = audit_coverage(scored_ids, events, workers)
        boundary_ids = {event.get("request_id") for event in events
                        if event.get("event") == "explicit_segment_boundary_active"}
        internal_ids = {matching_internal_id(rid, boundary_ids)
                        for rid in scored_ids}
        unexpected = [event for event in events
                      if event.get("event") in DIAGNOSTIC_EVENTS
                      and event.get("request_id") in internal_ids]
        require(not unexpected,
                "r11 scored request emitted a Prefill filter or plan-unavailable event")
        require(controller_error is None,
                "r11 controller reported failure despite positive request coverage")
        print(json.dumps({**identity,
            "stress_pass": True,
            "four_worker_verified_requests": coverage["four_worker_post_repair_verified_requests"],
        }, sort_keys=True))
        return 0
    except (CoverageError, OSError, ValueError, KeyError, TypeError,
            RuntimeError) as exc:
        print(json.dumps({"schema": "hypic-r11-stress-audit/v1",
                          "stress_pass": False, "not_quality_verdict": True,
                          "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
