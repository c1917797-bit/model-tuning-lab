"""Bounded adapter audit regressions on disposable files; no tool agent/NPU."""
from pathlib import Path
import tempfile
import unittest

from verify_tool_adapter_boundary_case import REPO, audit_boundary


class AdapterBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="adapter-audit-", dir="/cache/cch")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.agents = (REPO / "AGENTS.md").read_text()
        (self.root / "AGENTS.md").write_text(self.agents)
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n")

    def check(self):
        return audit_boundary(self.root, "@AGENTS.md\n")

    def test_actual_bootstrap_and_thin_shim(self):
        self.assertEqual(self.check()["existing_adapters"], ["CLAUDE.md"])

    def test_full_canonical_copy_rejected(self):
        (self.root / "CLAUDE.md").write_text(self.agents)
        with self.assertRaisesRegex(RuntimeError, "one-line shim"):
            self.check()

    def test_adapter_governance_override_rejected(self):
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\nCommit directly to main.\n")
        with self.assertRaisesRegex(RuntimeError, "one-line shim"):
            self.check()

    def test_untracked_tool_config_not_ignored(self):
        (self.root / ".codex").mkdir()
        (self.root / ".codex/config.toml").write_text('model = "example"\n')
        with self.assertRaisesRegex(RuntimeError, "inventory changed"):
            self.check()

    def test_canonical_pointer_missing_rejected(self):
        (self.root / "AGENTS.md").write_text(
            self.agents.replace(".agents/skills.registry.yaml", "missing-registry"))
        with self.assertRaisesRegex(RuntimeError, "canonical bootstrap pointer"):
            self.check()

    def test_main_adapter_drift_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "one-line shim"):
            audit_boundary(self.root, "@different.md\n")

    def test_missing_adapter_rejected(self):
        (self.root / "CLAUDE.md").unlink()
        with self.assertRaisesRegex(RuntimeError, "inventory changed"):
            self.check()

    def test_symlinked_adapter_requires_review(self):
        path = self.root / "CLAUDE.md"
        path.unlink()
        path.symlink_to(self.root / "AGENTS.md")
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            self.check()


if __name__ == "__main__":
    unittest.main()
