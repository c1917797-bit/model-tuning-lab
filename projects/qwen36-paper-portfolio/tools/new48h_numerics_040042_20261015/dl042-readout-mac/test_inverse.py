import importlib.util,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Inverse(unittest.TestCase):
 def test_inverse_all16(self):
  s=importlib.util.spec_from_file_location('_042_inverse_test',P/'verify_inverse.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);self.assertEqual(len(m.verify(P)),16)
 def test_singlefactor_production_no_debug_or_fullstate(self):
  t=(P/'kernel/readout_mac042/op_kernel/qwen36_gdn_deltalog_decode_readout_mac042.h').read_text();a=t.index('inline void AppendTile(');b=t.index('inline void StoreOutput(',a);x=t[a:b];self.assertEqual(x.count('DL_FINAL_COMPOUND_BEGIN'),1);self.assertNotIn('StoreBase(',x);self.assertNotIn('DataCopy(precast',t);self.assertNotIn('double',t);self.assertIn('StoreULog(',x)
 def test_missing_actualbuild_ref_refused(self):
  s=importlib.util.spec_from_file_location('_042_bind_test',P/'bind_frame.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with self.assertRaises(Exception):m.bind(m.ref(P/'frame/SOURCE_TEMPLATE.json'),{'path':'missing','bytes':0,'sha256':'0'*64})
