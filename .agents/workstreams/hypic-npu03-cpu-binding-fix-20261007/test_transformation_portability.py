"""Exercise only the delivered target tree, without its parent workstream."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from verify_mst_transformation_suite import DEFAULT_FIXTURE

class StandaloneTransformationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mst-portable-", dir="/cache/cch")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "delivered"
        shutil.copytree(DEFAULT_FIXTURE, self.root, ignore=shutil.ignore_patterns("__pycache__"))
    def run_entry(self):
        return subprocess.run(["bash", str(self.root / "scripts/validate-mst.sh")],
                              cwd=self.root.parent, capture_output=True, text=True)
    def test_delivered_tree_runs_without_parent_helpers(self):
        result = self.run_entry()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["fixture"], str(self.root))
        self.assertEqual(output["maintainer_skills"], 7)
        self.assertEqual(output["product_health"], "ok")
        self.assertFalse(list(self.root.rglob("__pycache__")))
    def test_delivered_tree_rejects_bad_registry_status(self):
        path = self.root / ".agents/skills.registry.yaml"
        path.write_text(path.read_text().replace("status: experimental", "status: active", 1))
        result = self.run_entry()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid Skill status", result.stderr)
    def test_delivered_tree_rejects_adapter_duplication(self):
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\nOverride maintainer instructions.\n")
        result = self.run_entry()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("thin shim", result.stderr)

if __name__ == "__main__":
    unittest.main()
