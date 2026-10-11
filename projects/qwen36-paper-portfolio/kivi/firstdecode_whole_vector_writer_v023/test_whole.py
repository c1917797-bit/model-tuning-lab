"""Strict synthetic evidence regressions; never historical NPU/model authority."""
import copy, hashlib, json, re, tempfile, types, unittest
from pathlib import Path
PRODUCER_ARCHIVE=None
REVIEWED_DEPS=None
CORE=None
class Evidence(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.n=0
  self.cid="a"*64;self.source=dict(path=CORE.PRODUCER_ROOT+"/SOURCE_MANIFEST.json",bytes=CORE.PRODUCER_BYTES,sha256=CORE.PRODUCER_SHA)
 def tearDown(self):self.tmp.cleanup()
 def artifact(self,x):
  self.n+=1;p=self.root/("%d.json"%self.n);p.write_text(json.dumps(x),encoding="utf-8");return CORE.ref(p)
 def terminal(self):
  return dict(operationId="exec-0000000000000001",operation=dict(targetPeerId="peer",routeDecision="peer_direct",
   result=dict(record=dict(id="exec-0000000000000001",state="completed",exitCode=0,cancelled=False,timedOut=False,error=None,
    command="/usr/bin/python3",args=["-I","-B","actual.py"],cwd=CORE.ROOT,durationMs=1000,stdout="",stderr=""))))
 def original(self,x):return CORE.original(x,"peer","exec-0000000000000001")
 def extract_safety(self):
  p=PRODUCER_ARCHIVE/"safety_host.py"
  mf=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes());r=next(r for r in mf["files"]if Path(r["path"]).name==p.name)
  class C:
   GIB=1024**3;IMAGE=CORE.IMAGE;ROOT=Path(CORE.ROOT);HBM_RESERVE_MIB=3072
   require=staticmethod(CORE.need)
  return CORE.extract(p,r["sha256"],("device_map","environment","labels","create_argv","validate_inspect","cpu_admission","actual_hbm"),
   dict(c=C,re=re,Path=Path,PHYSICAL=(4,5,6,7),MEM=64*CORE.GIB,OWNER="kivi-firstdecode-eager-diagnostic-v1",DOCKER="/usr/bin/docker"))
 def owned(self,arm="candidate"):
  return dict(cid=self.cid,name="fixture",image=CORE.IMAGE,arm=arm,source=self.source,host_sha256="b"*64,
   guest_cpus=[1]if arm=="cpu-preflight"else[1,2,3,4],mounts={"/adakv-results":["/fixture",True]})
 def inspect(self,owned):
  s=self.extract_safety();cpu=owned["arm"]=="cpu-preflight";mem=(8 if cpu else 64)*CORE.GIB
  return dict(Id=self.cid,Image=CORE.IMAGE,Name="/fixture",Config=dict(Image=CORE.IMAGE,Entrypoint=["/bin/bash"],
   Cmd=["-c","exec /bin/sleep infinity"],WorkingDir=str(Path(CORE.ROOT)),Labels=s["labels"](owned),
   Env=[k+"="+v for k,v in s["environment"](cpu).items()]),HostConfig=dict(Privileged=False,Memory=mem,MemorySwap=mem,
   NanoCpus=(1 if cpu else 4)*10**9,CpusetCpus=",".join(map(str,owned["guest_cpus"])),IpcMode="private",
   NetworkMode="none",ShmSize=4*CORE.GIB,PidsLimit=2048,DeviceRequests=[],DeviceCgroupRules=[],CapDrop=["ALL"],
   SecurityOpt=["no-new-privileges"],Devices=[dict(PathOnHost=k,PathInContainer=v,CgroupPermissions="rwm")
    for k,v in({}if cpu else s["device_map"]()).items()]),
   Mounts=[dict(Type="bind",Destination="/adakv-results",Source="/fixture",RW=True)],
   State=dict(Running=False,Pid=0,OOMKilled=False),ExecIDs=None)
 def test_original_success_and_envelope(self):
  x=self.terminal();r=self.original(x);self.assertEqual(r["exitCode"],0)
  self.assertEqual(self.original(dict(structuredContent=x,content=[dict(type="text",text=json.dumps(x))])),r)
 def test_original_failed_parent_not_promoted(self):
  x=self.terminal();x["operation"]["result"]["record"]["exitCode"]=1
  with self.assertRaisesRegex(ValueError,"actual success"):self.original(x)
 def test_original_missing_handle_not_terminal(self):
  x=self.terminal();del x["operation"]["result"]["record"]
  with self.assertRaises(ValueError):self.original(x)
 def test_original_timeout_and_wrong_peer(self):
  x=self.terminal();x["operation"]["result"]["record"]["timedOut"]=True
  with self.assertRaises(ValueError):self.original(x)
  x=self.terminal();x["operation"]["targetPeerId"]="foreign"
  with self.assertRaises(ValueError):self.original(x)
 def test_original_truncated_and_text_disagreement(self):
  x=self.terminal();x["truncated"]=True
  with self.assertRaisesRegex(ValueError,"untruncated"):self.original(x)
  x=self.terminal()
  with self.assertRaisesRegex(ValueError,"disagreement"):self.original(dict(structuredContent=x,content=[dict(type="text",text="{}")]))
 def test_exact_command_and_budget(self):
  r=self.original(self.terminal());CORE.exact_command(r,"/usr/bin/python3",r["args"],5400)
  with self.assertRaises(ValueError):CORE.exact_command(r,"/usr/bin/python3",["different"],5400)
  r["durationMs"]=5400001
  with self.assertRaises(ValueError):CORE.exact_command(r,"/usr/bin/python3",r["args"],5400)
 def test_ref_two_three_exact_and_bool_rejected(self):
  r=self.artifact({"x":1});self.assertEqual(CORE.obj(r),{"x":1})
  self.assertEqual(CORE.obj({k:r[k]for k in("path","sha256")}),{"x":1})
  r["bytes"]=True
  with self.assertRaises(ValueError):CORE.obj(r)
 def test_ref_wrong_sha_and_duplicate_json(self):
  r=self.artifact({"x":1});r["sha256"]="f"*64
  with self.assertRaises(ValueError):CORE.obj(r)
  with self.assertRaisesRegex(ValueError,"duplicate"):CORE.decode('{"x":1,"x":2}')
 def test_ref_nonfinite_rejected(self):
  with self.assertRaisesRegex(ValueError,"nonfinite"):CORE.decode('{"x":NaN}')
 def child(self,code):
  return dict(requested_argv=["actual"],actual_host_argv=["/usr/bin/prlimit","--as=unlimited","--","actual"],
   pid=10,termination_observed=True,exit_code=code,stdout_ref=self.artifact({"stdout":""}),stderr_ref=self.artifact({"stderr":""}))
 def test_normal_owned_server_stop_nonzero_accepted(self):
  for code in(0,137,143,-15):CORE.child(self.child(code),["actual"],success=False)
 def test_computation_child_nonzero_rejected(self):
  with self.assertRaisesRegex(ValueError,"computational"):CORE.child(self.child(143),["actual"],success=True)
 def test_server_not_reaped_rejected(self):
  x=self.child(143);x["termination_observed"]=False
  with self.assertRaisesRegex(ValueError,"completed"):CORE.child(x,["actual"],success=False)
 def test_original_inspect_cpu_device_free_and_candidate(self):
  for arm in("cpu-preflight","candidate"):
   o=self.owned(arm);self.extract_safety()["validate_inspect"](self.inspect(o),o)
 def test_original_inspect_protected_device_and_memory_negative(self):
  o=self.owned();x=self.inspect(o);x["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
  with self.assertRaisesRegex(ValueError,"protected"):self.extract_safety()["validate_inspect"](x,o)
  x=self.inspect(o);x["HostConfig"]["Memory"]+=1
  with self.assertRaisesRegex(ValueError,"resources"):self.extract_safety()["validate_inspect"](x,o)
 def test_original_inspect_source_and_mount_negative(self):
  o=self.owned();x=self.inspect(o);x["Config"]["Labels"]["model-tuning-lab.source-manifest-sha256"]="f"*64
  with self.assertRaisesRegex(ValueError,"labels"):self.extract_safety()["validate_inspect"](x,o)
  x=self.inspect(o);x["Mounts"][0]["RW"]=False
  with self.assertRaisesRegex(ValueError,"mounts"):self.extract_safety()["validate_inspect"](x,o)
 def test_original_inspect_workdir_and_foreign_CID_negative(self):
  o=self.owned();x=self.inspect(o);x["Config"]["WorkingDir"]="/wrong"
  with self.assertRaisesRegex(ValueError,"labels"):self.extract_safety()["validate_inspect"](x,o)
  x=self.inspect(o);x["Id"]="c"*64
  with self.assertRaisesRegex(ValueError,"owned CID"):self.extract_safety()["validate_inspect"](x,o)
 def test_original_cpu_ancestor_quota_negative(self):
  s=self.extract_safety();h=dict(effective_capacity=7,effective_cpus=list(range(7)),quota_ancestors=[dict(key="root",capacity=7)])
  d=copy.deepcopy(h);self.assertEqual(s["cpu_admission"](h,d)["guest_cpus"],[1,2,3,4])
  d["quota_ancestors"][0]["capacity"]=6
  with self.assertRaisesRegex(ValueError,"summed7"):s["cpu_admission"](h,d)
 def test_original_hbm_memory_first_ratio_is_not_HBM(self):
  text="| Chip | Bus-Id | AICore(%) Memory-Usage(MB) HBM-Usage(MB) |\n| 4 910B4 | OK | unused |\n| 0 | 0000:01:00.0 | 0 0 / 0 29696 / 32768 |"
  self.assertEqual(self.extract_safety()["actual_hbm"](text,4)["used_mib"],29696)
  with self.assertRaisesRegex(ValueError,"reserve3"):self.extract_safety()["actual_hbm"](text.replace("29696","29697"),4)
 def stat(self,pid,ticks):
  return str(pid)+" (worker) "+" ".join(["S"]+["0"]*18+[str(ticks)]+["0"]*3)
 def namespace(self):
  identities=[dict(pid=i+10,start_ticks=i+100,cgroup="7:memory:/docker/"+self.cid)for i in range(5)]
  refs=[self.artifact(dict(schema="kivi.actual-rank-owner-request/v1",rank=i,identity=identities[i+1],
   container_id=self.cid,source_ref=self.source,run_id="run",physical_card=i+4,mapping_is_not_yet_verified=True,run_authority=False))for i in range(4)]
  front=self.artifact(identities[0]);owner=self.artifact({"owner":"fixture"})
  rows=[]
  for i,ident in enumerate(identities):
   hp=i+1000;st=self.stat(hp,ident["start_ticks"])
   argv=["real-worker"];digest=hashlib.sha256(b"real-worker\0").hexdigest()
   rows.append(dict(guest_identity=ident,host_pid=hp,nspid=[hp,ident["pid"]],stat_before=st,stat_after=st,
    cgroup=ident["cgroup"],cmdline_sha256=digest,physical_cards=[]if i==0 else[i+3],
    process_proof=dict(pid=hp,start_ticks=ident["start_ticks"],cgroup=ident["cgroup"],argv=argv,namespace_pids=[hp,ident["pid"]],cmdline_sha256=digest)))
  x=dict(schema="kivi.actual-firstdecode-namespace-raw/v1",container_id=self.cid,external_owner_authority_ref=owner,
   original_consumer_required=True,run_authority=False,host_processes=rows,request_refs=refs,frontend_ref=front,owned_inspect={})
  recipe=dict(external_owner_authority_ref=owner,source_ref=self.source,run_id="run")
  proofs=[dict(pid=r["host_pid"],start_ticks=r["guest_identity"]["start_ticks"],cgroup=r["cgroup"],physical=i+3,chip=0)
   for i,r in enumerate(rows)if i]
  return x,recipe,proofs
 def ns_call(self,x,recipe,proofs):return CORE.namespace(x,recipe,self.owned(),lambda r,o:None,proofs,5000)
 def test_namespace_all4_actual_raw_stat(self):
  x,r,p=self.namespace();ids=self.ns_call(x,r,p);self.assertEqual(len(ids),4)
 def test_namespace_pid_reuse_and_canary_card_negative(self):
  x,r,p=self.namespace();x["host_processes"][1]["stat_after"]=self.stat(1001,999)
  with self.assertRaisesRegex(ValueError,"stable namespace"):self.ns_call(x,r,p)
  x,r,p=self.namespace();p[0]["physical"]=7
  with self.assertRaisesRegex(ValueError,"borrowed canary"):self.ns_call(x,r,p)
 def test_raw_consumer_scope_not_full_model(self):
  roles={k:{"path":"/"+k,"sha256":"f"*64}for k in("fast_oracle","fast_consume","writer_reader")}
  client=dict(rank_bundle_refs=[{}]*4);frame=self.artifact({"raw_fixture":True})
  x=dict(schema="kivi.actual-firstdecode-independent/v1",status="FIRSTDECODE_RAW_COMPONENTS_CONSUMED",source=self.source,
   client_ref={},rank_bundle_refs=client["rank_bundle_refs"],actual_ranks=4,actual_FA_layers_per_rank=16,
   frames=[dict(rank=r,layer="L%d"%l,frame_ref=frame)for r in range(4)for l in range(16)],
   original_prefill_tokens=32768,actual_first_decode_length=32769)
  for k in("full1536_attention_outputs_per_FA_checked","source_bound_original_writer_checked","native_and_compact_disjoint_spans_checked","no_candidate_math_import"):x[k]=True
  for k in("untouched_GDN_content_checked","model_ready","performance_ready","run_authority","graph_checked","allocation_replaced","whole_176"):x[k]=False
  for k,role in(("independent_oracle_source","fast_oracle"),("independent_reader_source","fast_consume"),("writer_reader_source","writer_reader")):x[k]=roles[role]
  x.update(writer_reader_source=CORE.VECTOR_REFERENCES["writer"],original_writer_reader_source=roles["writer_reader"],
   independent_vector_source=CORE.VECTOR_REFERENCES["vector"],aggregate_reference_source=CORE.VECTOR_REFERENCES["aggregate"])
  CORE.raw_result(x,self.source,{},client,dict(runtime_roles=roles))
  x["model_ready"]=True
  with self.assertRaisesRegex(ValueError,"not promoted"):CORE.raw_result(x,self.source,{},client,dict(runtime_roles=roles))

 def cleanup_fixture(self):
  ctx=CORE.Context.__new__(CORE.Context);ctx.s=self.extract_safety()
  actualmf=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes());ctx.m=actualmf
  ctx.own={Path(r["path"]).name:r for r in actualmf["files"]}
  ctx.boundary=CORE.extract(REVIEWED_DEPS/"protected_lifecycle.py",
   "4bbd492809c9ba1922fd3885b101f8cc6fe187884703c21e4a2d44acd1444b75",
   ("protected_boundary",),dict(re=re,require=CORE.need))["protected_boundary"]
  old=CORE.extract(REVIEWED_DEPS/"saved_step_host_run.py",
   "86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc",
   ("process_rows",),{})
  funcs=CORE.extract(REVIEWED_DEPS/"full_matrix_host.py",
   "ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
   ("idle_one",),dict(require=CORE.need,re=re,legacy=lambda:types.SimpleNamespace(**old)))
  ctx.h=types.SimpleNamespace(**funcs)
  o=self.owned();o["host_sha256"]=ctx.own["safety_host.py"]["sha256"]
  o["sources"]={Path(r["path"]).name:r["sha256"]for r in actualmf["files"]}
  o["create_receipt"]=self.artifact(dict(exit_code=0,stdout=self.cid+"\n",requested_argv=ctx.s["create_argv"](o)))
  ins=self.inspect(o)
  before=self.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",self.cid],stdout=json.dumps([ins])))
  after=self.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",self.cid],stdout=json.dumps([ins])))
  stop=self.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","stop","--time","15",self.cid],
   cleanup_safety_only=True,original_admission_failures=[]))
  smi="\n".join("| %d 910B4 | OK | unused |\n| 0 | 0000:01:00.0 | 0 0 / 0 2867 / 32768 |\nNo running processes found in NPU %d"%(i,i)for i in(4,5,6,7))
  release=self.artifact(dict(exit_code=0,requested_argv=["/usr/local/sbin/npu-smi","info"],stdout=smi))
  x=dict(container=self.cid,stopped=True,retained=True,deleted=False,errors=[],primary_error=None,
   before_inspect=before,after_inspect=after,stop_receipt=stop,release_smi=release,
   protected_boundary=ctx.boundary([],[],[self.cid],[5000]))
  return ctx,o,x
 def test_actual_cleanup_complete_original_validator(self):
  ctx,o,x=self.cleanup_fixture();after=ctx.cleanup(self.artifact(x),o,5000);self.assertEqual(after["State"]["Pid"],0)
 def test_cleanup_foreign_stop_rejected(self):
  ctx,o,x=self.cleanup_fixture();v=CORE.obj(x["stop_receipt"]);v["requested_argv"][-1]="f"*64;x["stop_receipt"]=self.artifact(v)
  with self.assertRaisesRegex(ValueError,"exact own stop"):ctx.cleanup(self.artifact(x),o,5000)
 def test_cleanup_live_or_OOM_rejected(self):
  for key,value in(("Pid",123),("OOMKilled",True)):
   ctx,o,x=self.cleanup_fixture();v=CORE.obj(x["after_inspect"]);ins=json.loads(v["stdout"]);ins[0]["State"][key]=value
   v["stdout"]=json.dumps(ins);x["after_inspect"]=self.artifact(v)
   with self.assertRaises(ValueError):ctx.cleanup(self.artifact(x),o,5000)
 def test_cleanup_original_primary_not_erased(self):
  ctx,o,x=self.cleanup_fixture();x["primary_error"]="ValueError('first original fault')"
  with self.assertRaisesRegex(ValueError,"primary"):ctx.cleanup(self.artifact(x),o,5000)
 def test_protected_churn_accepted_but_own0_rejected(self):
  ctx,o,x=self.cleanup_fixture()
  row=dict(physical=0,chip=0,pid=9999,start_ticks=90,cgroup="/external",cmdline_sha256="f"*64)
  pb=ctx.boundary([], [row], [self.cid], [5000]);self.assertEqual(pb["external_added"],[row])
  row["cgroup"]="/docker/"+self.cid
  with self.assertRaisesRegex(ValueError,"owned process"):ctx.boundary([], [row], [self.cid], [5000])
 def test_cleanup_source_drift_rejected(self):
  ctx,o,x=self.cleanup_fixture();o["sources"]["client.py"]="f"*64
  with self.assertRaisesRegex(ValueError,"complete source"):ctx.cleanup(self.artifact(x),o,5000)
 def test_raw_CPU8_requires_exact_TP4_release_first(self):
  npu=dict(State=dict(FinishedAt="2026-10-10T12:00:00.123456789Z"))
  raw=dict(State=dict(StartedAt="2026-10-10T12:00:01Z"))
  CORE.raw_after_release(npu,raw)
  for value in("2026-10-10T11:59:59Z","0001-01-01T00:00:00Z","2026-10-10T12:00:01"):
   raw["State"]["StartedAt"]=value
   with self.assertRaises(ValueError):CORE.raw_after_release(npu,raw)
 def test_actual_empty_child_streams_allowed_not_empty_JSON(self):
  p=self.root/"empty.stdout";p.write_bytes(b"");r=CORE.ref(p)
  x=self.child(0);x["stdout_ref"]=r;x["stderr_ref"]=r
  CORE.child(x,["actual"])
  with self.assertRaisesRegex(ValueError,"bounded complete artifact"):CORE.obj(r)
 def test_RFC3339Nano_exact_boundary_and_invalid_forms(self):
  npu=dict(State=dict(FinishedAt="2026-10-10T12:00:00.123456789Z"))
  raw=dict(State=dict(StartedAt="2026-10-10T12:00:00.123456789+00:00"))
  CORE.raw_after_release(npu,raw)
  raw["State"]["StartedAt"]="2026-10-10T12:00:00.123456788Z"
  with self.assertRaisesRegex(ValueError,"after exact TP4"):CORE.raw_after_release(npu,raw)
  for value in("2026-10-10T12:00:00.1234567890Z","2026-10-10T12:00:00+03:00","2026-10-10T12:00:00","2026-02-30T12:00:00Z"):
   with self.assertRaises(ValueError):CORE.utc(value)

 def cann_fixture(self,imported=False):
  m=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes());x=m["cann_python_binding"]
  row=next(r for r in m["files"]if Path(r["path"]).name=="cann_python.py")
  # Evaluate actual producer's final return expression; no hand-copied schema,
  # no ACL binary executed and no Torch/device imports in this regression.
  import ast,importlib.machinery
  code=(PRODUCER_ARCHIVE/"cann_python.py").read_bytes()
  self.assertEqual(hashlib.sha256(code).hexdigest(),row["sha256"])
  funcs=CORE.extract(PRODUCER_ARCHIVE/"cann_python.py",row["sha256"],("spec_identity",),
   dict(need=CORE.need,ACL=x["acl_file"],ACL_BYTES=x["acl_bytes"],ACL_SHA=x["acl_sha256"],
    importlib=types.SimpleNamespace(machinery=importlib.machinery),
    file_identity=lambda p,n,h:dict(path=p,size_bytes=n,sha256=h)))
  loader=importlib.machinery.ExtensionFileLoader("acl",x["acl_file"])
  # Windows normalizes the Linux path in the host fixture. The actual Linux
  # ExtensionFileLoader uses this exact source-bound path; no binary executes.
  loader.path=x["acl_file"]
  spec=importlib.machinery.ModuleSpec("acl",loader,origin=x["acl_file"])
  resolution=funcs["spec_identity"](spec)
  before=["/fixture/python"]
  node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef)and n.name=="install")
  returned=next(n for n in reversed(node.body)if isinstance(n,ast.Return))
  expr=ast.Expression(body=returned.value);ast.fix_missing_locations(expr)
  namespace=dict(IMAGE=m["cann_python_binding"]["image"],ROOT=x["pythonpath_root"],
   source=self.source,env=dict(path=x["set_env_file"],size_bytes=x["set_env_bytes"],sha256=x["set_env_sha256"]),
   selected=resolution,active=resolution,before=before,cached_before=dict(imported=False,memcpy_observed=False),
   sys=types.SimpleNamespace(path=[x["pythonpath_root"],*before],flags=types.SimpleNamespace(isolated=1)))
  binding=eval(compile(expr,str(PRODUCER_ARCHIVE/"cann_python.py"),"eval"),namespace)
  cached=dict(imported=False,memcpy_observed=False)
  if imported:
   fake=types.ModuleType("acl");fake.__file__=x["acl_file"];fake.__spec__=spec
   fake.rt=types.SimpleNamespace(memcpy=lambda:None)
   fn=CORE.extract(PRODUCER_ARCHIVE/"cann_python.py",row["sha256"],("cached",),
    dict(need=CORE.need,types=types,ACL=x["acl_file"],sys=types.SimpleNamespace(modules={"acl":fake}),
     spec_identity=funcs["spec_identity"]))["cached"]
   cached=fn(required=True,memcpy_required=True)
  return m,binding,cached
 def test_actual_CANN_CPU_return_expression_resolution_only(self):
  m,b,c=self.cann_fixture();CORE.cann_record(b,c,m,self.source,False)
  self.assertFalse(b["acl_import_executed_by_helper"])
 def test_actual_CANN_N1_cached_native_origin_memcpy(self):
  m,b,c=self.cann_fixture(True);CORE.cann_record(b,c,m,self.source,True)
 def test_CANN_N1_missing_import_or_memcpy_rejected(self):
  m,b,c=self.cann_fixture()
  with self.assertRaisesRegex(ValueError,"import/memcpy required"):CORE.cann_record(b,c,m,self.source,True)
  m,b,c=self.cann_fixture(True);c["memcpy_observed"]=False
  with self.assertRaisesRegex(ValueError,"memcpy callable"):CORE.cann_record(b,c,m,self.source,True)
 def test_CANN_wrong_root_binary_or_loader_rejected(self):
  m,b,c=self.cann_fixture(True)
  for key,value in(("origin","/foreign/acl.so"),("loader_type","python.SourceFileLoader")):
   changed=copy.deepcopy(b);changed["effective_resolution"][key]=value
   with self.assertRaises(ValueError):CORE.cann_record(changed,c,m,self.source,True)
  changed=copy.deepcopy(b);changed["set_env"]["sha256"]="f"*64
  with self.assertRaises(ValueError):CORE.cann_record(changed,c,m,self.source,True)
 def test_CANN_wrong_source_path_assimilation_or_permission_rejected(self):
  m,b,c=self.cann_fixture(True)
  for key,value in(("source_ref",{}),("sys_path_after",b["sys_path_after"]+["/foreign"]),("model_ready",True)):
   changed=copy.deepcopy(b);changed[key]=value
   with self.assertRaises(ValueError):CORE.cann_record(changed,c,m,self.source,True)
 def worker_CANN_fixture(self):
  m,b,c=self.cann_fixture(True);ids=[dict(pid=20+i,start_ticks=100+i,cgroup="7:memory:/docker/"+self.cid)for i in range(4)]
  recipe=dict(diagnostic_root=str(self.root));rr=self.artifact(recipe)
  for ident in ids:
   p=self.root/("CANN-WORKER-p%d.json"%ident["pid"])
   p.write_text(json.dumps(dict(source_ref=self.source,recipe_ref=rr,identity=ident,binding=b,
    cached_after_native_import=c,model_ready=False,performance_ready=False)),encoding="utf-8")
  return m,ids,recipe,rr
 def test_CANN_worker_actual_all4_pid_start_source_raw(self):
  m,ids,recipe,rr=self.worker_CANN_fixture()
  self.assertEqual(len(CORE.worker_cann(m,self.source,recipe,rr,ids)),4)
 def test_CANN_worker_wrong_pid_start_source_reject(self):
  for field,value in(("start_ticks",999),("cgroup","/external")):
   m,ids,recipe,rr=self.worker_CANN_fixture()
   p=self.root/"CANN-WORKER-p20.json";x=json.loads(p.read_bytes());x["identity"][field]=value
   p.write_text(json.dumps(x),encoding="utf-8")
   with self.assertRaisesRegex(ValueError,"PID/start/CID/source"):CORE.worker_cann(m,self.source,recipe,rr,ids)
 def test_raw_CPU8_uses_exact_original_controller_child_and_full_budget(self):
  import ast
  p=Path(CORE.__file__).parent/"raw_cpu8.py";t=ast.parse(p.read_bytes())
  self.assertFalse(any(isinstance(n,ast.ClassDef)for n in ast.walk(t)))
  calls=[n for n in ast.walk(t)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
  self.assertTrue(any(isinstance(n.func.value,ast.Name)and n.func.value.id=="H"and n.func.attr=="Joint"for n in calls))
  self.assertTrue(any(isinstance(n.func.value,ast.Name)and n.func.value.id=="H"and n.func.attr=="controller"for n in calls))
  child=next(n for n in calls if isinstance(n.func.value,ast.Name)and n.func.value.id=="H"and n.func.attr=="child")
  self.assertEqual(child.args[3].value,5310)
  self.assertEqual({k.arg:k.value.value for k in child.keywords},{"observe":False})
  self.assertIn("raw_after_release",[n.func.attr for n in calls])



class EffectiveConfiguration(unittest.TestCase):
 setUp=Evidence.setUp
 tearDown=Evidence.tearDown
 artifact=Evidence.artifact
 owned=Evidence.owned
 def config_fixture(self,stage):
  import ast,importlib.util
  m=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes())
  row=next(r for r in m["files"]if Path(r["path"]).name=="server_entry.py")
  wire=(PRODUCER_ARCHIVE/"server_entry.py").read_bytes()
  self.assertEqual(hashlib.sha256(wire).hexdigest(),row["sha256"])
  proof_row=next(r for r in m["files"]if Path(r["path"]).name=="config_cpu.py")
  proof_wire=(PRODUCER_ARCHIVE/"config_cpu.py").read_bytes()
  self.assertEqual(hashlib.sha256(proof_wire).hexdigest(),proof_row["sha256"])
  ns={};exec(compile(proof_wire,"<actual-source-config-helper>","exec"),ns)
  installed={}
  for name,h in ns["PINS"].items():
   rows=[r for r in m["dependencies"]if r["sha256"]==h];self.assertEqual(len(rows),1)
   installed[name]=dict(path=self.root.as_posix()+"/fixture-installed/"+name.replace(".","/")+".py",bytes=rows[0]["bytes"],sha256=h)
  scalar=types.SimpleNamespace(max_num_batched_tokens=32768,max_num_seqs=1,enable_chunked_prefill=True,
   async_scheduling=False,long_prefill_token_threshold=0,max_num_partial_prefills=1,max_long_partial_prefills=1,
   max_num_scheduled_tokens=None,scheduler_reserve_full_isl=True)
  args=types.SimpleNamespace(model="/models/Qwen3.6-27B",max_model_len=33792,enforce_eager=True,
   enable_prefix_caching=False,mamba_cache_mode="none",max_num_batched_tokens=32768,max_num_seqs=1,
   enable_chunked_prefill=True,async_scheduling=False)
  model=types.SimpleNamespace(architecture="Qwen3_5ForConditionalGeneration",
   hf_config=types.SimpleNamespace(model_type="qwen3_5"),runner_type="generate",
   is_encoder_decoder=False,is_chunked_prefill_supported=True,max_model_len=33792,enforce_eager=True)
  policy=(ns["require_cpu_policy"](args,scalar,6*CORE.GIB)if stage=="cpu"else
          ns["require_firstdecode_policy"](model,scalar,6*CORE.GIB))
  tree=ast.parse(wire)
  if stage=="server":
   outer=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="install_engine_config_gate")
   inner=next(x for x in outer.body if isinstance(x,ast.FunctionDef)and x.name=="checked")
   call=next(x for x in ast.walk(inner)if isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=="publish")
   expression=call.args[0];env=dict(policy=policy,proof=types.SimpleNamespace(actual_sources=lambda:installed))
  else:
   outer=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="actual_config_precheck")
   expression=next(x.value for x in reversed(outer.body)if isinstance(x,ast.Return))
   env=dict(stage=stage,installed=installed,policy=policy,full=(stage=="n1"),
    proof=types.SimpleNamespace(CPU_SCHEDULER_ASSUMPTIONS=ns["CPU_SCHEDULER_ASSUMPTIONS"]))
  value=eval(compile(ast.fix_missing_locations(ast.Expression(body=expression)),"<actual-producer-config-return>","eval"),env)
  return value,m
 def test_actual_CPU_scalar_return_expression_honest_partial(self):
  value,m=self.config_fixture("cpu");checked=CORE.effective_config(value,"cpu",m)
  self.assertFalse(value["actual_model_config_constructed"]);self.assertEqual(checked["max_num_batched_tokens"],32768)
 def test_CPU_cannot_claim_model_or_full_engine(self):
  for key in("actual_model_config_constructed","model_dependent_scheduler_fields_verified","full_engine_config_verified"):
   value,m=self.config_fixture("cpu");value[key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):CORE.effective_config(value,"cpu",m)
 def test_actual_N1_return_expression_full_configuration(self):
  value,m=self.config_fixture("n1");CORE.effective_config(value,"n1",m)
  self.assertTrue(value["actual_model_config_constructed"])
  value["full_engine_config_verified"]=False
  with self.assertRaisesRegex(ValueError,"CPU scalar"):CORE.effective_config(value,"n1",m)
 def test_actual_config_no_larger_batch_or_subchunk(self):
  for key,bad in(("max_num_batched_tokens",33792),("long_prefill_token_threshold",8192),("max_num_seqs",True)):
   value,m=self.config_fixture("n1");value["actual_policy"][key]=bad
   with self.subTest(key=key),self.assertRaises(ValueError):CORE.effective_config(value,"n1",m)
 def test_actual_config_all_installed_sources_and_stage_binding(self):
  value,m=self.config_fixture("cpu");del value["actual_installed_sources"]["vllm.config.scheduler"]
  with self.assertRaisesRegex(ValueError,"all six"):CORE.effective_config(value,"cpu",m)
  value,m=self.config_fixture("n1");value["actual_installed_sources"]["vllm.config.model"]["sha256"]="f"*64
  with self.assertRaisesRegex(ValueError,"byte binding"):CORE.effective_config(value,"n1",m)
  value,m=self.config_fixture("n1")
  with self.assertRaisesRegex(ValueError,"stage/schema"):CORE.effective_config(value,"cpu",m)
 def server_fixture(self):
  value,m=self.config_fixture("server");front=dict(pid=123,start_ticks=456,cgroup="7:memory:/docker/"+self.cid)
  frontend=self.root/"FRONTEND.json";frontend.write_text(json.dumps(front),encoding="utf-8")
  recipe=dict(diagnostic_root=str(self.root),frontend_binding_path=str(frontend))
  rr=self.artifact(recipe);ctx=types.SimpleNamespace(m=m,producer=self.source)
  record=dict(value,source=self.source,recipe_ref=rr,actual_pid=front["pid"])
  p=self.root/"SERVER-CONFIG-p123.json";p.write_text(json.dumps(record),encoding="utf-8")
  raw=dict(frontend_ref=CORE.ref(frontend),host_processes=[dict(guest_identity=front)])
  return ctx,recipe,rr,raw,self.owned(),p
 def test_actual_server_return_bound_to_frontend_source_recipe(self):
  ctx,r,rr,raw,o,p=self.server_fixture();answer=CORE.server_configuration(ctx,r,rr,raw,o)
  self.assertEqual(answer["ref"],CORE.ref(p));self.assertEqual(answer["frontend_identity"]["start_ticks"],456)
 def test_server_wrong_PID_source_recipe_rejected(self):
  for key,bad in(("actual_pid",True),("source",{}),("recipe_ref",{})):
   ctx,r,rr,raw,o,p=self.server_fixture();record=json.loads(p.read_bytes());record[key]=bad;p.write_text(json.dumps(record),encoding="utf-8")
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"PID/source/recipe"):CORE.server_configuration(ctx,r,rr,raw,o)
 def test_server_not_canary_or_foreign_frontend_CID(self):
  ctx,r,rr,raw,o,p=self.server_fixture();o["cid"]="f"*64
  with self.assertRaisesRegex(ValueError,"mapped frontend"):CORE.server_configuration(ctx,r,rr,raw,o)

 def test_CPU_missing_or_falsely_verified_decoder_assumption_rejected(self):
  for changed in("missing","true","verified","wrong_origin","bool_alias"):
   value,m=self.config_fixture("cpu")
   if changed=="missing":del value["cpu_scheduler_assumptions"]
   elif changed=="true":value["cpu_scheduler_assumptions"]["is_encoder_decoder"]=True
   elif changed=="verified":value["cpu_scheduler_assumptions"]["checkpoint_verified"]=True
   elif changed=="wrong_origin":value["cpu_scheduler_assumptions"]["origin"]="guessed checkpoint"
   else:value["cpu_scheduler_assumptions"]["is_encoder_decoder"]=0
   with self.subTest(changed=changed),self.assertRaisesRegex(ValueError,"decoder-branch assumption"):
    CORE.effective_config(value,"cpu",m)
 def test_N1_cannot_reuse_unverified_CPU_decoder_fallback(self):
  value,m=self.config_fixture("n1")
  self.assertIsNone(value["cpu_scheduler_assumptions"])
  value["cpu_scheduler_assumptions"]=dict(is_encoder_decoder=False,checkpoint_verified=False,
   origin="installed SchedulerConfig.default_factory decoder fallback")
  with self.assertRaisesRegex(ValueError,"actual ModelConfig"):
   CORE.effective_config(value,"n1",m)


