"""Software callback-entry discrimination. Fakes are never real NPU qualification."""
import ast,copy,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import render_native_input as R
class StopBeforeBridge(Exception):pass
class Tensor:
 def __init__(self,shape,dtype='i32',values=None,device='npu'):
  self.shape=shape;self.dtype=dtype;self.ndim=len(shape);self.device=types.SimpleNamespace(type=device)
  self.values=values
 def cpu(self):return self
 def tolist(self):return self.values
 def detach(self):return self
 def clone(self):return self
class Controls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original,cls.geometry,cls.snapshot,cls.G,cls.S=R.actual_chain()
  cls.bundle=R.adapt(cls.snapshot['files'])
 def test_complete_actual_inverse_and_narrow_math_scope(self):
  own=R.inverse(self.bundle);self.assertEqual(own,self.snapshot['files'])
  original=self.G['inverse'](dict(self.geometry,files=self.S['inverse'](dict(self.snapshot,files=own))))
  self.assertEqual(original,self.original);self.assertEqual(set(self.bundle['inverse_delta']),{'service_runner.py'})
  a=ast.parse(own['service_runner.py']);b=ast.parse(self.bundle['files']['service_runner.py'])
  for name in('_snap','_native_samples','_native_method'):
   x=next(n for n in a.body if isinstance(n,ast.FunctionDef)and n.name==name)
   y=next(n for n in b.body if isinstance(n,ast.FunctionDef)and n.name==name)
   self.assertEqual(ast.dump(x,include_attributes=False),ast.dump(y,include_attributes=False))
  for name in('core112.py','adapter.py','oracle112.py','independent_model.py','g2_numeric.py','transaction.py','tp_consensus.py'):
   self.assertEqual(self.bundle['files'][name],self.original[name])
 def test_order_repeat_and_wrong_geometry_seam_refuse(self):
  with self.assertRaises(ValueError):R.adapt(self.original)
  with self.assertRaises(ValueError):R.adapt(self.geometry['files'])
  with self.assertRaises(ValueError):R.adapt(self.bundle['files'])
 def fixture(self,mutate=None,fast=False):
  source=ast.parse(self.bundle['files']['service_runner.py'])
  install=next(x for x in source.body if isinstance(x,ast.FunctionDef)and x.name=='install')
  callback=copy.deepcopy(next(x for x in install.body if isinstance(x,ast.FunctionDef)and x.name=='after_prefill'))
  unit=ast.fix_missing_locations(ast.Module(body=[callback],type_ignores=[]))
  refs={k:k+'-source'for k in('runner','base_runner','qwen35','qwen_next','attention')}
  files={n:n+'-ref'for n in('fa_native_geometry.py','cache_observation.py','fa_prefill131r10.py')}
  state=types.SimpleNamespace(completed=False,prefill=None,generation=1,completed_requests=[],strong_requests=[])
  ids=Tensor((2048,),values=list(range(2048)));positions=Tensor((2048,),'i64',list(range(2048)))
  request=types.SimpleNamespace(prompt_token_ids=list(range(2048)))
  ni=dict(actual_token_ids=ids,request_id='request',sources={k:refs[k]for k in('runner','base_runner','qwen35','qwen_next')},
   no_mm_features=True,no_soft_prompt=True,actual_input_mode='native-token-ids',
   actual_CPU_token_ids=list(range(2048)),request_prompt_token_ids=list(range(2048)))
  kw=dict(input_ids=ids,positions=positions,request=request,request_id='request',native_input=ni,
   hidden=Tensor((2048,5120),'bf16'),metadata=object(),forward_context=object())
  m=dict(performance_profile=dict(scope=dict(input_tokens=2048,output_tokens=1024)),files=files,actual118c={'capture':'before-bridge'})
  events=[];geometry=object();worker=object();inner=object();ctx=object()
  def bind(*a,**k):
   self.assertIs(k['input_ids'],ids);self.assertIs(k['request'],request);events.append(('bind',k));return geometry
  def reg(*a,**k):
   self.assertEqual(k['length'],2048);self.assertIs(k['native_geometry'],geometry)
   events.append(('register',k));return [],dict(request_id='request',slot=0)
  def capture(*a,**k):
   if 'length'in k:self.assertEqual(k['length'],2048)
   events.append(('capture',k));return 'capture-ref'
  def obj(ref):raise StopBeforeBridge()
  modules={}
  for name in('fa_native_geometry','cache_observation','fa_prefill131r10','native_seams'):
   module=types.ModuleType(name);module.__file__=files.get(name+'.py',name);modules[name]=module
  modules['fa_native_geometry'].bind_all=bind
  modules['cache_observation'].capture=capture;modules['fa_prefill131r10'].capture=capture
  C=types.SimpleNamespace(ref=lambda x:x,obj=obj)
  ns=dict(E=types.SimpleNamespace(need=R.need),state=state,m=m,refs=refs,C=C,torch=types.SimpleNamespace(Tensor=Tensor,int32='i32',int64='i64',bfloat16='bf16'),
   source_ref='source',worker=worker,inner=inner,get_attention_context=ctx,group=types.SimpleNamespace(rank_in_group=0),
   fast_performance=fast,restore_tail=lambda:events.append(('restore',None)),R=types.SimpleNamespace(register=reg))
  if mutate:mutate(kw,m,modules)
  prior={k:sys.modules.get(k)for k in modules};present={k:k in sys.modules for k in modules}
  try:
   sys.modules.update(modules);exec(compile(unit,'actual-rendered-after-prefill','exec'),ns)
   ns['after_prefill'](**kw)
  finally:
   for k in modules:
    if present[k]:sys.modules[k]=prior[k]
    else:sys.modules.pop(k,None)
  return state,events
 def test_actual_rendered_callback_prefix_reaches_original_bridge_seam(self):
  for fast in(False,True):
   with self.assertRaises(StopBeforeBridge):self.fixture(fast=fast)
 def test_actual_rendered_callback_real_domain_negative_controls(self):
  changes=[
   lambda k,m,n:m['performance_profile']['scope'].update(input_tokens=131),
   lambda k,m,n:m['performance_profile']['scope'].update(output_tokens=160),
   lambda k,m,n:k.update(input_ids=Tensor((131,),values=list(range(131)))),
   lambda k,m,n:k['native_input'].update(request_id='other'),
   lambda k,m,n:k['native_input']['sources'].update(runner='wrong'),
   lambda k,m,n:k['native_input']['actual_CPU_token_ids'].pop(),
   lambda k,m,n:k.update(positions=Tensor((2048,),'i64',list(range(2047))+[0])),
   lambda k,m,n:k.update(hidden=Tensor((131,5120),'bf16')),
   lambda k,m,n:k.update(hidden=Tensor((2048,5120),'fp16')),
   lambda k,m,n:setattr(n['fa_native_geometry'],'__file__','wrong-ref')]
  for mutate in changes:
   with self.subTest(change=changes.index(mutate)):
    with self.assertRaises((ValueError,KeyError)):self.fixture(mutate)
 def test_prefill_tail_and_layer_slots_are_already_length_general(self):
  base=R.PARENT
  tail=(base/'prefill_tail.py').read_text();slots=(base/'layer_slots131r10.py').read_text()
  self.assertIn('type(length) is int and length > 0',tail);self.assertIn('meta.num_actual_tokens == length',tail)
  self.assertIn('(observation[\'slot\'],observation[\'length\'])==(slot,length)',tail)
  self.assertIn('owner.length==self.length',slots);self.assertNotIn('==131',slots)
if __name__=='__main__':unittest.main()
