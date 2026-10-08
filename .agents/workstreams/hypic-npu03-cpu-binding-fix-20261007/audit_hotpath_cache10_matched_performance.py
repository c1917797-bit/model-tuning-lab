#!/usr/bin/env python3
"""Independently audit all six r13 matched performance phases from raw rows."""

from __future__ import annotations

import json
import math
import statistics
from datetime import datetime
from pathlib import Path

from binding_off_service import BENCHMARK, BENCHMARK_SHA, IMAGE, ROOT, sha256
from binding_off_quality import python_source_digest
from performance_request_coverage import diagnose_request_coverage
from verify_hotpath_request_coverage import load_worker_namespace_pids
from hotpath_cache10_matched_performance import (
    EXPECTED_CONFIG, ORDER, QUALITY_AUDIT, REQUEST_ID_BENCHMARK,
    REQUEST_ID_BENCHMARK_SHA, SOURCE_COMMIT, SOURCE_ROOT, require,
)


OUT = ROOT / "hotpath-cache10r13-matched-performance-audit.json"
METRICS = ("tpot_weighted_ms", "tpot_p95_ms", "ttft_p95_ms",
           "output_tokens_per_second", "benchmark_duration_s")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def close(actual: float, expected: float, label: str) -> None:
    require(math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6),
            f"{label}: raw/summary mismatch {actual} != {expected}")


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def root_for(arm: str, phase: str) -> Path:
    return ROOT / f"performance-context-41984-hotpath-cache10perf-{arm}-{phase}"


def normalized_spec(contract: dict, root: Path, arm: str) -> dict:
    prefix = f"/results/{root.name}/{arm}"
    command = contract["serving_command"].replace(prefix, "/results/ROOT/ARM")
    require(prefix not in command and "--gpu-memory-utilization 0.85" in command
            and "--max-model-len 41984" in command
            and "--additional-config '{\"enable_cpu_binding\":false}'" in command,
            "serving command identity drift")
    env = dict(entry.split("=", 1) for entry in contract["serving_env"])
    require(env.pop("VLLM_ASCEND_HYPIC_ENABLE") == ("1" if arm == "hypic-only" else "0"),
            "HYPIC enablement arm drift")
    require(env["VLLM_ASCEND_HYPIC_EVIDENCE_FILE"] ==
            f"{prefix}/hypic-evidence.jsonl", "evidence env path drift")
    env["VLLM_ASCEND_HYPIC_EVIDENCE_FILE"] = "/results/ROOT/ARM/hypic-evidence.jsonl"
    require(env.get("VLLM_ASCEND_HYPIC_MATERIAL_CACHE_MAX_MB") == "3584"
            and env.get("VLLM_ASCEND_HYPIC_MAX_MATERIALIZED_SEGMENTS") == "10"
            and env.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
            "cache/visible-device env drift")
    return {"command": command, "env": env,
            "binds": sorted(contract["serving_binds"])}


