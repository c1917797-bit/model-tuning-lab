"""CPU operand controls using the exact original adapter and a labelled fake FIA.

No NPU/operator or actual model success is inferred. Same-image must run these;
this local host may lack Torch, which is recorded as skips rather than PASS.
"""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g3_fia_contract as DOMAIN
import g3_fa_consumer as JOIN
from service_fia import ServiceFiaBoundary
try:
 import torch as t
except ImportError:t=None


def adapter():
 path=P/'adapter.py'
 if not path.exists():path=P.parents[1]/'bole_service_reference/qualified/adapter.py'
 spec=importlib.util.spec_from_file_location('g3_original_adapter_operand_fixture',path)
 value=importlib.util.module_from_spec(spec);sys.modules[spec.name]=value;spec.loader.exec_module(value);return value

@unittest.skipIf(t is None,'local host has no Torch; mandatory actual same-image CPU operand controls remain pending')
class TensorOperandTests(unittest.TestCase):
 def fixture(self,length):
  A=adapter();q=t.arange(3*6*256,dtype=t.float32).reshape(3,6,256).div(4096).to(t.bfloat16)
  k=t.ones((3,1,256),dtype=t.bfloat16);v=k*2
  cache=t.arange(12*128*256,dtype=t.float32).reshape(12,128,1,256).div(500000).to(t.bfloat16)
  owner=A.Owner('operand-fixture',1,0,length,0)
  trial=A.prepare(t,owner,q,k,v,cache,cache.clone()*3,tuple(range(12)))
  calls=[]
  def fake_fia(**kw):
   calls.append(kw);return t.zeros((1,6,3,256),dtype=t.float16),None
  boundary=ServiceFiaBoundary(t,NS(npu_fused_infer_attention_score=fake_fia),trial,C.ref(P/'service_fia.py'))
  schemas={'fixture':'explicit CPU test schema only'}
  class Proxy:
   ops=NS(npu=NS(npu_fused_infer_attention_score=NS(_schemas=schemas)))
   def __getattr__(self,key):return getattr(t,key)
  abi=dict(schema='bole.actual-FIA-installed-ABI/v115',NPU=False,operator_executed=False,schema_family=schemas,
   argument_names=['query','key','value','atten_mask','block_table','input_layout','block_size','actual_seq_lengths',
   'actual_seq_lengths_kv','num_key_value_heads','num_heads','scale','sparse_mode','pre_tokens','next_tokens','inner_precise'])
  with patch.dict(os.environ,BOLE_PAGED_TREE_ENABLE='1'):A.native(Proxy(),boundary,trial,abi,sparse_mode=1)
  anchor=dict(key=cache,value=cache.clone()*3,ownership=dict(CPU_table=list(range(12,24)),request_physical_blocks=[1],
   blocks_per_phys_block=12,physical_block_size=1536,kernel_block_size=128,use_hybrid_blocks=True))
  return dict(query=q.reshape(3,1536),key=k.reshape(3,256),value=v.reshape(3,256),trial=trial),anchor,calls
 def test_original_adapter_native_operands_join_all_extended_page_edges(self):
  for length in(254,382,1022,1153):
   row,anchor,calls=self.fixture(length)
   self.assertTrue(JOIN.consume(t,row,anchor,length));self.assertEqual(len(calls),1)
   self.assertEqual(calls[0]['key'].dtype,t.float16);self.assertTrue(row['trial']['fp16_boundary']['completed'])
 def test_actual_prefix_padding_or_sibling_mask_corruption_is_rejected(self):
  for wrong in('prefix','padding','sibling'):
   row,anchor,calls=self.fixture(1153);native=row['trial']['native_before']
   if wrong=='prefix':native['key'][0,0,0,0]+=1
   elif wrong=='padding':native['value'][-1,0,-1,0]=1
   else:native['atten_mask'][0,0,1,1155]=False
   with self.subTest(wrong=wrong),self.assertRaises(ValueError):JOIN.consume(t,row,anchor,1153)
 def test_rebound_allocation_or_old_two_page_capture_cannot_qualify_long_frame(self):
  for wrong in('allocation','old-page-shape'):
   row,anchor,calls=self.fixture(1153)
   if wrong=='allocation':anchor['ownership']['request_physical_blocks']=[1,2]
   else:row['trial']['native_before']['key']=row['trial']['native_before']['key'][:2]
   with self.subTest(wrong=wrong),self.assertRaises(ValueError):JOIN.consume(t,row,anchor,1153)
 def test_service_boundary_checks_geometry_before_any_delegate_call(self):
  trial=dict(owner=NS(length=1153));calls=[]
  boundary=ServiceFiaBoundary(t,NS(npu_fused_infer_attention_score=lambda **kw:calls.append(kw)),trial,C.ref(P/'service_fia.py'))
  with self.assertRaises(ValueError):boundary.npu_fused_infer_attention_score(query=t.zeros((1,6,3,256),dtype=t.bfloat16),
   key=t.zeros((2,1,128,256),dtype=t.bfloat16),value=t.zeros((2,1,128,256),dtype=t.bfloat16))
  self.assertEqual(calls,[])

if __name__=='__main__':unittest.main()
