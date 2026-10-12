"""Native vLLM plugin static identity; synthetic files, never imports the plugin."""
import copy
import hashlib
import json
import unittest
import test_validate_monkeypatch_package as legacy


class NativePluginPackageTests(unittest.TestCase):
    def setUp(self):
        self.fixture = legacy.PackageValidatorTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.package = self.fixture.package
        self.manifest = self.fixture.valid_fixture()
        package = self.package / "fixture_plugin"
        package.mkdir()
        (package / "__init__.py").write_text("def register():\n    pass\n")
        (package / "helper.py").write_text("VALUE = 1\n")
        (self.package / "pyproject.toml").write_text(
            '[project]\nname = "native-fixture"\nversion = "0.0.0"\n'
            '[project.entry-points."vllm.general_plugins"]\n'
            'fixture_plugin = "fixture_plugin:register"\n')
        treatment = self.manifest["treatment"]
        treatment.update({
            "loader_kind": "vllm.general_plugins",
            "loader_file": "pyproject.toml",
            "entry_point_group": "vllm.general_plugins",
            "entry_point_name": "fixture_plugin",
            "patch_file": "fixture_plugin/__init__.py",
            "entrypoint": "fixture_plugin:register",
        })
        # No alternative loader is needed for the declared native route.
        (self.package / "sitecustomize.py").unlink()
        self.refresh()

    def refresh(self):
        t = self.manifest["treatment"]
        for kind in ("patch", "loader", "launcher"):
            t[kind + "_sha256"] = hashlib.sha256(
                (self.package / t[kind + "_file"]).read_bytes()).hexdigest()
        self.manifest["source_files"] = [
            {"path": p.relative_to(self.package).as_posix(),
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted((self.package / "fixture_plugin").rglob("*.py"))]
        self.save()

    def save(self):
        self.fixture.save(self.manifest)

    def run_check(self):
        return self.fixture.run_validator()

    def reject(self, message):
        self.save()
        result = self.run_check()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)

    def test_native_package_init_and_pyproject_pass_without_sitecustomize(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["loader_kind"], "vllm.general_plugins")
        self.assertEqual(record["source_files_verified"], 2)
        self.assertTrue(record["not_runtime_activation_or_delivery_acceptance"])

    def test_missing_python_file_from_manifest_rejected(self):
        self.manifest["source_files"].pop()
        self.reject("source file inventory mismatch")

    def test_changed_helper_bytes_rejected(self):
        (self.package / "fixture_plugin/helper.py").write_text("VALUE = 2\n")
        self.reject("SHA256 mismatch")

    def test_duplicate_source_file_rejected(self):
        self.manifest["source_files"].append(copy.deepcopy(self.manifest["source_files"][0]))
        self.reject("duplicate native source file")

    def test_source_path_escape_rejected(self):
        self.manifest["source_files"][0]["path"] = "../outside.py"
        self.reject("safe relative path")

    def test_wrong_entrypoint_group_rejected(self):
        self.manifest["treatment"]["entry_point_group"] = "another.group"
        self.reject("entry_point_group")

    def test_wrong_toml_entrypoint_rejected(self):
        p = self.package / "pyproject.toml"
        p.write_text(p.read_text().replace("fixture_plugin:register", "fixture_plugin:wrong"))
        self.refresh()
        self.reject("entrypoint declaration mismatch")

    def test_missing_toml_entrypoint_rejected(self):
        (self.package / "pyproject.toml").write_text('[project]\nname = "native-fixture"\n')
        self.refresh()
        self.reject("entrypoint declaration mismatch")

    def test_unknown_loader_kind_rejected(self):
        self.manifest["treatment"]["loader_kind"] = "unknown"
        self.reject("loader_kind")

    def test_symlink_source_rejected(self):
        (self.package / "fixture_plugin/link.py").symlink_to(
            self.package / "fixture_plugin/helper.py")
        self.refresh()
        self.reject("symlink")

    def test_invalid_toml_rejected(self):
        (self.package / "pyproject.toml").write_text("[broken")
        self.refresh()
        self.save()
        result = self.run_check()
        self.assertEqual(result.returncode, 2)

    def test_entrypoint_file_mismatch_rejected(self):
        self.manifest["treatment"]["entrypoint"] = "missing:register"
        self.reject("entrypoint module")


if __name__ == "__main__":
    unittest.main()
