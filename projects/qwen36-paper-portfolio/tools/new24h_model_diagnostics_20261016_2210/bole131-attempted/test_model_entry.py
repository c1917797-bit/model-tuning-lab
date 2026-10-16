"""CPU actual-source AST callsite controls, not actual model/NPU evidence."""
import ast,hashlib,types,unittest
from pathlib import Path
import torch as t
import model_entry as B
P=Path(__file__).resolve().parent

class Tests(unittest.TestCase):
 def test_real_qwen_forward_post_RoPE_and_outer_gating_preserved(self):
  p=P/'evidence/qwen3_next.py';source=p.read_bytes().decode('utf8');tree=ast.parse(source)
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Qwen3NextAttention')
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='forward')
  # Execute the COMPLETE actual forward body, preserving the real call order.
  ns={'torch':t};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns)
  q=t.arange(3*6*256,dtype=t.float32).reshape(3,-1)
  k=t.arange(3*256,dtype=t.float32).reshape(3,-1);v=k+19
  seen=[]
  def rotary(positions,a,b):
   seen.append(('rope',positions.tolist()));return a+1000,b+2000
  class Attention:
   def __call__(self,a,b,c):
    seen.append(('attn',));t.testing.assert_close(a,q+1000);t.testing.assert_close(b,k+2000);t.testing.assert_close(c,v);return a
  obj=types.SimpleNamespace(attn_output_gate=False,q_size=1536,kv_size=256,num_heads=6,num_kv_heads=1,head_dim=256,
   qkv_proj=lambda hidden:(t.cat((q,k,v),dim=-1),None),q_norm=lambda x:x,k_norm=lambda x:x,
   rotary_emb=rotary,attn=Attention(),o_proj=lambda x:(x+3000,None))
  output=t.empty_like(q);positions=t.tensor([127,128,128])
  ns['forward'](obj,positions,output,t.zeros((3,5120)))
  self.assertEqual(seen,[('rope',[127,128,128]),('attn',)])
  t.testing.assert_close(output,q+4000)
 def test_actual_source_contains_real_hook_seam_not_preRoPE(self):
  source=(P/'evidence/qwen3_next.py').read_bytes().decode('utf8');tree=ast.parse(source)
  cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Qwen3NextAttention')
  fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='forward')
  calls=[(n.lineno,ast.unparse(n.func))for n in ast.walk(fn)if isinstance(n,ast.Call)]
  self.assertLess(next(l for l,n in calls if n=='self.rotary_emb'),next(l for l,n in calls if n=='self.attn'))
  self.assertLess(next(l for l,n in calls if n=='self.attn'),next(l for l,n in calls if n=='self.o_proj'))
 def test_context_all64_order_repeat_fail(self):
  c=B.Context(B.Owner('r',9,1,127,0),(2,3,5),(127,128,128),'TREE');c.phase='FORWARD'
  for i in range(64):c.visit(i,'fa'if i%4==3 else'gdn');c.captures[i]={}
  self.assertEqual(len(c.order),64)
  with self.assertRaises(ValueError):c.visit(63,'fa')
  with self.assertRaises(ValueError):B.Context(c.owner,c.tokens,c.positions,'TREE').visit(0,'gdn')
 def test_default_OFF_does_not_touch_model(self):
  import os
  from unittest.mock import patch
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaisesRegex(ValueError,'default OFF'):
    B.Bridge(None,None,None,None,qwen_next_ref=None,gdn_ref=None,actual118c=None,conv_seam=None,treeconv=None,tree_metadata=None,core112=None,paged=None,torch_npu=None,actual_fia_abi=None,actual_conv_abi=None,calibration_reader=None)
 def test_actual_worker_load_body_returns_before_discovery(self):
  from contextlib import nullcontext
  from unittest.mock import patch
  import worker_entry as W,os
  p=P/'evidence/worker.py';tree=ast.parse(p.read_bytes().decode('utf8'))
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='NPUWorker')
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='load_model')
  ns={'set_current_vllm_config':lambda cfg:nullcontext()};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns)
  events=[]
  class Worker:load_model=ns['load_model']
  worker=Worker();worker.vllm_config=types.SimpleNamespace(model_config=types.SimpleNamespace(enable_sleep_mode=False),weight_transfer_config=None)
  outer=object();worker.model_runner=types.SimpleNamespace(load_model=lambda:events.append('real-load-body'),get_model=lambda:outer)
  class Check:
   def ref(self,path):return {'path':str(path)}
  expected={'path':str(p)}
  def discovered(C,actual,*_):
   self.assertIs(actual,outer);self.assertEqual(events,['real-load-body']);events.append('discover');return object(),dict(model_ready=False)
  with patch.dict(os.environ,BOLE_MODEL_OBJECT_AUDIT_ENABLE='1'),patch.object(W,'discover',discovered):
   restore=W.install_after_load(Worker,Check(),worker_ref=expected,qwen35_ref=None,qwen_next_ref=None,emit=lambda *x:events.append('emit'))
   worker.load_model();restore()
  self.assertEqual(events,['real-load-body','discover','emit']);self.assertTrue(hasattr(worker,'_bole_model_objects'))
 def test_worker_audit_OFF_never_imports_backend(self):
  import os,worker_entry as W
  from unittest.mock import patch
  with patch.dict(os.environ,{},clear=True):self.assertIsNone(W.install_after_load(None,None,worker_ref=None,qwen35_ref=None,qwen_next_ref=None,emit=None))
 def test_real_install_all64_keyword_routes_and_restore(self):
  # Explicit CPU wiring fixture; no validation or numerical qualification claim.
  class GDN:
   def _forward_core(self,mixed_qkv,b,a,core_attn_out):return 'native'
  class FA:
   def forward(self,query,key,value):return 'native-fa'
  bridge=B.Bridge.__new__(B.Bridge);bridge.saved=[];bindings=[];seen=[]
  for i in range(64):
   if i%4==3:bindings.append(dict(index=i,kind='fa',layer=types.SimpleNamespace(self_attn=types.SimpleNamespace(attn=FA()))))
   else:bindings.append(dict(index=i,kind='gdn',layer=types.SimpleNamespace(linear_attn=GDN())))
  bridge.bindings=bindings
  bridge._gdn=lambda binding,obj,*args:seen.append(binding['index'])
  bridge._fa=lambda binding,*args:seen.append(binding['index'])
  bridge.install();token=B.BUS.set(object())
  try:
   for row in bindings:
    if row['kind']=='gdn':row['layer'].linear_attn._forward_core(mixed_qkv=1,b=2,a=3,core_attn_out=4)
    else:row['layer'].self_attn.attn.forward(1,2,3)
  finally:B.BUS.reset(token)
  self.assertEqual(seen,list(range(64)));bridge.restore()
  self.assertEqual(bindings[0]['layer'].linear_attn._forward_core(1,2,3,4),'native')
  self.assertNotIn('_forward_core',bindings[0]['layer'].linear_attn.__dict__)
 def test_ON_missing_real_predecessors_reject_before_backend(self):
  import os
  from unittest.mock import patch
  with patch.dict(os.environ,BOLE_THREE_NODE_MODEL_ENABLE='1',BOLE_PAGED_TREE_ENABLE='1'):
   with self.assertRaisesRegex(ValueError,'actual component chains'):
    B.Bridge(None,None,None,None,qwen_next_ref=None,gdn_ref=None,actual118c=None,conv_seam=None,treeconv=None,tree_metadata=None,core112=None,paged=None,torch_npu=None,actual_fia_abi=None,actual_conv_abi=None,calibration_reader=None,arm_verified=True)
 def test_actual_prefill_context_callback_once_dummy_and_recursion(self):
  import worker_entry as W,os
  from unittest.mock import patch
  result=object();events=[]
  class Inner:
   def forward(self,input_ids,positions,intermediate_tensors=None,inputs_embeds=None):events.append('native');return result
  inner=Inner();request=object();worker=types.SimpleNamespace(_bole_model_objects={'inner':inner},model_runner=types.SimpleNamespace(input_batch=types.SimpleNamespace(req_ids=['r'],req_id_to_index={'r':0}),requests={'r':request}))
  ctx=types.SimpleNamespace(attn_metadata=None)
  def get_context():return ctx
  def callback(**kw):
   self.assertIs(kw['request'],request);self.assertIs(kw['hidden'],result);self.assertIs(kw['forward_context'],ctx)
   events.append('callback');self.assertIs(inner.forward(kw['input_ids'],kw['positions']),result)
  class Check:
   def ref(self,p):return {'path':str(p)}
  expected={'path':str(P/'test_model_entry.py')}
  with patch.dict(os.environ,BOLE_MODEL_OBJECT_AUDIT_ENABLE='1'):
   restore=W.install_after_native_prefill(worker,Check(),qwen_next_ref=expected,get_forward_context=get_context,context_source_ref=expected,callback=callback,callback_source_ref=expected)
   self.assertIs(inner.forward(t.tensor([1,2]),t.tensor([0,1])),result)
   self.assertEqual(events,['native'])
   ctx.attn_metadata={'gdn':types.SimpleNamespace(num_prefills=1)}
   inner.forward(t.tensor([1,2]),t.tensor([0,1]));inner.forward(t.tensor([1,2]),t.tensor([0,1]))
   restore()
  self.assertEqual(events,['native','native','callback','native','native'])
  self.assertNotIn('forward',inner.__dict__)
 def test_bounded_export_excludes_pool_and_opaque_runtime(self):
  import diagnostic_export as E
  pool=t.zeros(100000);small=t.ones(2)
  proposal=dict(schema='bole.actual-model-selected-path-staging/v1',published=False,writes=[dict(layer=0,kind='state',arena=pool,arena_identity=('actual',),before=small,after=small+1)])
  raw=E.export_staged(t,proposal,cap_bytes=64)
  self.assertNotIn('arena',raw['payload']['writes'][0]);self.assertEqual(raw['logical_tensor_bytes'],16)
  with self.assertRaises(ValueError):E.export(t,{'model':object()},cap_bytes=64)
  with self.assertRaises(ValueError):E.export(t,pool,cap_bytes=64)

if __name__=='__main__':unittest.main()
