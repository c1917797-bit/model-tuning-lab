"""Local fixtures/source-only regressions. No Torch, Docker, remote or actual model claim."""
import ast,copy,hashlib,importlib.util,json,re,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name):
 s=importlib.util.spec_from_file_location("_next_test_"+name,HERE/(name+".py"))
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ns(**kwargs):return types.SimpleNamespace(**kwargs)
def need(v,m):
 if not v:raise ValueError(m)
def scheduler():
 return ns(max_num_batched_tokens=40960,max_num_seqs=16,enable_chunked_prefill=True,
  async_scheduling=False,long_prefill_token_threshold=0,max_num_partial_prefills=1,
  max_long_partial_prefills=1,max_num_scheduled_tokens=40960,scheduler_reserve_full_isl=True)
def config(m):
 return ns(model_config=ns(architecture="Qwen3_5ForConditionalGeneration",hf_config=ns(model_type="qwen3_5"),
  runner_type="generate",is_encoder_decoder=False,is_chunked_prefill_supported=True,max_model_len=33792,enforce_eager=True),
  scheduler_config=scheduler(),parallel_config=ns(tensor_parallel_size=4,pipeline_parallel_size=1,
   data_parallel_size=1,prefill_context_parallel_size=1,decode_context_parallel_size=1,
   worker_cls=m.POLICY["worker_cls"],enable_dbo=False),
  cache_config=ns(enable_prefix_caching=False,mamba_cache_mode="none",kv_cache_memory_bytes=6*1024**3),
  speculative_config=None,kv_transfer_config=None,ec_transfer_config=None,
  compilation_config=ns(cudagraph_mode=ns(name="NONE"),mode=ns(name="NONE")))
