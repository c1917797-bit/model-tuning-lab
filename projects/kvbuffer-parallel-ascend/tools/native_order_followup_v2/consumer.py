#!/usr/bin/env python3
"""NEW v2 raw numerical consumer. No v1 PASS conversion or model launcher admission."""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
import binding as b
PYTHON="/usr/local/python3.12.13/bin/python3"
def flags(argv):
    result={};i=0
    while i<len(argv):
        k=argv[i];b.require(k.startswith("--") and k not in result,"unique explicit runner flags")
        if k=="--execute":result[k]=True;i+=1;continue
        if k=="--batches":
            j=i+1
            while j<len(argv) and not argv[j].startswith("--"):j+=1
            b.require(j>i+1,"true batch group");result[k]=argv[i+1:j];i=j;continue
        b.require(i+1<len(argv) and not argv[i+1].startswith("--"),"flag value")
        result[k]=argv[i+1];i+=2
    return result
def terminal(a,read):
    keys={"report","identity","operation","stdout","stderr","child","peer_id","operation_id",
          "command","args","cwd","producer_sources","expected"}
    b.require(type(a) is dict and set(a)==keys,"MAIN-issued exact NEW RunAuthority")
    r=b.obj(a["operation"],read);root=r.get("structuredContent",r)
    b.require(root.get("schema")=="agentweb.operation/v1" and root.get("kind")=="exec"
              and root.get("operationId")==a["operation_id"] and root.get("terminal") is True
              and root.get("status")=="completed" and root.get("succeeded") is True
              and root.get("error") is None,"actual original successful tool terminal")
    o=root["operation"];record=o["result"]["record"]
    b.require(a["peer_id"]==b.PEER and o.get("routeDecision")=="peer_direct"
              and o.get("targetPeerId")==b.PEER and o.get("fallbackUsed") is False
              and record.get("id")==a["operation_id"] and record.get("state")=="completed"
              and record.get("exitCode")==0 and record.get("error") is None
              and record.get("cancelled") is False and record.get("timedOut") is False,
              "original zero/notcancel/nottimeout direct operation")
    b.require(record.get("command")==a["command"] and record.get("args")==a["args"]
              and record.get("cwd")==a["cwd"]==str(b.ROOT) and a["command"]=="/usr/bin/python3"
              and type(a["args"]) is list,"exact original command/argv/cwd")
    producer=a["producer_sources"]
    b.require(type(producer) is dict and producer,"MAIN reviewed actual producer closure")
    for path,h in producer.items():b.raw(dict(path=path,sha256=h),read)
    argv=a["args"]
    if "-c" in argv:
        b.require(argv.count("-c")==1 and argv.index("-c")+1<len(argv)
                  and b.digest(argv[argv.index("-c")+1].encode()) in producer.values(),
                  "original inline MAIN program bytes bound to reviewed source")
    else:
        b.require(any(v in producer for v in argv),"original file controller bound to reviewed source")
    stdout=b.raw(a["stdout"],read).decode();stderr=b.raw(a["stderr"],read).decode()
    b.require(record.get("stdout")==stdout and record.get("stderr")==stderr,"original unedited outer streams")
    markers=[b.clean(line[len(b.PREFIX):]) for line in stdout.splitlines() if line.startswith(b.PREFIX)]
    b.require(markers and all(type(x) is dict and set(x)=={"report","identity","child"} for x in markers),
              "actual NEW parent marker protocol")
    for x in markers:
        for value in x.values():b.ref(value)
    b.require(len({x["child"]["path"] for x in markers})==len(markers)
              and len({x["report"]["path"] for x in markers})==len(markers),
              "unique original child/report markers")
    expected={k:a[k] for k in ("report","identity","child")}
    b.require(markers.count(expected)==1,"original stdout binds this exact report/identity/child")
    return record
