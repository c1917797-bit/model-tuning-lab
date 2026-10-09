"""Independent whole-original FULL TP4 paired1024/final2048 consumer; default OFF.
No legacy27/v4, flattened operation, partial kernel, kernel timing projection,
active free-generation GDN equality, or synthetic task score is accepted.
"""
import argparse,hashlib,json,re,math
from pathlib import Path
import source_contract as c,service_contract as service,wire,consume_model,gdn_stream
from original_terminal import original_terminal
PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
import identity_bridge
def command(ref,argv):
 x=c.obj(ref)
 c.require(x["requested_argv"]==argv and x["argv"]==["/usr/bin/prlimit","--as=unlimited","--",*argv] and x["exit_code"]==0,
  "actual whole original exact source-bound CLI/AS restoration/exit")
 return x
def proof_module():
 import sys,importlib
 before=list(sys.path)
 try:
  sys.path.insert(0,str(c.KERNEL));m=importlib.import_module("sparq_token_v4.proof")
  km=c.obj(dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA))
  c.bound(m.__file__,km["files"]["sparq_token_v4/proof.py"]);return m
 finally:sys.path[:]=before
def owned_stop(stage,source,files,arm):
 cleanup=c.obj(stage["cleanup"]);cid=stage["container_id"];root=Path(stage["cleanup"]["path"]).parent
 owned=c.bound(root/"OWNED.json",c.sha(root/"OWNED.json"))
 x=consume_model.stopped(cleanup["after_inspect"],cid,owned,source,files,arm=="cpu-preflight",arm=arm)
 c.require(cleanup["container"]==cid and cleanup["stopped"] is True and cleanup["retained"] is True and
  cleanup["deleted"] is False and cleanup["errors"]==[] and cleanup["primary_error"] is None and
  cleanup["protected_boundary"]["own_on_protected"] is False,"actual exact own stop retain/release; external protected churn is not equality gate")
 command(cleanup["stop_receipt"],["/usr/bin/docker","stop","--time","15",cid])
 raw=command(cleanup["release_smi"],["/usr/local/sbin/npu-smi","info"])
 from host_run import H,PHYSICAL
 for card in PHYSICAL:H.frozen().idle_one(raw["stdout"],card)
 return x
def cpu_stage(ref,source,files):
 stage=c.obj(ref);x=owned_stop(stage,source,files,"cpu-preflight");probe=c.obj(stage["probe"])
 c.require(stage["status"]=="complete" and stage["primary"] is None and stage["secondary"]==[] and
  identity_bridge.static_probe(probe,source,files),
  "actual CPU Devices[] startup/source import closure, not nominal name")
 gdn_stream.validate_probe(probe,files)
 import component_bootstrap
 actual=c.obj(source)["disjoint_component_handoff"]["actual_native_component_pass_evidence"]
 component_bootstrap.verify_probe(c,probe,source,dict(path=actual["path"],sha256=actual["sha256"]))
 args=[str(c.ROOT/"full_cpu_preflight.py"),"--execute","--source-manifest-sha256",source["sha256"],"--output",stage["probe"]["path"]]
 child=command(stage["original_child"],service.docker_argv(stage["container_id"],args))
 marks=[l for l in child["stdout"].splitlines() if l.startswith("MAIN_SPARQ_FULL_CPU ")]
 c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(result=stage["probe"],status="source-static-checked"),
  "original CPU whole stdout -> immutable probe")
 return x
