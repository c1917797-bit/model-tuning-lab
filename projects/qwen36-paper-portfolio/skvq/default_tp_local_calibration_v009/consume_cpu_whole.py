"""Independent actual whole-terminal/CPU-owned/calibration consumer. No launch/native.
Replays original calibration oracle in READ-ONLY mode; no producer/KMeans math.
"""
import argparse,ast,copy,hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
import cpu_host as H
def host_argv(root,sha,whole_file,mode):
    return ["/usr/bin/env","MAIN_SKVQ_CALIBRATION_CPU_ENABLE=1","/usr/bin/prlimit",
      "--cpu=600:600","--","/usr/bin/python3","-B",str(C.ROOT/"cpu_host.py"),
      "--execute","--source-manifest-sha256",sha,"--whole-ref-json",str(whole_file),
      "--feature-mode",mode,"--output",str(root)]
def original(value,argv):
    C.need(value["schema"]=="agentweb.operation/v1","actual full operation schema")
    op=value["operation"];record=op["result"]["record"]
    C.need(value["terminal"]is True and value["status"]=="completed"and value["succeeded"]is True and
      value["error"]is None and op["ok"]is True and op["result"]["state"]=="completed"and
      op["routeDecision"]=="peer_direct"and op["targetPeerId"]=="lgw_a6109c51076a4a2c9d2674ca5a8704a0",
      "actual successful whole direct terminal, not unknown/running/failed fixture")
    C.need([record["command"]]+record["args"]==argv and record["exitCode"]==0 and
      record.get("error")is None and record.get("timedOut")is False and record.get("cancelled")is False,
      "exact current CPU whole argv/non-timeout/non-cancelled/exit0")
    return record
