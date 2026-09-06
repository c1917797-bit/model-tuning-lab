#!/usr/bin/env python3
"""Create and verify a profile-only clone with dynamic profiling enabled."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from typing import Any


EXPECTED_ACCELERATORS = [f"/dev/davinci{index}" for index in range(4)]


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def inspect(name: str) -> dict[str, Any]:
    result = run("docker", "inspect", name, check=False)
    if result.returncode:
        raise FileNotFoundError(name)
    return json.loads(result.stdout)[0]


def env_map(item: dict[str, Any]) -> dict[str, str]:
    return {
        entry.split("=", 1)[0]: entry.split("=", 1)[1]
        for entry in item["Config"].get("Env", [])
        if "=" in entry
    }


def accelerators(item: dict[str, Any]) -> list[str]:
    return [
        entry["PathOnHost"]
        for entry in item["HostConfig"].get("Devices", [])
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]


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


def create_clone(source: dict[str, Any], clone_name: str) -> None:
    config = source["Config"]
    host = source["HostConfig"]
    command = ["docker", "create", "--name", clone_name]
    if host.get("NetworkMode"):
        command.extend(["--network", host["NetworkMode"]])
    if host.get("IpcMode"):
        command.extend(["--ipc", host["IpcMode"]])
    if host.get("CpusetCpus"):
        command.extend(["--cpuset-cpus", host["CpusetCpus"]])
    if host.get("ShmSize"):
        command.extend(["--shm-size", str(host["ShmSize"])])
    if host.get("Privileged"):
        command.append("--privileged")
    if host.get("Runtime") and host["Runtime"] != "runc":
        command.extend(["--runtime", host["Runtime"]])
    for bind in host.get("Binds") or []:
        command.extend(["--volume", bind])
    for device in host.get("Devices") or []:
        value = (
            f"{device['PathOnHost']}:{device['PathInContainer']}:"
            f"{device['CgroupPermissions']}"
        )
        command.extend(["--device", value])
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
    result = run(*command, check=False)
    if result.returncode:
        raise RuntimeError(
            f"docker create failed ({result.returncode}): "
            f"{result.stdout}\n{result.stderr}"
        )


def verify_clone(
    source: dict[str, Any],
    clone: dict[str, Any],
    expected_hypic: str,
) -> dict[str, Any]:
    if source["State"]["Status"] != "exited":
        raise RuntimeError(
            f"source must be exited before clone use: {source['State']['Status']}"
        )
    if clone["State"]["Status"] not in {"created", "exited"}:
        raise RuntimeError(
            f"profile clone must be stopped for verification: "
            f"{clone['State']['Status']}"
        )
    if source["Image"] != clone["Image"]:
        raise RuntimeError("profile clone image differs from source")
    if effective_argv(source) != effective_argv(clone):
        raise RuntimeError("profile clone effective argv differs from source")
    source_env = env_map(source)
    clone_env = env_map(clone)
    expected_env = dict(source_env)
    expected_env["PROFILING_MODE"] = "dynamic"
    if clone_env != expected_env:
        changed = sorted(
            key
            for key in set(clone_env) | set(expected_env)
            if clone_env.get(key) != expected_env.get(key)
        )
        raise RuntimeError(f"unexpected profile clone environment delta: {changed}")
    hypic_enabled = clone_env.get("VLLM_ASCEND_HYPIC_ENABLE") == "1"
    if expected_hypic == "enabled" and not hypic_enabled:
        raise RuntimeError("profile clone does not enable HYPIC")
    if expected_hypic == "disabled" and hypic_enabled:
        raise RuntimeError("profile clone unexpectedly enables HYPIC")
    source_host = source["HostConfig"]
    clone_host = clone["HostConfig"]
    for field in (
        "NetworkMode",
        "IpcMode",
        "Privileged",
        "CpusetCpus",
        "ShmSize",
        "Runtime",
    ):
        if source_host.get(field) != clone_host.get(field):
            raise RuntimeError(f"profile clone HostConfig.{field} differs")
    if mount_signature(source) != mount_signature(clone):
        raise RuntimeError("profile clone bind mounts differ")
    if source_host.get("Devices") != clone_host.get("Devices"):
        raise RuntimeError("profile clone devices differ")
    if accelerators(clone) != EXPECTED_ACCELERATORS:
        raise RuntimeError(
            f"profile clone accelerators are not NPU0-3: {accelerators(clone)}"
        )
    if clone_host.get("CpusetCpus") != "112-191":
        raise RuntimeError("profile clone CPU set is not 112-191")
    return {
        "schema": "hypic-profile-clone/v1",
        "source_container": source["Name"].lstrip("/"),
        "source_container_id": source["Id"],
        "profile_container": clone["Name"].lstrip("/"),
        "profile_container_id": clone["Id"],
        "image_id": clone["Image"],
        "state": clone["State"]["Status"],
        "cpuset_cpus": clone_host["CpusetCpus"],
        "accelerator_devices": accelerators(clone),
        "hypic_enabled": hypic_enabled,
        "environment_delta": {"PROFILING_MODE": "dynamic"},
        "effective_argv_equal": True,
        "bind_mounts_equal": True,
        "devices_equal": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--clone", required=True)
    parser.add_argument(
        "--expected-hypic",
        choices=("enabled", "disabled"),
        required=True,
    )
    args = parser.parse_args()
    source = inspect(args.source)
    if source["State"]["Status"] != "exited":
        raise RuntimeError(
            f"refusing to clone running source {args.source}: "
            f"{source['State']['Status']}"
        )
    try:
        clone = inspect(args.clone)
    except FileNotFoundError:
        create_clone(source, args.clone)
        clone = inspect(args.clone)
    manifest = verify_clone(source, clone, args.expected_hypic)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
