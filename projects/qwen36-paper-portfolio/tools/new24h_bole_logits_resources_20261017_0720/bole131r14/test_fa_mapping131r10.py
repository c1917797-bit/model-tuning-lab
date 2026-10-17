"""Exact native context and hybrid page mapping, CPU metadata fixtures only."""
import ast,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import torch
import fa_prefill131r10 as F
import test_cache_registry as K

class Tests(unittest.TestCase):
 def test_actual_context_none_and_all64_registry_complete(self):
  fixture=K.Tests();w,inner,kw=fixture.fixture();meta,_,_,generic=kw['get_attention_context']('layer3')
  self.assertIsNone(generic);self.assertEqual(kw['forward_context'].slot_mapping,{})
  rows,window=K.R.register(torch,K.C,w,inner,**kw);self.assertEqual(len(rows),64)
 def hybrid(self):
  b=K.Block();b.table=torch.arange(12,24,dtype=torch.int32).reshape(1,12);b.num_blocks_per_row=[12];b.pcp_world_size=b.dcp_world_size=1
  b.blocks_per_phys_block=12;b.logical_block_size=b.block_size=128;b.physical_block_size=1536;b.use_hybrid_blocks=True
  b.slot_mapping=NS(gpu=torch.arange(1536,1667,dtype=torch.int32));m=NS(block_tables=b.table,slot_mapping=b.slot_mapping.gpu)
  return b,m,NS(slot_mapping={})
 def test_actual_observed_physical1_expands12through23_not_stale_request(self):
  b,m,c=self.hybrid();out=F.mapping(torch,b,m,c,'p',None,list(range(12,24)),12,131,[1]);self.assertEqual(out,list(range(1536,1667)))
  b.table=torch.tensor([[12,20,13,14,15,16,17,18,19,21,22,23]],dtype=torch.int32);m.block_tables=b.table
  with self.assertRaises(ValueError):F.mapping(torch,b,m,c,'p',None,b.table[0].tolist(),12,131,[1])
 def test_nonempty_generic_unknown_view_or_wrong_actual_value_refuses(self):
  for bad in('generic','clone','value','GPUtable','physical'):
   b,m,c=self.hybrid();physical=list(range(12,24));request=[1]
   if bad=='generic':c.slot_mapping={'p':m.slot_mapping}
   elif bad=='clone':m.slot_mapping=m.slot_mapping.clone()
   elif bad=='value':m.slot_mapping[130]+=1
   elif bad=='GPUtable':m.block_tables=m.block_tables.clone()
   else:request=[2]
   with self.assertRaises(ValueError):F.mapping(torch,b,m,c,'p',None,physical,12,131,request)
 def test_actual_source_context_omits_generic_and_backend_uses_meta(self):
  p=Path(__file__).parent/'evidence';asc=ast.parse((p/'ascend_forward_context.py').read_bytes());fn=next(n for n in asc.body if isinstance(n,ast.FunctionDef)and n.name=='set_ascend_forward_context')
  self.assertNotIn('slot_mapping',[x.arg for x in fn.args.args])
  assignments=[n for n in ast.walk(fn)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='forward_context_kwargs'for t in n.targets)]
  self.assertEqual(len(assignments),1);self.assertNotIn('slot_mapping',[x.value for x in assignments[0].value.keys])
  backend=ast.parse((p/'ascend_attention.py').read_bytes());cls=next(n for n in backend.body if isinstance(n,ast.ClassDef)and n.name=='AscendAttentionBackendImpl');reshape=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='reshape_and_cache')
  self.assertIn('slots = attn_metadata.slot_mapping',ast.unparse(reshape));self.assertIn('slot_mapping=slots[:attn_metadata.num_actual_tokens]',ast.unparse(reshape).replace(' ',''))

class CaptureTests(unittest.TestCase):
 def test_real_capture_serializes_all64_before_registration(self):
  import tempfile,os,json
  from unittest.mock import patch
  from pathlib import Path
  import sourceio as C
  import fa_prefill131r10 as A
  import test_cache_registry as F
  w,m,k=F.Tests().fixture()
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);source=dict(files={'fa_prefill131r10.py':C.ref(A.__file__)},runtime_sources={n:C.ref(__file__)for n in('runner','block_table','attention','ascend_attention','forward_context','ascend_forward_context')},model_receipt_root=str(root))
   sr=C.write(root/'SOURCE.json',source)
   # Windows cannot fsync a directory; model the OS call only. Linux actual
   # guest still executes the original fsync and must not skip it.
   real_open=A.os.open
   def op(path,flags,*args,**kw):return real_open(root/'SOURCE.json',os.O_RDWR)if Path(path)==root and os.name=='nt'else real_open(path,flags,*args,**kw)
   with patch.dict(os.environ,BOLE_MODEL_RAW_ROOT=str(root)),patch.object(A.os,'open',side_effect=op):
    receipt=A.capture(C,sr,w,m,request_id='r',request=k['request'],metadata=k['metadata'],context=k['forward_context'],rank=0,length=131)
   raw=C.obj(receipt);self.assertEqual(len(raw['rows']),16);self.assertEqual(len(raw['GDN_selected_operands']),48);self.assertFalse(raw['numerical_qualified'])

if __name__=='__main__':unittest.main()
