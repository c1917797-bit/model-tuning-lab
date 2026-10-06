#!/usr/bin/env python3
"""Collect bounded, diagnostic-only TP4 native profiles from a frozen arm.

Prefill and Decode stimuli are separate. The Decode capture includes startup
prefill rows, so downstream analysis must select steady Decode intervals.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py")
NAMES = {
    "no-cache": "qwen36_hypic2048_profile_baseline_npu0_3_v1",
    "hypic-only": "qwen36_hypic2048_profile_treatment_npu0_3_v1",
}
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MODEL = "qwen36-hypic-e2e-2048"
PORT = 8223


def run(*args: str, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check, timeout=timeout)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_container(arm: str) -> tuple[dict, dict[str, str]]:
    name = NAMES[arm]
    values = json.loads(run("docker", "inspect", name).stdout)
    if len(values) != 1:
        raise RuntimeError("profile container inspect cardinality mismatch")
    item = values[0]
    env = dict(entry.split("=", 1) for entry in item["Config"]["Env"] if "=" in entry)
    devices = [
        entry["PathOnHost"] for entry in item["HostConfig"]["Devices"]
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]
    if not (
        item["Name"] == f"/{name}"
        and item["Image"] == IMAGE
        and item["Config"]["Labels"].get("hypic.experiment") == "hypic-qwen36-e2e-2048-20261006"
        and item["Config"]["Labels"].get("hypic.arm") == f"profile-{arm}"
        and item["State"]["Status"] == "running"
        and item["HostConfig"]["CpusetCpus"] == "112-191"
        and devices == [f"/dev/davinci{index}" for index in range(4)]
        and env.get("PROFILING_MODE") == "dynamic"
        and env.get("VLLM_ASCEND_HYPIC_ENABLE") == ("0" if arm == "no-cache" else "1")
    ):
        raise RuntimeError("profile container identity, ownership, or state mismatch")
    return item, env


def worker_pids(name: str) -> dict[int, int]:
    output = run("docker", "exec", name, "ps", "-eo", "pid,args").stdout
    found: dict[int, list[int]] = {rank: [] for rank in range(4)}
    for line in output.splitlines():
        match = re.search(r"^\s*(\d+)\s+.*VLLM::Worker_TP([0-3])\b", line)
        if match:
            found[int(match.group(2))].append(int(match.group(1)))
    if any(len(values) != 1 for values in found.values()):
        raise RuntimeError(f"expected exactly one worker per TP rank: {found}")
    pids = {rank: values[0] for rank, values in found.items()}
    for rank, pid in pids.items():
        socket = f"/root/dynamic_profiling_socket_{pid}"
        if run("docker", "exec", name, "test", "-S", socket, check=False).returncode:
            raise RuntimeError(f"rank {rank} dynamic profiler socket missing: {socket}")
    return pids


def benchmark_args(output: Path, tokens: int, requests: int, concurrency: int, arm: str) -> list[str]:
    args = [
        "python3", str(BENCHMARK),
        "--base-url", f"http://127.0.0.1:{PORT}",
        "--model", MODEL,
        "--input-tokens", "32768",
        "--prefix-tokens", "16384",
        "--output-tokens", str(tokens),
        "--requests", str(requests),
        "--concurrency", str(concurrency),
        "--warmup-requests", "2",
        "--warmup-evidence-timeout", "300",
        "--timeout", "2400",
        "--json-output", str(output),
    ]
    if arm == "hypic-only":
        args += ["--evidence-file", str(ROOT / "profiles" / arm / "hypic-evidence.jsonl")]
    return args


def verify_stimulus(path: Path, requests: int, tokens: int) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    results = document["results"]
    summary = document["summary"]
    passed = (
        len(results) == requests
        and sorted(row["index"] for row in results) == list(range(requests))
        and summary.get("successful") == requests
        and summary.get("failed") == 0
        and all(row.get("ok") is True and row.get("output_tokens") == tokens for row in results)
    )
    return {"passed": passed, "requests": requests, "output_tokens": tokens, "sha256": sha256(path)}


def summarize_rank(path: Path) -> dict:
    files = [item for item in path.rglob("*") if item.is_file()]
    # Dynamic msprof names differ from torch_npu.profiler's ASCEND_PROFILER_OUTPUT.
    kernels = sorted(path.rglob("op_summary_*.csv"))
    traces = sorted(path.rglob("msprof_*.json"))
    ops = sorted(path.rglob("op_statistic_*.csv"))
    apis = sorted(path.rglob("api_statistic_*.csv"))
    steps = sorted(path.rglob("task_time_*.csv"))
    kernel_columns = []
    for item in kernels:
        with item.open(encoding="utf-8", newline="") as stream:
            kernel_columns.append(len(next(csv.reader(stream), [])))
    valid_traces = 0
    for item in traces:
        try:
            json.loads(item.read_text(encoding="utf-8"))
            valid_traces += 1
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    return {
        "file_count": len(files),
        "op_summary_count": len(kernels),
        "op_summary_column_counts": kernel_columns,
        "op_statistic_count": len(ops),
        "api_statistic_count": len(apis),
        "task_time_count": len(steps),
        "msprof_trace_count": len(traces),
        "valid_msprof_trace_count": valid_traces,
        "complete": bool(kernels and ops and apis and steps and traces)
        and all(columns >= 40 for columns in kernel_columns)
        and valid_traces == len(traces),
        "file_manifest": [
            {"path": str(item.relative_to(ROOT)), "size_bytes": item.stat().st_size, "sha256": sha256(item)}
            for item in sorted(files)
        ],
    }


def offline_export(name: str, arm: str, phase: str, rank: int) -> dict:
    root = ROOT / "profiles" / arm / phase / f"rank{rank}" / "msprof"
    captures = sorted(item for item in root.glob("PROF_*") if item.is_dir())
    if len(captures) != 1:
        raise RuntimeError(f"rank {rank}: expected one raw PROF directory, found {len(captures)}")
    container_capture = f"/results/profiles/{arm}/{phase}/rank{rank}/msprof/{captures[0].name}"
    commands = (
        ["docker", "exec", name, "msprof", "--parse=on", f"--output={container_capture}"],
        ["docker", "exec", name, "msprof", "--export=on", f"--output={container_capture}"],
    )
    results = []
    for command in commands:
        result = run(*command, check=False, timeout=600)
        results.append({"command": command, "exit_code": result.returncode, "stdout_tail": result.stdout[-3000:], "stderr_tail": result.stderr[-3000:]})
        if result.returncode:
            break
    return {"capture": str(captures[0].relative_to(ROOT)), "steps": results, "passed": len(results) == 2 and all(item["exit_code"] == 0 for item in results)}


def finalize_existing(arm: str, phase: str) -> int:
    phase_root = ROOT / "profiles" / arm / phase
    original = phase_root / "profile-manifest.json"
    if not original.is_file():
        raise RuntimeError(f"{original}: initial capture manifest missing")
    target = phase_root / "profile-finalized.json"
    if target.exists():
        raise RuntimeError(f"{target}: finalized capture already exists")
    initial = json.loads(original.read_text(encoding="utf-8"))
    item, _ = inspect_container(arm)
    if item["Id"] != initial.get("container_id"):
        raise RuntimeError("profile container changed since raw capture")
    exports = {}
    for rank in range(4):
        exports[str(rank)] = offline_export(NAMES[arm], arm, phase, rank)
    ranks = {str(rank): summarize_rank(phase_root / f"rank{rank}" / "msprof") for rank in range(4)}
    passed = (
        initial.get("stimulus", {}).get("passed") is True
        and all(row.get("exit_code") == 0 for row in initial.get("profiler_results", {}).values())
        and all(row["passed"] for row in exports.values())
        and all(row["complete"] for row in ranks.values())
    )
    result = {
        "schema": "hypic-native-profile-finalized/v1",
        "initial_manifest_sha256": sha256(original),
        "arm": arm,
        "phase": phase,
        "container_id": item["Id"],
        "offline_exports": exports,
        "ranks": ranks,
        "passed": passed,
        "note": "recovered raw dynamic msprof data by explicit per-PROF parse and export; no NPU requests repeated",
    }
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"arm": arm, "phase": phase, "passed": passed, "finalized": str(target)}, sort_keys=True))
    return 0 if passed else 2


def stop_profiler(process: subprocess.Popen[str]) -> tuple[int | None, str, str]:
    try:
        stdout, stderr = process.communicate(input="stop\nquit\n", timeout=600)
        return process.returncode, stdout[-3000:], stderr[-3000:]
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        return process.returncode, stdout[-3000:], stderr[-3000:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(NAMES), required=True)
    parser.add_argument("--phase", choices=("prefill", "decode"), required=True)
    parser.add_argument("--finalize-existing", action="store_true")
    parser.add_argument(
        "--offline-ranks", default="0,1,2,3",
        help="TP ranks to parse/export; all four ranks are always dynamically captured",
    )
    args = parser.parse_args()
    arm, phase = args.arm, args.phase
    if args.finalize_existing:
        return finalize_existing(arm, phase)
    try:
        offline_ranks = tuple(int(value) for value in args.offline_ranks.split(","))
    except ValueError as exc:
        raise RuntimeError("--offline-ranks must be comma-separated integers") from exc
    if not offline_ranks or len(offline_ranks) != len(set(offline_ranks)) or any(rank not in range(4) for rank in offline_ranks):
        raise RuntimeError("--offline-ranks must be a nonempty unique subset of 0,1,2,3")
    phase_root = ROOT / "profiles" / arm / phase
    if phase_root.exists():
        raise RuntimeError(f"{phase_root}: existing capture; refuse overwrite")
    item, _ = inspect_container(arm)
    name = NAMES[arm]
    pids = worker_pids(name)
    phase_root.mkdir(parents=True)
    warmup_path = phase_root / "profile-warmup.json"
    warmup_command = benchmark_args(warmup_path, 16, 2, 2, arm)
    warmup = run(*warmup_command, check=False, timeout=2400)
    (phase_root / "profile-warmup.log").write_text(warmup.stdout[-8000:] + warmup.stderr[-8000:], encoding="utf-8")
    warmup_check = verify_stimulus(warmup_path, 2, 16) if warmup_path.is_file() else {"passed": False}
    if warmup.returncode or not warmup_check["passed"]:
        raise RuntimeError(f"{phase}: compile/preload warmup failed; see profile-warmup.log")

    processes: dict[int, subprocess.Popen[str]] = {}
    profiler_results: dict[int, dict] = {}
    workload_path = phase_root / "profile-workload.json"
    output_tokens = 1 if phase == "prefill" else 128
    workload_command = benchmark_args(workload_path, output_tokens, 4, 4, arm)
    workload = None
    started_at = datetime.now(timezone.utc)
    error = None
    try:
        for rank, pid in pids.items():
            output = f"/results/profiles/{arm}/{phase}/rank{rank}/msprof"
            run("docker", "exec", name, "mkdir", "-p", output)
            command = [
                "docker", "exec", "-i", name, "msprof",
                "--dynamic=on", f"--pid={pid}", f"--output={output}",
                "--task-time=l2", "--ai-core=on",
                "--aic-metrics=PipeUtilization", "--export=on",
            ]
            processes[rank] = subprocess.Popen(command, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)
        for rank, process in processes.items():
            if process.poll() is not None:
                raise RuntimeError(f"rank {rank} msprof exited before capture")
            assert process.stdin is not None
            process.stdin.write("start\n")
            process.stdin.flush()
        time.sleep(3)
        for rank, process in processes.items():
            if process.poll() is not None:
                raise RuntimeError(f"rank {rank} msprof exited after start")
        workload = run(*workload_command, check=False, timeout=2400)
        (phase_root / "profile-workload.log").write_text(workload.stdout[-8000:] + workload.stderr[-8000:], encoding="utf-8")
    except Exception as exc:
        error = str(exc)
    finally:
        for rank, process in processes.items():
            code, stdout, stderr = stop_profiler(process)
            profiler_results[rank] = {"exit_code": code, "stdout_tail": stdout, "stderr_tail": stderr}

    stimulus = verify_stimulus(workload_path, 4, output_tokens) if workload_path.is_file() else {"passed": False}
    exports = {}
    for rank in offline_ranks:
        try:
            exports[str(rank)] = offline_export(name, arm, phase, rank)
        except Exception as exc:
            exports[str(rank)] = {"passed": False, "error": str(exc)}
    ranks = {str(rank): summarize_rank(phase_root / f"rank{rank}" / "msprof") for rank in range(4)}
    profile_complete = all(result["complete"] for result in ranks.values())
    selected_profile_complete = all(ranks[str(rank)]["complete"] for rank in offline_ranks)
    passed = (
        error is None and workload is not None and workload.returncode == 0
        and stimulus["passed"] and selected_profile_complete
        and all(result["passed"] for result in exports.values())
        and all(result["exit_code"] == 0 for result in profiler_results.values())
    )
    manifest = {
        "schema": "hypic-native-profile-2048/v1",
        "captured_at": started_at.isoformat(),
        "arm": arm,
        "phase": phase,
        "container": name,
        "container_id": item["Id"],
        "image": IMAGE,
        "physical_npus": [0, 1, 2, 3],
        "rank_container_pids": pids,
        "diagnostic_only": True,
        "profile_traffic_not_formal_performance_evidence": True,
        "phase_scope": "prefill-dominant one-output-token requests" if phase == "prefill" else "128-token requests including prefill onset; select at least 10 steady Decode intervals in analysis",
        "profiler_config": "dynamic msprof task-time=l2 ai-core=on aic-metrics=PipeUtilization export=on",
        "warmup": warmup_check,
        "warmup_command": warmup_command,
        "workload_command": workload_command,
        "workload_exit_code": None if workload is None else workload.returncode,
        "stimulus": stimulus,
        "profiler_results": profiler_results,
        "offline_ranks": offline_ranks,
        "offline_export_omitted_ranks": [rank for rank in range(4) if rank not in offline_ranks],
        "offline_exports": exports,
        "ranks": ranks,
        "profile_complete": profile_complete,
        "selected_profile_complete": selected_profile_complete,
        "passed": passed,
        "error": error,
    }
    manifest_path = phase_root / "profile-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"arm": arm, "phase": phase, "passed": passed, "profile_complete": profile_complete, "stimulus_passed": stimulus["passed"], "manifest": str(manifest_path), "error": error}, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
