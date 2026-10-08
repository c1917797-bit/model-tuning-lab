#!/usr/bin/env python3
"""Offline guard for the full r13 paired 127x3 explicit-boundary ruler."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class R13FullSelectionTests(unittest.TestCase):
    def test_both_full_arms_keep_one_matched_denominator(self) -> None:
        results = {}
        for arm in ("no-cache", "hypic-only"):
            env = {**os.environ, "PYTHONPATH": str(HERE),
                   "HYPIC_HOTPATH_QUALITY_CAMPAIGN": "cache10r13",
                   "HYPIC_HOTPATH_QUALITY_ARM": arm,
                   "HYPIC_HOTPATH_QUALITY_MODE": "full",
                   "HYPIC_QUALITY_PLUGIN_REPO":
                       "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008",
                   "HYPIC_QUALITY_PLUGIN_COMMIT":
                       "c12060cd47e7575ead059983d7a8bb4704165c98"}
            code = (
                "import json, hotpath_quality_full as h; "
                "items, _ = h.cases(); "
                "print(json.dumps({'indexes':[x['index'] for x in items], "
                "'boundaries':[x['boundary'] for x in items], "
                "'attempt':h.quality.ATTEMPT, 'root':h.quality.QROOT.name, "
                "'repetitions':h.REPETITIONS, 'concurrency':h.CONCURRENCY, "
                "'max_output':h.MAX_OUTPUT, "
                "'reserved':h.quality.ATTEMPT in h.quality.RESERVE_ATTEMPTS}))"
            )
            process = subprocess.run(
                [sys.executable, "-B", "-c", code], cwd=HERE, env=env,
                capture_output=True, text=True, check=True)
            results[arm] = json.loads(process.stdout)
        base, cand = results["no-cache"], results["hypic-only"]
        self.assertEqual(base["indexes"], list(range(127)))
        self.assertEqual(base["indexes"], cand["indexes"])
        self.assertEqual(base["boundaries"], cand["boundaries"])
        self.assertTrue(all(value >= 4096 for value in base["boundaries"]))
        for arm, result in results.items():
            suffix = "baseline" if arm == "no-cache" else "hypic"
            self.assertEqual(result["attempt"], f"hotpath-cache10r13-full-{suffix}")
            self.assertEqual(result["root"],
                             f"quality-context-41984-hotpath-cache10r13-full-{suffix}")
            self.assertEqual(result["repetitions"], 3)
            self.assertEqual(result["concurrency"], 8)
            self.assertEqual(result["max_output"], 2048)
            self.assertTrue(result["reserved"])


if __name__ == "__main__":
    unittest.main()