class CurrentProducerRebinding(unittest.TestCase):
 """Actual frozen source + real filesystem regressions, not model authority."""
 setUp=Evidence.setUp
 tearDown=Evidence.tearDown
 artifact=Evidence.artifact
 def manifest(self):
  raw=(PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes()
  self.assertEqual(len(raw),CORE.PRODUCER_BYTES)
  self.assertEqual(hashlib.sha256(raw).hexdigest(),CORE.PRODUCER_SHA)
  return json.loads(raw)
 def test_exact018_manifest_and_all37_source_bytes(self):
  m=self.manifest()
  self.assertEqual((len(m["files"]),len(m["dependencies"]),m["source_count"],m["software_tests_declared"]),(37,168,205,190))
  for row in m["files"]:
   p=PRODUCER_ARCHIVE/Path(row["path"]).name;wire=p.read_bytes()
   self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(row["bytes"],row["sha256"]))
  self.assertEqual(CORE.PRODUCER_ROOT,m["root"])
 def test_old014_and_failed016_refs_rejected_before_any_source_or_module_read(self):
  old=dict(path=CORE.PRODUCER_ROOT.replace("-018","-014")+"/SOURCE_MANIFEST.json",bytes=84644,
   sha256="8549453b332327e4440de005dfccfecc3fcbd123702c7e98e323de59ff92803a")
  old016=dict(path=CORE.PRODUCER_ROOT.replace("-018","-016")+"/SOURCE_MANIFEST.json",bytes=98890,
    sha256="79427342373ef63b11f5709d689c2ef6186afe09a94eaef53889b8f09cc3d0c7")
  old017=dict(path=CORE.PRODUCER_ROOT.replace("-018","-017")+"/SOURCE_MANIFEST.json",bytes=102218,
   sha256="17a1e214a80bea2dbe9e10fffdfe2b6fae81203c63b1c3410e6bf3f6b95bf19f")
  for bad in(old,old016,old017,dict(self.source,bytes=True),dict(self.source,bytes=71457)):
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,"unique frozen producer"):CORE.Context(bad)
 def software_gate(self,value):
  # Execute the EXACT two source statements consumed by producer_only; no
  # parallel hand-written acceptance predicate or fake Context initialization.
  import ast
  tree=ast.parse(Path(CORE.__file__).read_bytes())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="producer_only")
  i=next(i for i,n in enumerate(fn.body)if isinstance(n,ast.Assign)
   and any(isinstance(z,ast.Name)and z.id=="sw"for z in n.targets))
  statements=fn.body[i:i+2]
  self.assertTrue(isinstance(statements[1],ast.Expr))
  ns=dict(obj=CORE.obj,need=CORE.need,PRODUCER_TESTS=CORE.PRODUCER_TESTS,r=dict(software=self.artifact(value)),
   ctx=types.SimpleNamespace(producer=self.source,m=self.manifest()))
  exec(compile(ast.Module(body=statements,type_ignores=[]),CORE.__file__,"exec"),ns)
 def test_actual_software190_gate_accepts_current_whole_record(self):
  self.software_gate(dict(source=self.source,successful=True,tests=190,NPU=False,model_ready=False))
 def test_actual_software_gate_rejects_old_partial_failed_or_promoted(self):
  good=dict(source=self.source,successful=True,tests=190,NPU=False,model_ready=False)
  for change in(dict(tests=50),dict(tests=57),dict(tests=167),dict(tests=179),dict(successful=False),dict(source={}),dict(NPU=True),dict(model_ready=True)):
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,"actual software190"):
    self.software_gate(dict(good,**change))

 def run_original_creator_regression(self,name):
  # Reuse frozen author's real producer/contract/strict-loader test body.
  # Only directory fsync is spied on Windows; regular bytes/hash/stat/link are
  # actual. No source/global replacement in a runtime producer namespace.
  import ast,os,sys,importlib.util
  m=self.manifest();rows={Path(r["path"]).name:r for r in m["files"]}
  def module(name):
   p=PRODUCER_ARCHIVE/(name+".py");wire=p.read_bytes();row=rows[p.name]
   self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(row["bytes"],row["sha256"]))
   spec=importlib.util.spec_from_file_location("_whole012_fixture_"+name,p)
   actual=importlib.util.module_from_spec(spec);exec(compile(wire,str(p),"exec"),actual.__dict__)
   return actual
  p=PRODUCER_ARCHIVE/"test_firstdecode.py";wire=p.read_bytes()
  self.assertEqual(hashlib.sha256(wire).hexdigest(),rows[p.name]["sha256"])
  tree=ast.parse(wire)
  node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="ActualOwnerReferenceCreator")
  env=dict(unittest=unittest,ast=ast,os=os,sys=sys,types=types,json=json,Path=Path,HERE=PRODUCER_ARCHIVE,module=module)
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),"exec"),env)
  result=unittest.TestResult();env["ActualOwnerReferenceCreator"](name).run(result)
  self.assertEqual(result.testsRun,1)
  self.assertTrue(result.wasSuccessful(),str(result.errors)+str(result.failures))
 def test_actual_creator_complete_Ref3_and_nested_mapping(self):
  self.run_original_creator_regression("test_real_creator_all_six_and_mapping_nested_use_strict_actual_bytes")
 def test_actual_strict_loader_still_rejects_Ref2(self):
  self.run_original_creator_regression("test_original_ref2_is_rejected_by_unchanged_loader_before_object_read")
 def test_actual_creator_good_Ref3_and_bad_SHA(self):
  self.run_original_creator_regression("test_creator_existing_ref3_preserved_and_bad_original_sha_rejected")
 def test_actual_creator_bool_size_extra_key_rejected(self):
  self.run_original_creator_regression("test_creator_bool_wrong_size_and_extra_key_not_normalized_away")
 def test_actual_creator_missing_inspect_no_fake_size(self):
  self.run_original_creator_regression("test_missing_original_inspect_cannot_create_owner_or_fake_size")
 def test_actual_publication_then_mutation_is_rejected(self):
  self.run_original_creator_regression("test_consumer_rejects_changed_original_after_owner_publication")
 def test_actual_creator_exact_two_normalizations_strict_loader(self):
  self.run_original_creator_regression("test_actual_creator_only_two_checked_inspect_calls_and_loader_stays_closed")

