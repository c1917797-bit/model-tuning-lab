"""Pure-stdlib source/IEEE controls; no real raw/precondition/NPU qualification."""
import ast, contextlib, hashlib, importlib.util, io, os, struct, sys, unittest
from pathlib import Path
P = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location("power2_source_controls", P / "control.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
def fp32(x): return struct.unpack("f", struct.pack("f", x))[0]
def half(x): return struct.unpack("e", struct.pack("e", x))[0]
class Controls(unittest.TestCase):
    def test01_cold_without_runtime(self):
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(m.main([]), 0)
        self.assertNotIn("torch", sys.modules); self.assertNotIn("torch_npu", sys.modules)
    def test02_original_half_subnormal_can_lose_one_bit(self):
        x = fp32(2**-18 + 2**-25)
        self.assertEqual(abs(half(x) - x), 2**-25)
        self.assertEqual(half(x * 2), x * 2)
    def test03_reciprocal_K_can_create_new_loss_and_must_not_be_waived(self):
        x = fp32(2**-17 + 2**-24)
        self.assertEqual(half(x), x)
        self.assertNotEqual(half(x * .5), x * .5)
    def test04_overflow_and_underflow_not_exempted(self):
        with self.assertRaises((OverflowError, struct.error)): half(65504.0 * 2)
        self.assertNotEqual(half(2**-25), 2**-25)
        text = (P / "control.py").read_text()
        self.assertIn('"scaled_nonzero_inputs_not_zeroed"', text)
        self.assertIn('"scaled_half_finite"', text)
    def test05_all_products_scores_outputs_not_sampled(self):
        text = (P / "control.py").read_text()
        for n in ("all49152_FP32_products_bitwise_equal", "full192_FP32_QK_bitwise_equal", "full192_FP32_half_roundtrip_QK_bitwise_equal", "full1536_ideal_AV_inverse_scale_bitwise_equal", "full1536_scaled_post_BF16_matches_saved_golden"):
            self.assertIn(n, text)
    def test06_original_reference_source_unchanged(self):
        p = Path(os.environ.get("ADAKV_POWER2_SOFTWARE_REFERENCE_SOURCE", m.GOLDEN_REF["path"]))
        self.assertEqual(p.stat().st_size, m.GOLDEN_REF["bytes"])
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), m.GOLDEN_REF["sha256"])
        fn = next(n for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "reference")
        self.assertTrue(ast.get_source_segment(p.read_text(), fn).endswith(".to(q.dtype)"))
    def test07_no_native_invocation_and_no_hidden_clock_extension(self):
        tree = ast.parse((P / "control.py").read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertFalse(any(x and x.startswith("torch_npu") for x in imports))
        self.assertNotIn("npu_fused_infer_attention_score", (P / "control.py").read_text())
        self.assertEqual((m.START, m.CUT), (1791835594, 1791878794))
        self.assertEqual(m.FACTORS, {"query": 2., "key": .5, "value": 2.})
    def test08_full_physical_inputs_and_FP32_output_rescale(self):
        text = (P / "control.py").read_text()
        self.assertIn('"key": raw["expected_key"].float()', text)
        self.assertIn('"value": raw["expected_value"].float()', text)
        self.assertIn('y = x * .5', text)
        self.assertIn('return y.to(t.bfloat16)', text)
if __name__ == "__main__": unittest.main()
