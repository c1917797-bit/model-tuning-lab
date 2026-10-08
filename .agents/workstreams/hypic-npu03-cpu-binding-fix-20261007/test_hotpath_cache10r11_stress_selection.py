#!/usr/bin/env python3
"""Offline regression for the frozen r11/r12 c8 diagnostic stress identities."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class R11StressSelectionTests(unittest.TestCase):
    def test_frozen_stress_selection_and_service_settings(self) -> None:
        for campaign in ("cache10r11", "cache10r12"):
            with self.subTest(campaign=campaign):
                self._assert_campaign(campaign)

    def _assert_campaign(self, campaign: str) -> None:
        env = os.environ.copy()
        env.update({
            "PYTHONPATH": str(HERE),
            "HYPIC_HOTPATH_QUALITY_CAMPAIGN": campaign,
            "HYPIC_HOTPATH_QUALITY_ARM": "hypic-only",
            "HYPIC_HOTPATH_QUALITY_MODE": "stress",
        })
        code = (
            "import json, hotpath_quality_full as h; "
            "items, _ = h.cases(); "
            "print(json.dumps({'indexes':[x['index'] for x in items], "
            "'attempt':h.quality.ATTEMPT, 'root':h.quality.QROOT.name, "
            "'repetitions':h.REPETITIONS, 'concurrency':h.CONCURRENCY, "
            "'max_output':h.MAX_OUTPUT, "
            "'reserved':h.quality.ATTEMPT in h.quality.RESERVE_ATTEMPTS}))"
        )
        process = subprocess.run(
            [sys.executable, "-B", "-c", code], cwd=HERE, env=env,
            capture_output=True, text=True, check=True,
        )
        result = json.loads(process.stdout)
        self.assertEqual(result["indexes"], [*range(75, 92), 107, 111])
        self.assertEqual(result["attempt"], f"hotpath-{campaign}-stress-hypic")
        self.assertEqual(result["root"],
                         f"quality-context-41984-hotpath-{campaign}-stress-hypic")
        self.assertEqual(result["repetitions"], 3)
        self.assertEqual(result["concurrency"], 8)
        self.assertEqual(result["max_output"], 2048)
        self.assertTrue(result["reserved"])


if __name__ == "__main__":
    unittest.main()
