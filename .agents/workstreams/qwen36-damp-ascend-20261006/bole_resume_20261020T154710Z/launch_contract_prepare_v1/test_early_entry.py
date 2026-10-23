"""Filesystem regressions for caller preparation; not algorithm qualification."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("early_entry", P / "early_entry.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

class CallerTests(unittest.TestCase):
    def test_fresh_parent_is_initialized_but_leaf_is_not(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "new-owned-run" / "software"
            leaf = root / "consumer"
            self.assertEqual(E.initialize(root, leaf, base), [str(root.parent), str(root)])
            self.assertTrue(root.is_dir())
            self.assertFalse(leaf.exists())

    def test_existing_lock_parent_does_not_overwrite_leaf(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "software"
            root.mkdir()
            (root / ".math-recovery.lock").touch()
            leaf = root / "consumer"
            self.assertEqual(E.initialize(root, leaf, base), [])
            leaf.mkdir()
            with self.assertRaises(ValueError):
                E.initialize(root, leaf, base)

    def test_symlink_parent_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            real = base / "real"
            real.mkdir()
            link = base / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(ValueError):
                E.initialize(link / "software", link / "software" / "consumer", base)

    def test_output_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with self.assertRaises(ValueError):
                E.initialize(base.parent / "not-owned", base.parent / "not-owned" / "consumer", base)

    def test_default_off_and_partial_operands_reject(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(P / "early_entry.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["enabled"])
        result = subprocess.run([sys.executable, "-I", "-B", str(P / "early_entry.py"), "--host-cpu", "144"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_unresolved_traversal_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "owner" / ".." / ".." / "outside"
            with self.assertRaises(ValueError):
                E.initialize(root, root / "consumer", base)
            self.assertFalse((base / "owner").exists())

if __name__ == "__main__":
    unittest.main()