ACTUAL_ARCHIVE=None
ACTUAL_EVIDENCE={
 "ORIGINAL_0548.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_KIVI018_0548_ORIGINAL_20261010.json","bytes":8686,"sha256":"fd71a259d096f75631cb5b6b54e33bee4747ccb7946e1454468a3c6486adc370"},
 "RESULT.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/RESULT.json","bytes":1090213,"sha256":"18e831dbf9c35b10f18d80d40a445155dc98ba656835c1918ee40fc4c7b4f6d4"},
 "cpu-preflight/OWNED.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/cpu-preflight/OWNED.json","bytes":45873,"sha256":"4af89afb4125c56d08028e5b9f19cd2e36d47a5e9b80e6cd8d18f33ad121d6dc"},
 "cpu-preflight/create_receipt.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/cpu-preflight/create-1791664212372375240.json","bytes":100269,"sha256":"f8559fa15ac93d0d0f5f97d7c27fbc457a9ed7ea68b918e6855c1103418dc035"},
 "candidate/OWNED.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/OWNED.json","bytes":45857,"sha256":"c2e67560bbd4d0ea89f29de50f8c2ea81df3ae2d5f9041c8b14e5bb32feca20d"},
 "candidate/create_receipt.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/create-1791664281154148680.json","bytes":100917,"sha256":"2a9262bf9efc53e19002073e7034183e77e20fca2486394b0f3b1b576ed15ff5"}}
