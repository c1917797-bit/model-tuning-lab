#!/usr/bin/env python3
"""Offline admission for a diagnostic c1 subset; never a full quality rerun."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class R14VariabilitySelectionTests(unittest.TestCase):
    def test_two_arms_have_one_fixed_three_sample_denominator(self) -> None:
        results = {}
        for arm in ("no-cache", "hypic-only"):
            env = {**os.environ, "PYTHONPATH": str(HERE),
                   "HYPIC_R14_ARM": arm}
            code = (
                "import json, os, r14_variability_adapter as a; "
                "h=a.configure(os.environ['HYPIC_R14_ARM']); "
                "items, _ = h.cases(); "
                "print(json.dumps({'indexes':[x['index'] for x in items], "
                "'tokens':[x['prompt_tokens'] for x in items], "
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
        self.assertEqual(base["indexes"], [0, 55, 48])
        self.assertEqual(base["indexes"], cand["indexes"])
        self.assertEqual(base["tokens"], [24616, 10352, 39642])
        self.assertEqual(base["tokens"], cand["tokens"])
        self.assertEqual(base["boundaries"], cand["boundaries"])
        for arm, item in results.items():
            suffix = "baseline" if arm == "no-cache" else "hypic"
            name = f"hotpath-cache10r14-variability-{suffix}"
            self.assertEqual(item["attempt"], name)
            self.assertEqual(item["root"], f"quality-context-41984-{name}")
            self.assertEqual(item["repetitions"], 3)
            self.assertEqual(item["concurrency"], 1)
            self.assertEqual(item["max_output"], 2048)
            self.assertTrue(item["reserved"])


if __name__ == "__main__":
    unittest.main()
