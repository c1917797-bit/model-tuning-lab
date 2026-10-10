"""Independent original capture + after-release CPU terminal consumer, DEFAULT OFF.
No controller, Torch, device query, deletion, or performance permission. Pure
metadata/scalar replay does not repeat the long tensor oracle. Its actual child,
all16 outputs and fixed source identity are consumed, never a supplied PASS flag.
"""
import argparse,hashlib,importlib.util,json,math,sys,types
from pathlib import Path
GIB=1024**3
CUTOFF=1791788425
CORE_SHA="a5d27c8945e21c88f5ba82e5b6f1f8c05c7252b68b7ea237b67d7aef7cae31e1"
RELEASE_SHA="bacb98cb15e6cc8b4542e9153d2124a3cb73045735c44485970074b969485f37"
def need(v,m):
 if not v:raise ValueError(m)
def module(row,name):
 p=Path(row["path"]);b=p.read_bytes()
 need(p.is_absolute() and p.resolve()==p and not p.is_symlink() and len(b)==row["bytes"]
  and hashlib.sha256(b).hexdigest()==row["sha256"],"exact source Ref before import")
 if name in sys.modules:
  m=sys.modules[name];need(Path(m.__file__).resolve()==p,"foreign namespace")
  return m
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m
 try:exec(compile(b,str(p),"exec"),m.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 return m
def context(source):
 m=json.loads(Path(source["path"]).read_bytes())
 roles=m["runtime_roles"];need(roles["release_core"]["sha256"]==CORE_SHA
  and roles["release_replay"]["sha256"]==RELEASE_SHA,"unchanged original pure release code")
 core=module(roles["release_core"],"_mixed_terminal_original_core");need(core.obj(source)==m,"exact runtime MF")
 release=module(roles["release_replay"],"_mixed_terminal_release")
 ctx=release.make_context(source,core=core,core_ref=roles["release_core"])
 need(ctx.own["consume_whole_cpu.py"]==core.ref(Path(__file__).resolve())
  and roles["whole_cpu_consumer"]==ctx.own["consume_whole_cpu.py"],"actual own terminal consumer closure")
 ctx.scanner=module(roles["output_scanner"],"_mixed_terminal_scanner")
 loader=module(ctx.own["loader.py"],"_mixed_terminal_loader")
 ctx.memory=loader.memory_module(m)
 ctx.core=core;ctx.release=release
 ctx.resources=types.MethodType(resource_replay,ctx)
 return ctx
def finite(x,lo,hi):
 return type(x)in(int,float) and math.isfinite(x) and lo<=x<=hi
def unchanged(r,ctx):
 need(r["source"]==ctx.producer and r["primary"]is None and r["secondary"]==[],
  "successful exact-source host; first faults preserved")
 need(r["unchanged_source_after"]=={q["path"]:q["sha256"]for q in ctx.m["files"]},"all own sources unchanged")
 for k in("model_ready","performance_ready","run_authority"):need(r[k]is False,"no broader host permission")
 need(r["cleanup_seconds"]==90 and finite(r["cumulative_cleanup_seconds"],0,90),"whole cleanup90 unchanged")
def terminal(core,result_ref,terminal_ref,peer,operation,command,args,budget):
 r=core.obj(result_ref);rec=core.original(core.obj(terminal_ref),peer,operation)
 if rec.get("cwd")is None:
  # Only this source-qualified host's absolute direct entry is cwd-independent.
  # host_binding below still checks every flag, output, source and phase.
  inner=r["actual_host_argv"];outer=[command,*args]
  script=str(Path(r["source"]["path"]).parent/"host_run.py")
  need(type(inner)is list and inner[:5]==["/usr/bin/python3","-I","-B",script,"--execute"]
   and (outer==inner or(len(outer)==len(inner)+3 and outer[:2]==["/usr/bin/taskset","-c"]
    and __import__("re").fullmatch(r"[0-9]+(?:,[0-9]+)*",outer[2])and outer[3:]==inner))
   and rec["command"]==command and rec["args"]==args
   and finite(rec["durationMs"],0.000001,budget*1000),"exact absolute own source entry with actual null cwd")
 else:core.exact_command(rec,command,args,budget)
 markers=[]
 for line in rec["stdout"].splitlines():
  try:v=core.decode(line)
  except(ValueError,TypeError):continue
  if type(v)is dict and set(v)=={"result","status"}:markers.append(v)
 need(markers==[dict(result=result_ref,status=r["status"])],"one original operation binds exact RESULT")
 need(finite(r["elapsed_seconds"],0.000001,budget),"same phase deadline no reset")
 return r,rec
def host_binding(ctx,r,rec,phase,result_ref):
 host=r["actual_host_process"];inner=r["actual_host_argv"];root=ctx.m["root"]
 need(type(host["pid"])is int and host["pid"]>1 and type(host["start_ticks"])is int
  and host["start_ticks"]>0 and host["argv"]==inner,"actual stable host identity")
 need(inner[:5]==["/usr/bin/python3","-I","-B",root+"/host_run.py","--execute"],"actual frozen host entry")
 tail=inner[5:];need(len(tail)%2==0,"only actual flag/value host options")
 opts={}
 for k,v in zip(tail[::2],tail[1::2]):
  need(k.startswith("--") and k not in opts,"unique actual options");opts[k]=v
 allowed={"--phase","--output","--port","--capture-peer","--capture-operation","--capture-command","--capture-args"}
 for name in("source","component","software","model-manifest","firstdecode-args","capture-result","capture-terminal"):
  allowed.update(("--"+name,"--"+name+"-sha256"))
 need(set(opts)<=allowed and opts.get("--phase","capture")==phase
  and opts["--output"]==str(Path(result_ref["path"]).parent),"exact scope/output; peer capture not yet terminal-qualified")
 need(opts["--source"]==ctx.producer["path"] and opts["--source-sha256"]==ctx.producer["sha256"],"same source argv")
 if "--port"in opts:need(opts["--port"].isdigit()and 1024<=int(opts["--port"])<=65535,"actual bounded port")
 outer=[rec["command"],*rec["args"]]
 need(outer==inner or(len(outer)>len(inner)and outer[-len(inner):]==inner
  and outer[:2]==["/usr/bin/taskset","-c"]),"original terminal really invoked this host")
 return opts
def owned_create(ctx,owned):
 c=ctx.core
 need(owned["source"]==ctx.producer and owned["host_sha256"]==ctx.own["safety_host.py"]["sha256"]
  and owned["sources"]=={Path(q["path"]).name:q["sha256"]for q in ctx.m["files"]},"same exact complete source owner")
 raw=c.obj(owned["create_receipt"])
 need(raw["exit_code"]==0 and raw["stdout"].strip()==owned["cid"]
  and raw["requested_argv"]==ctx.s["create_argv"](owned),"exact actual bounded create")
def cleanup_cpu(ctx,cleanup_ref,owned):
 c=ctx.core;owned_create(ctx,owned)
 need(owned["arm"]=="cpu-preflight","CPU branch cannot certify candidate")
 x=c.obj(cleanup_ref)
 need(x["schema"]=="kivi.actual-devices-empty-cleanup/v1" and x["container"]==owned["cid"]
  and x["stopped"]is x["retained"]is True and x["deleted"]is False
  and x["primary_error"]is None and x["errors"]==[] and x["npu_release_claim"]is False,
  "CPU own stop-retain, no false NPU release")
 before=ctx.inspect(x["before_inspect"],owned)
 after=ctx.inspect(x["after_inspect"],owned,True)
 need(before["HostConfig"].get("Devices",[])==after["HostConfig"].get("Devices",[])==[],
  "actual Devices[] before and after stop")
 sr=c.obj(x["stop_receipt"])
 need(sr["exit_code"]==0 and sr["requested_argv"]==["/usr/bin/docker","stop","--time","15",owned["cid"]]
  and sr["cleanup_safety_only"]is True and sr["original_admission_failures"]==[],
  "only exact CPU stop; no foreign CID or concealed formal failure")
 snap=sr["cleanup_resource_snapshot"]
 need(snap["aggregate_peak_rss_kib"]==snap["host_peak_rss_kib"]+snap["child_peak_rss_kib"]
  and 0<=snap["aggregate_peak_rss_kib"]<=512*1024 and snap["formal_limit_bytes"]==512*1024**2,
  "actual cleanup host+CLI RSS")
 # Deliberately no NPU query, current idle predicate, release_smi or foreign CID.
 return after
def resource_replay(ctx,x,whole_root,initial):
 c=ctx.core;floor=(73 if initial else 9)*GIB
 need(x["memory"]["SwapTotal"]==x["memory"]["SwapFree"] and x["ordinary_floor_bytes"]==floor
  and x["memory"]["MemAvailable"]>=floor and x["disk_free_bytes"]>=(8.5+(160 if initial else 0))*GIB,
  "actual no-swap RAM and fresh joint workspace/disk reserve")
 allocation=ctx.s["cpu_admission"](x["host_cpu"],x["daemon_cpu"])
 need(x["cpu_allocation"]==allocation and x["aggregate_rss_kib"]==x["host_peak_rss_kib"]+x["child_peak_rss_kib"]
  and 0<=x["aggregate_rss_kib"]<=512*1024,"source-derived quota/cpuset and summed host512MiB")
 er=c.obj(x["engine"])
 need(er["exit_code"]==0 and er["requested_argv"]==["/usr/bin/docker","info","--format","{{json .}}"]
  and c.decode(er["stdout"])["NCPU"]>=7,"actual engine inventory")
 scan=c.obj(x["actual_output_scan_ref"])
 if getattr(ctx,"capture_root",None)is not None:
  need(scan["schema"]=="kivi.mixed-joint-retained-output/v1" and scan["independent_roots"]is True
   and scan["limit_bytes"]==160*GIB,"combined retained raw plus new CPU output")
  now=Path(whole_root);old=ctx.capture_root
  need(now!=old and now not in old.parents and old not in now.parents,"disjoint exact output roots")
  used=ctx.scanner.consume(scan["current"],now)+ctx.scanner.consume(scan["retained_capture"],old)
  need(scan["output_bytes"]==used,"summed exact scanner output")
 else:used=ctx.scanner.consume(scan,Path(whole_root))
 need(x["output_bytes"]==used<=160*GIB and x["output_allowance_bytes"]==160*GIB,"whole160 no reset")
 return allocation
def cpu_observations(ctx,refs,owned,root):
 need(len(refs)>=2,"CPU pre-create and completed resource evidence")
 allocation=None
 for i,r in enumerate(refs):
  x=ctx.core.obj(r)
  need(x["schema"]=="kivi.actual-cpu-only-resource-observation/v1" and x["devices"]==[]
   and x["npu_ownership_claim"]is False,"CPU observation has no current NPU ownership predicate")
  if x["inspected"]is None:need(i==0,"only before CPU creation lacks inspect")
  else:
   q=ctx.inspect(x["inspected"],owned)
   need(q["State"]["Running"]is True and q["State"]["Pid"]>0 and q["HostConfig"].get("Devices",[])==[],
    "own live CPU observation")
  a=ctx.resources(x["resources"],root,i==0)
  if allocation is None:allocation=a
  need(a==allocation,"same actual CPU allocation through long phase")
 return allocation
def preflights(ctx,r,opts,npu,owned,cpu,co):
 c=ctx.core;root=ctx.m["root"];config=module(ctx.own["native_config_adapter.py"],"_mixed_terminal_config")
 cr=c.obj(cpu["report"]);nr=c.obj(npu["canary"])
 for x,mode in((cr,"cpu"),(nr,"n1")):
  need(x["schema"]=="kivi.actual-firstdecode-preflight/v1" and x["source"]==ctx.producer
   and x["mode"]==mode and x["model_ready"]is x["performance_ready"]is False,"actual source-bound preflight")
  config.validate_record(x["actual_engine_config"],ctx.m,mode)
 need(cr["status"]=="CPU_IMPORT_PARSER_CHECKED" and cr["canary"]==[]
  and nr["status"]=="N1_ALL4_TINY_CHECKED"
  and [(q["logical"],q["physical"],q["output"])for q in nr["canary"]]==[(i,i+4,[4.,5.])for i in range(4)],
  "actual CPU necessary invariants then all4 tiny and actual full config")
 for x,limit,cid in((cr,8*GIB,co["cid"]),(nr,64*GIB,owned["cid"])):
  ctx.memory.consume_memory(x["memory"],expected_limit=limit,container_id=cid)
 for value,mode,o,report in((c.obj(cpu["child"]),"cpu",co,cpu["report"]),
   (c.obj(npu["canary_child"]),"n1",owned,npu["canary"])):
  argv=ctx.c.docker_argv(o["cid"],[root+"/guest_probe.py","--execute","--mode",mode,
   "--source-manifest-sha256",ctx.producer["sha256"],"--output",report["path"],
   "--cache-bytes",str(6*GIB),"--port",opts.get("--port","8250")])
  c.child(value,argv)
ABI_HELPER_SHA="f94d81f163f0076e8243990dd687f7ec8d42ce1ed30d67eea3155bf1c3a073a4"
ABI_SOURCE_API="triton.runtime.driver.active.utils.get_device_properties(torch.npu.current_device())"
def driver_record(q,rank):
 need(type(rank)is int and rank in range(4) and q["schema"]=="kivi.actual-rank-driver-properties/v1"
  and type(q["logical_rank"])is type(q["current_device"])is int
  and q["logical_rank"]==q["current_device"]==rank,"same actual rank/device properties")
 helper=q["helper_source"]
 need(type(helper)is dict and set(helper)=={"path","bytes","sha256"}
  and type(helper["bytes"])is int and helper["bytes"]==2090 and helper["sha256"]==ABI_HELPER_SHA
  and helper["path"]=="/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py",
  "actual source-qualified installed helper Ref, not guessed torch properties")
 props=q["device_properties"]
 need(type(props)is dict and set(props)=={"num_aicore","num_vectorcore"}
  and all(type(v)is int and 0<v<=65535 for v in props.values()),"whole real driver counts, no defaults")
 need(q["source_api"]==ABI_SOURCE_API
  and all(type(q[k])is str and q[k] for k in("driver_type_module","driver_type_name","raw_properties_repr"))
  and len(q["raw_properties_repr"])<=16384,"actual original driver API and bounded whole representation")
 need(q["model_ready"]is q["performance_ready"]is q["run_authority"]is False,"ABI proof is not model success")
 return props
def capture_abi(ctx,r,recipe,recipe_ref,identities,canary):
 need(r["worker_first_fault_refs"]==[] and r["worker_first_fault"]is None,
  "first worker fault can never be promoted into successful mixed capture")
 need(type(canary)is list and len(canary)==len(identities)==4,"complete actual four ranks")
 out=[]
 for rank,identity in enumerate(identities):
  root=Path(recipe["diagnostic_root"])
  need(not (root/("RANK-%d-FATAL.json"%rank)).exists(),"preserved original worker fatal excludes success")
  rr=ctx.core.ref(root/("DRIVER-PROPERTIES-r%d.json"%rank));q=ctx.core.obj(rr)
  need(q["source_ref"]==ctx.producer and q["recipe_ref"]==recipe_ref and q["identity"]==identity,
   "properties from same actual initialized worker/source/recipe")
  props=driver_record(q,rank);pre=canary[rank]
  need(type(pre["logical"])is type(pre["physical"])is int and pre["logical"]==rank and pre["physical"]==rank+4,
   "actual N1 physical mapping")
  proof=pre["actual_driver_properties"]
  need(props==driver_record(proof,rank) and q["helper_source"]==proof["helper_source"]
   and q["driver_type_module"]==proof["driver_type_module"] and q["driver_type_name"]==proof["driver_type_name"],
   "same actual N1 and worker compiler/helper/core properties")
  out.append(rr)
 return out
def capture(ctx,rr,tr,peer,operation,command,args):
 c=ctx.core;r,rec=terminal(c,rr,tr,peer,operation,command,args,5400);unchanged(r,ctx)
 need(r["schema"]=="kivi.actual-mixed-owned-capture-host/v2"
  and r["status"]=="ALL16_CAPTURED_RELEASED_NUMERIC_PENDING" and r["phase_seconds"]==5400
  and r["whole176"]is r["full_model_correctness_verified"]is False and r["independent_raw_consumer_required"]is True,
  "actual capture scope, not numerical result")
 opts=host_binding(ctx,r,rec,"capture",rr);host=r["actual_host_process"]
 for key,flag in(("component","component"),("software","software"),("model_manifest","model-manifest"),("firstdecode_predecessor","firstdecode-args")):
  q=r[key];c.read(q);need(opts["--"+flag]==q["path"]and opts["--"+flag+"-sha256"]==q["sha256"],"actual capture argv "+flag)
 need(r["component"]==ctx.m["packed3_qualification_ref"] and r["model_manifest"]==ctx.m["model_manifest"],"same model/packed3 prerequisite")
 prerequisite=module(ctx.own["prerequisite.py"],"_mixed_terminal_packed3");prerequisite.consumed(r["component"],c.obj)
 pred=module(ctx.own["firstdecode_precondition.py"],"_mixed_terminal_firstdecode")
 pred.replay(ctx.c,ctx.m,r["firstdecode_predecessor"])
 sw=c.obj(r["software"])
 need(sw["source"]==ctx.producer and sw["successful"]is True and sw["tests"]==ctx.m["software_tests_declared"]
  and sw["NPU"]is sw["model_ready"]is False,"actual complete same-source software")
 npu=r["npu"];cpu=r["cpu"];owned=c.obj(npu["owned"]);co=c.obj(cpu["owned"])
 need(owned["source"]==co["source"]==ctx.producer and owned["arm"]=="candidate" and co["arm"]=="cpu-preflight"
  and npu["container"]==owned["cid"] and owned["cid"]!=co["cid"],"actual distinct CPU then TP4 owners")
 preflights(ctx,r,opts,npu,owned,cpu,co)
 cpu_stopped=ctx.cleanup(cpu["cleanup"],co,host["pid"])
 stopped=ctx.cleanup(npu["cleanup"],owned,host["pid"])
 need(c.utc(cpu_stopped["State"]["FinishedAt"])<=c.utc(stopped["State"]["StartedAt"])
  and c.utc(stopped["State"]["FinishedAt"])<=CUTOFF*10**9,"CPU before NPU and original absolute cutoff")
 need(0<c.utc(stopped["State"]["FinishedAt"])-c.utc(stopped["State"]["StartedAt"])<=5400*10**9,
  "actual NPU container lifetime within whole capture budget")
 recipe=c.obj(npu["recipe"]);need(recipe["source_ref"]==npu["source"]==ctx.producer
  and recipe["container_id"]==owned["cid"] and recipe["bits"]==2 and recipe["cache_bytes"]==6*GIB
  and recipe["image_id"]==ctx.c.IMAGE and recipe["run_authority"]is False,"same actual mixed recipe")
 owner=c.obj(recipe["external_owner_authority_ref"])
 need(owner["schema"]=="kivi.mixed.actual-owned-precondition/v2" and owner["source"]==ctx.producer
  and owner["container_id"]==owned["cid"] and owner["image"]==ctx.c.IMAGE
  and owner["physical_devices"]==[4,5,6,7] and owner["logical_to_physical"]=={str(i):i+4 for i in range(4)}
  and owner["guest_limit_bytes"]==64*GIB and owner["host_limit_bytes"]==512*1024**2
  and owner["portfolio_cutoff"]==CUTOFF and owner["canary_ref"]==npu["canary"] and owner["cpu_ref"]==cpu["report"],
  "actual owner and preconditions, not detached declaration")
 ctx.inspect(owner["owned_inspect_ref"],owned)
 root=Path(rr["path"]).parent;allocation=ctx.observation(owner["resource_ref"],owned,host["pid"],root,True)
 need(npu["observations"],"actual all-stage resource samples")
 proofs=[]
 for index,q in enumerate(npu["observations"]):
  x=c.obj(q)
  if index==0:
   need(q==owner["resource_ref"] and x["label"]=="model-preflight",
    "first exact owner pre-create resource Ref, not a borrowed initial floor")
   initial=True
  else:
   need(q!=owner["resource_ref"] and x["label"]in(
    "all4-N1","all4-N1-finished","model-startup",
    "kivi-real-all4-owner-bind","model-mixed-capture","model-after-mixed-capture"),
    "subsequent source-bound live model observation")
   initial=False
  need(ctx.observation(q,owned,host["pid"],root,initial)==allocation,"unchanged actual capture allocation")
  proofs.extend(x["actual_compute"])
 need(npu["worker_process_proofs"] and all(p in proofs for p in npu["worker_process_proofs"]),"actual all4 worker proof binding")
 need(x["label"]=="model-after-mixed-capture","source-defined final model observation")
 namespace_reader=module(ctx.m["runtime_roles"]["firstdecode_consumer"],"_mixed_terminal_predecessor_namespace")
 identities=namespace_reader.namespace(c.obj(npu["all4_namespace"]),recipe,owned,ctx.inspect,npu["worker_process_proofs"],host["pid"])
 driver_refs=capture_abi(ctx,r,recipe,npu["recipe"],identities,c.obj(npu["canary"])["canary"])
 client=c.obj(npu["client_report"])
 need(client["schema"]=="kivi.actual-mixed-all16-client/v2" and client["status"]=="ALL16_RAW_AND_NATIVE_FINAL_OBSERVED"
  and client["source_ref"]==ctx.producer and client["recipe_ref"]==npu["recipe"]
  and len(client["capture_receipt_refs"])==16 and len(client["rank_final_refs"])==4
  and client["rank_final_refs"]==npu["rank_final_refs"] and client["cpu_numeric_during_lease"]is False,
  "complete same real capture not scalar numerical substitute")
 need(client["rank_identities"]=={str(i):v for i,v in enumerate(identities)},"same actual mapped workers")
 ledger=c.obj(client["actual_resource_ledger"])
 need(ledger["actual"]is True and len(ledger["owners"])==4,"all actual owner geometry inputs")
 events=[];geometries=[]
 for q in ledger["owners"]:
  owner_layout=c.obj(q);capacity=c.obj(owner_layout["capacity_receipt_ref"])
  events.append(capacity["event_ref"]);geometries.append(owner_layout["field_geometry_refs"])
 fields=module(ctx.own["loader.py"],"_mixed_terminal_loader").geometry_modules(ctx.m)[1]
 accounting=module(ctx.m["runtime_roles"]["resource_ledger"],"_mixed_terminal_resource_ledger")
 actual_geometry=accounting.from_layouts(events,geometries,fields_module=fields,document=c.obj)
 need(ledger["ledger"]==accounting.ledger(actual_geometry)
  and ledger["ledger"]["retained_payload_and_declared_additional_bytes"]<=160*GIB,"actual source-derived raw shape budget")
 c.child(npu["client_child"],npu["client_argv"]);c.child(npu["server_child"],npu["server_argv"],False)
 for key,script in(("client_argv","client.py"),("server_argv","server_entry.py")):
  actual=npu[key];prefix=ctx.c.docker_argv(owned["cid"],[ctx.m["root"]+"/"+script,"--execute",
   "--source-manifest-sha256",ctx.producer["sha256"],"--recipe-ref-json"])
  need(actual[:len(prefix)]==prefix and c.obj(c.ref(actual[len(prefix)]))==npu["recipe"],"actual source/recipe entry "+key)
  suffix=(["--output",npu["client_report"]["path"],"--port",opts.get("--port","8250")]if key=="client_argv"
   else["--cache-bytes",str(6*GIB),"--port",opts.get("--port","8250")])
  need(actual==prefix+[actual[len(prefix)]]+suffix,"full original client/server literal argv")
 config=module(ctx.own["native_config_adapter.py"],"_mixed_terminal_config")
 production=c.obj(c.ref(Path(recipe["diagnostic_root"])/"ACTUAL-PRODUCTION-ENGINE-CONFIG.json"))
 config.validate_record(production,ctx.m,"server")
 need(production["source"]==ctx.producer and production["recipe_ref"]==npu["recipe"],"actual production factory receipt")
 frontend=c.obj(c.obj(npu["all4_namespace"])["frontend_ref"])
 need(production["actual_pid"]==frontend["pid"],"real API frontend factory PID")
 return dict(result=r,recipe=recipe,client=client,owned=owned,stopped=stopped,root=root,opts=opts,preflight_owned=co,
  actual_driver_qualification_refs=driver_refs)
def consume(ctx,request):
 c=ctx.core
 need(request["schema"]=="kivi.mixed-whole-terminal-input/v1" and request["source"]==ctx.producer,"explicit bounded original input recipe")
 cap=request["capture"];cpu=request["cpu"]
 captured=capture(ctx,cap["result"],cap["terminal"],cap["peer"],cap["operation"],cap["command"],cap["args"])
 r,rec=terminal(c,cpu["result"],cpu["terminal"],cpu["peer"],cpu["operation"],cpu["command"],cpu["args"],43200)
 unchanged(r,ctx);opts=host_binding(ctx,r,rec,"cpu-numeric",cpu["result"])
 need(r["schema"]=="kivi.actual-mixed-independent-cpu-host/v2" and r["status"]=="ALL16_CPU_CONSUMED_STOPPED_RETAINED"
  and r["CPU_phase_seconds"]==43200 and r["capture_result"]==cap["result"] and r["capture_original_terminal"]==cap["terminal"]
  and r["Devices"]==[] and r["NPU_release_claim"]is r["raw_deleted"]is False and r["exact_NPU_release_replayed"]is True,
  "actual separate CPU original result")
 for n,q in(("capture-result",cap["result"]),("capture-terminal",cap["terminal"])):
  need(opts["--"+n]==q["path"]and opts["--"+n+"-sha256"]==q["sha256"],"actual exact CPU capture input")
 need(opts["--capture-peer"]==cap["peer"]and opts["--capture-operation"]==cap["operation"]
  and opts["--capture-command"]==cap["command"]and c.decode(opts["--capture-args"])==cap["args"],"original CPU replays exact capture operation")
 for n,key in(("component","component"),("software","software"),("model-manifest","model_manifest"),("firstdecode-args","firstdecode_predecessor")):
  q=captured["result"][key];need(opts["--"+n]==q["path"]and opts["--"+n+"-sha256"]==q["sha256"],"same preconditions both phases")
 owned=c.obj(r["cpu_owned"])
 need(owned["cid"]not in(captured["owned"]["cid"],captured["preflight_owned"]["cid"]),"distinct independent CPU owner")
 stopped=cleanup_cpu(ctx,r["cpu_cleanup"],owned)
 c.raw_after_release(captured["stopped"],stopped)
 need(c.utc(stopped["State"]["FinishedAt"])<=CUTOFF*10**9,"original absolute CPU finish cutoff")
 need(0<c.utc(stopped["State"]["FinishedAt"])-c.utc(stopped["State"]["StartedAt"])<=43200*10**9,
  "actual CPU lifetime within independent budget")
 lease=c.obj(r["peer_lease"])
 need(lease["source_ref"]==ctx.producer and lease["owned_ref"]==r["cpu_owned"] and lease["Devices"]==[]
  and lease["actual_host_process"]==r["actual_host_process"] and lease["npu_ownership_claim"]is False,
  "own immutable peer snapshot only, not cross-paper concurrent permission")
 started=ctx.inspect(lease["started_inspect_ref"],owned)
 need(started["State"]["Running"]is True and started["State"]["Pid"]>0,"actual CPU initially live")
 c.raw_after_release(captured["stopped"],started)
 ctx.capture_root=captured["root"];root=Path(cpu["result"]["path"]).parent
 allocation=cpu_observations(ctx,r["observations"],owned,root)
 need(owned["guest_cpus"]==allocation["guest_cpus"][:1]and lease["cpu_allocation"]==allocation,"exact distinct host/guest1 CPU allocation")
 for key in("actual_memory_before","actual_memory_after"):
  q=c.obj(r[key]);need(q["source"]==ctx.producer,"CPU actual memory source")
  ctx.memory.consume_memory(q["actual_memory"],expected_limit=8*GIB,container_id=owned["cid"])
 before=c.obj(r["actual_memory_before"])["actual_memory"]
 after=c.obj(r["actual_memory_after"])["actual_memory"]
 ctx.memory.consume_memory(after,expected_limit=8*GIB,container_id=owned["cid"],namespace_pid=before["process"]["pid"])
 recipe=c.obj(r["offline_recipe"]);cr=captured["client"];npu=captured["result"]["npu"]
 need(recipe["producer_ref"]==ctx.producer and recipe["capture_plan_ref"]==captured["recipe"]["capture_plan_ref"]
  and recipe["capture_receipt_refs"]==cr["capture_receipt_refs"] and recipe["rank_final_refs"]==cr["rank_final_refs"]
  and recipe["rank_identities"]==cr["rank_identities"] and recipe["cpu_owned_ref"]==r["cpu_owned"]
  and recipe["npu_cleanup_ref"]==npu["cleanup"] and recipe["npu_owned_ref"]==npu["owned"]
  and recipe["actual_host_pid"]==captured["result"]["actual_host_process"]["pid"]
  and recipe["portfolio_cutoff_epoch"]==CUTOFF and recipe["cpu_deadline_epoch"]<=CUTOFF,"whole same raw offline recipe")
 child=c.obj(r["child"]);leaf=Path(r["independent_result"]["path"]).parent
 argv=ctx.c.docker_argv(owned["cid"],[ctx.m["root"]+"/cpu_entry.py","--execute","--source-manifest-sha256",
  ctx.producer["sha256"],"--recipe",r["offline_recipe"]["path"],"--recipe-sha256",r["offline_recipe"]["sha256"],"--output-dir",str(leaf)])
 c.child(child,argv)
 output=c.obj(r["independent_result"])
 need(output["schema"]=="kivi.mixed-offline-numeric-components/v2"
  and output["status"]=="ALL16_STAGES_NUMERIC_AND_SCALAR_CONSUMED_AFTER_RELEASE"
  and output["producer_ref"]==ctx.producer and len(output["stage_result_refs"])==len(output["stage_CPU_seconds"])==16
  and all(finite(v,0,43200)for v in output["stage_CPU_seconds"])
  and sum(output["stage_CPU_seconds"])<=r["elapsed_seconds"],"actual all16 bounded independent numeric child")
 markers=[]
 for line in c.read(child["stdout_ref"],allow_empty=True).decode().splitlines():
  try:v=c.decode(line)
  except(ValueError,TypeError):continue
  if type(v)is dict and set(v)=={"result","status"}:markers.append(v)
 need(markers==[dict(result=r["independent_result"],status=output["status"])],"real independent child stdout binds complete matrix")
 for key in("raw_deleted","model_ready","performance_ready","run_authority","cleanup_authority"):
  need(output[key]is False,"numeric component cannot grant broader scope "+key)
 roles=ctx.m["runtime_roles"]
 offline=module(roles["offline_consume"],"_mixed_terminal_offline_pins")
 need(recipe["source_refs"]=={n:roles[n]for n in offline.ROLES}
  and all(roles[n]["sha256"]==offline.ROLE_SHA[n]for n in offline.ROLES),"all exact independent source pins")
 for key,role in(("installer_sha256","installer"),("capture_sha256","provenance"),("observer_sha256","stage_observer")):
  need(recipe[key]==roles[role]["sha256"],"same actual raw writer/capture source "+key)
 expected_release=ctx.release.before_numeric(ctx,core=c,core_ref=roles["release_core"],
  npu_cleanup_ref=npu["cleanup"],npu_owned_ref=npu["owned"],host_pid=recipe["actual_host_pid"],
  cpu_inspect_ref=recipe["cpu_started_inspect_ref"],cpu_owned_ref=r["cpu_owned"])
 need(output["release_replay"]==expected_release,"actual original release before all numerics")
 mods={n:module(roles[n],"_mixed_terminal_"+n)for n in("capture_receipt","stage_consumer","stage_lifecycle","bindings","assignment_oracle","matrix_consumer")}
 replay=mods["matrix_consumer"].consume(output["stage_result_refs"],cr["rank_final_refs"],recipe["capture_plan_ref"],
  capture_receipt_refs=cr["capture_receipt_refs"],capture_reader=mods["capture_receipt"],stage_reader=mods["stage_consumer"],
  life=mods["stage_lifecycle"],bindings=mods["bindings"],oracle=mods["assignment_oracle"],
  source_refs=recipe["source_refs"],installer_sha256=recipe["installer_sha256"])
 need(replay==output["matrix"],"independent complete selected matrix/all64 native lifecycle rejoin")
 return dict(schema="kivi.actual-mixed-whole-terminal-consumed/v1",
  status="SELECTED_MIXED_NUMERIC_AND_ALL64_LIFECYCLE_WHOLE_CONSUMED",
  source=ctx.producer,capture_original_terminal=cap["terminal"],cpu_original_terminal=cpu["terminal"],
  capture_result=cap["result"],cpu_result=cpu["result"],independent_result=r["independent_result"],
  MAIN_original_operations_verified=True,actual_NPU_released_before_CPU=True,
  actual_driver_qualification_refs=captured["actual_driver_qualification_refs"],
  CPU_no_NPU_idle_requirement=True,CPU_stopped_retained=True,protected0_3_checked_at_capture_release=True,
  full_selected_FA64_checked=True,numeric_frames=320,whole_output_rows=576,
  full_output_elements_per_row=1536,all64_owner_native_lifecycle_checked=True,
  cross_paper_joint_admission_verified=False,raw_deleted=False,
  model_ready=False,performance_ready=False,run_authority=False,cleanup_authority=False,
  full_model_correctness_verified=False,graph_checked=False,GDN_numerically_checked=False,
  uncovered=replay["uncovered"])
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 p.add_argument("--input");p.add_argument("--input-sha256");p.add_argument("--source");p.add_argument("--source-sha256")
 p.add_argument("--output")
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return
 src=dict(path=a.source,bytes=Path(a.source).stat().st_size,sha256=a.source_sha256)
 ctx=context(src);request=ctx.core.obj(dict(path=a.input,sha256=a.input_sha256))
 result=consume(ctx,request)
 rr=ctx.c.write(Path(a.output),result)
 print(json.dumps(dict(result=rr,status=result["status"])),flush=True)
if __name__=="__main__":main()
