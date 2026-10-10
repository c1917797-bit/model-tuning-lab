#!/usr/bin/env python3
"""Offline-only r17 cap-isolation preflight; device execution is not admitted."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from r16_original_source_full_adapter import SOURCE_COMMIT, configure as configure_r16


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
    if sys.argv[1:] != ["--check"]:
        raise RuntimeError("r17 device run is not admitted; only --check is enabled")
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
            or fingerprint["physical_npus"] != [0, 1, 2, 3]):
        raise RuntimeError("r17 offline invariant drift")
    print(json.dumps({
        "arm": arm,
        "device_run_admitted": False,
        "root": str(quality.QROOT),
        "source_commit": SOURCE_COMMIT,
        "sample_count": len(cases),
        "concurrency": controller.CONCURRENCY,
        "max_output_tokens": controller.MAX_OUTPUT,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
