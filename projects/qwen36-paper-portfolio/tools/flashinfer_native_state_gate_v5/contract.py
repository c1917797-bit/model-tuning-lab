"""Source/protocol/evidence contracts; software cannot sign device success."""
from __future__ import annotations
import hashlib,json,math,os,re
from datetime import datetime,timezone
from pathlib import Path
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
ROOT=Path(__file__).resolve().parent
D,H,N,CHUNK,PARTS,STEPS=256,6,384,128,3,160
LIMITS={"relative_rms":.005,"cosine":.99998,"max_abs":.00303,"lse_max_abs":.00303}
MODES=(("eager",0),("graph",0),("graph",1),("graph",2))
CUT="2026-10-09T11:17:31+00:00"
OWN=("contract.py","oracle.py","native.py","numerics.py","main.py","consumer.py","test_software.py","host.py","READY.md")
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
 digest=hashlib.sha256()
 with p.open("rb") as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
 return digest.hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def bound(path,digest):
 p=Path(path);require(p.is_absolute() and ".." not in p.parts and re.fullmatch("[a-f0-9]{64}",digest or ""),"absolute SHA-bound Ref")
 require(sha(p)==digest,"actual bytes changed: "+str(p))
 return {"path":str(p),"sha256":digest}
def load_ref(r):
 require(set(r)=={"path","sha256"},"exact Ref fields")
 bound(r["path"],r["sha256"]);return json.loads(Path(r["path"]).read_bytes())
