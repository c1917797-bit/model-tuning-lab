#!/usr/bin/env python3
"""Test whether successful Ascend CPU binding causes the NPU0-3 Decode floor.

Compare with the pinned profiled graph-on control. The only serving variable is
--additional-config '{"enable_cpu_binding":false}'. No image files or host CPU
affinity settings are modified; physical NPU0-3 only.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PREDECESSOR = HERE.parent / "hypic-qwen36-e2e-2048-20261006"
ROOT = Path("/cache/cch/hypic-npu03-comm-root-20261007/binding-off")
NAME = "hypic_npu03_bindingoff_20261007"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
SOURCE_SHA = "c88cd60f6929d1596f3553b68f31de506f5d60c2401429aa5cd819418ac40ad4"
BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py")
BENCHMARK_SHA = "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822"
HYPIC_COMMIT = "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"
FLAG = " --additional-config '{\"enable_cpu_binding\":false}'"


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
    service = load("hypic_bindingoff_service", PREDECESSOR / "profile_service.py")
    capture = load("hypic_bindingoff_capture", PREDECESSOR / "capture_hypic_profile.py")
    snapshot, original_sources = service.source_inspects()
    if sha256(snapshot) != SOURCE_SHA:
        raise RuntimeError("frozen source snapshot drifted")
    sources = copy.deepcopy(original_sources)
    source = sources[service.SOURCE_NAMES["no-cache"]]
    if source["Image"] != IMAGE or source["HostConfig"]["CpusetCpus"] != "112-191":
        raise RuntimeError("frozen image/cpuset drifted")
    visible = [entry for entry in source["Config"]["Env"] if entry.startswith("ASCEND_RT_VISIBLE_DEVICES=")]
    physical = [entry["PathOnHost"] for entry in source["HostConfig"]["Devices"] if entry["PathOnHost"].startswith("/dev/davinci") and entry["PathOnHost"] != "/dev/davinci_manager"]
    if visible != ["ASCEND_RT_VISIBLE_DEVICES=0,1,2,3"] or physical != [f"/dev/davinci{i}" for i in range(4)]:
        raise RuntimeError("physical device mapping drifted")
    command = source["Config"]["Cmd"]
    if command[:2] != ["bash", "-lc"] or len(command) != 3 or "--additional-config" in command[2] or "--enforce-eager" in command[2]:
        raise RuntimeError("frozen graph-on command drifted")
    old_mount = "/cache/cch/hypic-qwen36-e2e-2048-20261006:/results"
    if source["HostConfig"]["Binds"].count(old_mount) != 1:
        raise RuntimeError("frozen artifact mount drifted")
    source["HostConfig"]["Binds"] = [f"{ROOT}:/results" if item == old_mount else item for item in source["HostConfig"]["Binds"]]
    command[2] += FLAG
    if command[2].count("enable_cpu_binding") != 1:
        raise RuntimeError("binding switch count differs")

    def frozen_sources():
        return snapshot, sources

    service.source_inspects = frozen_sources
    service.ROOT = ROOT
    service.NAMES["no-cache"] = NAME
    capture.ROOT = ROOT
    capture.NAMES["no-cache"] = NAME
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
        "schema": "hypic-npu03-binding-off-probe/v1",
        "diagnostic_only": True,
        "primary_variable": FLAG.strip(),
        "physical_npus": [0, 1, 2, 3],
        "cpuset_cpus": "112-191",
        "image": IMAGE,
        "source_snapshot_sha256": sha256(snapshot),
        "benchmark_sha256": sha256(BENCHMARK),
        "source_commit": commit,
        "service_command": command[2],
        "control_root": "/cache/cch/hypic-npu03-comm-root-20261007/graph-on",
        "profile_root": str(ROOT / "profiles" / "no-cache" / "decode"),
        "abort": "occupied NPU0-3 or port 8223, drift, invalid outputs, or owned cleanup failure",
    }
    (ROOT / "probe-contract.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    code = 2
    try:
        service.start("no-cache")
        item = service.inspect(NAME)
        if item is None or item["Config"]["Cmd"][2].count("enable_cpu_binding") != 1:
            raise RuntimeError("binding-off activation command not present")
        sys.argv = [str(PREDECESSOR / "capture_hypic_profile.py"), "--arm", "no-cache", "--phase", "decode", "--offline-ranks", "0,2"]
        code = capture.main()
    finally:
        item = service.inspect(NAME)
        if item is not None:
            service.exact_profile_identity(item, "no-cache")
            service.stop("no-cache")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
