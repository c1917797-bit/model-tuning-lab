"""CPU boundary/negative controls; no HAL or kernel success is emulated."""
import unittest,types
import torch
from fa_fp16_boundary import FiaBoundary
def arguments():
 return dict(query=torch.ones((1,6,3,256),dtype=torch.bfloat16),
  key=torch.ones((2,1,128,256),dtype=torch.bfloat16),value=torch.ones((2,1,128,256),dtype=torch.bfloat16),
  atten_mask=torch.zeros((1,1,3,256),dtype=torch.bool),block_table=torch.tensor([[0,1]],dtype=torch.int32),
  input_layout="BNSD",block_size=128,actual_seq_lengths=[3],actual_seq_lengths_kv=[134],
  num_key_value_heads=1,num_heads=6,scale=256**-.5,sparse_mode=1,
  pre_tokens=2147483647,next_tokens=2147483647,inner_precise=2)
def delegate(**kw):return torch.ones((1,6,3,256),dtype=torch.float16),None
class Tests(unittest.TestCase):
 def make(self,fn=delegate):
  trial={};return FiaBoundary(torch,types.SimpleNamespace(npu_fused_infer_attention_score=fn),trial),trial
 def test_cast_and_exact_parameters(self):
  a=arguments();seen=[]
  def called(**kw):
   seen.append(kw)
   for k in ("query","key","value"):self.assertEqual(kw[k].dtype,torch.float16)
   for k in ("atten_mask","block_table"):self.assertIs(kw[k],a[k])
   self.assertEqual(kw["inner_precise"],a["inner_precise"]);return delegate(**kw)
  f,trial=self.make(called);out,_=f.npu_fused_infer_attention_score(**a)
  self.assertEqual(out.dtype,torch.bfloat16);self.assertTrue(trial["fp16_boundary"]["completed"]);self.assertEqual(len(seen),1)
 def test_wrong_shape_rejected(self):
  f,_=self.make();a=arguments();a["query"]=a["query"][:,:,:1]
  with self.assertRaisesRegex(ValueError,"three-node"):f.npu_fused_infer_attention_score(**a)
 def test_wrong_dtype_rejected(self):
  f,_=self.make();a=arguments();a["query"]=a["query"].float()
  with self.assertRaisesRegex(ValueError,"input BF16"):f.npu_fused_infer_attention_score(**a)
 def test_overflow_rejected(self):
  f,_=self.make();a=arguments();a["query"].fill_(1e10)
  with self.assertRaisesRegex(ValueError,"FP16 conversion"):f.npu_fused_infer_attention_score(**a)
 def test_nonfinite_rejected(self):
  f,_=self.make();a=arguments();a["query"].fill_(float("nan"))
  with self.assertRaisesRegex(ValueError,"original QKV"):f.npu_fused_infer_attention_score(**a)
 def test_wrong_output_dtype_rejected(self):
  f,_=self.make(lambda **kw:(torch.ones((1,6,3,256),dtype=torch.bfloat16),None))
  with self.assertRaisesRegex(ValueError,"FP16 FIA output"):f.npu_fused_infer_attention_score(**arguments())
 def test_input_mutation_rejected(self):
  def mutate(**kw):kw["query"].add_(1);return delegate(**kw)
  f,_=self.make(mutate)
  with self.assertRaisesRegex(ValueError,"preserves converted"):f.npu_fused_infer_attention_score(**arguments())
 def test_second_call_rejected(self):
  f,_=self.make();f.npu_fused_infer_attention_score(**arguments())
  with self.assertRaisesRegex(ValueError,"cannot repeat"):f.npu_fused_infer_attention_score(**arguments())
if __name__=="__main__":unittest.main()
