#!/usr/bin/env python3
"""Read-only replay of the bounded HYPIC exact-main source-map case."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PLUGIN = Path("/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008")
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r12-stress-hypic/hypic-only")
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
SOURCE = "c12060cd47e7575ead059983d7a8bb4704165c98"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=cwd, text=True,
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr)
    return result.stdout.strip()


def checked(path: Path, digest: str) -> bytes:
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == digest,
            f"evidence SHA256 drift: {path}")
    return data


def main() -> int:
    skill = ".agents/skills/ascend-source-map/SKILL.md"
    require(git(REPO, "rev-parse", "origin/main") == MAIN, "main moved")
    require(git(REPO, "rev-parse", f"{MAIN}:{skill}") ==
            "7aac2fc220ef5191b0de224615fc2cb17de347ce", "main Skill drift")
    require(git(REPO, "rev-parse", f"HEAD:{skill}") ==
            "7aac2fc220ef5191b0de224615fc2cb17de347ce", "branch Skill drift")
    require(git(REPO, "rev-parse", f"{MAIN}:.agents/skills.registry.yaml") ==
            "2611864bbcf719d57920aae03ff9eb85521526b4", "registry drift")
    require(git(PLUGIN, "rev-parse", "HEAD") == SOURCE, "plugin HEAD drift")
    require(not git(PLUGIN, "status", "--porcelain"), "plugin worktree dirty")
    for path, symbols in {
        "hypic_vllm_ascend/ingress.py": ("parse_segment_ends",),
        "hypic_vllm_ascend/segmenter.py": ("hash_segment",),
        "hypic_vllm_ascend/transition.py": ("compose_state_torch",),
        "hypic_vllm_ascend/patches/gdn.py": ("_position_independent_gdn_core",),
        "hypic_vllm_ascend/position_independent.py":
            ("_ready_segment_entry", "_select_materializations",
             "_commit_materializations", "schedule_position_independent"),
        "hypic_vllm_ascend/cache.py": ("class SegmentCache",),
        "hypic_vllm_ascend/material.py": ("class MaterializedSegmentStore",),
        "hypic_vllm_ascend/patches/scheduler.py": ("_apply_materialization_report",),
        "hypic_vllm_ascend/seam.py": ("hit_seam_positions",),
        "hypic_vllm_ascend/patches/attention.py":
            ("_repair_position_independent_kv", "_forward_position_independent_attention"),
        "tests/test_evicted_directory_rebuild.py": ("_commit_materializations",),
    }.items():
        source = git(PLUGIN, "show", f"{SOURCE}:{path}")
        require(all(symbol in source for symbol in symbols),
                f"source seam drift: {path}")
    start = json.loads(checked(RAW / "service-start.json",
        "5cb01c734f77476b820e0484170c048ca1dcdd1917ec09abf04099be4bfda076"))
    require(start["fingerprint"]["source_commit"] == SOURCE
            and start["fingerprint"]["plugin_source_root"] == str(PLUGIN)
            and start["fingerprint"]["physical_npus"] == [0, 1, 2, 3],
            "r12 source/physical lane receipt drift")
    log = checked(RAW / "service.full.7d083aa3a096.log",
        "6d70834a456f91a4ae5b34577805c296f8500e11c2569302d321ccb88efe02a1").decode()
    require(log.count("module=/opt/hypic/hypic_vllm_ascend/__init__.py") >= 6
            and "paper_missing=C3.1,C3.2,C3.3,C3.4,C3.5,C3.6" in log,
            "runtime import or C3 boundary drift")
    controller = checked(HERE / "binding_off_quality.py",
        "b533ca4513d9b80e53ac3e2def8667f1aec01f86f73c1ffa7bf38755e2b8276f").decode()
    require("frozen_plugin_mount" in controller
            and 'sorted(item["HostConfig"]["Binds"]) == sorted(binds)' in controller
            and "selected_plugin_source()" in controller,
            "controller source-bind enforcement drift")
    case = (HERE / "ASCEND_SOURCE_MAP_CASE_20261009.md").read_text()
    for boundary in ("Status: **partial-evidence**", "No implemented serving seam",
                     "did **not** retain", "not a new NPU run",
                     "not a complete source-to-binary attestation"):
        require(boundary in case, f"case boundary absent: {boundary}")
    print(json.dumps({"schema": "ascend-source-map-real-task-case/v1",
        "tested_main": MAIN, "plugin_commit": SOURCE,
        "source_mount_controller_checked": True,
        "raw_independent_bind_receipt_retained": False,
        "c3_implemented": False, "long_term_acceptance": "partial-evidence"},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