def arm(ref,refs,files,previous_stopped):
 x=c.obj(ref);root=Path(ref["path"]).parent;cid=x["container_id"]
 c.require(x["schema"]=="sparq.tp4-arm-result/v1" and x["status"]=="complete" and x["mode"]=="formal" and
  x["source"]==refs["source"] and x["component"]==refs["component"] and x["model_manifest"]==refs["model-manifest"] and
  x["diagnostic"]==refs["diagnostic"] and x["primary"] is None and x["secondary"]==[],
  "actual whole formal arm source/model/component authority")
 stop=owned_stop(x,refs["source"],files,x["arm"])
 c.require(proof_module().cpu_stopped_before_npu_started(previous_stopped,stop["State"]["StartedAt"]),
  "exact ns prior guest stopped before next owned model guest starts")
 ident=c.obj(x["identity"]);a=c.obj(c.bound(root/"service/ARM.json",c.sha(root/"service/ARM.json")))
 c.require(ident["source"]==refs["source"] and ident["component"]==refs["component"] and ident["model_manifest"]==refs["model-manifest"] and
  ident["mode"]=="formal" and ident["arm"]==x["arm"] and ident["container_id"]==cid and
  a["schema"]=="sparq.author-ann-stock-full-arm/v1" and a["author_algorithm"]==dict(protocol=c.AUTHOR_PROTOCOL,reallocate_to_mean_value=False,meanON_not_supported_by_service=True) and a["source"]==refs["source"] and a["source_files"]==files and a["numeric_authority"]==refs["component"] and
  a["arm"]==x["arm"] and a["mode"]=="formal" and a["common"]==service.COMMON and
  a["command"]==service.server_argv(ident["port"]) and a["identity"]==x["identity"] and
  a["protocol"]==service.PROTOCOL and a["observation_graph"] is False and a["formal_enabled"] is True,
  "actual same common stock FULL server/config and no diagnostic observation graph in timing")
 identity_bridge.consume_n1(a["device_dependency"],refs["source"],files,x["identity"],root/"service")
 from host_run import identity_args
 expanded=list(ident["image_argv_template"]);i=expanded.index("--identity-sha256")+1
 c.require(expanded[i]=="@ACTUAL_IDENTITY_SHA256@" and expanded.count("@ACTUAL_IDENTITY_SHA256@")==1,"only exact self hash sentinel")
 expanded[i]=x["identity"]["sha256"]
 server_expected=service.docker_argv(cid,identity_args(refs,x["identity"],x["arm"],ident["port"],"formal"))
 c.require(expanded==[service.PY,"-B",*identity_args(refs,x["identity"],x["arm"],ident["port"],"formal")],"complete real image argv expansion")
 client_expected=[str(c.ROOT/"bench.py"),"--execute","--arm-dir",str(root/"service"),"--port",str(ident["port"]),"--output",str(root/"client")]
 if x["task_scores"]:client_expected+=["--tasks",refs["tasks"]["path"],"--tasks-sha256",refs["tasks"]["sha256"]]
 for name,expected in (("server",server_expected),("client",service.docker_argv(cid,client_expected))):
  child=c.obj(x["children"][name])
  c.require(child["requested_argv"]==expected and child["actual_host_argv"]==["/usr/bin/prlimit","--as=unlimited","--",*expected] and
   child["child_termination_observed"] is True and child["child_host_pid"]>1,
   "actual foreground exact original server/client argv, termination")
  for key in ("stdout_ref","stderr_ref"):c.bound(child[key]["path"],child[key]["sha256"])
  if name=="client":
   c.require(child["exit_code"]==0,"actual client failed")
   marks=[l for l in Path(child["stdout_ref"]["path"]).read_text().splitlines() if l.startswith("SPARQ_SERVICE_HTTP ")]
   c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(report=x["http"],status="complete"),"whole original client marker")
 http=wire.http(x["http"],c.bound(root/"service/ARM.json",c.sha(root/"service/ARM.json")))
 final=x["formal_stats"];summary=c.obj(final["report"])
 final_args=[str(c.ROOT/"formal_stats.py"),"--execute","--trace",str(root/"service/trace"),"--source",refs["source"]["path"],
  "--source-sha256",refs["source"]["sha256"],"--output",final["report"]["path"]]
 child=command(final["original_child"],service.docker_argv(cid,final_args))
 marks=[l for l in child["stdout"].splitlines() if l.startswith("SPARQ_FORMAL_FINALIZED ")]
 c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(result=final["report"]) and
  summary["schema"]=="sparq.actual-formal-finalization/v1" and summary["source"]==refs["source"] and len(summary["workers"])==4,
  "actual after-timing finalizer whole command/stdout/report")
 trace=root/"service/trace"
 c.require(sorted(p.name for p in trace.glob("*.json"))==sorted(["FORMAL_WORKER-r%d.json"%r for r in range(4)]+["FORMAL_FINAL-r%d.json"%r for r in range(4)]),
  "formal per-layer debug JSON actually OFF; only before/after timing worker summaries")
 workers={}
 for rank,rr in enumerate(summary["workers"]):
  w=c.obj(rr);start=c.obj(w["worker_start"]);process=w["process"]
  identity_bridge.validate_worker_flag(w["common_identity_flag"]);identity_bridge.validate_worker_flag(start["common_identity_flag"])
  c.require(w["schema"]=="sparq.formal-worker-final/v1" and w["rank"]==start["rank"]==rank and
   w["source"]==start["source"]==refs["source"] and w["source_files"]==start["source_files"]==files and
   w["component"]==start["component"]==refs["component"] and w["arm"]==start["arm"]==x["arm"] and
   w["mode"]=="formal" and w["timing_debug_off"] is True and w["diagnostic_trace_enabled"] is False and
   all(process[k]==start["process"][k] for k in ("pid","start_ticks","cmdline_sha256","argv","cgroup")),
   "actual formal worker stable PID/start/hash/cgroup/no debug identity")
  actual=[p for p in x["process_proofs"] if p["physical"]==rank+4 and p["chip"]==0 and p["namespace_pids"][-1]==process["pid"] and
   p["start_ticks"]==process["start_ticks"] and p["cmdline_sha256"]==process["cmdline_sha256"] and cid in p["cgroup"]]
  c.require(actual and process["argv"],"actual physical model worker authority, never kernel canary")
  c.require(w["real_turns"]>0 and w["full_turns"]==w["original_full_replays"]==w["original_post_updates"]>0 and
   set(w["captures"])=={str(b) for b in range(1,17)} and
   all(len(z)==16 and {v["layer"] for v in z.values()}==set(service.FA) for z in w["captures"].values()) and
   len(w["GDN"])==48 and {v["layer"] for v in w["GDN"]}==set(service.GDN),
   "actual complete16 FA stock captures/real replay/POSTupdate and original48 GDN receivers")
  for rid,r in http["requests"].items():
   req=w["requests"].get(rid)
   c.require(req and req["last_computed"]+req["last_scheduled"]>=r["prompt_tokens"]+r["output_tokens"]-1,
    "all measured/warmup request IDs actually forwarded on each actual rank")
  if x["arm"]=="candidate":
   budget=w["budget"]
   c.require(budget["full_native_KV_GDN_not_removed"] is True and budget["owned_guarded_bytes"]<=service.AUX_CEILING and
    budget["actual_delta_allocated_bytes"]<=service.AUX_CEILING and budget["actual_peak_upper_delta_bytes"]<=service.AUX_CEILING,
    "actual full candidate capture/transient aux peak <=2GiB, no simulated allocator saving")
  else:c.require(w["budget"]["dense_fake_aux_not_allocated"] is True,"no fake dense aux budget")
  workers[rank]=dict(report=rr,process=process)
 return dict(arm=x["arm"],round=x["round"],ref=ref,stop=stop["State"]["FinishedAt"],metrics=http["metrics"],workers=workers,tasks=x["task_scores"])
