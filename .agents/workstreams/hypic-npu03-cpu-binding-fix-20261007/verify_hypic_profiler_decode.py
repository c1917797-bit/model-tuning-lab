#!/usr/bin/env python3
"""Independently audit the immutable r6 Decode capture and parsed NPU traces."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


BASE = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
RAW = BASE / "profiler-hypic-hotcold-20261009-r6"
DECODE = RAW / "decode"
PARSED = BASE / "profiler-offline-parse-20261009-r6-decode"
COMPUTE_TYPES = {"AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV"}
REQUIRED_FIELDS = {
    "Stream ID", "Input Shapes", "Output Shapes", "aic_mac_ratio",
    "aic_mte2_ratio", "aiv_vec_ratio",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_us(value: str) -> float:
    instant = datetime.fromisoformat(value)
    require(instant.utcoffset() is not None, "profile time lacks timezone")
    return instant.timestamp() * 1_000_000


def kernel_window(events: list[dict], start_us: float, stop_us: float) -> dict:
    hardware_pids = {
        event.get("pid")
        for event in events
        if event.get("ph") == "M"
        and event.get("name") == "process_name"
        and (event.get("args") or {}).get("name") == "Ascend Hardware"
    }
    require(bool(hardware_pids), "Ascend Hardware process metadata absent")
    timestamps = sorted(
        float(event["ts"])
        for event in events
        if event.get("ph") == "X"
        and event.get("pid") in hardware_pids
        and (event.get("args") or {}).get("Task Type") in COMPUTE_TYPES
        and start_us <= float(event["ts"]) <= stop_us
    )
    span_us = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
    return {
        "compute_kernel_count": len(timestamps),
        "compute_span_s": span_us / 1_000_000,
        "first_kernel_utc_us": timestamps[0] if timestamps else None,
        "last_kernel_utc_us": timestamps[-1] if timestamps else None,
    }


def csv_shape(path: Path) -> tuple[list[str], int]:
    with path.open(newline="", errors="replace") as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return header, rows


def main() -> int:
    contract = read_json(DECODE / "contract.json")
    result = read_json(DECODE / "result.json")
    capture = read_json(DECODE / "capture.json")
    artifact = read_json(DECODE / "artifact-audit.json")
    release = read_json(DECODE / "release.json")
    guard = read_json(RAW / "hypic-only-decode" / "lane-guard.json")
    require(contract["phase"] == result["phase"] == "decode", "wrong capture phase")
    require(contract["physical_npus"] == [0, 1, 2, 3] and
            contract["port"] == 8223 and
            contract["source_commit"] == "c12060cd47e7575ead059983d7a8bb4704165c98",
            "capture identity mismatch")
    require(result["contract_sha256"] == sha256(DECODE / "contract.json"),
            "contract drift")
    require(result["valid"] is True and not result["errors"], "device capture invalid")
    require(result["capture"] == capture and result["release"] == release,
            "result receipt mismatch")
    require(all(release.get(key) is True for key in
                ("container_removed", "owned_workers_released", "port_released")),
            "exact owned resource release incomplete")
    require(guard["samples"] > 0 and not guard["foreign"] and
            not guard["probe_errors"], "physical NPU isolation invalid")
    workers = capture["worker_pid_by_physical_npu"]
    require(set(workers) == {"0", "1", "2", "3"} and
            len(set(workers.values())) == 4, "four-worker physical mapping absent")
    require(len(capture["warmups"]) == 2 and
            all(item["output_tokens"] == 32 for item in capture["warmups"]),
            "warmup incomplete")
    stimulus = capture["capture"]
    require(stimulus["prefill_outside_window"] is True and
            stimulus["output_tokens"] == 512 and
            stimulus["chunks_after_start"] >= 64 and
            stimulus["error"] is None, "Decode stimulus incomplete")
    start_us = utc_us(stimulus["profile_start_utc"])
    stop_us = utc_us(stimulus["profile_stop_utc"])
    require(start_us < stop_us, "profile capture interval invalid")
    inventory = artifact["inventory"]
    require(artifact["nonempty_files"] == len(inventory) and
            len(inventory) > 0, "raw artifact inventory incomplete")
    for item in inventory:
        path = DECODE / item["path"]
        require(path.is_file() and path.stat().st_size == item["size"] and
                sha256(path) == item["sha256"], f"raw artifact drift: {item['path']}")

    rank_dirs = sorted(PARSED.glob("rank*_ascend_pt"))
    require(len(rank_dirs) == 4, "parsed rank count invalid")
    ranks = []
    for rank, directory in enumerate(rank_dirs):
        require(directory.name == f"rank{rank}_ascend_pt", "parsed rank identity drift")
        info = read_json(directory / f"profiler_info_{rank}.json")
        config = info["config"]
        experiment = config["experimental_config"]
        require(info["rank_id"] == rank and
                info["torch_npu_version"] == "2.10.0.post4" and
                info["cann_version"] == "9.1.0", "profiler stack identity drift")
        require(set(config["common_config"]["activities"]) ==
                {"ProfilerActivity.CPU", "ProfilerActivity.NPU"} and
                experiment["_profiler_level"] == "Level1" and
                experiment["_aic_metrics"] == "ACL_AICORE_PIPE_UTILIZATION",
                "detailed profiler configuration absent")
        output = directory / "ASCEND_PROFILER_OUTPUT"
        header, rows = csv_shape(output / "kernel_details.csv")
        require(REQUIRED_FIELDS <= set(header) and rows > 0,
                f"detailed kernel evidence absent on rank {rank}")
        for name in ("op_statistic.csv", "api_statistic.csv",
                     "operator_details.csv", "step_trace_time.csv"):
            require(csv_shape(output / name)[1] > 0,
                    f"{name} empty on rank {rank}")
        event_summary = kernel_window(
            read_json(output / "trace_view.json"), start_us, stop_us)
        require(event_summary["compute_kernel_count"] >= 64 and
                event_summary["compute_span_s"] >= 1.0,
                f"steady NPU Decode kernel proof absent on rank {rank}")
        ranks.append({"rank": rank, "kernel_rows": rows,
                      "kernel_columns": len(header), **event_summary})

    print(json.dumps({
        "schema": "hypic-profiler-decode-audit/v1",
        "capture_valid": True,
        "four_rank_steady_decode_proven": True,
        "numeric_prefill_min_47_retrospective_met": False,
        "capture_interval_utc": [stimulus["profile_start_utc"],
                                 stimulus["profile_stop_utc"]],
        "control_sha256": {
            name: sha256(DECODE / name)
            for name in ("contract.json", "capture.json", "artifact-audit.json",
                         "result.json", "release.json")
        },
        "guard_sha256": sha256(RAW / "hypic-only-decode" / "lane-guard.json"),
        "ranks": ranks,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