def write_new(p,x):
 raw=canonical(x)+b"\n"
 with Path(p).open("xb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return {"path":str(p),"sha256":sha(p)}
DEPENDENCIES={
 "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py":"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py":"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py":"86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"}
def source_identity(path,digest):
 r=bound(path,digest);m=load_ref(r)
 require(m.get("schema")=="flashinfer.native-state-sources/v5" and m.get("default_enabled") is False and m.get("npu_executed") is False and set(m.get("files",{}))==set(OWN),"complete new source closure")
 actual={name:sha(ROOT/name) for name in OWN}
 require(actual==m["files"],"current authored source drift")
 require(m.get("dependencies")==DEPENDENCIES and m.get("source_count")==12,"actual9 own +3 pinned generic dependencies")
 for p,s in DEPENDENCIES.items():bound(p,s)
 return r,actual
def protocol():
 return {"schema":"flashinfer.native-state-protocol/v5","paper":"2501.01005",
   "mechanism":"exact normalized partial attention states plus natural-log LSE composition",
   "native_partial":"old-FIA BNSD BF16 softmax_lse_flag=True",
   "native_merge":"npu_attention_update update_type0; no native tiling optimality claim",
   "batch_sizes":list(range(1,17)),"query_widths":[1,4],"head_count":H,"kv_heads":1,"head_dim":D,
   "capacity_tokens":N,"chunk_tokens":CHUNK,"partitions":PARTS,"steps":STEPS,
   "modes":[list(x) for x in MODES],"limits":LIMITS,"single_local_KV_head_only":True,
   "empty_domain":"zero output/natural -inf LSE; original undefined native values retained on failure",
   "native_undefined_padding_rewritten":False,"model_consumer_verified":False}
def query_counts(batch,qmax,step):
 require(1<=batch<=16 and qmax in (1,4) and 0<=step<STEPS,"fixed complete protocol coordinates")
 return [((0,1,1,1,0,1,1,1)[(step+b)%8] if qmax==1 else (0,1,4,2,0,3,1,4)[(step+b)%8]) for b in range(batch)]
class SlotBook:
 """Real numerical allocator row lifecycle, NOT a vLLM scheduler bridge."""
 def __init__(self,batch):
  self.total=batch+3;self.rows=[dict(rid="initial-"+str(i),generation=0,length=(0,1,63,127,128,129,255,256,257,383)[i%10]) for i in range(self.total)]
 def advance(self,batch,qmax,step):
  reset=(step//16)%self.total if step in (64,112) else None
  if reset is not None:
   row=self.rows[reset];row.update(rid="reuse-"+str(step),generation=row["generation"]+1,length=0)
  slots=[(step+b)%self.total for b in range(batch)];counts=query_counts(batch,qmax,step);writes=[]
  for b,(slot,count) in enumerate(zip(slots,counts)):
   row=self.rows[slot]
   if row["length"]+count>N:
    require(reset is None or reset!=slot,"duplicate same-step reset")
    row.update(rid="capacity-reuse-"+str(step)+"-"+str(slot),generation=row["generation"]+1,length=0)
    writes.append({"slot":slot,"reset":True,"start":0,"count":0})
   start=row["length"]
   if count:writes.append({"slot":slot,"reset":False,"start":start,"count":count});row["length"]+=count
  if reset is not None:writes.insert(0,{"slot":reset,"reset":True,"start":0,"count":0})
  return {"slots":slots,"counts":counts,"rows":[dict(self.rows[s]) for s in slots],"writes":writes,"explicit_reset_slot":reset}
def visible_lengths(frame,qmax):
 result=[]
 for row,count in zip(frame["rows"],frame["counts"]):
  result.append([row["length"]-count+q+1 if q<count else 0 for q in range(qmax)])
 return result
def metric(actual,expected):
 require(len(actual)==len(expected)>0,"independent per-head metric width")
 if not all(math.isfinite(float(x)) for x in list(actual)+list(expected)):return {"finite":False,"passed":False}
 aa=math.fsum(float(x)**2 for x in actual);ee=math.fsum(float(x)**2 for x in expected)
 err=math.fsum((float(a)-float(e))**2 for a,e in zip(actual,expected))
 ma=max(abs(float(a)-float(e)) for a,e in zip(actual,expected))
 if ee==0:return {"finite":True,"relative_rms":None,"cosine":None,"max_abs":ma,"zero_reference":True,"passed":err==0}
 rel=math.sqrt(err/ee);cos=math.fsum(float(a)*float(e) for a,e in zip(actual,expected))/math.sqrt(aa*ee) if aa>0 else None
 return {"finite":True,"relative_rms":rel,"cosine":cos,"max_abs":ma,"zero_reference":False,
   "passed":cos is not None and rel<=LIMITS["relative_rms"] and cos>=LIMITS["cosine"] and ma<=LIMITS["max_abs"]}
def expected_launch_argv(p,launch_ref):
 require(type(launch_ref) is dict and set(launch_ref)=={"path","sha256"},"actual immutable launch byte Ref required; SHA is never optional")
 bound(launch_ref["path"],launch_ref["sha256"])
 require(Path(launch_ref["path"]).read_bytes()==canonical(p)+b"\n","actual canonical launch bytes equal loaded proof")
 template=p.get("image_python_argv_template")
 require(type(template) is list and template.count("@ACTUAL_LAUNCH_SHA256@")==1 and
   template.index("@ACTUAL_LAUNCH_SHA256@")>0 and template[template.index("@ACTUAL_LAUNCH_SHA256@")-1]=="--launch-proof-sha256","single explicit SHA placeholder position, never argv substring")
 actual_sha=launch_ref["sha256"]
 return [actual_sha if v=="@ACTUAL_LAUNCH_SHA256@" else v for v in template]
def inspect_row(ref):
 rows=load_ref(ref)
 if "stdout" in rows:rows=json.loads(rows["stdout"])
 require(type(rows) is list and len(rows)==1,"one complete original exact CID inspect")
 return rows[0]
def validate_cpu_phase(e,cid,source,files):
 require(re.fullmatch("[a-f0-9]{64}",cid or ""),"actual complete independent CPU-only CID")
 owned=load_ref(e["cpu_only_owned"]);live=inspect_row(e["cpu_only_inspect"]);stopped=inspect_row(e["cpu_stopped_inspect"])
 require(owned.get("cid")==cid and owned.get("mode")=="cpu" and owned.get("source")==source and
   owned.get("host_sha256")==files["host.py"],"actual own source-bound CPU-only role")
 from host import validate_inspect
 validate_inspect(live,owned);validate_inspect(stopped,owned)
 require(not (live["HostConfig"].get("Devices") or []) and live["State"]["Running"] is True and live["State"]["Pid"]>0,
  "original actual CPU-only inspected live guest: no device nodes/remaps")
 require(not stopped["State"]["Running"] and stopped["State"]["Pid"]==0 and not stopped.get("ExecIDs") and
  not stopped["State"].get("OOMKilled",False),"actual CPU-only stopped-retained process/no OOM")
 cleanup=load_ref(e["cpu_only_cleanup"])
 require(cleanup["container"]==cid and cleanup["stopped"] is True and cleanup["retained"] is True and cleanup["deleted"] is False and
  cleanup["errors"]==[] and cleanup["primary_error"] is None and cleanup["after_inspect"]==e["cpu_stopped_inspect"],
  "original CPU-only exact own stop-retain/primary-secondary closure")
 stop=load_ref(cleanup["stop_receipt"])
 require(stop["requested_argv"]==["/usr/bin/docker","stop","--time","15",cid] and stop["exit_code"]==0,
  "original precise CPU-only stop terminal, no rm/global stops")
 return live,stopped
def validate_no_device_abi(r,source,files):
 require(r.get("schema")=="flashinfer.no-device-native-abi/v5" and r.get("status")=="actual-schema-checked" and
  r.get("source_manifest")==source and r.get("sources_before")==r.get("sources_after")==files and
  r.get("script_sha256")==files["main.py"] and r.get("native_script_sha256")==files["native.py"],
  "actual complete this-source no-device ABI receipt required")
 require(r.get("npu_executed") is False and r.get("device_initialized_before") is False and r.get("device_initialized_after") is False and
  r.get("actual_guest_device_nodes_before")==[] and r.get("actual_guest_device_nodes_after")==[] and r.get("device_inventory_before")==[] and r.get("device_inventory_after")==[] and r.get("primary_error") is None and r.get("secondary_errors")==[],
  "actual no-device phase must remain no-process/no-context, not numerical PASS")
 require(r.get("image_id")==IMAGE and r.get("cgroup",{}).get("value")==8*1024**3 and
  type(r.get("affinity")) is list and len(r["affinity"])==1,"actual no-device owned guest CPU/memory")
 stack=r.get("actual_stack",{})
 require(stack.get("vllm_ascend")=="0.23.0" and stack.get("cann")=="9.1.0" and stack.get("torch") and stack.get("torch_npu"),
  "actual no-device deployed stack versions")
 from native import OPS,required_schema
 require(set(r.get("actual_exports",{}))=={n+"."+o for n,o in OPS},"all four actual native schemas, no partial ABI")
 for name,overload in OPS:
  row=r["actual_exports"][name+"."+overload]
  require(set(row["arguments"])>=required_schema(name,overload) and
    row["sha256"]==hashlib.sha256(row["schema"].encode()).hexdigest(),"original schema bytes and required actual args")
  require(row["return_types"]==(["Tensor"] if name.startswith("_npu_fused") else ["Tensor","Tensor"]),"actual native return arity")
  if overload=="out":require(re.search(r"Tensor\[\]\s+out\b",row["schema"]) is not None,"actual FIA Tensor[] out list required")
 sources=r.get("actual_runtime_sources",{})
 require(set(sources)=={"attention_cp","common_cp","torch_npu_library","vllm_ascend_library","cann_version","cann_env"},
  "actual no-device exact installed CP/native/CANN source inventory")
 for ref in sources.values():
  require(set(ref)=={"path","sha256"} and Path(ref["path"]).is_absolute() and ".." not in Path(ref["path"]).parts and
   re.fullmatch("[a-f0-9]{64}",ref["sha256"]),"actual no-device absolute source SHA Ref")
 native=sources["torch_npu_library"]
 require(r.get("actually_mapped_libraries",{}).get(native["path"])==native["sha256"],"actual no-device imported mapped TorchNPU library")
 require(type(r.get("actual_argv")) is list and r["actual_argv"][:2]==["/usr/local/python3.12.13/bin/python3","-B"] and
  r["actual_argv"][2:]==[str(ROOT/"main.py"),"--no-device-abi","--source-manifest",source["path"],
   "--source-manifest-sha256",source["sha256"],"--output-dir","/flashinfer-results"],
  "actual no-device exact source-bound Python CLI before context")
 return r
def validate_launch(p,source,files,argv,launch_ref=None,now=None):
 require(p.get("schema")=="portfolio.native-device-launch/v1" and p.get("image_id")==IMAGE and re.fullmatch("[0-9a-f]{64}",p.get("container_id","")),"MAIN fresh exact owned launch proof required")
 require(p.get("physical_devices")==[6] and p.get("logical_to_physical")=={"0":6} and p.get("memory_cgroup_bytes")==8*1024**3 and p.get("guest_cpu_budget")==1,"exact single6to0/8GiB/1CPU")
 expected=expected_launch_argv(p,launch_ref)
 require(p.get("source_manifest")==source and p.get("sources")==files and expected==argv,"this actual source/script/full CLI including canonical immutable launch SHA")
 require(all(p.get(k) is True for k in ("fresh_idle_verified","source_canary_passed","nonprivileged","actual_effective_cgroup_cpu_verified")),"actual prerequisites pending cannot dispatch")
 stack=p.get("stack");require(type(stack) is dict and stack.get("vllm_ascend")=="0.23.0" and stack.get("cann")=="9.1.0" and stack.get("torch_npu"),"explicit deployed stack versions")
 require(set(p.get("stack_source_refs",{}))>={"attention_cp","common_cp","torch_npu_library"},"deployed CP/native library source pins")
 for alias,pair in p["stack_source_refs"].items():
  require(set(pair)=={"runtime_ref","snapshot_ref"},"dual runtime/host-readable snapshot Ref")
  rr,sr=pair["runtime_ref"],pair["snapshot_ref"]
  require(set(rr)==set(sr)=={"path","sha256"} and rr["sha256"]==sr["sha256"] and re.fullmatch("[a-f0-9]{64}",rr["sha256"]),"same actual runtime/snapshot bytes")
  require(Path(rr["path"]).is_absolute() and ".." not in Path(rr["path"]).parts,"absolute runtime source path")
  bound(sr["path"],sr["sha256"])
 require(type(p.get("evidence")) is dict and set(p["evidence"])>={"inspect","resources","protected","canary","guest_cpu","canary_child","no_device_abi","no_device_child","post_no_device_idle","cpu_only_inspect","cpu_only_owned","cpu_only_cleanup","cpu_stopped_inspect"},"original complete host evidence Refs")
 for r in p["evidence"].values():load_ref(r)
 inspected=load_ref(p["evidence"]["inspect"])
 if "stdout" in inspected:inspected=json.loads(inspected["stdout"])
 require(type(inspected) is list and len(inspected)==1,"original exact container inspect array")
 x=inspected[0];hc=x["HostConfig"];cfg=x["Config"]
 require(x["Id"]==p["container_id"] and x["Image"]==IMAGE and x["State"]["Running"] is True and x["State"]["Pid"]>0 and
    hc["Privileged"] is False and hc["Memory"]==8*1024**3 and hc["MemorySwap"]==8*1024**3 and hc["NanoCpus"]==10**9 and
    hc["NetworkMode"]=="none" and hc["IpcMode"]=="private" and hc["ShmSize"]==2*1024**3 and hc["PidsLimit"]==512 and set(hc.get("CapDrop") or [])=={"ALL"} and set(hc.get("SecurityOpt") or [])=={"no-new-privileges"} and
    not hc.get("DeviceRequests") and not hc.get("DeviceCgroupRules"),"actual current owned isolation/budget")
 require(p.get("owner")=="flashinfer-native-state-v5" and cfg["Labels"].get("model-tuning-lab.owner")==p["owner"] and
    cfg["Labels"].get("model-tuning-lab.source-manifest-sha256")==source["sha256"] and cfg["Labels"].get("model-tuning-lab.controller-sha256")==files["host.py"],"new source-bound owner; no H8/old canary borrow")
 devices=hc["Devices"];wanted={"/dev/davinci6":"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager","/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
 require(len(devices)==4 and {v["PathOnHost"]:v["PathInContainer"] for v in devices}==wanted and
    all(v["CgroupPermissions"]=="rwm" for v in devices),"actual inspect single6to0 device identity")
 no_device=validate_no_device_abi(load_ref(p["evidence"]["no_device_abi"]),source,files)
 require(no_device["actual_stack"]==stack and all(no_device["actual_runtime_sources"].get(alias)==pair["runtime_ref"]
   for alias,pair in p["stack_source_refs"].items()),"pre-device ABI stack/source must match actual fresh canary")
 nd_child=load_ref(p["evidence"]["no_device_child"])
 cpu_live,cpu_stopped=validate_cpu_phase(p["evidence"],p["cpu_container_id"],source,files)
 require(p["cpu_container_id"]!=p["container_id"] and datetime.fromisoformat(cpu_stopped["State"]["FinishedAt"].replace("Z","+00:00"))<=datetime.fromisoformat(x["State"]["StartedAt"].replace("Z","+00:00")),"actual CPU stop-retain finishes before distinct NPU guest starts")
 expected_nd=["/usr/bin/docker","exec",p["cpu_container_id"],"/bin/bash","-c",
  'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kvbp-diagnostic",*no_device["actual_argv"]]
 require(nd_child.get("exit_code")==0 and nd_child.get("requested_argv")==expected_nd and
  nd_child.get("argv")==["/usr/bin/prlimit","--as=unlimited","--",*expected_nd],
  "original successful no-device Docker-only AS child exact actual CLI")
 require(type(nd_child.get("observed_utc")) is str,"original no-device child completion time")
 canary=load_ref(p["evidence"]["canary"])
 require(canary.get("fresh_canary_passed") is True and canary.get("source_manifest")==source and
    canary.get("sources_before")==files and canary.get("sources_after")==files,"fresh actual this-source canary")
 require(canary.get("script_sha256")==files["host.py"] and canary.get("stack")==stack and canary.get("stack_source_refs")==p["stack_source_refs"] and canary.get("no_device_abi")==p["evidence"]["no_device_abi"] and canary.get("preinit_actual_exports")==no_device["actual_exports"],"actual new canary/stack/controller linkage")
 require(datetime.fromisoformat(nd_child["observed_utc"])<=datetime.fromisoformat(canary["created_utc"]),"actual no-device child must complete before canary")
 child=load_ref(p["evidence"]["canary_child"])
 require(child.get("exit_code")==0 and child.get("child_termination_observed") is True and child.get("physical_pid_proofs"),"original actually terminated fresh canary")
 require(all(v["stage"]=="canary" and v["namespace_pids"][-1]==canary["pid"] and v["physical"]==6 and p["container_id"] in v["cgroup"] for v in child["physical_pid_proofs"]),"actual this-canary physical6 PID evidence")
 cpu=load_ref(p["evidence"]["guest_cpu"]);res=load_ref(p["evidence"]["resources"])["resources"];protected=load_ref(p["evidence"]["protected"])
 require(cpu["effective_capacity"]==1 and cpu["effective_cpus"]==[res["cpu_allocation"]["guest_cpu"]] and hc["CpusetCpus"]==str(cpu["effective_cpus"][0]),"actual guest effective CPU quota/cpuset")
 require(res["ordinary_floor_bytes"]==int((8+8+.25)*1024**3) and res["memory"]["MemAvailable"]>=res["ordinary_floor_bytes"] and res["host_cpu"]["effective_capacity"]>=1 and res["daemon_cpu"]["effective_capacity"]>=3,"actual ordinary RAM/effective host-daemon CPU admission")
 require(set(protected["processes"])=={"0","1","2","3"},"complete protected0..3 baseline")
 t=datetime.fromisoformat(p["preflight_utc"].replace("Z","+00:00"));now=now or datetime.now(timezone.utc)
 require(t.tzinfo and 0<=(now-t).total_seconds()<=600,"fresh <=600s actual launch")
 require(now<datetime.fromisoformat(CUT),"fixed portfolio cutoff")
 return p
def metric_record(m):
 require(m.get("finite") is True and m.get("passed") is True,"original finite metric result")
 if m.get("zero_reference") is True:
  require(m.get("max_abs")==0,"zero-domain/reference requires exact zero")
 else:
  for k in ("relative_rms","cosine","max_abs"):
   require(type(m.get(k)) in (int,float) and math.isfinite(m[k]),"complete finite metric "+k)
  require(m["relative_rms"]<=LIMITS["relative_rms"] and m["cosine"]>=LIMITS["cosine"] and m["max_abs"]<=LIMITS["max_abs"],"original per-query/head numerical bounds")
def validate_cases(report,read_case=load_ref):
 require(report.get("schema")=="flashinfer.native-state-numerics/v5" and report.get("status")=="passed" and report.get("protocol")==protocol(),"actual complete new numerical report")
 cases=report["cases"];wanted={(b,q,m,t) for b in range(1,17) for q in (1,4) for m,t in MODES}
 require(len(cases)==128 and {(c["batch"],c["query_width"],c["mode"],c["trial"]) for c in cases}==wanted,"128 exact B/q/eager/graph cases")
 guards=("guards","pointers","input_immutable","cache_bitwise","untouched_slots_bitwise","reuse_zeroed","empty_output_zero","empty_lse_neginf","native_defined_finite","partial_defined_finite","merge_finite")
 count=0
 for header in cases:
  c=read_case(header["actual_case_ref"]) if "actual_case_ref" in header else header
  require(all(c[k]==header[k] for k in ("batch","query_width","mode","trial")),"actual case Ref coordinates")
  require(c["status"]=="passed" and len(c["steps"])==STEPS,"160 actual changing steps per case")
  book=SlotBook(c["batch"])
  for i,row in enumerate(c["steps"]):
   require(row["step"]==i+1 and row["frame"]==book.advance(c["batch"],c["query_width"],i),"original schedule/lease/generation/write replay")
   require(all(row.get(k) is True for k in guards),"complete per-step cache/state/guard predicates")
   metrics=row["per_query_head_metrics"]
   require(len(metrics)==c["batch"]*H*c["query_width"],"all head/query/request independent gates, never GQA mean")
   for m in metrics:metric_record(m)
   native=row["native_full_per_query_head_metrics"]
   require(len(native)==len(metrics),"original native full control domain")
   for m in native:metric_record(m)
   require(type(row["native_lse_max_abs"]) in (int,float) and math.isfinite(row["native_lse_max_abs"]) and row["native_lse_max_abs"]<=LIMITS["lse_max_abs"],"original native LSE bound")
   require(type(row["lse_max_abs"]) in (int,float) and math.isfinite(row["lse_max_abs"]) and row["lse_max_abs"]<=LIMITS["lse_max_abs"],"natural LSE per-head bound")
   require(row["native_undefined_padding_rewritten"] is False,"preserve raw native undefined padding")
   require(re.fullmatch("[a-f0-9]{64}",row["raw_step"]["sha256"]) and row["raw_step"]["bytes"]>0 and row["raw_step"]["retained"] is False,"original raw checkpoint/completed owned deletion identity")
   count+=1
 require(count==20480,"full 20480-step matrix")
 return {"changing_feedback_steps":count,"cases":128,"numerical_component_checked":True,
   "actual_MAIN_operation_authority_verified":False,"serving_ready":False,"model_lifecycle_verified":False,
   "matched1024_e2e_verified":False,"final2048_task_verified":False}
