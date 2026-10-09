"""Whole-original MAIN host/model consumer, OFF by default; stdlib, no Torch.
Component full128/20480 prerequisite is replayed, never inherited from partial011.
Every real turn/all16 FA and48 GDN, actual allocation/mixed/reuse/FULL is consumed.
No active-state equality across free-running candidate/dense is invented.
"""
import argparse,json,re,math
from pathlib import Path
import source_contract as c,gdn_source,gdn_state,gdn_stream,ann_fa_consumer as fa_model_numeric,allocator_coverage
from original_terminal import original_terminal
PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
import identity_bridge
def event(ref,source,component):
 x=c.obj(ref)
 c.require(x["schema"]=="sparq.actual-full-model-observation/v3" and x["source"]==source and
  x["rank"] in range(4) and x["kernel_authority"]==dict(source_manifest=component["source_manifest"],
   original_terminal=component["original_terminal"]),"whole actual layer event/source/29source-original component")
 return x
def consume_trace(index_ref,source,component):
 index=c.obj(index_ref);trace=Path(index["trace_root"])
 c.require(index["schema"]=="sparq.actual-entire-model-trace/v1" and index["source"]==source and
  trace.is_dir() and trace.resolve()==trace and Path("/cache/cch") in trace.parents and index["sampled"] is False,
  "actual entire immutable owned model trace inventory")
 import wire
 http=wire.http(index["http"],index["arm"]);seen_requests={r:set() for r in range(4)};forwarded={r:{} for r in range(4)}
 all_refs=[]
 for part in index["chunks"]:
  page=c.obj(part);c.require(page["source"]==source and page["trace_root"]==str(trace),"complete trace page source")
  all_refs.extend(page["events"])
 all_json=sorted(p.name for p in trace.glob("rank*.json"))
 c.require(all_json==sorted(Path(r["path"]).name for r in all_refs) and len(all_json)>0 and
  len(all_json)==len(set(all_json)),"entire actual layer/turn trace, no removed or sampled records")
 events={};sequences={r:[] for r in range(4)};workers={};boundaries={r:[] for r in range(4)}
 for ref in all_refs:
  p=Path(ref["path"]);c.require(p.parent==trace,"exact actual top-level trace event")
  match=re.fullmatch(r"rank([0-3])-([0-9]{8})-([a-z0-9-]+)\.json",p.name)
  c.require(match is not None,"actual producer event filename/rank/kind/counter")
  rank=int(match.group(1));sequences[rank].append(int(match.group(2)))
  x=event(ref,source,component);c.require(x["rank"]==rank and x["kind"]==match.group(3),"actual whole event not renamed")
  events[p.name]=(None,ref) # Keep exact Ref only; do not retain every full FA/GDN payload in 8GiB CPU checker.
  if x["kind"]=="actual-rank-worker":
   c.require(rank not in workers,"one real worker per TP rank");workers[rank]=x["value"]
  if x["kind"]=="actual-model-boundary":boundaries[rank].append(ref)
 for rank,seq in sequences.items():
  c.require(sorted(seq)==list(range(1,len(seq)+1)),"every event counter for actual rank, no holes/truncation")
  w=workers.get(rank)
  c.require(w is not None,"actual worker record required")
  identity_bridge.validate_worker_flag(w["common_identity_flag"])
  c.require(w["rank"]==w["logical_device"]==rank and w["world_size"]==4 and
   type(w["namespace_pid"]) is int and w["namespace_pid"]>0 and w["actual_proc_argv"],
   "actual TP4 rank/logical-device/PID/argv source record")
 def read(ref,kind,rank):
  x=event(ref,source,component);p=Path(ref["path"])
  c.require(p.name in events and events[p.name][1]==ref and x["kind"]==kind and x["rank"]==rank,
   "entire actual current layer Ref belongs to same full inventory")
  return x["value"]
 import hashlib
 evidence_digest=hashlib.sha256();checked_turn_count=0;active_observation_count=0
 coverage=allocator_coverage.Coverage();full_epochs={r:0 for r in range(4)};numpy_dependency=None
 for rank in range(4):
  for boundary_ref in sorted(boundaries[rank],key=lambda x:Path(x["path"]).name):
   b=read(boundary_ref,"actual-model-boundary",rank)
   c.require(set(b["gdn"])=={str(i) for i in gdn_state.GDN},"all actual48 native GDN layers for EVERY model boundary")
   states=[read(b["gdn"][str(i)],"actual-gdn-state",rank) for i in gdn_state.GDN]
   checker_ref=c.bound(c.ROOT/"gdn_stream.py",c.obj(source)["files"]["gdn_stream.py"])
   c.require(all(x.get("schema")==gdn_stream.PROTOCOL for x in states),"current model authority requires NEW complete all-row live-byte/finite protocol")
   checked=[gdn_state.consume(x,gdn_source.sources(),checker_ref,source) for x in states]
   for check in checked:
    if numpy_dependency is None:numpy_dependency=check["numpy_dependency"]
    c.require(check["numpy_dependency"]==numpy_dependency,"same actual observed NumPy source across all4/all48/all epochs")
   active=[]
   for x in states:
    for s in x["states"]:
     domain=next(z for z in checked if z["layer"]==x["layer"])["writer_domain"]["written_slots"][s["name"]]
     observations=s["active_slots"];record=s["live_check"]
     c.require([z["slot"] for z in observations]==domain and s["active_state_dense_equivalence_not_asserted"] is True and
      record["all_after_finite"] is True and record["all_inactive_exact"] is True,
      "complete actual active AND inactive finite/full-byte coverage")
     for z in observations:
      active.append(dict(layer=x["layer"],state=s["name"],slot=z["slot"],
       bitwise_changed=z["bitwise_changed"],after_finite=z["after_finite"],
       changed_is_observation_not_extra_algorithm_gate=True,
       exact_original_byte_streams={k:record[k] for k in ("original_before_stream_sha256","original_after_stream_sha256")},
       postmortem_success_raw_replay_claimed=False))
   if b["runtime"]=="FULL":
    c.require(set(b["fa"])=={str(i) for i in range(3,64,4)} and b["mixed_FA_records"]=={},
     "all actual16 FA conditional output rows, not capture-time Python calls")
    fas=[]
    for i in range(3,64,4):
     x=read(b["fa"][str(i)],"actual-full-ann-oracle",rank)
     c.require(x["model_epoch"]==b["epoch"] and x["batch"]==b["batch"] and
      x.get("complete_online_full_qKV_literal_FP64") is True and x.get("postmortem_full_qKV_replay") is False,"actual own full-qKV online literal/FP64 independent oracle, not postmortem full-cache replay")
     y=fa_model_numeric.consume(x);c.require(y["passed"],"unchanged actual full-row FP64 PA output metric failed")
     fas.append(y)
    full_epochs[rank]+=1
   else:
    c.require(b["runtime"]=="NONE" and b["fa"]=={} and set(b["mixed_FA_records"])=={str(i) for i in range(3,64,4)},
     "whole original mixed NONE16FA unchanged path, no sparse override")
    fas=[]
    for i in range(3,64,4):
     x=read(b["mixed_FA_records"][str(i)],"actual-mixed-stock-fa",rank)
     c.require(x["epoch"]==b["epoch"] and x["actual_original_forward_impl_called"] is True and
      x["sparse_algorithm_active"] is False and x["output_finite"] is True and
      x["independent_mixed_numeric_pass_not_claimed"] is True,"original untouched mixed path is source provenance, not fabricated numerical reference")
   c.require(set(b["request_ids"])<=set(http["requests"]),"every actual model request comes from original SSE cohort")
   seen_requests[rank].update(b["request_ids"])
   for req in b["native_request_rows"]["request_rows"]:
    forwarded[rank][req["rid"]]=max(forwarded[rank].get(req["rid"],0),req["computed"]+req["scheduled"])
   cell=coverage.consume_turn(rank,b,states)
   evidence_digest.update(c.canonical(dict(rank=rank,epoch=b["epoch"],runtime=b["runtime"],batch=b["batch"],allocation=cell,
    conditional_FA_checks=fas,inactive_GDN_checks=checked,active_GDN_observations=active,
    active_GDN_dense_equivalence_not_claimed=True)))
   checked_turn_count+=1;active_observation_count+=len(active)
 summary=coverage.finish()
 for rank in range(4):
  c.require(seen_requests[rank]==set(http["requests"]),"every actual SSE request processed on every rank")
  for rid,request in http["requests"].items():
   c.require(forwarded[rank][rid]>=request["prompt_tokens"]+request["output_tokens"]-1,
    "all actual requested token forwards on every rank, final sampled token need not be forwarded")
 c.require(len({len(boundaries[r]) for r in range(4)})==1 and len(set(full_epochs.values()))==1,"actual TP4 complete turn counts agree")
 return dict(schema="sparq.actual-full64-model-check/v3",source=source,index=index_ref,workers=workers,
  coverage=summary,actual_http=index["http"],actual_requests_per_rank=len(http["requests"]),all_actual_checks_rolling_sha256=evidence_digest.hexdigest(),checked_turn_count=checked_turn_count,
  active_observation_count=active_observation_count,FA=16,GDN=48,
  GDN_protocol=gdn_stream.PROTOCOL,GDN_numpy_dependency=numpy_dependency,all_active_and_inactive_GDN_after_finite=True,
  GDN_full_original_before_CPU_saved=True,GDN_complete_live_byte_consumer=True,GDN_permanent_success_raw_replay=False,active_GDN_diagnostic_not_dense_equality=True,
  mixed_FA_source_unchanged_not_new_independent_numeric_claim=True,
  conditional_output_threshold=dict(relative_rms=.005,cosine=.99998),mean_configuration=False,online_independent_full_qKV_literal_FP64=True,postmortem_full_qKV_replay=False,passed=True,
  performance_passed=False,task_quality_passed=False,model_ready=False)
