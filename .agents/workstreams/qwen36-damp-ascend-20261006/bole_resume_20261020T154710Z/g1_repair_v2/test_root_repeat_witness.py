from repair14_ledger import previous_text
import g1_inverse as G1
"""Real actual-source Python body replay on CPU, not backend or model proof."""
import ast,contextvars,inspect,json,sys,threading,types,unittest
from pathlib import Path
from itertools import islice
import torch as t
import root_repeat_witness as W
import root_repeat_consumer as R
import sourceio as C
P=Path(__file__).resolve().parent

def actual_fn(path,cls):
 tree=ast.parse(path.read_bytes());node=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name==cls)
 fn=next(x for x in node.body if isinstance(x,ast.FunctionDef)and x.name=='forward')
 module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fn],type_ignores=[])
 ns=dict(torch=t,IntermediateTensors=dict,islice=islice,
  get_pp_group=lambda:types.SimpleNamespace(is_first_rank=True,is_last_rank=True),
  _EXTRA_CTX=types.SimpleNamespace(flash_comm_v1_enabled=False))
 exec(compile(ast.fix_missing_locations(module),str(path),'exec'),ns);return ns['forward'],ns

def mirror(perturb=False):
 """Two CPU layers, complete source bodies; deliberately no actual class claim."""
 decoder,dns=actual_fn(P/'evidence/root_witness_actual_patch.py','AscendQwen3_5DecoderLayer')
 gdn,gns=actual_fn(P/'evidence/gdn.py','AscendGatedDeltaNetAttention')
 model,mns=actual_fn(P/'evidence/qwen3_next.py','Qwen3NextModel')
 G=type('SoftwareGDN',(),{'forward':gdn,'__call__':gdn});D=type('SoftwareDecoder',(),{'forward':decoder,'__call__':decoder});M=type('SoftwareModel',(),{'forward':model})
 layers=[];state={'call':0}
 for i in range(2):
  obj=G();obj.in_proj_qkv=lambda x:(t.ones((1,2560)),None);obj.in_proj_ba=lambda x:(t.ones((1,24)),None)
  obj.in_proj_z=lambda x:(t.ones((1,1536)),None);obj.head_v_dim=128;obj.num_v_heads=12;obj.tp_size=1;obj.prefix='software'
  obj._split_ba_for_tp=lambda x:x.chunk(2,-1);obj.norm=lambda x,z:x+z
  from test_projection_trace import native
  apply=native('ascend_linear.py','AscendUnquantizedLinearMethod.apply',{'torch':types.SimpleNamespace(ops=types.SimpleNamespace(vllm=types.SimpleNamespace(unquantized_gemm=lambda x,w,b:t.cat((x,t.zeros((1,5120-x.shape[-1]))),-1))))})
  quant=type('SoftwareProjectionQuant',(),{'apply':apply})()
  pf=native('vllm_linear.py','RowParallelLinear.forward',{'tensor_model_parallel_all_reduce':lambda x:x})
  proj=type('SoftwareProjection',(),{'forward':pf,'__call__':pf})()
  for key,value in dict(quant_method=quant,custom_op=None,weight=object(),prefix='software',input_is_parallel=True,tp_rank=0,tp_size=1,bias=None,skip_bias_add=False,reduce_results=True,return_bias=True).items():setattr(proj,key,value)
  obj.out_proj=proj
  layer=D();layer.layer_idx=i;layer.layer_type='linear_attention';layer.layer_scale=False;layer.linear_attn=obj
  layer.input_layernorm=lambda x,r=None:x.clone()if r is None else(x.clone(),r.clone())
  layer.post_attention_layernorm=lambda x,r:(x.clone(),r.clone())
  layer.mlp=lambda x,idx=i:x+3+(1 if perturb and idx==0 and state['call']==2 else 0)
  layers.append(layer)
 gns['torch']=types.SimpleNamespace(zeros=t.zeros,ops=types.SimpleNamespace(vllm=types.SimpleNamespace(qwen_gdn_attention_core=lambda q,b,a,out,*x:out.fill_(2))))
 gns['maybe_save_kv_layer_to_connector']=lambda *x:None;gns['rearrange']=lambda x,*args:x.reshape(1,-1)
 obj=M();obj.layers=layers;obj.start_layer=0;obj.end_layer=2;obj._maybe_add_hidden_state=lambda acc,*args:acc
 obj.embed_input_ids=lambda ids:t.ones((1,5120));obj.norm=lambda h,r:(h+r,None)
 w=W.Witness.__new__(W.Witness);w.t=t;w.C=C;w.BUS=contextvars.ContextVar('software_ar',default=None)
 w.owner=types.SimpleNamespace(request='software',generation=1,slot=0,length=131,version=0);w.tokens=(7,8,9)
 w.bridge=types.SimpleNamespace(model=obj,own_source={'runtime_sources':{k:C.ref(P/p)for k,p in [('qwen_patch','evidence/root_witness_actual_patch.py'),('gdn','evidence/gdn.py'),('qwen_next','evidence/qwen3_next.py')]}})
 w.model_code=model.__code__;w.codes={decoder.__code__:'decoder',gdn.__code__:'gdn'};w.objects={}
 for i,l in enumerate(layers):w.objects[id(l)]=('decoder',i,l);w.objects[id(l.linear_attn)]=('gdn',i,l.linear_attn)
 w.thread=threading.get_ident();w.frames={};w.rows=[];w.retained=[];w.calls=[];w.used=0;w.fault=None;w.entered=False;w.active_objects=[]
 import projection_trace as PT
 def scope():
  active=[v for v in w.frames.values()if v[0]=='gdn'and v[2]==0]
  return None if not active else(active[0][1],layers[0].linear_attn)
 refs={str(P/'evidence'/n):C.ref(P/'evidence'/n)for n in('vllm_linear.py','ascend_linear.py')}
 w.projection=PT.ProjectionTrace(C,layers[0].linear_attn.out_proj,refs,lambda c,s,v:w._snapshot(c,'out_proj',0,s,v),scope)
 return w,state