class CurrentCwdAndOriginalMountOrder(unittest.TestCase):
 """Source/original artifact replay only; not whole/raw numeric acceptance."""
 def actual(self,name):
  r=ACTUAL_EVIDENCE[name]
  p=ACTUAL_ARCHIVE/name if ACTUAL_ARCHIVE is not None else Path(r["path"])
  wire=p.read_bytes()
  self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(r["bytes"],r["sha256"]))
  return CORE.decode(wire)
 def source_context(self):
  m=CORE.decode((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes())
  self.assertEqual((CORE.PRODUCER_BYTES,CORE.PRODUCER_SHA),
   (len((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes()),hashlib.sha256((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest()))
  own={Path(r["path"]).name:dict(r,path=str(PRODUCER_ARCHIVE/Path(r["path"]).name))for r in m["files"]}
  return types.SimpleNamespace(producer=ACTUAL_EVIDENCE["RESULT.json"]and self.actual("RESULT.json")["source"],own=own)
 def record(self):
  return CORE.original(self.actual("ORIGINAL_0548.json"),"lgw_a6109c51076a4a2c9d2674ca5a8704a0","exec-0000000000000548")
 def test_actual0548_unspecified_cwd_full_absolute_argv_and_pinned_sources(self):
  rec=self.record();inner=self.actual("RESULT.json")["actual_host_argv"]
  self.assertIsNone(rec["cwd"]);self.assertEqual([rec["command"],*rec["args"]],inner)
  CORE.exact_command(rec,rec["command"],rec["args"],5400,producer_context=self.source_context(),producer_argv=inner)
  CORE.exact_command(dict(rec,cwd=CORE.ROOT),rec["command"],rec["args"],5400)
  self.assertIsNone(rec["cwd"]) # original is not patched to a invented cwd
 def test_null_cwd_rejects_relative_paths_missing_cwd_and_other_directory(self):
  rec=self.record();inner=self.actual("RESULT.json")["actual_host_argv"];ctx=self.source_context()
  for index in (3,6,10,14,18,22,26):
   bad=list(inner);bad[index]="relative/file"
   with self.subTest(index=index),self.assertRaises(ValueError):
    CORE.exact_command(dict(rec,command=bad[0],args=bad[1:]),bad[0],bad[1:],5400,producer_context=ctx,producer_argv=bad)
  for change in ("missing","foreign","empty"):
   bad=dict(rec)
   if change=="missing":del bad["cwd"]
   else:bad["cwd"]="/unreviewed"if change=="foreign"else""
   with self.subTest(change=change),self.assertRaises(ValueError):
    CORE.exact_command(bad,rec["command"],rec["args"],5400,producer_context=ctx,producer_argv=inner)
 def test_null_cwd_wrong_source_argv_duration_and_raw_without_proof_rejected(self):
  rec=self.record();inner=self.actual("RESULT.json")["actual_host_argv"];ctx=self.source_context()
  for name in CORE.CWD_INDEPENDENT_PINS:
   bad=types.SimpleNamespace(producer=ctx.producer,own=copy.deepcopy(ctx.own));bad.own[name]["sha256"]="f"*64
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,"source identity"):
    CORE.exact_command(rec,rec["command"],rec["args"],5400,producer_context=bad,producer_argv=inner)
  with self.assertRaises(ValueError):CORE.exact_command(rec,rec["command"],rec["args"],5400)
  for change in (dict(durationMs=5400001),dict(durationMs=True),dict(args=rec["args"]+["--unreviewed"])):
   with self.subTest(change=change),self.assertRaises(ValueError):
    CORE.exact_command(dict(rec,**change),rec["command"],rec["args"],5400,producer_context=ctx,producer_argv=inner)
 def test_current_source_actual_Popen_cwd_and_file_based_imports(self):
  import ast
  ctx=self.source_context()
  for name in CORE.CWD_INDEPENDENT_PINS:CORE.read(ctx.own[name],128*1024)
  tree=ast.parse(CORE.read(ctx.own["host_run.py"]))
  calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and isinstance(n.func.value,ast.Name)and n.func.value.id=="subprocess"and n.func.attr=="Popen"]
  self.assertEqual(len(calls),3)
  for call in calls:
   value=next(k.value for k in call.keywords if k.arg=="cwd")
   self.assertTrue(isinstance(value,ast.Attribute)and isinstance(value.value,ast.Name)
    and value.value.id=="c"and value.attr=="ROOT")
  for name in ("model_contract.py","loader.py"):
   code=CORE.read(ctx.own[name]);t=ast.parse(code)
   base=next(n.value for n in t.body if isinstance(n,ast.Assign)and any(isinstance(z,ast.Name)and z.id=="BASE"for z in n.targets))
   self.assertIn("__file__",ast.unparse(base));self.assertIn("resolve()",ast.unparse(base))
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and n.func.attr=="chdir"for n in ast.walk(tree)))
 def create_factory(self):
  from pathlib import PurePosixPath
  ns=Evidence.extract_safety(self);ns["c"].ROOT=PurePosixPath(CORE.ROOT)
  return ns["create_argv"]
 def test_actual_both_create_receipts_replay_complete_original_mount_order(self):
  factory=self.create_factory()
  for arm in ("cpu-preflight","candidate"):
   owned=self.actual(arm+"/OWNED.json");created=self.actual(arm+"/create_receipt.json")
   self.assertEqual(owned["source"],self.source_context().producer)
   self.assertEqual(owned["create_receipt"]["sha256"],ACTUAL_EVIDENCE[arm+"/create_receipt.json"]["sha256"])
   self.assertNotEqual(created["requested_argv"],factory(owned)) # prove old sorted-dict seam
   CORE.exact_create_receipt(created,owned,factory)
   self.assertEqual(len(owned["mounts"]),174)
 def test_original_create_rejects_missing_extra_duplicate_and_RW_mount(self):
  factory=self.create_factory();owned=self.actual("candidate/OWNED.json");created=self.actual("candidate/create_receipt.json")
  i=created["requested_argv"].index("--mount")
  for change in ("missing","extra","duplicate","RW"):
   bad=copy.deepcopy(created);argv=bad["requested_argv"]
   if change=="missing":del argv[i:i+2]
   elif change=="extra":argv[i:i]=["--mount","type=bind,source=/unreviewed,destination=/unreviewed,readonly"]
   elif change=="duplicate":argv[i:i]=argv[i:i+2]
   else:argv[i+1]=argv[i+1].removesuffix(",readonly")
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,"mount set"):
    CORE.exact_create_receipt(bad,owned,factory)
 def test_original_create_resource_CID_and_nonmount_order_still_exact(self):
  factory=self.create_factory();owned=self.actual("candidate/OWNED.json");created=self.actual("candidate/create_receipt.json")
  for flag in ("--memory","--cpuset-cpus","--workdir","--label","--device"):
   bad=copy.deepcopy(created);i=bad["requested_argv"].index(flag);bad["requested_argv"][i+1]+="-changed"
   with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,"source-bound create"):
    CORE.exact_create_receipt(bad,owned,factory)
  bad=copy.deepcopy(created);bad["stdout"]="f"*64
  with self.assertRaisesRegex(ValueError,"source-bound create"):CORE.exact_create_receipt(bad,owned,factory)
 def test_actual_consumer_call_order_and_no_raw_cwd_relaxation(self):
  import ast
  tree=ast.parse(Path(CORE.__file__).read_bytes())
  producer=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="producer_only")
  direct=[(i,n.value)for i,n in enumerate(producer.body)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)]
  guard=next((i,n)for i,n in direct if isinstance(n.func,ast.Name)and n.func.id=="exact_command")
  i=next(i for i,n in enumerate(producer.body)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=="outer"for x in n.targets))
  self.assertGreater(guard[0],i);self.assertEqual({k.arg for k in guard[1].keywords},{"producer_context","producer_argv"})
  consume=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="consume")
  raw=next(n for n in ast.walk(consume)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="exact_command")
  self.assertEqual(raw.keywords,[])
  cleanup=next(n for c in tree.body if isinstance(c,ast.ClassDef)and c.name=="Context"for n in c.body if isinstance(n,ast.FunctionDef)and n.name=="cleanup")
  self.assertTrue(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="exact_create_receipt"for n in ast.walk(cleanup)))


