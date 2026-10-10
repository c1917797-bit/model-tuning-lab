#!/usr/bin/env python3
"""Offline-only contract regression for the repaired-source r19 GSM8K pair."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).resolve().parent


def child(code: str, arm: str = "no-cache") -> dict:
    env = os.environ.copy()
    env["HYPIC_R19_GSM8K_ARM"] = arm
    run = subprocess.run(
        [sys.executable, "-c", code], cwd=HERE, env=env,
        capture_output=True, text=True, timeout=30, check=True)
    return json.loads(run.stdout)


class R19Gsm8kOfflineTest(unittest.TestCase):
    def test_both_arms_keep_repaired_source_and_full_ruler(self) -> None:
        code = (
            "import json,os,r19_c32_gsm8k_adapter as a;"
            "p=a.check_preregistration();"
            "q=a.configure(os.environ['HYPIC_R19_GSM8K_ARM']);"
            "f=q.preflight();"
            "print(json.dumps({'root':str(q.QROOT),'source':f['source_commit'],"
            "'image':f['image'],'npus':f['physical_npus'],"
            "'units':f['unit_order'],'cache_mb':f['material_cache_max_mb'],"
            "'segments':f['max_materialized_segments'],"
            "'max_output':f['max_output_tokens'],"
            "'dataset':f['datasets']['gsm8k']['sha256']}))"
        )
        prereg = json.loads((HERE / "HYPIC_R19_GSM8K_PHASE_PREREGISTRATION_20261010.json")
                            .read_text(encoding="utf-8"))
        for arm in ("no-cache", "hypic-only"):
            with self.subTest(arm=arm):
                actual = child(code, arm)
                self.assertEqual(actual["root"], prereg["arm_roots"][arm])
                self.assertEqual(actual["source"], prereg["source_commit"])
                self.assertEqual(actual["image"], prereg["image"])
                self.assertEqual(actual["npus"], [0, 1, 2, 3])
                self.assertEqual(actual["units"],
                                 [["gsm8k", 1], ["gsm8k", 2], ["gsm8k", 3]])
                self.assertEqual(actual["cache_mb"], 3584)
                self.assertEqual(actual["segments"], 10)
                self.assertEqual(actual["max_output"], 2048)
                self.assertEqual(actual["dataset"], prereg["dataset_sha256"])

    def test_auditor_checks_pair_seam_and_1319_frozen_samples(self) -> None:
        actual = child(
            "import json,r19_c32_gsm8k_audit as a;"
            "print(json.dumps({'seam':a.pair_seam(),"
            "'samples':len(a.frozen_samples())}))")
        self.assertEqual(actual["seam"]["only_treatment_switch"], ["0", "1"])
        self.assertTrue(actual["seam"]["normalized_commands_equal"])
        self.assertTrue(actual["seam"]["binds_equal"])
        self.assertEqual(actual["samples"], 1319)

    def test_auditor_refuses_missing_raw_root(self) -> None:
        actual = child(
            "import json;from pathlib import Path;"
            "import r19_c32_gsm8k_audit as a;"
            "missing=Path('/cache/cch/hypic-r19-gsm8k-definitely-absent');"
            "result='unexpected-pass';"
            "\ntry:a.audit_arm(missing,'no-cache',[],None)"
            "\nexcept RuntimeError as e:result=str(e)"
            "\nprint(json.dumps({'result':result}))")
        self.assertIn("root absent", actual["result"])


if __name__ == "__main__":
    unittest.main()
