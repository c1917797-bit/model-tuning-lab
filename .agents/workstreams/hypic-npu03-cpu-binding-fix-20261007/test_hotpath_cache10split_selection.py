#!/usr/bin/env python3
"""Offline regression for the proposed exact-ID split; never starts a service."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SHARD0 = set(range(53)) | {54, 55, 56}
PROBE = """
import json
import sys
sys.path.insert(0, sys.argv[1])
import hotpath_quality_full as hotpath
items, _ = hotpath.cases()
fingerprint = hotpath.quality.preflight()
print(json.dumps({
    "ids": [item["index"] for item in items],
    "attempt": hotpath.quality.ATTEMPT,
    "root_exists": hotpath.quality.QROOT.exists(),
    "physical_npus": fingerprint["physical_npus"],
    "gpu_memory_utilization": fingerprint["gpu_memory_utilization"],
    "material_cache_max_mb": fingerprint["material_cache_max_mb"],
    "max_materialized_segments": fingerprint["max_materialized_segments"],
}))
"""


def probe(arm: str, shard: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "HYPIC_HOTPATH_QUALITY_CAMPAIGN": "cache10split",
        "HYPIC_HOTPATH_QUALITY_ARM": arm,
        "HYPIC_HOTPATH_QUALITY_MODE": "full",
        "HYPIC_HOTPATH_QUALITY_SHARD": shard,
    })
    return subprocess.run(
        [sys.executable, "-B", "-c", PROBE, str(HERE)],
        cwd=HERE, env=env, text=True, capture_output=True, check=False,
    )


class SplitSelectionTests(unittest.TestCase):
    def test_exact_partition_and_frozen_service_identity(self) -> None:
        outputs = {}
        for arm, shard in (("no-cache", "0"), ("no-cache", "1"),
                           ("hypic-only", "1")):
            result = probe(arm, shard)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs[arm, shard] = json.loads(result.stdout)
            self.assertFalse(outputs[arm, shard]["root_exists"])
            self.assertEqual(outputs[arm, shard]["physical_npus"], [0, 1, 2, 3])
            self.assertEqual(outputs[arm, shard]["gpu_memory_utilization"], 0.85)
            self.assertEqual(outputs[arm, shard]["material_cache_max_mb"], 3584)
            self.assertEqual(outputs[arm, shard]["max_materialized_segments"], 10)
        self.assertEqual(set(outputs["no-cache", "0"]["ids"]), SHARD0)
        shard1 = set(range(127)) - SHARD0
        self.assertEqual(set(outputs["no-cache", "1"]["ids"]), shard1)
        self.assertEqual(outputs["no-cache", "1"]["ids"],
                         outputs["hypic-only", "1"]["ids"])
        self.assertEqual(len(SHARD0 | shard1), 127)
        self.assertFalse(SHARD0 & shard1)
        self.assertEqual(
            outputs["no-cache", "0"]["attempt"],
            "hotpath-cache10split-baseline-shard0",
        )
        self.assertEqual(
            outputs["no-cache", "1"]["attempt"],
            "hotpath-cache10split-baseline-shard1",
        )
        self.assertEqual(
            outputs["hypic-only", "1"]["attempt"],
            "hotpath-cache10split-hypic-shard1",
        )

    def test_candidate_shard0_is_not_rerun(self) -> None:
        result = probe("hypic-only", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized hot-path quality campaign/arm/mode",
                      result.stderr)

    def test_unapproved_run_fails_before_service_or_root_creation(self) -> None:
        env = os.environ.copy()
        env.update({
            "HYPIC_HOTPATH_QUALITY_CAMPAIGN": "cache10split",
            "HYPIC_HOTPATH_QUALITY_ARM": "no-cache",
            "HYPIC_HOTPATH_QUALITY_MODE": "full",
            "HYPIC_HOTPATH_QUALITY_SHARD": "0",
        })
        env.pop("HYPIC_HOTPATH_SPLIT_USER_APPROVED", None)
        result = subprocess.run(
            [sys.executable, "-B", str(HERE / "hotpath_quality_full.py")],
            cwd=HERE, env=env, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require explicit user method approval", result.stderr)
        self.assertFalse(
            (HERE.parents[3] / "hypic-npu03-cpu-binding-fix-20261007" /
             "quality-context-41984-hotpath-cache10split-baseline-shard0").exists()
        )


if __name__ == "__main__":
    unittest.main()