def tasks_checked(final,refs):
 inputs=service.task_manifest(refs["tasks"]);result={}
 for task,t in inputs["tasks"].items():
  scores={}
  for label,a in final.items():
   x=c.obj(a["ref"]);root=Path(a["ref"]["path"]).parent;meta=c.obj(a["tasks"])
   c.require(meta["tasks"]==refs["tasks"] and meta["arm"]==label,"exact frozen final task inputs/arm")
   entry=meta["scores"][task];responses=c.obj(entry["responses"]);score=c.obj(entry["score"])
   expected=[entry["responses"]["path"] if v=="@RESPONSES@" else entry["score"]["path"] if v=="@OUTPUT@" else v for v in t["scorer_cli"]]
   command(entry["actual_scorer_terminal"],service.docker_argv(x["container_id"],expected[2:]))
   identity=service.digest([service.COMMON,refs["source"],refs["model-manifest"],refs["tasks"],t,dict(cap=2048,temperature=0,seed=0,ignore_eos=False,thinking=False)])
   c.require(entry["original_cli"]==expected and score["schema"]=="qwen36.actual-task-score/v1" and score["task"]==task and
    score["arm"]==label and score["responses_sha256"]==entry["responses"]["sha256"] and score["protocol_identity"]==identity and
    score["scorer_source"]==t["scorer_source"] and score["request_count"]==t["request_count"] and
    responses["protocol_identity"]==identity and responses["max_tokens"]==2048 and responses["thinking_mode_enabled"] is False and
    responses["temperature"]==0 and responses["seed"]==0 and responses["ignore_eos"] is False and
    len(responses["rows"])==t["request_count"],"original scorer source/CLI/input/all rows/no-thinking EOS2048 identity")
   for row,prompt in zip(responses["rows"],service.task_prompts(t)):
    c.require(row["task_request_id"]==prompt["id"],"whole frozen task prompt order")
    wire.replay(row,prompt["prompt_token_ids"],root/"client",2048,exact=False)
   scores[label]=score["score"]
  result[task]=dict(dense=scores["dense"],candidate=scores["candidate"],**service.loss(scores["dense"],scores["candidate"]))
  c.require(result[task]["accepted"],"full real final tasks violate conservative both1% definitions")
 return result
