"""Independent whole-terminal/resource/cleanup firstdecode consumer. No launcher."""
import ast, datetime, hashlib, importlib.util, json, math, os, re, sys
from pathlib import Path
GIB=1024**3
PRODUCER_ROOT="/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-014"
PRODUCER_SHA="8549453b332327e4440de005dfccfecc3fcbd123702c7e98e323de59ff92803a"
PRODUCER_BYTES=84644
PRODUCER_OWN=31;PRODUCER_DEPS=163;PRODUCER_COUNT=194;PRODUCER_TESTS=110
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
ROOT="/opt/host/vnf/austinov/model-tuning-lab"
SCOPE_FALSE=("model_ready","performance_ready","run_authority","whole176","full_model_correctness_verified")
def need(v,why):
 if not v:raise ValueError(why)
def decode(b):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,"duplicate JSON key");out[k]=v
  return out
 def bad(v):raise ValueError("nonfinite JSON "+v)
 return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def read(r,limit=8*1024**2,allow_empty=False):
 need(type(r)is dict and set(r)in({"path","sha256"},{"path","bytes","sha256"}),"strict original Ref2/3")
 p=Path(r["path"]);need(p.is_absolute()and ".."not in p.parts and not p.is_symlink()and p.is_file()and p.resolve()==p,"ordinary absolute Ref")
 need(re.fullmatch("[a-f0-9]{64}",r["sha256"]or"")is not None,"whole original SHA")
 a=p.stat();need((0 if allow_empty else 1)<=a.st_size<=limit,"bounded complete artifact")
 if "bytes"in r:need(type(r["bytes"])is int and r["bytes"]==a.st_size,"positive nonbool exact bytes")
 b=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)
  and len(b)==a.st_size and hashlib.sha256(b).hexdigest()==r["sha256"],"stable whole bytes/SHA")
 return b
def obj(r,limit=8*1024**2):return decode(read(r,limit))
def ref(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def source_module(r,name):
 read(r,128*1024)
 need(name not in sys.modules,"foreign cached namespace")
 spec=importlib.util.spec_from_file_location(name,r["path"]);m=importlib.util.module_from_spec(spec)
 sys.modules[name]=m
 try:spec.loader.exec_module(m)
 except BaseException:sys.modules.pop(name,None);raise
 return m
def original(raw,peer,operation):
 out=raw.get("structuredContent",raw);need(type(out)is dict,"whole operation envelope")
 if "structuredContent"in raw:
  blocks=[v for v in raw.get("content",[])if v.get("type")=="text"]
  if blocks:need(len(blocks)==1 and decode(blocks[0]["text"])==out,"text/structured disagreement")
 op=out.get("operation",out);oid=out.get("operationId")
 need(oid==operation and re.fullmatch("exec-[0-9a-f]{16}",oid or"")is not None
  and op.get("targetPeerId")==peer and op.get("routeDecision")=="peer_direct","exact MAIN operation/peer/direct")
 for k in("targetPeerId","routeDecision"):
  if k in out and op is not out:need(out[k]==op.get(k),"origin disagreement")
 rec=op.get("result",{}).get("record")
 need(type(rec)is dict and rec.get("id")==oid and rec.get("state")=="completed"
  and type(rec.get("exitCode"))is int and rec["exitCode"]==0
  and rec.get("cancelled")is rec.get("timedOut")is False and rec.get("error")is None
  and type(rec.get("stdout"))is type(rec.get("stderr"))is str,"actual success/no transport/cancel/timeout")
 for v in(raw,out,op,op.get("result",{}),rec):
  need(not any("truncat"in str(k).lower()and x not in(False,None,0,"")for k,x in v.items()),"untruncated whole original")
 return rec
def exact_command(rec,command,args,max_seconds):
 need(rec["command"]==command and rec["args"]==args and rec["cwd"]==ROOT
  and type(rec["durationMs"])in(int,float)and math.isfinite(rec["durationMs"])
  and 0<rec["durationMs"]<=max_seconds*1000,"literal command/cwd/bounded whole duration")
def utc(s):
 # Docker RFC3339Nano; Python3.9 fromisoformat cannot consume nine-digit fractions.
 # Compare exact integer nanoseconds, never truncate a release/start ordering.
 need(type(s)is str,"actual UTC timestamp string")
 m=re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(?:Z|\+00:00)",s)
 need(m is not None,"explicit UTC timestamp with at most nine fraction digits")
 d=datetime.datetime(*[int(m.group(i))for i in range(1,7)],tzinfo=datetime.timezone.utc)
 delta=d-datetime.datetime(1970,1,1,tzinfo=datetime.timezone.utc)
 return (delta.days*86400+delta.seconds)*10**9+int((m.group(7)or"").ljust(9,"0"))
def raw_after_release(npu_stopped,raw_stopped):
 finish=utc(npu_stopped["State"]["FinishedAt"]);start=utc(raw_stopped["State"]["StartedAt"])
 need(0<finish<=start,
  "independent CPU8 begins only after exact TP4 stopped")
def extract(path,digest,names,namespace):
 b=Path(path).read_bytes();need(hashlib.sha256(b).hexdigest()==digest,"actual extracted whole source SHA")
 t=ast.parse(b);nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name in names]
 need({n.name for n in nodes}==set(names),"actual method closure")
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),"exec"),namespace)
 return namespace
