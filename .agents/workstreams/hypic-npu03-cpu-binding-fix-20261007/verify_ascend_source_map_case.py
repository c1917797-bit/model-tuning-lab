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
R13 = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r13-full-hypic")
R13_AUDIT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hotpath-quality-cache10r13-dual-audit.json")
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


def python_source_digest(root: Path) -> dict:
    files = sorted(path for path in root.rglob("*.py") if path.is_file())
    require(bool(files), "HYPIC package Python source absent")
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return {"python_files": len(files), "python_tree_sha256": digest.hexdigest()}


def verify_r13_source(attestation: dict, start: dict, audit: dict) -> None:
    source = python_source_digest(PLUGIN / "hypic_vllm_ascend")
    fingerprint = start["fingerprint"]
    require(attestation["schema"] == "hypic-serving-source-attestation/v1"
            and attestation["container_id"] == start["container_id"]
            and attestation["image"] == fingerprint["image"]
            and attestation["selected_source_commit"] == SOURCE
            and attestation["selected_source_root"] == str(PLUGIN)
            and attestation["container_import_file"]
                == "/opt/hypic/hypic_vllm_ascend/__init__.py"
            and attestation["python_files"] == source["python_files"]
            and attestation["python_tree_sha256"] == source["python_tree_sha256"]
            and f"{PLUGIN}:/source-hypic:ro" in attestation["actual_binds"]
            and isinstance(attestation["actual_command"], list)
            and any("cp -a /source-hypic /opt/hypic" in item
                    and "pip install --no-deps -e /opt/hypic" in item
                    for item in attestation["actual_command"])
            and fingerprint["source_commit"] == SOURCE
            and fingerprint["plugin_source_root"] == str(PLUGIN)
            and fingerprint["physical_npus"] == [0, 1, 2, 3],
            "r13 live source attestation drift")
    require(audit["evidence_valid"] is True
            and audit["candidate"]["source_attestation_sha256"]
                == start["source_attestation_sha256"]
            and audit["candidate"]["container_id"] == start["container_id"]
            and audit["candidate"]["scored_rows"] == 381
            and audit["baseline"]["scored_rows"] == 381
            and audit["candidate"]["correct"] == 219
            and audit["baseline"]["correct"] == 230
            and audit["deployed_quality_decision"] == "REJECT_OR_QUALIFY"
            and audit["strict_c1_c2_hot_coverage"]["decision"] == "FAIL"
            and audit["strict_c1_c2_hot_coverage"]["four_worker_verified_scored_requests"] == 368
            and audit["strict_c1_c2_hot_coverage"]["expected_scored_requests"] == 381
            and audit["paper_c3_decision"] == "not-implemented",
            "r13 bounded pair/source decision drift")


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
    case_record = json.loads(
        (HERE / "skill-cases/ascend-source-map.json").read_text(encoding="utf-8"))
    controller_receipt = next(
        item for item in case_record["evidence"]
        if item["path"].endswith("/binding_off_quality.py"))
    controller = checked(HERE / "binding_off_quality.py",
                         controller_receipt["sha256"]).decode()
    require("frozen_plugin_mount" in controller
            and 'sorted(item["HostConfig"]["Binds"]) == sorted(binds)' in controller
            and "selected_plugin_source()" in controller
            and "source_attestation_sha256" in controller,
            "controller source-bind enforcement drift")
    r13_start = json.loads(checked(R13 / "hypic-only/service-start.json",
        "99249b282c99f33f2e224287cba9319695ede3233f2f396e9f335eefaf514201"))
    attestation_path = (R13 / "hypic-only" /
        f"source-attestation.{r13_start['container_id'][:12]}.json")
    r13_attestation_bytes = checked(attestation_path,
        "d2169d9b36561aa59c1fdcded08df9c98f7fee6a145e7aca1290986c1a92a687")
    require(r13_start["source_attestation_sha256"] ==
            hashlib.sha256(r13_attestation_bytes).hexdigest()
            and (R13 / "hypic-only/source-attestation.json").read_bytes()
                == r13_attestation_bytes,
            "r13 attestation/start or alias drift")
    checked(R13 / "arm-result.json",
        "f4ef1e4f3c2367b41121a6f49209d4d229adaa8eecdb52b050cfad1ebc97329a")
    r13_audit = json.loads(checked(R13_AUDIT,
        "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"))
    verify_r13_source(json.loads(r13_attestation_bytes), r13_start, r13_audit)
    case = (HERE / "ASCEND_SOURCE_MAP_CASE_20261009.md").read_text()
    for boundary in ("Status: **partial-evidence**", "No implemented serving seam",
                     "did **not** retain", "not a new NPU run",
                     "r13 serving-source attestation", "prospective source-map gate",
                     "REJECT_OR_QUALIFY"):
        require(boundary in case, f"case boundary absent: {boundary}")
    print(json.dumps({"schema": "ascend-source-map-real-task-case/v1",
        "tested_main": MAIN, "plugin_commit": SOURCE,
        "source_mount_controller_checked": True,
        "r12_raw_independent_bind_receipt_retained": False,
        "r13_actual_bind_and_python_digest_verified": True,
        "r13_full_2048_pair_complete": True,
        "c3_implemented": False, "long_term_acceptance": "partial-evidence"},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
