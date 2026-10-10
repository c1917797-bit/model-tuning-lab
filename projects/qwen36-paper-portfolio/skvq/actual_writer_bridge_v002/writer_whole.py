"""Read-only original-operation/owned-single4/after-release byte-consumer closure.
No launch, Torch, NumPy or candidate mathematical routine is imported here.
Actual mathematical adjudication must have completed in the exact Devices[] child.
"""
import argparse,copy,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_host as H
import writer_resources as R
def host_argv(root,source,whole_file):
    return ["/usr/bin/env","MAIN_SKVQ_WRITER_HOST_ENABLE=1","/usr/bin/prlimit","--cpu=3600:3600","--",
      "/usr/bin/python3","-B",str(C.ROOT/"writer_host.py"),"--execute","--source-manifest-sha256",
      source["sha256"],"--calibration-whole-ref-json",str(whole_file),"--output",str(root)]
def original(value,argv):
    C.need(value["schema"]=="agentweb.operation/v1","actual original operation schema")
    op=value["operation"];record=op["result"]["record"]
    C.need(value["terminal"]is True and value["status"]=="completed"and value["succeeded"]is True and
      value["error"]is None and op["ok"]is True and op["result"]["state"]=="completed"and
      op["routeDecision"]=="peer_direct"and op["targetPeerId"]=="lgw_a6109c51076a4a2c9d2674ca5a8704a0",
      "real successful whole terminal; failed/unknown/cancel/transport cannot promote")
    C.need([record["command"]]+record["args"]==argv and record["exitCode"]==0 and record.get("error")is None and
      record.get("timedOut")is False and record.get("cancelled")is False,"actual exact whole argv/exit")
    return record
