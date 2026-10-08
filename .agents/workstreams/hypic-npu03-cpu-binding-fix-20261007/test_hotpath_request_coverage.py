"""Offline regression for per-scored-request, post-repair TP evidence."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_hotpath_request_coverage import (
    CoverageError, audit_coverage, load_worker_namespace_pids,
)


API_ID = "chatcmpl-one"
INTERNAL_ID = "chatcmpl-one-0"
WORKERS = {101, 102, 103, 104}


def boundary() -> dict:
    return {
        "event": "explicit_segment_boundary_active",
        "request_id": INTERNAL_ID,
    }


def verified(pid: int, **changes: object) -> dict:
    row = {
        "event": "worker_hot_request_verified",
        "request_id": INTERNAL_ID,
        "pid": pid,
        "skipped_prefix_tokens": 4096,
        "complete_hybrid_repair_validated": True,
    }
    row.update(changes)
    return row


class RequestCoverageTests(unittest.TestCase):
    def test_host_pid_is_joined_to_container_pid_before_event_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "hypic-only"
            directory.mkdir()
            host = {str(i): 100 + i for i in range(4)}
            inside = {str(i): 200 + i for i in range(4)}
            mapping = {
                "schema": "hypic-worker-pid-namespace-map/v1",
                "container_id": "owned-container",
                "physical_npu_to_host_pid": host,
                "physical_npu_to_namespace_pid": inside,
                "nspid_lines": {
                    str(i): f"NSpid:\t{100+i}\t{200+i}"
                    for i in range(4)
                },
            }
            path = directory / "worker-namespace-map.json"
            path.write_text(json.dumps(mapping), encoding="utf-8")
            start = {
                "container_id": "owned-container",
                "worker_pid_by_physical_npu": host,
                "worker_namespace_map_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            pids = load_worker_namespace_pids(root, start)
            self.assertEqual(pids, {200, 201, 202, 203})
            report = audit_coverage(
                [API_ID], [boundary(), *(verified(pid) for pid in pids)], pids
            )
            self.assertEqual(report["four_worker_post_repair_verified_requests"], 1)
            with self.assertRaisesRegex(CoverageError, "four-worker"):
                audit_coverage(
                    [API_ID], [boundary(), *(verified(pid) for pid in host.values())], pids
                )
            mapping["nspid_lines"]["0"] = "NSpid:\t999\t200"
            path.write_text(json.dumps(mapping), encoding="utf-8")
            with self.assertRaisesRegex(CoverageError, "namespace line"):
                load_worker_namespace_pids(root, {
                    **start,
                    "worker_namespace_map_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                })

    def test_four_worker_post_repair_evidence_passes(self) -> None:
        report = audit_coverage(
            [API_ID], [boundary(), *(verified(pid) for pid in WORKERS)], WORKERS
        )
        self.assertEqual(report["four_worker_post_repair_verified_requests"], 1)

    def test_batch_counter_and_old_worker_events_do_not_pass(self) -> None:
        rows = [
            boundary(),
            {"event": "complete_hybrid_repair", "verified_hot_requests": 999},
            *({"event": "worker_hot_path", "pid": pid, "requests": 999}
              for pid in WORKERS),
        ]
        with self.assertRaisesRegex(CoverageError, "batch counters"):
            audit_coverage([API_ID], rows, WORKERS)

    def test_missing_one_worker_fails(self) -> None:
        rows = [boundary(), *(verified(pid) for pid in sorted(WORKERS)[:-1])]
        with self.assertRaisesRegex(CoverageError, "four-worker"):
            audit_coverage([API_ID], rows, WORKERS)

    def test_event_before_hybrid_repair_does_not_pass(self) -> None:
        rows = [
            boundary(),
            *(verified(pid, complete_hybrid_repair_validated=False)
              for pid in WORKERS),
        ]
        with self.assertRaisesRegex(CoverageError, "four-worker"):
            audit_coverage([API_ID], rows, WORKERS)

    def test_zero_skipped_tokens_does_not_pass(self) -> None:
        rows = [
            boundary(),
            *(verified(pid, skipped_prefix_tokens=0) for pid in WORKERS),
        ]
        with self.assertRaisesRegex(CoverageError, "four-worker"):
            audit_coverage([API_ID], rows, WORKERS)

    def test_ambiguous_internal_boundary_does_not_pass(self) -> None:
        rows = [
            boundary(),
            {"event": "explicit_segment_boundary_active",
             "request_id": INTERNAL_ID + "-other"},
            *(verified(pid) for pid in WORKERS),
        ]
        with self.assertRaisesRegex(CoverageError, "unique boundary"):
            audit_coverage([API_ID], rows, WORKERS)


if __name__ == "__main__":
    unittest.main()
