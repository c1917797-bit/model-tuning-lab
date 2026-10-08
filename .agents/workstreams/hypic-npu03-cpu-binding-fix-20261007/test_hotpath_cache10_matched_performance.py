#!/usr/bin/env python3
"""Offline regression for the prospective six-phase cache10 performance gate."""

import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ["HYPIC_QUALITY_ATTEMPT"] = "hotpath-cache10perf-no-cache-screen"

import audit_hotpath_cache10_matched_performance as audit
import binding_off_quality as quality
import hotpath_cache10_matched_performance as performance


class Cache10PerformanceTests(unittest.TestCase):
    def test_r13_entry_gate_requires_current_dual_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def digest(path: Path) -> str:
                return hashlib.sha256(path.read_bytes()).hexdigest()
            items = {}
            for arm, suffix in (("no-cache", "baseline"),
                                ("hypic-only", "hypic")):
                attempt = root / f"quality-context-41984-hotpath-cache10r13-full-{suffix}"
                attempt.mkdir()
                (attempt / "contract.json").write_text("{}")
                (attempt / "arm-result.json").write_text("{}")
                items["baseline" if arm == "no-cache" else "candidate"] = {
                    "scored_rows": 381,
                    "contract_sha256": digest(attempt / "contract.json"),
                    "arm_result_sha256": digest(attempt / "arm-result.json"),
                    "fingerprint": {
                        "source_commit": performance.SOURCE_COMMIT,
                        "gpu_memory_utilization": 0.85,
                        "material_cache_max_mb": 3584,
                        "max_materialized_segments": 10,
                    },
                }
            receipt = {
                "evidence_valid": True,
                "pair_seam": {"normalized_commands_equal": True},
                "source_commit": performance.SOURCE_COMMIT,
                "strict_c1_c2_hot_coverage": {"expected_scored_requests": 381},
                **items,
            }
            path = root / performance.QUALITY_AUDIT
            path.write_text(json.dumps(receipt))
            fake = SimpleNamespace(ROOT=root, sha256=digest)
            self.assertEqual(performance.entry_gate(fake), digest(path))
            receipt["source_commit"] = "wrong-source"
            path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(RuntimeError, "not independently valid"):
                performance.entry_gate(fake)

    def test_startup_guard_precedes_service_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "phase"
            events = []
            class Guard:
                def __init__(self, arm, workers, owned_container_id):
                    self.started = False
                    self.workers = workers
                    self.owned_container_id = owned_container_id
                def start(self):
                    self.started = True
                    events.append("guard-start")
                def set_expected_workers(self, workers):
                    events.append("set-workers")
                def assert_clean(self):
                    events.append("guard-check")
                def close(self):
                    quality.write_json(root / "no-cache/lane-guard.json", {
                        "samples": 1, "foreign": [], "probe_errors": []})
            def start(arm, container_id, fingerprint, guard):
                self.assertTrue(guard.started)
                self.assertEqual(events[0], "guard-start")
                events.append("service-start")
                quality.write_json(root / arm / "service-start.json", {
                    "worker_pid_by_physical_npu": {
                        "0": 101, "1": 102, "2": 103, "3": 104}})
            def cleanup(arm, container_id):
                quality.write_json(root / arm / "service-stop.json", {
                    "container_removed": True})
            fake = SimpleNamespace(
                QROOT=root, ROOT=root.parent,
                preflight=lambda: {"gpu_memory_utilization": 0.85,
                    "material_cache_max_mb": 3584,
                    "max_materialized_segments": 10},
                spec=lambda arm: ({}, [], [], "cmd"),
                assert_lane_available=lambda: None,
                create=lambda arm: "owned-container",
                ForeignProcessGuard=Guard, start=start, cleanup=cleanup,
                interrupt=lambda signum, frame: None,
                write_json=quality.write_json,
                sha256=lambda path: hashlib.sha256(path.read_bytes()).hexdigest())
            service = SimpleNamespace(BENCHMARK_SHA="sha")
            with (patch.object(performance, "entry_gate", return_value="audit-sha"),
                  patch.object(performance, "earlier_phases"),
                  patch.object(performance, "pair_seam", return_value={}),
                  patch.object(performance, "run_benchmark", return_value={})):
                self.assertEqual(performance.run_phase(
                    fake, service, "no-cache", "screen"), 0)
            self.assertLess(events.index("guard-start"), events.index("service-start"))
            self.assertIn("set-workers", events)

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