def inspect_cleanup(e,source,Controller,mounts,index):
    npu=index==1;phase=("input-plan","single4-writer","independent")[index]
    devices=({"/dev/davinci4":"/dev/davinci0",**{"/dev/"+x:"/dev/"+x for x in
      ("davinci_manager","devmm_svm","hisi_hdc")}}if npu else {})
    expected=dict(mounts)
    if npu:expected["/usr/local/Ascend/driver"]=("/usr/local/Ascend/driver",False)
    actual={d:(s,bool(rw))for d,(s,rw)in e["mounts"].items()}
    C.need(e["phase"]==phase and e["npu"]is npu and e["mem"]==8*H.GIB and e["devices"]==devices and
      e["env"]==H.environment(npu)and e["source"]==source["sha256"]and e["released"]is True and
      re.fullmatch("[0-9a-f]{64}",e["cid"])and actual==expected,"three exact sequential current owned guests")
    release=C.obj(e["release_ref"])
    C.need(release["cid"]==e["cid"]and release["retained"]is True and release["deleted"]is False and
      release["released"]is True and release["noOOM"]is True and not release.get("secondary")and
      ("release_smi"in release)==npu,"own-only stop-retain; CPU does not claim NPU-idle release")
    stop=C.obj(release["stop"]);argv=[H.DOCKER,"stop","--time","15",e["cid"]]
    C.need(stop["argv"]==argv and stop["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      stop["exit_code"]==0,"exact actual owned stop original")
    raw=C.obj(release["inspect"]);argv=[H.DOCKER,"inspect",e["cid"]]
    C.need(raw["argv"]==argv and raw["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      raw["exit_code"]==0,"exact actual final inspect original")
    rows=json.loads(raw["stdout"]);C.need(len(rows)==1,"one owned final inspect")
    normalized=copy.deepcopy(e);normalized["mounts"]=actual
    Controller.validate(None,rows[0],normalized)
    state=rows[0]["State"]
    C.need(state["Running"]is False and state["Pid"]==0 and state["OOMKilled"]is False and not rows[0].get("ExecIDs"),
      "actual owned stopped/Pid0/noExec/noOOM")
    pre=C.obj(e["mount_preflight_ref"]);fresh=H.preflight_module().observe(expected,phase,source)
    C.need(pre["schema"]==fresh["schema"]and pre["passed"]is True and fresh["passed"]is True and
      pre["source_ref"]==source and pre["phase"]==phase and len(pre["mounts"])==len(fresh["mounts"]),
      "exact source/evidence mount preflight, not declaration")
    for before,after in zip(pre["mounts"],fresh["mounts"]):
        C.need({k:v for k,v in before.items()if k!="identity"}=={k:v for k,v in after.items()if k!="identity"},
          "complete original/current mount source/destination/kind")
        keys=("dev","ino","mode")if before["kind"]=="directory"else tuple(before["identity"])
        C.need(all(before["identity"][k]==after["identity"][k]for k in keys),"original mount object identity")
    return release
def resource_evidence(e):
    value=C.obj(e["resource_ref"]);allocation=value["allocation"]
    C.need(R.allocate(value["host_cpu"],value["daemon_cpu"])==allocation,"actual host1/guest1/reserve2 CPU4 replay")
    total=R.memory_admit(value["host_memory"],value["daemon_memory"],8*H.GIB)
    C.need(total==value["ordinary_floor_bytes"]==int(16.5*H.GIB)and value["memory"]["MemAvailable"]>=total and
      value["memory"]["SwapTotal"]==value["memory"]["SwapFree"]and
      value["disk_available_bytes"]>=(9 if e["npu"]else 8)*H.GIB,"actual ordinary RAM/disk no HugeTLB")
    return value
def child_cli(ref,cid,args,*,npu=False):
    raw=C.obj(ref);argv=[H.DOCKER,"exec"]
    if npu:argv+=["--env","MAIN_OWNED_CID="+cid]
    argv+=[cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"skvq-owned",H.PY,"-B",*args]
    C.need(raw["argv"]==argv and raw["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      raw["exit_code"]==0 and raw["terminated"]is True and raw["primary"]is None,"actual exact four child CLI/exit")
    for row in(raw["stdout"],raw["stderr"]):C.checked(row)
    return raw
def protected(raw,host,smi_ref):
    known={e["cid"]:e["phase"]for e in host["owned"]}
    C.need(set(raw)=={"smi","actual","original","boundary","owned_cids","owned_host_pids","current_cid","current_phase"}and
      raw["smi"]==smi_ref and raw["original"]==host["protected0_3"]and raw["owned_host_pids"]==[host["host_pid"]]and
      type(host["host_pid"])is int and host["host_pid"]>1 and
      type(raw["owned_cids"])is list and len(raw["owned_cids"])==len(set(raw["owned_cids"]))and
      set(raw["owned_cids"])<=set(known)and raw["current_cid"]in raw["owned_cids"]and
      known[raw["current_cid"]]==raw["current_phase"],"original protected boundary exact already-owned identities")
    C.need(raw["boundary"]==C.protected_module().protected_boundary(raw["original"],raw["actual"],
      raw["owned_cids"],raw["owned_host_pids"]),"protected external churn not frozen baseline equality")
def observations(host,source):
    PC=C.module("process_cmdline",C.HOST_BINDINGS["process_cmdline.py"]);proofs=[]
    npu=host["owned"][1]
    for row in host["actual_npu_observations"]:
        value=C.obj(row);smi=C.obj(value["smi"])
        C.need(smi["argv"]==[H.SMI,"info"]and smi["exit_code"]==0,"actual original SMI argv/exit")
        protected(C.obj(value["protected_boundary_ref"]),host,value["smi"])
        C.need(value["actual_hbm"]==[H.control_hbm(smi["stdout"],4)],"single4 physical3GiB reserve replay")
        for proof in value["proofs"]:
            C.need(proof["physical"]==4 and proof["chip"]==0 and npu["cid"]in proof["cgroup"]and
              proof["namespace_pids"][0]==proof["pid"],"only actual own physical4 mapping")
            PC.consume(C.obj(proof["actual_cmdline_raw_ref"]),proof,source);proofs.append(proof)
    C.need(proofs,"real single4 process proofs required")
    return proofs
def identity_proved(who,proofs,cid,argv):
    C.need(set(who)=={"pid","start_ticks","cgroup","argv","cmdline_sha256"}and who["argv"]==argv and cid in who["cgroup"],
      "actual exact guest process identity/argv/owned cgroup")
    found=[p for p in proofs if p["namespace_pids"][-1]==who["pid"]and p["start_ticks"]==who["start_ticks"]and
      p["cgroup"]==who["cgroup"]and p["argv"]==who["argv"]and p["cmdline_sha256"]==who["cmdline_sha256"]]
    C.need(found,"actual host SMI/proc bytes prove guest PID/start/argv, not declaration")
def independent(value,producer,source,producer_ref,plan,proof_ref):
    C.need(value["schema"]=="skvq.actual-writer.independent/v1"and value["status"]=="ACTUAL_ALL64_Q2Q4_WRITER_BYTES_CONSUMED"and
      value["source_ref"]==source and value["producer_ref"]==producer_ref and value["input_plan_ref"]==plan and
      value["device_proof_ref"]==proof_ref and value["actual_cases"]==128 and value["actual_axis_writer_calls"]==256 and
      all(value[k]is False for k in C.scopes())and value["all_original_payload_SS_ZP_bytes_exact"]is True and
      value["sink5_recent128_full_guards_exact"]is True and value["original_full_input_bytes_unchanged"]is True and
      value["whole_owned_original_cleanup_semantic_consumption_pending"]is True,"actual same-image full independent mathematical result")
    want=[(r,l,b,a)for r in range(4)for l in C.LAYERS for b in(2,4)for a in("K","V")]
    got=[(x["rank"],x["logical_layer"],x["bits"],x["axis"])for x in value["checked"]]
    C.need(got==want,"all256 unique actual independent axes")
    originals={(c["rank"],c["logical_layer"],c["bits"],a):r for c in producer["cases"]for a,r in c["axes"].items()}
    for result,key in zip(value["checked"],want):
        row=originals[key];C.need(result["raw_observation_ref"]==row,"same real raw-axis independent result")
        observed=C.obj(row)
        for timing in("before","after"):
            for raw in observed[timing].values():C.checked(raw,2**22)
        C.checked(observed["input_after_ref"],2**22)
        C.need(result["exact_payload_scales_zero_points"]is True and result["full_sink_recent_guard_unchanged"]is True and
          result["full_input_unchanged"]is True and result["independent_candidate_math_not_called"]is True,
          "actual complete all-plane adjudication")
    return value
def consume(root,original_ref,expected):
    source=C.source(expected);root=Path(root)
    C.need(root.parent==C.ROOT.parent and re.fullmatch("run-skvq-actual-writer-bridge-002-[a-zA-Z0-9-]+",root.name),"exact current writer whole root")
    href=C.ref(root/"HOST_RESULT.json");host=C.obj(href)
    C.need(host["schema"]=="skvq.actual-writer.owned-host/v1"and host["status"]=="ACTUAL_WRITER_RAW_CONSUMED_PENDING_WHOLE"and
      host["source_ref"]==source and host["primary"]is None and host["secondary"]==[]and len(host["owned"])==3 and
      len({e["cid"]for e in host["owned"]})==3 and host["total_seconds"]==3600 and
      host["device_block_seconds"]==host["independent_cpu_block_seconds"]==1800 and host["cleanup_included_seconds"]==180 and
      0<host["elapsed_seconds"]<=3600 and 0<=host["actual_cleanup_seconds"]<=180 and
      host["portfolio_cutoff_epoch"]==C.CUT and host["CPU_QUEUE_no_peer_admission"]is True and
      all(host[k]is False for k in C.scopes()),"successful exact current whole source/budget/coverage, no failed upgrade")
    whole_file=Path(host["calibration_whole_ref_file"]["path"]);C.checked(host["calibration_whole_ref_file"])
    C.need(json.loads(whole_file.read_bytes())==host["calibration_whole_ref"],"actual unchanged input descriptor")
    original(C.obj(original_ref),host_argv(root,source,whole_file))
    from writer_inputs import verify_whole
    verify_whole(host["calibration_whole_ref"])
    mounts=H.mount_set(root,whole_file,host["calibration_whole_ref"]);Controller=H.control_class(source,mounts,H.preflight_module())
    C.need(host["original_Control_source"]==Controller.donor_source and host["original_Control_AST"]==Controller.original_ast_sha256 and
      host["adapted_Control_AST"]==Controller.adapted_ast_sha256 and host["literal_delta"]==Controller.literal_delta,"exact source-qualified original safety body and narrow single4 literals")
    releases=[]
    for i,e in enumerate(host["owned"]):
        releases.append(inspect_cleanup(e,source,Controller,mounts,i));resource_evidence(e)
    C.need([x["phase"]for x in host["capspent"]]==["input-plan","single4-writer","independent"]and
      [x["cid"]for x in host["capspent"]]==[e["cid"]for e in host["owned"]]and
      all(x["cpu"]==1 and x["memory"]==8*H.GIB for x in host["capspent"]),"actual three CPU1/8GiB stages, not donor CPU4")
    result=host["result"];stages=result["actual_cli_refs"];C.need(set(stages)=={"input-plan","canary","numeric","independent"},"actual complete four-stage CLI set")
    plan=result["input_plan_ref"];prior=result["numpy_ref"];canary=result["canary_ref"];producer_ref=result["numeric_ref"]
    for name,index in(("input-plan",0),("canary",1),("numeric",1),("independent",2)):
        raw=child_cli(stages[name],host["owned"][index]["cid"],H.args(name,source,root,whole_file),npu=index==1)
        sink=(C.ref(root/"input-plan/work/CPU_RESULT.json")if name=="input-plan"else
          (canary if name=="canary"else(producer_ref if name=="numeric"else result["independent_ref"])))
        C.need(json.loads(Path(raw["stdout"]["path"]).read_bytes())==sink,"actual sole stdout Ref matches actual stage result")
    cpu=C.obj(C.ref(root/"input-plan/work/CPU_RESULT.json"))
    C.need(cpu["status"]=="ACTUAL_INPUT_PLAN_NUMPY24_COMPLETE"and cpu["source_ref"]==source and cpu["input_plan_ref"]==plan and cpu["numpy_ref"]==prior,"actual CPU plan/24 exact scalar-vector configurations")
    canary_value=H.consume_canary(C.obj(canary),source,plan,prior)
    proofs=observations(host,source)
    identity_proved(canary_value["identity"],proofs,host["owned"][1]["cid"],[H.PY,"-B",*H.args("canary",source,root,whole_file)])
    producer=C.obj(producer_ref)
    C.need(producer["status"]=="ACTUAL_ALL64_Q2Q4_WRITER_RETURNED_RAW_PENDING_INDEPENDENT"and producer["primary"]is None and
      producer["source_ref"]==source and producer["input_plan_ref"]==plan and producer["device_proof_ref"]==result["device_proof_ref"]and
      producer["owned_cid"]==host["owned"][1]["cid"]and producer["physical_card"]==4 and producer["logical_device"]==0 and
      producer["identity"]==producer["identity_at_terminal"]and producer["npu_executed"]is True and
      producer["actual_case_count"]==128 and producer["actual_axis_writer_calls"]==256 and all(producer[k]is False for k in C.scopes()),"complete actual original writer producer")
    identity_proved(producer["identity"],proofs,producer["owned_cid"],[H.PY,"-B",*H.args("numeric",source,root,whole_file)])
    proof=C.device_proof(C.obj(result["device_proof_ref"]),source,plan)
    C.need(proof["cid"]==producer["owned_cid"]and proof["fresh_canary_ref"]==canary and proof["prior_numpy_ref"]==prior and
      C.obj(proof["owned_ref"])["cid"]==proof["cid"]and proof["resource_ref"]==host["owned"][1]["resource_ref"],"same real owned proof/prior/resource")
    mapping=C.obj(proof["mapping_ref"]);clock=C.obj(proof["clock_ref"]);gate=C.obj(proof["source_gate_ref"])
    C.need(mapping["cid"]==proof["cid"]and mapping["canary_ref"]==canary and mapping["devices"]==host["owned"][1]["devices"]and
      all(p in proofs for p in mapping["actual_mapping_proofs"])and mapping["actual_mapping_proofs"]and
      clock["portfolio_cutoff_epoch"]==C.CUT and clock["protocol_ref"]==C.CLOCK and clock["observed_epoch"]+1800<=C.CUT and
      gate["source_ref"]==source and gate["capture_source"]==C.CAPTURE and gate["calibration_source"]==C.CALIBRATION and
      gate["calibration_whole_ref"]==host["calibration_whole_ref"]and gate["entire_closure_bytes_checked"]is True,"real map/source/fixed clock semantics")
    consumed=independent(C.obj(result["independent_ref"]),producer,source,producer_ref,plan,result["device_proof_ref"])
    reader=C.module("_skvq_writer_actual_budget",C.BUDGET);reader.consume(host["output_budget_snapshot"],root);C.snapshot(root)
    C.need(C.ref(root/"HOST_RESULT.json")==href and C.source(expected)==source,"unchanged terminal/source after whole consumption")
    return dict(schema="skvq.actual-writer.whole/v1",status="OWNED_SINGLE4_ALL64_Q2Q4_WRITER_BYTES_CONSUMED",
      source_ref=source,original_ref=original_ref,host_result_ref=href,calibration_whole_ref=host["calibration_whole_ref"],
      producer_ref=producer_ref,independent_ref=result["independent_ref"],input_plan_ref=plan,device_proof_ref=result["device_proof_ref"],
      actual_cases=128,actual_axis_writer_calls=256,only_physical_card=4,whole_owned_cleanup_semantics_checked=True,
      actual_writer_byte_math_consumed_in_same_image_Devices_empty=True,packed_reader_attention_model_pending=True,**C.scopes())
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--root");p.add_argument("--original-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.root and a.original_ref_json and a.output and Path(a.output)==Path(a.root)/"WRITER_WHOLE.json","actual whole original/exclusive whole sink")
    print(json.dumps(C.publish(a.output,consume(a.root,json.loads(Path(a.original_ref_json).read_bytes()),a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()

