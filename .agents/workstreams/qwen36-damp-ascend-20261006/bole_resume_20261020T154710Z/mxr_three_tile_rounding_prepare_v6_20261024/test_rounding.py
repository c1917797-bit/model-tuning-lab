"""Stdlib source/bit controls, not Torch/NPU numerical qualification."""
import importlib.util,struct,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
    s=importlib.util.spec_from_file_location('_round_'+n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=load('rounding_capture')
class Rounding(unittest.TestCase):
    def test_raw_label_ABI(self):
        correct=dict(schema='mxr.actual-three-tile-rounding-raw/v1',arm='saved_candidate',variant='precast')
        R.validate_raw_labels(correct)
        for key in correct:
            missing=dict(correct);del missing[key]
            with self.assertRaises(ValueError):R.validate_raw_labels(missing)
            for value in ('wrong',None,True,1):
                with self.assertRaises(ValueError):R.validate_raw_labels(dict(correct,**{key:value}))
        with self.assertRaises(ValueError):R.validate_raw_labels([])
    def test_rne_ties_sign_subnormal(self):
        for bits,expected in ((0x3f808000,0x3f80),(0x3f818000,0x3f82),(0xbf808000,0xbf80),(0x00008000,0),(0x00008001,1),(0,0),(0x80000000,0x8000)):
            self.assertEqual(R.round_f32_bits(bits),expected)
        with self.assertRaises(ValueError):R.round_f32_bits(True)
        with self.assertRaises(ValueError):R.round_f32_bits(0x7f800000)
    def test_unknown_native_precast(self):
        r=R.classify_bits(0x3f808001,0x3f81,0x3f80,0x3f81)
        self.assertTrue(r['actual_matches_f32_RNE']);self.assertFalse(r['native_matches_candidate'])
        self.assertFalse(r['exact_real_inverse_rounding_proven']);self.assertIn('unknown',r['native_precast'])
    def test_actual_arithmetic_inverse(self):
        raw=Path(R.VARIANT['path']).read_bytes();module,delta=R.adapt_variant(raw)
        self.assertIn('for iteration in range(2):',delta['observed'])
        self.assertEqual(module.eager.__code__.co_name,'eager')
        bad=raw.replace(b'for iteration in range(2):',b'for iteration in range(3):')
        with self.assertRaises(ValueError):R.adapt_variant(bad)
    def test_source_whole(self):
        M=load('prepare_successor');b=M.render();self.assertEqual(M.inverse(b),b['before'])
        self.assertIsNone(b['manifest']['authority_ref'])
        self.assertEqual(b['manifest']['wu_boundary_scope']['tiles'],[[0,0],[3,2],[19,5]])
        self.assertEqual((b['manifest']['phase_seconds'],b['manifest']['child_seconds'],b['manifest']['cleanup_seconds']),(600,300,90))
        self.assertEqual(b['files']['event_probe.py'],b['before']['event_probe.py'])
        self.assertEqual(b['files']['private_protected_observer.py'],b['before']['private_protected_observer.py'])
if __name__=='__main__':unittest.main()
