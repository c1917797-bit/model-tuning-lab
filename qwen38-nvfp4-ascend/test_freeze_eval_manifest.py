#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("freeze_eval_manifest.py")
SPEC = importlib.util.spec_from_file_location("freeze_eval_manifest", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FreezeManifestTest(unittest.TestCase):
    def test_mmlu_format(self):
        row = ["Question?", "one", "two", "three", "four", "C"]
        self.assertEqual(
            MODULE.format_mmlu(row, False),
            "Question?\nA. one\nB. two\nC. three\nD. four\nAnswer: ",
        )
        self.assertTrue(MODULE.format_mmlu(row, True).endswith("Answer: C"))

    def test_jsonl_is_stable(self):
        records = [{"z": 1, "a": "two"}, {"id": "x"}]
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.jsonl"
            second = Path(directory) / "second.jsonl"
            self.assertEqual(MODULE.write_jsonl(first, records), MODULE.write_jsonl(second, records))
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