def stopped(ref,cid,owned_ref,source,files,cpu,arm="candidate"):
 from service_contract import ROOT as HOST_WORKDIR
 raw=c.obj(ref);rows=json.loads(raw["stdout"]);e=c.obj(owned_ref)
 c.require(raw["exit_code"]==0 and raw["requested_argv"]==["/usr/bin/docker","inspect",cid] and len(rows)==1,
  "actual original exact Docker inspect receipt")
 x=rows[0];s=x["State"];h=x["HostConfig"];cfg=x["Config"]
 c.require(e["cid"]==cid and e["image"]==x["Image"]=="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1" and
  e["source"]==source and e["sources"]==files and e["host_sha256"]==files["host_run.py"] and
  e["arm"]==("cpu-preflight" if cpu else arm) and x["Id"]==cid and x["Name"]=="/"+e["name"] and
  s["Running"] is False and s["Pid"]==0 and s["OOMKilled"] is False and not x.get("ExecIDs"),
  "whole owned source/CID/image/name/arm identity stopped retained noOOM/noExec")
 expected_labels={"model-tuning-lab.owner":"sparq-author-ann-fp32-stock-full-v3","model-tuning-lab.run":e["name"],
  "model-tuning-lab.arm":e["arm"],"model-tuning-lab.source-manifest-sha256":source["sha256"],
  "model-tuning-lab.controller-sha256":files["host_run.py"]}
 c.require(all(cfg["Labels"].get(k)==v for k,v in expected_labels.items()) and cfg["Image"]==e["image"] and
  cfg["Entrypoint"]==["/bin/bash"] and cfg["Cmd"]==["-c","exec /bin/sleep infinity"] and cfg["WorkingDir"]==str(HOST_WORKDIR),
  "actual original owned labels and init, never arbitrary matching CID")
 mem=(8 if cpu else 64)*1024**3;cores=1 if cpu else 4
 c.require(h["Privileged"] is False and h["Memory"]==h["MemorySwap"]==mem and h["NanoCpus"]==cores*10**9 and
  h["CpusetCpus"]==",".join(map(str,e["guest_cpus"])) and len(e["guest_cpus"])==cores and
  h["IpcMode"]=="private" and h["NetworkMode"]=="none" and h["ShmSize"]==4*1024**3 and h["PidsLimit"]==2048 and
  not h.get("DeviceRequests") and not h.get("DeviceCgroupRules") and set(h.get("CapDrop") or [])=={"ALL"} and
  set(h.get("SecurityOpt") or [])=={"no-new-privileges"},"actual whole isolated CPU/model budget")
 environment={"ASCEND_RT_VISIBLE_DEVICES":"" if cpu else "0,1,2,3","TORCH_DEVICE_BACKEND_AUTOLOAD":"0",
  "PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1",
  "QWEN36_SPARQ_TOKEN_ENABLED":"0","SPARQ_TP4_SERVICE":"0","VLLM_DISABLE_REQUEST_ID_RANDOMIZATION":"1"}
 env=cfg.get("Env") or []
 c.require(all(env.count(k+"="+v)==1 and sum(s.startswith(k+"=") for s in env)==1 for k,v in environment.items()),
  "actual source-bound environment no duplicate drift")
 devices={} if cpu else {"/dev/davinci%d"%p:"/dev/davinci%d"%r for r,p in enumerate((4,5,6,7))}
 if not cpu:devices.update({"/dev/"+n:"/dev/"+n for n in ("davinci_manager","devmm_svm","hisi_hdc")})
 dev=h.get("Devices") or []
 c.require(len(dev)==len(devices) and {d["PathOnHost"]:d["PathInContainer"] for d in dev}==devices and
  all(d["CgroupPermissions"]=="rwm" for d in dev),"actual Devices[] or exact4..7 including only three controls")
 mounts=x["Mounts"]
 c.require(len(mounts)==len(e["mounts"]) and all(m["Type"]=="bind" for m in mounts) and
  {m["Destination"]:(m["Source"],m["RW"]) for m in mounts}==
  {n:(p,bool(rw)) for n,(p,rw) in e["mounts"].items()},"actual whole original input/output mount closure")
 created=c.obj(e["create_receipt"])
 c.require(created["exit_code"]==0 and created["stdout"].strip()==cid and
  created["requested_argv"][:4]==["/usr/bin/docker","create","--name",e["name"]] and
  created["requested_argv"][-3:]==[e["image"],"-c","exec /bin/sleep infinity"],
  "original successful exact create receipt, not synthesized owner metadata")
 return x
