#!/usr/bin/env python3
"""Frozen r17 cap-isolation adapter with hash-checked device admission."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import sys

from r16_original_source_full_adapter import SOURCE_COMMIT, configure as configure_r16


HERE = Path(__file__).resolve().parent
PREREG = HERE / "HYPIC_R17_CAP1024_PREREGISTRATION_20261010.json"


def check_preregistration() -> dict:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    if (prereg.get("schema") != "hypic-r17-cap1024-preregistration/v1"
            or prereg.get("source_commit") != SOURCE_COMMIT
            or prereg.get("physical_npus") != [0, 1, 2, 3]
            or prereg.get("sample_count") != 127
            or prereg.get("repetitions") != 3
            or prereg.get("concurrency") != 8
            or prereg.get("max_output_tokens") != 1024):
        raise RuntimeError("r17 preregistration identity drift")
    files = prereg.get("file_sha256", {})
    expected = {"r17_cap1024_offline_adapter.py", "audit_r17_cap1024_full.py",
                "hotpath_quality_audit.py", "hotpath_quality_full.py",
                "binding_off_quality.py", "r16_original_source_full_adapter.py"}
    if set(files) != expected:
        raise RuntimeError("r17 preregistration file set drift")
    for name, digest in files.items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"r17 preregistered file drift: {name}")
    return prereg


def configure(arm: str):
    controller = configure_r16(arm)
    quality = controller.quality
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"hotpath-cache10r17-cap1024-full-{suffix}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r17 attempt collides with an existing controller")
    quality.ATTEMPT_ROOTS[attempt] = f"quality-context-41984-{attempt}"
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / quality.ATTEMPT_ROOTS[attempt]
    quality.EXPERIMENT = f"hypic-npu03-original-cap1024-20261010-{suffix}"
    controller.CAMPAIGN = "cache10r17-cap1024"
    controller.MAX_OUTPUT = 1024

    base_preflight = quality.preflight

    def cap1024_preflight() -> dict:
        fingerprint = base_preflight()
        if fingerprint.get("max_output_tokens") != 2048:
            raise RuntimeError("base service fingerprint output cap drift")
        fingerprint["max_output_tokens"] = 1024
        return fingerprint

    quality.preflight = cap1024_preflight
    return controller


def main() -> int:
    if sys.argv[1:] not in (["--check"], ["--run"]):
        raise RuntimeError("r17 requires --check or --run")
    prereg = check_preregistration()
    arm = os.environ.get("HYPIC_R17_ARM", "")
    controller = configure(arm)
    quality = controller.quality
    if Path(quality.QROOT).exists():
        raise RuntimeError("r17 result root already exists")
    cases, _ = controller.cases()
    fingerprint = quality.preflight()
    if (len(cases) != 127 or controller.CONCURRENCY != 8
            or controller.REPETITIONS != 3 or controller.MAX_OUTPUT != 1024
            or fingerprint["source_commit"] != SOURCE_COMMIT
            or fingerprint["max_output_tokens"] != 1024
            or fingerprint["physical_npus"] != [0, 1, 2, 3]
            or fingerprint["image"] != prereg["image"]
            or fingerprint["model_index_sha256"] != prereg["model_index_sha256"]
            or fingerprint["evaluator_sha256"] != prereg["evaluator_sha256"]
            or fingerprint["datasets"]["longbenchv2"]["sha256"]
                != prereg["dataset_sha256"]):
        raise RuntimeError("r17 offline invariant drift")
    if str(quality.QROOT) != prereg["arm_roots"][arm]:
        raise RuntimeError("r17 preregistered root drift")
    if sys.argv[1:] == ["--run"]:
        return controller.main()
    print(json.dumps({
        "arm": arm,
        "preregistration_valid": True,
        "device_run_started": False,
        "root": str(quality.QROOT),
        "source_commit": SOURCE_COMMIT,
        "sample_count": len(cases),
        "concurrency": controller.CONCURRENCY,
        "max_output_tokens": controller.MAX_OUTPUT,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
