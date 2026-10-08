#!/usr/bin/env python3
"""Offline regression for the prospective six-phase cache10 performance gate."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ["HYPIC_QUALITY_ATTEMPT"] = "hotpath-cache10perf-no-cache-screen"

import audit_hotpath_cache10_matched_performance as audit
import binding_off_quality as quality
import hotpath_cache10_matched_performance as performance


class Cache10PerformanceTests(unittest.TestCase):
    def test_frozen_pair_differs_only_in_enablement_and_evidence_path(self) -> None:
        self.assertEqual(quality.ATTEMPT, "hotpath-cache10perf-no-cache-screen")
        self.assertTrue(performance.pair_seam(quality)["enablement_only"])
        normalized = []
        for arm in ("no-cache", "hypic-only"):
            _, binds, env, command = quality.spec(arm)
            normalized.append(audit.normalized_spec(
                {"serving_binds": binds, "serving_env": env,
                 "serving_command": command}, quality.QROOT, arm))
        self.assertEqual(normalized[0], normalized[1])

    def test_archived_fixed_workload_rows_fit_both_arms(self) -> None:
        archived = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
        for arm in ("no-cache", "hypic-only"):
            with self.subTest(arm=arm):
                values = performance.validate_report(
                    archived / arm / "screen/performance.json", arm)
                self.assertGreater(values["tpot_weighted_ms"], 0)

    def test_corrupt_fixed_output_row_is_rejected(self) -> None:
        source = (Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") /
                  "no-cache/screen/performance.json")
        data = json.loads(source.read_text())
        data["results"][0]["output_tokens"] = 1023
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "performance.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(RuntimeError, "fixed-output rows invalid"):
                performance.validate_report(path, "no-cache")

    def test_missing_full_quality_audit_prevents_live_phase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake_quality = SimpleNamespace(ROOT=Path(directory))
            with self.assertRaisesRegex(RuntimeError, "audit absent"):
                performance.entry_gate(fake_quality)

    def test_prehealth_release_touches_only_proven_owned_container(self) -> None:
        item = {"Id": "exact-id", "State": {"Status": "running"}}
        fake = SimpleNamespace(
            name_for=Mock(return_value="exact-name"),
            inspect=Mock(side_effect=[item, None]),
            owned=Mock(), run=Mock(), write_json=Mock(),
            QROOT=Path("/tmp/unused-cache10-performance-test"))
        performance.cleanup_before_health(fake, "hypic-only", "exact-id")
        fake.owned.assert_called_once_with(item, "hypic-only", "exact-id")
        self.assertEqual(fake.run.call_args_list[0].args,
                         ("docker", "stop", "--time", "30", "exact-id"))
        self.assertEqual(fake.run.call_args_list[1].args,
                         ("docker", "rm", "exact-id"))

    def test_identity_change_prevents_prehealth_cleanup(self) -> None:
        fake = SimpleNamespace(
            name_for=Mock(return_value="exact-name"),
            inspect=Mock(return_value={"Id": "foreign-id"}),
            owned=Mock(), run=Mock(), write_json=Mock(),
            QROOT=Path("/tmp/unused-cache10-performance-test"))
        with self.assertRaisesRegex(RuntimeError, "identity changed"):
            performance.cleanup_before_health(fake, "hypic-only", "exact-id")
        fake.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
