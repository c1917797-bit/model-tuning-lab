#!/usr/bin/env python3
"""Replay immutable pre-health environmental-failure receipts for retry19."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry19")
OWNED_ID = "2e92362738a88715789c8bb291fbc0d162a8dde19576529a25668e6a62c23973"
FOREIGN_ID = "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
EXPECTED = {
    "contract.json": "fe59917a8ddf62cb538e7a5e9ef30d63d2eae8d14fd5f3798a495211d303b8f9",
    "arm-result.json": "25cce108c805d785d4ac01b092990bafced2a3409667cdf1fa2813d572d78506",
    "hypic-only/lane-guard.json": "f4d59b8e9553aa1b526af1e3d6b9e03d5e9a6b90cb9175c9f14f1958eeee91e5",
    "hypic-only/pre-health-release.json": "e938b1a0e99c76d281bf781909bc4392b853f3af424c3a33f925f54125ae59e7",
    "hypic-only/hypic-evidence.jsonl": "9df31bb84fa849c581e7815390e9e120b8fcb2ff2152050463b1c9db9ad15ffd",
}

def validate() -> dict:
    for rel, expected in EXPECTED.items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"{rel}: immutable receipt hash mismatch")
    result = json.loads((ROOT / "arm-result.json").read_text())
    guard = json.loads((ROOT / "hypic-only/lane-guard.json").read_text())
    release = json.loads((ROOT / "hypic-only/pre-health-release.json").read_text())
    foreign = [p for sample in guard.get("foreign", []) for p in sample.get("processes", [])]
    if not (result.get("valid") is False and result.get("phase") == "repeat3"
            and result.get("metrics") is None and result.get("performance_sha256") is None
            and "lane guard" in str(result.get("error", "")).lower()
            and guard.get("samples") == 46 and guard.get("probe_errors") == []
            and any(p.get("physical_npu") == 2 and p.get("pid") == 1731309
                    and p.get("container_id") == FOREIGN_ID for p in foreign)
            and release.get("container_removed") is True
            and release.get("container_id") == OWNED_ID
            and release.get("worker_release_proven") is False):
        raise RuntimeError("retry19 does not match the frozen environmental-failure boundary")
    forbidden = ("hypic-only/service-start.json", "hypic-only/benchmark-command.json", "performance.json")
    if any((ROOT / rel).exists() for rel in forbidden):
        raise RuntimeError("retry19 unexpectedly contains health/scored-performance artifacts")
    evidence = (ROOT / "hypic-only/hypic-evidence.jsonl").read_text()
    if "benchmark_request" in evidence or "scored_response" in evidence:
        raise RuntimeError("retry19 unexpectedly contains scored-request evidence")
    if subprocess.run(["docker", "inspect", OWNED_ID], capture_output=True, check=False).returncode == 0:
        raise RuntimeError("retry19-owned service container still exists")
    return {"classification": "environmental-pre-health-isolation-failure", "foreign_physical_npu": 2,
            "foreign_pid": 1731309, "foreign_container_id": FOREIGN_ID, "guard_samples": 46,
            "probe_errors": 0, "scored_requests": 0, "performance_metric_valid": False,
            "owned_container_removed": True, "worker_release_proven_by_controller": False,
            "immutable_receipts_verified": len(EXPECTED)}

if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
