"""Negative checks on disposable copies; original fixture and NPUs untouched."""
from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import yaml
from verify_mst_transformation_suite import DEFAULT_FIXTURE, verify_registry_contract

class TransformationRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mst-regression-", dir="/cache/cch")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "target"
        shutil.copytree(DEFAULT_FIXTURE, self.root)
        shutil.copy2(DEFAULT_FIXTURE.parent / "input-snapshot.json",
                     self.root.parent / "input-snapshot.json")
        self.path = self.root / ".agents/skills.registry.yaml"
        self.registry = yaml.safe_load(self.path.read_text())

    def save(self):
        self.path.write_text(yaml.safe_dump(self.registry, sort_keys=False))

    def test_valid_transformed_registry(self):
        self.assertEqual(verify_registry_contract(self.root), 7)

    def test_active_status_is_rejected(self):
        self.registry["skills"][0]["status"] = "active"
        self.save()
        with self.assertRaisesRegex(RuntimeError, "invalid Skill status"):
            verify_registry_contract(self.root)

    def test_duplicate_id_is_rejected(self):
        self.registry["skills"][1]["id"] = self.registry["skills"][0]["id"]
        self.save()
        with self.assertRaisesRegex(RuntimeError, "duplicate Skill IDs"):
            verify_registry_contract(self.root)

    def test_missing_trigger_is_rejected(self):
        self.registry["skills"][0]["triggers"] = []
        self.save()
        with self.assertRaisesRegex(RuntimeError, "missing triggers"):
            verify_registry_contract(self.root)

    def test_orphan_is_rejected(self):
        (self.root / ".agents/skills/unregistered").mkdir()
        with self.assertRaisesRegex(RuntimeError, "orphan"):
            verify_registry_contract(self.root)

    def test_missing_skill_file_is_rejected(self):
        (self.root / self.registry["skills"][0]["path"] / "SKILL.md").unlink()
        with self.assertRaisesRegex(RuntimeError, "missing Skill file"):
            verify_registry_contract(self.root)

    def test_runtime_path_is_rejected(self):
        self.registry["skills"][0]["path"] = "runtime-skills/customer-helper"
        self.save()
        with self.assertRaisesRegex(RuntimeError, "escapes tree"):
            verify_registry_contract(self.root)

    def test_frontmatter_name_mismatch(self):
        path = self.root / self.registry["skills"][0]["path"] / "SKILL.md"
        path.write_text(path.read_text().replace(
            "name: mst-repo-onboarding", "name: wrong-name", 1))
        with self.assertRaisesRegex(RuntimeError, "frontmatter mismatch"):
            verify_registry_contract(self.root)

    def test_maintainer_publication_is_rejected_by_full_runner(self):
        path = self.root / "runtime-skills/publish-policy.yaml"
        policy = yaml.safe_load(path.read_text())
        policy["allowed"].append({"skill": "mst-skill-governor"})
        path.write_text(yaml.safe_dump(policy, sort_keys=False))
        run = subprocess.run(
            [sys.executable, "-B", str(DEFAULT_FIXTURE.parents[2] /
             "verify_mst_transformation_suite.py"), "--fixture", str(self.root)],
            capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("exposed as runtime asset", run.stderr)

    def add_component(self):
        component = self.root / "components/worker"
        shutil.copytree(self.root / ".agents", component / ".agents")
        return component

    def test_nested_registry_requires_precedence(self):
        self.add_component()
        with self.assertRaisesRegex(RuntimeError, "selection precedence"):
            verify_registry_contract(self.root)

    def test_nested_registry_is_walked(self):
        component = self.add_component()
        self.registry["selection"]["precedence"] = ["crate_scoped", "workspace_scoped"]
        self.save()
        path = component / ".agents/skills.registry.yaml"
        registry = yaml.safe_load(path.read_text())
        registry["skills"][0]["status"] = "active"
        path.write_text(yaml.safe_dump(registry, sort_keys=False))
        with self.assertRaisesRegex(RuntimeError, "invalid Skill status"):
            verify_registry_contract(self.root)

    def test_nested_valid_registry(self):
        self.add_component()
        self.registry["selection"]["precedence"] = ["crate_scoped", "workspace_scoped"]
        self.save()
        self.assertEqual(verify_registry_contract(self.root), 14)

if __name__ == "__main__":
    unittest.main()
