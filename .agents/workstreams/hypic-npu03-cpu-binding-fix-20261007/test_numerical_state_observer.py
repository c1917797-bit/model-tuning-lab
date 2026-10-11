import ast
import hashlib
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from numerical_state_observer import HOOK, SWITCH, SPECS, install, instrument

SOURCE_ROOT = Path("/cache/cch/hypic_vllm_ascend-hotproof-20261008/hypic_vllm_ascend/patches")


class ObserverTests(unittest.TestCase):
    def test_frozen_runtime_hashes_and_injection_seams(self):
        for component, (digest, name) in SPECS.items():
            path = SOURCE_ROOT / (component + ".py")
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            instrument(raw.decode(), str(path), name, {}, component)

    def test_disabled_does_not_access_modules(self):
        with patch.dict(os.environ, {SWITCH: "0"}):
            handle = install(None, None, request_id=None, layers=None)
            self.assertEqual(handle.changes, [])
            handle.uninstall()

    def test_gdn_hook_order_and_return_preserved(self):
        source = """def core(ssm_cache, x):
    h_batch = x + 1
    cache_composes = 0
    ssm_cache.index_copy_(0, 0, h_batch)
    return h_batch
"""
        events = []
        class Cache:
            def index_copy_(self, *args):
                events.append(("write", args[-1]))
        namespace = {HOOK: lambda stage, frame: events.append((stage, frame["h_batch"]))}
        fn = instrument(source, "fixture", "core", namespace, "gdn")
        self.assertEqual(fn(Cache(), 4), 5)
        self.assertEqual(events, [("gdn_initial", 5), ("write", 5),
                                  ("gdn_committed", 5)])

    def test_ambiguous_gdn_seam_rejected(self):
        with self.assertRaisesRegex(ValueError, "seam drift"):
            instrument("def core():\n    return None\n", "fixture", "core", {}, "gdn")

    def test_transactional_install_filtering_and_uninstall(self):
        with tempfile.TemporaryDirectory() as directory:
            modules, hashes = {}, {}
            source_by_component = {
                "gdn": """def _position_independent_gdn_core(ctx, layer_name, ssm_cache):
    cache_composes = 0
    ssm_cache.index_copy_(0, 0, 1)
""",
                "attention": """def _repair_position_independent_kv(ctx, layer_name):
    value = 1
""",
                "runner": """def _rewrite_position_independent_inputs(ctx, layer_name):
    value = 1
""",
            }
            for component, source in source_by_component.items():
                path = Path(directory) / (component + ".py")
                path.write_text(source)
                module = types.ModuleType("fixture_" + component)
                module.__file__ = str(path)
                exec(compile(source, str(path), "exec"), module.__dict__)
                modules[component] = module
                hashes[component] = hashlib.sha256(source.encode()).hexdigest()
            originals = {k: getattr(v, SPECS[k][1]) for k, v in modules.items()}
            events = []
            ctx = types.SimpleNamespace(req_ids=("target",),
                plans={"target": types.SimpleNamespace(entries=(object(),))})
            with patch.dict(os.environ, {SWITCH: "1"}):
                wrong = dict(hashes, runner="bad")
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    install(modules, lambda *a: None, request_id="target",
                            layers={"layer0"}, source_hashes=wrong)
                for key, module in modules.items():
                    self.assertIs(getattr(module, SPECS[key][1]), originals[key])
                    self.assertFalse(hasattr(module, HOOK))
                handle = install(modules, lambda stage, req, frame: events.append(stage),
                    request_id="target", layers={"layer0"}, source_hashes=hashes)
                modules["attention"]._repair_position_independent_kv(ctx, "other")
                self.assertEqual(events, [])
                modules["attention"]._repair_position_independent_kv(ctx, "layer0")
                self.assertEqual(events, ["kv_committed"])
                ctx.plans["target"].entries = (None,)
                modules["attention"]._repair_position_independent_kv(ctx, "layer0")
                self.assertEqual(events, ["kv_committed"])
                handle.uninstall()
                for key, module in modules.items():
                    self.assertIs(getattr(module, SPECS[key][1]), originals[key])
                    self.assertFalse(hasattr(module, HOOK))


if __name__ == "__main__":
    unittest.main()
