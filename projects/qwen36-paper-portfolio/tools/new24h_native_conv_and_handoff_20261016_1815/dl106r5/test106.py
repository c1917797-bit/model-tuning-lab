import ast,hashlib,importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import qualification106 as Q,common106 as C
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def original_file(name):
 if sys.platform=='win32':
  root=P.parent/'deltalog-real-worker-new24h-101-repair5';b=(root/'SOURCE_TEMPLATE.json').read_bytes();assert(len(b),hashlib.sha256(b).hexdigest())==(Q.MODEL_TEMPLATE['bytes'],Q.MODEL_TEMPLATE['sha256']);m=json.loads(b);r=m['files'][name];p=root/name;data=p.read_bytes();assert(len(data),hashlib.sha256(data).hexdigest())==(r['bytes'],r['sha256']);return p
 return Q.checked(Q.obj(Q.MODEL_TEMPLATE)['files'][name])
class Controls(unittest.TestCase):
 def test_real_cold_OFF_package_and_bind(self):
  code='import sys,os;sys.path.insert(0,'+repr(str(P))+');os.environ.pop("QWEN36_DELTALOG_PRODUCTION106_ENABLE",None);from qwen36_deltalog_production106 import register;register();assert not any(n in sys.modules for n in("torch","torch_npu","vllm","vllm_ascend"))'
  r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  r=subprocess.run([sys.executable,'-I','-B',str(P/'bind106.py')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_real_ON_missing_future_evidence_before_torch(self):
  code='import sys,os;sys.path.insert(0,'+repr(str(P))+');os.environ.update(QWEN36_DELTALOG_PRODUCTION106_ENABLE="1",QWEN36_DELTALOG_PRODUCTION106_MODE="production-bounded",QWEN36_DELTALOG_PRODUCTION106_SOURCE_REF="{}",QWEN36_DELTALOG_PRODUCTION106_QUALIFICATION_REF="{}");from qwen36_deltalog_production106 import register\ntry:register()\nexcept (ValueError,KeyError):pass\nelse:raise AssertionError("future refs admitted")\nassert "torch" not in sys.modules'
  e=dict(os.environ)
  for k in list(e):
   if k.startswith(('QWEN36_DELTALOG','MXR_CAPTURE','VLLM_PROFILER','TORCH_PROFILER')):e.pop(k)
  r=subprocess.run([sys.executable,'-I','-B','-c',code],env=e,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_actual_CPU_query_tuple_and_shape_boundaries(self):
  for np,q in((1,(0,2048)),(0,(0,1))):self.assertEqual(C.request_geometry(types.SimpleNamespace(num_prefills=np,num_decodes=1-np),dict(query=dict(values=q))),q)
  for q in([0,2048],(0,129),(0,3151),(0,16384)):
   with self.assertRaises(ValueError):C.request_geometry(types.SimpleNamespace(num_prefills=1,num_decodes=0),dict(query=dict(values=q)))
  for n in(200,417,3151,16384):
   with self.assertRaises(ValueError):C.check_shape(prompt_tokens=n,sequences=1)
  with self.assertRaises(ValueError):C.check_shape(prompt_tokens=2048,sequences=16)
 def test_unchanged_flush_equation_AST_and_13args(self):
  def fn(p,name):return next(n for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name==name)
  keep=('selected','selected_base','k_log','u_log','lambda_log','decay','length','live','safe_lambda','coeff','live_payload','safe_u_log','safe_k_log','contribution','logical')
  def equations(f):return[ast.dump(n,include_attributes=False)for n in f.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id in keep]
  self.assertEqual(equations(fn(original_file('plugin/qwen36_deltalog_service/primitives.py'),'_flush_slots')),equations(fn(P/'qwen36_deltalog_production106/primitives.py','_flush_slots')))
  for f in(original_file('plugin/qwen36_deltalog_service/runtime.py'),P/'qwen36_deltalog_production106/runtime.py'):
   n=fn(f,'_route');op=next(x for x in ast.walk(n)if isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=='_OP');self.assertEqual(len(op.args),13)
  for n in('runtime_helpers.py','binding.py','builder_mirror.py','integration.py','layout_controls.py','transform.py'):
   self.assertEqual(original_file('plugin/qwen36_deltalog_service/'+n).read_bytes(),(P/'qwen36_deltalog_production106'/n).read_bytes())
 def test_real_finite_flush_bitwise_and_sticky_failure(self):
  import torch
  torch.set_num_threads(1)
  from qwen36_deltalog_production106 import primitives as N,health
  # Load original021 without its package to execute the same actual flush body.
  tree=ast.parse(original_file('plugin/qwen36_deltalog_service/primitives.py').read_bytes());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='_flush_slots');ns=dict(Any=object,CAPACITY=7,VALUE_HEADS=12,KEY_HEADS=4,_audit=lambda *a,**k:None);exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual021flush>','exec'),ns)
  for length in(0,3,7):
   torch.manual_seed(106+length);base=torch.randn(2,12,128,128)*.01;aux=dict(k_log=torch.randn(2,4,7,128).bfloat16(),u_log=torch.randn(2,12,7,128)*.01,lambda_log=torch.zeros(2,12,16),decay=torch.zeros(2,12,16),length=torch.zeros(2,12,16,dtype=torch.int32));aux['length'][0,:,0]=length;aux['k_log'][0,:,length:]=float('nan');aux['u_log'][0,:,length:]=float('nan');other={k:v.clone()for k,v in aux.items()};left=types.SimpleNamespace(kv_cache=[None,base.clone()]);right=types.SimpleNamespace(kv_cache=[None,base.clone()]);ids=torch.tensor([0],dtype=torch.int32)
   ns['_flush_slots'](torch,left,aux,ids,'test');N._flush_slots(torch,right,other,ids,'test');self.assertTrue(torch.equal(left.kv_cache[1].view(torch.uint8),right.kv_cache[1].view(torch.uint8)))
  health.observe(torch,torch.tensor([float('nan')]));health.observe(torch,torch.tensor([1.]));self.assertFalse(health.snapshot(torch,outside_timing=True)['all_finite'])
 def test_no_host_scalar_or_tensor_capture_in_hot_functions(self):
  paths=('runtime.py','primitives.py')
  for name in paths:
   tree=ast.parse((P/'qwen36_deltalog_production106'/name).read_bytes())
   for f in[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('_route','_ensure_aux','_flush_slots','_flush_all')]:
    attrs={n.func.attr for n in ast.walk(f)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)};self.assertFalse(attrs&{'cpu','item','tolist','synchronize','save','load_library'},(name,f.name,attrs))
 def test_exact_Ref_rejects_mutation(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'evidence.json';p.write_bytes(b'{}\n');r=Q.ref(p);self.assertEqual(Q.obj(r),{});p.write_bytes(b'{ }\n')
   with self.assertRaises(ValueError):Q.obj(r)
 def test_qualifier_never_accepts_published_future_boolean(self):
  with patch.object(Q,'obj',return_value=dict(execution_admitted=True)),patch.object(Q,'consume',return_value=dict(execution_admitted=False)):
   with self.assertRaises(ValueError):Q.qualify({}, {})
  import live106
  value=dict(schema='deltalog.production-worker/v106',source_ref={},qualification_ref={},mode='bounded-production',tensor_capture=False,native_peer=False,graph=False,async_scheduling=False,PDC=False,synchronization_outside_timing=True,tensor_snapshot=False,receipt_trigger='SIGUSR1 outside timed client interval',health=dict(outside_timing=True,all_finite=False,rows={'cpu':dict(finite=False,observations=3)}))
  with patch.object(Q,'qualify',return_value={}):
   with self.assertRaises(ValueError):live106.validate_snapshot(value,{},{})
 def test_model_receipt_gate_positive_and_real_missing_retirement_rejects(self):
  # In-memory ABI fixture ONLY. Components themselves are separately checked
  # by the actual101 reader tests; no mock is written as an evidence receipt.
  from copy import deepcopy
  refs={n:{'label':n}for n in('model','owner','component','component-owner','library','plugin','plugin-template','typed-reader','model-consumer','tensor','loaded','client','tensor-contract')};sr=refs['model'];ids=('assigned-a','assigned-b');prefixes=('first','middle','last')
  tensor_contract=dict(schema='actual-software-contract');pins={'tensor_consumer.py':refs['tensor-contract']};rmodel=dict(prepared_template=Q.MODEL_TEMPLATE,prepared_only=False,files=pins,root='/actual101',library_ref=refs['library'],bridge024_source_ref=refs['component'],bridge024_owner_ref=refs['component-owner'],plugin_source=refs['plugin'],plugin_template_ref=refs['plugin-template'],split_qualification_api_ref=refs['typed-reader'])
  owner=dict(schema='deltalog.actual-owned-dispatch-smoke/v025',source=sr,component_owner=refs['component-owner'],primary=None,secondary=[],all_created_containers_release_verified=True,status='actual-DL-smoke-only',owned_containers=[dict(cid=str(i),exact_owned_release_verified=True)for i in range(3)],independent_smoke_consumer=refs['model-consumer'],actual_loaded_workers=refs['loaded'],client=refs['client'])
  rows=[]
  for rank in range(4):
   for prefix in prefixes:
    for rid in ids:
     for step in range(10):
      identity=dict(rank=rank,prefix=prefix,engine_request_id=rid,kind='prefill'if step==0 else'decode');v=dict(passed=True)
      if step:v.update(length_before=(step-1)%8,length_after=step%8)
      rows.append(dict(identity=identity,independent=v))
  selections=[dict(rank=i,selected=list(prefixes),all48=list(range(48)))for i in range(4)]
  tensor=dict(schema='deltalog.selected-model-tensor-diagnostic/v026',source=sr,primary=None,modified_decode_arithmetic_pass=True,validation_contract=tensor_contract,actual_second_request_slot_reuse_observed=True,selections=selections,records=rows)
  c=dict(schema='deltalog.model-selected-tensor-independent-consumption/v026',source=sr,actual_loaded_workers=refs['loaded'],actual_client=refs['client'],smoke_dispatch_and_response_pass=True,selected_modified_decode_pass=True,actual_slot_reuse_observed=True,responses=[dict(prompt_tokens=2048,output_tokens=10,finish='length')for _ in ids],dispatch=dict(dispatch_trajectory_pass=True,capacity7_merge_reachable=True,rows=[dict(rank=i,all48=True,requests={rid:dict(prefill=True,decode=9)for rid in ids})for i in range(4)]),actual_assignments=[dict(engine_id=i)for i in ids],actual_retirement=[dict(engine_id=i,all4_actual_retirement_pass=True,error=None)for i in ids],selected_tensor_ref=refs['tensor'],validation_contract=tensor_contract)
  objects=dict(model=rmodel,owner=owner,plugin=dict(prepared_template=refs['plugin-template'],files={'qwen36_deltalog_service/split_qualification.py':refs['typed-reader']},prepared_only=False),tensor=tensor)
  objects['plugin-template']=dict(files=objects['plugin']['files']);objects['model-consumer']=c
  m=dict(model_source_ref=sr,model_owner_ref=refs['owner'],library_ref=refs['library'],component_source_ref=refs['component'],component_owner_ref=refs['component-owner'])
  comp=dict(schema='deltalog.eager-component-to-model-diagnostic/v101',diagnostic_smoke_admitted=True,source=refs['component'],owner=refs['component-owner'])
  def lookup(r):return dict(files=pins,root='/actual101')if r==Q.MODEL_TEMPLATE else objects[r['label']]
  def loader(r,n):return types.SimpleNamespace(admit=lambda C,m:comp)if r==refs['typed-reader']else types.SimpleNamespace(VALIDATION_CONTRACT=tensor_contract)
  with patch.object(Q,'obj',side_effect=lookup),patch.object(Q,'checked',return_value=P),patch.object(Q,'load',side_effect=loader):
   self.assertEqual(Q.model_gate(m)['model_library'],refs['library'])
   saved=deepcopy(c['actual_retirement']);c['actual_retirement'][1]['all4_actual_retirement_pass']=False
   with self.assertRaises(ValueError):Q.model_gate(m)
   c['actual_retirement']=saved;tensor['records'][-1]['independent']['passed']=False
   with self.assertRaises(ValueError):Q.model_gate(m)
if __name__=='__main__':unittest.main()
