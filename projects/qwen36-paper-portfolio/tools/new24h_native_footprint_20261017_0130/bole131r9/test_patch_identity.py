"""Execute actual installed assignment AST; explicit CPU fixture, no backend."""
import ast,functools,sys,types,unittest,__future__
from pathlib import Path
from unittest.mock import patch
import model_entry as M,sourceio as C
P=Path(__file__).resolve().parent
NAME='vllm_ascend.patch.worker.patch_qwen3_5'

def actual_assignment_fixture():
 path=P/'evidence/worker_patch/patch_qwen3_5.py'
 tree=ast.parse(path.read_text(encoding='utf8'))
 targets={n:type(n,(),{})for n in('Qwen3NextAttention','Qwen3_5DecoderLayer','Qwen3_5MultiTokenPredictor')}
 module=types.ModuleType(NAME);module.__file__=str(path)
 module.__dict__.update(targets,torch=types.SimpleNamespace(Tensor=object),IntermediateTensors=object)
 nodes=[]
 for n in tree.body:
  if isinstance(n,ast.ClassDef)and n.name in('AscendQwen3NextAttention','AscendQwen3_5DecoderLayer'):nodes.append(n)
  elif isinstance(n,ast.If)and ast.unparse(n.test)=='Qwen3_5MultiTokenPredictor is not None':nodes.append(n)
  elif isinstance(n,ast.Assign)and ast.unparse(n.targets[0])in('Qwen3NextAttention.forward','Qwen3_5DecoderLayer.forward'):nodes.append(n)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec',flags=__future__.annotations.compiler_flag),module.__dict__)
 return path,module,targets

class Tests(unittest.TestCase):
 def test_real_assignment_all_three_identities(self):
  path,module,targets=actual_assignment_fixture()
  with patch.dict(sys.modules,{NAME:module}):
   for role,name in [('fa','Qwen3NextAttention'),('decoder','Qwen3_5DecoderLayer'),('mtp','Qwen3_5MultiTokenPredictor')]:
    M.patched_source(C,targets[name]().forward,C.ref(path),role)
   # Actual discover function across all64 fixture objects, using original
   # installed model-forward body and actual patched decoder/FA assignments.
   import worker_entry as W
   next_path=P/'evidence/qwen3_next.py';tree=ast.parse(next_path.read_text(encoding='utf8'))
   cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Qwen3NextModel')
   body=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='forward')
   ns={};exec(compile(ast.Module(body=[body],type_ignores=[]),str(next_path),'exec',flags=__future__.annotations.compiler_flag),ns)
   model_module=types.ModuleType('vllm.model_executor.models.qwen3_5');model_module.__file__=str(P/'evidence/qwen3_5.py')
   inner_type=type('Qwen3_5Model',(),dict(__module__=model_module.__name__,forward=ns['forward']))
   inner=inner_type();inner.start_layer=0;inner.end_layer=64;inner.layers=[]
   for i in range(64):
    layer=targets['Qwen3_5DecoderLayer']();layer.layer_idx=i
    if i%4==3:
     layer.layer_type='full_attention';layer.self_attn=targets['Qwen3NextAttention']();layer.self_attn.attn=types.SimpleNamespace(layer_name='fa.%d'%i)
    else:layer.layer_type='linear_attention';layer.linear_attn=types.SimpleNamespace(prefix='gdn.%d'%i)
    inner.layers.append(layer)
   outer=types.SimpleNamespace(named_modules=lambda:[('model',inner)])
   with patch.dict(sys.modules,{model_module.__name__:model_module}):
    actual,receipt=W.discover(C,outer,C.ref(model_module.__file__),C.ref(next_path),C.ref(path))
    self.assertIs(actual,inner);self.assertEqual(receipt['counts'],dict(gdn=48,fa=16))
    with self.assertRaisesRegex(ValueError,'actual model callable source identity'):
     W.discover(C,outer,C.ref(model_module.__file__),C.ref(next_path))
 def test_unknown_wrapper_and_same_source_wrong_function_reject(self):
  path,module,targets=actual_assignment_fixture();native=targets['Qwen3NextAttention'].forward
  @functools.wraps(native)
  def wrapped(*args,**kwargs):return native(*args,**kwargs)
  with patch.dict(sys.modules,{NAME:module}):
   with self.assertRaisesRegex(ValueError,'actual model callable source identity'):M.patched_source(C,wrapped,C.ref(path),'fa')
   with self.assertRaisesRegex(ValueError,'exact installed patch function identity'):M.patched_source(C,targets['Qwen3_5DecoderLayer'].forward,C.ref(path),'fa')
 def test_foreign_target_replacement_and_bad_pin_reject(self):
  path,module,targets=actual_assignment_fixture();native=targets['Qwen3NextAttention'].forward
  with patch.dict(sys.modules,{NAME:module}):
   targets['Qwen3NextAttention'].forward=targets['Qwen3_5DecoderLayer'].forward
   with self.assertRaisesRegex(ValueError,'identity_target'):M.patched_source(C,native,C.ref(path),'fa')
   bad=dict(C.ref(path),sha256='0'*64)
   with self.assertRaisesRegex(ValueError,'expected'):M.patched_source(C,native,bad,'fa')
 def test_real_FA_body_post_fused_rope_then_native_attention(self):
  path,module,targets=actual_assignment_fixture();calls=[]
  class Tensor:
   device='cpu';dtype='fixture'
  q,k,v=Tensor(),Tensor(),Tensor()
  def fused(**kw):calls.append(('fused',kw));return q,k,v,None
  module.torch=types.SimpleNamespace(ops=types.SimpleNamespace(vllm=types.SimpleNamespace(triton_split_qkv_rmsnorm_mrope=fused)))
  class Cache:
   def __getitem__(self,positions):return Tensor()
  class Output:
   def __setitem__(self,key,value):calls.append(('output',value))
  obj=targets['Qwen3NextAttention']();obj.qkv_proj=lambda hidden:(Tensor(),None)
  obj.config=types.SimpleNamespace(model_type='qwen3_5_text',rms_norm_eps=1e-6)
  obj.rotary_emb=types.SimpleNamespace(cos_sin_cache=Cache(),mrope_section=[16,16,16],mrope_interleaved=True,rotary_dim=256)
  obj.q_norm=types.SimpleNamespace(weight=1.0);obj.k_norm=types.SimpleNamespace(weight=1.0)
  obj.num_heads=6;obj.num_kv_heads=1;obj.head_dim=256;obj.attn_output_gate=False
  def attention(a,b,c):
   self.assertIs(a,q);self.assertIs(b,k);self.assertIs(c,v);calls.append(('attn',));return 'attended'
  obj.attn=attention;obj.o_proj=lambda x:('projected',None)
  obj.forward([131,132,132],Output(),Tensor())
  self.assertEqual([x[0]for x in calls],['fused','attn','output'])

if __name__=='__main__':unittest.main()
