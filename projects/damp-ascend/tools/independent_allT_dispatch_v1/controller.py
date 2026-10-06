#!/usr/bin/env python3
"""MAIN-only true-T restricted correctness dispatcher. Default dry/OFF."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime,timezone
from independent_contract import (BASE_NEW as BASE,REPO,PROJECT,DEADLINE,MODEL_CONFIG,
    packet,source_snapshot,model_geometry,checked,sha,read,require,load,validate_shards)

ROOT=Path("/cache/cch/qwen36-damp-20261006")
GATE_TIMEOUT=3600
CLEANUP_SECONDS=180

def deadline(seconds=0,now=None):
    now=now or datetime.now(timezone.utc)
    left=(datetime.fromisoformat(DEADLINE.replace("Z","+00:00"))-now).total_seconds()
    require(left>seconds,"original DAMP cutoff incl phase/cleanup; never extend")
    return left

def source_preparation(pin=None):
    row=packet(pin)
    planner=load("_independent_allT_planner",PROJECT/"tools/allT_dispatch_plan_v1/plan.py")
    host=load("_independent_allT_host",PROJECT/"tools/allT_dispatch_controller_v1/controller.py")
    full=load("_independent_allT_full",PROJECT/"tools/run_full_capture.py")
    selected=load("_independent_allT_scheduling",PROJECT/"tools/selected_prefill_dispatch_v1/controller.py")
    source=planner.source_admission()
    native,missing=planner.native_identity()
    require(not missing,"actual native source manifest missing: "+repr(missing))
    safety=full.helper()  # Frozen read-only safety imports; no commands at preparation.
    require("torch" not in sys.modules and "torch_npu" not in sys.modules,"source-only host preparation")
    return planner,host,full,selected,safety,dict(source=source,native=native,
        model_geometry=model_geometry(),sources=source_snapshot(),packet_sha256=sha(BASE/"PACKET.json"))

def make_plan(run_id,planner,packet_sha):
    # Same hard resource/device/create-owner contract; NEW runner identity explicit.
    result=planner.make_plan(run_id,ROOT/("allT-dispatch-"+run_id))
    for entry in result["shards"]:
        create=list(entry["docker_create_argv"])
        pos=create.index("--entrypoint")
        create[pos:pos]=["--mount","type=bind,source="+str(MODEL_CONFIG)+",target="+str(MODEL_CONFIG)+",readonly",
                        "-e","DAMP_RUN_INDEPENDENT_ALLT_V1=1"]
        entry["docker_create_argv"]=create
        entry["create_argv_sha256"]=planner.argv_sha(create)
        entry["docker_canary_exec_argv"][-2]=entry["create_argv_sha256"]
        gate=list(entry["gate_argv_source_bound_incomplete"])
        require(gate[2]==str(planner.GATE/"run_all_batch_gate.py"),"unexpected frozen runner argv")
        gate[2]=str(BASE/"runner.py")
        gate += ["--packet-sha256",packet_sha]
        entry["gate_argv_source_bound_incomplete"]=gate
        entry["execution_packet"]="damp-independent-allT-v1"
        entry["reference_anchor"]="six actual B16 whole-vs16xB1 anchors before trueT"
    result.update(execution_packet="damp-independent-allT-v1",launchable=False,
                  calibration_source_lock_required=False,calibrated_plan_count=0)
    return result

def emit(path,value,errors,*,primary=None):
    """Secondary evidence failure may not erase the actual primary failure."""
    try:
        with Path(path).open("x",encoding="utf-8") as f:
            json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write("\n")
        return True
    except BaseException as error:
        row={"path":str(path),"error":repr(error)}
        errors.append(row)
        print("secondary evidence-write failure: "+repr(row),file=sys.stderr,flush=True)
        if primary is None:raise
        return False

def artifact_hash(path,errors,primary=None):
    try:return sha(path) if Path(path).is_file() else None
    except BaseException as secondary:
        row={"path":str(path),"hash_error":repr(secondary)};errors.append(row)
        print("secondary raw-hash error: "+repr(row),file=sys.stderr,flush=True)
        if primary is None:raise
        return None

class Commands:
    """Original stdout/stderr retained; immutable command is never retried."""
    def __init__(self,audit,errors):
        self.audit,self.errors,self.index=Path(audit),errors,0
    def run(self,label,argv,timeout=90,allowed=(0,)):
        self.index+=1;stem="%04d-%s"%(self.index,label)
        out,err=self.audit/(stem+".stdout"),self.audit/(stem+".stderr")
        started=time.monotonic();result=None;primary=None
        try:
            with out.open("xb") as stdout,err.open("xb") as stderr:
                result=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=timeout,check=False)
            if result.returncode not in allowed:raise RuntimeError("actual command exit "+str(result.returncode)+": "+stem)
        except BaseException as error:primary=error
        row={"argv":argv,"exit_code":None if result is None else result.returncode,
             "error":None if primary is None else repr(primary),"stdout":str(out),"stderr":str(err),
             "stdout_sha256":artifact_hash(out,self.errors,primary),
             "stderr_sha256":artifact_hash(err,self.errors,primary),
             "elapsed_seconds":time.monotonic()-started,"automatic_retry":False}
        emit(self.audit/(stem+".receipt.json"),row,self.errors,primary=primary)
        if primary is not None:raise primary
        return out.read_text(errors="replace"),result.returncode
    def json(self,label,argv):
        stdout,_=self.run(label,argv)
        return json.loads(stdout,parse_constant=lambda v:(_ for _ in()).throw(ValueError(v)))

def parallel(cmd,host,entries,cids,key,timeout,monitor=None):
    jobs=[];started=time.monotonic();primary=None
    try:
        for e in entries:
            cid=cids[e["physical_card"]];host.inspect_proof(host.inspect(cmd,cid,"dispatch-inspect"),e,cid)
            argv=host.immutable_exec(e[key],cid)
            stem="parallel-"+key+"-physical"+str(e["physical_card"])
            out,err=cmd.audit/(stem+".stdout"),cmd.audit/(stem+".stderr")
            a=out.open("xb")
            try:b=err.open("xb")
            except BaseException:a.close();raise
            j=dict(entry=e,cid=cid,argv=argv,out=out,err=err,a=a,b=b,proc=None)
            jobs.append(j);j["proc"]=subprocess.Popen(argv,stdout=a,stderr=b)
        while any(j["proc"].poll() is None for j in jobs):
            deadline(CLEANUP_SECONDS)
            require(time.monotonic()-started<=timeout,"single bounded phase timeout; no automatic retry")
            require(all(j["proc"].poll() in(None,0) for j in jobs),"first actual shard failure")
            if monitor is not None:monitor()
            time.sleep(3)
        require(all(j["proc"].returncode==0 for j in jobs),"actual shard nonzero exit")
    except BaseException as error:primary=error
    finally:
        for j in jobs:
            p=j["proc"]
            try:
                if p is not None and p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
            except BaseException as secondary:
                cmd.errors.append(dict(local_exec_cleanup_error=repr(secondary),container_id=j["cid"]))
                if primary is None:primary=secondary
            finally:j["a"].close();j["b"].close()
            row=dict(argv=j["argv"],container_id=j["cid"],
                exit_code=None if p is None else p.returncode,
                stdout=str(j["out"]),stdout_sha256=artifact_hash(j["out"],cmd.errors,primary),
                stderr=str(j["err"]),stderr_sha256=artifact_hash(j["err"],cmd.errors,primary),
                automatic_retry=False,not_performance=True)
            try:emit(cmd.audit/("parallel-"+key+"-physical"+str(j["entry"]["physical_card"])+".receipt.json"),
                     row,cmd.errors,primary=primary)
            except BaseException as secondary:
                if primary is None:primary=secondary
    if primary is not None:raise primary
    return jobs

def execute(args,prepared):
    require(os.environ.get("DAMP_INDEPENDENT_ALLT_EXECUTE")=="1","MAIN opt-in only")
    require(Path.cwd().resolve()==REPO,"canonical host cwd")
    deadline(GATE_TIMEOUT+CLEANUP_SECONDS);packet(args.packet_sha256)
    require(Path(args.packet_manifest).resolve()==BASE/"PACKET.json","this NEW manifest only")
    planner,host,full,selected,safety,source=prepared
    root=ROOT/("allT-dispatch-"+args.run_id)
    initial=make_plan(args.run_id,planner,args.packet_sha256)
    require(not root.exists() and not root.is_symlink(),"new one-shot output only")
    raw=read(checked(args.parent_operation_receipt,args.parent_operation_sha256))
    terminal=selected.parent_terminal(raw,host) # Nonzero completed remains FAILED; scheduling only.
    root.mkdir(exist_ok=False);audit=root/"launch";audit.mkdir()
    errors=[];cmd=Commands(audit,errors);entries=initial["shards"];cids={}
    primary=None;protected=None;results=None
    try:
        emit(audit/"SOURCE.json",dict(packet=packet(args.packet_sha256),source=source,initial_plan=initial),errors)
        emit(audit/"PARENT_TERMINAL.json",selected.parent_stopped(cmd,host,full,args),errors)
        image=cmd.json("image-inspect",["docker","image","inspect",planner.IMAGE])
        require(len(image)==1 and image[0]["Id"]==planner.IMAGE and image[0]["Architecture"]=="arm64","immutable actual image")
        before=host.fresh_resources(cmd,safety,planner,allow_selector=args.allow_cpu_selector)
        protected=before["protected"];emit(audit/"PRELAUNCH.json",before,errors)
        host.absent_names(cmd,entries)
        for e in entries:Path(e["host_output_mount"]).mkdir(exist_ok=False)
        source_preparation(args.packet_sha256)
        for e in entries:
            deadline(GATE_TIMEOUT+CLEANUP_SECONDS)
            stdout,_=cmd.run("create-physical"+str(e["physical_card"]),e["docker_create_argv"])
            cid=stdout.strip();require(re.fullmatch("[a-f0-9]{64}",cid),"unknown create; do not guess/reclaim/retry")
            cids[e["physical_card"]]=cid
            host.inspect_proof(host.inspect(cmd,cid,"created-inspect"),e,cid)
            cmd.run("start-physical"+str(e["physical_card"]),["docker","start",cid])
            actual=host.inspect(cmd,cid,"started-inspect");host.inspect_proof(actual,e,cid)
            host.cgroup_record(actual,cid,8*host.GIB,1)
            cmd.run("file-source-preflight",["docker","exec",cid,planner.PYTHON,"-B","-c",
                                                host.filesystem_preflight_code(planner)])
        emit(audit/"CANARY_PRECHECK.json",host.fresh_resources(cmd,safety,planner,protected,args.allow_cpu_selector),errors)
        jobs=parallel(cmd,host,entries,cids,"docker_canary_exec_argv",90)
        for j in jobs:emit(j["entry"]["expected_canary_path"],host.json_line(j["out"],"damp_allT_canary_v1"),errors)
        final=host.fresh_resources(cmd,safety,planner,protected,args.allow_cpu_selector)
        info=root/"engine-info.json";emit(info,final["docker_info"],errors)
        admission=dict(schema="damp_allT_MAIN_live_admission_v1",observed_at_unix_ns=final["observed_at_unix_ns"],
            capture_operation_id=host.PARENT_OPERATION,capture_terminal=True,owned_TP4_lease_released=True,
            physical_npu_ids=[4,5,6,7],exclusive_resource_check_passed=True,protected_NPU0_3_unchanged=True,
            ordinary_mem_available_bytes=final["ordinary_mem_available_bytes"],
            per_card_cgroup_limit_bytes=8*host.GIB,free_disk_bytes=final["free_disk_bytes"],
            docker_cpu_capacity=dict(observed_at_unix_ns=final["observed_at_unix_ns"],
                info_path=str(info),info_sha256=sha(info),per_numeric_shard_cpu_quota=1,
                numeric_shards_cpu_quota=4,optional_selector_cpu_quota=2,joint_cpu_quota=6,
                formal_performance_exclusive=True),cards={})
        emit(audit/"FINAL_PRECHECK.json",final,errors)
        for e in entries:
            cid=cids[e["physical_card"]];actual=host.inspect(cmd,cid,"final-inspect");host.inspect_proof(actual,e,cid)
            proof=dict(physical_npu_ids=[e["physical_card"]],logical_to_physical={"0":e["physical_card"]},
                privileged=False,exclusive_resource_check_passed=True,observed_at_unix_ns=time.time_ns(),
                container_id=cid,container_inspect=actual,fresh_resource_audit=str(audit/"FINAL_PRECHECK.json"))
            emit(e["expected_device_proof_path"],proof,errors)
            admission["cards"][str(e["physical_card"])]=dict(container_name=e["container_name"],container_id=cid,
                container_image_id=planner.IMAGE,create_argv_sha256=e["create_argv_sha256"],
                fresh_created_from_this_plan=True,inspect_single_card_scope_passed=True,
                device_proof=e["expected_device_proof_path"],device_proof_sha256=sha(e["expected_device_proof_path"]),
                canary=e["expected_canary_path"],canary_sha256=sha(e["expected_canary_path"]))
        emit(root/"admission.json",admission,errors)
        planner.validate_live_admission(admission,entries,planner.gate_contract(),time.time_ns())
        source_preparation(args.packet_sha256);deadline(GATE_TIMEOUT+CLEANUP_SECONDS)
        emit(audit/"EXECUTION_PLAN.json",dict(shards=entries,immutable_ID_exec=True,not_performance=True),errors)
        count=[0]
        def monitor():
            count[0]+=1;host.monitor_owned(cmd,entries,cids,protected,audit,count[0],
                final["mount_headroom"]["daemon_identity"],args.allow_cpu_selector)
        parallel(cmd,host,entries,cids,"docker_gate_exec_argv",GATE_TIMEOUT,monitor)
        reports=[read(Path(e["gate_output"])/"report.json") for e in entries]
        results=validate_shards(reports,args.packet_sha256)
        source_preparation(args.packet_sha256);deadline(CLEANUP_SECONDS)
        emit(audit/"AGGREGATE.json",dict(source_bound_gate=results,
            reports=[dict(path=str(Path(e["gate_output"])/"report.json"),
                          sha256=sha(Path(e["gate_output"])/"report.json")) for e in entries],
            npu_executed=True,serving_ready=False,performance_claim=False,task_accuracy_claim=False),errors)
    except BaseException as error:
        primary=error;retained=[]
        for e in entries:
            p=Path(e["gate_output"])/"report.json"
            try:retained.append(dict(physical=e["physical_card"],path=str(p),
                sha256=sha(p) if p.is_file() else None,content=read(p) if p.is_file() else None))
            except BaseException as secondary:retained.append(dict(physical=e["physical_card"],copy_error=repr(secondary)))
        emit(audit/"FAILURE.json",dict(original_error=repr(primary),nullable_gate_reports=retained,
            automatic_retry=False,unknown_creates_not_reclaimed=True,scope="not paper-wide no-go"),errors,primary=primary)
    finally:
        stops=[]
        for e in entries:
            cid=cids.get(e["physical_card"])
            if cid is not None:
                try:stops.append(host.stop_owned(cmd,e,cid))
                except BaseException as secondary:
                    stops.append(dict(id=cid,stop_error=repr(secondary),deleted=False))
                    if primary is None:primary=secondary
        try:emit(audit/"STOP_RETAIN.json",stops,errors,primary=primary)
        except BaseException as secondary:
            if primary is None:primary=secondary
        if cids:
            try:
                safety.output=lambda argv,timeout=30:cmd.run("release-safety",argv,timeout)[0]
                released=safety.idle_snapshot();rows=host.parse_processes(released["npu_smi"])
                require(host.protected_fingerprint(rows)==protected,"protected0-3 changed; no external signals")
                require(all(not rows[card] for card in range(4,8)),"4-7 not fully released; MAIN attention")
                emit(audit/"POST_RELEASE.json",dict(snapshot=released,protected=protected),errors,primary=primary)
            except BaseException as secondary:
                if primary is None:primary=secondary
                emit(audit/"RELEASE_FAILURE.json",dict(error=repr(secondary),no_external_signals=True),errors,primary=primary)
    if primary is not None:raise primary
    require(not errors,"evidence/cleanup errors preclude PASS")
    emit(audit/"RESULT.json",dict(status="independent_restricted_allT_dispatch_pass",aggregate=results,
        exact_owned_containers_stopped_and_retained=True,capture_terminal=terminal,
        serving_ready=False,general_sr_supported=False,calibrated_plan_count=0,
        performance_claim=False,task_accuracy_claim=False,deadline=DEADLINE),errors)
    return dict(status="independent_restricted_allT_dispatch_pass",audit=str(audit),not_performance=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true");p.add_argument("--run-id",default="independent_v1")
    p.add_argument("--packet-manifest",type=Path,default=BASE/"PACKET.json");p.add_argument("--packet-sha256")
    p.add_argument("--parent-operation-receipt",type=Path);p.add_argument("--parent-operation-sha256")
    p.add_argument("--allow-cpu-selector",action="store_true")
    args=p.parse_args()
    if args.execute:
        require(os.environ.get("DAMP_INDEPENDENT_ALLT_EXECUTE")=="1","MAIN explicit execution opt-in")
        for f in("packet_sha256","parent_operation_receipt","parent_operation_sha256"):
            require(getattr(args,f) is not None,"missing actual authority "+f)
    prepared=source_preparation(args.packet_sha256)
    if not args.execute:
        print(json.dumps(dict(schema="damp-independent-allT-plan/v1",status="dry-plan-not-executed",
            source=prepared[-1],plan=make_plan(args.run_id,prepared[0],sha(BASE/"PACKET.json")),
            no_docker_or_npu=True,launchable=False,serving_ready=False,performance_claim=False,
            pending=["MAIN full review","actual original MA0455 terminal hash","exact parent stopped",
                     "fresh aggregate resources and one-card canaries","six genuine native split anchors"]),
            allow_nan=False));return 0
    print(json.dumps(execute(args,prepared),allow_nan=False));return 0
if __name__=="__main__":raise SystemExit(main())
