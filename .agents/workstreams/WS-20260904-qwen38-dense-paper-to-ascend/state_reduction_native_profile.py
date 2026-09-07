#!/usr/bin/env python3
"""Collect resumable, bounded native profiles for the frozen DRRQR A/B.

The profile service is cloned from the already-audited formal service.  The
only workload-affecting delta is PROFILING_MODE=dynamic.  Profile traffic is
the exact frozen performance workload, including its two warmups.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import state_reduction_formal_runner as formal


PROFILE_ROOT = formal.ROOT / "native-profile"
PROFILE_CONTAINERS = {
    "baseline": "qwen36_state_reduction_baseline_profile_npu4_7_tp4",
    "drrqr-dk64": "qwen36_state_reduction_drrqr_dk64_profile_npu4_7_tp4",
    "drrqr-dk96": "qwen36_state_reduction_drrqr_dk96_profile_npu4_7_tp4",
}
HOST_DEVICE_PAIRS = [
    (f"/dev/davinci{index}", f"/dev/davinci{index - 4}")
    for index in formal.HOST_NPUS
]


def run(
    args: list[str],
    *,
    check: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, **kwargs)


def inspect(name: str) -> dict[str, Any]:
    result = run(["docker", "inspect", name], check=False, capture_output=True)
    if result.returncode:
        raise FileNotFoundError(name)
    return json.loads(result.stdout)[0]


def env_map(item: dict[str, Any]) -> dict[str, str]:
    return {
        entry.split("=", 1)[0]: entry.split("=", 1)[1]
        for entry in item["Config"].get("Env", [])
        if "=" in entry
    }


def effective_argv(item: dict[str, Any]) -> list[str]:
    return (item["Config"].get("Entrypoint") or []) + (
        item["Config"].get("Cmd") or []
    )


def mount_signature(item: dict[str, Any]) -> set[tuple[Any, ...]]:
    return {
        (
            mount["Type"],
            mount["Source"],
            mount["Destination"],
            mount["RW"],
            mount.get("Propagation", ""),
        )
        for mount in item.get("Mounts", [])
    }


def device_pairs(item: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (entry["PathOnHost"], entry["PathInContainer"])
        for entry in item["HostConfig"].get("Devices", [])
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]


def clone_source(source: dict[str, Any], clone_name: str) -> None:
    config = source["Config"]
    host = source["HostConfig"]
    command = ["docker", "create", "--name", clone_name]
    for key, value in sorted((config.get("Labels") or {}).items()):
        command.extend(["--label", f"{key}={value}"])
    if host.get("NetworkMode"):
        command.extend(["--network", host["NetworkMode"]])
    if host.get("IpcMode"):
        command.extend(["--ipc", host["IpcMode"]])
    if host.get("CpusetCpus"):
        command.extend(["--cpuset-cpus", host["CpusetCpus"]])
    if host.get("ShmSize"):
        command.extend(["--shm-size", str(host["ShmSize"])])
    if host.get("Memory"):
        command.extend(["--memory", str(host["Memory"])])
    if host.get("MemorySwap"):
        command.extend(["--memory-swap", str(host["MemorySwap"])])
    if host.get("Privileged"):
        command.append("--privileged")
    if host.get("ReadonlyRootfs"):
        command.append("--read-only")
    if host.get("Runtime") and host["Runtime"] != "runc":
        command.extend(["--runtime", host["Runtime"]])
    for bind in host.get("Binds") or []:
        command.extend(["--volume", bind])
    for device in host.get("Devices") or []:
        command.extend([
            "--device",
            f"{device['PathOnHost']}:{device['PathInContainer']}:"
            f"{device['CgroupPermissions']}",
        ])
    for capability in host.get("CapAdd") or []:
        command.extend(["--cap-add", capability])
    for option in host.get("SecurityOpt") or []:
        command.extend(["--security-opt", option])
    for limit in host.get("Ulimits") or []:
        command.extend([
            "--ulimit",
            f"{limit['Name']}={limit['Soft']}:{limit['Hard']}",
        ])
    if config.get("WorkingDir"):
        command.extend(["--workdir", config["WorkingDir"]])
    if config.get("User"):
        command.extend(["--user", config["User"]])
    environment = [
        entry
        for entry in config.get("Env", [])
        if not entry.startswith("PROFILING_MODE=")
    ]
    environment.append("PROFILING_MODE=dynamic")
    for entry in environment:
        command.extend(["--env", entry])
    entrypoint = config.get("Entrypoint") or []
    if entrypoint:
        command.extend(["--entrypoint", entrypoint[0]])
    command.append(source["Image"])
    command.extend(entrypoint[1:])
    command.extend(config.get("Cmd") or [])
    result = run(command, check=False, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"docker create failed ({result.returncode}): "
            f"{result.stdout}\n{result.stderr}"
        )


def verify_clone(
    arm: str,
    source: dict[str, Any],
    clone: dict[str, Any],
    *,
    require_source_exited: bool,
) -> dict[str, Any]:
    if require_source_exited and source["State"]["Status"] != "exited":
        raise RuntimeError(
            f"source must be exited: {source['State']['Status']}"
        )
    if clone["State"]["Status"] not in {"created", "exited", "running"}:
        raise RuntimeError(f"unexpected profile clone state: {clone['State']['Status']}")
    if source["Image"] != clone["Image"]:
        raise RuntimeError("profile clone image differs from source")
    if effective_argv(source) != effective_argv(clone):
        raise RuntimeError("profile clone effective argv differs from source")
    expected_env = env_map(source)
    expected_env["PROFILING_MODE"] = "dynamic"
    observed_env = env_map(clone)
    if observed_env != expected_env:
        changed = sorted(
            key
            for key in set(expected_env) | set(observed_env)
            if expected_env.get(key) != observed_env.get(key)
        )
        raise RuntimeError(f"unexpected environment delta: {changed}")
    source_host = source["HostConfig"]
    clone_host = clone["HostConfig"]
    for field in (
        "NetworkMode",
        "IpcMode",
        "Privileged",
        "ReadonlyRootfs",
        "CpusetCpus",
        "ShmSize",
        "Memory",
        "MemorySwap",
        "Runtime",
    ):
        if source_host.get(field) != clone_host.get(field):
            raise RuntimeError(f"profile clone HostConfig.{field} differs")
    if source_host.get("Devices") != clone_host.get("Devices"):
        raise RuntimeError("profile clone devices differ")
    if mount_signature(source) != mount_signature(clone):
        raise RuntimeError("profile clone mounts differ")
    if device_pairs(clone) != HOST_DEVICE_PAIRS:
        raise RuntimeError(f"unexpected NPU map: {device_pairs(clone)}")
    if clone_host.get("CpusetCpus") != formal.CPUSET:
        raise RuntimeError("unexpected CPU set")
    return {
        "schema": "state-reduction-profile-clone/v1",
        "arm": arm,
        "source_container": source["Name"].lstrip("/"),
        "source_container_id": source["Id"],
        "profile_container": clone["Name"].lstrip("/"),
        "profile_container_id": clone["Id"],
        "profile_container_state": clone["State"]["Status"],
        "image_id": clone["Image"],
        "host_to_container_devices": [
            {"host": host, "container": container}
            for host, container in device_pairs(clone)
        ],
        "cpuset_cpus": clone_host["CpusetCpus"],
        "environment_delta": {"PROFILING_MODE": "dynamic"},
        "effective_argv_equal": True,
        "mounts_equal": True,
        "devices_equal": True,
    }


def ensure_clone(arm: str) -> dict[str, Any]:
    source_name = formal.ARMS[arm]["container"]
    clone_name = PROFILE_CONTAINERS[arm]
    source = inspect(source_name)
    if source["State"]["Status"] != "exited":
        raise RuntimeError(f"formal source is not exited: {source_name}")
    try:
        clone = inspect(clone_name)
    except FileNotFoundError:
        clone_source(source, clone_name)
        clone = inspect(clone_name)
    if clone["State"]["Status"] == "running":
        raise RuntimeError(f"profile clone is already running: {clone_name}")
    return verify_clone(arm, source, clone, require_source_exited=True)


def valid_manifest(path: Path, arm: str) -> bool:
    try:
        data = json.loads(path.read_text())
        workload = Path(data["workload_json"])
        files = data["profile_files"]
        return (
            data.get("schema") == "state-reduction-native-profile/v1"
            and data.get("arm") == arm
            and data.get("profiler_exit_code") == 0
            and data.get("export_exit_code") == 0
            and data.get("docker_cp_exit_code") == 0
            and data.get("workload_exit_code") == 0
            and data.get("workload_verified") is True
            and formal.valid_performance(workload)
            and data.get("profile_file_count") == len(files)
            and data.get("profile_csv_count", 0) > 0
            and len(files) > 0
            and all(
                Path(item["path"]).is_file()
                and Path(item["path"]).stat().st_size == item["size_bytes"]
                and formal.sha256(Path(item["path"])) == item["sha256"]
                for item in files
            )
        )
    except Exception:
        return False


def archive_incomplete(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.replace(path, path.with_name(path.name + f".invalid.{stamp}"))


def start_profile_service(arm: str) -> dict[str, Any]:
    clone_name = PROFILE_CONTAINERS[arm]
    other_names = [
        formal.ARMS[name]["container"] for name in formal.ARMS
    ] + [
        PROFILE_CONTAINERS[name] for name in PROFILE_CONTAINERS
        if name != arm
    ]
    running = [
        name
        for name in other_names
        if formal.container_state(name) == "running"
    ]
    if running:
        raise RuntimeError(f"another experiment container is running: {running}")
    formal.wait_lane_empty()
    if not formal.port_is_free():
        raise RuntimeError(f"port {formal.PORT} is in use")
    run(["docker", "start", clone_name], stdout=subprocess.DEVNULL)
    deadline = time.monotonic() + 900
    while True:
        healthy = run(
            ["curl", "-fsS", f"http://127.0.0.1:{formal.PORT}/health"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if healthy:
            break
        if formal.container_state(clone_name) != "running":
            raise RuntimeError(f"{clone_name} exited before readiness")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"{clone_name} health timeout")
        time.sleep(10)
    clone = inspect(clone_name)
    source = inspect(formal.ARMS[arm]["container"])
    manifest = verify_clone(
        arm, source, clone, require_source_exited=True
    )
    container_pids = {
        int(value)
        for value in run(
            ["docker", "top", clone_name, "-eo", "pid"],
            capture_output=True,
        ).stdout.splitlines()[1:]
        if value.strip().isdigit()
    }
    for device in formal.HOST_NPUS:
        output = run(
            ["npu-smi", "info", "-t", "proc-mem", "-i", str(device)],
            capture_output=True,
        ).stdout
        observed = {
            int(value) for value in re.findall(r"Process id:(\d+)", output)
        }
        if not observed or not observed.issubset(container_pids):
            raise RuntimeError(f"NPU{device} ownership mismatch: {observed}")
    return manifest


def rank0_pid_and_socket(container: str) -> tuple[int, str]:
    lines = run(
        ["docker", "exec", container, "ps", "-eo", "pid,args"],
        capture_output=True,
    ).stdout.splitlines()
    matches = [
        int(line.strip().split(None, 1)[0])
        for line in lines
        if "VLLM::Worker_TP0" in line
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one rank-0 worker, found {matches}")
    pid = matches[0]
    dynamic_socket = f"/root/dynamic_profiling_socket_{pid}"
    result = run(
        ["docker", "exec", container, "test", "-S", dynamic_socket],
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"dynamic profiling socket missing: {dynamic_socket}")
    return pid, dynamic_socket


def exact_workload(arm: str, output: Path) -> list[str]:
    return [
        sys.executable,
        str(formal.BENCHMARK),
        "--base-url",
        f"http://127.0.0.1:{formal.PORT}",
        "--model",
        formal.ARMS[arm]["served"],
        "--input-tokens",
        "32768",
        "--prefix-tokens",
        "16384",
        "--output-tokens",
        "1024",
        "--requests",
        "40",
        "--concurrency",
        "16",
        "--warmup-requests",
        "2",
        "--warmup-evidence-timeout",
        "300",
        "--timeout",
        "2400",
        "--json-output",
        str(output),
    ]


def collect_profile(arm: str, clone_manifest: dict[str, Any]) -> Path:
    arm_root = PROFILE_ROOT / arm
    manifest_path = arm_root / "profile-manifest.json"
    if valid_manifest(manifest_path, arm):
        return manifest_path
    archive_incomplete(arm_root)
    arm_root.mkdir(parents=True)
    container = PROFILE_CONTAINERS[arm]
    rank0_pid, dynamic_socket = rank0_pid_and_socket(container)
    attempt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    container_root = f"/tmp/state-reduction-native-profile/{arm}/{attempt_id}"
    container_msprof = f"{container_root}/msprof"
    run(["docker", "exec", container, "mkdir", "-p", container_msprof])
    profiler_command = [
        "docker",
        "exec",
        "-i",
        container,
        "msprof",
        "--dynamic=on",
        f"--pid={rank0_pid}",
        f"--output={container_msprof}",
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
            f"msprof exited after start: {stdout}\n{stderr}"
        )
    workload_json = arm_root / "profile-workload.json"
    workload_command = exact_workload(arm, workload_json)
    started = time.monotonic()
    workload = run(
        workload_command,
        check=False,
        capture_output=True,
        timeout=3000,
    )
    elapsed = time.monotonic() - started
    try:
        profiler_stdout, profiler_stderr = profiler.communicate(
            input="stop\nquit\n",
            timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        run(
            ["docker", "exec", container, "pkill", "-TERM", "-x", "msprof"],
            check=False,
        )
        time.sleep(5)
        run(
            ["docker", "exec", container, "pkill", "-KILL", "-x", "msprof"],
            check=False,
        )
        profiler.kill()
        stdout, stderr = profiler.communicate()
        raise RuntimeError(
            f"msprof did not stop: {stdout}\n{stderr}"
        ) from exc
    profile_dirs = run(
        [
            "docker",
            "exec",
            container,
            "find",
            container_msprof,
            "-mindepth",
            "1",
            "-maxdepth",
            "1",
            "-type",
            "d",
            "-name",
            "PROF_*",
        ],
        capture_output=True,
    ).stdout.splitlines()
    if len(profile_dirs) != 1:
        raise RuntimeError(f"expected one PROF directory, found {profile_dirs}")
    export_command = [
        "docker",
        "exec",
        container,
        "msprof",
        "--export=on",
        f"--output={profile_dirs[0]}",
    ]
    exported = run(
        export_command,
        check=False,
        capture_output=True,
        timeout=900,
    )
    profile_output = arm_root / "msprof"
    profile_output.mkdir()
    copy_result = run(
        [
            "docker",
            "cp",
            f"{container}:{container_msprof}/.",
            str(profile_output),
        ],
        check=False,
        capture_output=True,
    )
    files: list[dict[str, Any]] = []
    for path in sorted(profile_output.rglob("*")):
        if path.is_file():
            files.append({
                "path": str(path),
                "relative_path": str(path.relative_to(arm_root)),
                "size_bytes": path.stat().st_size,
                "sha256": formal.sha256(path),
            })
    csv_files = [
        item
        for item in files
        if Path(item["path"]).name.startswith("op_summary")
        and Path(item["path"]).suffix.lower() == ".csv"
    ]
    workload_verified = (
        workload.returncode == 0
        and formal.valid_performance(workload_json)
    )
    manifest = {
        "schema": "state-reduction-native-profile/v1",
        "experiment_id": "state-reduction-qwen36-formal-npu4-7-tp4-20260906",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "arm": arm,
        "head_k_dim": formal.ARMS[arm]["head_k_dim"],
        "clone": clone_manifest,
        "rank0_container_pid": rank0_pid,
        "dynamic_socket": dynamic_socket,
        "profiler_command": profiler_command,
        "profiler_exit_code": profiler.returncode,
        "profiler_stdout_tail": profiler_stdout[-8000:],
        "profiler_stderr_tail": profiler_stderr[-8000:],
        "export_command": export_command,
        "export_exit_code": exported.returncode,
        "export_stdout_tail": exported.stdout[-8000:],
        "export_stderr_tail": exported.stderr[-8000:],
        "workload_command": workload_command,
        "workload_exit_code": workload.returncode,
        "workload_elapsed_s": elapsed,
        "workload_stdout_tail": workload.stdout[-8000:],
        "workload_stderr_tail": workload.stderr[-8000:],
        "workload_json": str(workload_json),
        "workload_json_sha256": (
            formal.sha256(workload_json) if workload_json.exists() else None
        ),
        "workload_verified": workload_verified,
        "docker_cp_exit_code": copy_result.returncode,
        "docker_cp_stdout": copy_result.stdout,
        "docker_cp_stderr": copy_result.stderr,
        "profile_file_count": len(files),
        "profile_csv_count": len(csv_files),
        "profile_files": files,
    }
    formal.atomic_json(manifest_path, manifest)
    if (
        profiler.returncode != 0
        or exported.returncode != 0
        or copy_result.returncode != 0
        or not workload_verified
        or not csv_files
    ):
        raise RuntimeError(f"profile evidence rejected: {manifest_path}")
    return manifest_path


def stop_clone(arm: str) -> None:
    container = PROFILE_CONTAINERS[arm]
    if formal.container_state(container) == "running":
        run(["docker", "stop", "--time", "60", container])
    if formal.container_state(container) != "exited":
        raise RuntimeError(f"profile container did not exit: {container}")
    formal.wait_lane_empty()
    arm_root = PROFILE_ROOT / arm
    arm_root.mkdir(parents=True, exist_ok=True)
    with (arm_root / "service.profile.log").open("w") as stream:
        run(
            ["docker", "logs", "--timestamps", container],
            check=False,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )


def preflight() -> None:
    formal.preflight()
    if formal.sha256(formal.BENCHMARK) != formal.EXPECTED[str(formal.BENCHMARK)]:
        raise RuntimeError("benchmark hash drift")
    for arm in formal.ARMS:
        formal.verify_container(arm)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(formal.ARMS), required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    preflight()
    if args.self_test:
        print("state-reduction native profile self-test passed")
        return 0
    manifest_path = PROFILE_ROOT / args.arm / "profile-manifest.json"
    if valid_manifest(manifest_path, args.arm):
        if formal.container_state(PROFILE_CONTAINERS[args.arm]) == "running":
            raise RuntimeError(
                "valid profile manifest exists but its profile container is "
                "still running; inspect the authoritative controller before cleanup"
            )
        print(manifest_path)
        return 0
    clone_manifest = ensure_clone(args.arm)
    running = False
    try:
        clone_manifest = start_profile_service(args.arm)
        running = True
        manifest_path = collect_profile(args.arm, clone_manifest)
    finally:
        if running or formal.container_state(PROFILE_CONTAINERS[args.arm]) == "running":
            stop_clone(args.arm)
    if not valid_manifest(manifest_path, args.arm):
        raise RuntimeError(f"final profile validation failed: {manifest_path}")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
