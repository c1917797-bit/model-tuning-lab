#!/usr/bin/env python3
"""Fresh full max-2048 quality pair on known-good historical HYPIC source."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
BASE_CONTROLLER_SHA256 = "8ee34e61635731038df4312763ca2cac72b31578980a24539ca442fe7979c06d"
BASE_SERVICE_SHA256 = "714012b683142201fc4cf40d734f4d48f53210d7ade93479bf550e27020db0c4"
SOURCE_ROOT = "/cache/cch/hypic_vllm_ascend-r15-original"
SOURCE_COMMIT = "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(arm: str):
    if arm not in {"no-cache", "hypic-only"}:
        raise RuntimeError("r16 arm must be no-cache or hypic-only")
    if (_sha(HERE / "hotpath_quality_full.py") != BASE_CONTROLLER_SHA256
            or _sha(HERE / "binding_off_quality.py") != BASE_SERVICE_SHA256):
        raise RuntimeError("historical controller/service bytes drifted")
    os.environ["HYPIC_HOTPATH_QUALITY_CAMPAIGN"] = "cache10r13"
    os.environ["HYPIC_HOTPATH_QUALITY_MODE"] = "full"
    os.environ["HYPIC_HOTPATH_QUALITY_ARM"] = arm
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE_ROOT
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = SOURCE_COMMIT
    import hotpath_quality_full as controller

    quality = controller.quality
    if (controller.CAMPAIGN != "cache10r13" or controller.MODE != "full"
            or controller.REPETITIONS != 3 or controller.CONCURRENCY != 8
            or quality.IMAGE != "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"):
        raise RuntimeError("historical controller import identity drift")
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"hotpath-cache10r16-full-{suffix}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r16 attempt collides with historical controller")
    quality.ATTEMPT_ROOTS[attempt] = f"quality-context-41984-{attempt}"
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / quality.ATTEMPT_ROOTS[attempt]
    quality.EXPERIMENT = f"hypic-npu03-original-full-20261010-{suffix}"
    controller.CAMPAIGN = "cache10r16"
    return controller


if __name__ == "__main__":
    arm = os.environ.get("HYPIC_R16_ARM", "")
    controller = configure(arm)
    if sys.argv[1:] == ["--check"]:
        print(json.dumps({
            "arm": arm, "root": str(controller.quality.QROOT),
            "source_commit": SOURCE_COMMIT,
            "max_output_tokens": controller.MAX_OUTPUT,
            "concurrency": controller.CONCURRENCY,
            "sample_count": len(controller.cases()[0]),
        }, sort_keys=True))
        raise SystemExit(0)
    if sys.argv[1:]:
        raise RuntimeError("unsupported r16 argument")
    raise SystemExit(controller.main())
