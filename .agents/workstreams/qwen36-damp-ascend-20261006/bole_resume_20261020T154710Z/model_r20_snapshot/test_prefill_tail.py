import unittest
from types import SimpleNamespace as NS
import torch
import prefill_tail as P
from model_entry import tensor_id


class Meta: pass
GDNAttentionMetadata=Meta

class NativeFixture:
 def _forward_core(self,mixed_qkv,b,a,core_attn_out):
  self.kv_cache[0][1,:3].copy_(mixed_qkv[-3:])
  if getattr(self,'corrupt_extra',False):self.kv_cache[0][1,4,0]=0


CURRENT=None
def context():return CURRENT

class C:
 @staticmethod
 def ref(p):return __import__('pathlib').Path(p).resolve().as_posix()


class Tests(unittest.TestCase):
 def fixture(self):
  # Exact source-derived shape: width3 +8 speculative entries. Sentinel extras
  # must survive both private convolution preparation and staging unchanged.
  arena=torch.arange(2*11*2560,dtype=torch.float32).reshape(2,11,2560).to(torch.bfloat16)
  obj=NS(kv_cache=[arena,None],conv1d=NS(weight=torch.zeros(2560,1,4),bias=None))
  m=Meta();m.num_prefills=1;m.num_decodes=0;m.num_spec_decodes=0;m.spec_sequence_masks=None;m.num_actual_tokens=127
  m.prefill_query_start_loc=torch.tensor([0,127]);m.prefill_state_indices=torch.tensor([1]);m.non_spec_state_indices_tensor=torch.tensor([1])
  m.non_spec_prefill_metadata=NS(causal_conv1d=NS(query_start_loc=torch.tensor([0,127]),cache_indices=torch.tensor([1])))
  req=object();kw=dict(original_gdn_module=NS(GDNAttentionMetadata=Meta),request=req,request_id='actual',slot=1,length=127,native_prefill_returned=True)
  obj._bole_pure_prefill_observation=dict(metadata=m,request=req,request_id='actual',slot=1,length=127,actual_native_forward_returned=True,arena_identity=tensor_id(arena),raw_last3=arena[1,:3].clone(),extra_before=arena[1,3:].clone())
  return obj,m,kw
 def test_wide_leading_view_and_all_extra_bytes_immutable(self):
  obj,m,k=self.fixture();before=obj.kv_cache[0].clone();tail=P.bind(torch,obj,m,**k)
  self.assertEqual(tuple(tail.view.shape),(2,3,2560))
  self.assertEqual(tail.view.stride(0),11*2560)
  private=tail.view[1:2].clone();private.zero_()
  P.unchanged(torch,tail,obj=obj,request=k['request'],request_id='actual',slot=1,length=127)
  self.assertTrue(torch.equal(obj.kv_cache[0].view(torch.int16),before.view(torch.int16)))
  obj.kv_cache[0][1,10,0]=1
  with self.assertRaises(ValueError):P.unchanged(torch,tail,obj=obj,request=k['request'],request_id='actual',slot=1,length=127)
 def test_no_spec_or_partial_or_wrongslot_window(self):
  for field,value in [('num_spec_decodes',1),('num_decodes',1),('num_prefills',2),('spec_sequence_masks',torch.tensor([False]))]:
   obj,m,k=self.fixture();setattr(m,field,value)
   with self.assertRaises(ValueError):P.bind(torch,obj,m,**k)
  obj,m,k=self.fixture();m.non_spec_prefill_metadata.causal_conv1d.cache_indices=torch.tensor([0])
  with self.assertRaises(ValueError):P.bind(torch,obj,m,**k)
 def test_wrong_request_and_before_native_rejected(self):
  obj,m,k=self.fixture();k['native_prefill_returned']=False
  with self.assertRaises(ValueError):P.bind(torch,obj,m,**k)
  k['native_prefill_returned']=True;tail=P.bind(torch,obj,m,**k)
  with self.assertRaises(ValueError):P.unchanged(torch,tail,obj=obj,request=object(),request_id='actual',slot=1,length=127)
 def test_actual_builder_2d_conv_block_table_first_column(self):
  obj,m,k=self.fixture();m.non_spec_prefill_metadata.causal_conv1d.cache_indices=torch.tensor([[1,0,0]])
  P.bind(torch,obj,m,**k)
  m.non_spec_prefill_metadata.causal_conv1d.cache_indices=torch.tensor([[0,1,0]])
  with self.assertRaises(ValueError):P.bind(torch,obj,m,**k)
 def test_complete_48_original_core_capture_before_bind_and_extra_corruption(self):
  global CURRENT
  mapping={};layers=[];request=object()
  for i in range(48):
   obj,m,k=self.fixture()
   native=NativeFixture();native.kv_cache=obj.kv_cache;native.conv1d=obj.conv1d;native.prefix='g'+str(i)
   m.prefill_has_initial_state=torch.tensor([False]);mapping[native.prefix]=m
   layers.append(NS(layer_type='linear_attention',linear_attn=native))
  runner=NS(input_batch=NS(req_ids=['actual'],req_id_to_index={'actual':0}),requests={'actual':request})
  worker=NS(model_runner=runner,_bole_model_objects={'inner':NS(layers=layers)})
  CURRENT=NS(attn_metadata=mapping);ref=C.ref(__file__)
  restore=P.install_capture(worker,torch,C,get_forward_context=context,gdn_ref=ref,context_ref=ref)
  x=torch.ones(127,2560,dtype=torch.bfloat16)
  for layer in layers:layer.linear_attn._forward_core(mixed_qkv=x,b=None,a=None,core_attn_out=None)
  obj=layers[0].linear_attn
  tail=P.bind(torch,obj,mapping[obj.prefix],original_gdn_module=NS(GDNAttentionMetadata=Meta),request=request,request_id='actual',slot=1,length=127,native_prefill_returned=True)
  P.unchanged(torch,tail,obj=obj,request=request,request_id='actual',slot=1,length=127)
  obj.corrupt_extra=True
  with self.assertRaises(ValueError):obj._forward_core(mixed_qkv=x,b=None,a=None,core_attn_out=None)
  restore();CURRENT=None


if __name__=='__main__':unittest.main()