class Context:
 def __init__(self,producer):
  need(producer==dict(path=PRODUCER_ROOT+"/SOURCE_MANIFEST.json",bytes=PRODUCER_BYTES,sha256=PRODUCER_SHA),"unique frozen producer")
  m=obj(producer);need(m["schema"]=="kivi.actual-firstdecode-bootstrap-sources/v1","producer schema")
  own={Path(r["path"]).name:r for r in m["files"]}
  need(len(own)==PRODUCER_OWN and len(m["dependencies"])==PRODUCER_DEPS and m["source_count"]==PRODUCER_COUNT,"whole194 actual source")
  c=source_module(own["model_contract.py"],"_kivi_firstdecode_whole_contract")
  need(c.source(producer)==m,"actual current194 loader audit");c.configure(m)
  self.c=c;self.m=m;self.own=own;self.producer=producer
  self.runtime_boundary=source_module(own["runtime_boundary.py"],"_kivi_firstdecode_whole_runtime_boundary")
  ns=dict(c=c,re=re,Path=Path,PHYSICAL=(4,5,6,7),MEM=64*GIB,OWNER="kivi-firstdecode-eager-diagnostic-v1")
  self.s=extract(own["safety_host.py"]["path"],own["safety_host.py"]["sha256"],
    ("device_map","cpu_admission","environment","labels","create_argv","validate_inspect","actual_hbm"),dict(ns,DOCKER="/usr/bin/docker"))
  life=m["runtime_roles"]["protected_lifecycle"]
  self.boundary=extract(life["path"],life["sha256"],("protected_boundary",),dict(re=re,require=need))["protected_boundary"]
  sr=m["runtime_roles"]["output_scanner"]
  self.scanner=source_module(sr,"_kivi_firstdecode_whole_output_scanner")
  # Exact frozen infrastructure, no commands or live /proc/device inspection.
  self.h=c.module(c.H8,c.DEPS[str(c.H8)],"_kivi_firstdecode_whole_frozen_h8").frozen()
  ev=m["runtime_roles"]["memory_evidence"]
  if "evidence"in sys.modules:
   need(ref(sys.modules["evidence"].__file__)==ev,"foreign cached memory evidence")
  else:source_module(ev,"evidence")
  self.memory=source_module(m["runtime_roles"]["memory_stream"],"_kivi_firstdecode_whole_memory_stream")
 def inspect(self,r,owned,stopped=False):
  raw=obj(r);need(raw["exit_code"]==0 and raw.get("requested_argv",raw.get("argv"))==["/usr/bin/docker","inspect",owned["cid"]],"exact own inspect receipt")
  xs=decode(raw["stdout"]);need(type(xs)is list and len(xs)==1,"one exact inspect")
  x=xs[0];self.s["validate_inspect"](x,owned)
  state=x["State"];need(state["OOMKilled"]is False,"actual OOM invalidates scope")
  if stopped:need(state["Running"]is False and state["Pid"]==0 and not x.get("ExecIDs"),"stopped/Pid0/noExec")
  return x
 def cleanup(self,r,owned,host_pid):
  need(owned["host_sha256"]==self.own["safety_host.py"]["sha256"]and
   owned["sources"]=={Path(q["path"]).name:q["sha256"]for q in self.m["files"]},"actual complete source identity in OWNED")
  created=obj(owned["create_receipt"])
  need(created["exit_code"]==0 and created["stdout"].strip()==owned["cid"]and
   created["requested_argv"]==self.s["create_argv"](owned),"actual exact source-bound create receipt")
  x=obj(r);need(x["container"]==owned["cid"]and x["stopped"]is x["retained"]is True
    and x["deleted"]is False and x["errors"]==[]and x["primary_error"]is None,"exact own stop-retain/no errors/primary")
  self.inspect(x["before_inspect"],owned);after=self.inspect(x["after_inspect"],owned,True)
  sr=obj(x["stop_receipt"]);need(sr["exit_code"]==0 and sr["requested_argv"]==["/usr/bin/docker","stop","--time","15",owned["cid"]]
    and sr["cleanup_safety_only"]is True and sr["original_admission_failures"]==[],"exact own stop/no borrowed cleanup success")
  release=obj(x["release_smi"]);need(release["exit_code"]==0 and release["requested_argv"]==["/usr/local/sbin/npu-smi","info"],"actual release SMI")
  for p in(4,5,6,7):self.h.idle_one(release["stdout"],p)
  pb=x["protected_boundary"]
  need(pb==self.boundary(pb["baseline"],pb["observed"],[owned["cid"]],[host_pid]),"independent protected0..3 replay")
  return after
 def resources(self,x,whole_root,initial):
  need(type(x)is dict and x["memory"]["SwapTotal"]==x["memory"]["SwapFree"],"actual unused swap")
  floor=(73 if initial else 9)*GIB
  need(x["ordinary_floor_bytes"]==floor and x["memory"]["MemAvailable"]>=floor
   and x["disk_free_bytes"]>=(8.5+(32 if initial else 0))*GIB,"actual RAM/disk reserve unchanged")
  allocation=self.s["cpu_admission"](x["host_cpu"],x["daemon_cpu"])
  need(x["cpu_allocation"]==allocation and x["aggregate_rss_kib"]==x["host_peak_rss_kib"]+x["child_peak_rss_kib"]
   and 0<=x["aggregate_rss_kib"]<=512*1024,"summed CPU7/host+children512MiB")
  engine=obj(x["engine"]);need(engine["exit_code"]==0 and decode(engine["stdout"])["NCPU"]>=7,"actual engine CPU")
  scan=obj(x["actual_output_scan_ref"])
  used=self.scanner.consume(scan,Path(whole_root))
  need(x["output_allowance_bytes"]==32*GIB and x["output_bytes"]==used<=32*GIB,"complete strict32GiB scanner replay")
  return allocation
 def observation(self,r,owned,host_pid,whole_root,initial=False):
  x=obj(r);smi=obj(x["smi"])
  need(smi["exit_code"]==0 and x["npu_smi"]==smi["stdout"]and x["observed_utc"]==smi["observed_utc"],"SMI raw observation binding")
  pb=x["protected_boundary"]
  need(pb["observed"]==x["protected0_3"]and pb==self.boundary(pb["baseline"],pb["observed"],[owned["cid"]],[host_pid]),"protected original all boundaries")
  need(x["actual_hbm"]==[self.s["actual_hbm"](smi["stdout"],p)for p in(4,5,6,7)],"actual full physical HBM3GiB reserve")
  rawrows=self.h.legacy().process_rows(smi["stdout"])
  need([(p["physical"],p["chip"],p["pid"])for p in x["actual_compute"]]==[(n,ch,pid)for n,ch,pid in rawrows if n in(4,5,6,7)],"all actual4..7 processes, no omitted foreign")
  for p in x["actual_compute"]+x["actual_device_fd_holders"]:
   need(owned["cid"]in p["cgroup"]and p["pid"]!=host_pid and p["start_ticks"]>0,"actual same owned PID/start/FDs")
  if initial:
   for card in(4,5,6,7):self.h.idle_one(smi["stdout"],card)
  return self.resources(x["resources"],whole_root,initial)
