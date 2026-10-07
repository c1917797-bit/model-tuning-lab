#!/usr/bin/env python3
"""Diagnostic cpuset swap on physical NPU0-3; never a formal HYPIC gate.

Control is the 2026-10-07 graph-on profile. Only the isolated service
container cpuset changes from 112-191 to 96-175 (80 CPUs in each arm).
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PREDECESSOR = HERE.parent / "hypic-qwen36-e2e-2048-20261006"
ROOT = Path("/cache/cch/hypic-npu03-comm-root-20261007/cpuset96-175")
NAME = "hypic_npu03_cpuset96175_20261007"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
SOURCE_SHA = "c88cd60f6929d1596f3553b68f31de506f5d60c2401429aa5cd819418ac40ad4"
BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py")
BENCHMARK_SHA = "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822"
HYPIC_COMMIT = "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    profile_root = ROOT / "profiles" / "no-cache" / "decode"
    if ROOT.exists():
        raise RuntimeError(f"{ROOT} already exists; refuse overwrite")
    if sha256(BENCHMARK) != BENCHMARK_SHA:
        raise RuntimeError("benchmark bytes drifted")
    commit = subprocess.run(
        ["git", "-C", "/cache/cch/hypic_vllm_ascend-v0.8.5", "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if commit != HYPIC_COMMIT:
        raise RuntimeError("HYPIC source commit drifted")
    service = load("hypic_cpuset_service", PREDECESSOR / "profile_service.py")
    capture = load("hypic_cpuset_capture", PREDECESSOR / "capture_hypic_profile.py")
    snapshot, sources = service.source_inspects()
    source = copy.deepcopy(sources[service.SOURCE_NAMES["no-cache"]])
    if sha256(snapshot) != SOURCE_SHA or source["Image"] != IMAGE:
        raise RuntimeError("frozen source snapshot or image drifted")
    if source["HostConfig"]["CpusetCpus"] != "112-191":
        raise RuntimeError("frozen cpuset drifted")
    devices = source["HostConfig"]["Devices"]
    physical = [entry["PathOnHost"] for entry in devices if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
    if physical != [f"/dev/davinci{i}" for i in range(4)]:
        raise RuntimeError("physical NPU mapping differs from 0-3")
    if "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3" not in source["Config"]["Env"]:
        raise RuntimeError("visible device order drifted")
    if source["HostConfig"]["NetworkMode"] != "host":
        raise RuntimeError("frozen network mode drifted")
    command = source["Config"]["Cmd"]
    if command[:2] != ["bash", "-lc"] or len(command) != 3 or "--enforce-eager" in command[2]:
        raise RuntimeError("frozen graph-on command drifted")
    old_mount = "/cache/cch/hypic-qwen36-e2e-2048-20261006:/results"
    if source["HostConfig"]["Binds"].count(old_mount) != 1:
        raise RuntimeError("frozen artifact mount drifted")

    def exact(item: dict, arm: str) -> None:
        env = dict(entry.split("=", 1) for entry in item["Config"]["Env"] if "=" in entry)
        actual = [entry["PathOnHost"] for entry in item["HostConfig"]["Devices"] if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
        if not (
            arm == "no-cache" and item["Name"] == f"/{NAME}" and item["Image"] == IMAGE
            and item["HostConfig"]["CpusetCpus"] == "96-175"
            and actual == physical and env.get("PROFILING_MODE") == "dynamic"
            and env.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3"
            and env.get("VLLM_ASCEND_HYPIC_ENABLE") == "0"
            and item["Config"]["Labels"].get("hypic.arm") == "profile-no-cache"
        ):
            raise RuntimeError("cpuset probe container identity mismatch")

    def create(arm: str):
        if arm != "no-cache" or not service.lane_empty() or not service.port_free():
            raise RuntimeError("NPU0-3 or port 8223 occupied")
        if service.inspect(NAME) is not None:
            raise RuntimeError("exact probe container already exists")
        env = dict(entry.split("=", 1) for entry in source["Config"]["Env"] if "=" in entry)
        env["PROFILING_MODE"] = "dynamic"
        env["VLLM_ASCEND_HYPIC_EVIDENCE_FILE"] = "/results/profiles/no-cache/hypic-evidence.jsonl"
        script = command[2].replace("/results/no-cache", "/results/profiles/no-cache")
        if script == command[2]:
            raise RuntimeError("frozen output-path references absent")
        args = [
            "docker", "create", "--name", NAME,
            "--label", f"hypic.experiment={service.EXPERIMENT}",
            "--label", "hypic.arm=profile-no-cache",
            "--label", "hypic.purpose=cpuset-diagnostic-only",
            "--network", "host", "--shm-size", str(source["HostConfig"]["ShmSize"]),
            "--cpuset-cpus", "96-175",
        ]
        for entry in devices:
            args += ["--device", f"{entry['PathOnHost']}:{entry['PathInContainer']}:{entry['CgroupPermissions']}"]
        for bind in source["HostConfig"]["Binds"]:
            args += ["-v", f"{ROOT}:/results" if bind == old_mount else bind]
        for key, value in sorted(env.items()):
            args += ["-e", f"{key}={value}"]
        args += [IMAGE, "bash", "-lc", script]
        service.run(*args)
        item = service.inspect(NAME)
        if item is None:
            raise RuntimeError("docker create returned without owned container")
        exact(item, arm)
        return item, sha256(snapshot)

    def inspect_capture(arm: str):
        item = service.inspect(NAME)
        if item is None or item["State"]["Status"] != "running":
            raise RuntimeError("owned probe service is not running")
        exact(item, arm)
        return item, dict(entry.split("=", 1) for entry in item["Config"]["Env"] if "=" in entry)

    service.ROOT = ROOT
    service.NAMES["no-cache"] = NAME
    service.create = create
    service.exact_profile_identity = exact
    capture.ROOT = ROOT
    capture.NAMES["no-cache"] = NAME
    capture.inspect_container = inspect_capture
    original_export = capture.offline_export
    original_summarize = capture.summarize_rank

    def bounded_export(name: str, arm: str, phase: str, rank: int):
        path = ROOT / "profiles" / arm / phase / f"rank{rank}" / "msprof"
        raw_bytes = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        if raw_bytes > 1_500_000_000:
            return {"passed": False, "skipped": "raw rank exceeds 1.5 GB", "raw_bytes": raw_bytes}
        return original_export(name, arm, phase, rank)

    def bounded_summarize(path: Path):
        files = [item for item in path.rglob("*") if item.is_file()]
        large = [item for item in files if item.name.startswith("msprof_") and item.suffix == ".json" and item.stat().st_size > 500_000_000]
        if large:
            return {"complete": False, "file_count": len(files), "bounded_skip": "JSON exceeds 500 MB; no whole-file parse"}
        return original_summarize(path)

    capture.offline_export = bounded_export
    capture.summarize_rank = bounded_summarize
    ROOT.mkdir(parents=True)
    contract = {
        "schema": "hypic-npu03-cpuset-probe/v1",
        "diagnostic_only": True,
        "primary_variable": "docker --cpuset-cpus 112-191 -> 96-175; constant 80 CPUs",
        "physical_npus": [0, 1, 2, 3],
        "image": IMAGE,
        "source_snapshot_sha256": sha256(snapshot),
        "benchmark_sha256": sha256(BENCHMARK),
        "source_commit": commit,
        "service_command": command[2],
        "profile_root": str(profile_root),
        "control_root": "/cache/cch/hypic-npu03-comm-root-20261007/graph-on",
        "abort": "occupied NPU0-3 or port 8223, drift, invalid outputs, or owned cleanup failure",
    }
    (ROOT / "probe-contract.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    code = 2
    try:
        service.start("no-cache")
        sys.argv = [str(PREDECESSOR / "capture_hypic_profile.py"), "--arm", "no-cache", "--phase", "decode", "--offline-ranks", "0,2"]
        code = capture.main()
    finally:
        item = service.inspect(NAME)
        if item is not None:
            exact(item, "no-cache")
            service.stop("no-cache")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
