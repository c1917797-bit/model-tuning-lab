"""Independent whole-terminal/resource/cleanup firstdecode consumer. No launcher."""
import ast, datetime, hashlib, importlib.util, json, math, os, re, sys
from pathlib import Path
GIB=1024**3
PRODUCER_ROOT="/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-003"
PRODUCER_SHA="827e987e372957cd0dce3438b035dbe5aa752d7f695dfe78417d9b913dfa83d3"
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
  need(producer==dict(path=PRODUCER_ROOT+"/SOURCE_MANIFEST.json",bytes=58655,sha256=PRODUCER_SHA),"unique frozen producer")
  m=obj(producer);need(m["schema"]=="kivi.actual-firstdecode-bootstrap-sources/v1","producer schema")
  own={Path(r["path"]).name:r for r in m["files"]}
  need(len(own)==24 and len(m["dependencies"])==154 and m["source_count"]==178,"whole178 original source")
  c=source_module(own["model_contract.py"],"_kivi_firstdecode_whole_contract")
  need(c.source(producer)==m,"actual original178 loader audit");c.configure(m)
  self.c=c;self.m=m;self.own=own;self.producer=producer
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
def consume(a,ctx):
 rr=ref(a.result);need(rr["sha256"]==a.result_sha256,"original whole RESULT SHA")
 tr=ref(a.terminal);need(tr["sha256"]==a.terminal_sha256,"original whole terminal SHA")
 rec=original(obj(tr),a.peer,a.operation)
 exact_command(rec,a.expected_command,decode(a.expected_args),5400)
 r=obj(rr);need(r["schema"]=="kivi.actual-firstdecode-owned-host/v1"and
  r["status"]=="RAW_CAPTURED_PENDING_INDEPENDENT_WHOLE_CONSUMPTION"and r["source"]==ctx.producer
  and r["primary"]is None and r["secondary"]==[],"firstfault preserved; no failed operation promoted")
 markers=[]
 for line in rec["stdout"].splitlines():
  try:v=decode(line)
  except(ValueError,TypeError):continue
  if type(v)is dict and set(v)=={"result","status"}:markers.append(v)
 need(markers==[dict(result=rr,status=r["status"])],"unique actual host stdout binds RESULT")
 for k in SCOPE_FALSE:need(r[k]is False,"no inherited broader permission "+k)
 need(r["independent_raw_consumer_required"]is True and r["phase_seconds"]==5400 and r["cleanup_seconds"]==90
  and 0<r["elapsed_seconds"]<=5400 and 0<=r["cumulative_cleanup_seconds"]<=90,"same whole5400/cleanup90 no clock reset")
 need(r["unchanged_source_after"]=={q["path"]:q["sha256"]for q in ctx.m["files"]},"all24 own source unchanged")
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
 sw=obj(r["software"]);need(sw["source"]==ctx.producer and sw["successful"]is True and sw["tests"]==ctx.m["software_tests_declared"]==18 and sw["NPU"]is sw["model_ready"]is False,"actual software18")
 cr=obj(cpu["report"]);nr=obj(npu["canary"])
 need(cr["schema"]==nr["schema"]=="kivi.actual-firstdecode-preflight/v1"and cr["source"]==nr["source"]==ctx.producer
  and cr["status"]=="CPU_IMPORT_PARSER_CHECKED"and nr["status"]=="N1_ALL4_TINY_CHECKED"and cr["mode"]=="cpu"and nr["mode"]=="n1"
  and cr["canary"]==[]and [(q["logical"],q["physical"],q["output"])for q in nr["canary"]]==[(i,i+4,[4.,5.])for i in range(4)],"actual CPU8/all4 tiny distinct from model")
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
 ids=namespace(obj(npu["all4_namespace"]),recipe,owned,ctx.inspect,npu["worker_process_proofs"],host["pid"])
 client=obj(npu["client_report"])
 need(client["schema"]=="kivi.actual-firstdecode-client/v1"and client["status"]=="HTTP_AND_NATIVE_FINAL_OBSERVED"
  and client["source_ref"]==ctx.producer and client["recipe_ref"]==npu["recipe"]and client["rank_bundle_refs"]==npu["rank_bundle_refs"]
  and client["done_observed"]is True and client["native_retirement_is_not_inferred_from_HTTP_DONE"]is True
  and client["usage"]["prompt_tokens"]==32768 and client["usage"]["completion_tokens"]==2 and len(client["completion_token_ids"])==2,"actual full input+2/token/native FINAL client")
 read(client["raw_sse_ref"])
 child(npu["client_child"],npu["client_argv"])
 # Owned stop is the server's termination cause. Nonzero server return is NOT numerical failure.
 child(npu["server_child"],npu["server_argv"],success=False)
 rawref=ref(a.raw_result);need(rawref["sha256"]==a.raw_result_sha256,"exact independent raw result")
 rawrec=original(obj(ref(a.raw_terminal)),a.raw_peer,a.raw_operation)
 need(ref(a.raw_terminal)["sha256"]==a.raw_terminal_sha256,"raw whole SHA")
 exact_command(rawrec,a.raw_expected_command,decode(a.raw_expected_args),a.raw_wall_seconds)
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
 raw_stopped=ctx.cleanup(ref(a.raw_cleanup),ro,host["pid"])
 raw_after_release(npu_stopped,raw_stopped)
 # Finished identities are replayed by original scalar consumer; verify source-bound rank bundles tie to mapped workers.
 for i,q in enumerate(client["rank_bundle_refs"]):
  bundle=obj(q);need(bundle["rank"]==i and bundle["identity"]==ids[i],"raw rank bundle matches actual namespace mapping")
 return dict(schema="kivi.actual-firstdecode-whole-consumed/v1",status="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED",
  producer_source=ctx.producer,original_terminal=tr,original_result=rr,raw_original_terminal=ref(a.raw_terminal),
  independent_raw_result=rawref,host_owned_admission_semantically_consumed=True,MAIN_original_operation_verified=True,
  firstdecode_integration_checked=True,original_prefill_tokens=32768,actual_first_decode_length=32769,FA_frames=64,
  native_finished_all4_checked=True,first_fault=None,protected0_3_checked=True,stopped_retained_CIDs=[co["cid"],owned["cid"],ro["cid"]],
  server_cleanup_exit_code=npu["server_child"]["exit_code"],normal_server_stop_is_not_computation_failure=True,
  model_ready=False,performance_ready=False,run_authority=False,whole176=False,whole_176=False,
  graph_checked=False,mixed_checked=False,GDN_numerically_checked=False,full_model_correctness_verified=False,
  scope="single-request B1 eager32768+2 actual all4/FA16 firstdecode only; no FULL/mixed/GDN/model-perf/tasks")