# Byte-exact current0548 pre-create resource children. Not model/raw acceptance.
OBSERVATION_ARCHIVE=None
OBSERVATION_EVIDENCE={
 "FIRST_OBSERVATION.json":dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/observation-1791664278790524020.json",bytes=11530,sha256="00f5041f558d4fe8dcb5ecf258bca8ef3f97b739dc1852d56c68c5978a59018b"),
 "engine-1791664278788955340.json":dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/engine-1791664278788955340.json",bytes=3140,sha256="be1757c38ee007179517be04f10582b90c9924447e7734fd7c601fc9d4a05830"),
 "OUTPUT-SCAN-1791664278748210610.json":dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/OUTPUT-SCAN-1791664278748210610.json",bytes=1275,sha256="7d7689e6dc841eac5413eff903e903119d526ca150a80ceea835467a9306e6ca")}

class CurrentObservationPhase(unittest.TestCase):
 def actual(self,name):
  r=OBSERVATION_EVIDENCE[name]
  p=OBSERVATION_ARCHIVE/name if OBSERVATION_ARCHIVE is not None else Path(r["path"])
  b=p.read_bytes()
  self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r["bytes"],r["sha256"]))
  return CORE.decode(b)
 def ctx(self):
  import importlib.util
  from pathlib import PurePosixPath
  helper=Evidence.extract_safety(self)
  sr=REVIEWED_DEPS/"output_budget.py"
  self.assertEqual(hashlib.sha256(sr.read_bytes()).hexdigest(),"44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad")
  sp=importlib.util.spec_from_file_location("_kivi_phase_scanner_fixture",sr);scanner=importlib.util.module_from_spec(sp);sp.loader.exec_module(scanner)
  original=scanner.consume
  # Only host path spelling differs in Windows local fixtures; contents/root are unchanged.
  scanner.Path=PurePosixPath
  scanner.consume=lambda value,root:original(value,PurePosixPath(root.as_posix()))
  ctx=CORE.Context.__new__(CORE.Context);ctx.s=helper;ctx.scanner=scanner
  m=CORE.decode((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes())
  ctx.own={Path(r["path"]).name:dict(r,path=str(PRODUCER_ARCHIVE/Path(r["path"]).name))for r in m["files"]}
  return ctx
 def resource_call(self,row,initial):
  from unittest.mock import patch
  original=CORE.obj
  children={OBSERVATION_EVIDENCE[n]["path"]:n for n in OBSERVATION_EVIDENCE if n!="FIRST_OBSERVATION.json"}
  def bounded_child(r,*args):
   if r.get("path")in children:
    n=children[r["path"]];self.assertEqual(r["sha256"],OBSERVATION_EVIDENCE[n]["sha256"])
    if "bytes"in r:self.assertEqual(r["bytes"],OBSERVATION_EVIDENCE[n]["bytes"])
    return self.actual(n)
   return original(r,*args)
  scan=self.actual("OUTPUT-SCAN-1791664278748210610.json")
  with patch.object(CORE,"obj",bounded_child):
   return self.ctx().resources(row["resources"],scan["root"],initial)
 def first(self):return OBSERVATION_EVIDENCE["FIRST_OBSERVATION.json"]
 def test_actual0548_initial_phase_and_real_full_resource_replay(self):
  row=self.actual("FIRST_OBSERVATION.json")
  self.assertTrue(CORE.model_observation_initial(row,self.first(),0,self.first()))
  self.assertEqual(row["resources"]["ordinary_floor_bytes"],73*CORE.GIB)
  self.assertEqual(self.resource_call(row,True),row["resources"]["cpu_allocation"])
 def test_actual0548_old_all_live_consumer_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"RAM/disk reserve"):
   self.resource_call(self.actual("FIRST_OBSERVATION.json"),False)
 def test_every_source_live_label_uses_original_nine_GiB_predicate(self):
  for label in CORE.MODEL_LIVE_LABELS:
   row=self.actual("FIRST_OBSERVATION.json");row["label"]=label
   row["resources"]["ordinary_floor_bytes"]=9*CORE.GIB
   with self.subTest(label=label):
    self.assertFalse(CORE.model_observation_initial(row,dict(path="/fixture",sha256="f"*64),1,self.first()))
    self.assertEqual(self.resource_call(row,False),row["resources"]["cpu_allocation"])
 def test_wrong_floor_is_never_accepted_as_either_phase(self):
  for initial,floor in((True,9),(False,73),(True,72),(False,8)):
   row=self.actual("FIRST_OBSERVATION.json");row["resources"]["ordinary_floor_bytes"]=floor*CORE.GIB
   with self.subTest(initial=initial,floor=floor),self.assertRaisesRegex(ValueError,"RAM/disk reserve"):
    self.resource_call(row,initial)
 def test_wrong_first_ref_or_label_rejected(self):
  row=self.actual("FIRST_OBSERVATION.json")
  with self.assertRaisesRegex(ValueError,"exact owner"):CORE.model_observation_initial(row,{},0,self.first())
  row["label"]="model-startup"
  with self.assertRaisesRegex(ValueError,"exact owner"):CORE.model_observation_initial(row,self.first(),0,self.first())
 def test_preflight_reentry_and_unknown_live_label_rejected(self):
  row=self.actual("FIRST_OBSERVATION.json")
  for label,ref in(("model-preflight",self.first()),("model-preflight",{}),("unreviewed-stage",{})):
   row["label"]=label
   with self.subTest(label=label),self.assertRaisesRegex(ValueError,"live phase"):
    CORE.model_observation_initial(row,ref,1,self.first())
 def test_source_ast_complete_host_and_delegated_owner_observe_sites(self):
  import ast
  ctx=self.ctx();labels=set();explicit_initial=[]
  for name in CORE.MODEL_OBSERVATION_PINS:
   tree=ast.parse(CORE.read(ctx.own[name]))
   self.assertEqual(ctx.own[name]["sha256"],CORE.MODEL_OBSERVATION_PINS[name])
   for call in ast.walk(tree):
    if not(isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute)and call.func.attr=="observe"):continue
    if not call.args or not isinstance(call.args[0],ast.Constant):continue
    label=call.args[0].value
    if label in("cpu-preflight","software-cpu-preflight"):continue
    labels.add(label)
    initial=next((k.value for k in call.keywords if k.arg=="initial"),None)
    if initial is not None:
     self.assertIsInstance(initial,ast.Constant);self.assertIs(initial.value,True);explicit_initial.append(label)
  host=ast.parse(CORE.read(ctx.own["host_run.py"]))
  n1=next(call for call in ast.walk(host)if isinstance(call,ast.Call)and isinstance(call.func,ast.Name)
   and call.func.id=="child"and isinstance(call.args[1],ast.Constant)and call.args[1].value=="all4-N1")
  self.assertFalse(any(k.arg=="observe"for k in n1.keywords))
  labels.update(("all4-N1","all4-N1-finished"))
  self.assertEqual(labels,{"model-preflight",*CORE.MODEL_LIVE_LABELS})
  self.assertEqual(explicit_initial,["model-preflight"])
  run=next(n for n in host.body if isinstance(n,ast.FunctionDef)and n.name=="run")
  self.assertTrue(any(isinstance(n,ast.Attribute)and n.attr=="observations"for n in ast.walk(run)))
 def test_actual_owner_bind_phase_no_false_initial_reserve(self):
  row=self.actual("FIRST_OBSERVATION.json");row["label"]="kivi-real-all4-owner-bind"
  self.assertFalse(CORE.model_observation_initial(row,dict(path="/fixture-owner-bind",sha256="e"*64),2,self.first()))
  row["resources"]["ordinary_floor_bytes"]=9*CORE.GIB
  self.resource_call(row,False)
 def test_original_model_loop_calls_phase_reader_not_blanket_false(self):
  import ast
  tree=ast.parse(Path(CORE.__file__).read_bytes())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="producer_only")
  calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="model_observations"]
  self.assertEqual(len(calls),1)
  loop=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="model_observations")
  call=next(n for n in ast.walk(loop)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="observation")
  self.assertEqual([(k.arg,k.value.id)for k in call.keywords],[("initial","initial")])
 def test_complete_loop_uses_one_true_then_all_source_live_phases(self):
  from unittest.mock import patch
  rows=[self.actual("FIRST_OBSERVATION.json")]
  for label in CORE.MODEL_LIVE_LABELS:
   row=copy.deepcopy(rows[0]);row["label"]=label;row["resources"]["ordinary_floor_bytes"]=9*CORE.GIB;row["actual_compute"]=[]
   rows.append(row)
  refs=[self.first()]+[dict(path="/phase-fixture/"+str(i),sha256=str(i)*64)for i in range(1,len(rows))]
  ctx=self.ctx();seen=[];allocation=rows[0]["resources"]["cpu_allocation"]
  def observation(ro,owned,pid,output,initial=False):
   index=refs.index(ro);seen.append(initial)
   return self.resource_call(rows[index],initial)
  ctx.observation=observation
  saved=CORE.obj
  with patch.object(CORE,"obj",lambda r,*a:rows[refs.index(r)]if r in refs else saved(r,*a)):
   self.assertEqual(CORE.model_observations(ctx,dict(observations=refs),dict(resource_ref=self.first()),{},1,"/fixture",allocation),[])
  self.assertEqual(seen,[True]+[False]*len(CORE.MODEL_LIVE_LABELS))

