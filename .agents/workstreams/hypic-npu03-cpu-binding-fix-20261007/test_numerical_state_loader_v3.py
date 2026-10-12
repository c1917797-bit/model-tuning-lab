import hashlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import numerical_state_loader_v3 as loader
from numerical_state_writer import read_sealed


class DummyHandle:
    def __init__(self):
        self.removed = False
    def uninstall(self):
        self.removed = True


class LoaderTests(unittest.TestCase):
    def test_capture_session_uses_resolved_internal_id(self):
        adapter = object.__new__(loader.RuntimeAdapter)
        adapter.session = None
        adapter.config = self.config("/raw")
        adapter.modules = {}
        adapter.observer = DummyHandle()
        fake_torch = types.SimpleNamespace(npu=types.SimpleNamespace(current_device=lambda: 2))
        fake_parallel = types.SimpleNamespace(
            get_tp_group=lambda: types.SimpleNamespace(world_size=4, rank_in_group=2))
        with patch.dict(sys.modules, {"torch": fake_torch,
                    "vllm.distributed.parallel_state": fake_parallel}), \
             patch.object(loader, "Session") as session:
            session.return_value.handles = []
            adapter.capture("positions_committed", "selected-ab12cd34", {})
            self.assertEqual(session.call_args.args[1]["request_id"], "selected-ab12cd34")
            self.assertEqual(adapter.config["request_id"], "selected")
            session.return_value.capture.assert_called_once_with(
                "positions_committed", "selected-ab12cd34", {})

    def test_packaged_enabled_loader_and_rollback_without_runtime_import(self):
        import json
        import subprocess
        with tempfile.TemporaryDirectory() as root:
            config = self.config(root)
            del config["manifest_sha256"]
            config_path = Path(root)/"capture.json"
            config_path.write_text(json.dumps(config))
            package = Path(__file__).resolve().parent/"state-observer-package-v3"
            env = dict(os.environ, PYTHONPATH=str(package), PYTHONDONTWRITEBYTECODE="1",
                       HYPIC_STATE_OBSERVER_ENABLE="1",
                       HYPIC_STATE_CAPTURE_CONFIG=str(config_path))
            code = ("import sys;import hypic_diagnostic_patch as p;"
                    "assert 'hypic_vllm_ascend' not in sys.modules;"
                    "assert p._HANDLE in sys.meta_path;"
                    "p.deactivate();assert p._HANDLE is None;"
                    "assert not any(type(x).__name__=='RegistrationFinder' for x in sys.meta_path)")
            result = subprocess.run([sys.executable, "-B", "-c", code],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(root).glob("rank-*")), [])

    def test_packaged_enabled_bad_config_fails_startup(self):
        import subprocess
        package = Path(__file__).resolve().parent/"state-observer-package-v3"
        env = dict(os.environ, PYTHONPATH=str(package), PYTHONDONTWRITEBYTECODE="1",
                   HYPIC_STATE_OBSERVER_ENABLE="1",
                   HYPIC_STATE_CAPTURE_CONFIG="/nonexistent-hypic-diagnostic-config")
        result = subprocess.run([sys.executable, "-B", "-c", "print('should-not-run')"],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 78)
        self.assertNotIn("should-not-run", result.stdout)

    def config(self, root):
        return dict(raw_root=root, request_id="selected", kv_layer="a",
                    gdn_layer="g", manifest_sha256="1"*64)

    def test_disabled_no_import_or_finder(self):
        before = list(sys.meta_path)
        with patch.dict(os.environ, {loader.SWITCH: "0"}):
            self.assertIsNone(loader.activate(None))
        self.assertEqual(sys.meta_path, before)

    def test_finder_install_remove_no_eager_import(self):
        with patch.dict(os.environ, {loader.SWITCH: "1"}):
            before = list(sys.meta_path)
            handle = loader.activate(self.config("/nonexistent-not-read-until-worker"))
            self.assertNotIn(loader.TARGET, sys.modules)
            with self.assertRaises(RuntimeError):
                loader.activate(self.config("/raw"))
            handle.uninstall()
            self.assertEqual(sys.meta_path, before)

    def test_late_import_refused(self):
        with patch.dict(os.environ, {loader.SWITCH: "1"}), patch.dict(
                sys.modules, {loader.TARGET: types.ModuleType("already")}):
            with self.assertRaises(RuntimeError):
                loader.activate(self.config("/raw"))

    def test_registration_after_original_and_restore(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"plugin.py"
            source = "def register():\n    calls.append('original')\n    return 9\n"
            path.write_text(source)
            module = types.ModuleType("fixture")
            module.__file__, module.calls = str(path), []
            exec(compile(source, str(path), "exec"), module.__dict__)
            original = module.register
            handle = DummyHandle()
            with patch.object(loader, "PLUGIN_SHA", hashlib.sha256(source.encode()).hexdigest()), \
                 patch.dict(os.environ, {loader.SWITCH: "1", "VLLM_ASCEND_HYPIC_ENABLE": "1"}):
                adapter = loader.RuntimeAdapter(module, self.config(root))
                real_import = loader.importlib.import_module
                def modules(name):
                    return types.SimpleNamespace() if name.startswith(loader.TARGET+".patches.") else real_import(name)
                def install(*args, **kwargs):
                    self.assertEqual(module.calls, ["original"])
                    return handle
                with patch.object(loader.importlib, "import_module", side_effect=modules), \
                     patch("numerical_state_observer_v2.install", side_effect=install):
                    self.assertEqual(module.register(), 9)
                adapter.uninstall()
                self.assertTrue(handle.removed)
                self.assertIs(module.register, original)

    def test_session_complete_seals_after_uninstall(self):
        with tempfile.TemporaryDirectory() as root:
            handle = DummyHandle()
            def collector(emit, **kwargs):
                return lambda stage, req, frame: emit(dict(request_id=req, rank=0,
                    pid=os.getpid(), schema="fixture", stage=stage))
            with patch("numerical_state_capture.Collector", side_effect=collector), \
                 patch("numerical_state_observer_v2.install_step_receipt", return_value=handle):
                session = loader.Session(dict(attention=None, runner=None), self.config(root), rank=0, device=0)
                frame = {"ctx": types.SimpleNamespace(batch_plan=types.SimpleNamespace(step_id=3))}
                for stage in ("positions_committed", "kv_committed", "gdn_initial", "gdn_committed"):
                    session.capture(stage, "selected", frame)
                session.finish(dict(request_id="selected", rank=0, pid=os.getpid(), step=3))
                self.assertTrue(handle.removed)
                self.assertTrue(session.done)
                self.assertEqual(len(read_sealed(session.writer.path)[1]), 5)

    def test_failed_session_never_seals(self):
        with tempfile.TemporaryDirectory() as root:
            handle = DummyHandle()
            with patch("numerical_state_capture.Collector"), \
                 patch("numerical_state_observer_v2.install_step_receipt", return_value=handle):
                session = loader.Session(dict(attention=None, runner=None), self.config(root), rank=0, device=0)
                with self.assertRaises(RuntimeError):
                    session.finish(dict(step=99))
                session.rollback()
                self.assertTrue(handle.removed)
                self.assertFalse((session.writer.path/"SEAL.json").exists())


if __name__ == "__main__":
    unittest.main()
