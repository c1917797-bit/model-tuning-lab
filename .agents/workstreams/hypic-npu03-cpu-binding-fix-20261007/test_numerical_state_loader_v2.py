import importlib
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch
import numerical_state_loader as old
import numerical_state_loader_v2 as new


class FinderTests(unittest.TestCase):
    def test_editable_finder_after_pathfinder(self):
        calls = []
        class Loader:
            def create_module(self, spec):
                return None
            def exec_module(self, module):
                calls.append("loaded")
                module.register = lambda: None
        class Editable:
            @classmethod
            def find_spec(cls, fullname, path=None, target=None):
                calls.append("editable")
                return importlib.util.spec_from_loader(fullname, Loader())
        hook = new.RegistrationFinder({})
        adapter = types.SimpleNamespace(uninstall=lambda: calls.append("uninstalled"))
        with patch.object(new, "RuntimeAdapter", return_value=adapter), \
             patch.object(sys, "meta_path", [hook, importlib.machinery.PathFinder, Editable]), \
             patch.object(importlib.machinery.PathFinder, "find_spec", return_value=None):
            try:
                with self.assertRaises(ImportError):
                    old.RegistrationFinder({}).find_spec(old.TARGET)
                importlib.import_module(old.TARGET)
                self.assertEqual(calls, ["editable", "loaded"])
                self.assertIs(hook.adapter, adapter)
                hook.uninstall()
                self.assertNotIn(hook, sys.meta_path)
            finally:
                sys.modules.pop(old.TARGET, None)

    def test_non_target_and_absent(self):
        hook = new.RegistrationFinder({})
        self.assertIsNone(hook.find_spec("not_hypic"))
        with patch.object(sys, "meta_path", [hook]):
            with self.assertRaises(ImportError):
                hook.find_spec(old.TARGET)

    def test_default_disabled_unchanged(self):
        with patch.dict(old.os.environ, {old.SWITCH: "0"}):
            before = list(sys.meta_path)
            self.assertIsNone(new.activate(None))
            self.assertEqual(sys.meta_path, before)

    def test_resolver_failure_propagates(self):
        class Broken:
            def find_spec(self, *args):
                raise ValueError("broken real finder")
        hook = new.RegistrationFinder({})
        with patch.object(sys, "meta_path", [hook, Broken()]):
            with self.assertRaisesRegex(ValueError, "broken real finder"):
                hook.find_spec(old.TARGET)


if __name__ == "__main__":
    unittest.main()
