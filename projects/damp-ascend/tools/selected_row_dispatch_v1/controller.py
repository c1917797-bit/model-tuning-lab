#!/usr/bin/env python3
"""NEW MAIN-only selected-row balanced dispatch. Default dry, never old PASS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import types
from selected_contract import (HERE,REPO,PROJECT,OLD_DIR,OLD_PACKET_SHA,BATCH_GROUPS,EXECUTION_PACKET,
    packet,source_snapshot,validate_shards,sha,read,checked,require,load)

ORIGINAL=load("_selected_row_original_controller",OLD_DIR/"controller.py")
PRIOR_OPERATION="exec-00000000000006a0"
def source_preparation(pin=None):
    packet(pin)
    prepared=list(ORIGINAL.source_preparation(OLD_PACKET_SHA))
    prepared[-1]={**prepared[-1],"selected_row_sources":source_snapshot(),
        "selected_row_packet_sha256":sha(HERE/"PACKET.json"),"balanced_groups":BATCH_GROUPS}
    return tuple(prepared)
def make_plan(run_id,planner,pin):
    result=ORIGINAL.make_plan(run_id,planner,OLD_PACKET_SHA)
    for entry in result["shards"]:
        group=BATCH_GROUPS[entry["physical_card"]]
        create=entry["docker_create_argv"];pos=create.index("--entrypoint")
        create[pos:pos]=["-e","DAMP_RUN_SELECTED_ROW_DISPATCH_V1=1"]
        entry["create_argv_sha256"]=planner.argv_sha(create)
        entry["docker_canary_exec_argv"][-2]=entry["create_argv_sha256"]
        gate=entry["gate_argv_source_bound_incomplete"]
        require(gate[2]==str(OLD_DIR/"runner.py"),"original independent runner seam")
        gate[2]=str(HERE/"runner.py")
        pos=gate.index("--packet-sha256");gate[pos+1]=pin
        gate.extend(["--batches",*map(str,group)])
        entry.update(batches=list(group),execution_packet=EXECUTION_PACKET,
            reference_anchor="48 fullS/localS1 pairs then six original B16 anchors",
            grouping_semantics="explicit noncontiguous four-T group; no start/end shortcut")
    result.update(execution_packet=EXECUTION_PACKET,balanced_groups={str(k):list(v) for k,v in BATCH_GROUPS.items()},
        selected_row_pairs=192,native_split_anchor_cases=24,launchable=False)
    return result
def prior_release(args):
    """MAIN-issued actual refs, not a success label. Never stop prior containers."""
    raw=read(checked(args.prior_terminal,args.prior_terminal_sha256))
    d=raw.get("structuredContent",raw);operation=d.get("operation",{})
    result=operation.get("result",{});record=result.get("record",{})
    require(d.get("schema")=="agentweb.operation/v1" and d.get("kind")=="exec" and
        d.get("operationId")==PRIOR_OPERATION and d.get("terminal") is True and d.get("status")=="completed" and
        operation.get("routeDecision")=="peer_direct" and
        operation.get("targetPeerId")=="lgw_a6109c51076a4a2c9d2674ca5a8704a0" and
        result.get("found") is True and result.get("ok") is True and result.get("state")=="completed" and
        record.get("id")==PRIOR_OPERATION and record.get("state")=="completed" and
        record.get("cancelled") is False and record.get("timedOut") is False and
        record.get("command")=="/usr/bin/python3" and record.get("cwd")==str(REPO) and
        result.get("lane")=="job" and record.get("lane")=="job" and
        type(record.get("exitCode")) is int and type(record.get("args")) is list and
        all(type(x) is str for x in record["args"]) and type(record.get("stdout")) is str and
        type(record.get("stderr")) is str,
        "actual prior MA06a0 complete/direct exact command; cancelled/live/unknown remains blocked")
    require(hashlib.sha256(json.dumps(record["args"],separators=(",",":")).encode()).hexdigest()==
        args.prior_args_sha256,"MAIN exact original args identity")
    argv=record["args"]
    require(argv[:2]==["-B",str(OLD_DIR/"controller.py")] and
        argv.count("--packet-sha256")==1 and argv[argv.index("--packet-sha256")+1]==OLD_PACKET_SHA,
        "original live source/launcher identity")
    success=record["exitCode"]==0
    require((success and record.get("error") is None and d.get("error") is None and d.get("succeeded") is True) or
        (not success and record.get("error")=="exit code" and d.get("error")=="exit code" and
         d.get("succeeded") is False),"completed failure is not numerical success")
    admission=read(checked(args.prior_admission,args.prior_admission_sha256))
    plan=read(checked(args.prior_execution_plan,args.prior_execution_plan_sha256))
    stops=read(checked(args.prior_stop_retain,args.prior_stop_retain_sha256))
    require(set(admission["cards"])=={"4","5","6","7"} and len(plan["shards"])==4 and len(stops)==4,
        "original four owned lease records")
    by_id={s["id"]:s for s in stops};entries=[]
    require(len(by_id)==4 and {e["physical_card"] for e in plan["shards"]}=={4,5,6,7} and
        len({a["container_id"] for a in admission["cards"].values()})==4,"four unique original leases")
    for entry in plan["shards"]:
        card=entry["physical_card"];a=admission["cards"][str(card)];cid=a["container_id"]
        require(entry["batches"]==list(range(1+4*(card-4),5+4*(card-4))) and
            entry["container_name"]==a["container_name"] and entry["create_argv_sha256"]==a["create_argv_sha256"],
            "prior contiguous plan must NOT be relabelled balanced")
        stop=by_id.get(cid,{})
        require(stop.get("name")==entry["container_name"] and stop.get("status") in("exited","created") and
            stop.get("deleted") is False,"exact prior STOPPED/RETAINED refs")
        entries.append((entry,cid))
    return {"operation_id":PRIOR_OPERATION,"prior_success":success,"entries":entries,"raw_terminal_sha256":sha(args.prior_terminal)}
def execute(args,prepared):
    require(os.environ.get("DAMP_SELECTED_ROW_DISPATCH_EXECUTE")=="1","NEW MAIN execution opt-in")
    proof=prior_release(args) # Before any new directory/Docker/NPU.
    planner,host,full,selected,safety,_=prepared
    ORIGINAL.deadline(ORIGINAL.GATE_TIMEOUT+ORIGINAL.CLEANUP_SECONDS)
    initial=make_plan(args.run_id,planner,args.packet_sha256)
    audit=ORIGINAL.ROOT/("selected-row-prior-"+args.run_id)
    require(not audit.exists() and not audit.is_symlink(),"new prior-release audit only")
    audit.mkdir();errors=[];cmd=ORIGINAL.Commands(audit,errors)
    for entry,cid in proof["entries"]:
        actual=host.inspect(cmd,cid,"prior-stopped-inspect");host.inspect_proof(actual,entry,cid)
        require(actual["State"].get("Running") is False and actual["State"].get("Status") in("exited","created") and
            actual["State"].get("Pid")==0,"actual prior lease must already be stopped; no external stop")
    ORIGINAL.emit(audit/"PRIOR_RELEASE.json",proof,errors)
    namespace=dict(vars(ORIGINAL))
    namespace.update(BASE=HERE,packet=packet,source_preparation=source_preparation,make_plan=make_plan,
        validate_shards=validate_shards)
    f=ORIGINAL.execute
    result=types.FunctionType(f.__code__,namespace,f.__name__,f.__defaults__,f.__closure__)(args,prepared)
    return {"status":"selected_row_balanced_dispatch_pass","original_controller_result":result,
        "prior_release":str(audit/"PRIOR_RELEASE.json"),"serving_ready":False,"performance_claim":False}
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true");p.add_argument("--run-id",default="selected_row_v1")
    p.add_argument("--packet-manifest",type=Path,default=HERE/"PACKET.json");p.add_argument("--packet-sha256")
    p.add_argument("--parent-operation-receipt",type=Path);p.add_argument("--parent-operation-sha256")
    p.add_argument("--allow-cpu-selector",action="store_true")
    p.add_argument("--prior-args-sha256")
    for name in ("prior-terminal","prior-admission","prior-execution-plan","prior-stop-retain"):
        p.add_argument("--"+name,type=Path);p.add_argument("--"+name+"-sha256")
    args=p.parse_args(argv)
    if args.execute:
        for n in ("packet_sha256","parent_operation_receipt","parent_operation_sha256","prior_args_sha256",
            "prior_terminal","prior_terminal_sha256","prior_admission","prior_admission_sha256",
            "prior_execution_plan","prior_execution_plan_sha256","prior_stop_retain","prior_stop_retain_sha256"):
            require(getattr(args,n) is not None,"MAIN original ref missing: "+n)
    prepared=source_preparation(args.packet_sha256)
    if not args.execute:
        print(json.dumps({"schema":"damp-selected-row-balanced-plan/v1","status":"dry-not-executed",
            "plan":make_plan(args.run_id,prepared[0],sha(HERE/"PACKET.json")),
            "sources":prepared[-1],"no_docker_or_npu":True,"launchable":False},allow_nan=False));return 0
    print(json.dumps(execute(args,prepared),allow_nan=False));return 0
if __name__=="__main__":raise SystemExit(main())
