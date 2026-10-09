#!/usr/bin/env python3
"""Isolated r14 diagnostic adapter around immutable historical controllers."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_CONTROLLER_SHA256 = "8ee34e61635731038df4312763ca2cac72b31578980a24539ca442fe7979c06d"
BASE_SERVICE_SHA256 = "714012b683142201fc4cf40d734f4d48f53210d7ade93479bf550e27020db0c4"
SOURCE_REPO = "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008"
SOURCE_COMMIT = "c12060cd47e7575ead059983d7a8bb4704165c98"
INDEXES = (0, 55, 48)
TOKENS = (24616, 10352, 39642)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(arm: str):
    if arm not in {"no-cache", "hypic-only"}:
        raise RuntimeError("r14 arm must be no-cache or hypic-only")
    if (_sha(HERE / "hotpath_quality_full.py") != BASE_CONTROLLER_SHA256
            or _sha(HERE / "binding_off_quality.py") != BASE_SERVICE_SHA256):
        raise RuntimeError("historical quality controller/source hash drift")
    # Import only a known historical controller; all r14 changes stay in memory.
    os.environ["HYPIC_HOTPATH_QUALITY_CAMPAIGN"] = "cache10r13"
    os.environ["HYPIC_HOTPATH_QUALITY_MODE"] = "full"
    os.environ["HYPIC_HOTPATH_QUALITY_ARM"] = arm
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE_REPO
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = SOURCE_COMMIT
    import hotpath_quality_full as controller

    quality = controller.quality
    if (controller.CAMPAIGN != "cache10r13" or controller.MODE != "full"
            or controller.REPETITIONS != 3 or controller.CONCURRENCY != 8
            or quality.IMAGE != "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"):
        raise RuntimeError("historical controller import identity drift")
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"hotpath-cache10r14-variability-{suffix}"
    root_name = f"quality-context-41984-{attempt}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r14 attempt unexpectedly exists in historical controller")
    quality.ATTEMPT_ROOTS[attempt] = root_name
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / root_name
    quality.EXPERIMENT = f"hypic-npu03-bindingoff-quality41984-20261007-{attempt}"
    controller.CAMPAIGN = "cache10r14"
    controller.MODE = "variability"
    controller.CONCURRENCY = 1
    original_cases = controller.cases

    def selected_cases():
        items, evaluator = original_cases()
        selected = [items[index] for index in INDEXES]
        if (tuple(item["index"] for item in selected) != INDEXES
                or tuple(item["prompt_tokens"] for item in selected) != TOKENS):
            raise RuntimeError("r14 predeclared sample identity drift")
        return selected, evaluator

    controller.cases = selected_cases
    return controller


if __name__ == "__main__":
    raise SystemExit(configure(os.environ.get("HYPIC_R14_ARM", "")).main())
