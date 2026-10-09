"""Fail-closed tests for the physical-lane parser in the GDN probe."""

from __future__ import annotations

import unittest

from run_hypic_gdn_affine_npu_probe import npu_processes


class NpuProcessParserTests(unittest.TestCase):
    def test_all_four_cards_idle(self) -> None:
        snapshot = "\n".join(
            f"| No running processes found in NPU {card} |"
            for card in range(4)
        )
        self.assertEqual(npu_processes(snapshot), [])

    def test_physical_npu_zero_process_is_returned(self) -> None:
        snapshot = "\n".join(
            ["| 0  0 | 12345 | python3 | 1024 |"]
            + [
                f"| No running processes found in NPU {card} |"
                for card in range(1, 4)
            ]
        )
        self.assertEqual(
            npu_processes(snapshot), [{"physical_npu": 0, "pid": 12345}]
        )

    def test_missing_process_section_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "NPU3"):
            npu_processes(
                "\n".join(
                    f"| No running processes found in NPU {card} |"
                    for card in range(3)
                )
            )


if __name__ == "__main__":
    unittest.main()