class Config(unittest.TestCase):
 def setUp(self):
  self.m=load("native_config_adapter");self.cfg=config(self.m)
  self.args=ns(**self.m.POLICY,max_num_partial_prefills=1,max_long_partial_prefills=1,
   long_prefill_token_threshold=0,scheduler_reserve_full_isl=True)
  self.manifest=dict(runtime_roles={"native_config_adapter":{"path":"exact"}},files=[],dependencies=[])
  self.calls=[];self.proof=ns(PINS={"vllm.engine.arg_utils":"a"*64},actual_sources=lambda:{"original":True})
 def test_policy_accept(self):self.assertTrue(self.m.require_engine_config(self.cfg)["model_verified"])
 def test_no_B1(self):
  self.cfg.scheduler_config.max_num_seqs=1
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_batch32768(self):
  self.cfg.scheduler_config.max_num_batched_tokens=32768
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_native_worker_drift(self):
  self.cfg.parallel_config.worker_cls="other.Worker"
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_FULL(self):
  self.cfg.compilation_config.cudagraph_mode.name="FULL"
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_cache_drift(self):
  self.cfg.cache_config.kv_cache_memory_bytes+=1
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_prefix(self):
  self.cfg.cache_config.enable_prefix_caching=True
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_contextparallel(self):
  self.cfg.parallel_config.prefill_context_parallel_size=2
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_encoder_model(self):
  self.cfg.model_config.is_encoder_decoder=True
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_speculation(self):
  self.cfg.speculative_config=object()
  with self.assertRaises(ValueError):self.m.require_engine_config(self.cfg)
 def test_no_boolean_int_policy(self):
  self.args.max_num_seqs=True
  with self.assertRaises(ValueError):self.m.parsed(self.args,dict(self.m.POLICY))
 def test_CPU_never_model_registry(self):
  class Forbidden:
   def __getattribute__(self,n):raise AssertionError("CPU accessed model/engine "+n)
  def cls(**kw):self.calls.append(kw);s=scheduler();s.max_num_scheduled_tokens=None;return s
  with patch.object(self.m,"proof",return_value=self.proof),patch.object(self.m.importlib,"import_module",return_value=ns(SchedulerConfig=cls)):
   x=self.m.check_mixed_config(api=Forbidden(),args=self.args,stage="cpu",torch=ns(npu=ns(is_initialized=lambda:False)),
    source_manifest=self.manifest,expected_policy=dict(self.m.POLICY))
  self.assertEqual(len(self.calls),1);self.assertFalse(x["model_verified"])
  self.assertFalse(x["actual_model_config_constructed"]);self.assertFalse(x["full_engine_config_built"])
  self.assertFalse(x["CPU_model_registry_called"])
 def test_CPU_initialized_reject(self):
  with patch.object(self.m,"proof",return_value=self.proof):
   with self.assertRaises(ValueError):self.m.check_mixed_config(api=None,args=self.args,stage="cpu",
    torch=ns(npu=ns(is_initialized=lambda:True)),source_manifest=self.manifest,expected_policy=dict(self.m.POLICY))
 def test_N1_full_actual_factory(self):
  cfg=self.cfg;calls=self.calls
  class Engine:
   @classmethod
   def from_cli_args(cls,args):calls.append("args");return cls()
   def create_engine_config(self,**kw):calls.append(kw);return cfg
  with patch.object(self.m,"proof",return_value=self.proof),patch.object(self.m.importlib,"import_module",return_value=ns(UsageContext=ns(OPENAI_API_SERVER="actual-usage"))):
   x=self.m.check_mixed_config(api=ns(AsyncEngineArgs=Engine),args=self.args,stage="n1",torch=None,
    source_manifest=self.manifest,expected_policy=dict(self.m.POLICY))
  self.assertEqual(calls,["args",{"usage_context":"actual-usage"}]);self.assertTrue(x["model_verified"])
 def factory(self):
  cfg=self.cfg;calls=self.calls
  class Engine:
   def create_engine_config(self,*args,**kw):calls.append((args,kw));return cfg
  return Engine
 def install(self,Engine,events):
  return self.m.install_engine_config_gate(api=ns(AsyncEngineArgs=Engine),source_manifest=self.manifest,publish=events.append)
 def test_real_production_gate_same_object_and_restore(self):
  E=self.factory();old=E.create_engine_config;events=[]
  with patch.object(self.m,"proof",return_value=self.proof),patch.object(self.m,"ref",return_value={"sha256":"a"*64}):
   restore=self.install(E,events);answer=E().create_engine_config(7,usage_context="native")
   self.assertIs(answer,self.cfg);self.assertEqual(self.calls,[((7,),{"usage_context":"native"})])
   self.assertEqual(events[0]["stage"],"server");restore();self.assertIs(E.create_engine_config,old)
 def test_production_drift_stops_before_return(self):
  E=self.factory();events=[];self.cfg.scheduler_config.async_scheduling=True
  with patch.object(self.m,"proof",return_value=self.proof),patch.object(self.m,"ref",return_value={"sha256":"a"*64}):
   restore=self.install(E,events)
   with self.assertRaises(ValueError):E().create_engine_config()
   self.assertEqual(events,[]);restore()
 def test_stacked_factory_reject(self):
  with patch.object(self.m,"proof",return_value=self.proof),patch.object(self.m,"ref",return_value={"sha256":"b"*64}):
   with self.assertRaises(ValueError):self.install(self.factory(),[])
 def test_restore_foreign_wrapper_reject(self):
  E=self.factory()
  with patch.object(self.m,"proof",return_value=self.proof),patch.object(self.m,"ref",return_value={"sha256":"a"*64}):
   restore=self.install(E,[]);E.create_engine_config=lambda s:None
   with self.assertRaises(ValueError):restore()
 def test_v008_proof_unchanged(self):
  self.assertEqual(hashlib.sha256((HERE/"native_config_v008.py").read_bytes()).hexdigest(),self.m.PROOF_SHA)
 def valid_record(self,stage):
  p=load("native_config_v008");installed={n:{"sha256":h}for n,h in p.PINS.items()}
  observed=self.m.require_engine_config(self.cfg)if stage=="n1"else dict(
   scheduler=self.m.scheduler_policy(scheduler()),model_verified=False,full_engine_config_verified=False)
  return p,self.m.record(self.manifest,stage,installed,observed,stage=="n1")
 def test_record_CPU_not_model(self):
  p,x=self.valid_record("cpu")
  with patch.object(self.m,"proof",return_value=p):self.assertFalse(self.m.validate_record(x,self.manifest,"cpu")["model_verified"])
 def test_CPU_promoted_flag_rejected(self):
  p,x=self.valid_record("cpu");x["model_verified"]=True
  with patch.object(self.m,"proof",return_value=p):
   with self.assertRaises(ValueError):self.m.validate_record(x,self.manifest,"cpu")
 def test_record_observed_B1_rejected(self):
  p,x=self.valid_record("n1");x["observed"]["scheduler"]["max_num_seqs"]=1
  with patch.object(self.m,"proof",return_value=p):
   with self.assertRaises(ValueError):self.m.validate_record(x,self.manifest,"n1")
 def test_record_official_source_drift_rejected(self):
  p,x=self.valid_record("n1");x["actual_installed_sources"]["vllm.config.scheduler"]["sha256"]="f"*64
  with patch.object(self.m,"proof",return_value=p):
   with self.assertRaises(ValueError):self.m.validate_record(x,self.manifest,"n1")
