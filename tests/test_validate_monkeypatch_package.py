"""Behavioral tests for the static runtime-monkeypatch package validator."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts/validate_monkeypatch_package.py"
TEMPLATE = REPO / ".agents/skills/runtime-monkeypatch-delivery/assets/template"


class PackageValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / "candidate"
        shutil.copytree(TEMPLATE, self.package)
        self.manifest_path = self.package / "MANIFEST.json"

    def run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (sys.executable, "-B", str(VALIDATOR), str(self.package)),
            cwd=REPO, capture_output=True, text=True, check=False,
        )

    def valid_fixture(self) -> dict:
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = "hypic-static-fixture"
        source = manifest["source_contract"]
        source.update({
            "image_digest": "sha256:" + "a" * 64,
            "framework_version": "vllm-0.10.2",
            "cann_version": "8.2",
            "live_module": "vllm.foo",
            "live_object": "Runner",
            "source_sha256": "b" * 64,
        })
        (self.package / "patch.py").write_text(
            "def activate():\n    print('PATCH_CALLED')\n", encoding="utf-8")
        manifest["treatment"]["patch_sha256"] = hashlib.sha256(
            (self.package / "patch.py").read_bytes()).hexdigest()
        manifest["evidence"].update({
            "experiment_id": "exp-20261008-validator-fixture",
            "branch": "work/validator-fixture",
            "commit": "c" * 40,
        })
        self.save(manifest)
        return manifest

    def save(self, manifest: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_template_is_not_a_valid_candidate(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 2)
        self.assertIn("template", result.stderr)

    def test_customized_hash_bound_fixture_passes_static_only(self) -> None:
        self.valid_fixture()
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["static_identity_valid"])
        self.assertTrue(receipt["not_runtime_activation_or_delivery_acceptance"])
        self.assertEqual(receipt["required_roles"], ["engine", "worker"])

    def test_patch_hash_drift_fails_closed(self) -> None:
        manifest = self.valid_fixture()
        manifest["treatment"]["patch_sha256"] = "d" * 64
        self.save(manifest)
        result = self.run_validator()
        self.assertEqual(result.returncode, 2)
        self.assertIn("SHA256 mismatch", result.stderr)

    def test_launcher_hash_drift_fails_closed(self) -> None:
        manifest = self.valid_fixture()
        manifest["treatment"]["launcher_sha256"] = "e" * 64
        self.save(manifest)
        result = self.run_validator()
        self.assertEqual(result.returncode, 2)
        self.assertIn("SHA256 mismatch", result.stderr)

    def test_path_traversal_fails_closed(self) -> None:
        manifest = self.valid_fixture()
        manifest["treatment"]["patch_file"] = "../outside.py"
        self.save(manifest)
        result = self.run_validator()
        self.assertEqual(result.returncode, 2)
        self.assertIn("safe relative path", result.stderr)

    def test_disabled_control_cannot_be_omitted(self) -> None:
        manifest = self.valid_fixture()
        manifest["activation"]["disabled_control_required"] = False
        self.save(manifest)
        result = self.run_validator()
        self.assertEqual(result.returncode, 2)
        self.assertIn("disabled_control_required", result.stderr)

    def test_same_wrapper_switches_treatment_without_changing_command(self) -> None:
        self.valid_fixture()
        command = ("bash", str(self.package / "run_with_patch.sh"),
                   sys.executable, "-c", "print('request-ok')")
        for switch in (None, "0", "1"):
            env = os.environ.copy()
            if switch is None:
                env.pop("MODEL_TUNING_RUNTIME_PATCH_ENABLE", None)
            else:
                env["MODEL_TUNING_RUNTIME_PATCH_ENABLE"] = switch
            result = subprocess.run(command, cwd=REPO, env=env,
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("request-ok", result.stdout)
            if switch == "1":
                self.assertGreaterEqual(result.stdout.count("PATCH_CALLED"), 2)
                self.assertGreaterEqual(result.stderr.count(
                    "MODEL_TUNING_PATCH_ACTIVE"), 2)
            else:
                self.assertNotIn("PATCH_CALLED", result.stdout)
                self.assertNotIn("MODEL_TUNING_PATCH_ACTIVE", result.stderr)


if __name__ == "__main__":
    unittest.main()
