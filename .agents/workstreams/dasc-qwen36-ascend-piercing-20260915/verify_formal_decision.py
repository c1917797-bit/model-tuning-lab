#!/usr/bin/env python3
"""Independent fail-closed decision logic for normalized DASC v13 evidence."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import statistics
from pathlib import Path


PERF_CONFIG = {
    "input_tokens": 32768,
    "prefix_tokens": 16384,
    "output_tokens": 1024,
    "requests": 40,
    "concurrency": 16,
    "warmup_requests": 2,
    "warmup_mode": "concurrent_materialization_gate",
    "ignore_eos": True,
    "segment_boundary_transport": "vllm_xargs.hypic_segment_ends",
    "segment_ends": [16384, 32768],
}
QUALITY_REQUESTS = {"longbenchv2": 127, "gsm8k": 1319}
FIXED_IDENTITY = {
    "physical_npus": [4, 5, 6, 7],
    "host_to_container_devices": ["4:0", "5:1", "6:2", "7:3"],
    "tensor_parallel_size": 4,
    "communication": "HCCL",
    "max_model_len": 44032,
    "max_num_seqs": 32,
    "block_size": 128,
    "kv_cache_memory_bytes_per_rank": 9663676416,
}
EXPECTED_CONTAINERS = {
    "dense": "dasc_qwen36_formal_v13_dense_20260916",
    "candidate": "dasc_qwen36_formal_v13_candidate_20260916",
}


def metric_sum(snapshot: dict, needle: str) -> float:
    return sum(float(value) for name, value in snapshot.items() if needle in name)


def cache_hit_delta(record: dict) -> float:
    return metric_sum(record["metrics_after"], "prefix_cache_hits_total") - metric_sum(
        record["metrics_before"], "prefix_cache_hits_total"
    )


def verify_identity(payload: dict) -> dict:
    dense_arm = payload["arms"]["dense"]
    candidate_arm = payload["arms"]["candidate"]
    dense = dense_arm["identity"]
    candidate = candidate_arm["identity"]
    ignored = {"dasc_plugin", "mode", "w_max"}
    dense_fixed = {key: value for key, value in dense.items() if key not in ignored}
    candidate_fixed = {
        key: value for key, value in candidate.items() if key not in ignored
    }
    return {
        "fixed_fields_equal": dense_fixed == candidate_fixed,
        "required_runtime_identity": all(
            dense.get(key) == value and candidate.get(key) == value
            for key, value in FIXED_IDENTITY.items()
        ),
        "dense_treatment": dense.get("dasc_plugin") is False
        and dense.get("mode") is None
        and dense.get("w_max") is None,
        "candidate_treatment": candidate.get("dasc_plugin") is True
        and candidate.get("mode") == "physical-cache-eager"
        and candidate.get("w_max") == 64,
        "runtime_manifest_hash_bound": dense.get("runtime_manifest_sha256")
        == dense_arm.get("runtime_manifest_sha256")
        and candidate.get("runtime_manifest_sha256")
        == candidate_arm.get("runtime_manifest_sha256"),
        "runtime_manifests_equal": dense_arm.get("runtime_manifest")
        == candidate_arm.get("runtime_manifest"),
    }


def verify_candidate_activation(payload: dict) -> dict:
    activation = payload.get("candidate_activation", {})
    physical = activation.get("physical_cache_pids")
    geometry = activation.get("tp_geometry_pids")
    dispatch = activation.get("worker_dispatch_pids")
    return {
        "reported_ok": activation.get("ok") is True,
        "four_workers": isinstance(physical, list) and len(physical) == 4,
        "worker_cohort_aligned": physical == geometry == dispatch,
        "compact_lt_dense": activation.get("compact_lt_dense") is True,
        "positive_blocks": activation.get("positive_blocks") is True,
        "heterogeneous_cache_grouped": activation.get("heterogeneous_cache_grouped")
        is True,
    }


def verify_device_ownership_history(rows: object, arm: str) -> dict:
    samples = rows if isinstance(rows, list) else []
    def timestamp_valid(row: object) -> bool:
        if not isinstance(row, dict):
            return False
        try:
            parsed = datetime.fromisoformat(row["observed_at_utc"])
        except (KeyError, TypeError, ValueError):
            return False
        return parsed.utcoffset() is not None

    return {
        "history_nonempty": bool(samples),
        "all_samples_objects": all(isinstance(row, dict) for row in samples),
        "timestamps_valid": bool(samples) and all(timestamp_valid(row) for row in samples),
        "physical_npus_fixed": bool(samples)
        and all(
            isinstance(row, dict)
            and row.get("physical_npus") == [4, 5, 6, 7]
            for row in samples
        ),
        "container_fixed": bool(samples)
        and all(
            isinstance(row, dict)
            and row.get("container") == EXPECTED_CONTAINERS[arm]
            for row in samples
        ),
        "owned_process_set_nonempty": bool(samples)
        and all(
            isinstance(row, dict)
            and isinstance(row.get("owned_pids"), list)
            and bool(row["owned_pids"])
            for row in samples
        ),
        "no_foreign_processes": bool(samples)
        and all(
            isinstance(row, dict)
            and row.get("ok") is True
            and row.get("foreign_pids") == []
            for row in samples
        ),
        "observations_owned": bool(samples)
        and all(
            isinstance(row, dict)
            and isinstance(row.get("observed_device_pids"), list)
            and isinstance(row.get("owned_pids"), list)
            and set(row["observed_device_pids"]) <= set(row["owned_pids"])
            for row in samples
        ),
        "npu_workers_observed": any(
            isinstance(row, dict) and bool(row.get("observed_device_pids"))
            for row in samples
        ),
    }


def verify_performance_run(run: dict) -> dict:
    report = run["report"]
    config = report["config"]
    summary = report["summary"]
    rows = report["results"]
    indices = sorted(row.get("index") for row in rows)
    return {
        "config": all(config.get(key) == value for key, value in PERF_CONFIG.items()),
        "row_count": len(rows) == 40,
        "unique_complete_indices": indices == list(range(40)),
        "all_rows_ok": all(row.get("ok") is True for row in rows),
        "fixed_outputs": all(
            row.get("output_tokens") == 1024
            and row.get("requested_output_tokens") == 1024
            for row in rows
        ),
        "summary_complete": summary.get("successful") == 40
        and summary.get("failed") == 0
        and summary.get("fixed_output_verified") is True,
        "positive_cache_hit_delta": cache_hit_delta(run) > 0,
        "metrics_present": all(
            key in summary
            for key in (
                "ttft_mean_ms",
                "ttft_p95_ms",
                "tpot_mean_ms",
                "tpot_p95_ms",
                "benchmark_duration_s",
            )
        ),
    }


def verify_quality_run(run: dict, dataset: str) -> dict:
    summary = run["summary"]
    rows = run["details"]
    expected = QUALITY_REQUESTS[dataset]
    indices = sorted(row.get("index") for row in rows)
    correct = sum(row.get("correct") is True for row in rows)
    accuracy = 100.0 * correct / expected
    return {
        "schema": summary.get("schema") == "mst.dasc.cache-hit-quality/v1",
        "dataset": summary.get("dataset") == dataset,
        "row_count": len(rows) == expected,
        "unique_complete_indices": indices == list(range(expected)),
        "all_rows_ok": all(row.get("ok") is True for row in rows),
        "summary_complete": summary.get("requests") == expected
        and summary.get("successful") == expected
        and summary.get("failed") == 0,
        "accuracy_recomputed": abs(float(summary["accuracy_pct"]) - accuracy) < 1e-12,
        "cache_hit_recomputed": cache_hit_delta(summary) > 0
        and float(summary.get("prefix_cache_hit_delta", 0)) == cache_hit_delta(summary),
        "cache_hit_required": summary.get("adapter_require_cache_hit") is True
        and summary.get("cache_hit_verified") is True,
    }


def evaluate(payload: dict) -> dict:
    if payload.get("schema") != "dasc-formal-v13-normalized/v1":
        raise ValueError("unexpected normalized evidence schema")
    identities = verify_identity(payload)
    activation = verify_candidate_activation(payload)
    capacity = payload.get("cache_capacity", {})
    device_ownership_checks = {
        arm: verify_device_ownership_history(
            payload["arms"][arm].get("device_ownership_history"), arm
        )
        for arm in ("dense", "candidate")
    }
    performance_checks = {}
    performance_values = {}
    quality_checks = {}
    quality_values = {}

    for arm in ("dense", "candidate"):
        performance = payload["arms"][arm]["performance"]
        if len(performance) != 3 or len({run["run_id"] for run in performance}) != 3:
            raise ValueError(f"{arm} must contain three unique performance runs")
        performance_checks[arm] = [verify_performance_run(run) for run in performance]
        performance_values[arm] = {
            run["run_id"]: {
                "ttft_mean_ms": float(run["report"]["summary"]["ttft_mean_ms"]),
                "input_tokens_per_second": (
                    40 * 32768 / float(run["report"]["summary"]["benchmark_duration_s"])
                ),
            }
            for run in performance
        }
        quality_checks[arm] = {}
        quality_values[arm] = {}
        for dataset, expected in QUALITY_REQUESTS.items():
            runs = payload["arms"][arm]["quality"][dataset]
            if len(runs) != 3 or len({run["run_id"] for run in runs}) != 3:
                raise ValueError(f"{arm}/{dataset} must contain three unique quality runs")
            quality_checks[arm][dataset] = [
                verify_quality_run(run, dataset) for run in runs
            ]
            quality_values[arm][dataset] = {
                run["run_id"]: float(run["summary"]["accuracy_pct"]) for run in runs
            }

    perf_ids = set(performance_values["dense"])
    paired_performance = perf_ids == set(performance_values["candidate"])
    performance_direction = paired_performance and all(
        performance_values["candidate"][run_id]["ttft_mean_ms"]
        < performance_values["dense"][run_id]["ttft_mean_ms"]
        and performance_values["candidate"][run_id]["input_tokens_per_second"]
        > performance_values["dense"][run_id]["input_tokens_per_second"]
        for run_id in perf_ids
    )

    quality_gates = {}
    for dataset in QUALITY_REQUESTS:
        dense_values = list(quality_values["dense"][dataset].values())
        candidate_values = list(quality_values["candidate"][dataset].values())
        tolerance = max(1.0, max(dense_values) - min(dense_values))
        loss = statistics.median(dense_values) - statistics.median(candidate_values)
        quality_gates[dataset] = {
            "dense_range_pct_points": max(dense_values) - min(dense_values),
            "allowed_loss_pct_points": tolerance,
            "median_loss_pct_points": loss,
            "pass": loss <= tolerance,
        }

    all_run_checks = all(
        all(all(check.values()) for check in performance_checks[arm])
        and all(
            all(all(check.values()) for check in quality_checks[arm][dataset])
            for dataset in QUALITY_REQUESTS
        )
        for arm in ("dense", "candidate")
    )
    checks = {
        "identity": all(identities.values()),
        "candidate_activation": all(activation.values()),
        "cache_capacity": capacity.get("ok") is True
        and all(capacity.get("checks", {}).values()),
        "device_ownership": all(
            all(values.values()) for values in device_ownership_checks.values()
        ),
        "all_raw_runs_valid": all_run_checks,
        "performance_runs_paired": paired_performance,
        "performance_direction_every_run": performance_direction,
        "quality": all(value["pass"] for value in quality_gates.values()),
    }
    return {
        "schema": "dasc-formal-v13-decision/v1",
        "identity_checks": identities,
        "candidate_activation_checks": activation,
        "cache_capacity": capacity,
        "device_ownership_checks": device_ownership_checks,
        "performance_checks": performance_checks,
        "quality_checks": quality_checks,
        "quality_gates": quality_gates,
        "checks": checks,
        "decision": "accept" if all(checks.values()) else "reject",
        "ok": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