def runtime_report(report,identity,identity_ref,batches,card,packet,gm,pins,own,finite,bridge,legacy,ar,read):
    middle=batches!=[1] and batches!=[16]
    before={**pins,**own} if middle else pins
    pp=b.protocol(batches,card) if middle else b.split_protocol(batches[0],card,finite,legacy)
    schema="kvbp.intermediate-native-gate/v2" if middle else "kvbp.split-native-gate/v2"
    status="intermediate_batches_kernel_native_eager_graph_pass" if middle else "single_batch_kernel_native_eager_graph_pass"
    b.require(report.get("schema")==schema and report.get("status")==status and report.get("claim")=="kernel-only"
              and "error" not in report and "secondary_finalize_error" not in report
              and report.get("candidate_namespace")==b.NS and report.get("finite_scope")==finite.FINITE_SCOPE,
              "actual v2 complete report, never v1/failure promotion")
    expected_identity_schema="kvbp.native-order-middle-launch/v2" if middle else "kvbp.split-launch-identity/v2"
    b.require(identity.get("schema")==expected_identity_schema and identity.get("protocol")==pp
              and identity.get("image_id")==b.IMAGE and identity.get("physical_devices")==[card]
              and identity.get("logical_to_physical")=={"0":card}
              and all(identity.get(k) is True for k in ("fresh_idle_verified","nonprivileged","source_canary_passed"))
              and identity.get("memory_cgroup_bytes")==8*b.GIB
              and identity.get("source_manifest")==packet["v2_gate_manifest"]
              and identity.get("sources")==before and identity.get("artifact_refs")==ar,"actual launch/source/artifact identity")
    checked,meta=b.artifacts(ar,gm,pins,read)
    b.require(report.get("frozen_receipts")==checked and report.get("artifact_refs")==ar
              and report.get("source_manifest")==packet["v2_gate_manifest"]
              and report.get("sources_before")==before==report.get("sources_after")
              and report.get("launch_identity")==identity and report.get("launch_identity_sha256")==identity_ref["sha256"]
              and report.get("protocol")==pp and report.get("native_sources")==legacy.NATIVE_PINS
              and report.get("candidate_schema")==meta["schema"],"actual completed source64/70/native schema binding")
    script=b.BASE/"middle_run.py" if middle else b.GATE/"run.py"
    b.require(report.get("script_sha256")==before[str(script)] and report.get("cgroup",{}).get("bytes")==8*b.GIB,
              "actual script hash/cgroup")
    native_schema=report.get("native_schema")
    b.require(type(native_schema) is str and all(x in native_schema for x in
              ("npu_recurrent_gated_delta_rule","beta","scale","actual_seq_lengths","ssm_state_indices")),
              "actual native operation schema")
    maps=report.get("loaded_libraries")
    b.require(type(maps) is dict and maps.get(ar["library"]["path"])==ar["library"]["sha256"]
              and maps.get(b.NATIVE_SO)==b.NATIVE_SHA and
              all(type(path) is str and path.startswith("/") and "(deleted)" not in path
                  and re.fullmatch("[0-9a-f]{64}",h) for path,h in maps.items()),
              "actual mapped candidate/native library, not source-only")
    runtime=report.get("runtime",{})
    b.require(runtime.get("logical_device_count")==1 and runtime.get("logical_device")==0
              and type(runtime.get("device_name")) is str and runtime["device_name"]
              and runtime.get("torch")==meta["runtime"]["torch"]
              and runtime.get("torch_npu")==meta["runtime"]["torch_npu"],"same actual immutable image runtime")
    start=datetime.fromisoformat(identity["preflight_utc"].replace("Z","+00:00"))
    b.require(start.tzinfo is not None and type(report.get("created_ns")) is int
              and type(report.get("completed_ns")) is int
              and 0<=report["created_ns"]/1e9-start.timestamp()<=600
              and report["completed_ns"]>report["created_ns"],"original fresh launch/completed timing")
    b.require(len(report["cases"])==4*len(batches) and {x["batch"] for x in report["cases"]}==set(batches),
              "no omitted/duplicated true-T cases")
    for t in batches:
        b.require(b.validate_batch([x for x in report["cases"] if x["batch"]==t],t,finite,bridge)==640,
                  "unchanged 160x4 raw/finite/slot/log/flush/numerical guards")
    if middle:
        b.require(report.get("npu_executed") is True and report.get("serving_ready") is False
                  and report.get("performance_measurement_admitted") is False
                  and report.get("driver_sources")==own
                  and report.get("followup_manifest")==gm["_followup_ref"]
                  and identity.get("followup_manifest")==gm["_followup_ref"],"middle actual/frozen/default service scope")
        b.require(report.get("middle_meta")==identity.get("middle_meta"),"same actual Meta14 Ref")
        m=b.validate_meta14(report["middle_meta"],ar,packet["v2_gate_manifest"],pins,own,read)
        b.require(m["followup_manifest"]==gm["_followup_ref"] and m["schema"]==meta["schema"] and m["prepare_schema"]==meta["prepare_schema"],"Meta14 schema")
    return before,pp
