#!/usr/bin/env python3
"""Replay the immutable NPU Prefill capture and offline parser audit."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


BASE = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
RAW = BASE / "profiler-hypic-hotcold-20261009-r2"
PREFILL = RAW / "prefill"
PARSED = BASE / "profiler-offline-parse-20261009-r2-prefill"
REQUIRED_KERNEL_FIELDS = {
    "Stream ID", "Input Shapes", "Output Shapes", "aic_mac_ratio",
    "aic_mte2_ratio", "aiv_vec_ratio",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def read_json(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_shape(path: Path) -> tuple[list[str], int]:
    with path.open(newline="", errors="replace") as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return header, rows


def main() -> int:
    expected_hashes = {
        "contract.json": "54f72f823bf88c4ba9163ca4497c537280dec1067b5393b9a8b42425399fb138",
        "capture.json": "5853dff8f335939116d7ee89deae839fad9c8d983b8c38f98df10c156d3c8a5b",
        "artifact-audit.json": "ec479b547ae72890dfb5f232bad8b7dd3d7f89ddac9dd9f17a18b1d02b13e3f6",
        "result.json": "c400e15775c82675f5ee57761370302460319b1ab2457deae2fd8978e071de15",
        "release.json": "74174566fe0602f9a6d4200dee0aa59cce5bb7345005f13ad2debe8f5e95cd8b",
    }
    for name, expected in expected_hashes.items():
        require(sha256(PREFILL / name) == expected, f"{name} SHA256 drift")

    result = read_json(PREFILL / "result.json")
    capture = read_json(PREFILL / "capture.json")
    artifact = read_json(PREFILL / "artifact-audit.json")
    guard = read_json(RAW / "hypic-only-prefill" / "lane-guard.json")
    require(sha256(RAW / "hypic-only-prefill" / "lane-guard.json") ==
            "4734d3678d2aebe4c4b2b4694f72e7667cbde1f83631e6ee94301d120737f6a7",
            "guard SHA256 drift")
    require(result["valid"] and result["errors"] == [], "capture invalid")
    require(result["phase"] == "prefill", "wrong phase")
    require(all(result["release"][key] for key in
                ("container_removed", "owned_workers_released", "port_released")),
            "owned resource release incomplete")
    require(guard["samples"] == 88 and not guard["foreign"] and
            not guard["probe_errors"], "physical NPU0-3 isolation invalid")
    require(len(capture["warmups"]) == 2 and
            all(item["output_tokens"] == 32 for item in capture["warmups"]),
            "warmup incomplete")
    require(capture["capture"]["prefill_focused"] and
            capture["capture"]["output_tokens"] == 1, "Prefill request incomplete")
    workers = capture["worker_pid_by_physical_npu"]
    require(set(workers) == {"0", "1", "2", "3"} and
            len(set(workers.values())) == 4, "four-worker mapping invalid")
    require(artifact["nonempty_files"] == 281 and
            len(artifact["inventory"]) == 281, "raw artifact count drift")
    for item in artifact["inventory"]:
        path = PREFILL / item["path"]
        require(path.is_file() and path.stat().st_size == item["size"] and
                sha256(path) == item["sha256"], f"raw artifact drift: {item['path']}")

    rank_dirs = sorted(PARSED.glob("rank*_ascend_pt"))
    require(len(rank_dirs) == 4, "parsed rank count invalid")
    per_rank = []
    for rank, directory in enumerate(rank_dirs):
        info = read_json(directory / f"profiler_info_{rank}.json")
        config = info["config"]
        experiment = config["experimental_config"]
        require(info["rank_id"] == rank and
                info["torch_npu_version"] == "2.10.0.post4" and
                info["cann_version"] == "9.1.0", "profiler stack identity drift")
        require(set(config["common_config"]["activities"]) ==
                {"ProfilerActivity.CPU", "ProfilerActivity.NPU"} and
                experiment["_profiler_level"] == "Level1" and
                experiment["_aic_metrics"] == "ACL_AICORE_PIPE_UTILIZATION" and
                experiment["_export_type"] == ["text"],
                "detailed profiler configuration absent")
        output = directory / "ASCEND_PROFILER_OUTPUT"
        kernel_header, kernel_rows = csv_shape(output / "kernel_details.csv")
        require(len(kernel_header) == 46 and kernel_rows == 5622 and
                REQUIRED_KERNEL_FIELDS <= set(kernel_header),
                "detailed kernel evidence drift")
        for name in ("op_statistic.csv", "api_statistic.csv",
                     "operator_details.csv", "step_trace_time.csv"):
            require(csv_shape(output / name)[1] > 0, f"{name} empty on rank {rank}")
        require(isinstance(read_json(output / "trace_view.json"), list),
                f"trace invalid on rank {rank}")
        per_rank.append({"rank": rank, "kernel_rows": kernel_rows,
                         "kernel_columns": len(kernel_header),
                         "kernel_sha256": sha256(output / "kernel_details.csv")})

    print(json.dumps({
        "schema": "hypic-profiler-prefill-audit/v1",
        "device_capture_valid": True,
        "offline_parse_complete": True,
        "numeric_preregistered_min_47_met": False,
        "semantic_level1_pipe_fields_present": True,
        "rank_count": len(per_rank),
        "ranks": per_rank,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
