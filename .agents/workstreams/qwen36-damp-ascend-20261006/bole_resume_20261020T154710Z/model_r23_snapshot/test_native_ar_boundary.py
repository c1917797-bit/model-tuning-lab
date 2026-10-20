"""CPU ABI/negative controls; never an actual FIA execution certificate."""
import unittest,torch,json
from pathlib import Path
from types import SimpleNamespace as NS
import sourceio as C
from ar_fp16_boundary import NativeARBoundary
import ar_fp16_boundary as B
class Tests(unittest.TestCase):
 def fixture(self,length=132,delegate=None):
  if delegate is None:delegate=NS(npu_fused_infer_attention_score=lambda **kw:(kw['query'].clone(),None))
  evidence=json.loads((Path(__file__).parent/'SOURCE_TEMPLATE.json').read_bytes())['native_ar_boundary_repair']['evidence']
  capture={};boundary=NativeARBoundary(torch,delegate,capture,C.ref(B.__file__),evidence)
  kw=dict(query=torch.ones((1,6,1,256),dtype=torch.bfloat16),key=torch.ones((1,1,length,256),dtype=torch.bfloat16),
   value=torch.ones((1,1,length,256),dtype=torch.bfloat16),input_layout='BNSD',num_heads=6,num_key_value_heads=1,
   scale=256**-.5,actual_seq_lengths=[1],actual_seq_lengths_kv=[length],sparse_mode=0,
   pre_tokens=2147483647,next_tokens=2147483647,inner_precise=0)
  return boundary,capture,kw
 def test132_and133_keep_actual_arguments_and_BF16_output(self):
  for length in(132,133):
   calls=[]
   def delegate(**kw):
    calls.append(kw);self.assertEqual(kw['query'].dtype,torch.float16);self.assertEqual(kw['inner_precise'],0)
    return kw['query'].clone(),None
   b,c,k=self.fixture(length,NS(npu_fused_infer_attention_score=delegate));out,_=b.npu_fused_infer_attention_score(**k)
   self.assertEqual(out.dtype,torch.bfloat16);self.assertTrue(c['ar_fp16_boundary']['completed']);self.assertEqual(len(calls),1)
   with self.assertRaises(ValueError):b.npu_fused_infer_attention_score(**k)
 def test_wrong_geometry_or_operation_knob_rejected_before_delegate(self):
  for name,bad in(('inner_precise',2),('sparse_mode',1),('actual_seq_lengths_kv',[131]),('atten_mask',torch.zeros(1))):
   calls=[];b,c,k=self.fixture(delegate=NS(npu_fused_infer_attention_score=lambda **kw:calls.append(kw)))
   k[name]=bad
   with self.assertRaises(ValueError):b.npu_fused_infer_attention_score(**k)
   self.assertEqual(calls,[])
 def test_mutated_converted_input_rejected(self):
  def delegate(**kw):
   kw['key'].zero_();return kw['query'].clone(),None
  b,c,k=self.fixture(delegate=NS(npu_fused_infer_attention_score=delegate))
  with self.assertRaisesRegex(ValueError,'input unchanged'):b.npu_fused_infer_attention_score(**k)
  self.assertFalse(c['ar_fp16_boundary']['completed'])
 def test_fp16_overflow_and_unknown_source_rejected(self):
  b,c,k=self.fixture();k['query'].fill_(1e10)
  with self.assertRaisesRegex(ValueError,'finite AR FP16'):b.npu_fused_infer_attention_score(**k)
  with self.assertRaisesRegex(ValueError,'exact separately'):NativeARBoundary(torch,None,{},dict(path='unknown',bytes=0,sha256='0'*64),{})
if __name__=='__main__':unittest.main()