def child(a,report,identity,batches,card,before,packet,pins,own,read):
    c=b.obj(a["child"],read);e=a["expected"]
    b.require(type(e) is dict and set(e)=={"container_id","owner","run_id","physical_device","batches","runner_argv"}
              and e["physical_device"]==card and e["batches"]==batches
              and re.fullmatch("[0-9a-f]{64}",e["container_id"])
              and type(e["owner"]) is str and e["owner"].startswith("kvbuffer-")
              and type(e["run_id"]) is str and e["run_id"],"MAIN external exact child/container/command expectation")
    cid=e["container_id"]
    b.require(c.get("schema")=="kvbp.native-order-child/v2" and c.get("evidence_kind")=="actual-main-execution"
              and c.get("report")==a["report"] and c.get("identity")==a["identity"]
              and c.get("producer_sources")==a["producer_sources"] and c.get("source_before")==before==c.get("source_after")
              and c.get("service_ready") is False and c.get("performance") is False,"actual NEW child, not software authority")
    ex=c["execution"];b.require(ex.get("command") in ("/usr/bin/docker","docker") and ex.get("cwd")==str(b.ROOT)
              and ex.get("exit_code")==0 and ex.get("error") is None and ex.get("cancelled") is False
              and ex.get("timed_out") is False,"actual child zero/notcancel/nottimeout")
    argv=ex["args"];expected=e["runner_argv"]
    b.require(type(argv) is list and argv[:2]==["exec",cid] and type(expected) is list
              and expected[:2]==[PYTHON,"-B"] and argv.count(expected[2])==1
              and argv[argv.index(expected[2])-2:]==expected,"actual image Python runner suffix")
    middle=batches not in ([1],[16]);script=b.BASE/"middle_run.py" if middle else b.GATE/"run.py"
    b.require(expected[2]==str(script),"NEW actual runner path")
    x=flags(expected[3:])
    fixed={"--execute":True,"--physical-device":str(card),"--identity":c["image_identity_path"],
           "--output-dir":c["image_output_dir"]}
    for key,value in report["artifact_refs"].items():
        flag={"build":"build-receipt","meta":"meta-receipt","library":"library"}[key]
        fixed["--"+flag]=value["path"];fixed["--"+flag+"-sha256"]=value["sha256"]
    if middle:
        fixed["--batches"]=[str(t) for t in batches]
        fixed["--followup-manifest"]=report["followup_manifest"]["path"]
        fixed["--followup-manifest-sha256"]=report["followup_manifest"]["sha256"]
        fixed["--middle-meta"]=report["middle_meta"]["path"]
        fixed["--middle-meta-sha256"]=report["middle_meta"]["sha256"]
    else:
        fixed["--batch"]=str(batches[0]);fixed["--source-manifest"]=packet["v2_gate_manifest"]["path"]
        fixed["--source-manifest-sha256"]=packet["v2_gate_manifest"]["sha256"]
    b.require(x==fixed and Path(c["image_output_dir"]).is_absolute()
              and Path("/kvbuffer-results") in Path(c["image_output_dir"]).parents,"exact actual true-T artifact CLI")
    for value in (ex["stdout"],ex["stderr"]):b.raw(value,read)
    inspect=b.obj(c["container_inspect"],read);stopped=b.obj(c["stopped_inspect"],read)
    def inspect_one(rows):
        b.require(type(rows) is list and len(rows)==1,"one actual original inspect")
        value=rows[0];h=value["HostConfig"];labels=value["Config"].get("Labels") or {}
        expected_devices={"/dev/davinci"+str(card):"/dev/davinci0",
            "/dev/davinci_manager":"/dev/davinci_manager","/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
        devices=h.get("Devices") or []
        b.require(value["Id"]==cid and value["Image"]==b.IMAGE and h.get("Privileged") is False
                  and not h.get("DeviceRequests") and h.get("Memory")==h.get("MemorySwap")==8*b.GIB
                  and len(devices)==4 and {d["PathOnHost"]:d["PathInContainer"] for d in devices}==expected_devices
                  and all(d["CgroupPermissions"]=="rwm" for d in devices)
                  and labels.get("model-tuning-lab.owner")==e["owner"]
                  and labels.get("model-tuning-lab.run")==e["run_id"],"original exact owner/image/8GiB/only authorized card")
        return value
    inspect_one(inspect);s=inspect_one(stopped)
    b.require(s["State"].get("Running") is False and s["State"].get("Pid")==0
              and c.get("cleanup")==dict(container_id=cid,stopped=True,retained=True,deleted=False),
              "actual original exact stopped/PID0/retained cleanup")
    proof=b.obj(c["device_proof"],read)
    b.require(proof.get("schema")=="kvbp.native-order-device-binding/v2" and proof.get("container_id")==cid
              and proof.get("image_id")==b.IMAGE and proof.get("physical_devices")==[card]
              and proof.get("logical_to_physical")=={"0":card} and proof.get("preflight_utc")==identity["preflight_utc"]
              and proof.get("separate_canary_not_gate") is True
              and identity["evidence"].get("device_proof")==c["device_proof"]
              and identity["evidence"].get("container_inspect")==c["container_inspect"],
              "actual external proof/canary versus real kernel separation")
    b.require(set(proof.get("raw_refs",{}))=={"canary","mapping","host_processes","cgroup"},"complete original raw proof")
    for value in proof["raw_refs"].values():b.require(b.raw(value,read),"nonempty raw device evidence")
    b.require(proof["raw_refs"]["mapping"]==c["container_inspect"],"exact inspected physical mapping")
    hp=b.ROOT/"projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py"
    host=b.module(hp,pins[str(hp)],"_kv_v2_original_process_parser",read)
    observation=b.obj(c["actual_gate_process"],read);waiting=b.obj(c["waiting_process"],read)
    process=observation["process"]
    b.require(observation.get("physical_card")==card and observation.get("separate_canary_not_gate") is True
              and type(process.get("pid")) is int and process["pid"]>0
              and type(process.get("start_ticks")) is int and process["start_ticks"]>0
              and process["pid"]==waiting.get("pid") and process["start_ticks"]==waiting.get("start_ticks")
              and process.get("argv")==expected and type(process.get("namespace_pids")) is list
              and process["namespace_pids"] and process["namespace_pids"][0]==process["pid"]
              and all(type(x) is int and x>0 for x in process["namespace_pids"]),
              "actual gate PID/starttime/argv continuity, not canary")
    for value in (process,waiting):
        b.require(type(value.get("cgroup")) is str and
                  any(x in (cid,"docker-"+cid+".scope") for line in value["cgroup"].splitlines()
                      for x in line.split(":",2)[-1].split("/")),"actual exact exec cgroup")
    rows=host.parse_processes(observation["npu_smi"])
    b.require([x["pid"] for x in rows[card]]==[process["pid"]],"actual own NPU/PID")
    # Historical replay must not read today's /proc for old protected PIDs.
    pbefore=b.obj(c["protected_processes_before"],read);pafter=b.obj(c["protected_processes_after"],read)
    for value in (pbefore,pafter):
        b.require(value.get("schema")=="kvbp.native-order-protected-processes/v2"
                  and type(value.get("observed_ns")) is int and set(value.get("processes",{}))==set(map(str,range(4))),
                  "actual historical protected0-3 source observation")
        for processes in value["processes"].values():
            b.require(type(processes) is list and all(type(x.get("pid")) is int and x["pid"]>0
                      and type(x.get("start_ticks")) is int and x["start_ticks"]>0 for x in processes),
                      "actual protected PID/starttime identity")
    b.require(pbefore["processes"]==pafter["processes"]==c["protected0_3"]
              and pbefore["observed_ns"]<=report["created_ns"]<=report["completed_ns"]<=pafter["observed_ns"],
              "historical protected identity/time unchanged")
    for x in range(4):
        b.require([r["pid"] for r in rows[x]]==[r["pid"] for r in c["protected0_3"][str(x)]],
                  "original gate protected PID set")
    release=b.raw(c["release_processes"],read).decode();released=host.parse_processes(release)
    b.require(not released[card] and all([r["pid"] for r in released[x]]==
              [r["pid"] for r in c["protected0_3"][str(x)]] for x in range(4)),
              "actual own card released/protected0-3 unchanged")
    b.require(type(c.get("resource_refs")) is list and c["resource_refs"],"original sampled resource refs retained")
    for value in c["resource_refs"]:b.raw(value,read)
    native=b.ref(c["native_library"]);b.require(native["sha256"]==b.NATIVE_SHA,"actual native binary Ref")
    b.raw(native,read)
    return dict(container_id=cid,physical_device=card,batches=batches,process=process,
                raw_authority=a,resource_refs=c["resource_refs"],resource_semantics_independently_validated=False)
def validate_complete(inputs,packet_ref,*,enabled=False,read=b.read_file):
    b.require(enabled is True,"default OFF; explicit MAIN raw evidence validation")
    b.require(type(inputs) is dict and set(inputs)=={"b1","b16","middle"} and type(inputs["middle"]) is list
              and len(inputs["middle"])==4,"complete actual B1/B16 and four middle shards")
    packet,gm,pins,own,finite,bridge,legacy=b.sources(packet_ref,read);gm["_followup_ref"]=packet_ref
    jobs=[(inputs["b1"],[1],5),(inputs["b16"],[16],6)]
    for a in inputs["middle"]:
        e=a.get("expected",{});card=e.get("physical_device")
        b.require(card in b.GROUPS,"authorized exact middle group")
        jobs.append((a,list(b.GROUPS[card]),card))
    b.require({c for _,_,c in jobs[2:]}==set(b.GROUPS),"four distinct middle shards")
    detail=[];seen=set();covered=[];common=None
    for a,batches,card in jobs:
        terminal(a,read)
        report=b.obj(a["report"],read);ident=b.obj(a["identity"],read)
        before,_=runtime_report(report,ident,a["identity"],batches,card,packet,gm,pins,own,
                                finite,bridge,legacy,report["artifact_refs"],read)
        identity=(report["artifact_refs"],report["candidate_schema"],report["native_sources"],report["loaded_libraries"])
        if common is None:common=identity
        else:b.require(identity==common,"same candidate/native artifacts, schemas, source and loaded library identity")
        row=child(a,report,ident,batches,card,before,packet,pins,own,read)
        b.require(row["container_id"] not in seen,"six distinct owned numerical workers")
        seen.add(row["container_id"]);covered+=batches;detail.append(row)
    b.require(sorted(covered)==list(range(1,17)),"all sixteen real token batches, no fake padding")
    return dict(schema="kvbp.native-order-all-T-numerical-checked/v2",
        status="actual_v2_raw_numerical_component_checked",namespace=b.NS,
        source_manifest=packet_ref,gate_source_manifest=packet["v2_gate_manifest"],original_inputs=inputs,
        numerical_batches=list(range(1,17)),unique_cases=64,changing_feedback_steps=10240,details=detail,
        numerical_limits=dict(output=.00303,complete_and_per_head_l2=2e-6),
        component_graph_replay_verified=True,legacy_pass_fabricated=False,
        evidence_kind="MAIN-issued-original-execution-refs-not-cryptographic-authenticity",
        service_launcher_admitted=False,resource_telemetry_semantics_validated=False,
        **{k:False for k in b.FALSE_SCOPE},
        limitations=["full sampled resource semantics remain a separate MAIN consumer/producer review",
                     "v1 plugin/launcher cannot consume new namespace as if old PASS",
                     "48-layer cache lifecycle, mixed scheduling, paired E2E and task accuracy remain pending"])
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--enable",action="store_true")
    p.add_argument("--source-audit",action="store_true")
    for n in ("manifest","inputs"):p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
    p.add_argument("--output");a=p.parse_args(argv)
    if not a.enable and not a.source_audit:
        print(json.dumps(dict(status="OFF",launches_npu=False,serving_ready=False)));return 0
    b.require(a.manifest and a.manifest_sha256,"reviewed actual NEW source Ref")
    pr=dict(path=a.manifest,sha256=a.manifest_sha256)
    if a.source_audit:
        p,_,pins,own,_,_,_=b.sources(pr)
        print(json.dumps(dict(status="source_audit_pass",gate_sources=len(pins),followup_sources=len(own),
                              launches_npu=False,serving_ready=False)));return 0
    b.require(a.inputs and a.inputs_sha256 and a.output,"actual MAIN input Ref/new output")
    ir=dict(path=a.inputs,sha256=a.inputs_sha256)
    result=validate_complete(b.obj(ir),pr,enabled=True);result["input_ref"]=ir;b.write_new(a.output,result)
    print(json.dumps(dict(checked=b.actual_ref(a.output),serving_ready=False)));return 0
if __name__=="__main__":raise SystemExit(main())