def child(x,requested,success=True):
 need(x["requested_argv"]==requested and x["actual_host_argv"]==["/usr/bin/prlimit","--as=unlimited","--",*requested],"exact child AS restoration")
 ended=x.get("termination_observed",x.get("child_termination_observed"))
 pid=x.get("pid",x.get("child_host_pid"))
 need(ended is True and type(pid)is int and pid>1 and type(x["exit_code"])is int,"actual child completed")
 if success:need(x["exit_code"]==0,"actual computational child must succeed")
 read(x["stdout_ref"],allow_empty=True);read(x["stderr_ref"],allow_empty=True)
def stat_start(raw,pid):
 p=raw.find("(");e=raw.rfind(")");f=raw[e+2:].split()
 need(0<p<e and int(raw[:p].strip())==pid and len(f)>=20 and f[0]!="Z"and f[19].isdigit(),"actual live raw /proc stat")
 return int(f[19])
def namespace(x,recipe,owned,inspect_fn,proofs,host_pid):
 need(x["schema"]=="kivi.actual-firstdecode-namespace-raw/v1"and x["container_id"]==owned["cid"]
  and x["external_owner_authority_ref"]==recipe["external_owner_authority_ref"]and x["original_consumer_required"]is True
  and x["run_authority"]is False and len(x["host_processes"])==5 and len(x["request_refs"])==4,"actual all4+frontend original")
 inspect_fn(x["owned_inspect"],owned)
 reqs=[obj(r)for r in x["request_refs"]];front=obj(x["frontend_ref"]);identities=[front]+[r["identity"]for r in reqs]
 need([r["rank"]for r in reqs]==list(range(4))and len({v["host_pid"]for v in x["host_processes"]})==5,"ordered unique all4 ranks")
 for i,(row,ident)in enumerate(zip(x["host_processes"],identities)):
  need(set(ident)=={"pid","start_ticks","cgroup"}and type(ident["pid"])is type(ident["start_ticks"])is int
   and ident["pid"]>0 and ident["start_ticks"]>0 and owned["cid"]in ident["cgroup"]
   and row["guest_identity"]==ident and row["nspid"][-1]==ident["pid"]and row["host_pid"]!=host_pid
   and owned["cid"]in row["cgroup"]and stat_start(row["stat_before"],row["host_pid"])==stat_start(row["stat_after"],row["host_pid"])==ident["start_ticks"]
   and re.fullmatch("[a-f0-9]{64}",row["cmdline_sha256"]or"")is not None,"real stable namespace/start/CID")
  p=row["process_proof"]
  need(p["pid"]==row["host_pid"]and p["start_ticks"]==ident["start_ticks"]and p["cgroup"]==row["cgroup"]and p["argv"]
   and p["namespace_pids"]==row["nspid"]and p["cmdline_sha256"]==row["cmdline_sha256"]
   ==hashlib.sha256(b"\0".join(v.encode()for v in p["argv"])+b"\0").hexdigest(),"original host gate proof")
  if i:
   req=reqs[i-1];need(req["schema"]=="kivi.actual-rank-owner-request/v1"and req["container_id"]==owned["cid"]
    and req["source_ref"]==recipe["source_ref"]and req["run_id"]==recipe["run_id"]and req["physical_card"]==i+3
    and req["mapping_is_not_yet_verified"]is True and req["run_authority"]is False and row["physical_cards"]==[i+3],"original actual rank source/card")
   hits=[p for p in proofs if p["pid"]==row["host_pid"]and p["start_ticks"]==ident["start_ticks"]]
   need(hits and all(p["physical"]==i+3 and p["chip"]==0 and p["cgroup"]==row["cgroup"]for p in hits),"rank not borrowed canary/startup label")
 return identities[1:]
def raw_result(x,source,client_ref,client,m):
 need(x["schema"]=="kivi.actual-firstdecode-independent/v1"and x["status"]=="FIRSTDECODE_RAW_COMPONENTS_CONSUMED"
  and x["source"]==source and x["client_ref"]==client_ref and x["rank_bundle_refs"]==client["rank_bundle_refs"]
  and x["actual_ranks"]==4 and x["actual_FA_layers_per_rank"]==16 and len(x["frames"])==64
  and x["original_prefill_tokens"]==32768 and x["actual_first_decode_length"]==32769,"actual whole64 raw consumer same source/client")
 for k in("full1536_attention_outputs_per_FA_checked","source_bound_original_writer_checked","native_and_compact_disjoint_spans_checked","no_candidate_math_import"):
  need(x[k]is True,"exact original raw consumer predicate "+k)
 for k in("untouched_GDN_content_checked","model_ready","performance_ready","run_authority","graph_checked","allocation_replaced","whole_176"):
  need(x[k]is False,"raw firstdecode scope not promoted "+k)
 for k,role in(("independent_oracle_source","fast_oracle"),("independent_reader_source","fast_consume"),("writer_reader_source","writer_reader")):
  need(x[k]==m["runtime_roles"][role],"actual independent oracle/reader source")
 seen=set()
 for row in x["frames"]:
  need(type(row["rank"])is int and row["rank"]in range(4)and type(row["layer"])is str,"actual frame key")
  key=(row["rank"],row["layer"]);need(key not in seen,"no repeated frame claims");seen.add(key)
  read(row["frame_ref"])
 need(all(sum(r==i for r,l in seen)==16 for i in range(4)),"all16 peractual rank")
