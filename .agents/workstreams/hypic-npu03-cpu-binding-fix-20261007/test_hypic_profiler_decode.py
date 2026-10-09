"""Synthetic checks for the preregistered independent Decode trace gate."""

import unittest

from verify_hypic_profiler_decode import kernel_window, utc_us


class DecodeTraceGateTest(unittest.TestCase):
    def test_hardware_compute_events_within_capture_interval(self):
        start = utc_us("2026-10-09T18:00:00+00:00")
        events = [
            {"ph": "M", "name": "process_name", "pid": 42,
             "args": {"name": "Ascend Hardware"}},
            {"ph": "M", "name": "process_name", "pid": 43,
             "args": {"name": "Python"}},
            {"ph": "X", "pid": 42, "ts": str(start - 1),
             "args": {"Task Type": "AI_CORE"}},
            {"ph": "X", "pid": 43, "ts": str(start + 100),
             "args": {"Task Type": "AI_CORE"}},
            {"ph": "X", "pid": 42, "ts": str(start + 100),
             "args": {"Task Type": "HCCL"}},
        ]
        events.extend(
            {"ph": "X", "pid": 42, "ts": str(start + 100 + index * 20_000),
             "args": {"Task Type": "AI_VECTOR_CORE"}}
            for index in range(64)
        )
        summary = kernel_window(events, start, start + 1_500_000)
        self.assertEqual(summary["compute_kernel_count"], 64)
        self.assertGreaterEqual(summary["compute_span_s"], 1.0)

    def test_missing_hardware_metadata_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "Ascend Hardware"):
            kernel_window([], 0, 1)


if __name__ == "__main__":
    unittest.main()