def inspect_cleanup(e,source,Controller,mounts):
    C.need(type(e["npu"])is bool and e["npu"]is False and e["phase"]=="calibration"and
      e["mem"]==8*H.GIB and e["devices"]=={}and e["env"]==H.environment()and
      e["source"]==source["sha256"]and re.fullmatch("[0-9a-f]{64}",e["cid"])and e["released"]is True,
      "one actual CPU8 owned/source/environment, no accelerator lease")
    expected={p:(s,rw)for p,(s,rw)in e["mounts"].items()}
    C.need(expected==mounts,"actual complete source/evidence RO plus sole owned RW")
    release=C.bound(e["release_ref"])
    C.need(release["cid"]==e["cid"]and release["retained"]is True and release["deleted"]is False and
      release["released"]is True and release["noOOM"]is True and not release.get("secondary")and
      "release_smi"not in release,"exact CPU-only stop retained, no NPU idle release claim")
    stop=C.bound(release["stop"]);argv=[H.DOCKER,"stop","--time","15",e["cid"]]
    C.need(stop["argv"]==argv and stop["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      stop["exit_code"]==0,"exact own stop original command/exit")
    observed=C.bound(release["inspect"])
    C.need(observed["argv"]==[H.DOCKER,"inspect",e["cid"]]and observed["exit_code"]==0 and
      observed["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*observed["argv"]],
      "actual sole exact inspect terminal")
    rows=json.loads(observed["stdout"]);C.need(len(rows)==1,"one actual final inspected container")
    normalized=copy.deepcopy(e);normalized["mounts"]=expected
    Controller.validate(None,rows[0],normalized)
    state=rows[0]["State"]
    C.need(state["Running"]is False and state["Pid"]==0 and not state["OOMKilled"]and not rows[0].get("ExecIDs"),
      "actual own stopped/Pid0/noExec/noOOM")
    return release
def resource_evidence(e,R):
    rs=C.bound(e["resource_ref"]);a=rs["allocation"]
    C.need(R.allocate(rs["host_cpu"],rs["daemon_cpu"])==a,"independent actual summed7 CPU replay")
    total=R.memory_admit(rs["host_memory"],rs["daemon_memory"],8*H.GIB)
    C.need(total==rs["ordinary_floor_bytes"]==int(16.5*H.GIB)and
      rs["memory"]["MemAvailable"]>=total and rs["memory"]["SwapTotal"]==rs["memory"]["SwapFree"]and
      rs["disk_available_bytes"]>=8*H.GIB,"actual CPU8+host.5+reserve8 ordinary RAM/disk; no HugeTLB")
    return rs
def workload(value,source,whole_ref,root,whole_file,mode):
    import cpu_entry as E
    C.need(value["schema"]=="skvq.default-tp-local.cpu-workload/v1"and
      value["status"]=="CALIBRATION_CPU_WORKLOAD_CONSUMED_HOST_AUTHORITY_PENDING"and
      value["source_ref"]==source and value["capture_whole_ref"]==whole_ref and value["primary"]is None and
      value["total_seconds"]==600 and value["cleanup_reserved_seconds"]==90 and
      value["host_owned_terminal_consumer_required"]is True and
      all(value[k]is False for k in("native_ready","model_ready","performance_ready","task_ready")),
      "actual all-stage CPU-only workload, no borrowed success")
    planned=E.plans(source,whole_file,root/"work",mode);actual=value["completed"]
    C.need(len(actual)==len(planned)==3,"complete library/producer/independent children")
    for row,(label,argv,result)in zip(actual,planned):
        argv[0]=H.PY
        C.need(row["stage"]==label and row["result_ref"]==C.reference(result),"actual unique expected stage file")
        raw=C.bound(row["original_cli_ref"])
        C.need(raw["argv"]==argv and raw["exit_code"]==0 and raw["timed_out"]is False and
          raw["actual_child_completed"]is True and raw["source_ref"]==source,"exact real fresh child CLI/source/exit")
        C.need(json.loads(Path(raw["stdout"]["path"]).read_bytes())==row["result_ref"],
          "actual sole stdout file Ref equals expected result")
        C.need(C.reference(raw["stdout"]["path"])==raw["stdout"]and
          C.reference(raw["stderr"]["path"])==raw["stderr"],"original child complete stdout/stderr bytes")
    from consume import consume
    consumed=C.bound(actual[-1]["result_ref"])
    independent=consume(root/"work"/"producer",whole_ref,source,write_artifacts=False,module_namespace="captured")
    C.need(independent==consumed and independent["actual_rank_fits"]==128 and
      len(independent["calibration_refs"])==len(independent["writer_handoffs"])==64,
      "read-only independent full128/all64 math/PT/writer replay")
    return actual[-1]["result_ref"],independent
def consume(root,original_ref,expected):
    source=C.source(expected);root=Path(root);H.C.need(root.parent==C.ROOT.parent and
      re.fullmatch("run-skvq-default-tp-local-009-[a-zA-Z0-9-]+",root.name),"exact current CPU experiment root")
    href=C.reference(root/"HOST_RESULT.json");host=C.bound(href)
    C.need(host["schema"]=="skvq.default-tp-local.owned-host/v1"and
      host["status"]=="CPU_CALIBRATION_WORKLOAD_COMPLETE_PENDING_WHOLE"and host["source_ref"]==source and
      host["primary"]is None and host["secondary"]==[]and len(host["owned"])==1 and
      host["total_seconds"]==600 and host["cleanup_included_seconds"]==90 and
      0<host["elapsed_seconds"]<=600 and 0<=host["actual_cleanup_seconds"]<=90 and
      host["portfolio_cutoff_epoch"]==C.CUT and host["Devices_empty"]is True and
      host["no_NPU_observation"]is True and host["CPU_QUEUE_no_peer_admission"]is True and
      all(host[k]is False for k in("native_ready","model_ready","performance_ready","task_ready")),
      "actual original current-source complete CPU-only host, no failed fixture upgrade")
    wf=host["capture_whole_ref_file"];C.need(C.reference(wf["path"])==wf,"original input Ref descriptor identity")
    whole_file=Path(wf["path"]);whole_ref=json.loads(whole_file.read_bytes())
    C.need(whole_ref==host["capture_whole_ref"],"same original whole-input descriptor")
    original(C.bound(original_ref),host_argv(root,source["sha256"],whole_file,host["feature_mode"]))
    from calibration_inputs import inputs
    inputs(whole_ref) # actual new derived whole again, never old05a7 success
    row=C.CAPTURE_BINDINGS["resources.py"];R=C.donor("_skvq_cal009_cpu_resources",row["path"],row["sha256"])
    mounts=H.mount_set(root,whole_file,whole_ref);pre=H.mount_adapter()
    Controller=H.control_class(source,R,mounts,pre);e=host["owned"][0]
    C.need(host["donor_control_source_ref"]==Controller.donor_source_ref and
      host["exact_original_control_class_ast_sha256"]==Controller.donor_class_ast_sha256,
      "exact original class reuse, no old capture identity")
    inspect_cleanup(e,source,Controller,mounts);resource_evidence(e,R)
    before=C.bound(e["mount_preflight_ref"]);after=pre.observe(mounts,"calibration",source)
    C.need(before["passed"]is True and after["passed"]is True and before["source_ref"]==source and
      before["phase"]=="calibration"and len(before["mounts"])==len(after["mounts"]),"actual exact full mount preflight")
    for a,b in zip(before["mounts"],after["mounts"]):
        C.need({k:v for k,v in a.items()if k!="identity"}=={k:v for k,v in b.items()if k!="identity"},
          "original/current mount destinations and types")
        keys=("dev","ino","mode")if a["kind"]=="directory"else tuple(a["identity"])
        C.need(all(a["identity"][k]==b["identity"][k]for k in keys),"actual original mount object identity")
    raw=C.bound(host["result"]["actual_child_cli_ref"])
    argv=[H.DOCKER,"exec",e["cid"],"/bin/bash","-c",
      'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"skvq-owned",H.PY,"-B",
      *H.guest_args(source,whole_file,root,host["feature_mode"])]
    C.need(raw["argv"]==argv and raw["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      raw["exit_code"]==0 and raw["terminated"]is True and raw["primary"]is None,
      "actual CPU aggregate original Docker child exact -B argv/exit")
    for r in(raw["stdout"],raw["stderr"]):C.need(C.reference(r["path"])==r,"quiescent actual aggregate original logs")
    C.need(json.loads(Path(raw["stdout"]["path"]).read_bytes())==host["result"]["workload_ref"],
      "CPU stdout equals actual sole workload Ref")
    workload_ref=host["result"]["workload_ref"];value=C.bound(workload_ref)
    independent_ref,independent=workload(value,source,whole_ref,root,whole_file,host["feature_mode"])
    H.output_bytes(root);C.need(C.reference(root/"HOST_RESULT.json")==href,"immutable original terminal")
    return dict(schema="skvq.default-tp-local.whole/v1",status="OWNED_CPU_ALL128_CALIBRATION64_CONSUMED",
      source_ref=source,original_ref=original_ref,host_result_ref=href,capture_whole_ref=whole_ref,
      workload_ref=workload_ref,independent_ref=independent_ref,
      actual_rank_fits=128,calibration_refs=independent["calibration_refs"],
      writer_handoffs=independent["writer_handoffs"],Devices_empty=True,CPU_QUEUE_no_peer_admission=True,
      author_global_grouping_equivalent=False,unified_clip=.95,smooth_enabled=False,runtime_pre_rope=False,
      clock=C.CLOCK,portfolio_cutoff_epoch=C.CUT,quantized_native_consumer_pending=True,
      native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--root");ap.add_argument("--original-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,native_ready=False,model_ready=False)));return
    C.need(a.root and a.original_ref_json and a.output,"real original terminal/new CPU output")
    ref=json.loads(Path(a.original_ref_json).read_bytes())
    C.need(Path(a.output)==Path(a.root)/"CALIBRATION_WHOLE.json","sole exclusive whole sink")
    print(json.dumps(C.publish(a.output,consume(a.root,ref,a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()
