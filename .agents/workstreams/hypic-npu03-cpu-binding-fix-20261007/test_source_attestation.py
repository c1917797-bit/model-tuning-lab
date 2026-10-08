#!/usr/bin/env python3
"""Offline regression for fail-closed HYPIC serving-source attestation."""

from __future__ import annotations

import tempfile
import unittest
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import binding_off_quality as quality


class SourceAttestationTests(unittest.TestCase):
    def test_package_tree_digest_is_stable_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "__init__.py").write_text("version = 1\n")
            (root / "sub").mkdir()
            source = root / "sub" / "part.py"
            source.write_text("value = 1\n")
            first = quality.python_source_digest(root)
            self.assertEqual(first["python_files"], 2)
            self.assertEqual(first, quality.python_source_digest(root))
            source.write_text("value = 2\n")
            self.assertNotEqual(first["python_tree_sha256"],
                                quality.python_source_digest(root)["python_tree_sha256"])

    def test_empty_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "source absent"):
                quality.python_source_digest(Path(temporary))

    def test_container_probe_matches_host_digest_algorithm(self) -> None:
        self.assertIn('digest.update(b"\\0")', quality.CONTAINER_SOURCE_PROBE)
        self.assertIn('importlib.util.find_spec("hypic_vllm_ascend")',
                      quality.CONTAINER_SOURCE_PROBE)
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "hypic_vllm_ascend"
            package.mkdir()
            (package / "__init__.py").write_text("version = 1\n")
            (package / "module.py").write_text("value = 2\n")
            env = {**os.environ, "PYTHONPATH": temporary}
            result = subprocess.run(
                [sys.executable, "-c", quality.CONTAINER_SOURCE_PROBE],
                cwd=temporary, env=env, text=True, capture_output=True, check=True)
            observed = json.loads(result.stdout)
            self.assertEqual(observed["import_file"], str(package / "__init__.py"))
            self.assertEqual(observed["python_tree_sha256"],
                             quality.python_source_digest(package)["python_tree_sha256"])

    def test_attestation_persists_actual_binds_and_fails_closed(self) -> None:
        item = {"Id": "abc123", "Image": "image-sha",
                "HostConfig": {"Binds": ["host:/source-hypic:ro", "out:/results"]},
                "Config": {"Cmd": ["bash", "-lc", "serve"]}}
        identity = {"import_file": "/opt/hypic/hypic_vllm_ascend/__init__.py",
                    "python_files": 2, "python_tree_sha256": "a" * 64}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(quality, "QROOT", root), \
                    patch.object(quality, "inspect", return_value=item), \
                    patch.object(quality, "owned"), \
                    patch.object(quality, "selected_plugin_source",
                                 return_value=(root, "commit")), \
                    patch.object(quality, "python_source_digest",
                                 return_value={"python_files": 2,
                                               "python_tree_sha256": "a" * 64}), \
                    patch.object(quality, "run",
                                 return_value=SimpleNamespace(stdout=json.dumps(identity))):
                digest = quality.attest_serving_source(
                    "owned-container", "hypic-only", "abc123",
                    {"source_commit": "commit"})
                path = root / "hypic-only" / "source-attestation.abc123.json"
                self.assertEqual(digest, quality.sha256(path))
                receipt = json.loads(path.read_text())
                self.assertEqual(receipt["actual_binds"],
                                 ["host:/source-hypic:ro", "out:/results"])
                self.assertEqual(receipt["container_import_file"],
                                 identity["import_file"])
                with patch.object(quality, "run",
                                  return_value=SimpleNamespace(stdout=json.dumps(
                                      {**identity, "python_tree_sha256": "b" * 64}))):
                    with self.assertRaisesRegex(RuntimeError, "differ"):
                        quality.attest_serving_source(
                            "owned-container", "no-cache", "abc123",
                            {"source_commit": "commit"})
                self.assertFalse((root / "no-cache" / "source-attestation.json").exists())


if __name__ == "__main__":
    unittest.main()
