#!/usr/bin/env python3
"""Prospective bounded HYPIC-on source comparison; not a quality acceptance run."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
BASE_CONTROLLER_SHA256 = "8ee34e61635731038df4312763ca2cac72b31578980a24539ca442fe7979c06d"
BASE_SERVICE_SHA256 = "714012b683142201fc4cf40d734f4d48f53210d7ade93479bf550e27020db0c4"
SOURCES = {
    "original": (
        "/cache/cch/hypic_vllm_ascend-r15-original",
        "3ad0967589304cd8fc4e7cff02f48ecc6125c89f",
    ),
    "current": (
        "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008",
        "c12060cd47e7575ead059983d7a8bb4704165c98",
    ),
}
# Chosen from immutable r13 outcomes before r15 launch: two neutral length
# controls, four strongly regressed samples, and two improved controls.
INDEXES = (55, 6, 30, 40, 49, 26, 50, 48)
TOKENS = (10352, 15683, 11036, 24608, 16739, 25585, 27771, 39642)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure(source: str):
    if source not in SOURCES:
        raise RuntimeError("r15 source must be original or current")
    if (_sha(HERE / "hotpath_quality_full.py") != BASE_CONTROLLER_SHA256
            or _sha(HERE / "binding_off_quality.py") != BASE_SERVICE_SHA256):
        raise RuntimeError("historical controller/service bytes drifted")
    source_root, source_commit = SOURCES[source]
    os.environ["HYPIC_HOTPATH_QUALITY_CAMPAIGN"] = "cache10r13"
    os.environ["HYPIC_HOTPATH_QUALITY_MODE"] = "full"
    os.environ["HYPIC_HOTPATH_QUALITY_ARM"] = "hypic-only"
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = source_root
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = source_commit
    import hotpath_quality_full as controller

    quality = controller.quality
    if (controller.CAMPAIGN != "cache10r13" or controller.MODE != "full"
            or controller.REPETITIONS != 3 or controller.CONCURRENCY != 8
            or quality.IMAGE != "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"):
        raise RuntimeError("historical controller import identity drift")
    attempt = f"hotpath-cache10r15-source-{source}"
    root_name = f"quality-context-41984-{attempt}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r15 attempt collides with historical controller")
    quality.ATTEMPT_ROOTS[attempt] = root_name
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / root_name
    quality.EXPERIMENT = f"hypic-npu03-source-lineage-20261010-{source}"
    controller.CAMPAIGN = "cache10r15"
    controller.MODE = "source-lineage"
    controller.CONCURRENCY = 8
    original_cases = controller.cases

    def selected_cases():
        items, evaluator = original_cases()
        selected = [items[index] for index in INDEXES]
        if (tuple(item["index"] for item in selected) != INDEXES
                or tuple(item["prompt_tokens"] for item in selected) != TOKENS):
            raise RuntimeError("r15 preregistered sample identity drift")
        return selected, evaluator

    controller.cases = selected_cases
    return controller


if __name__ == "__main__":
    selected_source = os.environ.get("HYPIC_R15_SOURCE", "")
    configured = configure(selected_source)
    if sys.argv[1:] == ["--check"]:
        print(json.dumps({
            "source": selected_source, "root": str(configured.quality.QROOT),
            "commit": SOURCES[selected_source][1], "sample_indexes": INDEXES,
            "concurrency": configured.CONCURRENCY,
            "max_output_tokens": configured.MAX_OUTPUT,
        }, sort_keys=True))
        raise SystemExit(0)
    if sys.argv[1:]:
        raise RuntimeError("unsupported r15 argument")
    raise SystemExit(configured.main())