def consume(result_ref,terminal_ref):
 host=c.obj(result_ref);plan=c.obj(host["plan"]);c.validate_execution_clock(plan,host);refs=host["refs"];source,files=c.source(refs["source"]["path"],refs["source"]["sha256"])
 c.component(refs["component"],replay=True);service.diagnostic_authority(refs["diagnostic"],refs["component"],source,replay=True)
 origin=original_terminal(c.obj(terminal_ref),PEER);record=origin["record"];argv=[record["command"],*record["args"]]
 marks=[l for l in record["stdout"].splitlines() if l.startswith("MAIN_SPARQ_TP4_SERVICE ")]
 c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(result=result_ref,status="complete") and
  host["schema"]=="sparq.tp4-service-host/v1" and host["status"]=="complete" and host["mode"]==plan["mode"]=="formal" and
  host["primary"] is None and host["secondary"]==[] and host["source_files_before"]==host["source_files_after"]==files and
  host["refs"]==plan["refs"] and plan["source_files"]==files and argv==plan["expected_host_argv"]==plan["actual_host_process"]["argv"] and
  plan["actual_host_process"]["cmdline_sha256"]==hashlib.sha256(("\0".join(argv)+"\0").encode()).hexdigest(),
  "whole original MAIN source/CLI/PID/hash/stdio successful host, never flattened helper")
 c.require(plan["phase_seconds"]==5400 and plan["cleanup_seconds"]==90 and plan["deadline_monotonic"]-plan["created_monotonic"]==5400 and
  0<host["phase_elapsed_seconds"]<=5400 and plan["cutoff"]==service.CUT and plan["physical_devices"]==[4,5,6,7] and
  plan["memory_guest_bytes"]==64*1024**3 and plan["memory_host_bytes"]==256*1024**2 and plan["memory_reserve_bytes"]==8*1024**3,
  "one whole strict lease/ordinaryRAM/reserve/no resets")
 previous=cpu_stage(host["cpu_stage"],source,files)["State"]["FinishedAt"];arms=[]
 c.require(len(host["arms"])==(8 if plan["final_task_requested"] else 6),"all three paired screens plus optional two complete task arms")
 for rr in host["arms"]:
  a=arm(rr,refs,files,previous);previous=a["stop"];arms.append(a)
 c.require([(a["round"],a["arm"]) for a in arms[:6]]==[(0,"dense"),(0,"candidate"),(1,"candidate"),(1,"dense"),(2,"dense"),(2,"candidate")],
  "preregistered paired alternating order")
 speedups=[]
 for i in range(3):
  pair={a["arm"]:a for a in arms if a["round"]==i};ratio=pair["candidate"]["metrics"]["output_tokens_per_second"]/pair["dense"]["metrics"]["output_tokens_per_second"]
  c.require(ratio>=1.10,"each actual paired fixed1024 benefit>=10%");speedups.append(ratio)
 tasks={}
 if plan["final_task_requested"]:
  c.require([(a["round"],a["arm"]) for a in arms[6:]]==[(3,"dense"),(3,"candidate")],"both actual final2048 task arms")
  tasks=tasks_checked({a["arm"]:a for a in arms[6:]},refs)
 return dict(schema="sparq.actual-stock-full-service-authority/v3",execution_clock=c.execution_clock(),source=source,component=refs["component"],diagnostic=refs["diagnostic"],
  original_terminal=terminal_ref,original_operation_id=origin["operation_id"],actual_host=result_ref,
  actual_three_paired_fixed1024_verified=True,speedups=speedups,original_stock_FULL_replay_bound=True,
  full64_diagnostic_authority_separately_verified=True,active_GDN_dense_free_generation_equivalence_not_claimed=True,
  tasks=tasks,final2048_task_verified=bool(tasks),ready=bool(tasks),performance_microbenchmark_not_used=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 for n in ("result","terminal"):p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
 p.add_argument("--output");a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",ready=False)));return
 out=consume(c.bound(a.result,a.result_sha256),c.bound(a.terminal,a.terminal_sha256))
 print(json.dumps(c.write(a.output,out),sort_keys=True))
if __name__=="__main__":main()