def effective_config(value,stage,m):
 """Reconstruct exact policy/installed-byte identities, not model permission."""
 need(type(value)is dict and stage in("cpu","n1","server")
  and value["schema"]=="kivi.actual-firstdecode-effective-config/v1"
  and value["stage"]==stage,"actual config stage/schema")
 for k in("engine_or_weights_created","model_ready","performance_ready","run_authority"):
  need(value[k]is False,"config proof is not engine/model authority "+k)
 full=(stage!="cpu")
 need(value["full_engine_config_verified"]is full,"CPU scalar versus N1/server actual full config")
 if stage!="server":
  need(value["actual_model_config_constructed"]is full
   and value["actual_scheduler_config_constructed"]is True
   and value["model_dependent_scheduler_fields_verified"]is full,
   "CPU must not claim model-qualified configuration")
 if stage=="cpu":
  assumed=value.get("cpu_scheduler_assumptions")
  need(type(assumed)is dict and set(assumed)=={"is_encoder_decoder","checkpoint_verified","origin"}
   and assumed["is_encoder_decoder"]is False and assumed["checkpoint_verified"]is False
   and assumed["origin"]=="installed SchedulerConfig.default_factory decoder fallback",
   "explicit unverified CPU decoder-branch assumption; not actual checkpoint fact")
 elif stage=="n1":
  need(value.get("cpu_scheduler_assumptions")is None,"N1 actual ModelConfig, not CPU decoder fallback")
 pins={
  "vllm.engine.arg_utils":"3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d",
  "vllm.config.scheduler":"36bdfcf50a8f30d9f1c0dbdd3630a0075234f5c9e1a77943a934c45329f25c86",
  "vllm.config.model":"cf5aeb9e16d6cac82426cf7e8d140741b35c503ae8b9e1fc9ba3dde53c585a62",
  "vllm.config.vllm":"ba062ec38d075937b73d953059cf1d0e1b96f1474990bc6d45ed45e20ba6a336",
  "vllm.entrypoints.openai.api_server":"6d8df133280618a1afffa9d03e4655af011f2f94ced0f90c15f7fc8b0afc538f",
  "vllm_ascend.platform":"30c75952f784c4d047d7202dd7f68c8fc7c22bb975853a5048fb51ffcbe1f2a8"}
 sources=value["actual_installed_sources"]
 need(type(sources)is dict and set(sources)==set(pins),"all six exact installed config sources")
 for name,h in pins.items():
  r=sources[name];rows=[x for x in m["dependencies"]if x["sha256"]==h]
  need(len(rows)==1 and type(r)is dict and set(r)=={"path","bytes","sha256"}
   and type(r["bytes"])is int and r["bytes"]==rows[0]["bytes"]and r["sha256"]==h
   and type(r["path"])is str and Path(r["path"]).is_absolute()
   and ".."not in Path(r["path"]).parts
   and r["path"].endswith("/"+name.replace(".","/")+".py"),
   "actual installed module/archive byte binding "+name)
 scalar=dict(max_model_len=33792,enforce_eager=True,max_num_batched_tokens=32768,
  max_num_seqs=1,enable_chunked_prefill=True,async_scheduling=False,
  long_prefill_token_threshold=0,max_num_partial_prefills=1,max_long_partial_prefills=1,
  scheduler_reserve_full_isl=True,cache_bytes=10*GIB)
 policy=value["actual_policy"]
 extra=(dict(model="/models/Qwen3.6-27B")if stage=="cpu"else
        dict(architecture="Qwen3_5ForConditionalGeneration",model_type="qwen3_5",runner_type="generate"))
 need(type(policy)is dict and set(policy)==set(scalar)|set(extra)|{"max_num_scheduled_tokens"},
  "only complete actual stage policy; no assumed model fields in CPU")
 for k,v in dict(scalar,**extra).items():
  need(type(policy[k])is type(v)and policy[k]==v,"unchanged actual configuration field "+k)
 need(policy["max_num_scheduled_tokens"]is None or
      type(policy["max_num_scheduled_tokens"])is int and policy["max_num_scheduled_tokens"]==32768,
      "no alternate actual native scheduled-token budget")
 return dict((k,policy[k])for k in scalar)|dict(max_num_scheduled_tokens=policy["max_num_scheduled_tokens"])

def server_configuration(ctx,recipe,recipe_ref,ns,owned):
 """Config came from the mapped real frontend, not canary or worker PID."""
 front=obj(ns["frontend_ref"])
 need(ns["frontend_ref"]==ref(Path(recipe["frontend_binding_path"]))
  and front==ns["host_processes"][0]["guest_identity"]
  and owned["cid"]in front["cgroup"],"actual mapped frontend PID/start/CID")
 p=Path(recipe["diagnostic_root"])/("SERVER-CONFIG-p%d.json"%front["pid"])
 rr=ref(p);record=obj(rr)
 need(record["source"]==ctx.producer and record["recipe_ref"]==recipe_ref
  and type(record["actual_pid"])is int and record["actual_pid"]==front["pid"],
  "actual server config PID/source/recipe, not inferred worker ID")
 scalar=effective_config(record,"server",ctx.m)
 return dict(ref=rr,frontend_identity=front,actual_scalar_policy=scalar)

def cann_cached(value,resolution,required):
 need(type(value)is dict and type(value.get("imported"))is bool and type(value.get("memcpy_observed"))is bool,"raw actual ACL cache schema")
 if value["imported"]is False:
  need(value==dict(imported=False,memcpy_observed=False)and not required,"actual native ACL import/memcpy required");return
 need(set(value)=={"imported","origin","memcpy_observed","memcpy_type","memcpy_module","import_is_not_device_correctness"}
  and value["origin"]==resolution and value["import_is_not_device_correctness"]is True,"actual cached native ACL origin, not numeric permission")
 if required:need(value["memcpy_observed"]is True and type(value["memcpy_type"])is str and value["memcpy_type"],"actual native rt.memcpy callable observed")
