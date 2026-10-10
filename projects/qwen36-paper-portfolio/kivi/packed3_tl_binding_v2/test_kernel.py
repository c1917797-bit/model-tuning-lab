"""Stdlib-only regression: actual Python fn.__globals__ compiler boundary."""
import argparse
import ast
import builtins
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import textwrap
import types
import unittest
from unittest import mock

ORIGINAL_SHA256 = "72771419067bc420c6cb812e67d97a9a13e84b30f6bff16045319836455b1137"
HERE = Path(os.path.abspath(__file__)).parent
ORIGINAL = None
SERIAL = 0

def load_module(path):
    global SERIAL
    SERIAL += 1
    spec = importlib.util.spec_from_file_location("kivi_tl_fixture_%d" % SERIAL, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class FakeLanguage:
    def __init__(self):
        self.constexpr = object()

class FakeJit:
    """Emulate the compiler's name lookup; do not evaluate kernel math."""
    def __init__(self, language):
        self.language = language
        self.functions = []

    def jit(self, fn):
        # Real compiler resolves tl from globals. This raises for the old file.
        found = eval("tl", fn.__globals__)
        if found is not self.language:
            raise ValueError("fake JIT incompatible language globals")
        source = textwrap.dedent(inspect.getsource(fn))
        names = [x for x in ast.walk(ast.parse(source))
                 if isinstance(x, ast.Name) and x.id == "tl"]
        if not names:
            raise AssertionError("fixture did not exercise actual kernel source")
        for value in fn.__annotations__.values():
            if value is not self.language.constexpr:
                raise AssertionError("annotation language differs from globals")
        self.functions.append(fn)
        return types.SimpleNamespace(fn=fn)

class FakeModule:
    pass

def torch_stub():
    return types.SimpleNamespace(nn=types.SimpleNamespace(Module=FakeModule))

def call_build(module, language=None, jit=None, qualify=None, properties=None,
               get_format=lambda value: 2):
    language = language or FakeLanguage()
    jit = jit or FakeJit(language)
    result = module.build(
        torch_stub(), jit, language,
        device_properties=properties or {"num_aicore": 24, "num_vectorcore": 48},
        get_format=get_format, qualify=qualify or (lambda: None))
    return result, language, jit

def functions_from(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    build = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "build")
    kernels = {x.name: ast.dump(x, include_attributes=False) for x in build.body
               if isinstance(x, ast.FunctionDef) and x.name in ("qk", "softmax", "av")}
    model = next(x for x in build.body if isinstance(x, ast.ClassDef) and x.name == "ModelNew")
    forward = next(x for x in model.body if isinstance(x, ast.FunctionDef) and x.name == "forward")
    return kernels, ast.dump(forward, include_attributes=False)

class LanguageGlobals(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE": "1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.module = load_module(HERE / "kernel.py")

    def test_original_source_exact_pin(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), ORIGINAL_SHA256)

    def test_actual_old_factory_reproduces_globals_nameerror(self):
        old = load_module(ORIGINAL)
        with self.assertRaisesRegex(NameError, "tl"):
            call_build(old)
        self.assertNotIn("tl", old.__dict__)

    def test_all_three_jit_functions_resolve_same_actual_global(self):
        model, language, jit = call_build(self.module)
        self.assertEqual([f.__name__ for f in jit.functions], ["qk", "softmax", "av"])
        instance = model()
        for name, fn in zip(("qk", "softmax", "av"), jit.functions):
            self.assertIs(fn.__globals__, self.module.__dict__)
            self.assertIs(eval("tl.constexpr", fn.__globals__), language.constexpr)
            self.assertIs(inspect.getclosurevars(fn).nonlocals["tl"], language)
            self.assertIs(getattr(instance, name).fn, fn)

    def test_same_language_repeated_build_allowed(self):
        language = FakeLanguage()
        one, _, jit1 = call_build(self.module, language)
        two, _, jit2 = call_build(self.module, language)
        self.assertEqual(len(jit1.functions), 3)
        self.assertEqual(len(jit2.functions), 3)
        self.assertIsNot(one, two)
        self.assertIs(self.module.__dict__["tl"], language)

    def test_incompatible_language_rebinding_hardreject_before_jit(self):
        old_language = FakeLanguage()
        call_build(self.module, old_language)
        new_language = FakeLanguage()
        new_jit = FakeJit(new_language)
        with self.assertRaisesRegex(ValueError, "incompatible Triton language global rebinding"):
            call_build(self.module, new_language, new_jit)
        self.assertEqual(new_jit.functions, [])
        self.assertIs(self.module.__dict__["tl"], old_language)

    def test_preexisting_incompatible_global_hardreject(self):
        self.module.tl = object()
        original_global = self.module.tl
        jit = FakeJit(FakeLanguage())
        with self.assertRaisesRegex(ValueError, "incompatible"):
            call_build(self.module, jit.language, jit)
        self.assertIs(self.module.tl, original_global)
        self.assertEqual(jit.functions, [])

    def test_default_off_never_touches_backend_or_qualify_or_globals(self):
        class Untouchable:
            def __getattribute__(self, name):
                raise AssertionError("default OFF touched backend")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "defaults OFF"):
                self.module.build(Untouchable(), Untouchable(), Untouchable(),
                                  device_properties=Untouchable(),
                                  get_format=Untouchable(), qualify=Untouchable())
        self.assertNotIn("tl", self.module.__dict__)

    def test_default_off_source_imports_no_torch_triton_or_numpy(self):
        actual_import = builtins.__import__
        seen = []
        def guarded(name, *args, **kwargs):
            seen.append(name)
            if name.split(".")[0] in ("torch", "torch_npu", "triton", "numpy"):
                raise AssertionError("hardware dependency import during source load")
            return actual_import(name, *args, **kwargs)
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("builtins.__import__", guarded):
            module = load_module(HERE / "kernel.py")
        self.assertNotIn("tl", module.__dict__)
        self.assertFalse(any(n.split(".")[0] in ("torch", "torch_npu", "triton", "numpy") for n in seen))
        tree = ast.parse((HERE / "kernel.py").read_text(encoding="utf-8"))
        imports = [x.names[0].name for x in tree.body if isinstance(x, ast.Import)]
        self.assertEqual(imports, ["os"])

    def test_qualification_failure_does_not_bind_or_compile(self):
        jit = FakeJit(FakeLanguage())
        def rejected():
            raise RuntimeError("actual source qualification denied")
        with self.assertRaisesRegex(RuntimeError, "qualification denied"):
            call_build(self.module, jit.language, jit, qualify=rejected)
        self.assertNotIn("tl", self.module.__dict__)
        self.assertEqual(jit.functions, [])

    def test_invalid_format_getter_does_not_bind(self):
        with self.assertRaisesRegex(ValueError, "format getter"):
            call_build(self.module, get_format=None)
        self.assertNotIn("tl", self.module.__dict__)

    def test_invalid_core_properties_do_not_bind_or_compile(self):
        for props in ({"num_aicore": 0, "num_vectorcore": 48},
                      {"num_aicore": True, "num_vectorcore": 48},
                      {"num_aicore": 24, "num_vectorcore": 65536},
                      {"num_aicore": 24, "num_vectorcore": 0}):
            jit = FakeJit(FakeLanguage())
            with self.assertRaisesRegex(ValueError, "actual core properties"):
                call_build(self.module, jit.language, jit, properties=props)
            self.assertNotIn("tl", self.module.__dict__)
            self.assertEqual(jit.functions, [])

    def test_three_kernel_asts_and_full_forward_are_byte_semantics_unchanged(self):
        old, old_forward = functions_from(ORIGINAL)
        new, new_forward = functions_from(HERE / "kernel.py")
        self.assertEqual(set(old), {"qk", "softmax", "av"})
        self.assertEqual(old, new)
        self.assertEqual(old_forward, new_forward)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--original", required=True, type=Path)
    a = p.parse_args()
    ORIGINAL = Path(os.path.abspath(a.original))
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LanguageGlobals)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"schema": "kivi.tl-globals-stdlib-regression/v1",
                      "tests_run": result.testsRun,
                      "failures": len(result.failures), "errors": len(result.errors),
                      "successful": result.wasSuccessful(),
                      "python": sys.version, "original_sha256": ORIGINAL_SHA256,
                      "npu_executed": False, "torch_imported": "torch" in sys.modules,
                      "triton_imported": "triton" in sys.modules}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
