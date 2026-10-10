"""Stdlib integer/AST regression for masked KIVI uint32 -> int32 -> float32."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import struct
import sys
import unittest
from unittest import mock

HERE = Path(os.path.abspath(__file__)).parent
BASELINE = None
LEGACY = None
BASE_KERNEL_SHA = "30f8474cb9b3de84fb8fd7b6e463d0993de232d0fa727ee2cb1b8729c4568c67"
BASE_TEST_SHA = "001cf0beb17b56dcbc27d7b9ee6f8beafaca99edb38ebf4fa76d61b75756816e"
OLD_ORIGINAL_SHA = "72771419067bc420c6cb812e67d97a9a13e84b30f6bff16045319836455b1137"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def expression_extract(word, bits, position):
    if bits not in (2, 4) or not 0 <= word <= 0xffffffff or not 0 <= position < 32 // bits:
        raise ValueError("unsupported integer regression domain")
    return (word >> (position * bits)) & ((1 << bits) - 1)

def byte_reference(word, bits, position):
    # Independent little-endian bit reader, not the kernel shift-mask expression.
    data = word.to_bytes(4, "little", signed=False)
    value = 0
    start = position * bits
    for offset in range(bits):
        bit = start + offset
        value += ((data[bit // 8] >> (bit % 8)) & 1) * (2 ** offset)
    return value

def signed_then_float32(code):
    signed = struct.unpack("<i", struct.pack("<I", code))[0]
    return signed, struct.unpack("<f", struct.pack("<f", signed))[0]

def find_named(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)

def is_tl_type(node, name):
    return (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "tl" and node.attr == name)

class ProjectOnlyMaskedSigned(ast.NodeTransformer):
    def __init__(self):
        self.count = 0

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if (isinstance(node.func, ast.Attribute) and node.func.attr == "to"
                and len(node.args) == 1 and is_tl_type(node.args[0], "int32")):
            if node.keywords or not isinstance(node.func.value, ast.Name) or node.func.value.id != "code":
                raise ValueError("signed cast outside masked code forbidden")
            self.count += 1
            return node.func.value
        return node

class MaskedSignedTests(unittest.TestCase):
    def old(self):
        return (BASELINE / "kernel.py").read_text(encoding="utf-8")

    def new(self):
        return (HERE / "kernel.py").read_text(encoding="utf-8")

    def test_exact_source_only_two_cast_chains_change(self):
        old = self.old()
        self.assertEqual(old.count("code.to(tl.float32)"), 2)
        self.assertEqual(self.new(), old.replace("code.to(tl.float32)",
                                                "code.to(tl.int32).to(tl.float32)"))
        self.assertEqual(self.new().count("code.to(tl.int32).to(tl.float32)"), 2)

    def test_entire_ast_only_masked_int32_casts_project_back_to_base(self):
        original = ast.parse(self.old())
        new = ast.parse(self.new())
        project = ProjectOnlyMaskedSigned()
        restored = project.visit(new)
        self.assertEqual(project.count, 2)
        self.assertEqual(ast.dump(original, include_attributes=False),
                         ast.dump(restored, include_attributes=False))

    def test_unsigned_word_shift_and_mask_unmodified_in_both_kernels(self):
        original = ast.parse(self.old())
        new = ast.parse(self.new())
        for name in ("qk", "av"):
            a, b = find_named(original, name), find_named(new, name)
            for variable in ("word", "code"):
                aa = next(x for x in ast.walk(a) if isinstance(x, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == variable for t in x.targets))
                bb = next(x for x in ast.walk(b) if isinstance(x, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == variable for t in x.targets))
                self.assertEqual(ast.dump(aa, include_attributes=False), ast.dump(bb, include_attributes=False))
            word = next(x for x in ast.walk(b) if isinstance(x, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "word" for t in x.targets))
            self.assertTrue(is_tl_type(word.value.args[0], "uint32"))
            code = next(x for x in ast.walk(b) if isinstance(x, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "code" for t in x.targets))
            self.assertIsInstance(code.value.op, ast.BitAnd)
            self.assertIsInstance(code.value.left.op, ast.RShift)

    def test_a16_rounding_forward_and_softmax_are_unchanged(self):
        original, new = ast.parse(self.old()), ast.parse(self.new())
        for name in ("forward", "softmax", "_bind_jit_tl"):
            self.assertEqual(ast.dump(find_named(original, name), include_attributes=False),
                             ast.dump(find_named(new, name), include_attributes=False))
        for name in ("qk", "av"):
            a, b = find_named(original, name), find_named(new, name)
            def rounds(fn):
                return [ast.dump(x, include_attributes=False) for x in ast.walk(fn)
                        if isinstance(x, ast.keyword) and x.arg == "fp_downcast_rounding"]
            self.assertEqual(rounds(a), rounds(b))
            self.assertGreaterEqual(len(rounds(b)), 2)
        self.assertEqual(self.new().count("enable_fp_fusion=False"),
                         self.old().count("enable_fp_fusion=False"))

    def test_all_2_4bit_codes_and_positions_int32_fp32_exact(self):
        for bits in (2, 4):
            maximum = (1 << bits) - 1
            for position in range(32 // bits):
                for code in range(maximum + 1):
                    # All surrounding bits set, including bit31 when outside field.
                    mask = maximum << (position * bits)
                    word = (0xffffffff & ~mask) | (code << (position * bits))
                    actual = expression_extract(word, bits, position)
                    reference = byte_reference(word, bits, position)
                    signed, f32 = signed_then_float32(actual)
                    self.assertEqual((actual, reference, signed, f32),
                                     (code, code, code, float(code)))
                    self.assertLessEqual(actual, 15)

    def test_deterministic_u32_words_independent_byte_unpack_highbit(self):
        rng = random.Random(20261010)
        words = [0, 1, 0x7fffffff, 0x80000000, 0xffffffff, 0xa5a5a5a5, 0x5a5a5a5a]
        words.extend(rng.getrandbits(32) for _ in range(1024))
        for bits in (2, 4):
            for word in words:
                for position in range(32 // bits):
                    code = expression_extract(word, bits, position)
                    reference = byte_reference(word, bits, position)
                    signed, f32 = signed_then_float32(code)
                    self.assertEqual(reference, code)
                    self.assertEqual(signed, code)
                    self.assertEqual(f32, float(reference))
        with self.assertRaisesRegex(ValueError, "unsupported"):
            expression_extract(0, 8, 0)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            expression_extract(1 << 32, 2, 0)

    def test_current_all3_jit_globals_same_backend_and_rebind_rejected(self):
        module = LEGACY.load_module(HERE / "kernel.py")
        language = LEGACY.FakeLanguage()
        with mock.patch.dict(os.environ, {module.ENV: "1"}):
            model, _, jit = LEGACY.call_build(module, language)
            self.assertEqual([x.__name__ for x in jit.functions], ["qk", "softmax", "av"])
            for fn in jit.functions:
                self.assertIs(eval("tl", fn.__globals__), language)
            LEGACY.call_build(module, language)
            other = LEGACY.FakeLanguage()
            other_jit = LEGACY.FakeJit(other)
            with self.assertRaisesRegex(ValueError, "incompatible"):
                LEGACY.call_build(module, other, other_jit)
            self.assertEqual(other_jit.functions, [])
            self.assertIs(module.tl, language)

    def test_current_default_off_no_backend_or_binding(self):
        module = LEGACY.load_module(HERE / "kernel.py")
        class Untouchable:
            def __getattribute__(self, name):
                raise AssertionError("default OFF touched hardware")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "defaults OFF"):
                module.build(Untouchable(), Untouchable(), Untouchable(),
                             device_properties=Untouchable(), get_format=Untouchable(), qualify=Untouchable())
        self.assertNotIn("tl", module.__dict__)
        self.assertFalse(any(x in sys.modules for x in ("torch", "torch_npu", "triton")))

def main():
    global BASELINE, LEGACY
    p = argparse.ArgumentParser()
    p.add_argument("--baseline-root", type=Path, required=True)
    p.add_argument("--original", type=Path, required=True)
    args = p.parse_args()
    BASELINE = Path(os.path.abspath(args.baseline_root))
    original = Path(os.path.abspath(args.original))
    if sha(BASELINE / "kernel.py") != BASE_KERNEL_SHA or sha(BASELINE / "test_kernel.py") != BASE_TEST_SHA:
        raise ValueError("exact inherited TL12 source/test identity")
    if sha(original) != OLD_ORIGINAL_SHA:
        raise ValueError("exact original pre-TL source identity")
    spec = importlib.util.spec_from_file_location("unchanged_tl12", BASELINE / "test_kernel.py")
    LEGACY = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(LEGACY)
    LEGACY.ORIGINAL = original
    # Twelve unchanged prior tests run against unchanged prior source.
    # Eight added tests cover this new current source and exact permitted delta.
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(LEGACY.LanguageGlobals),
        unittest.defaultTestLoader.loadTestsFromTestCase(MaskedSignedTests)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"schema": "kivi.masked-signed-stdlib-regression/v1",
                      "inherited_tests": 12, "current_delta_tests": 8,
                      "tests_run": result.testsRun, "failures": len(result.failures),
                      "errors": len(result.errors), "successful": result.wasSuccessful(),
                      "kernel_sha256": sha(HERE / "kernel.py"), "baseline_sha256": BASE_KERNEL_SHA,
                      "npu_executed": False, "python": sys.version,
                      "torch_imported": "torch" in sys.modules, "triton_imported": "triton" in sys.modules},
                     sort_keys=True))
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