class Terminal(unittest.TestCase):
 def setUp(self):
  self.m=load("consume_whole_cpu");self.core=load("release_core")
 def envelope(self):
  rr={"path":str(HERE/"fixture-result.json"),"bytes":1,"sha256":"a"*64}
  result=dict(status="actual",elapsed_seconds=1)
  rec=dict(id="exec-0123456789abcdef",state="completed",exitCode=0,cancelled=False,timedOut=False,error=None,
   stdout=json.dumps(dict(result=rr,status="actual"))+"\n",stderr="",command="/usr/bin/python3",
   args=["-I","source.py"],cwd=self.core.ROOT,durationMs=1000)
  raw=dict(operationId=rec["id"],operation=dict(targetPeerId="peer",routeDecision="peer_direct",result=dict(record=rec)))
  return rr,result,rec,raw
 def test_actual_terminal_binding(self):
  rr,result,rec,raw=self.envelope()
  with patch.object(self.core,"obj",side_effect=[result,raw]):
   self.assertEqual(self.m.terminal(self.core,rr,{},"peer",rec["id"],rec["command"],rec["args"],5400)[0],result)
 def test_wrong_peer(self):
  _,_,rec,raw=self.envelope()
  with self.assertRaises(ValueError):self.core.original(raw,"other",rec["id"])
 def test_failed_original(self):
  _,_,rec,raw=self.envelope();rec["exitCode"]=1
  with self.assertRaises(ValueError):self.core.original(raw,"peer",rec["id"])
 def test_truncated_original(self):
  _,_,rec,raw=self.envelope();rec["stdoutTruncated"]=True
  with self.assertRaises(ValueError):self.core.original(raw,"peer",rec["id"])
 def test_changed_literal_command(self):
  _,_,rec,_=self.envelope()
  with self.assertRaises(ValueError):self.core.exact_command(rec,"/bin/sh",rec["args"],5400)
 def test_duplicate_result_marker(self):
  rr,result,rec,raw=self.envelope();rec["stdout"]*=2
  with patch.object(self.core,"obj",side_effect=[result,raw]):
   with self.assertRaises(ValueError):self.m.terminal(self.core,rr,{},"peer",rec["id"],rec["command"],rec["args"],5400)
 def test_wall_budget_not_extended(self):
  _,_,rec,_=self.envelope();rec["durationMs"]=43200001
  with self.assertRaises(ValueError):self.core.exact_command(rec,rec["command"],rec["args"],43200)
 def test_release_nanosecond_order(self):
  a={"State":{"FinishedAt":"2026-10-10T12:00:00.000000002Z"}}
  b={"State":{"StartedAt":"2026-10-10T12:00:00.000000001Z"}}
  with self.assertRaises(ValueError):self.core.raw_after_release(a,b)