def audit_phase(arm: str, phase: str, quality_audit_sha: str) -> dict:
    root = root_for(arm, phase)
    require(root.is_dir(), f"{arm}/{phase}: root absent")
    contract = load(root / "contract.json")
    result = load(root / "arm-result.json")
    report = load(root / "performance.json")
    start = load(root / arm / "service-start.json")
    stop = load(root / arm / "service-stop.json")
    guard = load(root / arm / "lane-guard.json")
    command = load(root / "benchmark-command.json")
    attestation_path = root / arm / f"source-attestation.{start['container_id'][:12]}.json"
    attestation = load(attestation_path)
    source = python_source_digest(Path(SOURCE_ROOT) / "hypic_vllm_ascend")
    require(contract["schema"] == "hypic-cache10r13-matched-performance-contract/v1"
            and result["schema"] == "hypic-cache10r13-matched-performance-arm/v1"
            and contract["arm"] == arm and contract["phase"] == phase
            and contract["order_index"] == ORDER.index((arm, phase))
            and contract["quality_audit_sha256"] == quality_audit_sha
            and contract["benchmark_sha256"] == BENCHMARK_SHA
            and contract["request_id_adapter_sha256"] == REQUEST_ID_BENCHMARK_SHA
            and contract["benchmark_config"] == EXPECTED_CONFIG
            and contract["fingerprint"] == start["fingerprint"]
            and contract["fingerprint"]["image"] == IMAGE
            and contract["fingerprint"]["source_commit"] == SOURCE_COMMIT
            and contract["fingerprint"]["plugin_source_root"] == SOURCE_ROOT
            and contract["fingerprint"]["physical_npus"] == [0, 1, 2, 3]
            and contract["fingerprint"]["gpu_memory_utilization"] == 0.85
            and contract["fingerprint"]["material_cache_max_mb"] == 3584
            and contract["fingerprint"]["max_materialized_segments"] == 10,
            f"{arm}/{phase}: contract/service fingerprint drift")
    require(result["valid"] is True and result["error"] is None
            and result["arm"] == arm and result["phase"] == phase
            and result["container_id"] == start["container_id"] == stop["container_id"]
            and result["performance_sha256"] == sha256(root / "performance.json")
            and result["hypic_evidence_sha256"]
                == sha256(root / arm / "hypic-evidence.jsonl")
            and result["contract_sha256"] == sha256(root / "contract.json"),
            f"{arm}/{phase}: controller/hash drift")
    workers = start["worker_pid_by_physical_npu"]
    require(set(workers) == {"0", "1", "2", "3"}
            and len(set(workers.values())) == 4
            and sorted(workers.values()) == guard["expected_worker_pids"],
            f"{arm}/{phase}: physical worker identity drift")
    require(start["npu_smi_sha256"] == sha256(root / arm / "npu-smi-at-health.txt")
            and start["docker_top_sha256"] == sha256(root / arm / "docker-top-at-health.txt"),
            f"{arm}/{phase}: worker proof hashes drift")
    require(start.get("source_attestation_sha256") == sha256(attestation_path)
            and load(root / arm / "source-attestation.json") == attestation
            and attestation.get("schema") == "hypic-serving-source-attestation/v1"
            and attestation.get("container_id") == start["container_id"]
            and attestation.get("selected_source_commit") == SOURCE_COMMIT
            and attestation.get("selected_source_root") == SOURCE_ROOT
            and attestation.get("image") == IMAGE
            and attestation.get("container_import_file")
                == "/opt/hypic/hypic_vllm_ascend/__init__.py"
            and attestation.get("python_files") == source["python_files"]
            and attestation.get("python_tree_sha256") == source["python_tree_sha256"]
            and f"{SOURCE_ROOT}:/source-hypic:ro" in attestation.get("actual_binds", [])
            and f"{ROOT}:/results" in attestation.get("actual_binds", []),
            f"{arm}/{phase}: live source attestation drift")
    require(guard["samples"] > 0 and not guard["foreign"] and not guard["probe_errors"]
            and stop["container_removed"] is True
            and stop["owned_npus_released"] is True
            and stop["port_released"] is True
            and stop["lane_available"] is True
            and not stop["foreign_npu_processes"]
            and not stop["service_log_error"],
            f"{arm}/{phase}: isolation or exact release unproven")
    service_log = root / arm / f"service.full.{start['container_id'][:12]}.log"
    require(stop["service_log_sha256"] == sha256(service_log),
            f"{arm}/{phase}: service log hash drift")
    log = service_log.read_text(errors="replace")
    require("'enable_cpu_binding': False" in log
            and "The CPU allocation plan is as follows:" not in log,
            f"{arm}/{phase}: CPU binding-off activation drift")
    require(command["benchmark_sha256"] == BENCHMARK_SHA
            and command["request_id_adapter_sha256"] == REQUEST_ID_BENCHMARK_SHA
            and command["argv"][1] == str(REQUEST_ID_BENCHMARK)
            and command["argv"][0] == "python3"
            and ("--require-hot-path" in command["argv"]) == (arm == "hypic-only"),
            f"{arm}/{phase}: benchmark command drift")
    require(report["config"] == EXPECTED_CONFIG, f"{arm}/{phase}: workload drift")
    rows = report["results"]
    summary = report["summary"]
    warm = report["warmup_results"]
    require(len(rows) == 40 and sorted(row["index"] for row in rows) == list(range(40))
            and len(warm) == 2
            and all(row["ok"] is True and row["output_tokens"] == 1 for row in warm),
            f"{arm}/{phase}: measured/warmup cardinality drift")
    require(all(row["ok"] is True and row["error"] is None
                and row["output_tokens"] == row["requested_output_tokens"] == 1024
                and row["finish_reason"] == "length"
                and isinstance(row["output_sha256"], str)
                and len(row["output_sha256"]) == 64
                and isinstance(row["ttft_ms"], (int, float)) for row in rows),
            f"{arm}/{phase}: fixed-output raw row invalid")
    ids = [row.get("request_id") for row in rows + warm]
    require(all(isinstance(value, str) and value.startswith("cmpl-")
                for value in ids) and len(set(ids)) == 42,
            f"{arm}/{phase}: measured/warmup request IDs invalid")
    require(summary["successful"] == 40 and summary["failed"] == 0
            and summary["fixed_output_verified"] is True
            and summary["output_tokens"] == 40960
            and summary["finish_reasons"] == {"length": 40},
            f"{arm}/{phase}: summary validity drift")
    ttfts = [row["ttft_ms"] for row in rows]
    tpots = [(row["duration_s"] * 1000 - row["ttft_ms"]) / 1023 for row in rows]
    weighted = sum(row["duration_s"] * 1000 - row["ttft_ms"] for row in rows) / (40 * 1023)
    close(weighted, summary["tpot_weighted_ms"], "weighted TPOT")
    close(p95(tpots), summary["tpot_p95_ms"], "TPOT P95")
    close(p95(ttfts), summary["ttft_p95_ms"], "TTFT P95")
    close(40960 / summary["benchmark_duration_s"],
          summary["output_tokens_per_second"], "throughput")
    require(result["metrics"] == {key: summary[key] for key in METRICS},
            f"{arm}/{phase}: controller summary mismatch")
    coverage = None
    if arm == "hypic-only":
        require(summary["hot_path_verified"] is True
                and not summary["hot_path_missing"]
                and summary["run_evidence_event_counts"].get("worker_hot_path", 0) >= 4,
                f"{arm}/{phase}: measured hot path absent")
        workers = load_worker_namespace_pids(root, start)
        evidence = root / arm / "hypic-evidence.jsonl"
        events = [json.loads(line) for line in evidence.read_text(encoding="utf-8").splitlines()
                  if line.strip()]
        coverage = diagnose_request_coverage(rows, events, workers)
    else:
        require(summary["run_evidence_event_counts"].get("worker_hot_path", 0) == 0,
                f"{arm}/{phase}: baseline worker hot event")
    return {
        "root": str(root), "arm": arm, "phase": phase,
        "container_id": start["container_id"], "guard_samples": guard["samples"],
        "contract_sha256": sha256(root / "contract.json"),
        "performance_sha256": sha256(root / "performance.json"),
        "result_sha256": sha256(root / "arm-result.json"),
        "hypic_evidence_sha256": sha256(root / arm / "hypic-evidence.jsonl"),
        "request_coverage": coverage,
        "metrics": result["metrics"], "normalized_spec": normalized_spec(contract, root, arm),
        "created_at_utc": contract["created_at_utc"],
    }


