#!/usr/bin/env python3
"""Paired 2048-token quality services with an independent 41984 context identity."""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from profile_service import IMAGE, ROOT, lane_empty, port_free, run, sha256, source_inspects


CONTEXT = 41984
EXPERIMENT = "hypic-qwen36-quality2048-context41984-20261006"
QROOT = ROOT / "quality-context-41984"
SOURCE_ROOT = Path("/cache/cch/hypic_vllm_ascend-v0.8.5")
SOURCE_COMMIT = "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"
NAMES = {
    "no-cache": "qwen36_hypic2048_quality41984_baseline_npu0_3_v1",
    "hypic-only": "qwen36_hypic2048_quality41984_treatment_npu0_3_v1",
}
SOURCE_NAMES = {
    "no-cache": "/qwen36_hypic2048_baseline_npu0_3_v1",
    "hypic-only": "/qwen36_hypic2048_treatment_npu0_3_v1",
}


def inspect(name: str) -> dict | None:
    response = run("docker", "inspect", name, check=False)
    if response.returncode:
        return None
    values = json.loads(response.stdout)
    if len(values) != 1:
        raise RuntimeError("unexpected Docker inspect cardinality")
    return values[0]


def frozen_spec(arm: str) -> tuple[dict, dict[str, str], list[str], str]:
    snapshot_path, sources = source_inspects()
    source = sources[SOURCE_NAMES[arm]]
    if not (
        source["Image"] == IMAGE
        and source["HostConfig"]["CpusetCpus"] == "112-191"
        and source["HostConfig"]["NetworkMode"] == "host"
        and source["Config"]["Labels"].get("hypic.experiment") == "hypic-qwen36-e2e-2048-20261006"
        and source["Config"]["Labels"].get("hypic.arm") == arm
    ):
        raise RuntimeError("frozen source identity drift")
    devices = [entry["PathOnHost"] for entry in source["HostConfig"]["Devices"]
               if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
    if devices != [f"/dev/davinci{index}" for index in range(4)]:
        raise RuntimeError("frozen NPU0-3 mapping drift")
    if run("git", "-C", str(SOURCE_ROOT), "rev-parse", "HEAD").stdout.strip() != SOURCE_COMMIT:
        raise RuntimeError("HYPIC source commit drift")
    if run("git", "-C", str(SOURCE_ROOT), "diff", "--quiet", "--", "hypic_vllm_ascend", check=False).returncode:
        raise RuntimeError("HYPIC package source drift")
    if run("git", "-C", str(SOURCE_ROOT), "ls-files", "--others", "--exclude-standard", "--", "hypic_vllm_ascend").stdout.strip():
        raise RuntimeError("HYPIC package has untracked source")
    env = dict(value.split("=", 1) for value in source["Config"]["Env"] if "=" in value)
    if env.get("VLLM_ASCEND_HYPIC_ENABLE") != ("0" if arm == "no-cache" else "1"):
        raise RuntimeError("frozen HYPIC arm switch drift")
    if "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE" in env:
        raise RuntimeError("quality service must not inherit the fusion candidate")
    env["VLLM_ASCEND_HYPIC_EVIDENCE_FILE"] = f"/results/quality-context-41984/{arm}/hypic-evidence.jsonl"
    source_command = source["Config"]["Cmd"]
    if source_command[:2] != ["bash", "-lc"] or len(source_command) != 3:
        raise RuntimeError("frozen command shape drift")
    command = source_command[2]
    old_path = f"/results/{arm}"
    if (command.count(old_path) != 2 or command.count("--max-model-len 40960") != 1
            or command.count("--max-num-batched-tokens 40960") != 1
            or "--tensor-parallel-size 4" not in command):
        raise RuntimeError("frozen command content drift")
    command = command.replace(old_path, f"/results/quality-context-41984/{arm}")
    command = command.replace("--max-model-len 40960", f"--max-model-len {CONTEXT}")
    command = command.replace("--max-num-batched-tokens 40960", f"--max-num-batched-tokens {CONTEXT}")
    return source, env, ["bash", "-lc", command], sha256(snapshot_path)


def exact_identity(item: dict, arm: str) -> None:
    source, expected_env, command, _ = frozen_spec(arm)
    env = dict(value.split("=", 1) for value in item["Config"]["Env"] if "=" in value)
    devices = [(entry["PathOnHost"], entry["PathInContainer"], entry["CgroupPermissions"])
               for entry in item["HostConfig"]["Devices"]]
    expected_devices = [(entry["PathOnHost"], entry["PathInContainer"], entry["CgroupPermissions"])
                        for entry in source["HostConfig"]["Devices"]]
    labels = item["Config"]["Labels"]
    if not (
        item["Name"] == f"/{NAMES[arm]}"
        and item["Image"] == IMAGE
        and labels.get("hypic.experiment") == EXPERIMENT
        and labels.get("hypic.arm") == arm
        and labels.get("hypic.purpose") == "paired-quality-2048"
        and env == expected_env
        and item["Config"]["Cmd"] == command
        and item["HostConfig"]["CpusetCpus"] == "112-191"
        and item["HostConfig"]["NetworkMode"] == "host"
        and sorted(item["HostConfig"]["Binds"]) == sorted(source["HostConfig"]["Binds"])
        and item["HostConfig"]["ShmSize"] == source["HostConfig"]["ShmSize"]
        and devices == expected_devices
    ):
        raise RuntimeError("quality container is not the exact paired-context derivative")


def receipt(arm: str, name: str, data: dict) -> None:
    path = QROOT / arm / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def start(arm: str) -> None:
    name = NAMES[arm]
    existing = inspect(name)
    if existing is not None:
        exact_identity(existing, arm)
        if existing["State"]["Status"] != "created":
            raise RuntimeError("quality container exists but is not an unstarted exact candidate")
    if not lane_empty() or not port_free():
        raise RuntimeError("NPU0-3 or port 8223 occupied before quality service")
    other = inspect(NAMES["hypic-only" if arm == "no-cache" else "no-cache"])
    if other is not None and other["State"]["Status"] == "running":
        raise RuntimeError("the other quality arm is still running")
    source, env, command, snapshot_sha = frozen_spec(arm)
    if existing is None:
        args = ["docker", "create", "--name", name,
                "--label", f"hypic.experiment={EXPERIMENT}",
                "--label", f"hypic.arm={arm}",
                "--label", "hypic.purpose=paired-quality-2048",
                "--network", "host", "--shm-size", str(source["HostConfig"]["ShmSize"]),
                "--cpuset-cpus", "112-191"]
        for entry in source["HostConfig"]["Devices"]:
            args += ["--device", f"{entry['PathOnHost']}:{entry['PathInContainer']}:{entry['CgroupPermissions']}"]
        for bind in source["HostConfig"]["Binds"]:
            args += ["-v", bind]
        for key, value in sorted(env.items()):
            args += ["-e", f"{key}={value}"]
        run(*args)
    item = inspect(name)
    if item is None:
        raise RuntimeError("quality container absent after create")
    exact_identity(item, arm)
    run("docker", "start", name)
    deadline = time.monotonic() + 2400
    try:
        while time.monotonic() < deadline:
            current = inspect(name)
            if current is None or current["State"]["Status"] != "running":
                raise RuntimeError("quality container exited before health")
            try:
                with urlopen("http://127.0.0.1:8223/health", timeout=5) as response:
                    if response.status == 200:
                        receipt(arm, "service-start.json", {
                            "schema": "hypic-quality-context-service-start/v1",
                            "started_at": datetime.now(timezone.utc).isoformat(),
                            "arm": arm, "container": name, "container_id": item["Id"],
                            "image": IMAGE, "source_snapshot_sha256": snapshot_sha,
                            "max_model_len": CONTEXT, "max_num_batched_tokens": CONTEXT,
                            "physical_npus": [0, 1, 2, 3], "health_passed": True,
                        })
                        print(json.dumps({"arm": arm, "container": name, "health_passed": True}), flush=True)
                        return
            except Exception:
                pass
            time.sleep(10)
        raise RuntimeError("quality service health timeout")
    except Exception:
        run("docker", "stop", "--time", "60", name, check=False)
        raise


def stop(arm: str) -> None:
    name = NAMES[arm]
    item = inspect(name)
    if item is None:
        raise RuntimeError("exact quality container is absent")
    exact_identity(item, arm)
    if item["State"]["Status"] == "running":
        run("docker", "stop", "--time", "60", name)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if lane_empty() and port_free():
            break
        time.sleep(5)
    else:
        raise RuntimeError("NPU0-3 or port 8223 not released")
    current = inspect(name)
    if (current is None or current["Id"] != item["Id"]
            or current["State"]["Status"] not in ("exited", "created")):
        raise RuntimeError("quality container identity changed before removal")
    run("docker", "rm", name)
    receipt(arm, "service-stop.json", {
        "schema": "hypic-quality-context-service-stop/v1",
        "stopped_at": datetime.now(timezone.utc).isoformat(),
        "arm": arm, "container": name, "container_id": item["Id"],
        "owned_npus_released": True, "port_released": True, "container_removed": True,
    })
    print(json.dumps({"arm": arm, "container": name, "owned_npus_released": True,
                      "port_released": True, "container_removed": True}), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "stop"))
    parser.add_argument("--arm", choices=tuple(NAMES), required=True)
    args = parser.parse_args()
    if args.action == "start":
        start(args.arm)
    else:
        stop(args.arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
