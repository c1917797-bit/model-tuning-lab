#!/usr/bin/env python3
"""Replay the immutable pre-health environmental-failure receipts for retry18."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry18"
)
EXPECTED = {
    "contract.json": "c03c8fdf79ffe02ed42ee2e80558479e372b2be0959128795e83c6dbe7dd322a",
    "arm-result.json": "c0bd15e0a0a6340e338bcbf05a5f4791139d747589ad63b1351cb67f198bd4bc",
    "hypic-only/lane-guard.json": "6ae72bebd66aba903dd9f8bfebf90561374bd2699363428268b97d4f498f553b",
    "hypic-only/pre-health-release.json": "413c9d8d3b2af629b5c6732c0eeba857299ea28794d9245d8ae2b2a365a5048c",
    "hypic-only/hypic-evidence.jsonl": "26eaf6cda31342ba6742045a15ca34039c0d3598dad61a2508cbcdb8400e568c",
}
FOREIGN_CONTAINER = "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"


def validate() -> dict:
    for rel, expected in EXPECTED.items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"{rel}: immutable receipt hash mismatch")

    result = json.loads((ROOT / "arm-result.json").read_text())
    guard = json.loads((ROOT / "hypic-only/lane-guard.json").read_text())
    release = json.loads((ROOT / "hypic-only/pre-health-release.json").read_text())
    foreign = [
        process
        for sample in guard.get("foreign", [])
        for process in sample.get("processes", [])
    ]
    owned_id = result.get("container_id")
    if not (
        result.get("valid") is False
        and result.get("phase") == "repeat3"
        and result.get("metrics") is None
        and result.get("performance_sha256") is None
        and "lane guard" in str(result.get("error", "")).lower()
        and guard.get("samples") == 80
        and guard.get("probe_errors") == []
        and any(
            item.get("physical_npu") == 1
            and item.get("pid") == 1420898
            and item.get("container_id") == FOREIGN_CONTAINER
            for item in foreign
        )
        and release.get("container_removed") is True
        and release.get("container_id") == owned_id
        and release.get("worker_release_proven") is False
    ):
        raise RuntimeError("retry18 does not match the frozen environmental-failure boundary")

    forbidden = (
        "hypic-only/service-start.json",
        "hypic-only/benchmark-command.json",
        "performance.json",
    )
    if any((ROOT / rel).exists() for rel in forbidden):
        raise RuntimeError("retry18 unexpectedly contains health/scored-performance artifacts")
    own_container = subprocess.run(
        ["docker", "inspect", owned_id],
        capture_output=True,
        text=True,
        check=False,
    )
    if own_container.returncode == 0:
        raise RuntimeError("retry18-owned container still exists")

    return {
        "classification": "environmental-pre-health-failure",
        "foreign_physical_npu": 1,
        "foreign_pid": 1420898,
        "foreign_container_id": FOREIGN_CONTAINER,
        "guard_samples": 80,
        "probe_errors": 0,
        "scored_requests": 0,
        "performance_metric_valid": False,
        "owned_container_removed": True,
        "worker_release_proven_by_controller": False,
        "immutable_receipts_verified": len(EXPECTED),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
