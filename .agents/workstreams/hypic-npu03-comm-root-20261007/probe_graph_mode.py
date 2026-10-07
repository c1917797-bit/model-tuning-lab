#!/usr/bin/env python3
"""One-variable FULL_DECODE_ONLY versus enforce-eager diagnostic on NPU0-3.

Reuses the predecessor's exact service identity and bounded native profiler.
Only the serving --enforce-eager switch differs; this is diagnostic evidence,
not a formal HYPIC performance or quality gate.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORKSTREAMS = HERE.parent
PREDECESSOR = WORKSTREAMS / "hypic-qwen36-e2e-2048-20261006"
ARTIFACT_ROOT = Path("/cache/cch/hypic-npu03-comm-root-20261007")
BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py")
NAMES = {
    "graph-on": "hypic_npu03_graph_control_20261007",
    "eager": "hypic_npu03_eager_probe_20261007",
}
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PREDECESSOR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_commit() -> str:
    return subprocess.run(
        ["git", "-C", "/cache/cch/hypic_vllm_ascend-v0.8.5", "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=tuple(NAMES))
    args = parser.parse_args()
    arm = args.arm
    run_root = ARTIFACT_ROOT / arm
    if (run_root / "profiles" / "no-cache" / "decode").exists():
        raise RuntimeError(f"{run_root}: existing decode capture; refuse overwrite")
    if source_commit() != "3ad0967589304cd8fc4e7cff02f48ecc6125c89f":
        raise RuntimeError("pinned HYPIC source commit drifted")
    run_root.mkdir(parents=True, exist_ok=True)

    service = load_module("hypic_profile_service_for_graph_probe", "profile_service.py")
    capture = load_module("hypic_capture_for_graph_probe", "capture_hypic_profile.py")
    snapshot_path, original_sources = service.source_inspects()
    sources = copy.deepcopy(original_sources)
    source = sources[service.SOURCE_NAMES["no-cache"]]
    if source["Image"] != IMAGE:
        raise RuntimeError("pinned image drifted")
    old_bind = "/cache/cch/hypic-qwen36-e2e-2048-20261006:/results"
    if source["HostConfig"]["Binds"].count(old_bind) != 1:
        raise RuntimeError("frozen output mount differs")
    source["HostConfig"]["Binds"] = [
        f"{run_root}:/results" if item == old_bind else item
        for item in source["HostConfig"]["Binds"]
    ]
    command = source["Config"]["Cmd"]
    if command[:2] != ["bash", "-lc"] or len(command) != 3:
        raise RuntimeError("frozen service command shape differs")
    if arm == "eager":
        command[2] += " --enforce-eager"
    if command[2].count("--enforce-eager") != (1 if arm == "eager" else 0):
        raise RuntimeError("graph-mode switch count differs")

    def frozen_sources():
        return snapshot_path, sources

    service.source_inspects = frozen_sources
    service.ROOT = run_root
    service.NAMES["no-cache"] = NAMES[arm]
    capture.ROOT = run_root
    capture.NAMES["no-cache"] = NAMES[arm]

    manifest = {
        "schema": "hypic-npu03-graph-mode-probe/v1",
        "arm": arm,
        "primary_variable": "--enforce-eager" if arm == "eager" else "none",
        "diagnostic_only": True,
        "physical_npus": [0, 1, 2, 3],
        "source_commit": source_commit(),
        "image": IMAGE,
        "source_snapshot_sha256": sha256(snapshot_path),
        "benchmark_sha256": sha256(BENCHMARK),
        "service_command": command[2],
        "profile_root": str(run_root / "profiles" / "no-cache" / "decode"),
    }
    (run_root / "probe-contract.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    exit_code = 2
    try:
        service.start("no-cache")
        sys.argv = [
            str(PREDECESSOR / "capture_hypic_profile.py"),
            "--arm", "no-cache", "--phase", "decode", "--offline-ranks", "0,2",
        ]
        exit_code = capture.main()
    finally:
        item = service.inspect(NAMES[arm])
        if item is not None:
            service.exact_profile_identity(item, "no-cache")
            service.stop("no-cache")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
