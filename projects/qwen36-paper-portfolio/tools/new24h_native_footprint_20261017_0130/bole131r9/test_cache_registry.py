import ast,inspect,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import torch
import cache_registry as R
import prefill_tail as P
from model_entry import tensor_id

class Meta:pass
GDNAttentionMetadata=Meta
class Runner:pass
class Block:
 def get_cpu_tensor(self):return self.table
class Gdn:
 def _forward_core(self,mixed_qkv,b,a,core_attn_out):pass
class Backend:
 def forward(self,*args,**kw):pass
class FA:pass
class C:
 @staticmethod
 def ref(p):return Path(p).resolve().as_posix()
CURRENT=None
def get_forward_context():return CURRENT


def actual_attention_functions():
 path=Path(__file__).parent/'evidence/attention.py'
 tree=ast.parse(path.read_bytes().decode('utf8'))
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Attention')
 funcs=[next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='get_attention_context'),
        next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='forward')]
 unit=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*funcs],type_ignores=[])
 ns={'get_forward_context':get_forward_context,'torch':torch};exec(compile(ast.fix_missing_locations(unit),str(path),'exec'),ns)
 return ns['get_attention_context'],ns['forward'],path


class Tests(unittest.TestCase):
 def fixture(self):
  global CURRENT
  get_context,forward,path=actual_attention_functions();FA.forward=forward
  ref=C.ref(__file__);runner=Runner();request=object();meta={};static={};layers=[]
  for i in range(64):
   kind='full_attention'if i%4==3 else'linear_attention';prefix='layer'+str(i)
   if kind=='linear_attention':
    conv=torch.zeros(2,11,2560,dtype=torch.bfloat16);state=torch.zeros(2,12,128,128)
    obj=Gdn();obj.prefix=prefix;obj.kv_cache=[conv,state];obj.conv1d=NS(weight=torch.zeros(2560,1,4),bias=None)
    m=Meta();m.num_prefills=1;m.num_decodes=0;m.num_spec_decodes=0;m.spec_sequence_masks=None;m.num_actual_tokens=131
    m.prefill_query_start_loc=torch.tensor([0,131]);m.prefill_state_indices=torch.tensor([1]);m.non_spec_state_indices_tensor=torch.tensor([1]);m.non_spec_prefill_metadata=NS(causal_conv1d=NS(query_start_loc=torch.tensor([0,131]),cache_indices=torch.tensor([1])))
    obj._bole_pure_prefill_observation=dict(metadata=m,request=request,request_id='r',slot=1,length=131,actual_native_forward_returned=True,arena_identity=tensor_id(conv),raw_last3=conv[1,:3].clone(),extra_before=conv[1,3:].clone())
    layer=NS(layer_type=kind,layer_idx=i,linear_attn=obj)
   else:
    obj=FA();obj.layer_name=prefix;obj.kv_cache=[torch.zeros(3,128,1,256,dtype=torch.bfloat16),torch.zeros(3,128,1,256,dtype=torch.bfloat16)];obj.impl=Backend();obj.impl.key_cache,obj.impl.value_cache=obj.kv_cache
    obj.kv_sharing_target_layer_name=None;obj.query_quant=None;obj.calculate_kv_scales=False
    m=NS(num_prefills=1,num_decodes=0,num_actual_tokens=131,seq_lens_list=[131],actual_seq_lengths_q=[131],block_tables=torch.tensor([[2,0]]),slot_mapping=torch.tensor([2*128+p if p<128 else p-128 for p in range(131)]))
    layer=NS(layer_type=kind,layer_idx=i,self_attn=NS(attn=obj))
   meta[prefix]=m;static[prefix]=obj;layers.append(layer)
  g=Block();g.table=torch.tensor([[1]]);g.num_blocks_per_row=[1]
  f=Block();f.table=torch.tensor([[2,0]]);f.num_blocks_per_row=[2]
  runner.input_batch=NS(req_ids=['r'],req_id_to_index={'r':0},block_table=[g,f]);runner.requests={'r':request}
  runner.vllm_config=NS(compilation_config=NS(static_forward_context=static))
  runner.kv_cache_config=NS(kv_cache_groups=[NS(layer_names=[l.linear_attn.prefix for l in layers if l.layer_type=='linear_attention']),NS(layer_names=[l.self_attn.attn.layer_name for l in layers if l.layer_type=='full_attention'])])
  CURRENT=NS(attn_metadata=meta,no_compile_layers=static,slot_mapping={k:v.slot_mapping for k,v in meta.items()if hasattr(v,'slot_mapping')},dp_metadata=None,ubatch_slices=None,cudagraph_runtime_mode='NONE')
  worker=NS(model_runner=runner);inner=NS(layers=layers)
  kw=dict(request_id='r',request=request,metadata=meta,forward_context=CURRENT,get_attention_context=get_context,refs=dict(runner=ref,attention=C.ref(path),ascend_attention=ref,block_table=ref),length=131)
  return worker,inner,kw
 def test_actual_get_context_and_all64_registration(self):
  w,m,k=self.fixture();rows,window=R.register(torch,C,w,m,**k)
  self.assertEqual(len(rows),64);self.assertEqual(window['slot'],1)
  self.assertEqual(rows[3]['table'],(2,0));self.assertIs(rows[0]['conv_arena'],m.layers[0].linear_attn.kv_cache[0])
 def test_unallocated_or_bad_native_slot_mapping_rejected(self):
  for bad in ('unallocated','mapping','owner'):
   w,m,k=self.fixture()
   if bad=='unallocated':w.model_runner.input_batch.block_table[1].num_blocks_per_row=[1]
   elif bad=='mapping':k['metadata']['layer3'].slot_mapping[130]=1
   else:w.model_runner.requests['r']=object()
   with self.assertRaises(ValueError):R.register(torch,C,w,m,**k)


if __name__=='__main__':unittest.main()