def cann_record(binding,cached,m,source,required=False):
 x=m["cann_python_binding"];root=x["pythonpath_root"]
 want=dict(name="acl",origin=x["acl_file"],loader_type="_frozen_importlib_external.ExtensionFileLoader",
  binary=dict(path=x["acl_file"],size_bytes=x["acl_bytes"],sha256=x["acl_sha256"]))
 need(type(binding)is dict and binding["schema"]=="kivi.actual-cann-python-binding/v1"and binding["source_ref"]==source
  and binding["image"]==x["image"]==IMAGE and binding["pythonpath_root"]==root
  and binding["fixed_root_resolution"]==binding["effective_resolution"]==want
  and binding["set_env"]==dict(path=x["set_env_file"],size_bytes=x["set_env_bytes"],sha256=x["set_env_sha256"]),
  "actual source-bound fixed ACL extension/binary/CANN env")
 before=binding["sys_path_before"];after=binding["sys_path_after"]
 need(type(before)is type(after)is list and all(type(v)is str for v in before+after)
  and after==(before if root in before else[root,*before])and type(binding["isolated_flag"])is int
  and binding["isolated_flag"]in(0,1)and binding["acl_import_executed_by_helper"]is False
  and binding["actual_import_required_at_N1_and_worker"]is True and binding["model_ready"]is binding["performance_ready"]is False,
  "fixed-root resolution only, no arbitrary path/permission assimilation")
 cann_cached(binding["cached_before"],want,False);cann_cached(cached,want,required)
 return want
def worker_cann(m,source,recipe,recipe_ref,identities):
 need(len(identities)==4,"all4 actual worker CANN originals")
 refs=[]
 for ident in identities:
  q=ref(Path(recipe["diagnostic_root"])/("CANN-WORKER-p%d.json"%ident["pid"]));raw=obj(q)
  need(raw["source_ref"]==source and raw["recipe_ref"]==recipe_ref and raw["identity"]==ident
   and raw["model_ready"]is raw["performance_ready"]is False,"actual CANN worker PID/start/CID/source/recipe")
  cann_record(raw["binding"],raw["cached_after_native_import"],m,source,True);refs.append(q)
 return refs

def reject_worker_fatal(result):
 need(type(result)is dict and "worker_first_fault_refs"in result and "worker_first_fault"in result
  and result["worker_first_fault_refs"]==[]and result["worker_first_fault"]is None,
  "worker initialization first-fault must remain empty for success; never promote FATAL")

def driver_properties(value,rank,m):
 """Consume raw source-qualified driver ABI, never infer a Torch attribute."""
 keys={"schema","logical_rank","current_device","helper_source","device_properties",
  "raw_properties_repr","driver_type_module","driver_type_name","source_api",
  "model_ready","performance_ready","run_authority"}
 need(type(value)is dict and set(value)==keys
  and value["schema"]=="kivi.actual-rank-driver-properties/v1"
  and type(rank)is int and rank in range(4)
  and type(value["logical_rank"])is type(value["current_device"])is int
  and value["logical_rank"]==value["current_device"]==rank,
  "actual driver rank/device/schema, not canary or bool alias")
 archived=m["runtime_abi_original_refs"]["helper"]
 need(archived["bytes"]==2090 and archived["sha256"]==
  "f94d81f163f0076e8243990dd687f7ec8d42ce1ed30d67eea3155bf1c3a073a4",
  "exact installed helper original pin")
 rows=[r for r in m["dependencies"]if r["sha256"]==archived["sha256"]
  and r["path"]=="/cache/cch/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py"]
 need(len(rows)==1 and type(value["helper_source"])is dict
  and set(value["helper_source"])=={"path","bytes","sha256"}
  and type(value["helper_source"]["bytes"])is int
  and value["helper_source"]==rows[0],"actual installed helper path/bytes/SHA, no snapshot alias")
 props=value["device_properties"]
 need(type(props)is dict and set(props)=={"num_aicore","num_vectorcore"}
  and all(type(v)is int and 0<v<=65535 for v in props.values()),
  "exact two bounded integer compiler core counts; no fallback")
 need(type(value["raw_properties_repr"])is str and 0<len(value["raw_properties_repr"])<=16384
  and all(type(value[k])is str and value[k]for k in("driver_type_module","driver_type_name"))
  and value["source_api"]=="triton.runtime.driver.active.utils.get_device_properties(torch.npu.current_device())",
  "complete actual driver raw representation/type/API")
 for key in("model_ready","performance_ready","run_authority"):
  need(value[key]is False,"driver ABI is not model authority "+key)
 return props

def worker_driver_abi(ctx,recipe,recipe_ref,identities,canary,result):
 reject_worker_fatal(result)
 need(type(identities)is list and len(identities)==4 and type(canary)is list and len(canary)==4,
  "all four original driver owners and N1 rows")
 # Independently read the actual pure source-qualified FATAL originals as well
 # as RESULT fields. No HTTP DONE, absent operation handle or success flag is used.
 ctx.runtime_boundary.raise_if_any(ctx.c,recipe,recipe_ref,ctx.producer,ctx.own["runtime_boundary.py"])
 refs=[]
 for rank,ident in enumerate(identities):
  before=driver_properties(canary[rank]["actual_driver_properties"],rank,ctx.m)
  q=ref(Path(recipe["diagnostic_root"])/("DRIVER-PROPERTIES-r%d.json"%rank));raw=obj(q)
  extras={"source_ref","recipe_ref","identity"}
  need(type(raw)is dict and extras.issubset(raw)
   and raw["source_ref"]==ctx.producer and raw["recipe_ref"]==recipe_ref and raw["identity"]==ident,
   "actual worker driver source/recipe/PID/start/CID")
  proof={k:v for k,v in raw.items()if k not in extras}
  after=driver_properties(proof,rank,ctx.m)
  need(after==before and proof["helper_source"]==canary[rank]["actual_driver_properties"]["helper_source"]
   and proof["driver_type_module"]==canary[rank]["actual_driver_properties"]["driver_type_module"]
   and proof["driver_type_name"]==canary[rank]["actual_driver_properties"]["driver_type_name"],
   "same actual N1/worker current-rank driver ABI; no assigned core fallback")
  refs.append(q)
 return refs

