"""Software protocol checks only; never execute selector or load Torch."""
import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import post_reference_contract as c

class Contract(unittest.TestCase):
    def test_actual_resume_paths(self):
        self.assertEqual(str(c.CAPTURE), "/cache/cch/qwen36-damp-20261006/full-reference-resume-v1-on")
        self.assertEqual(c.LOCK.parent, c.AUDIT)
    def test_exact_cli(self):
        command = c.calibration_command("/usr/local/python3.12.13/bin/python3", c.PLANS)
        self.assertEqual(command[1:4], ["-B", "-m", "damp_calibrate.pipeline"])
        self.assertEqual(command[-2:], ["--cpu-threads", "8"])
        self.assertNotIn("docker", command)
    def test_unsafe_python(self):
        with self.assertRaises(ValueError): c.calibration_command("python3", c.PLANS)
    def test_output_boundaries(self):
        for path in (c.RESULTS, Path("/tmp/plans"), c.RESULTS/"x/../other/y"):
            with self.subTest(path=path), self.assertRaises(ValueError): c.absent_output(path)
    def test_missing_parent_receipt_is_not_pass(self):
        with self.assertRaises(ValueError): c.finalized(None, None)
    def test_source_is_stdlib(self):
        for name in ("post_reference_contract.py", "run.py"):
            tree = ast.parse((Path(__file__).parent/name).read_text())
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import): modules += [x.name for x in node.names]
                if isinstance(node, ast.ImportFrom): modules += [node.module or ""]
            self.assertFalse(any(x.split(".")[0] in {"torch", "torch_npu", "vllm"} for x in modules))
    def test_no_source_lock_writer(self):
        source = (Path(__file__).parent/"run.py").read_text()
        self.assertNotIn('write_text', source)
        self.assertIn('"serve_ready": False', source)
        self.assertIn('full_evidence(args.source_lock_sha256', source)
    def test_native_locks_unchanged(self):
        c.frozen_modules()
        self.assertNotIn("torch", sys.modules)

if __name__ == "__main__": unittest.main()
