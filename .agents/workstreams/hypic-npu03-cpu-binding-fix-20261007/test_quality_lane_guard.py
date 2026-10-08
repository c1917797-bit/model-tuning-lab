#!/usr/bin/env python3
"""Offline checks for fail-closed physical NPU0-3 process isolation."""

from __future__ import annotations

import subprocess
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import binding_off_quality as quality
import binding_off_service as service


def snapshot(extra: str = "") -> str:
    return ("| NPU     Chip              | Process id    | Process name | Process memory(MB) |\n"
            "| 0       0                 | 11            | VLLMWorker_TP | 100 |\n"
            "| 1       0                 | 12            | VLLMWorker_TP | 100 |\n"
            "| 2       0                 | 13            | VLLMWorker_TP | 100 |\n"
            "| 3       0                 | 14            | VLLMWorker_TP | 100 |\n"
            + extra)


class QualityLaneGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workers = {str(i): 11 + i for i in range(4)}

    def test_idle_lane_ignores_container_mapping_only(self) -> None:
        idle = "".join(f"No running processes found in NPU {i}\n" for i in range(4))
        def fake_run(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
            if args[:2] == ("npu-smi", "info"):
                return subprocess.CompletedProcess(args, 0, idle, "")
            if args[0] == "ss":
                return subprocess.CompletedProcess(args, 0, "", "")
            raise AssertionError(f"mapping-only inspection is not a lane gate: {args}")
        with patch.object(service, "run", side_effect=fake_run):
            service.assert_lane_available()

    def test_physical_process_still_blocks_lane(self) -> None:
        busy = "No running processes found in NPU 0\n"
        with patch.object(service, "run",
                          return_value=subprocess.CompletedProcess([], 0, busy, "")):
            with self.assertRaisesRegex(RuntimeError, "running process"):
                service.assert_lane_available()

    def check(self, content: str, code: int = 0) -> quality.ForeignProcessGuard:
        guard = quality.ForeignProcessGuard("no-cache", self.workers)
        result = subprocess.CompletedProcess(["npu-smi", "info"], code, content, "")
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(quality.subprocess, "run", return_value=result), \
                    patch.object(quality, "PROC_ROOT", Path(temporary)), \
                    patch.object(quality, "write_json"):
                guard.sample()
        return guard

    def test_owned_workers_are_clean(self) -> None:
        guard = self.check(snapshot())
        self.assertEqual(guard.samples, 1)
        self.assertEqual(guard.foreign, [])
        self.assertEqual(guard.errors, [])

    def test_foreign_pid_on_physical_three_is_recorded(self) -> None:
        guard = self.check(snapshot("| 3       0                 | 356193        | python | 2704 |\n"))
        self.assertEqual(guard.foreign[0]["processes"],
                         [{"physical_npu": 3, "pid": 356193}])

    def test_foreign_pid_captures_docker_cgroup_before_exit(self) -> None:
        container_id = "a" * 64
        with tempfile.TemporaryDirectory() as temporary:
            cgroup = Path(temporary) / "356193" / "cgroup"
            cgroup.parent.mkdir()
            cgroup.write_text(f"13:pids:/docker/{container_id}\n")
            result = subprocess.CompletedProcess(
                ["npu-smi", "info"], 0,
                snapshot("| 3       0                 | 356193        | python | 2704 |\n"), "")
            guard = quality.ForeignProcessGuard("no-cache", self.workers)
            with patch.object(quality, "PROC_ROOT", Path(temporary)), \
                    patch.object(quality.subprocess, "run", return_value=result), \
                    patch.object(quality, "write_json"):
                self.assertEqual(quality.foreign_container_id(356193), container_id)
                self.assertIsNone(quality.foreign_container_id(356194))
                guard.sample()
            self.assertEqual(guard.foreign[0]["processes"],
                             [{"physical_npu": 3, "pid": 356193,
                               "container_id": container_id}])

    def test_incomplete_or_failed_probe_is_not_clean(self) -> None:
        self.assertTrue(self.check("| NPU | Process id |\n").errors)
        self.assertTrue(self.check(snapshot(), code=1).errors)

    def test_abort_stop_requires_exact_owned_identity(self) -> None:
        item = {"Id": "different-id", "State": {"Status": "running"}}
        with patch.object(quality, "inspect", return_value=item), \
                patch.object(quality, "owned", side_effect=RuntimeError("identity mismatch")), \
                patch.object(quality, "run") as execute:
            with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                quality.stop_owned_for_abort("no-cache", "exact-owned-id")
        execute.assert_not_called()

    def test_abort_stop_uses_verified_container_id(self) -> None:
        item = {"Id": "exact-owned-id", "State": {"Status": "running"}}
        with patch.object(quality, "inspect", return_value=item), \
                patch.object(quality, "owned") as owned, \
                patch.object(quality, "run") as execute:
            quality.stop_owned_for_abort("no-cache", "exact-owned-id")
        owned.assert_called_once_with(item, "no-cache", "exact-owned-id")
        execute.assert_called_once_with("docker", "stop", "--time", "30", "exact-owned-id")

    def test_cleanup_preserves_owned_release_when_foreign_lane_is_busy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arm_dir = root / "no-cache"
            arm_dir.mkdir()
            start = {"container_id": "owned-container-id",
                     "worker_pid_by_physical_npu": self.workers}
            (arm_dir / "service-start.json").write_text(json.dumps(start))
            item = {"Id": "owned-container-id", "State": {"Status": "running"}}

            def fake_run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
                output = ("| No running processes found in NPU 0 |\n"
                          "| No running processes found in NPU 1 |\n"
                          "| No running processes found in NPU 2 |\n"
                          "| 3       0                 | 356193        | python | 2704 |\n")
                return subprocess.CompletedProcess(args, 0,
                                                   output if args[0] == "npu-smi" else "", "")

            with patch.object(quality, "QROOT", root), \
                    patch.object(quality, "inspect", side_effect=[item, None]), \
                    patch.object(quality, "owned"), \
                    patch.object(quality, "run", side_effect=fake_run), \
                    patch.object(quality.subprocess, "run",
                                 return_value=subprocess.CompletedProcess(["docker", "logs"], 0)), \
                    patch.object(quality, "assert_lane_available",
                                 side_effect=RuntimeError("foreign NPU3 process")):
                with self.assertRaisesRegex(RuntimeError, "shared lane unavailable"):
                    quality.cleanup("no-cache", "owned-container-id")
            receipt = json.loads((arm_dir / "service-stop.json").read_text())
            self.assertTrue(receipt["container_removed"])
            self.assertTrue(receipt["owned_npus_released"])
            self.assertTrue(receipt["port_released"])
            self.assertFalse(receipt["lane_available"])
            self.assertEqual(receipt["foreign_npu_processes"],
                             [{"physical_npu": 3, "pid": 356193}])


if __name__ == "__main__":
    unittest.main()
