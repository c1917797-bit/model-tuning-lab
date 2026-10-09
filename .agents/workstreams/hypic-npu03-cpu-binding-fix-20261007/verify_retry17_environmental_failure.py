#!/usr/bin/env python3
"""Replay the immutable pre-health environmental-failure receipts for retry17."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry17"
)
EXPECTED = {
    "contract.json": "78065f257df89c1eb032b22f4372d5a21793b97084657b8ea56324cca7cc7d22",
    "arm-result.json": "04c59278c0720e531e88dc0936a4b4a04f991ed178bf9e06472045dd14b49e46",
    "hypic-only/lane-guard.json": "f0276d28026a9b7da0218db46093521aa70be4077d2c77c9f0654f7011b168b6",
    "hypic-only/pre-health-release.json": "bb665f2c1afa4db4f3eb5acd143c79fdf0cb44e16e646ccfdce6f6feeaf63898",
    "hypic-only/hypic-evidence.jsonl": "4105a55809328e22620da7e8f1a68a1bf96ea1326039e7c335e00e90f0570251",
}
FOREIGN_CONTAINER = "87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa"


def validate() -> dict:
    for rel, expected in EXPECTED.items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"{rel}: immutable receipt hash mismatch")

    result = json.loads((ROOT / "arm-result.json").read_text())
    guard = json.loads((ROOT / "hypic-only/lane-guard.json").read_text())
    release = json.loads((ROOT / "hypic-only/pre-health-release.json").read_text())
    foreign = [item for sample in guard.get("foreign", [])
               for item in sample.get("processes", [])]
    if not (
        result.get("valid") is False
        and result.get("metrics") is None
        and result.get("performance_sha256") is None
        and "lane guard" in str(result.get("error", "")).lower()
        and guard.get("samples") == 26
        and guard.get("probe_errors") == []
        and any(item.get("physical_npu") == 0
                and item.get("pid") == 1198578
                and item.get("container_id") == FOREIGN_CONTAINER
                for item in foreign)
        and release.get("container_removed") is True
        and release.get("container_id") == result.get("container_id")
        and release.get("worker_release_proven") is False
    ):
        raise RuntimeError("retry17 does not match the frozen environmental-failure boundary")
    forbidden = ("hypic-only/service-start.json",
                 "hypic-only/benchmark-command.json", "performance.json")
    if any((ROOT / rel).exists() for rel in forbidden):
        raise RuntimeError("retry17 unexpectedly contains health/scored-performance artifacts")
    container = subprocess.run(
        ["docker", "inspect", result["container_id"]],
        capture_output=True, text=True, check=False,
    )
    if container.returncode == 0:
        raise RuntimeError("retry17-owned container still exists")
    return {
        "classification": "environmental-pre-health-failure",
        "foreign_physical_npu": 0,
        "foreign_pid": 1198578,
        "foreign_container_id": FOREIGN_CONTAINER,
        "guard_samples": 26,
        "probe_errors": 0,
        "scored_requests": 0,
        "performance_metric_valid": False,
        "owned_container_removed": True,
        "worker_release_proven_by_controller": False,
        "immutable_receipts_verified": len(EXPECTED),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
