#!/usr/bin/env python3
"""Actual middle producer consumer. Stdlib/default OFF. No device acquisition."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
BASE=PROJECT/"tools/middle_service_bridge_v1"
SPLIT=PROJECT/"tools/split_service_consumer_v1"
PROGRAM=PROJECT/"tools/middle_batch_launch_v1/main_program.py"
PROGRAM_SHA="9c2ea05ff8e7910d84fc0ebb7e3d409118c30bf45d1971b00f11acb7ad641923"
RUNNER=PROJECT/"tools/middle_batch_gate_v1/run.py"
RUNNER_SHA="16ed62857871e4576694802bd45afb2a3ec70d726f90f2687860689b92ef3a10"
PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
GROUPS={4:[2,14,15],5:[7,11,13],6:[3,4,9,12],7:[5,6,8,10]}
RESULT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006")
META14={"path":str(RESULT/"preflight-middle-meta14-v1/results/report.json"),
        "sha256":"1c417ac0cae44e11842bd2a9434acd1cf537568f2bf19878ebb19dca64c65e75"}
OWN=("contract.py","launch.py","pair.py","test_contract.py","READY.md")
FALSE_SCOPE=("service_ready","model_lifecycle_verified","matched_e2e_verified",
             "task_accuracy_verified","formal_performance_authorized","graph_service_validated")
GIB=1024**3
HOST_RELEASE_REFS=[{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/FAILURE.json","sha256":"c30bef4436562085165fd273f21c22eeb163eafa843a7574c24c29dcb8c2d567"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/STOP_RETAIN.json","sha256":"4259d591b59c82cda036304c7da4b2484c84d3e141e7c39376d5cf8825f8a67b"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/POST_RELEASE.json","sha256":"6bd2b348f54c6bfb77e50f72583bc500138d6f8f9ef25ee8af41600008e3d752"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/parallel-docker_gate_exec_argv-physical4.receipt.json","sha256":"166a5874ac9aa5168adbcd006d346f33baf46d0bf88d14357c32426d1543d6e7"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/parallel-docker_gate_exec_argv-physical5.receipt.json","sha256":"3cda0e635e1c093672acbcd7f49c3882f8dbd548fdc22e3eaa0c776268cb0493"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/parallel-docker_gate_exec_argv-physical6.receipt.json","sha256":"40018f313339139df9987e46fd0dbd6b107c0317ce6d501aac1e948e253cab2b"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/parallel-docker_gate_exec_argv-physical7.receipt.json","sha256":"3fad1f7548c922b92a8bbcdc7c1495a05e0a17b1eae46f67a8c9c1f5805ecf49"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10310-owned-stop.receipt.json","sha256":"95da9f6e854e41be43b0cbfd8087e7f30206ef1018a54ee9538c7e359fb2894c"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10311-stop-afterinspect.receipt.json","sha256":"7609f420438b3dbfa2ff41a448bab0a5472adb28a1a12e1fa3545ff55e9791e5"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10313-owned-stop.receipt.json","sha256":"936389a7d0841770e2484db0a5eacc3672d07f07b990f8ae5746db3b9f8f7a06"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10314-stop-afterinspect.receipt.json","sha256":"3cb01c63868632086c6e3bbb3e7c7c4674d0364248892515ad8970767b4d0c33"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10316-owned-stop.receipt.json","sha256":"efb631079d6ed2c270c5d82429ad6e093df2f124f0ced229817ae56af99654eb"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10317-stop-afterinspect.receipt.json","sha256":"4671dd7366625dc8aa7d68106003deebeb13a2323c9ceb1d40a6c3fd81a1f002"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10319-owned-stop.receipt.json","sha256":"80b15ac5c79c9b8553334733fe7f48de8acdbbc13421fa29ed5b71e3c3a48090"},{"path":"/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/launch/10320-stop-afterinspect.receipt.json","sha256":"87bb0174bd814fd2550805ff1437121fcb7c7e471e895164ebdf7b193e3b3ae3"}]

def require(ok,why):
    if not ok:raise ValueError(why)
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def clean(data):
    def bad(x):raise ValueError("nonfinite JSON: "+x)
    value=json.loads(data,parse_constant=bad)
    def walk(x):
        if isinstance(x,float):require(math.isfinite(x),"nonfinite JSON metric")
        elif isinstance(x,dict):
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(value);return value
def read_file(path):
    p=Path(path)
    require(p.is_absolute() and ".." not in p.parts and p.is_file() and not p.is_symlink(),
            "ordinary absolute source/evidence file")
    return p.read_bytes()
def ref(value):
    require(type(value) is dict and set(value)=={"path","sha256"} and
            type(value["path"]) is str and Path(value["path"]).is_absolute() and
            ".." not in Path(value["path"]).parts and type(value["sha256"]) is str and
            re.fullmatch("[0-9a-f]{64}",value["sha256"]),"exact absolute SHA Ref")
    return value
def raw(value,read=read_file):
    ref(value);data=read(value["path"])
    require(type(data) is bytes and digest(data)==value["sha256"],"original byte drift: "+value["path"])
    return data
def obj(value,read=read_file):return clean(raw(value,read))
def actual_ref(path,read=read_file):return {"path":str(path),"sha256":digest(read(str(path)))}
def write_new(path,value):
    with Path(path).open("xb") as f:f.write(canonical(value)+b"\n")
def load_pinned(path,wanted,name,read=read_file):
    require(digest(read(str(path)))==wanted,"imported frozen source drift: "+str(path))
    s=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(s)
    sys.modules[name]=m;s.loader.exec_module(m)
    require(Path(m.__file__).resolve()==path and "torch" not in sys.modules and "torch_npu" not in sys.modules,
            "byte-bound stdlib module identity")
    return m

def sources(packet_ref,read=read_file):
    require(packet_ref["path"]==str(BASE/"PACKET.json"),"NEW packet at canonical path")
    p=obj(packet_ref,read)
    require(p.get("schema")=="kvbp.middle-service-bridge-sources/v1" and
            p.get("default_enabled") is False and set(p.get("sources",{}))==set(OWN),
            "exact NEW five-file closure/default OFF")
    for n,h in p["sources"].items():
        require(digest(read(str(BASE/n)))==h,"NEW source drift: "+n)
    deps=p.get("dependencies",{})
    require(type(deps) is dict and len(deps)==60 and deps.get(str(PROGRAM))==PROGRAM_SHA and
            deps.get(str(RUNNER))==RUNNER_SHA,"exact reviewed dependency closure60")
    for path,h in deps.items():
        ref({"path":path,"sha256":h})
        require(digest(read(path))==h,"frozen dependency drift: "+path)
    old=load_pinned(SPLIT/"consumer.py",deps[str(SPLIT/"consumer.py")],"_kvbp_middle_old_consumer",read)
    # The original consumer rechecks original49/artifacts. It does not run host npu-smi.
    return p,old

def terminal(authority,read=read_file):
    require(type(authority) is dict and set(authority)=={
        "operation","operation_id","peer_id","command","args","cwd","stdout","stderr",
        "inputs","program","shards"},"MAIN-issued exact middle RunAuthority")
    require(authority["peer_id"]==PEER and re.fullmatch("exec-[0-9a-f]+",authority["operation_id"]),
            "intended direct peer/original operation")
    op=obj(authority["operation"],read);root=op.get("structuredContent",op)
    require(root.get("schema")=="agentweb.operation/v1" and root.get("kind")=="exec" and
            root.get("operationId")==authority["operation_id"] and root.get("terminal") is True and
            root.get("status")=="completed" and root.get("succeeded") is True and root.get("error") is None,
            "actual successful terminal, not host cleanup release or status-only")
    o=root["operation"];r=o["result"]["record"]
    require(o.get("routeDecision")=="peer_direct" and o.get("targetPeerId")==PEER and
            o.get("fallbackUsed") is False and r.get("id")==authority["operation_id"] and
            r.get("state")=="completed" and r.get("exitCode")==0 and r.get("error") is None and
            r.get("cancelled") is False and r.get("timedOut") is False,
            "actual original zero/notcancel/nottimeout direct execution")
    expected=["-B","-c",raw(authority["program"],read).decode(),
              "--execute","--inputs",authority["inputs"]["path"],
              "--inputs-sha256",authority["inputs"]["sha256"]]
    require(authority["program"]=={"path":str(PROGRAM),"sha256":PROGRAM_SHA} and
            authority["command"]=="/usr/bin/python3" and authority["args"]==expected and
            authority["cwd"]==str(ROOT) and r.get("command")==authority["command"] and
            r.get("args")==expected and r.get("cwd")==str(ROOT),"actual exact -c program/MAIN inputs/argv")
    stdout=raw(authority["stdout"],read).decode();stderr=raw(authority["stderr"],read).decode()
    require(r.get("stdout")==stdout and r.get("stderr")==stderr,"raw outer streams are original tool streams")
    shards=[];complete=[]
    for line in stdout.splitlines():
        if line.startswith("MAIN_KVBUFFER_MIDDLE_SHARD "):
            shards.append(clean(line[len("MAIN_KVBUFFER_MIDDLE_SHARD "):]))
        elif line.startswith("MAIN_KVBUFFER_MIDDLE_COMPLETE "):
            complete.append(clean(line[len("MAIN_KVBUFFER_MIDDLE_COMPLETE "):]))
    require(len(shards)==4 and {s.get("physical_card") for s in shards}==set(GROUPS) and
            len(complete)==1 and authority["shards"]==shards,"unique original four shard markers")
    for s in shards:
        require(set(s)=={"physical_card","batches","child","report"} and
                s["batches"]==GROUPS[s["physical_card"]],"true balanced groups, no fake contiguous endpoints")
        ref(s["child"]);ref(s["report"])
    return shards,complete[0]

def false_scope(value):
    require(all(value.get(k) is False for k in FALSE_SCOPE),"no component-to-service/quality/performance promotion")

def metadata(meta,oldmeta,pins49,libsha,buildsha):
    require(meta.get("status")=="actual_14_positive_Meta_pass" and "error" not in meta and
            meta.get("schema")==oldmeta["schema"] and meta.get("prepare_schema")==oldmeta["prepare_schema"] and
            meta.get("sources_before")==pins49==meta.get("sources_after") and
            meta.get("library_sha256")==libsha and meta.get("build_receipt_sha256")==buildsha and
            meta.get("loaded_libraries",{}).get(str(RESULT/"build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"))==libsha,
            "actual Meta14 source49/schema/loaded SO identity; schema is unchanged Torch schema")
    require(meta.get("meta")==[dict(T=t,slots=t+3,shape=[t,12,128],dtype="torch.bfloat16") for t in range(2,16)]
            and meta.get("output_alias_checks") is True and
            all(meta.get(k) is False for k in ("npu_executed","physical_nd_proven","graph_proven","service_ready")),
            "true14 positive Meta/nonalias only, no device proof")

def process(observation,waiting,cid,card,argv,protected,host):
    p=observation["process"]
    require(observation.get("physical_card")==card and observation.get("separate_canary_not_gate") is True and
            type(p.get("pid")) is int and p["pid"]>0 and
            type(p.get("start_ticks")) is int and p["start_ticks"]>0 and
            p["pid"]==waiting.get("pid") and p["start_ticks"]==waiting.get("start_ticks") and
            p.get("argv")==argv,"actual exec PID/starttime/argv continuity, not separate canary")
    require(type(p.get("namespace_pids")) is list and p["namespace_pids"] and
            all(type(x) is int and x>0 for x in p["namespace_pids"]) and p["namespace_pids"][0]==p["pid"],
            "actual namespace PID chain")
    for value in (p,waiting):
        require(type(value.get("cgroup")) is str and
                any(x in (cid,"docker-"+cid+".scope") for line in value["cgroup"].splitlines()
                    for x in line.split(":",2)[-1].split("/")),"exact container cgroup")
    rows=host.parse_processes(observation["npu_smi"])
    require([x["pid"] for x in rows[card]]==[p["pid"]],"actual one real NPU PID on own physical card")
    require(host.protected_fingerprint(rows)==protected,"protected0-3 fingerprint changed")
    return dict(pid=p["pid"],start_ticks=p["start_ticks"],physical_card=card)

def middle(authority,split_checked,packet,old,read=read_file,listing=None):
    shards,complete=terminal(authority,read)
    sp,pins49,_,bridge,d,host,helper=old.sources(split_checked["source_manifest"],read)
    deps=packet["dependencies"]
    m=load_pinned(PROGRAM,PROGRAM_SHA,"_kvbp_middle_reviewed_main",read)
    runner=load_pinned(RUNNER,RUNNER_SHA,"_kvbp_middle_frozen_driver",read)
    split=load_pinned(PROJECT/"tools/split_gate_v1/contract.py",
                      pins49[str(PROJECT/"tools/split_gate_v1/contract.py")],"_kvbp_middle_gate_contract",read)
    pins54={**pins49,str(PROJECT/"tools/split_dispatch_v1/PACKET.json"):old.PACKET_SHA,
            str(RUNNER):RUNNER_SHA,**m.RELEASE_PINS}
    require(len(pins54)==54 and all(deps.get(p)==h for p,h in pins54.items()),"original54 publication identity")
    config=obj(authority["inputs"],read)
    require(config.get("main_approved") is True and config.get("main_program_sha256")==PROGRAM_SHA and
            config.get("middle_meta14")==META14 and config.get("release_authority_kind")=="host_job_cleanup_observed"
            and config.get("release_helper_sources")==m.RELEASE_PINS,"MAIN exact explicit program/Meta/release prerequisites")
    phase=config.get("phase_seconds")
    require(type(phase) is dict and set(phase)==set(map(str,GROUPS)) and
            all(type(v) is int and 1800<=v<=10800 for v in phase.values()),"explicit original single-phase budgets")
    joint=obj(split_checked["joint"],read)
    require(config["formal_start_utc"]==joint["inputs"]["formal_start_utc"] and
            config["deadline_utc"]==joint["inputs"]["deadline_utc"],"one real KV formal clock, not middle reset")
    slug=config["run_slug"];require(re.fullmatch("[a-z0-9][a-z0-9-]{0,40}",slug),"bounded original run slug")
    root=RESULT/("middle-main-"+slug);audit=root/"audit"
    program=obj(actual_ref(audit/"PROGRAM.json",read),read)
    require(program.get("source")==raw(authority["program"],read).decode() and
            program.get("sha256")==PROGRAM_SHA and program.get("inputs")==authority["inputs"] and
            program.get("actual_process_argv")==[authority["command"]]+authority["args"] and
            program.get("source_dependencies")==pins54,"original actual program/cmdline/inputs/source54")
    prerequisite=program["middle_meta14"]
    require(prerequisite==dict(report=META14,status="actual_14_positive_Meta_pass",
            positive_batches=list(range(2,16)),npu_executed=False,
            scope="positive Meta prerequisite only; actual device identity/terminal still required"),"actual Meta producer descriptor")
    metadata(obj(META14,read),old.obj(sp["artifacts"]["meta"],read),pins49,split.LIBRARY_SHA,split.BUILD_SHA)
    release=obj(actual_ref(audit/"PARENT_RELEASE.json",read),read)
    require(release.get("rpc_terminal_reconstructed") is False and release.get("scope")=="release only, not numerical PASS"
            and release.get("source_helpers")==m.RELEASE_PINS,"real host cleanup only, never fabricated RPC/PASS")
    ra=release["authority"]
    require(ra.get("authority_kind")=="host_job_cleanup_observed" and
            ra.get("awmcp_terminal_reconstructed") is False and ra.get("numerical_pass_claimed") is False and
            ra.get("original_failure_retained") is True,"actual prior failure remains failure")
    require(ra.get("references")==HOST_RELEASE_REFS and config.get("release_host_job_refs")==HOST_RELEASE_REFS,
            "exact15 current070e host cleanup producer Refs, no invented terminal")
    for r in ra["references"]:raw(r,read)
    require(config.get("release_host_job_refs")==ra["references"] and
            len(release.get("stopped",[]))==4 and
            all(r["state"].get("Running") is False and r["state"].get("Pid")==0 for r in release["stopped"]) ,
            "explicit original cleanup Refs/four stopped PID0")
    detail=[];seen=set();all_batches=[]
    for marker in sorted(shards,key=lambda x:x["physical_card"]):
        card=marker["physical_card"];job=m.spec(card,slug);ca=Path(job["job_root"])/"audit"
        require(marker["child"]["path"]==str(ca/"CHILD.json") and
                marker["report"]["path"]==str(Path(job["output_root"])/"gate/report.json"),"original child/report namespace")
        child=obj(marker["child"],read);report=obj(marker["report"],read)
        identity_ref=child["identity"];identity=obj(identity_ref,read)
        require(identity_ref["path"]==str(Path(job["launch_root"])/"identity.json") and
                child.get("report")==marker["report"] and child.get("cwd")==str(ROOT) and
                child.get("exit_code")==0 and child.get("source_after")==pins54 and
                child.get("main_program_sha256")==PROGRAM_SHA and child.get("middle_meta14")==prerequisite and
                child.get("service_ready") is False and child.get("performance") is False,
                "actual zero/same producer source54/limited child")
        require(identity.get("schema")=="kvbp.middle-batch-launch-identity/v1" and
                identity.get("physical_devices")==[card] and identity.get("logical_to_physical")=={"0":card}
                and identity.get("image_id")==d.IMAGE and identity.get("fresh_idle_verified") is True and
                identity.get("nonprivileged") is True and identity.get("source_canary_passed") is True and
                identity.get("memory_cgroup_bytes")==8*GIB and identity.get("protocol")==runner.protocol(GROUPS[card],card)
                and identity.get("library_sha256")==split.LIBRARY_SHA and
                identity.get("build_receipt_sha256")==split.BUILD_SHA and identity.get("meta_receipt_sha256")==split.META_SHA
                and identity.get("repo_sources")==split.REPO_PINS and identity.get("native_sources")==split.NATIVE_PINS and
                identity.get("driver_sources")=={"run.py":RUNNER_SHA} and identity.get("native_library_sha256")==runner.NATIVE_SO_SHA,
                "actual source-bound single-card true-T identity")
        ev=identity["evidence"];mapping=obj(ev["mapping"],read)
        require(type(mapping) is list and len(mapping)==1,"actual one original mapping inspect")
        cid=mapping[0]["Id"];require(cid not in seen,"four distinct owned workers");seen.add(cid)
        m.checked_spec(mapping[0],job,cid,d)
        require(all(x.get("CgroupPermissions")=="rwm" for x in mapping[0]["HostConfig"]["Devices"]),
                "exact device-node permissions")
        require(child.get("argv")==m.gate_argv(job,cid,d),"original Docker WAIT/shim/native argv")
        raw(child["stdout"],read);raw(child["stderr"],read)
        fresh=obj(ev["host_processes"],read)
        protected=fresh["protected"]
        require(fresh.get("docker_info",{}).get("NCPU",0)>=5 and fresh.get("available",0)>=fresh.get("joint_ram_required",40*GIB)
                and fresh.get("free_disk_bytes",0)>=fresh.get("disk_required",0) and
                fresh.get("joint_ram_required",0)>=8*GIB,"actual joint budget/raw prelaunch")
        cv=clean(raw(ev["separate_canary"],read))
        require(cv.get("status")=="actual_canary_pass" and cv.get("expected_physical_card")==card and
                cv.get("create_argv_sha256")==digest(canonical(job["create_argv"])) and
                cv.get("canary_program_sha256")==helper.CANARY_SHA,"actual separate source canary")
        for r in (ev["image_sources"],ev["parent_release"]):raw(r,read)
        require(ev["middle_meta14"]==META14 and ev["parent_release"]==actual_ref(audit/"PARENT_RELEASE.json",read),
                "same explicit prerequisites")
        waiting=obj(ev["waiting_bash"],read)
        observed=obj(child["actual_gate_pid"],read)
        require(child["actual_gate_pid"]["path"]==str(ca/"ACTUAL_GATE_NPU_PID.json"),"original actual gate PID Ref")
        argv=child["argv"][child["argv"].index(d.PYTHON):]
        pid=process(observed,waiting,cid,card,argv,protected,host)
        start=datetime.fromisoformat(identity["preflight_utc"].replace("Z","+00:00"))
        require(start.tzinfo is not None and type(report.get("created_ns")) is int and
                0<=report["created_ns"]/1e9-start.timestamp()<=600 and
                report.get("completed_ns",0)>report["created_ns"],"actual preflight-to-gate fresh<=600/completed")
        require(report.get("schema")=="kvbp.intermediate-native-gate/v1" and
                report.get("status")=="intermediate_batches_kernel_native_eager_graph_pass" and
                report.get("claim")=="kernel-only" and "error" not in report and report.get("npu_executed") is True and
                report.get("serving_ready") is False and report.get("performance_measurement_admitted") is False and
                report.get("script_sha256")==RUNNER_SHA and report.get("driver_sources")=={"run.py":RUNNER_SHA} and
                report.get("launch_identity")==identity and report.get("launch_identity_sha256")==identity_ref["sha256"] and
                report.get("protocol")==runner.protocol(GROUPS[card],card) and
                report.get("native_sources")==split.NATIVE_PINS,"complete actual original report/protocol")
        require(report.get("frozen_receipts")==dict(build_receipt_sha256=split.BUILD_SHA,
                    meta_receipt_sha256=split.META_SHA,library_sha256=split.LIBRARY_SHA,
                    repo_sources=split.REPO_PINS,meta_is_not_npu_proof=True) and
                digest(report["candidate_schema"].encode())==report.get("candidate_schema_sha256") and
                digest(report["native_schema"].encode())==report.get("native_schema_sha256") and
                all(x in report["native_schema"] for x in ("npu_recurrent_gated_delta_rule","beta","scale",
                                                          "actual_seq_lengths","ssm_state_indices")) and
                report.get("runtime",{}).get("torch")==old.obj(sp["artifacts"]["meta"],read)["torch"] and
                report["runtime"].get("torch_npu")==old.obj(sp["artifacts"]["meta"],read)["torch_npu"] and
                type(report["runtime"].get("device_name")) is str and report["runtime"]["device_name"],
                "complete frozen receipts/schema hashes/native callable/image versions")
        require(report.get("loaded_libraries",{}).get("/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so")==split.LIBRARY_SHA
                and report.get("loaded_libraries",{}).get(runner.NATIVE_SO)==runner.NATIVE_SO_SHA and
                report.get("candidate_schema")==old.obj(sp["artifacts"]["meta"],read)["schema"]
                and report.get("cgroup",{}).get("bytes")==8*GIB and
                report.get("runtime",{}).get("logical_device_count")==1 and report["runtime"].get("logical_device")==0 and
                all(type(p) is str and p.startswith("/") and "(deleted)" not in p and
                    type(h) is str and re.fullmatch("[0-9a-f]{64}",h)
                    for p,h in report["loaded_libraries"].items()),
                "actual schemas/mapped libraries/cgroup/single runtime domain")
        require(len(report["cases"])==4*len(GROUPS[card]) and
                {r["batch"] for r in report["cases"]}==set(GROUPS[card]),"no omitted/duplicated true-T cases")
        for t in GROUPS[card]:
            require(bridge.validate_cases({"cases":[r for r in report["cases"] if r["batch"]==t]},t)==640,
                    "unchanged original numerical/slot/log/flush/graph/whole-state guards")
            all_batches.append(t)
        stops=old.command_receipts(ca/"cleanup","stopped-inspect",read,listing)
        require(len(stops)==1 and stops[0][1]["argv"]==["/usr/bin/docker","inspect",cid],"actual own cleanup receipt")
        stopped=clean(stops[0][2]["stdout"])
        require(type(stopped) is list and len(stopped)==1,"one actual stopped inspect")
        m.checked_spec(stopped[0],job,cid,d)
        require(stopped[0]["State"].get("Running") is False and stopped[0]["State"].get("Pid")==0 and
                child.get("cleanup")==dict(container_id=cid,stopped=True,retained=True,deleted=False),
                "exact owned stop-retain PID0, not unchecked boolean")
        detail.append(dict(physical_card=card,batches=GROUPS[card],child=marker["child"],report=marker["report"],
                           identity=identity_ref,process=pid,cases=4*len(GROUPS[card]),steps=640*len(GROUPS[card])))
    require(sorted(all_batches)==list(range(2,16)) and complete==dict(cases=56,feedback_steps=8960,
            source_after=pins54,service_ready=False,performance=False),"complete original56/8960 marker/source54")
    return dict(operation=authority["operation"],inputs=authority["inputs"],program=authority["program"],
                details=detail,meta14=META14,cases=56,steps=8960,source54=pins54)

def validate_complete(inputs,packet_ref,*,enabled=False,read=read_file,listing=None):
    require(enabled,"default OFF; explicit reviewed MAIN authority required")
    require(type(inputs) is dict and set(inputs)=={"split_inputs","split_manifest","split_checked","middle"} and
            type(inputs["split_checked"]) is dict and set(inputs["split_checked"])=={"input_ref","checked"},
            "actual split and middle source-bound inputs; status-only unsupported")
    packet,old=sources(packet_ref,read)
    checked=old.validate(inputs["split_inputs"],inputs["split_manifest"],enabled=True,read=read,listing=listing)
    checked["input_ref"]=inputs["split_checked"]["input_ref"]
    supplied=obj(inputs["split_checked"]["checked"],read)
    require(obj(inputs["split_checked"]["input_ref"],read)==inputs["split_inputs"] and supplied==checked,
            "actual original checked split replay and raw inputs")
    result=middle(inputs["middle"],checked,packet,old,read,listing)
    result.update(schema="kvbp.checked-all-T-kernel-prerequisite/v1",
                  status="actual_split_and_middle_raw_prerequisites_checked",
                  source_packet=packet_ref,original_inputs=inputs,split_checked=inputs["split_checked"]["checked"],
                  numerical_batches=list(range(1,17)),cases=64,feedback_steps=10240,
                  component_graph_replay_verified=True,legacy_pass_fabricated=False,
                  evidence_kind="MAIN-issued-original-execution-refs-not-cryptographic-authenticity")
    result.update({k:False for k in FALSE_SCOPE})
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--enable",action="store_true")
    for n in ("packet","inputs"):
        p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
    p.add_argument("--output");p.add_argument("--source-audit",action="store_true")
    a=p.parse_args(argv)
    if not a.enable and not a.source_audit:
        print(json.dumps(dict(status="OFF",launches_npu=False,service_ready=False)));return 0
    require(a.packet and a.packet_sha256,"explicit reviewed NEW packet Ref")
    pr={"path":a.packet,"sha256":a.packet_sha256}
    if a.source_audit:
        packet,_=sources(pr)
        print(json.dumps(dict(status="source-only",dependencies=len(packet["dependencies"]),
                              launches_npu=False,service_ready=False)));return 0
    require(a.inputs and a.inputs_sha256 and a.output,"original inputs/new output")
    ir={"path":a.inputs,"sha256":a.inputs_sha256}
    result=validate_complete(obj(ir),pr,enabled=True);result["input_ref"]=ir
    write_new(a.output,result)
    print(json.dumps(dict(checked=actual_ref(a.output),service_ready=False)));return 0
if __name__=="__main__":raise SystemExit(main())
