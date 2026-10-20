"""The new precision seam is exact; original mathematical code remains pinned."""
import unittest,hashlib,json
from pathlib import Path
from repair14_ledger import previous_text,reverse
import g1_inverse as G1
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_only_declared_FA_precision_boundary_and_inverse_negative(self):
  current=(P/"model_entry.py").read_text()
  actual=G1.previous_text(P/"model_entry.py")
  new="  from fa_fp16_boundary import FiaBoundary\n  boundary=FiaBoundary(t,self.torch_npu,trial)\n  out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)"
  old="  out,_=self.A.native(t,self.torch_npu,trial,actual_fia,sparse_mode=1)"
  self.assertEqual(actual.count(new),1)
  ar_new="  from ar_fp16_boundary import NativeARBoundary\n  boundary=NativeARBoundary(t,self.torch_npu,ctx.captures[b['index']],self.own_source['files']['ar_fp16_boundary.py'],self.own_source['native_ar_boundary_repair']['evidence'])\n  out,_=boundary.npu_fused_infer_attention_score(query=q,key=k,value=v,input_layout='BNSD',num_heads=6,num_key_value_heads=1,scale=256**-.5,actual_seq_lengths=[1],actual_seq_lengths_kv=[cache['key'].shape[0]],sparse_mode=0,pre_tokens=2147483647,next_tokens=2147483647,inner_precise=0)"
  ar_old="  out,_=self.torch_npu.npu_fused_infer_attention_score(query=q,key=k,value=v,input_layout='BNSD',num_heads=6,num_key_value_heads=1,scale=256**-.5,actual_seq_lengths=[1],actual_seq_lengths_kv=[cache['key'].shape[0]],sparse_mode=0,pre_tokens=2147483647,next_tokens=2147483647,inner_precise=0)"
  self.assertEqual(actual.count(ar_new),1)
  self.assertEqual(actual.replace(new,old).replace(ar_new,ar_old),previous_text(P/"model_entry.py"))
  with self.assertRaisesRegex(ValueError,"current source differs"):reverse("model_entry.py",current+"# undeclared\n")
  with self.assertRaisesRegex(ValueError,"current source differs"):G1.reverse("model_entry.py",current+"# undeclared\n")
  ledger=json.loads((P/"FA_BOUNDARY_EDITS_R14.json").read_text())
  self.assertNotIn("independent_model.py",ledger);self.assertNotIn("oracle112.py",ledger)
  self.assertNotIn("adapter.py",ledger);self.assertNotIn("core112.py",ledger)
if __name__=="__main__":unittest.main()