NAMESPACE_EVIDENCE=dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/KIVI_ALL4_NAMESPACE_RAW.json",bytes=24074,sha256="154a008968f09ecdadcf72aa1e74869c6236fd69d4cee28e3bac623a9eeb5c6e")
class CurrentNativeTitleRepresentation(unittest.TestCase):
 def actual(self):
  # Source of the original Ref is RESULT.npu.all4_namespace, not this local name.
  result=CurrentCwdAndOriginalMountOrder.actual(self,"RESULT.json");r=result["npu"]["all4_namespace"]
  self.assertEqual((r.get("bytes",24074),r["sha256"]),(24074,NAMESPACE_EVIDENCE["sha256"]))
  p=OBSERVATION_ARCHIVE/"KIVI_ALL4_NAMESPACE_RAW.json"if OBSERVATION_ARCHIVE is not None else Path(r["path"])
  wire=p.read_bytes();self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(24074,NAMESPACE_EVIDENCE["sha256"]))
  return CORE.decode(wire)
 def test_actual_five_original_hashes_frontend_strict_and_four_padded_titles(self):
  rows=self.actual()["host_processes"]
  self.assertEqual(len(rows),5)
  for i,row in enumerate(rows):
   p=row["process_proof"];self.assertEqual(p["cmdline_sha256"],row["cmdline_sha256"])
   self.assertTrue(CORE.cmdline_digest_matches(p["argv"],row["cmdline_sha256"],i-1 if i else None))
   if i:
    self.assertEqual(p["argv"],["VLLM::Worker_TP%d"%(i-1)])
    self.assertEqual(hashlib.sha256(p["argv"][0].encode()+b"\0"*141).hexdigest(),row["cmdline_sha256"])
   else:self.assertEqual(hashlib.sha256(b"\0".join(v.encode()for v in p["argv"])+b"\0").hexdigest(),row["cmdline_sha256"])
 def test_actual_titles_wrong_rank_and_hash_disagreement_rejected(self):
  rows=self.actual()["host_processes"]
  for rank,row in enumerate(rows[1:]):
   self.assertFalse(CORE.cmdline_digest_matches(row["process_proof"]["argv"],row["cmdline_sha256"],(rank+1)%4))
   self.assertFalse(CORE.cmdline_digest_matches(row["process_proof"]["argv"],"f"*64,rank))
 def test_non_tail_NUL_and_ordinary_argv_do_not_gain_padding_exception(self):
  title="VLLM::Worker_TP0"
  for argv,wire,rank in(([title],title.encode()+b"\0x\0",0),
   (["ordinary"],b"ordinary"+b"\0"*141,0),([title],title.encode()+b"\0"*4097,0),
   (["/python","arg"],b"/python\0arg\0\0",None)):
   with self.subTest(argv=argv,rank=rank):self.assertFalse(CORE.cmdline_digest_matches(argv,hashlib.sha256(wire).hexdigest(),rank))
  self.assertTrue(CORE.cmdline_digest_matches(["ordinary"],hashlib.sha256(b"ordinary\0").hexdigest()))
 def test_original_source_gate_process_preserves_raw_hash_and_filters_padding(self):
  helper=REVIEWED_DEPS/"full_matrix_host.py"
  source=CORE.extract(helper,"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
   ("start_ticks","process_identity","gate_process"),dict(Path=Path,hashlib=hashlib,require=CORE.need))
  with tempfile.TemporaryDirectory()as directory:
   base=Path(directory);pid=123
   st=Evidence.stat(self,pid,456);(base/"stat").write_text(st)
   (base/"cgroup").write_text("7:memory:/docker/fixture")
   (base/"status").write_text("NSpid:\t123\t22\n")
   wire=b"VLLM::Worker_TP0"+b"\0"*141;(base/"cmdline").write_bytes(wire)
   class ProcPath:
    def __truediv__(self,value):self_value=value;return base
   source["Path"]=lambda value:ProcPath()
   original=source["gate_process"](pid)
   self.assertEqual(original["argv"],["VLLM::Worker_TP0"])
   self.assertEqual(original["cmdline_sha256"],hashlib.sha256(wire).hexdigest())
   self.assertTrue(CORE.cmdline_digest_matches(original["argv"],original["cmdline_sha256"],0))