def main() -> int:
    require(not OUT.exists(), "r13 performance audit exists; do not overwrite")
    require(sha256(BENCHMARK) == BENCHMARK_SHA, "benchmark source changed")
    require(sha256(REQUEST_ID_BENCHMARK) == REQUEST_ID_BENCHMARK_SHA,
            "request-ID adapter source changed")
    quality_path = ROOT / QUALITY_AUDIT
    quality = load(quality_path)
    require(quality["evidence_valid"] is True
            and quality["source_commit"] == SOURCE_COMMIT,
            "paired r13 quality evidence invalid")
    quality_sha = sha256(quality_path)
    phases = [audit_phase(arm, phase, quality_sha) for arm, phase in ORDER]
    require(len({item["container_id"] for item in phases}) == 6,
            "performance phases reused a service container")
    require(all(item["normalized_spec"] == phases[0]["normalized_spec"]
                for item in phases[1:]),
            "cross-phase serving identity differs beyond HYPIC switch/path")
    timestamps = [datetime.fromisoformat(item["created_at_utc"]) for item in phases]
    require(timestamps == sorted(timestamps), "preregistered phase order changed")
    per_arm = {arm: [item["metrics"] for item in phases if item["arm"] == arm]
               for arm in ("no-cache", "hypic-only")}
    medians = {arm: {key: statistics.median(row[key] for row in rows)
                     for key in METRICS} for arm, rows in per_arm.items()}
    base, cand = medians["no-cache"], medians["hypic-only"]
    effect = {
        "weighted_tpot_saved_ms": base["tpot_weighted_ms"] - cand["tpot_weighted_ms"],
        "weighted_tpot_saved_pct": 100 * (1 - cand["tpot_weighted_ms"] / base["tpot_weighted_ms"]),
        "ttft_p95_saved_s": (base["ttft_p95_ms"] - cand["ttft_p95_ms"]) / 1000,
        "throughput_ratio": cand["output_tokens_per_second"] / base["output_tokens_per_second"],
    }
    paired = [{key: per_arm["no-cache"][index][key] - per_arm["hypic-only"][index][key]
               for key in METRICS} for index in range(3)]
    hot_requests = sum(item["request_coverage"]["four_worker_verified_requests"]
                       for item in phases if item["arm"] == "hypic-only")
    require(0 <= hot_requests <= 120, "candidate measured hot count drift")
    all_hot = hot_requests == 120
    effect_screen = (effect["weighted_tpot_saved_ms"] >= 10
                     and effect["ttft_p95_saved_s"] >= 10)
    report = {
        "schema": "hypic-cache10r13-matched-performance-independent-audit/v1",
        "all_six_phases_valid": True,
        "deployed_quality_decision": quality["deployed_quality_decision"],
        "strict_quality_decision": quality["strict_quality_decision"],
        "performance_estimand": "all-request-deployed",
        "strict_c1_c2_hot_coverage": {
            "decision": "PASS" if all_hot else "FAIL",
            "four_worker_verified_measured_requests": hot_requests,
            "expected_measured_requests": 120,
        },
        "strict_c1_c2_performance_decision": (
            "EFFECT_SCREEN_PASS" if all_hot and effect_screen else
            "EFFECT_SCREEN_FAIL" if all_hot else "NOT_ACCEPTED_HOT_COVERAGE"
        ),
        "quality_audit_sha256": quality_sha,
        "phases": [{key: value for key, value in item.items()
                    if key != "normalized_spec"} for item in phases],
        "normalized_spec_identical": True, "per_arm": per_arm,
        "paired_baseline_minus_candidate": paired, "medians": medians, "effect": effect,
        "deployed_effect_screen_pass": effect_screen,
        "scope": "physical NPU0-3, TP4, source c12060c, 0.85/cache10, input32768/output1024/c16",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"audit": str(OUT), "all_six_phases_valid": True,
                      "deployed_effect_screen_pass": report["deployed_effect_screen_pass"],
                      "effect": effect}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