def producer_only(a,ctx):
 rr=ref(a.result);need(rr["sha256"]==a.result_sha256,"original whole RESULT SHA")
 tr=ref(a.terminal);need(tr["sha256"]==a.terminal_sha256,"original whole terminal SHA")
 rec=original(obj(tr),a.peer,a.operation)
 exact_command(rec,a.expected_command,decode(a.expected_args),5400)
 r=obj(rr);need(r["schema"]=="kivi.actual-firstdecode-owned-host/v1"and
  r["status"]=="RAW_CAPTURED_PENDING_INDEPENDENT_WHOLE_CONSUMPTION"and r["source"]==ctx.producer
  and r["primary"]is None and r["secondary"]==[],"firstfault preserved; no failed operation promoted")
 reject_worker_fatal(r)
 markers=[]
 for line in rec["stdout"].splitlines():
  try:v=decode(line)
  except(ValueError,TypeError):continue
  if type(v)is dict and set(v)=={"result","status"}:markers.append(v)
 need(markers==[dict(result=rr,status=r["status"])],"unique actual host stdout binds RESULT")
 for k in SCOPE_FALSE:need(r[k]is False,"no inherited broader permission "+k)
 need(r["independent_raw_consumer_required"]is True and r["phase_seconds"]==5400 and r["cleanup_seconds"]==90
  and 0<r["elapsed_seconds"]<=5400 and 0<=r["cumulative_cleanup_seconds"]<=90,"same whole5400/cleanup90 no clock reset")
 need(r["unchanged_source_after"]=={q["path"]:q["sha256"]for q in ctx.m["files"]},"all30 own source unchanged")
 output=Path(rr["path"]).parent;cpu=r["cpu"];npu=r["npu"];owned=obj(npu["owned"]);co=obj(cpu["owned"])
 need(owned["source"]==co["source"]==ctx.producer and owned["arm"]=="candidate"and co["arm"]=="cpu-preflight"
  and npu["container"]==owned["cid"]and owned["cid"]!=co["cid"],"two source-bound exact own containers")
 host=r["actual_host_process"];need(type(host["pid"])is int and host["pid"]>1 and host["start_ticks"]>0 and host["argv"]==r["actual_host_argv"],"actual host PID/start/argv")
 expected=["/usr/bin/python3","-I","-B",PRODUCER_ROOT+"/host_run.py","--execute"]
 for flag,key in(("source","source"),("component","component"),("software","software"),("model-manifest","model_manifest")):
  q=r[key];read(q);expected+=["--"+flag,q["path"],"--"+flag+"-sha256",q["sha256"]]
 # Port may be omitted iff the original parser default8250 is used.
 inner=r["actual_host_argv"];prefix=expected+["--output",str(output)]
 need(inner==prefix or(len(inner)==len(prefix)+2 and inner[:len(prefix)]==prefix and inner[-2]=="--port"and inner[-1].isdigit()),"literal original host option order/source")
 outer=[rec["command"],*rec["args"]]
 need(outer==inner or(len(outer)>len(inner)and outer[-len(inner):]==inner and outer[:2]==["/usr/bin/taskset","-c"]),"actual host source not unrelated terminal")
 need(r["component"]==ctx.m["packed3_qualification_ref"]and r["model_manifest"]==ctx.m["model_manifest"],"exact predecessor/model identity")
 sw=obj(r["software"]);need(sw["source"]==ctx.producer and sw["successful"]is True and sw["tests"]==ctx.m["software_tests_declared"]==PRODUCER_TESTS and sw["NPU"]is sw["model_ready"]is False,"actual software110")
 cr=obj(cpu["report"]);nr=obj(npu["canary"])
 need(cr["schema"]==nr["schema"]=="kivi.actual-firstdecode-preflight/v1"and cr["source"]==nr["source"]==ctx.producer
  and cr["status"]=="CPU_IMPORT_PARSER_CHECKED"and nr["status"]=="N1_ALL4_TINY_CHECKED"and cr["mode"]=="cpu"and nr["mode"]=="n1"
  and cr["canary"]==[]and [(q["logical"],q["physical"],q["output"])for q in nr["canary"]]==[(i,i+4,[4.,5.])for i in range(4)],"actual CPU8/all4 tiny distinct from model")
 cpu_config=effective_config(cr["actual_configuration"],"cpu",ctx.m)
 n1_config=effective_config(nr["actual_configuration"],"n1",ctx.m)
 need(cpu_config==n1_config,"same actual argv scalar policy across CPU and N1")
 # Delegate namespace cgroup semantics to pinned original pure reader.
 ctx.memory.consume_memory(cr["memory"],expected_limit=8*GIB,container_id=co["cid"])
 ctx.memory.consume_memory(nr["memory"],expected_limit=64*GIB,container_id=owned["cid"])
 cpu_child=obj(cpu["child"]);n1_child=obj(npu["canary_child"])
 for v,mode,cid,report in((cpu_child,"cpu",co["cid"],cpu["report"]),(n1_child,"n1",owned["cid"],npu["canary"])):
  argv=v["requested_argv"];child(v,argv)
  want=ctx.c.docker_argv(cid,[PRODUCER_ROOT+"/guest_probe.py","--execute","--mode",mode,"--source-manifest-sha256",PRODUCER_SHA,
    "--output",report["path"],"--cache-bytes",str(10*GIB),"--port",inner[-1]if inner[-2]=="--port"else"8250"])
  need(argv==want,"real CPU/N1 original child entry")
 cpu_stopped=ctx.cleanup(cpu["cleanup"],co,host["pid"]);npu_stopped=ctx.cleanup(npu["cleanup"],owned,host["pid"])
 need(utc(cpu_stopped["State"]["FinishedAt"])<=utc(npu_stopped["State"]["StartedAt"]),"CPU8 stopped before actual TP4")
 recipe=obj(npu["recipe"]);need(recipe["source_ref"]==npu["source"]==ctx.producer and recipe["container_id"]==owned["cid"]
  and recipe["image_id"]==IMAGE and recipe["bits"]==2 and recipe["cache_bytes"]==10*GIB and recipe["run_authority"]is False,"actual same recipe")
 owner=obj(recipe["external_owner_authority_ref"])
 need(owner["schema"]=="kivi.firstdecode.actual-owned-precondition/v1"and owner["source"]==ctx.producer and owner["container_id"]==owned["cid"]
  and owner["image"]==IMAGE and owner["physical_devices"]==[4,5,6,7]and owner["logical_to_physical"]==dict((str(i),i+4)for i in range(4))
  and owner["guest_limit_bytes"]==64*GIB and owner["host_limit_bytes"]==512*1024**2 and owner["ordinary_initial_floor_bytes"]==73*GIB
  and owner["phase_seconds_including_cleanup"]==5400 and owner["cleanup_seconds"]==90 and owner["hbm_reserve_mib_per_card"]==3072
  and owner["portfolio_cutoff"]==1791788425 and owner["canary_ref"]==npu["canary"]and owner["cpu_ref"]==cpu["report"],"actual owner admission unchanged")
 ctx.inspect(owner["owned_inspect_ref"],owned)
 allocation=ctx.observation(owner["resource_ref"],owned,host["pid"],output,True)
 actual_proofs=[]
 for ro in npu["observations"]:need(ctx.observation(ro,owned,host["pid"],output)==allocation,"unchanged CPU quota/cpuset across model")
 need(npu["observations"],"actual model observations required")
 for ro in npu["observations"]:actual_proofs.extend(obj(ro)["actual_compute"])
 need(npu["worker_process_proofs"] and all(p in actual_proofs for p in npu["worker_process_proofs"]),"all worker proofs bind completed raw observations")
 ns=obj(npu["all4_namespace"])
 ids=namespace(ns,recipe,owned,ctx.inspect,npu["worker_process_proofs"],host["pid"])
 config=server_configuration(ctx,recipe,npu["recipe"],ns,owned)
 need(config["actual_scalar_policy"]==n1_config,"same actual final server/native config")
 client=obj(npu["client_report"])
 need(client["schema"]=="kivi.actual-firstdecode-client/v1"and client["status"]=="HTTP_AND_NATIVE_FINAL_OBSERVED"
  and client["source_ref"]==ctx.producer and client["recipe_ref"]==npu["recipe"]and client["rank_bundle_refs"]==npu["rank_bundle_refs"]
  and client["done_observed"]is True and client["native_retirement_is_not_inferred_from_HTTP_DONE"]is True
  and client["usage"]["prompt_tokens"]==32768 and client["usage"]["completion_tokens"]==2 and len(client["completion_token_ids"])==2,"actual full input+2/token/native FINAL client")
 read(client["raw_sse_ref"])
 child(npu["client_child"],npu["client_argv"])
 # Owned stop is the server's termination cause. Nonzero server return is NOT numerical failure.
 child(npu["server_child"],npu["server_argv"],success=False)
 cann_record(cr["cann_python_binding"],cr["cann_cached_after_imports"],ctx.m,ctx.producer,False)
 cann_record(nr["cann_python_binding"],nr["cann_cached_after_imports"],ctx.m,ctx.producer,True)
 need(cr["native_worker_import_qualified"]is False and nr["native_worker_import_qualified"]is True,"CPU archive only versus actual N1 native-worker import")
 cann_refs=worker_cann(ctx.m,ctx.producer,recipe,npu["recipe"],ids)
 drivers=worker_driver_abi(ctx,recipe,npu["recipe"],ids,nr["canary"],r)
 return dict(rr=rr,tr=tr,r=r,npu=npu,co=co,owned=owned,host=host,client=client,ids=ids,npu_stopped=npu_stopped,cann_refs=cann_refs,config=config,drivers=drivers)
