"""CPU fixtures use actual mirror/reader/finish/wiring functions, no NPU claim."""
import ast,types,unittest
from pathlib import Path
import torch
from qwen36_deltalog_service import builder_mirror as M,integration as W
torch.set_num_threads(1)
NS=types.SimpleNamespace
class Layer:
 def __init__(self,p,b):self.prefix=p;self.kv_cache=(None,b)
class Arena:
 """CPU storage facade for source-contract fixtures ONLY; not hardware proof."""
 def __init__(self,t):self.t=t;self.device=NS(type='npu');self.dtype=t.dtype;self.shape=t.shape
 def stride(self):return self.t.stride()
 def is_contiguous(self):return self.t.is_contiguous()
 def data_ptr(self):return self.t.data_ptr()
 def storage_offset(self):return self.t.storage_offset()
 def untyped_storage(self):return self.t.untyped_storage()
 def numel(self):return self.t.numel()
 def element_size(self):return self.t.element_size()
class Tables:
 def __init__(self):self.block_tables=[NS(is_mamba_group=True)]
 def __getitem__(self,i):return self.block_tables[i]
def fixture():
 storage=torch.empty(48,8,12,128,128)
 layers=[Layer('fixture-%d'%i,Arena(storage[i]))for i in range(48)]
 r=NS(use_async_scheduling=False,use_async_spec_decode=False,speculative_config=None,model_config=NS(enforce_eager=True),pcp_size=1,use_cp=False,cache_config=NS(mamba_cache_mode='none',enable_prefix_caching=False),input_batch=NS(block_table=Tables()),kv_cache_config=NS(kv_cache_groups=[NS(layer_names=[l.prefix for l in layers])]),compilation_config=NS(static_forward_context={l.prefix:l for l in layers}))
 return r,layers
def attach(r,layers,nd):
 idx=torch.tensor([4,2],dtype=torch.int32);seq=None if nd==0 else torch.tensor([0,1],dtype=torch.int32)
 meta=NS(non_spec_state_indices_tensor=idx,non_spec_decode_metadata=None if seq is None else NS(actual_seq_lengths=seq),num_decodes=nd)
 cpu=M.check_cpu([]if nd==0 else[4],[4,2]if nd==0 else[2],[0]if nd==0 else[0,1],[False,False]if nd==0 else[False],8)
 state=r._deltalog018_state;state['epoch']+=1;step={'metadata':{0:meta},'epoch':state['epoch']};state['current']=step
 meta._deltalog018_cpu_receipt=dict(cpu=cpu,metadata=meta,state=state,step=step,epoch=state['epoch'],group=0,index_identity=M.tensor_identity(idx),seen=set())
 ctx=NS(attn_metadata={l.prefix:meta for l in layers},no_compile_layers={l.prefix:l for l in layers})
 return meta,idx[:nd],seq,ctx
class Tests(unittest.TestCase):
 def test_actual_config_rows_register_all48_not_invented(self):
  r,layers=fixture();rows=W.rows_from_native(r,Layer);receipt=M.register_layers(r,rows,Layer)
  self.assertEqual(len(receipt['registered_prefixes']),48)
  self.assertTrue(all(r._deltalog018_state['layers'][l.prefix]['layer']is l for l in layers))
  with self.assertRaises(ValueError):M.register_layers(r,rows,Layer)
 def test_overlap_and_wrong_mapping_rejected(self):
  r,ls=fixture();ls[1].kv_cache=ls[0].kv_cache
  with self.assertRaises(ValueError):M.register_layers(r,W.rows_from_native(r,Layer),Layer)
  r,ls=fixture();r.compilation_config.static_forward_context[ls[0].prefix]=NS(prefix=ls[0].prefix)
  with self.assertRaises(ValueError):W.rows_from_native(r,Layer)
 def test_pure_prefill_then_decode_and_mixed_full48_finish(self):
  r,ls=fixture();M.register_layers(r,W.rows_from_native(r,Layer),Layer)
  for nd in(0,1):
   meta,ids,seq,ctx=attach(r,ls,nd)
   for l in ls:
    M.read_receipt(r,l,meta,l.kv_cache[1],ids,seq,ctx,'core')
    if nd:M.read_receipt(r,l,meta,l.kv_cache[1],ids,seq,ctx,'decode')
   self.assertTrue(M.finish_step(r))
 def test_prefill_not_skipped_and_decode_none_rejected(self):
  r,ls=fixture();M.register_layers(r,W.rows_from_native(r,Layer),Layer);meta,ids,seq,ctx=attach(r,ls,0)
  with self.assertRaises(ValueError):M.finish_step(r)
  with self.assertRaises(ValueError):M.read_receipt(r,ls[0],meta,ls[0].kv_cache[1],ids,seq,ctx,'decode')
  meta,ids,seq,ctx=attach(r,ls,1)
  with self.assertRaises(ValueError):M.read_receipt(r,ls[0],meta,ls[0].kv_cache[1],ids,None,ctx,'core')
 def test_final_forward_wrapper_does_not_wait_next_prepare(self):
  r,ls=fixture();M.register_layers(r,W.rows_from_native(r,Layer),Layer);meta,ids,seq,ctx=attach(r,ls,0)
  class R:
   def _prepare_inputs(self,*a,**kw):return None
   def _model_forward(self):
    for l in ls:M.read_receipt(self,l,meta,l.kv_cache[1],ids,seq,ctx,'core')
    return 'real-body-fixture-result'
  W.install(R,Layer,lambda *a,**kw:None)
  result=R._model_forward(r);self.assertEqual(result,'real-body-fixture-result');self.assertTrue(r._deltalog018_state['current']['forward_complete'])
  with self.assertRaises(ValueError):R._model_forward(r)
 def test_runtime_no_device_to_host_metadata_calls_and_fixed_kernel(self):
  p=Path(__file__).parent/'qwen36_deltalog_service/runtime.py';t=ast.parse(p.read_bytes())
  self.assertFalse(any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr in('cpu','tolist')for x in ast.walk(t)))
  source=p.read_text();self.assertIn("aux['length'],actual_seq_lengths.contiguous(),ids.contiguous()",source)

if __name__=='__main__':unittest.main()
