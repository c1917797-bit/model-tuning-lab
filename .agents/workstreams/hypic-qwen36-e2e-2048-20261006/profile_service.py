#!/usr/bin/env python3
"""Launch or release an isolated dynamic-profiler clone of a frozen HYPIC arm.

The only serving differences are a profile-only artifact path and
PROFILING_MODE=dynamic. This service is diagnostic, not a benchmark arm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


EXPERIMENT = "hypic-qwen36-e2e-2048-20261006"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
PORT = 8223
NAMES = {
    "no-cache": "qwen36_hypic2048_profile_baseline_npu0_3_v1",
    "hypic-only": "qwen36_hypic2048_profile_treatment_npu0_3_v1",
}
SOURCE_NAMES = {
    "no-cache": "/qwen36_hypic2048_baseline_npu0_3_v1",
    "hypic-only": "/qwen36_hypic2048_treatment_npu0_3_v1",
}


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_inspects() -> tuple[Path, dict[str, dict]]:
    path = ROOT / "environment-and-container-snapshot.txt"
    content = path.read_text(encoding="utf-8")
    marker = '[\n    {\n        "Id"'
    if marker not in content:
        raise RuntimeError("original container snapshot is missing")
    values, _ = json.JSONDecoder().raw_decode(content[content.index(marker):])
    if not isinstance(values, list) or len(values) != 2:
        raise RuntimeError("expected exactly two frozen source containers")
    by_name = {value["Name"]: value for value in values}
    if set(by_name) != set(SOURCE_NAMES.values()):
        raise RuntimeError("source container names differ from the frozen experiment")
    return path, by_name


def lane_empty() -> bool:
    output = run("npu-smi", "info").stdout
    return all(f"No running processes found in NPU {index}" in output for index in range(4))


def port_free() -> bool:
    output = run("ss", "-ltn", "sport", f":{PORT}").stdout
    return re.search(rf":{PORT}(?:\s|$)", output, re.M) is None


def inspect(name: str) -> dict | None:
    result = run("docker", "inspect", name, check=False)
    if result.returncode:
        return None
    values = json.loads(result.stdout)
    if len(values) != 1:
        raise RuntimeError(f"{name}: unexpected docker inspect cardinality")
    return values[0]


def exact_profile_identity(item: dict, arm: str) -> None:
    name = NAMES[arm]
    labels = item["Config"]["Labels"]
    env = dict(entry.split("=", 1) for entry in item["Config"]["Env"] if "=" in entry)
    devices = [
        entry["PathOnHost"] for entry in item["HostConfig"]["Devices"]
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]
    if not (
        item["Name"] == f"/{name}"
        and item["Image"] == IMAGE
        and labels.get("hypic.experiment") == EXPERIMENT
        and labels.get("hypic.arm") == f"profile-{arm}"
        and env.get("PROFILING_MODE") == "dynamic"
        and env.get("VLLM_ASCEND_HYPIC_ENABLE") == ("0" if arm == "no-cache" else "1")
        and env.get("VLLM_ASCEND_HYPIC_EVIDENCE_FILE")
        == f"/results/profiles/{arm}/hypic-evidence.jsonl"
        and item["HostConfig"]["CpusetCpus"] == "112-191"
        and devices == [f"/dev/davinci{index}" for index in range(4)]
    ):
        raise RuntimeError(f"{name}: profile container identity mismatch")


def create(arm: str) -> tuple[dict, str]:
    snapshot_path, sources = source_inspects()
    source = sources[SOURCE_NAMES[arm]]
    if source["Image"] != IMAGE or source["HostConfig"]["CpusetCpus"] != "112-191":
        raise RuntimeError("frozen image or CPU set drift")
    if source["Config"]["Labels"].get("hypic.experiment") != EXPERIMENT:
        raise RuntimeError("frozen experiment label drift")
    source_arm = source["Config"]["Labels"].get("hypic.arm")
    if source_arm != arm:
        raise RuntimeError("frozen source arm mismatch")
    if source["HostConfig"]["NetworkMode"] != "host":
        raise RuntimeError("frozen network mode drift")
    device_entries = source["HostConfig"]["Devices"]
    npu_hosts = [entry["PathOnHost"] for entry in device_entries if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
    if npu_hosts != [f"/dev/davinci{index}" for index in range(4)]:
        raise RuntimeError("frozen physical NPU mapping drift")
    if not lane_empty() or not port_free():
        raise RuntimeError("NPU0-3 or port 8223 occupied before profile service")
    if inspect(NAMES[arm]) is not None:
        raise RuntimeError(f"{NAMES[arm]} already exists; refuse duplicate")
    other_arm = "hypic-only" if arm == "no-cache" else "no-cache"
    other = inspect(NAMES[other_arm])
    if other is not None and other["State"]["Status"] == "running":
        raise RuntimeError("other profile arm is running")

    env = dict(entry.split("=", 1) for entry in source["Config"]["Env"] if "=" in entry)
    env["PROFILING_MODE"] = "dynamic"
    env["VLLM_ASCEND_HYPIC_EVIDENCE_FILE"] = f"/results/profiles/{arm}/hypic-evidence.jsonl"
    source_command = source["Config"]["Cmd"]
    if source_command[:2] != ["bash", "-lc"] or len(source_command) != 3:
        raise RuntimeError("frozen serving command shape changed")
    old_path = f"/results/{arm}"
    if source_command[2].count(old_path) != 2:
        raise RuntimeError("expected exactly two source artifact path references")
    command = source_command[2].replace(old_path, f"/results/profiles/{arm}")
    if "--max-model-len 40960" not in command or "--tensor-parallel-size 4" not in command:
        raise RuntimeError("frozen serving command identity changed")

    args = [
        "docker", "create", "--name", NAMES[arm],
        "--label", f"hypic.experiment={EXPERIMENT}",
        "--label", f"hypic.arm=profile-{arm}",
        "--label", "hypic.purpose=diagnostic-only",
        "--network", "host", "--shm-size", str(source["HostConfig"]["ShmSize"]),
        "--cpuset-cpus", "112-191",
    ]
    for entry in device_entries:
        args += ["--device", f"{entry['PathOnHost']}:{entry['PathInContainer']}:{entry['CgroupPermissions']}"]
    for bind in source["HostConfig"]["Binds"]:
        args += ["-v", bind]
    for key, value in sorted(env.items()):
        args += ["-e", f"{key}={value}"]
    args += [IMAGE, "bash", "-lc", command]
    run(*args)
    item = inspect(NAMES[arm])
    if item is None:
        raise RuntimeError("docker create returned but container is absent")
    exact_profile_identity(item, arm)
    return item, sha256(snapshot_path)


def write_receipt(arm: str, name: str, payload: dict) -> None:
    path = ROOT / "profiles" / arm / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def start(arm: str) -> None:
    item, snapshot_sha = create(arm)
    name = NAMES[arm]
    run("docker", "start", name)
    deadline = time.monotonic() + 2400
    try:
        while time.monotonic() < deadline:
            current = inspect(name)
            if current is None or current["State"]["Status"] != "running":
                raise RuntimeError(f"{name}: exited before health")
            try:
                with urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as response:
                    if response.status == 200:
                        write_receipt(arm, "service-start.json", {
                            "schema": "hypic-profile-service-start/v1",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "arm": arm,
                            "container": name,
                            "container_id": item["Id"],
                            "image": IMAGE,
                            "source_snapshot_sha256": snapshot_sha,
                            "profile_mode": "dynamic",
                            "physical_npus": [0, 1, 2, 3],
                            "health_passed": True,
                            "diagnostic_only": True,
                        })
                        print(json.dumps({"container": name, "container_id": item["Id"], "health_passed": True}))
                        return
            except Exception:
                pass
            time.sleep(10)
        raise RuntimeError(f"{name}: health timeout")
    except Exception:
        run("docker", "stop", "--time", "60", name, check=False)
        raise


def stop(arm: str) -> None:
    name = NAMES[arm]
    item = inspect(name)
    if item is None:
        raise RuntimeError(f"{name}: no exact profile container to stop")
    exact_profile_identity(item, arm)
    if item["State"]["Status"] == "running":
        run("docker", "stop", "--time", "60", name)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if lane_empty() and port_free():
            break
        time.sleep(5)
    else:
        raise RuntimeError("NPU0-3 or port 8223 not released after profile stop")
    current = inspect(name)
    if current is None or current["Id"] != item["Id"] or current["State"]["Status"] != "exited":
        raise RuntimeError("profile container changed before removal")
    run("docker", "rm", name)
    write_receipt(arm, "service-stop.json", {
        "schema": "hypic-profile-service-stop/v1",
        "stopped_at": datetime.now(timezone.utc).isoformat(),
        "arm": arm,
        "container": name,
        "container_id": item["Id"],
        "owned_npus_released": True,
        "port_released": True,
        "container_removed": True,
    })
    print(json.dumps({"container": name, "owned_npus_released": True, "port_released": True, "container_removed": True}))


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