def consume(a,ctx):
 p=producer_only(a,ctx)
 rr,tr,r,npu,co,owned,host,client,ids,npu_stopped=[p[k]for k in("rr","tr","r","npu","co","owned","host","client","ids","npu_stopped")]
 rawref=ref(a.raw_result);need(rawref["sha256"]==a.raw_result_sha256,"exact independent raw result")
 rawrec=original(obj(ref(a.raw_terminal)),a.raw_peer,a.raw_operation)
 need(ref(a.raw_terminal)["sha256"]==a.raw_terminal_sha256,"raw whole SHA")
 need(a.raw_wall_seconds==5400,"full64 independent raw budget5400, no short-budget sampling")
 exact_command(rawrec,a.raw_expected_command,decode(a.raw_expected_args),a.raw_wall_seconds)
 owner_ref=ref(a.raw_owner_result);meta=obj(owner_ref)
 entry_refs=[]
 for line in rawrec["stdout"].splitlines():
  try:q=decode(line)
  except(ValueError,TypeError):continue
  if type(q)is dict and set(q)=={"path","bytes","sha256"}:entry_refs.append(q)
 need(len(entry_refs)==1,"one original raw-owner entry output")
 entry=obj(entry_refs[0]);own_mf=ref(Path(__file__).parent/"SOURCE_MANIFEST.json")
 need(entry["schema"]=="kivi.actual-firstdecode-whole-entry/v1"and entry["source"]==own_mf
  and entry["successful"]is True and entry["primary"]is None and entry["raw_owner_result"]==owner_ref
  and all(entry[k]is False for k in("model_ready","performance_ready","run_authority","whole176","NPU")),
  "independent new-source raw entry, not unowned helper success")
 need(meta["schema"]=="kivi.actual-firstdecode-raw-owned-host/v1"and meta["source"]==ctx.producer
  and meta["consumer_source"]==own_mf and meta["status"]=="RAW_FULL64_WITH_EXACT_CPU8_CLEANUP"
  and meta["primary"]is None and meta["secondary"]==[]and meta["original_model_result"]==rr
  and meta["original_model_terminal"]==tr and meta["original_raw_result"]==rawref
  and meta["raw_cpu8_owned"]==ref(a.raw_owned)and meta["original_raw_child"]==ref(a.raw_child)
  and meta["raw_cpu8_cleanup"]==ref(a.raw_cleanup)and meta["phase_seconds"]==5400
  and meta["cleanup_seconds"]==90 and 0<meta["elapsed_seconds"]<=5400 and 0<=meta["cumulative_cleanup_seconds"]<=90,
  "same actual independent CPU8 whole/source/64/90-cleanup result")
 need(meta["producer_source_after"]=={q["path"]:q["sha256"]for q in ctx.m["files"]}
  and meta["raw_checker_full64_unchanged"]is True,"all30 producer source unchanged across raw check")
 rh=meta["actual_host_process"];outer=[rawrec["command"],*rawrec["args"]];inner=meta["actual_host_argv"]
 need(type(rh["pid"])is int and rh["pid"]>1 and rh["start_ticks"]>0 and rh["argv"]==inner
  and len(outer)>=len(inner)and outer[-len(inner):]==inner
  and inner[:4]==["/usr/bin/python3","-I","-B",str(Path(__file__).parent/"main.py")]
  and inner[4:8]==["--execute","--mode","raw","--source-manifest-sha256"]
  and inner[8]==own_mf["sha256"]and inner.count("--output")==1
  and inner[inner.index("--output")+1]==entry_refs[0]["path"],
  "literal independently owned raw source/command/marker")
 raw=obj(rawref);raw_result(raw,ctx.producer,npu["client_report"],client,ctx.m)
 # Actual Devices[] CPU owner/child/stop is mandatory, not inferred from no-candidate-import.
 ro=obj(ref(a.raw_owned));need(ro["source"]==ctx.producer and ro["arm"]=="cpu-preflight"
  and ro["cid"]not in(co["cid"],owned["cid"]),"raw actual independent source-bound CPU8")
 ctx.memory.consume_memory(raw["actual_memory_before"],expected_limit=8*GIB,container_id=ro["cid"])
 raw_child=obj(ref(a.raw_child));rcargv=raw_child["requested_argv"];child(raw_child,rcargv)
 needle=[PRODUCER_ROOT+"/consume_raw.py","--execute","--source-manifest-sha256",PRODUCER_SHA,"--client-ref-json"]
 dc=ctx.c.docker_argv(ro["cid"],[])
 need(rcargv[:len(dc)]==dc and rcargv[len(dc):len(dc)+len(needle)]==needle,"real original independent entry no candidate/math")
 args=rcargv[len(dc):];need(args[-2:]==["--output",rawref["path"]],"raw actual result belongs to original CLI")
 clientref=obj(ref(Path(args[args.index("--client-ref-json")+1])))
 need(clientref==npu["client_report"],"raw CLI consumes exact same client")
 raw_stopped=ctx.cleanup(ref(a.raw_cleanup),ro,rh["pid"])
 raw_after_release(npu_stopped,raw_stopped)
 raw_allocation=None
 for i,q in enumerate(meta["raw_observations"]):
  allocation=ctx.observation(q,ro,rh["pid"],Path(owner_ref["path"]).parent,initial=(i==0))
  if raw_allocation is None:raw_allocation=allocation
  need(allocation==raw_allocation,"raw whole actual CPU quota/cpuset stable")
 need(len(meta["raw_observations"])==2,"original raw CPU8 preflight and complete resources")
 # Finished identities are replayed by original scalar consumer; verify source-bound rank bundles tie to mapped workers.
 for i,q in enumerate(client["rank_bundle_refs"]):
  bundle=obj(q);need(bundle["rank"]==i and bundle["identity"]==ids[i],"raw rank bundle matches actual namespace mapping")
 return dict(schema="kivi.actual-firstdecode-whole-consumed/v1",status="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED",
  producer_source=ctx.producer,original_terminal=tr,original_result=rr,raw_original_terminal=ref(a.raw_terminal),
  actual_CANN_N1_and_all4_worker_verified=True,actual_CANN_worker_refs=p["cann_refs"],
  actual_driver_N1_and_all4_worker_verified=True,actual_driver_worker_refs=p["drivers"],
  worker_initialization_fatal_originals_checked=True,
  CPU_scalar_configuration_checked=True,CPU_ModelConfig_verified=False,
  N1_actual_fullEngine_configuration_checked=True,actual_server_configuration=p["config"],
  independent_raw_result=rawref,host_owned_admission_semantically_consumed=True,MAIN_original_operation_verified=True,
  firstdecode_integration_checked=True,original_prefill_tokens=32768,actual_first_decode_length=32769,FA_frames=64,
  native_finished_all4_checked=True,first_fault=None,protected0_3_checked=True,stopped_retained_CIDs=[co["cid"],owned["cid"],ro["cid"]],
  server_cleanup_exit_code=npu["server_child"]["exit_code"],normal_server_stop_is_not_computation_failure=True,
  model_ready=False,performance_ready=False,run_authority=False,whole176=False,whole_176=False,
  graph_checked=False,mixed_checked=False,GDN_numerically_checked=False,full_model_correctness_verified=False,
  scope="single-request B1 eager32768+2 actual all4/FA16 firstdecode only; no FULL/mixed/GDN/model-perf/tasks")


