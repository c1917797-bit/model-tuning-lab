#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("verify_physical_v12.py")
SPEC = importlib.util.spec_from_file_location("verify_physical_v12_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence(pids: range = range(1, 5)) -> list[dict]:
    rows: list[dict] = [{"event": "heterogeneous_cache_grouped", "pid": 99}]
    for pid in pids:
        rows.extend(
            [
                {
                    "event": "physical_cache_bound",
                    "pid": pid,
                    "compact_page_bytes": 64,
                    "dense_page_bytes": 128,
                    "num_blocks": 1,
                },
                {"event": "tp_geometry_aligned", "pid": pid},
                {"event": "worker_dispatch_verified", "pid": pid},
            ]
        )
    return rows


def canary() -> dict:
    stopped = lambda content: {
        "content": content,
        "finish_reason": "stop",
        "reasoning_content": None,
    }
    return {
        "schema": "mst.dasc.physical-canary/v1",
        "short": stopped("OK"),
        "runs": [stopped("VERIFIED") for _ in range(3)],
        "variant": stopped("ASCEND"),
        "metrics_before": {"vllm:prefix_cache_hits_total": 0},
        "metrics_after": {"vllm:prefix_cache_hits_total": 3},
        "ok": True,
    }


class PhysicalV12VerifierTest(unittest.TestCase):
    def test_recomputes_positive_verdict(self) -> None:
        result = MODULE.canary_verdict(canary(), evidence())
        self.assertTrue(result["ok"])
        self.assertEqual(result["prefix_cache_hit_delta"], 3)

    def test_rejects_reported_success_with_bad_raw_evidence(self) -> None:
        rows = evidence()
        for row in rows:
            if row.get("event") == "worker_dispatch_verified":
                row["pid"] += 10
        result = MODULE.canary_verdict(canary(), rows)
        self.assertFalse(result["ok"])
        self.assertTrue(result["reported_ok"])

    def test_rejects_non_exact_output(self) -> None:
        value = canary()
        value["short"]["content"] = "OK\n"
        self.assertFalse(MODULE.canary_verdict(value, evidence())["ok"])

    def test_manifest_detects_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "payload.txt"
            payload.write_text("trusted\n", encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = root / "manifest.sha256"
            manifest.write_text(f"{digest}  {payload}\n", encoding="utf-8")
            self.assertTrue(MODULE.verify_manifest(manifest, root)["ok"])
            payload.write_text("tampered\n", encoding="utf-8")
            self.assertFalse(MODULE.verify_manifest(manifest, root)["ok"])


if __name__ == "__main__":
    unittest.main()
