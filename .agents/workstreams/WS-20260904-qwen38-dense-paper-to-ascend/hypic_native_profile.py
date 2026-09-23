#!/usr/bin/env python3
"""Collect a bounded rank-0 native profile for the frozen HYPIC workload."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_prefix_coexistence.py")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def assess_capture_stimulus(path: Path, expected_requests: int) -> dict[str, object]:
    """Separate successful profiler stimulus from algorithm acceptance."""

    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "verified": False,
            "reason": f"workload report is unreadable: {exc}",
        }
    config = report.get("config")
    summary = report.get("summary")
    results = report.get("results")
    if not isinstance(config, dict) or not isinstance(summary, dict):
        return {
            "verified": False,
            "reason": "workload report lacks config/summary objects",
        }
    if not isinstance(results, list):
        results = []
    observed = {
        "configured_requests": config.get("requests"),
        "summary_requests": summary.get("requests"),
        "successful": summary.get("successful"),
        "failed": summary.get("failed"),
        "fixed_output_verified": summary.get("fixed_output_verified"),
        "result_count": len(results),
        "all_measured_results_ok": bool(results)
        and all(isinstance(item, dict) and item.get("ok") is True for item in results),
        "coexistence_verified": summary.get("coexistence_verified"),
        "coexistence_missing": summary.get("coexistence_missing"),
        "hot_path_verified": summary.get("hot_path_verified"),
        "hot_path_missing": summary.get("hot_path_missing"),
    }
    verified = (
        observed["configured_requests"] == expected_requests
        and observed["summary_requests"] == expected_requests
        and observed["successful"] == expected_requests
        and observed["failed"] == 0
        and observed["fixed_output_verified"] is True
        and observed["result_count"] == expected_requests
        and observed["all_measured_results_ok"] is True
    )
    return {
        "verified": verified,
        "purpose": "bounded native-profiler traffic stimulus only",
        "algorithm_acceptance_derived_from_this_gate": False,
        "observed": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    parser.add_argument("--phase", choices=("pdc-baseline", "pdc-hypic"), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=300)
    args = parser.parse_args()

    inspect = json.loads(run("docker", "inspect", args.container).stdout)[0]
    if not inspect["State"]["Running"]:
        raise RuntimeError(f"container is not running: {args.container}")
    host_devices = [item["PathOnHost"] for item in inspect["HostConfig"]["Devices"]]
    accelerator_devices = [
        path
        for path in host_devices
        if path.startswith("/dev/davinci")
        and path.removeprefix("/dev/davinci").isdigit()
    ]
    if accelerator_devices != [f"/dev/davinci{index}" for index in range(4)]:
        raise RuntimeError(f"refusing non-NPU0-3 container devices: {accelerator_devices}")
    if inspect["HostConfig"]["CpusetCpus"] != "112-191":
        raise RuntimeError(f"unexpected CPU set: {inspect['HostConfig']['CpusetCpus']}")

    environment = dict(
        entry.split("=", 1)
        for entry in inspect["Config"].get("Env", [])
        if "=" in entry
    )
    if environment.get("PROFILING_MODE") != "dynamic":
        raise RuntimeError(
            "attach profiling requires a profile-only service started with "
            "PROFILING_MODE=dynamic"
        )

    processes = run(
        "docker", "exec", args.container, "ps", "-eo", "pid,args"
    ).stdout.splitlines()
    matches = [line.strip().split(None, 1)[0] for line in processes if "VLLM::Worker_TP0" in line]
    if len(matches) != 1:
        raise RuntimeError(f"expected one rank-0 worker, found {matches}")
    rank0_pid = matches[0]
    dynamic_socket = f"/root/dynamic_profiling_socket_{rank0_pid}"
    socket_probe = run(
        "docker",
        "exec",
        args.container,
        "test",
        "-S",
        dynamic_socket,
        check=False,
    )
    if socket_probe.returncode:
        available = run(
            "docker",
            "exec",
            args.container,
            "/bin/bash",
            "-lc",
            "find /root -maxdepth 1 -type s "
            "-name 'dynamic_profiling_socket_*' -printf '%f\\n' 2>/dev/null",
            check=False,
        ).stdout.splitlines()
        raise RuntimeError(
            f"rank-0 dynamic profiling socket missing: {dynamic_socket}; "
            f"available={available}"
        )

    phase_root = args.output_root / args.phase
    msprof_host = phase_root / "msprof"
    phase_root.mkdir(parents=True, exist_ok=True)
    msprof_container = Path("/results/profiles") / args.phase / "msprof"
    run("docker", "exec", args.container, "mkdir", "-p", str(msprof_container))
    profiler_command = [
        "docker", "exec", "-i", args.container,
        "msprof",
        "--dynamic=on",
        f"--pid={rank0_pid}",
        f"--output={msprof_container}",
        "--task-time=l2",
        "--ai-core=on",
        "--aic-metrics=PipeUtilization",
        "--export=on",
    ]
    profiler = subprocess.Popen(
        profiler_command,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(5)
    if profiler.poll() is not None:
        stdout, stderr = profiler.communicate()
        raise RuntimeError(f"msprof exited before workload: {stdout}\n{stderr}")
    assert profiler.stdin is not None
    profiler.stdin.write("start\n")
    profiler.stdin.flush()
    time.sleep(3)
    if profiler.poll() is not None:
        stdout, stderr = profiler.communicate()
        raise RuntimeError(
            f"msprof exited after start command: {stdout}\n{stderr}"
        )

    workload_json = phase_root / "profile-workload.json"
    workload_command = [
        "python3", str(BENCHMARK),
        "--base-url", "http://127.0.0.1:8221",
        "--model", "qwen36-hypic-piercing",
        "--input-tokens", "32768",
        "--native-prefix-tokens", "8192",
        "--pic-segment-tokens", "16384",
        "--warm-tail-tokens", "512",
        "--pic-placement-mode", "relocated",
        "--output-tokens", "128",
        "--requests", "4",
        "--concurrency", "4",
        "--pic-warmup-requests", "2",
        "--native-warmup-requests", "2",
        "--timeout", "2400",
        "--json-output", str(workload_json),
    ]
    if args.phase == "pdc-baseline":
        workload_command.append("--baseline")
    else:
        workload_command.append("--no-require-performance-target")
        workload_command.extend([
            "--evidence-file",
            "/cache/cch/hypic-qwen36-piercing-20260904/pdc-hypic/hypic-evidence.jsonl",
        ])
    profile_started = time.monotonic()
    workload = subprocess.run(
        workload_command,
        text=True,
        capture_output=True,
        timeout=max(args.duration + 600, 2400),
    )
    profile_elapsed = time.monotonic() - profile_started
    capture_stimulus = assess_capture_stimulus(workload_json, expected_requests=4)
    try:
        profiler_stdout, profiler_stderr = profiler.communicate(
            input="stop\nquit\n",
            timeout=600,
        )
    except subprocess.TimeoutExpired as error:
        run(
            "docker",
            "exec",
            args.container,
            "pkill",
            "-TERM",
            "-x",
            "msprof",
            check=False,
        )
        time.sleep(5)
        run(
            "docker",
            "exec",
            args.container,
            "pkill",
            "-KILL",
            "-x",
            "msprof",
            check=False,
        )
        profiler.kill()
        stdout, stderr = profiler.communicate()
        raise RuntimeError(
            f"msprof did not stop after workload: {stdout}\n{stderr}"
        ) from error

    files = []
    if msprof_host.exists():
        for path in sorted(msprof_host.rglob("*")):
            if path.is_file():
                files.append({
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
    manifest = {
        "schema": "hypic-native-profile/v1",
        "phase": args.phase,
        "container": args.container,
        "container_id": inspect["Id"],
        "image_id": inspect["Image"],
        "cpuset_cpus": inspect["HostConfig"]["CpusetCpus"],
        "host_accelerator_devices": accelerator_devices,
        "rank0_container_pid": int(rank0_pid),
        "dynamic_socket": dynamic_socket,
        "profile_duration_cap_s": args.duration,
        "profile_elapsed_s": profile_elapsed,
        "profiler_command": profiler_command,
        "profiler_exit_code": profiler.returncode,
        "profiler_stdout": profiler_stdout[-4000:],
        "profiler_stderr": profiler_stderr[-4000:],
        "workload_command": workload_command,
        "workload_exit_code": workload.returncode,
        "workload_exit_semantics": (
            "raw benchmark exit: zero requires algorithm acceptance; "
            "profile_capture_stimulus independently verifies completed traffic"
        ),
        "profile_capture_stimulus": capture_stimulus,
        "workload_stdout": workload.stdout[-8000:],
        "workload_stderr": workload.stderr[-8000:],
        "workload_json": str(workload_json),
        "workload_json_sha256": sha256_file(workload_json) if workload_json.exists() else None,
        "profile_files": files,
    }
    manifest_path = phase_root / "profile-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True), flush=True)
    return 0 if (
        profiler.returncode == 0
        and capture_stimulus.get("verified") is True
        and files
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