def execute(w,state):
 outputs=[]
 with w:
  for ordinal,node in enumerate((0,1,0,2)):
   state['call']=ordinal;ctx=types.SimpleNamespace(owner=w.owner,tokens=(w.tokens[node],),positions=(131+ordinal%2,),mode='AR')
   token=w.BUS.set(ctx)
   try:outputs.append(w.bridge.model.forward(t.tensor([w.tokens[node]]),t.tensor([131+ordinal%2])))
   finally:w.BUS.reset(token)
 return outputs

def payload(w,value):
 # Structural old-capture fixture, explicitly software CPU replay only.
 native=[]
 for call in(0,2):
  rows={(r['kind'],r['layer'],r['stage']):r for r in value['rows']if r['call']==call}
  captures={}
  for layer in(0,1):
   projected=rows[('gdn',layer,'projection_complete')]['tensors'];core=rows[('gdn',layer,'core_complete')]['tensors']
   captures[layer]=dict(inputs=projected['mixed_qkv']['immediate'].clone(),a=projected['a']['immediate'].clone(),b=projected['b']['immediate'].clone(),output=core['core_attn_out']['immediate'].clone())
  native.append(dict(steps=[dict(node=0,hidden=rows[('model',None,'immediate_final_hidden')]['tensors']['hidden']['immediate'].clone(),context=dict(captures=captures))]))
 return dict(root_repeat_witness=value,request=value['owner'],tree_context=dict(tokens=w.tokens),native=native)

