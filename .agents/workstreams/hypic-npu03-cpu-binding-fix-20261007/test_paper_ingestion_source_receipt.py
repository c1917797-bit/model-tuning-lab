"""CPU-only corruption regressions for the real ingestion source receipt."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ingestion_under_test",
                                             HERE / "verify_paper_ingestion_case.py")
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
original_loads = json.loads


class SourceReceiptTests(unittest.TestCase):
    def run_mutated(self, mutate):
        def decode(data, *args, **kwargs):
            value = original_loads(data, *args, **kwargs)
            if isinstance(value, dict) and value.get("schema") == "hypic-author-reference-pin/v2":
                value = copy.deepcopy(value)
                mutate(value)
            return value
        with patch.object(subject.json, "loads", side_effect=decode):
            with contextlib.redirect_stdout(io.StringIO()):
                subject.main()

    def test_real_case(self):
        self.run_mutated(lambda value: None)

    def test_wrong_commit(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value.update(commit="0" * 40))

    def test_duplicate_reference(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value["files"].__setitem__(0, value["files"][1]))

    def test_reference_hash_drift(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value["files"][0].update(sha256="0" * 64))

    def test_historical_manifest_drift(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value["files"][0].update(expected_sha256="0" * 64))

    def test_missing_reference_bytes(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value["files"][0].update(local=False, match=None))

    def test_license_hash_drift(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value["extra_files"][0].update(sha256="0" * 64))

    def test_missing_test_reference(self):
        with self.assertRaises(RuntimeError):
            self.run_mutated(lambda value: value["extra_files"].pop())


if __name__ == "__main__":
    unittest.main()
