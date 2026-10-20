"""The new precision seam is exact; original mathematical code remains pinned."""
import unittest,hashlib,json
from pathlib import Path
from repair14_ledger import previous_text,reverse
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_only_declared_FA_precision_boundary_and_inverse_negative(self):
  actual=(P/"model_entry.py").read_text()
  new="  from fa_fp16_boundary import FiaBoundary\n  boundary=FiaBoundary(t,self.torch_npu,trial)\n  out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)"
  old="  out,_=self.A.native(t,self.torch_npu,trial,actual_fia,sparse_mode=1)"
  self.assertEqual(actual.count(new),1)
  self.assertEqual(actual.replace(new,old),previous_text(P/"model_entry.py"))
  with self.assertRaisesRegex(ValueError,"current source differs"):reverse("model_entry.py",actual+"# undeclared\n")
  ledger=json.loads((P/"FA_BOUNDARY_EDITS_R14.json").read_text())
  self.assertNotIn("independent_model.py",ledger);self.assertNotIn("oracle112.py",ledger)
  self.assertNotIn("adapter.py",ledger);self.assertNotIn("core112.py",ledger)
if __name__=="__main__":unittest.main()