def consume(host_ref,terminal_ref,source_ref,component_ref):
 source,files=c.source(source_ref["path"],source_ref["sha256"]);component=c.component(component_ref,replay=True)
 origin=original_terminal(c.obj(terminal_ref),PEER);record=origin["record"];host=c.obj(host_ref)
 c.require(host["schema"]=="sparq.tp4-service-host/v1" and host["mode"]=="diagnostic" and host["status"]=="complete" and
  host["primary"] is None and host["secondary"]==[] and host["refs"]["source"]==source and host["refs"]["component"]==component_ref and
  host["source_files_before"]==host["source_files_after"]==files and 0<host["phase_elapsed_seconds"]<=5400,
  "whole source-bound actual model host terminal, no partial/failed/late grant")
 lines=[l for l in record["stdout"].splitlines() if l.startswith("MAIN_SPARQ_TP4_SERVICE ")]
 c.require(len(lines)==1 and json.loads(lines[0].split(" ",1)[1])==dict(result=host_ref,status="complete"),
  "whole original model stdout binds entire actual host result")
 plan=c.obj(host["plan"]);c.validate_execution_clock(plan,host)
 c.require([record["command"],*record["args"]]==plan["expected_host_argv"] and
  plan["refs"]==host["refs"] and plan["source_files"]==files and plan["mode"]=="diagnostic" and
  plan["physical_devices"]==[4,5,6,7] and plan["logical_to_physical"]=={"0":4,"1":5,"2":6,"3":7} and
  plan["memory_guest_bytes"]==64*1024**3 and plan["memory_host_bytes"]==256*1024**2 and
  plan["memory_reserve_bytes"]==8*1024**3 and plan["phase_seconds"]==5400 and plan["cleanup_seconds"]==90,
  "actual original single whole budget/physical4-7/CLI admission")
 cpu=c.obj(host["cpu_stage"]);cr=c.obj(cpu["cleanup"]);cx=stopped(cr["after_inspect"],cpu["container_id"],c.bound(Path(cpu["cleanup"]["path"]).parent/"OWNED.json",c.sha(Path(cpu["cleanup"]["path"]).parent/"OWNED.json")),source,files,True)
 cp=c.obj(cpu["probe"])
 c.require(cpu["status"]=="complete" and cpu["primary"] is None and cpu["secondary"]==[] and cx["HostConfig"]["Devices"]==[] and
  cx["HostConfig"]["Memory"]==cx["HostConfig"]["MemorySwap"]==8*1024**3 and cx["HostConfig"]["NanoCpus"]==10**9 and
  cp["source"]==source and cp["files"]==files and identity_bridge.static_probe(cp,source,files),
  "actual Devices[] same-source FULL import closure stopped before TP4")
 gdn_stream.validate_probe(cp,files)
 import component_bootstrap
 component_bootstrap.verify_probe(c,cp,source,component_ref)
 prechild=c.obj(cpu["original_child"])
 import service_contract as service
 preargs=[str(c.ROOT/"full_cpu_preflight.py"),"--execute","--source-manifest-sha256",source["sha256"],"--output",cpu["probe"]["path"]]
 c.require(prechild["requested_argv"]==service.docker_argv(cpu["container_id"],preargs) and prechild["exit_code"]==0,
  "actual exact original CPU import CLI/owned source and CID")
 premarks=[l for l in prechild["stdout"].splitlines() if l.startswith("MAIN_SPARQ_FULL_CPU ")]
 c.require(len(premarks)==1 and json.loads(premarks[0].split(" ",1)[1])==dict(result=cpu["probe"],status="source-static-checked"),
  "actual original CPU source marker binds complete probe bytes")
 c.require(len(host["arms"])==1,"single complete candidate diagnostic arm")
 arm=c.obj(host["arms"][0]);cleanup=c.obj(arm["cleanup"]);owned=stopped(cleanup["after_inspect"],arm["container_id"],c.bound(Path(arm["cleanup"]["path"]).parent/"OWNED.json",c.sha(Path(arm["cleanup"]["path"]).parent/"OWNED.json")),source,files,False)
 c.require(arm["status"]=="complete" and arm["arm"]=="candidate" and arm["primary"] is None and arm["secondary"]==[] and
  cleanup["stopped"] is True and cleanup["retained"] is True and cleanup["errors"]==[] and
  cleanup["protected_boundary"]["own_on_protected"] is False,"actual exact model stop-retain/release")
 import importlib,sys
 before=list(sys.path)
 try:
  sys.path.insert(0,str(c.KERNEL))
  proof=importlib.import_module("sparq_token_v4.proof")
  manifest=c.obj(dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA))
  c.bound(proof.__file__,manifest["files"]["sparq_token_v4/proof.py"])
  cpu_stopped_before_npu_started=proof.cpu_stopped_before_npu_started
 finally:sys.path[:]=before
 c.require(cpu_stopped_before_npu_started(cx["State"]["FinishedAt"],owned["State"]["StartedAt"]),
  "nanosecond exact CPU stopped BEFORE model NPU init")
 arm_root=Path(host["arms"][0]["path"]).parent
 arm_meta=c.obj(c.bound(arm_root/"service/ARM.json",c.sha(arm_root/"service/ARM.json")))
 identity_bridge.consume_n1(arm_meta["device_dependency"],source,files,arm["identity"],arm_root/"service")
 device={d["PathOnHost"]:d["PathInContainer"] for d in owned["HostConfig"]["Devices"]}
 c.require(all(device.get("/dev/davinci%d"%p)=="/dev/davinci%d"%r for r,p in enumerate((4,5,6,7))) and
  all("/dev/davinci%d"%p not in device for p in range(4)),"actual only physical4..7 mapped to logical0..3")
 post=c.obj(host["post_model_cpu"]);pc=c.obj(post["cleanup"]);px=stopped(pc["after_inspect"],post["container_id"],c.bound(Path(post["cleanup"]["path"]).parent/"OWNED.json",c.sha(Path(post["cleanup"]["path"]).parent/"OWNED.json")),source,files,True)
 c.require(post["schema"]=="sparq.full64-CPU-stage/v1" and post["status"]=="complete" and post["primary"] is None and post["secondary"]==[] and
  px["HostConfig"]["Devices"]==[] and px["HostConfig"]["Memory"]==px["HostConfig"]["MemorySwap"]==8*1024**3 and
  px["HostConfig"]["NanoCpus"]==10**9 and post["source"]==source and post["component"]==component_ref and
  post["trace"]==arm["actual_model_trace"],"actual second owned Devices[] CPU-golden stage, not host Torch assumption")
 c.require(cpu_stopped_before_npu_started(owned["State"]["FinishedAt"],px["State"]["StartedAt"]),
  "actual model stopped before independent CPU validation lease, same whole deadline")
 gold=c.obj(post["report"]);child=c.obj(post["original_child"])
 import service_contract as service
 cpu_args=[str(c.ROOT/"model_cpu_check.py"),"--execute","--source",source["path"],"--source-sha256",source["sha256"],
  "--component",component_ref["path"],"--component-sha256",component_ref["sha256"],
  "--trace",arm["actual_model_trace"]["path"],"--trace-sha256",arm["actual_model_trace"]["sha256"],
  "--output",post["report"]["path"]]
 c.require(child["requested_argv"]==service.docker_argv(post["container_id"],cpu_args) and child["exit_code"]==0,
  "actual original CPU golden exact source-bound CLI/ownedCID")
 marks=[l for l in child["stdout"].splitlines() if l.startswith("MAIN_SPARQ_FULL_MODEL_CPU ")]
 c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(result=post["report"],status="checked") and
  gold["schema"]=="sparq.actual-full64-CPU-check/v1" and gold["status"]=="checked" and
  gold["source"]==source and gold["source_files"]==files and gold["first_exception"] is None and
  gold["refs"]==dict(source=source,component=component_ref,trace=arm["actual_model_trace"]) and
  gold["initialized_before"] is False and gold["initialized_after"] is False and gold["actual_device_fds"]==[],
  "whole actual independent CPU FP64 report/stdio/source/no-device binding")
 checked=gold["check"]
 c.require(checked["schema"]=="sparq.actual-full64-model-check/v3" and checked["passed"] is True and checked["source"]==source and
  checked["index"]==arm["actual_model_trace"] and checked["FA"]==16 and checked["GDN"]==48 and
  checked["GDN_protocol"]==gdn_stream.PROTOCOL and checked["GDN_numpy_dependency"]==cp["GDN_stream_checker"]["numpy"] and checked["all_active_and_inactive_GDN_after_finite"] is True and
  checked["GDN_full_original_before_CPU_saved"] is True and checked["GDN_complete_live_byte_consumer"] is True and checked["GDN_permanent_success_raw_replay"] is False and
  checked["conditional_output_threshold"]==dict(relative_rms=.005,cosine=.99998) and checked["mean_configuration"] is False and checked["online_independent_full_qKV_literal_FP64"] is True and checked["postmortem_full_qKV_replay"] is False and checked["checked_turn_count"]>0 and
  re.fullmatch("[0-9a-f]{64}",checked["all_actual_checks_rolling_sha256"]) and
  checked["coverage"]["cells"]==checked["coverage"]["observed"]==4*(16*2+15) and
  checked["coverage"]["all_true_batches"]==list(range(1,17)),
  "complete allactual64/allB/mixed/reuse/FULL CPU check, not scalar boolean-only artifact")
 for serialized_rank,w in checked["workers"].items():
  c.require(type(serialized_rank) is str and serialized_rank in ("0","1","2","3"),"actual JSON rank keys")
  rank=int(serialized_rank)
  c.require(w["rank"]==rank,"rank worker whole JSON identity")
  proofs=[p for p in arm["process_proofs"] if p["physical"]==rank+4 and p.get("namespace_pids") and
   p["namespace_pids"][-1]==w["namespace_pid"] and p["cmdline_sha256"]==w["actual_proc_cmdline_sha256"] and
   arm["container_id"] in p["cgroup"]]
  c.require(proofs,"actual workload NPU rank PID/start/argv/cgroup authority, never canary reused")
 return dict(schema="sparq.actual-full64-model-authority/v3",execution_clock=c.execution_clock(),source=source,source_files=files,component=component_ref,
  original_terminal=terminal_ref,original_operation_id=origin["operation_id"],actual_host=host_ref,
  model_check=checked,actual_full64_model_diagnostic_verified=True,formal_permission_source_bound=True,
  default_enabled=False,performance_verified=False,task_quality_verified=False,ready=False)
def consume_authority(ref,source,component,replay=False):
 x=c.obj(ref)
 c.require(x["schema"]=="sparq.actual-full64-model-authority/v3" and x["source"]==source and x["component"]==component and
  x["actual_full64_model_diagnostic_verified"] is True and x["execution_clock"]==c.execution_clock(),
  "actual entire same-source full64 prerequisite and immutable user72h model clock")
 if replay:
  again=consume(x["actual_host"],x["original_terminal"],source,component)
  c.require(c.canonical(again)==c.canonical(x),"independent whole-original model consumer replay equality")
 return x
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 for n in ("host-result","terminal","source","component"):
  p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
 p.add_argument("--output");a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",model_ready=False,ready=False)));return
 refs={n:c.bound(getattr(a,n.replace("-","_")),getattr(a,n.replace("-","_")+"_sha256")) for n in ("host-result","terminal","source","component")}
 result=consume(refs["host-result"],refs["terminal"],refs["source"],refs["component"])
 print(json.dumps(c.write(a.output,result),sort_keys=True))
if __name__=="__main__":main()
