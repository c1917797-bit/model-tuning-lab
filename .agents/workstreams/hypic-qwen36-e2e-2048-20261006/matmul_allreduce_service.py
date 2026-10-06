#!/usr/bin/env python3
"""One-switch HYPIC + MatMulAllReduce candidate on owned NPU0-3 only."""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from profile_service import IMAGE, ROOT, lane_empty, port_free, run, sha256, source_inspects


NAME = "qwen36_hypic2048_matmulallreduce_npu0_3_v1"
ARM = "candidate-matmul-allreduce"
EXPERIMENT = "hypic-qwen36-e2e-2048-20261006"
SOURCE_NAME = "/qwen36_hypic2048_treatment_npu0_3_v1"
SOURCE_ROOT = Path("/cache/cch/hypic_vllm_ascend-v0.8.5")
PORT = 8223


def inspect() -> dict | None:
    response = run("docker", "inspect", NAME, check=False)
    if response.returncode:
        return None
    values = json.loads(response.stdout)
    if len(values) != 1:
        raise RuntimeError("candidate inspect cardinality mismatch")
    return values[0]


def frozen_spec() -> tuple[dict, dict[str, str], list[str], str]:
    snapshot_path, sources = source_inspects()
    source = sources[SOURCE_NAME]
    if not (
        source["Image"] == IMAGE
        and source["HostConfig"]["CpusetCpus"] == "112-191"
        and source["HostConfig"]["NetworkMode"] == "host"
        and source["Config"]["Labels"].get("hypic.experiment") == EXPERIMENT
        and source["Config"]["Labels"].get("hypic.arm") == "hypic-only"
    ):
        raise RuntimeError("frozen HYPIC source container identity drift")
    if run("git", "-C", str(SOURCE_ROOT), "rev-parse", "HEAD").stdout.strip() != "3ad0967589304cd8fc4e7cff02f48ecc6125c89f":
        raise RuntimeError("HYPIC source commit drift")
    if run("git", "-C", str(SOURCE_ROOT), "diff", "--quiet", "--", "hypic_vllm_ascend", check=False).returncode:
        raise RuntimeError("HYPIC package source changed since frozen run")
    if run("git", "-C", str(SOURCE_ROOT), "ls-files", "--others", "--exclude-standard", "--", "hypic_vllm_ascend").stdout.strip():
        raise RuntimeError("untracked HYPIC package source is present")
    devices = [entry["PathOnHost"] for entry in source["HostConfig"]["Devices"]
               if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
    if devices != [f"/dev/davinci{index}" for index in range(4)]:
        raise RuntimeError("frozen NPU0-3 device mapping drift")
    env = dict(item.split("=", 1) for item in source["Config"]["Env"] if "=" in item)
    if env.get("VLLM_ASCEND_HYPIC_ENABLE") != "1" or "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE" in env:
        raise RuntimeError("source treatment switch or fusion default drift")
    env["VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE"] = "1"
    env["VLLM_ASCEND_HYPIC_EVIDENCE_FILE"] = f"/results/{ARM}/hypic-evidence.jsonl"
    source_command = source["Config"]["Cmd"]
    if source_command[:2] != ["bash", "-lc"] or len(source_command) != 3:
        raise RuntimeError("frozen source command shape drift")
    if source_command[2].count("/results/hypic-only") != 2:
        raise RuntimeError("frozen source artifact path count drift")
    command = source_command[2].replace("/results/hypic-only", f"/results/{ARM}")
    if "--max-model-len 40960" not in command or "--tensor-parallel-size 4" not in command:
        raise RuntimeError("frozen model/parallelism command drift")
    return source, env, ["bash", "-lc", command], sha256(snapshot_path)


def exact_identity(item: dict) -> None:
    source, expected_env, command, _ = frozen_spec()
    labels = item["Config"]["Labels"]
    env = dict(value.split("=", 1) for value in item["Config"]["Env"] if "=" in value)
    devices = [(entry["PathOnHost"], entry["PathInContainer"], entry["CgroupPermissions"])
               for entry in item["HostConfig"]["Devices"]]
    expected_devices = [(entry["PathOnHost"], entry["PathInContainer"], entry["CgroupPermissions"])
                        for entry in source["HostConfig"]["Devices"]]
    if not (
        item["Name"] == f"/{NAME}"
        and item["Image"] == IMAGE
        and labels.get("hypic.experiment") == EXPERIMENT
        and labels.get("hypic.arm") == ARM
        and labels.get("hypic.purpose") == "optimization-iteration"
        and env == expected_env
        and item["Config"]["Cmd"] == command
        and item["HostConfig"]["CpusetCpus"] == "112-191"
        and item["HostConfig"]["NetworkMode"] == "host"
        and sorted(item["HostConfig"]["Binds"]) == sorted(source["HostConfig"]["Binds"])
        and item["HostConfig"]["ShmSize"] == source["HostConfig"]["ShmSize"]
        and devices == expected_devices
    ):
        raise RuntimeError("candidate container deviates from one-switch frozen treatment")


def receipt(name: str, data: dict) -> None:
    path = ROOT / ARM / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def start() -> None:
    existing = inspect()
    if existing is not None:
        exact_identity(existing)
        if existing["State"]["Status"] != "created":
            raise RuntimeError(f"{NAME} exists but is not an unstarted exact candidate")
    if not lane_empty() or not port_free():
        raise RuntimeError("NPU0-3 or port 8223 occupied before candidate start")
    source, env, command, snapshot_sha = frozen_spec()
    args = ["docker", "create", "--name", NAME,
            "--label", f"hypic.experiment={EXPERIMENT}",
            "--label", f"hypic.arm={ARM}",
            "--label", "hypic.purpose=optimization-iteration",
            "--network", "host", "--shm-size", str(source["HostConfig"]["ShmSize"]),
            "--cpuset-cpus", "112-191"]
    for entry in source["HostConfig"]["Devices"]:
        args += ["--device", f"{entry['PathOnHost']}:{entry['PathInContainer']}:{entry['CgroupPermissions']}"]
    for bind in source["HostConfig"]["Binds"]:
        args += ["-v", bind]
    for key, value in sorted(env.items()):
        args += ["-e", f"{key}={value}"]
    args += [IMAGE, *command]
    if existing is None:
        run(*args)
    item = inspect()
    if item is None:
        raise RuntimeError("candidate container missing after create")
    exact_identity(item)
    run("docker", "start", NAME)
    deadline = time.monotonic() + 2400
    try:
        while time.monotonic() < deadline:
            current = inspect()
            if current is None or current["State"]["Status"] != "running":
                raise RuntimeError("candidate exited before health")
            try:
                with urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as response:
                    if response.status == 200:
                        receipt("service-start.json", {
                            "schema": "hypic-matmul-allreduce-service-start/v1",
                            "started_at": datetime.now(timezone.utc).isoformat(),
                            "container": NAME, "container_id": item["Id"], "image": IMAGE,
                            "source_snapshot_sha256": snapshot_sha,
                            "single_behavior_change": "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1",
                            "same_treatment_source_and_protocol": True,
                            "physical_npus": [0, 1, 2, 3], "health_passed": True,
                        })
                        print(json.dumps({"container": NAME, "container_id": item["Id"], "health_passed": True}))
                        return
            except Exception:
                pass
            time.sleep(10)
        raise RuntimeError("candidate health timeout")
    except Exception:
        run("docker", "stop", "--time", "60", NAME, check=False)
        raise


def stop() -> None:
    item = inspect()
    if item is None:
        raise RuntimeError("exact candidate container absent")
    exact_identity(item)
    if item["State"]["Status"] == "running":
        run("docker", "stop", "--time", "60", NAME)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if lane_empty() and port_free():
            break
        time.sleep(5)
    else:
        raise RuntimeError("NPU0-3 or port 8223 not released")
    current = inspect()
    if current is None or current["Id"] != item["Id"] or current["State"]["Status"] != "exited":
        raise RuntimeError("candidate identity changed before removal")
    run("docker", "rm", NAME)
    receipt("service-stop.json", {
        "schema": "hypic-matmul-allreduce-service-stop/v1",
        "stopped_at": datetime.now(timezone.utc).isoformat(),
        "container": NAME, "container_id": item["Id"],
        "owned_npus_released": True, "port_released": True, "container_removed": True,
    })
    print(json.dumps({"container": NAME, "owned_npus_released": True,
                      "port_released": True, "container_removed": True}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "stop"))
    args = parser.parse_args()
    if args.action == "start":
        start()
    else:
        stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
