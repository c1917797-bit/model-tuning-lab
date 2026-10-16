"""Actual adapter call boundary exercised on CPU; not native FIA evidence."""
import os,types,unittest
from unittest.mock import patch
import torch as t
import adapter as A
import test_component as F
import reference as R

class Tests(unittest.TestCase):
 def test_actual_native_layout_eight_calls(self):
  for length in(0,127,128,131):
   for mode in(0,1):
    f=F.fixture(length);trial=A.prepare(t,*f);calls=[]
    def call(**kw):
     calls.append(kw);self.assertEqual(kw['input_layout'],'BNSD')
     self.assertEqual(tuple(kw['query'].shape),(1,6,3,256))
     p=trial['scratch_k'].shape[0];self.assertEqual(tuple(kw['key'].shape),(p,1,128,256))
     self.assertEqual(tuple(kw['atten_mask'].shape),(1,1,3,p*128))
     self.assertTrue(A.bits(t,kw['key'].permute(0,2,1,3).contiguous(),trial['scratch_k']))
     self.assertTrue(t.equal(kw['atten_mask'][0,0,:,:length+3],trial['mask']))
     self.assertTrue(bool(kw['atten_mask'][0,0,:,length+3:].all()))
     self.assertEqual(kw['block_table'].tolist(),[list(range(p))])
     self.assertEqual(kw['actual_seq_lengths_kv'],[length+3])
     q=kw['query'][0].permute(1,0,2).double()
     k=kw['key'].permute(0,2,1,3).reshape(-1,256).double()
     v=kw['value'].permute(0,2,1,3).reshape(-1,256).double()
     score=t.einsum('nhd,kd->nhk',q,k)*(256**-.5)
     score.masked_fill_(kw['atten_mask'][0,0,:,None,:],-float('inf'))
     result=t.einsum('nhk,kd->nhd',score.softmax(-1),v).bfloat16()
     if getattr(self,'bad_output',False):return result,None
     return result.permute(1,0,2).unsqueeze(0).contiguous(),None
    abi=dict(schema='bole.actual-FIA-installed-ABI/v115',NPU=False,operator_executed=False,
     schema_family={},argument_names=list(('query','key','value','atten_mask','block_table','input_layout','block_size','actual_seq_lengths','actual_seq_lengths_kv','num_key_value_heads','num_heads','scale','sparse_mode','pre_tokens','next_tokens','inner_precise')))
    fake=types.SimpleNamespace(ops=types.SimpleNamespace(npu=types.SimpleNamespace(npu_fused_infer_attention_score=types.SimpleNamespace(_schemas={}))))
    class TorchProxy:
     ops=fake.ops
     def __getattr__(self,n):return getattr(t,n)
    with patch.dict(os.environ,BOLE_PAGED_TREE_ENABLE='1'):
     output,_=A.native(TorchProxy(),types.SimpleNamespace(npu_fused_infer_attention_score=call),trial,abi,sparse_mode=mode)
    expected=R.sequential(t,*f[1:6],f[6],length,dtype=t.double).bfloat16()
    self.assertTrue(A.bits(t,output,expected));self.assertEqual(len(calls),1)
 def test_no_dimension_or_reference_change(self):
  from pathlib import Path
  s=(Path(__file__).parent/'adapter.py').read_text()
  self.assertIn("input_layout='BNSD'",s);self.assertNotIn("input_layout='TND'",s)
  f=F.fixture();self.assertEqual(f[1].shape[-1],256)
  import consume as C
  raw=dict(inputs=dict(q=f[1],k=f[2],v=f[3],kc=f[4],vc=f[5]),owner=dict(length=127),table=f[6],mode=0)
  # Use the real serialized boundary builder, not a bool-only input certificate.
  import dataclasses
  raw['owner']=dataclasses.asdict(f[0]);F.add_boundary(raw)
  self.assertTrue(C.native_boundary(t,raw))
  raw['native_after']['key'][0,0,0,0]+=1
  with self.assertRaisesRegex(ValueError,'operand bytes'):C.native_boundary(t,raw)
  F.add_boundary(raw);raw['native_before']['atten_mask'][0,0,0,-1]=False
  with self.assertRaisesRegex(ValueError,'operand bytes'):C.native_boundary(t,raw)
 def test_wrong_native_output_rejected(self):
  self.bad_output=True
  with self.assertRaisesRegex(ValueError,'exact observed BNSD output'):
   self.test_actual_native_layout_eight_calls()

if __name__=='__main__':unittest.main()
