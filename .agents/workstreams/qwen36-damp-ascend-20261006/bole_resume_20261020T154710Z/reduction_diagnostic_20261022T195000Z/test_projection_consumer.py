import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import compare_projection_reductions as C


class ProjectionConsumerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bole-reduce-consumer-")
        self.root = Path(self.temporary.name)
        self.config = dict(schema="bole.projection-reduction-diagnostic-input/v1",
                           consumer_sources=[C.reference(C.__file__), C._MATH_REF],
                           generations=[1, 2], ranks=[0, 1, 2, 3],
                           shape=[1, 2], tree_coordinate_cap=16,
                           projection_records=[])
        parts = ([1, 0x3F80], [1, 0xBF80], [1, 0x3B80], [1, 0x3B80])
        for generation in (1, 2):
            for rank in range(4):
                stages = {}
                for stage, words in (
                    ("pre_reduce", parts[rank]),
                    ("post_reduce", [4, 0x3C00 if generation == 1 else 0x3B80]),
                ):
                    raw = self.root / f"G{generation}-R{rank}-{stage}.bin"
                    raw.write_bytes(struct.pack("<HH", *words))
                    ref = C.reference(raw)
                    stages[stage] = dict(raw=ref, bytes=4, sha256=ref["sha256"],
                                         dtype="torch.bfloat16", shape=[1, 2],
                                         full_actual_tensor=True)
                meta = self.root / f"G{generation}-R{rank}.json"
                meta.write_text(json.dumps(dict(
                    schema="bole.native-prefill-boundary-repeatability/v1",
                    event="PROJECTION-INTERNAL", generation=generation, rank=rank,
                    source_sha256="a" * 64,
                    record=dict(generation=generation, diagnostic_only=True, stages=stages))))
                self.config["projection_records"].append(C.reference(meta))

    def tearDown(self):
        self.temporary.cleanup()

    def test_exact_sum_and_order_diagnostic(self):
        result = C.analyze(self.config)
        self.assertTrue(result["data_complete"])
        self.assertEqual(result["generations"][0]["exact_sum_mismatch"], [0] * 4)
        second = result["generations"][1]
        self.assertEqual(second["exact_sum_mismatch"], [1] * 4)
        self.assertEqual(second["tree_outside"], [0] * 4)
        self.assertTrue(second["tree_coverage_complete"])
        self.assertEqual(result["cross_generation"],
                         dict(pre_reduce=[0] * 4, post_reduce=[1] * 4))
        self.assertFalse(result["numerical_qualified"])
        self.assertFalse(result["formal_performance"])

    def test_missing_raw_stays_incomplete(self):
        ref = self.config["projection_records"][0]
        path = Path(ref["path"])
        meta = json.loads(path.read_text())
        del meta["record"]["stages"]["pre_reduce"]["raw"]
        path.write_text(json.dumps(meta))
        self.config["projection_records"][0] = C.reference(path)
        result = C.analyze(self.config)
        self.assertFalse(result["data_complete"])
        self.assertEqual(len(result["missing_raw"]), 1)
        self.assertEqual(result["generations"], [])

    def test_tampered_raw_rejected(self):
        meta = json.loads(Path(self.config["projection_records"][0]["path"]).read_text())
        raw = Path(meta["record"]["stages"]["pre_reduce"]["raw"]["path"])
        raw.write_bytes(b"xxxx")
        with self.assertRaisesRegex(ValueError, "exact stable Ref"):
            C.analyze(self.config)

    def test_duplicate_rank_rejected(self):
        self.config["projection_records"][-1] = self.config["projection_records"][0]
        with self.assertRaisesRegex(ValueError, "one record"):
            C.analyze(self.config)

    def test_wrong_source_and_shape_rejected(self):
        bad = copy.deepcopy(self.config)
        bad["consumer_sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "consumer bytes"):
            C.analyze(bad)
        bad = copy.deepcopy(self.config)
        bad["shape"] = [2, 2]
        with self.assertRaisesRegex(ValueError, "actual full BF16"):
            C.analyze(bad)

    def test_real_isolated_cli_and_no_overwrite(self):
        inputs = self.root / "INPUTS.json"
        inputs.write_text(json.dumps(self.config))
        output = self.root / "RESULT.json"
        command = [sys.executable, "-I", "-B", str(Path(C.__file__).resolve()),
                   "--execute", "--inputs-ref", json.dumps(C.reference(inputs)),
                   "--output", str(output)]
        first = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout), C.reference(output))
        original = output.read_bytes()
        second = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(output.read_bytes(), original)

    def test_real_default_off(self):
        result = subprocess.run([sys.executable, "-I", "-B", C.__file__],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(enabled=False, NPU=False))


if __name__ == "__main__":
    unittest.main()