class Tests(unittest.TestCase):
 def test_complete_actual_three_bodies_trace_positive_and_mlp_discrimination(self):
  for perturb in(False,True):
   w,state=mirror(perturb)
   with t.inference_mode():outputs=execute(w,state)
   self.assertIsNone(sys.gettrace());value=w.freeze()
   raw=payload(w,value)
   report=R.consume(t,raw,w.bridge.own_source)
   if perturb:self.assertEqual(report['first_immediate_root_difference']['key'],['decoder',0,'mlp_output'])
   else:self.assertIsNone(report['first_immediate_root_difference'])
   self.assertFalse(report['private_clone_lifetime_faults']);self.assertEqual(len(outputs),4)

 def test_private_clone_mutation_vs_legitimate_original_reuse(self):
  w,_=mirror();x=t.tensor([0.,-0.,float('nan')]);w._snapshot(0,'model',None,'x',dict(x=x))
  x.fill_(3);w._lifetime(0)
  item=w.rows[0]['tensors']['x'];self.assertTrue(item['lifetime'][0]['private_bits_equal']);self.assertFalse(item['lifetime'][0]['original_bits_equal'])
  w.retained[0][1].fill_(7);w._lifetime(1)
  self.assertFalse(item['lifetime'][-1]['private_bits_equal']);self.assertIn('changed_private',item)

 def test_actual_source_line_contract_and_mismatched_source_reject(self):
  refs={k:C.ref(P/p)for k,p in [('qwen_patch','evidence/root_witness_actual_patch.py'),('gdn','evidence/gdn.py'),('qwen_next','evidence/qwen3_next.py')]}
  W.source_contract(C,refs)
  refs['gdn']=dict(refs['gdn'],sha256='0'*64)
  with self.assertRaises(ValueError):W.source_contract(C,refs)

 def test_exception_and_existing_trace_restore_exact_namespace(self):
  w,state=mirror();old=lambda *args:None;sys.settrace(old)
  try:
   with self.assertRaises(ValueError):w.__enter__()
   self.assertIs(sys.gettrace(),old)
  finally:sys.settrace(None)
  w,state=mirror();w.bridge.model.layers[0].mlp=lambda x:(_ for _ in()).throw(RuntimeError('actual replay fault'))
  with self.assertRaises(RuntimeError):execute(w,state)
  self.assertIsNone(sys.gettrace());self.assertIsNotNone(w.fault)
  with self.assertRaises(ValueError):w.freeze()

 def test_budget_before_clone_missing_boundary_and_wrong_owner_refuse(self):
  w,_=mirror()
  with self.assertRaises(ValueError):w._snapshot(0,'model',None,'large',dict(x=t.zeros(65537)))
  self.assertEqual(w.used,0)
  w,state=mirror();execute(w,state);v=w.freeze();raw=payload(w,v)
  v['rows']=v['rows'][1:]
  with self.assertRaises(ValueError):R.consume(t,raw,w.bridge.own_source)

 def test_real_integration_unchanged_sequential_and_no_operator_replacement(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());proof=json.loads((P/'ROOT_WITNESS_EDITS.json').read_bytes())
  for name,p in proof.items():
   after=previous_text(P/name);restored=after
   for e in reversed(p['edits']):self.assertEqual(restored.count(e['after']),1);restored=restored.replace(e['after'],e['before'])
   self.assertEqual(__import__('hashlib').sha256(restored.encode()).hexdigest(),p['before']['sha256'])
  original=json.loads((P/'evidence/HISTORICAL_SOURCE_TEMPLATE_ROOT_R18.json').read_bytes())
  self.assertEqual(__import__('hashlib').sha256(previous_text(P/'model_entry.py').encode()).hexdigest(),original['files']['model_entry.py']['sha256'])
  for name in('native_seams.py','independent_model.py','core112.py','adapter.py','native_logits.py','native_dtype131r13.py','worker_entry.py'):
   self.assertEqual(__import__('hashlib').sha256(G1.previous_text(P/name).encode()).hexdigest(),original['files'][name]['sha256'])
  text=(P/'model_smoke.py').read_text();self.assertIn('with witness:',text);self.assertIn('root_repeat_witness=witness.freeze()',text)
  tree=ast.parse((P/'root_repeat_witness.py').read_bytes())
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id in('setattr','delattr')for n in ast.walk(tree)))

 def test_actual_installed_worker_wrapper_source_and_bound_old_closure(self):
  import worker_entry as ENTRY,os
  from unittest.mock import patch
  path=P/'evidence/qwen3_next.py';tree=ast.parse(path.read_bytes());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Qwen3NextModel');fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='forward')
  node=ast.ClassDef(name='Qwen3NextModel',bases=[],keywords=[],body=[fn],decorator_list=[])
  mod=types.ModuleType('_explicit_software_qwen_root_mirror');mod.__file__=str(path);sys.modules[mod.__name__]=mod
  module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),node],type_ignores=[])
  exec(compile(ast.fix_missing_locations(module),str(path),'exec'),mod.__dict__)
  obj=mod.Qwen3NextModel();worker=types.SimpleNamespace(_bole_model_objects=dict(inner=obj))
  getter=lambda:None;callback=lambda **kw:None;tr=C.ref(__file__)
  own=dict(files={'worker_entry.py':C.ref(ENTRY.__file__)},runtime_sources=dict(qwen_next=C.ref(path)))
  try:
   with patch.dict(os.environ,BOLE_MODEL_OBJECT_AUDIT_ENABLE='1'):
    restore=ENTRY.install_after_native_prefill(worker,C,qwen_next_ref=C.ref(path),get_forward_context=getter,context_source_ref=tr,callback=callback,callback_source_ref=tr)
   self.assertIs(W.native_model(C,types.SimpleNamespace(model=obj),own),mod.Qwen3NextModel.forward.__code__)
   original=obj.forward.__func__.__wrapped__;obj.forward.__func__.__wrapped__=object()
   with self.assertRaises(ValueError):W.native_model(C,types.SimpleNamespace(model=obj),own)
   obj.forward.__func__.__wrapped__=original;restore()
  finally:sys.modules.pop(mod.__name__)

 def test_late_legacy_capture_drift_not_called_native_compute_difference(self):
  w,state=mirror();execute(w,state);value=w.freeze();raw=payload(w,value)
  raw['native'][0]['steps'][0]['hidden'].fill_(99)
  report=R.consume(t,raw,w.bridge.own_source)
  self.assertIsNone(report['first_immediate_root_difference'])
  bad=[x for x in report['late_legacy_capture_joins']if not x['late_legacy_equals_immediate']]
  self.assertEqual([(x['call'],x['key'])for x in bad],[(0,['model',None,'immediate_final_hidden'])])

if __name__=='__main__':unittest.main()
