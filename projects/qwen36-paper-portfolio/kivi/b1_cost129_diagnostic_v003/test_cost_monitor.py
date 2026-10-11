"""Real original Python bodies + inert tensor boundaries, never a model/NPU claim."""
import ast, copy, importlib.util, json, os, sys, types, unittest, tempfile, subprocess
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import cost_monitor as P
def load(ref,name):
 s=importlib.util.spec_from_file_location(name,ref["path"]);m=importlib.util.module_from_spec(s)
 sys.modules[name]=m
 exec(compile(Path(ref["path"]).read_bytes(),ref["path"],"exec"),m.__dict__)
 return m
def existing_sync():
 EVENTS.append("sync")
EVENTS=[]
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  local=HERE.parent/"LOCAL_TARGET_REFS.json"
  if os.name=="nt":
   cls.refs=json.loads(local.read_bytes())
  else:
   m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
   cls.refs={n:m["runtime_roles"][n] for n in P.TARGETS if n!="writer"}
   cls.refs["writer"]=next(r for r in m["dependencies"]if r["sha256"]=="051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b")
  for r in cls.refs.values():r["path"]=str(Path(r["path"]).resolve())
  reader=types.ModuleType("reader");reader.k_rows=reader.v_rows=reader.attend=lambda *a:None
  cls.ambient_modules=dict(sys.modules)
  sys.modules["reader"]=reader
  cls.modules={r:load(ref,"_monitor_actual_"+r)for r,ref in cls.refs.items()if r!="lifecycle"}
  sys.modules["device_writer"]=cls.modules["writer"]
  cls.modules["lifecycle"]=load(cls.refs["lifecycle"],"_monitor_actual_lifecycle")
  cls.meta=cls.modules["metadata"];cls.producer=cls.modules["producer"]
 @classmethod
 def tearDownClass(cls):
  for name in ('reader','device_writer'):
   if name in cls.ambient_modules:sys.modules[name]=cls.ambient_modules[name]
   else:sys.modules.pop(name,None)
 def session(self,sync=None):
  return P.Session(self.refs,self.modules,rank=0,arm="candidate",source_ref={"fixture":"source"},recipe_ref={"fixture":"recipe"},synchronize=sync)
 def view(self):
  r=self.modules["lifecycle"].Request(slot=0,epoch=1,owner="real-python-body",generation=2,length=32768,
    kp=tuple(range(256)),vp=tuple(range(32640)),kt=0,vt=128,pending=True)
  a=types.SimpleNamespace(owned=lambda v:None,krefs=dict.fromkeys(r.kp,1),vrefs=dict.fromkeys(r.vp,1))
  return types.SimpleNamespace(a=a,r=r,generation=2,pending=True,read_length=32769)
 def invoke(self,v=None):
  return self.meta.row_plan(self.view()if v is None else v,None,capacity=33792,pool_pages=2376,pool_records=304128,pool_slots=16)
 def test01_actual_row_plan_return_and_prefix_count(self):
  p=self.session();before=self.invoke();actual=p.run("measured",self.invoke)
  self.assertEqual(actual,before);value=p.finish();row=next(r for r in value["stats"]if r["label"]=="metadata.row_plan")
  self.assertEqual((row["calls"],row["returns"],row["owned_prefix_entries"]),(1,1,32896))
  self.assertGreater(row["wall_ns"],0);self.assertGreaterEqual(row["thread_cpu_ns"],0)
 def test02_original_owner_guard_still_raises_same(self):
  v=self.view();v.a.vrefs.pop(400);p=self.session()
  with self.assertRaisesRegex(ValueError,"actual owned V records"):p.run("measured",self.invoke,v)
  self.assertIsNone(sys.getprofile());self.assertFalse(p.active)
  row=p.finish();self.assertTrue(row["windows"][0]["failed"])
 def test03_no_tensor_io_or_files_in_steady_window(self):
  p=self.session()
  with patch.object(Path,"read_bytes",side_effect=AssertionError("file inside profile")):
   self.assertEqual(p.run("steady",self.invoke)["controls"],(32769,32768,32640,0))
  self.assertEqual(p.finish()["tensor_snapshots"],0)
 def test04_original_sync_invoked_once_never_added(self):
  EVENTS.clear();p=self.session(existing_sync)
  p.run("measured",existing_sync);value=p.finish()
  self.assertEqual(EVENTS,["sync"]);self.assertEqual(value["new_synchronizations"],0)
  self.assertEqual(sum(r["calls"]for r in value["stats"]if r["label"].startswith("existing_sync@")),1)
 def test05_original_exception_identity_and_sync_order(self):
  EVENTS.clear();p=self.session(existing_sync);error=RuntimeError("original failure")
  def original():
   existing_sync();raise error
  try:p.run("failure",original)
  except RuntimeError as actual:self.assertIs(actual,error)
  else:self.fail("original failure swallowed")
  self.assertEqual(EVENTS,["sync"]);self.assertIsNone(sys.getprofile())
 def test06_ambient_profiler_rejected_preserved(self):
  p=self.session();old=lambda *a:None;sys.setprofile(old)
  try:
   with self.assertRaisesRegex(ValueError,"ambient monitoring/profiling"):p.run("x",self.invoke)
   self.assertIs(sys.getprofile(),old)
  finally:sys.setprofile(None)
 def test07_forged_same_filename_function_is_rejected(self):
  old=self.meta.row_plan
  forged=old.__code__.replace(co_consts=old.__code__.co_consts+("foreign",))
  self.meta.row_plan=types.FunctionType(forged,self.meta.__dict__)
  try:
   with self.assertRaisesRegex(ValueError,"actual target code differs"):self.session()
  finally:self.meta.row_plan=old
 def test08_source_hash_mismatch_rejected_before_install(self):
  refs=copy.deepcopy(self.refs);refs["metadata"]["sha256"]="0"*64
  with self.assertRaisesRegex(ValueError,"exact whole target source"):
   P.Session(refs,self.modules,rank=0,arm="candidate",source_ref={},recipe_ref={})
 def test09_whole_targets_required_not_silent_missing(self):
  refs=copy.deepcopy(self.refs);refs.pop("kernel")
  with self.assertRaisesRegex(ValueError,"complete source and actual module closure"):P.Session(refs,self.modules,rank=0,arm="candidate",source_ref={},recipe_ref={})
 def test10_phase_segments_do_not_overlap_or_hide_warmup(self):
  p=self.session()
  p.run("warmup0",self.invoke);p.run("warmup1",self.invoke);p.run("request00",self.invoke)
  x=p.finish();self.assertEqual([r["phase"]for r in x["windows"]],["warmup0","warmup1","request00"])
  self.assertEqual(len([r for r in x["stats"]if r["label"]=="metadata.row_plan"]),3)
 def test11_nested_row_plan_owned_inclusive_not_sum(self):
  p=self.session();v=self.view();v.a.active={0:v.r};v.a.epochs={0:1}
  v.a.owned=types.MethodType(self.modules["lifecycle"].CompactArena.owned,v.a)
  p.run("nested",self.invoke,v);value=p.finish()
  self.assertTrue(value["inclusive_categories_must_not_be_summed"])
  self.assertEqual({r["label"]for r in value["stats"]},{"metadata.row_plan","lifecycle.owned"})
 def test12_real_append_read_unchanged_calls_outputs_and_fence(self):
  oldroot=HERE
  os.environ.setdefault("KIVI_SCREEN_PRODUCER_ARCHIVE",str(oldroot))
  ref=P.reference(oldroot/"test_observer_off.py")
  fixture=load(ref,"_probe_actual_baseline_fixture")
  p=self.session();result=p.run("measured",fixture.full_off,self.producer)
  expected=fixture.full_off(self.producer);self.assertEqual(result,expected)
  row=p.finish();counts={r["label"]:r["calls"]for r in row["stats"]}
  self.assertEqual(counts["producer.append_read"],1);self.assertEqual(counts["producer.plan_requests"],1)
  self.assertEqual(result[1].count("sync"),1)
 def test13_closed_or_nested_session_rejected(self):
  p=self.session()
  def nested():
   with self.assertRaises(ValueError):p.run("inner",self.invoke)
  p.run("outer",nested);p.finish()
  with self.assertRaises(ValueError):p.run("closed",self.invoke)
 def test14_not_device_or_performance_evidence(self):
  p=self.session();p.run("x",self.invoke);v=p.finish()
  for k in("device_kernel_time_measured","numerical_verified","performance_accepted","run_authority"):self.assertIs(v[k],False)
  self.assertEqual(v["per_token_file_publications"],0);self.assertGreater(v["monitor_events"],0)
 def test15_original_monitor_tool_owner_untouched(self):
  p=self.session();sys.monitoring.use_tool_id(4,"another-owner")
  try:
   with self.assertRaisesRegex(ValueError,"ambient"):p.run("x",self.invoke)
   self.assertEqual(sys.monitoring.get_tool(4),"another-owner")
  finally:sys.monitoring.free_tool_id(4)
 def test16_no_loop_generator_or_instruction_events(self):
  p=self.session();p.run("x",self.invoke);x=p.finish()
  self.assertLess(x["monitor_events"],20)
  self.assertEqual(x["local_events"],["PY_START","PY_RETURN"])
  self.assertIsNone(sys.monitoring.get_tool(4));self.assertEqual(sys.monitoring.get_events(4),0)
 def native(self):
  """Actual NPUWorker execute/sample bodies; only external ABI objects are inert."""
  m=json.loads((HERE/'SOURCE_MANIFEST.json').read_bytes())
  r=next(q for q in m['dependencies']if q['sha256']=='c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3')
  path=Path('C:/Users/Huawei/AppData/Local/Temp/c156-kivi-native-reviewed-20261010/npu_worker.py')if os.name=='nt'else Path(r['path'])
  actual=P.reference(path);self.assertEqual((actual['bytes'],actual['sha256']),(r['bytes'],r['sha256']))
  tree=ast.parse(path.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='NPUWorker')
  nodes=[copy.deepcopy(n)for n in cls.body if isinstance(n,ast.FunctionDef)and n.name in('execute_model','sample_tokens')]
  for node in nodes:node.decorator_list=[]
  class Output:pass
  env=dict(ModelRunnerOutput=Output,AsyncModelRunnerOutput=type('Async',(),{}),NoneType=type(None),
   get_ascend_config=lambda:types.SimpleNamespace(msmonitor_use_daemon=False),
   get_pp_group=lambda:types.SimpleNamespace(is_first_rank=True))
  source=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+nodes,type_ignores=[])
  exec(compile(ast.fix_missing_locations(source),str(path),'exec'),env)
  return env,Output
 def chain(self):
  import cost_runtime as R,transport
  env,Output=self.native();session=P.Session(self.refs,self.modules,rank=0,arm='dense',source_ref={'source':1},recipe_ref={'recipe':1})
  ids=['a','b','c'];published=[];final={'final':1};outputs=[]
  runtime=R.Runtime(session,ids,lambda v:published.append(v)or{'published':1})
  def execute(scheduler,intermediate):
   self.assertIsNone(intermediate)
   if scheduler.finished_req_ids=={'c'}:runtime.native_final(final)
   result=Output();outputs.append(result);return result
  worker=types.SimpleNamespace(log_memory_stats=lambda:None,_pp_send_work=[],profiler=None,
   model_runner=types.SimpleNamespace(execute_model=execute,sample_tokens=lambda value:value))
  for rid,count in zip(ids,[2,2,129]):
   for n in [32768]+[1]*(count-1):
    scheduler=types.SimpleNamespace(num_scheduled_tokens={rid:n},total_num_scheduled_tokens=n,finished_req_ids=set())
    result=runtime.execute(env['execute_model'],worker,scheduler);self.assertIs(result,outputs[-1])
    token=object();self.assertIs(runtime.sample(env['sample_tokens'],worker,token),token)
   scheduler=types.SimpleNamespace(num_scheduled_tokens={},total_num_scheduled_tokens=0,finished_req_ids={rid})
   runtime.execute(env['execute_model'],worker,scheduler)
  self.assertEqual(len(published),1)
  with tempfile.TemporaryDirectory()as td:
   q=transport.publish(Path(td)/'COST-r0.json',published[0]);value=json.loads(Path(q['path']).read_bytes())
   manifest=dict(runtime_roles={k:v for k,v in self.refs.items()if k!='writer'},dependencies=[self.refs['writer']])
   result=R.consume(value,rank=0,arm='dense',source_ref={'source':1},recipe_ref={'recipe':1},final_ref=final,ids=ids,manifest=manifest)
  self.assertEqual(result['counts']['request00.decode'],128)
  return R,value,manifest,env,worker
 def test17_actual_native_worker_to_runtime_file_consumer(self):
  R,value,m,env,w=self.chain();self.assertEqual(value['native_execute_calls'],136)
 def test18_actual_chain_count_tamper_rejected(self):
  R,v,m,env,w=self.chain();v['windows']=[r for r in v['windows']if r['phase']!='warmup1.retire']
  with self.assertRaisesRegex(ValueError,'every actual'):
   R.consume(v,rank=0,arm='dense',source_ref={'source':1},recipe_ref={'recipe':1},final_ref={'final':1},ids=['a','b','c'],manifest=m)
 def test19_actual_native_exception_preserved_no_report(self):
  import cost_runtime as R
  env,Output=self.native();error=RuntimeError('native original');published=[]
  def fail(*a):raise error
  worker=types.SimpleNamespace(log_memory_stats=lambda:None,_pp_send_work=[],profiler=None,model_runner=types.SimpleNamespace(execute_model=fail))
  runtime=R.Runtime(self.session(),['a','b','c'],published.append)
  try:runtime.execute(env['execute_model'],worker,types.SimpleNamespace(num_scheduled_tokens={'a':32768},total_num_scheduled_tokens=32768,finished_req_ids=set()))
  except RuntimeError as actual:self.assertIs(actual,error)
  else:self.fail('original swallowed')
  self.assertEqual(published,[]);self.assertIsNone(sys.monitoring.get_tool(4))
 def test20_n1_precheck_uses_actual_build_and_no_candidate(self):
  import cost_runtime as R
  m=dict(runtime_roles={k:v for k,v in self.refs.items()if k!='writer'},dependencies=[self.refs['writer']])
  torch=types.SimpleNamespace(npu=types.SimpleNamespace(synchronize=existing_sync));EVENTS.clear()
  proof=R.precheck(None,m,self.modules,{},torch,rank=0,source_ref={'source':1})
  self.assertEqual(EVENTS,[]);self.assertTrue(proof['python_api_checked'])
  session=R.build(None,m,self.modules,{},torch,rank=0,arm='dense',source_ref={'source':1},recipe_ref={})
  value=session.finish();R.consume_bindings(value,proof,rank=0,source_ref={'source':1})
  proof['actual_code_bindings'][0]['line']+=1
  with self.assertRaisesRegex(ValueError,'same actual N1/worker'):R.consume_bindings(value,proof,rank=0,source_ref={'source':1})
 def test21_no_python_version_fallback(self):
  with patch.object(sys,'version_info',(3,11,9)):
   with self.assertRaises(ValueError):self.session()
 def test22_actual_bootstrap_calls_runtime_on_both_arms(self):
  tree=ast.parse((HERE/'kivi_firstdecode_bootstrap.py').read_bytes())
  methods={n.name:n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name in('execute_model','sample_tokens')}
  self.assertEqual(set(methods),{'execute_model','sample_tokens'})
  calls=[]
  runtime=types.SimpleNamespace(execute=lambda *a:calls.append(('execute',a))or 7,sample=lambda *a,**k:calls.append(('sample',a,k))or 8)
  env={'original_execute':object(),'original_sample':object()}
  exec(compile(ast.Module(body=list(methods.values()),type_ignores=[]),str(HERE/'kivi_firstdecode_bootstrap.py'),'exec'),env)
  worker=types.SimpleNamespace(_kivi_cost=runtime);scheduled=object()
  self.assertEqual(env['execute_model'](worker,scheduled),7)
  self.assertEqual(env['sample_tokens'](worker,scheduled),8)
  self.assertEqual(calls[0][1],(env['original_execute'],worker,scheduled))
 def test23_n1_worker_hash_randomization_stable(self):
  script='import sys;sys.path.insert(0,'+repr(str(HERE))+');import cost_monitor as p;print(p.digest(compile("x in {\\\"alpha\\\",\\\"beta\\\",\\\"gamma\\\",\\\"delta\\\"}","same-source","eval")))'
  results=[]
  for seed in('1','2'):
   env=dict(os.environ,PYTHONHASHSEED=seed)
   p=subprocess.run([sys.executable,'-B','-c',script],env=env,capture_output=True,text=True,timeout=15,check=True)
   results.append(p.stdout.strip())
  self.assertEqual(results[0],results[1]);self.assertEqual(len(results[0]),64)
if __name__=="__main__":unittest.main(verbosity=2)
