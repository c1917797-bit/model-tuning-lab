#!/usr/bin/env python3
"""Replay the immutable pre-health environmental-failure receipts for retry20."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry20"
)
EXPECTED = {
    "contract.json": "58ab99d5742582a6e66b256844324742480dc882bff77edf91910711796c750f",
    "arm-result.json": "8a5c6cdbda2344615dae10f14e10bfcc36924c6b567004311aebcdb4a58f9046",
    "hypic-only/hypic-evidence.jsonl": "7c94c68175fa496a766ca9c5670787c0680a81bcc1798b29f0ed01ab9f51ba59",
    "hypic-only/lane-guard.json": "4efe09fe5750e112356e6029fad68e712358f993f9474bd58035720492b72690",
    "hypic-only/pre-health-release.json": "c184f1d0af692b0b93b3deaef12cc4a49c3269f0dae66141d522ef11a6135576",
}
FOREIGN_CONTAINER = "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
OWNED_CONTAINER = "ea9357cfc3af46cc01a413bf9d0392e368b5381e9436899e3bcff2d7f7df74cc"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing receipt: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"hash mismatch: {relative}: {actual}")

    if not errors:
        arm = read_json(ROOT / "arm-result.json")
        guard = read_json(ROOT / "hypic-only/lane-guard.json")
        release = read_json(ROOT / "hypic-only/pre-health-release.json")

        if arm.get("arm") != "hypic-only" or arm.get("phase") != "repeat3":
            errors.append("arm-result identity mismatch")
        if arm.get("valid") is not False or arm.get("metrics") is not None:
            errors.append("attempt must remain invalid and unmeasured")
        if arm.get("performance_sha256") is not None:
            errors.append("unexpected performance receipt")
        if arm.get("container_id") != OWNED_CONTAINER:
            errors.append("owned container identity mismatch")
        if guard.get("samples") != 36 or guard.get("probe_errors") != []:
            errors.append("guard sample/error summary mismatch")
        if guard.get("expected_worker_pids") != []:
            errors.append("workers unexpectedly started")
        foreign = guard.get("foreign", [])
        captured = [
            process
            for event in foreign
            for process in event.get("processes", [])
        ]
        if not any(
            process.get("pid") == 1890601
            and process.get("physical_npu") == 3
            and process.get("container_id") == FOREIGN_CONTAINER
            for process in captured
        ):
            errors.append("expected foreign physical NPU3 process not recorded")
        if guard.get("owned_container_id") != OWNED_CONTAINER:
            errors.append("guard owned-container identity mismatch")
        if release.get("container_id") != OWNED_CONTAINER:
            errors.append("release container identity mismatch")
        if release.get("container_removed") is not True:
            errors.append("exact owned container removal not proven")
        if release.get("worker_release_proven") is not False:
            errors.append("unexpected worker-release claim")

    if errors:
        print("RETRY20_ENVIRONMENTAL_AUDIT=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RETRY20_ENVIRONMENTAL_AUDIT=PASS")
    print("classification=pre-health external physical NPU3 interference; zero measured performance")
    print("guard_samples=36; probe_errors=0; scored_requests=0; exact_owned_cleanup=true")
    print("foreign_pid=1890601; physical_npu=3; human_owner=unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
