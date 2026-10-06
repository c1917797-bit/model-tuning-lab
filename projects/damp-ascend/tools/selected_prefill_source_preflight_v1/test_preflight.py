"""Synthetic stdlib checks only. They cannot issue MAIN/NPU authority."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("selected_source_preflight_test_module",
                                             Path(__file__).with_name("preflight.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

SYNTHETIC_EF = '''
class DisableContext:
    def __init__(self):
        self.callback = None
        self.msg = None
        self.wrapping = True
    def __call__(self, fn):
        self = self
        def _fn(*args, **kwargs):
            if self.wrapping:
                return fn(*args, **kwargs)
            raise RuntimeError()
        _fn.__wrapped__ = fn
        _fn._torchdynamo_orig_callable = fn
        _fn._torchdynamo_disable = True
        _fn._torchdynamo_disable_recursive = True
        _fn._torchdynamo_disable_msg = None
        _fn.__name__ = fn.__name__
        _fn.__qualname__ = fn.__qualname__
        return _fn
'''
SYNTHETIC_FN = "def chunk_gated_delta_rule():\n    raise AssertionError('never execute')\n"

def module(name, path, source):
    result = types.ModuleType(name)
    result.__file__ = path
    result.__loader__ = object()
    sys.modules[name] = result
    exec(compile(source, path, "exec", dont_inherit=True), result.__dict__)
    return result

def bundle():
    ef = module("SYNTHETIC_selected_ef", m.EVAL_FRAME, SYNTHETIC_EF)
    chunk = module("SYNTHETIC_selected_chunk", m.CHUNK, SYNTHETIC_FN)
    compiler_src = "def disable(fn):\n    return DisableContext()(fn)\n"
    dec_src = "def disable(fn):\n    return DisableContext()(fn)\n"
    compiler = module("SYNTHETIC_selected_compiler", m.COMPILER, compiler_src)
    dec = module("SYNTHETIC_selected_decorators", m.DECORATORS, dec_src)
    compiler.DisableContext = dec.DisableContext = ef.DisableContext
    outer = ef.DisableContext()(chunk.chunk_gated_delta_rule)
    chunk.chunk_gated_delta_rule = outer
    gdn = types.SimpleNamespace(__file__=m.GDN, chunk_gated_delta_rule=outer)
    torch = types.SimpleNamespace(__version__="2.10.0+cpu", compiler=compiler,
                                  _dynamo=types.SimpleNamespace(disable=dec.disable))
    raw = {m.EVAL_FRAME: SYNTHETIC_EF.encode(), m.CHUNK: SYNTHETIC_FN.encode(),
           m.COMPILER: compiler_src.encode(), m.DECORATORS: dec_src.encode(), m.GDN: b"SYNTHETIC\n"}
    return torch, gdn, chunk, compiler, dec, ef, raw

class PreflightTests(unittest.TestCase):
    def wrapper(self):
        data = bundle()
        return data, data[1].chunk_gated_delta_rule, data[1].chunk_gated_delta_rule.__wrapped__

    def test_01_import_and_default_do_not_import_torch(self):
        before = {x for x in sys.modules if x == "torch" or x.startswith("torch.")}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(m.main([]), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "disabled")
        self.assertFalse(report["npu_executed"])
        self.assertEqual(before, {x for x in sys.modules if x == "torch" or x.startswith("torch.")})

    def test_02_two_level_canonical_wrapper(self):
        data, outer, inner = self.wrapper()
        observation = {}
        self.assertIs(m.prove_wrapper(outer, inner, data[5], observation), outer)
        self.assertTrue(observation["wrapper"]["code_is_canonical"])

    def test_03_different_canonical_code_rejected(self):
        data, outer, inner = self.wrapper()
        def foreign(*args, **kwargs):
            return None
        with self.assertRaises(m.Pending):
            m.prove_wrapper(foreign, inner, data[5], {})

    def test_04_backlink_mismatch_rejected(self):
        data, outer, inner = self.wrapper()
        outer._torchdynamo_orig_callable = object()
        with self.assertRaises(m.Pending):
            m.prove_wrapper(outer, inner, data[5], {})

    def test_05_cycle_rejected(self):
        data, outer, inner = self.wrapper()
        outer.__wrapped__ = outer
        with self.assertRaises(m.Pending):
            m.prove_wrapper(outer, inner, data[5], {})

    def test_06_extra_inner_wrapper_rejected(self):
        data, outer, inner = self.wrapper()
        inner.__wrapped__ = object()
        with self.assertRaises(m.Pending):
            m.prove_wrapper(outer, inner, data[5], {})

    def test_07_disable_flags_rejected(self):
        for field in ("_torchdynamo_disable", "_torchdynamo_disable_recursive"):
            data, outer, inner = self.wrapper()
            setattr(outer, field, False)
            with self.assertRaises(m.Pending):
                m.prove_wrapper(outer, inner, data[5], {})

    def test_08_context_options_rejected(self):
        for field, value in (("callback", object()), ("msg", "different"), ("wrapping", False)):
            data, outer, inner = self.wrapper()
            cells = dict(zip(outer.__code__.co_freevars, outer.__closure__))
            setattr(cells["self"].cell_contents, field, value)
            with self.assertRaises(m.Pending):
                m.prove_wrapper(outer, inner, data[5], {})

    def test_09_closure_function_rejected(self):
        data, outer, inner = self.wrapper()
        cells = dict(zip(outer.__code__.co_freevars, outer.__closure__))
        cells["fn"].cell_contents = lambda: None
        with self.assertRaises(m.Pending):
            m.prove_wrapper(outer, inner, data[5], {})

    def test_10_code_comparison_checks_body_not_name(self):
        data = bundle()
        raw = data[-1]
        observation = {}
        m.prove_code(data[3].disable, raw, m.COMPILER, "disable", observation, "fn")
        changed = dict(raw)
        changed[m.COMPILER] = b"def disable(fn):\n    return None\n"
        with self.assertRaises(m.Pending):
            m.prove_code(data[3].disable, changed, m.COMPILER, "disable", {}, "fn")

    def test_11_source_drift_recorded_before_failure(self):
        observation = {}
        with self.assertRaises(m.Pending):
            m.source_checks({"SYNTHETIC": "0" * 64}, observation, lambda path: b"wrong")
        self.assertEqual(observation["source_sha256"]["SYNTHETIC"], hashlib.sha256(b"wrong").hexdigest())

    def test_12_complete_synthetic_native_proof_never_invokes(self):
        data = bundle()
        pins = {p: hashlib.sha256(b).hexdigest() for p, b in data[-1].items()}
        observation = {}
        with patch.dict(m.PINS, pins, clear=True):
            result = m.native_proof(*data[:-1], observation, reader=data[-1].__getitem__)
        self.assertIs(result, data[1].chunk_gated_delta_rule)
        self.assertTrue(observation["verified"])
        self.assertEqual(observation["sources_after"], observation["source_sha256"])

    def test_13_native_alias_rejected_and_observed(self):
        data = bundle()
        data[1].chunk_gated_delta_rule = lambda: None
        pins = {p: hashlib.sha256(b).hexdigest() for p, b in data[-1].items()}
        observation = {}
        with patch.dict(m.PINS, pins, clear=True), self.assertRaises(m.Pending):
            m.native_proof(*data[:-1], observation, reader=data[-1].__getitem__)
        self.assertFalse(observation["native_alias"]["same_object"])

    def test_14_framework_alias_rejected(self):
        data = bundle()
        data[0]._dynamo.disable = lambda fn: fn
        with self.assertRaises(m.Pending):
            m.framework_proof(data[0], *data[3:6], data[-1], {})

    def test_15_opt_in_requires_fresh_output_before_torch_import(self):
        with self.assertRaises(m.Pending):
            m.main(["--execute"])
        with self.assertRaises(m.Pending):
            m.main(["--execute", "--out", "relative.json"])

if __name__ == "__main__":
    unittest.main()
