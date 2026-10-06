#!/usr/bin/env python3
"""Compare matched HYPIC TP4 profiles without treating them as formal A/B runs."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
ARMS = ("no-cache", "hypic-only")
PHASES = ("prefill", "decode")
ANALYZED_RANKS = (0, 1, 3)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unique_csv(arm: str, phase: str, rank: int, pattern: str) -> Path:
    root = ROOT / "profiles" / arm / phase / f"rank{rank}" / "msprof"
    files = list(root.glob(f"PROF_*/mindstudio_profiler_output/{pattern}"))
    if not files:
        raise RuntimeError(f"{arm}/{phase}/rank{rank}: {pattern} missing")
    if len(files) > 1 and len({sha256(path) for path in files}) != 1:
        raise RuntimeError(f"{arm}/{phase}/rank{rank}: conflicting duplicate {pattern}")
    return sorted(files)[-1]


def aggregate(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["OP Type"] == name]
    if len(rows) != 1:
        raise RuntimeError(f"{path}: expected one {name} row, found {len(rows)}")
    row = rows[0]
    return {"count": int(row["Count"]), "total_time_s": float(row["Total Time(us)"]) / 1e6,
            "csv_sha256": sha256(path)}


def late_decode_window(path: Path) -> dict:
    def rows():
        with path.open(encoding="utf-8", newline="") as stream:
            yield from csv.DictReader(stream)

    end = max(float(row["task_stop(us)"].strip()) for row in rows())
    start = end - 30_000_000
    sums = {"allreduce": 0.0, "event_wait": 0.0, "notify_wait": 0.0,
            "ai_core": 0.0, "ai_vector_core": 0.0, "mix_aic": 0.0}
    allreduce_count = 0
    for row in rows():
        task_end = float(row["task_stop(us)"].strip())
        if task_end <= start:
            continue
        task_start = float(row["task_start(us)"].strip())
        duration_s = max(0.0, task_end - max(task_start, start)) / 1e6
        kind = row["kernel_type"]
        if kind == "COMMUNICATION" and "all_reduce" in row["kernel_name"].lower():
            allreduce_count += 1
            sums["allreduce"] += duration_s
        elif kind == "EVENT_WAIT":
            sums["event_wait"] += duration_s
        elif kind == "NOTIFY_WAIT":
            sums["notify_wait"] += duration_s
        elif kind in ("AI_CORE", "AI_VECTOR_CORE", "MIX_AIC"):
            sums[kind.lower()] += duration_s
    return {"window_s": 30, "allreduce_tasks": allreduce_count,
            "decode_steps_lower_bound_if_129_collectives_per_step": allreduce_count // 129,
            "duration_s_by_task_type_overlapping": {key: round(value, 6) for key, value in sums.items()},
            "task_time_csv_sha256": sha256(path)}


def main() -> int:
    manifests = {}
    workloads = {}
    for arm in ARMS:
        for phase in PHASES:
            root = ROOT / "profiles" / arm / phase
            original = root / "profile-manifest.json"
            manifest = json.loads(original.read_text(encoding="utf-8"))
            if not manifest["stimulus"]["passed"] or len(manifest["profiler_results"]) != 4:
                raise RuntimeError(f"{arm}/{phase}: workload or four-rank raw capture failed")
            if any(row["exit_code"] != 0 for row in manifest["profiler_results"].values()):
                raise RuntimeError(f"{arm}/{phase}: at least one rank failed raw capture")
            rank_status = manifest["ranks"]
            if arm == "no-cache" and phase == "prefill":
                finalized = root / "profile-finalized.json"
                recovered = json.loads(finalized.read_text(encoding="utf-8"))
                if not recovered["passed"]:
                    raise RuntimeError("baseline Prefill offline recovery did not pass")
                rank_status = recovered["ranks"]
            if any(not rank_status[str(rank)]["complete"] for rank in ANALYZED_RANKS):
                raise RuntimeError(f"{arm}/{phase}: selected rank export incomplete")
            workload_path = root / "profile-workload.json"
            workload = json.loads(workload_path.read_text(encoding="utf-8"))
            expected_output = 1 if phase == "prefill" else 128
            if (workload["summary"]["successful"] != 4 or workload["summary"]["failed"] != 0
                    or not workload["summary"]["fixed_output_verified"]
                    or any(row["output_tokens"] != expected_output for row in workload["results"])):
                raise RuntimeError(f"{arm}/{phase}: fixed-output workload mismatch")
            manifests[(arm, phase)] = {"sha256": sha256(original), "full_four_rank_export":
                all(row["complete"] for row in rank_status.values()),
                "four_rank_raw_capture": True}
            workloads[(arm, phase)] = {"sha256": sha256(workload_path),
                "config": workload["config"], "ttft_p95_ms": workload["summary"]["ttft_p95_ms"],
                "duration_s": workload["summary"]["benchmark_duration_s"]}
    for phase in PHASES:
        if workloads[("no-cache", phase)]["config"] != workloads[("hypic-only", phase)]["config"]:
            raise RuntimeError(f"{phase}: profiled workload configuration drift")

    rank_evidence = {}
    for rank in ANALYZED_RANKS:
        arm_data = {}
        for arm in ARMS:
            phase_data = {}
            for phase in PHASES:
                comm = aggregate(unique_csv(arm, phase, rank, "communication_statistic_*.csv"),
                                 "hcom_allReduce_")
                matmul = aggregate(unique_csv(arm, phase, rank, "op_statistic_*.csv"),
                                   "MatMulV2") if phase == "decode" else None
                phase_data[phase] = {"allreduce": comm, "decode_matmul_v2": matmul}
            incremental_count = (phase_data["decode"]["allreduce"]["count"]
                                 - phase_data["prefill"]["allreduce"]["count"])
            if incremental_count != 129 * 127:
                raise RuntimeError(f"{arm}/rank{rank}: expected 129 collectives x 127 steps, got {incremental_count}")
            late = late_decode_window(unique_csv(arm, "decode", rank, "task_time_*.csv"))
            if late["decode_steps_lower_bound_if_129_collectives_per_step"] < 10:
                raise RuntimeError(f"{arm}/rank{rank}: fewer than ten late Decode steps")
            arm_data[arm] = {"phases": phase_data,
                "decode_incremental_allreduce_count": incremental_count,
                "decode_incremental_allreduce_total_time_s": round(
                    phase_data["decode"]["allreduce"]["total_time_s"]
                    - phase_data["prefill"]["allreduce"]["total_time_s"], 6),
                "last_30s": late}
        rank_evidence[str(rank)] = arm_data

    baseline = [rank_evidence[str(rank)]["no-cache"]["decode_incremental_allreduce_total_time_s"]
                for rank in ANALYZED_RANKS]
    treatment = [rank_evidence[str(rank)]["hypic-only"]["decode_incremental_allreduce_total_time_s"]
                 for rank in ANALYZED_RANKS]
    result = {"schema": "hypic-matched-native-profile-diagnostic/v1",
              "formal_performance_evidence": False, "analyzed_ranks": ANALYZED_RANKS,
              "rank2_status": "both arms raw-captured; baseline all-rank export timed out; treatment offline export deliberately omitted",
              "manifests": {f"{arm}/{phase}": item for (arm, phase), item in manifests.items()},
              "workloads": {f"{arm}/{phase}": item for (arm, phase), item in workloads.items()},
              "rank_evidence": rank_evidence,
              "median_incremental_allreduce_time_s": {"no-cache": statistics.median(baseline),
                  "hypic-only": statistics.median(treatment)},
              "interpretation_boundary": [
                  "One diagnostic profile per arm, with profiling overhead; not a formal performance gate.",
                  "Prefill-minus-Decode aggregate subtraction is directional, not a measured critical-path duration.",
                  "CANN AllReduce time can include synchronization wait; multi-stream task durations overlap and must not be summed into a removable wall-time estimate.",
                  "The trailing 30-second window contains at least ten Decode steps on all analyzed ranks, but request-tail and concurrent scheduling effects remain.",
              ]}
    output = ROOT / "profiles" / "profile-diagnostic.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "sha256": sha256(output),
                      "analyzed_ranks": ANALYZED_RANKS,
                      "median_incremental_allreduce_time_s": result["median_incremental_allreduce_time_s"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