class CPUCleanup(unittest.TestCase):
 def setUp(self):
  self.m=load("consume_whole_cpu");self.core=load("release_core");self.docs={};self.count=0
  self.source={"path":"source","bytes":1,"sha256":"a"*64}
  ownsource={"path":str(HERE/"safety_host.py"),"bytes":1,"sha256":"b"*64}
  self.ctx=self.core.Context.__new__(self.core.Context);self.ctx.producer=self.source
  self.ctx.m={"files":[ownsource]};self.ctx.own={"safety_host.py":ownsource}
  self.core.obj=lambda r:self.docs[r["id"]];self.ctx.core=self.core
  cfg=ns(require=need,GIB=1024**3,ROOT=Path("/source"),IMAGE="sha256:"+"c"*64)
  names={"device_map","environment","labels","create_argv","validate_inspect"}
  nodes=[n for n in ast.parse((HERE/"safety_host.py").read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name in names]
  namespace=dict(c=cfg,re=re,DOCKER="/usr/bin/docker",MEM=64*1024**3,PHYSICAL=(4,5,6,7),OWNER="fixture")
  exec(compile(ast.Module(body=nodes,type_ignores=[]),"actual-extracted-safety","exec"),namespace)
  self.ctx.s=namespace
  self.owned=dict(cid="d"*64,name="fixture",arm="cpu-preflight",source=self.source,
   host_sha256="b"*64,sources={"safety_host.py":"b"*64},guest_cpus=[1],mounts={},image=cfg.IMAGE)
  self.owned["create_receipt"]=self.put(dict(exit_code=0,stdout=self.owned["cid"],requested_argv=namespace["create_argv"](self.owned)))
  x=dict(Id=self.owned["cid"],Image=cfg.IMAGE,Name="/fixture",Mounts=[],ExecIDs=[],
   Config=dict(Image=cfg.IMAGE,Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],WorkingDir=str(cfg.ROOT),
    Labels=namespace["labels"](self.owned),Env=[k+"="+v for k,v in namespace["environment"](True).items()]),
   HostConfig=dict(Privileged=False,Memory=8*1024**3,MemorySwap=8*1024**3,NanoCpus=10**9,CpusetCpus="1",
    IpcMode="private",NetworkMode="none",ShmSize=4*1024**3,PidsLimit=2048,CapDrop=["ALL"],
    SecurityOpt=["no-new-privileges"],Devices=[]),
   State=dict(Running=False,Pid=0,OOMKilled=False))
  self.before=copy.deepcopy(x);self.after=copy.deepcopy(x)
  self.stop=dict(exit_code=0,requested_argv=["/usr/bin/docker","stop","--time","15",self.owned["cid"]],
   cleanup_safety_only=True,original_admission_failures=[],
   cleanup_resource_snapshot=dict(aggregate_peak_rss_kib=2,host_peak_rss_kib=1,child_peak_rss_kib=1,formal_limit_bytes=512*1024**2))
 def put(self,x):
  self.count+=1;self.docs[self.count]=x;return {"id":self.count}
 def execute(self):
  def ir(x):return self.put(dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",self.owned["cid"]],stdout=json.dumps([x])))
  r=self.put(dict(schema="kivi.actual-devices-empty-cleanup/v1",container=self.owned["cid"],stopped=True,
   retained=True,deleted=False,primary_error=None,errors=[],npu_release_claim=False,
   before_inspect=ir(self.before),after_inspect=ir(self.after),stop_receipt=self.put(self.stop)))
  return self.m.cleanup_cpu(self.ctx,r,self.owned)
 def test_exact_CPU_stop_consumed(self):self.assertEqual(self.execute()["Id"],self.owned["cid"])
 def test_unrelated_new_NPU_job_not_queried(self):
  self.docs["foreign"]=dict(cid="e"*64,devices=[4,5,6,7],running=True)
  self.ctx.h=ns(idle_one=lambda *a:(_ for _ in()).throw(AssertionError("must not ask NPU idle")))
  self.assertEqual(self.execute()["Id"],self.owned["cid"])
 def test_foreign_stop_reject(self):
  self.stop["requested_argv"][-1]="e"*64
  with self.assertRaises(ValueError):self.execute()
 def test_devices_reject(self):
  self.after["HostConfig"]["Devices"]=[dict(PathOnHost="/dev/davinci4",PathInContainer="/dev/davinci0",CgroupPermissions="rwm")]
  with self.assertRaises(ValueError):self.execute()
 def test_oom_reject(self):
  self.after["State"]["OOMKilled"]=True
  with self.assertRaises(ValueError):self.execute()
 def test_live_reject(self):
  self.after["State"].update(Running=True,Pid=99)
  with self.assertRaises(ValueError):self.execute()
 def test_exec_ids_reject(self):
  self.after["ExecIDs"]=["other"]
  with self.assertRaises(ValueError):self.execute()
 def test_image_drift_reject(self):
  self.after["Image"]="other"
  with self.assertRaises(ValueError):self.execute()
 def test_CPU_memory_drift_reject(self):
  self.after["HostConfig"]["Memory"]=64*1024**3
  with self.assertRaises(ValueError):self.execute()
 def test_source_drift_reject(self):
  self.owned["sources"]["safety_host.py"]="f"*64
  with self.assertRaises(ValueError):self.execute()
 def test_cleanup_failure_retained(self):
  self.stop["original_admission_failures"]=["cutoff"]
  with self.assertRaises(ValueError):self.execute()
 def test_cleanup_memory_fail(self):
  self.stop["cleanup_resource_snapshot"]["aggregate_peak_rss_kib"]=999999
  with self.assertRaises(ValueError):self.execute()
class Source(unittest.TestCase):
 def test_production_guard_surrounds_existing_server(self):
  t=(HERE/"server_entry.py").read_text()
  self.assertLess(t.index("install_engine_config_gate"),t.index("api.uvloop.run"))
  self.assertGreater(t.index("restore_config()"),t.index("api.uvloop.run"))
 def test_CPU_whole_no_live_NPU(self):
  m=load("consume_whole_cpu")
  import inspect
  t=inspect.getsource(m.cleanup_cpu)+inspect.getsource(m.cpu_observations)
  self.assertNotIn(".idle_one(",t);self.assertNotIn(".call(",t)
 def test_raw_core_unchanged(self):
  self.assertEqual(hashlib.sha256((HERE/"release_core.py").read_bytes()).hexdigest(),load("consume_whole_cpu").CORE_SHA)
 def test_matrix_replayed_not_scope_flag(self):
  t=(HERE/"consume_whole_cpu.py").read_text();self.assertIn('mods["matrix_consumer"].consume',t)
  self.assertIn('need(replay==output["matrix"]',t);self.assertNotIn("fast_oracle.consume",t)
 def test_actual_CPU_memory_and_recipe_explicit(self):
  t=(HERE/"cpu_phase.py").read_text()
  self.assertIn("offline_recipe=recipe_ref",t);self.assertIn('actual_memory_after=c.ref',t)
 def test_assembler_owns_adapter_and_consumer(self):
  t=(HERE/"assemble.py").read_text();self.assertIn('"native_config_adapter":"native_config_adapter.py"',t)
  self.assertIn('"whole_cpu_consumer":"consume_whole_cpu.py"',t)
 def test_CPU_no_registry_call(self):
  t=ast.parse((HERE/"native_config_adapter.py").read_bytes())
  fn=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=="check_mixed_config")
  branch=next(n for n in fn.body if isinstance(n,ast.If))
  text=ast.dump(ast.Module(body=branch.body,type_ignores=[]))
  self.assertNotIn("create_model_config",text);self.assertNotIn("from_cli_args",text)
 def test_compile_sources(self):
  for p in HERE.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
if __name__=="__main__":unittest.main(verbosity=2)
