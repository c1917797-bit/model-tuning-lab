"""Host-only default/source/importer controls; never executes official worker."""
import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from graph_candidate import worker_loader


class WorkerLoaderTests(unittest.TestCase):
    def test_absent_quality_profile_keeps_unfiltered_full_path(self):
        config = {"capacity_bytes": 100}
        self.assertIsNone(worker_loader._take_quality_policy(config))
        self.assertEqual(config, {"capacity_bytes": 100})

    def test_quality_hot_reuses_actual_policy_and_removes_stage_keyword(self):
        from independent_quality_evidence_policy import QualityEvidencePolicy
        config = {"evidence_profile": "quality-hot", "capacity_bytes": 100}
        policy = worker_loader._take_quality_policy(config)
        self.assertIs(type(policy), QualityEvidencePolicy)
        self.assertNotIn("evidence_profile", config)
        self.assertEqual(policy.descriptor()["profile"], "quality-hot")
        self.assertIsNone(policy.select({"event": "mixed_native_c2_completed"}))
        hot = policy.select({"event": "compact_c2_queries_completed", "request_id": "q"})
        self.assertEqual(hot["evidence_profile"], "quality-hot")
        self.assertEqual(hot["omitted_nonhot_counts"], {"mixed_native_c2_completed": 1})

    def test_catalog_uses_real_scheduler_interface_with_full_request_limit(self):
        import independent_catalog_scheduler_loader as catalog
        config = {"public_segments": ((1, 2, 3),)}
        with patch.object(catalog, "enable_scheduler", wraps=catalog.enable_scheduler) as install:
            worker_loader._enable_bound_scheduler("manifest", config, "raw",
                enabled=False, request_limit=1024)()
            install.assert_called_once_with("manifest", config, "raw",
                enabled=False, request_limit=1024)

    def test_single_public_scheduler_interface_is_unchanged(self):
        import independent_pic_scheduler_loader as single
        config = {"public_tokens": (1, 2, 3)}
        with patch.object(single, "enable_scheduler", wraps=single.enable_scheduler) as install:
            worker_loader._enable_bound_scheduler("manifest", config, "raw",
                enabled=False, request_limit=1024)()
            install.assert_called_once_with("manifest", config, "raw", enabled=False)

    def test_failed_worker_import_uninstalls_owned_finder_and_scheduler(self):
        finder = object()
        stopped = []
        with patch.object(worker_loader, "_finder", finder), patch.object(
                worker_loader, "_stop", None), patch.object(
                worker_loader, "_scheduler_stop", lambda: stopped.append("scheduler")):
            sys.meta_path.append(finder)
            try:
                worker_loader._uninstall_owned()
                self.assertNotIn(finder, sys.meta_path)
                self.assertEqual(stopped, ["scheduler"])
                self.assertIsNone(worker_loader._finder)
                self.assertIsNone(worker_loader._scheduler_stop)
            finally:
                if finder in sys.meta_path:
                    sys.meta_path.remove(finder)

    def test_uninstall_removes_facade_before_scheduler(self):
        stopped = []
        with patch.object(worker_loader, "_finder", None), patch.object(
                worker_loader, "_stop", lambda: stopped.append("facade")), patch.object(
                worker_loader, "_scheduler_stop", lambda: stopped.append("scheduler")):
            worker_loader._uninstall_owned()
            self.assertEqual(stopped, ["facade", "scheduler"])
            self.assertIsNone(worker_loader._stop)

    def test_default_disabled_needs_no_manifest_or_runtime(self):
        with patch.dict(os.environ, {}, clear=True):
            before = tuple(sys.meta_path)
            worker_loader.enable()()
            self.assertEqual(before, tuple(sys.meta_path))

    def fixture(self, directory, source="x = 1\n"):
        package = Path(directory) / "vllm_ascend"
        worker = package / "worker"
        worker.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        path = worker / "model_runner_v1.py"
        path.write_text(source)
        module = ModuleType("vllm_ascend")
        module.__file__ = str(package / "__init__.py")
        spec = importlib.util.spec_from_file_location(worker_loader.WORKER, path)
        return module, spec, source

    def test_real_native_importer_code_matches_source_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            module, spec, source = self.fixture(directory, "raise RuntimeError('must not execute')\n")
            with patch.dict(sys.modules, {"vllm_ascend": module}), patch.object(
                    worker_loader, "WORKER_SHA256", hashlib.sha256(source.encode()).hexdigest()):
                original, path, raw, code = worker_loader._verified_native_spec(spec)
                self.assertIs(original, spec.loader)
                self.assertEqual(raw, source.encode())
                self.assertEqual(Path(code.co_filename), path)

    def test_wrong_source_hash_fails_before_exec(self):
        with tempfile.TemporaryDirectory() as directory:
            module, spec, source = self.fixture(directory)
            with patch.dict(sys.modules, {"vllm_ascend": module}):
                with self.assertRaisesRegex(ValueError, "source drift"):
                    worker_loader._verified_native_spec(spec)

    def test_unknown_native_loader_wrapper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            module, spec, source = self.fixture(directory)
            class Unknown(importlib.machinery.SourceFileLoader):
                pass
            spec.loader = Unknown(worker_loader.WORKER, spec.origin)
            with patch.dict(sys.modules, {"vllm_ascend": module}):
                with self.assertRaisesRegex(ValueError, "original native"):
                    worker_loader._verified_native_spec(spec)

    def test_instance_exec_override_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            module, spec, source = self.fixture(directory)
            spec.loader.exec_module = lambda module: None
            with patch.dict(sys.modules, {"vllm_ascend": module}):
                with self.assertRaisesRegex(ValueError, "original native"):
                    worker_loader._verified_native_spec(spec)

    def test_wrong_origin_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            module, spec, source = self.fixture(directory)
            spec.origin = str(Path(directory) / "wrong.py")
            with patch.dict(sys.modules, {"vllm_ascend": module}):
                with self.assertRaisesRegex(ValueError, "original native"):
                    worker_loader._verified_native_spec(spec)

    def test_manifest_requires_explicit_graph_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text("{}")
            with self.assertRaisesRegex(ValueError, "graph profile"):
                worker_loader._manifest(path)

    def test_manifest_cannot_omit_nested_runtime_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text('{"graph_profile":"selective-prefill-native-decode-v1","source_sha256":{"fake.py":"a"}}')
            with self.assertRaisesRegex(ValueError, "omits graph"):
                worker_loader._manifest(path)


if __name__ == "__main__":
    unittest.main()
