"""Independent actual new CPU whole; old05a7 remains FAILED forever.
No Docker/native execution; explicit actual parent/child/source/owned replay.
"""
import argparse,ast,copy,hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import offline_contract as D
import cpu_host as H
def host_argv(root,sha):
    return ["/usr/bin/env","MAIN_SKVQ_OFFLINE_CPU_ENABLE=1","/usr/bin/prlimit","--cpu=3600:3600",
      "--","/usr/bin/python3","-B",str(D.ROOT/"cpu_host.py"),"--execute",
      "--source-manifest-sha256",sha,"--output",str(root)]
def original(value,argv):
    op=value["operation"];r=op["result"]["record"]
    D.need(value["schema"]=="agentweb.operation/v1"and value["terminal"]is True and
      value["status"]=="completed"and value["succeeded"]is True and value["error"]is None and
      op["ok"]is True and op["result"]["state"]=="completed"and op["routeDecision"]=="peer_direct"and
      op["targetPeerId"]=="lgw_a6109c51076a4a2c9d2674ca5a8704a0",
      "actual NEW successful CPU whole, not upgraded05a7/unknown/fixture")
    D.need([r["command"],*r["args"]]==argv and type(r["exitCode"])is int and r["exitCode"]==0 and
      r.get("error")is None and r["timedOut"]is False and r["cancelled"]is False and
      0<r["durationMs"]<=3600000,"actual one new CPU argv/exit0/bounded non-timeout")
    return r
def inspect_cleanup(e,source,Controller,mounts):
    D.need(type(e["npu"])is bool and e["npu"]is False and e["phase"]=="offline-consumer"and
      e["mem"]==2*H.GIB and e["devices"]=={}and e["env"]==H.environment()and
      e["source"]==source["sha256"]and re.fullmatch("[0-9a-f]{64}",e["cid"])and e["released"]is True,
      "one actual CPU2 owned/source/environment, no accelerator lease")
    expected={p:(s,rw)for p,(s,rw)in e["mounts"].items()}
    D.need(expected==mounts,"actual complete source/evidence RO plus sole owned RW")
    release=D.obj(e["release_ref"])
    D.need(release["cid"]==e["cid"]and release["retained"]is True and release["deleted"]is False and
      release["released"]is True and release["noOOM"]is True and not release.get("secondary")and
      "release_smi"not in release,"exact CPU-only stop retained, no NPU idle release claim")
    stop=D.obj(release["stop"]);argv=[H.DOCKER,"stop","--time","15",e["cid"]]
    D.need(stop["argv"]==argv and stop["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      stop["exit_code"]==0,"exact own stop original command/exit")
    observed=D.obj(release["inspect"])
    D.need(observed["argv"]==[H.DOCKER,"inspect",e["cid"]]and observed["exit_code"]==0 and
      observed["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*observed["argv"]],
      "actual sole exact inspect terminal")
    rows=json.loads(observed["stdout"]);D.need(len(rows)==1,"one actual final inspected container")
    normalized=copy.deepcopy(e);normalized["mounts"]=expected
    Controller.validate(None,rows[0],normalized)
    state=rows[0]["State"]
    D.need(state["Running"]is False and state["Pid"]==0 and not state["OOMKilled"]and not rows[0].get("ExecIDs"),
      "actual own stopped/Pid0/noExec/noOOM")
    return release
def resource_evidence(e,R):
    rs=D.obj(e["resource_ref"]);a=rs["allocation"]
    D.need(R.allocate(rs["host_cpu"],rs["daemon_cpu"])==a,"independent actual summed7 CPU replay")
    total=R.memory_admit(rs["host_memory"],rs["daemon_memory"],2*H.GIB)
    D.need(total==rs["ordinary_floor_bytes"]==int(10.5*H.GIB)and
      rs["memory"]["MemAvailable"]>=total and rs["memory"]["SwapTotal"]==rs["memory"]["SwapFree"]and
      rs["disk_available_bytes"]>=8*H.GIB,"actual CPU2+host.5+reserve8 ordinary RAM/disk; no HugeTLB")
    return rs

def workload(value,source,root):
    D.need(value["schema"]=="skvq.capture014.offline.workload/v1"and
      value["status"]=="ALL256_ORIGINAL_RAW_WITH_ORDERED_IDENTITY_CONSUMED_PENDING_CPU_WHOLE"and
      value["source_ref"]==source and value["producer_source_ref"]==D.CAPTURE and
      value["original_failed_whole_ref"]==D.FAILED_ORIGINAL and value["original_failed_whole_preserved"]is True and
      value["events"]==16384 and value["qkv_bytes"]==256*H.GIB and value["preprojection_K_raw_bytes"]==32*H.GIB and
      value["total_seconds"]==3600 and value["cleanup_reserved_seconds"]==180 and
      0<value["elapsed_seconds"]<=3420 and value["host_owned_terminal_consumer_required"]is True and
      all(value[k]is False for k in("native_ready","model_ready","performance_ready","task_ready"))and
      value["no_NPU"]is True and value["no_Torch"]is True,"complete actual new CPU all256 raw, not small identity fixture")
    C,loader,projection,stage=D.original_modules(source)
    import previous_failure as F
    F.inspect()
    for key,name in (("original_failure_authority_ref","ORIGINAL_FAILURE_CONSUMED.json"),
      ("original_owned_preflight_ref","ORIGINAL_OWNED_PREFLIGHT.json"),
      ("ordered_identity_preflight_ref","ORDERED_IDENTITY_PREFLIGHT.json"),
      ("full_raw_consumer_ref","CAPTURE_CONSUMED.json"),
      ("derived_old_host_consumer_ref","ORIGINAL_HOST_CONSUMED_DERIVED.json"),
      ("after_release_payload_ref","PAYLOAD_AFTER_RELEASE.json")):
        D.need(value[key]==D.ref(root/"work"/name),"new own raw result path/entire byte Ref")
    from identity_preflight import inspect_pairs
    D.need(D.obj(value["ordered_identity_preflight_ref"])==inspect_pairs(source),
      "independent real all4 ordered identity replay, not declarations")
    combined=D.obj(value["full_raw_consumer_ref"])
    D.need(combined["current_source_ref"]==D.CAPTURE and
      combined["derived_identity_consumer_source_ref"]==source and
      combined["original_failed_whole_ref"]==D.FAILED_ORIGINAL and
      combined["original_failed_whole_preserved"]is True and
      combined["derived_ordered_identity_ref"]==value["ordered_identity_preflight_ref"]and
      combined["after_release_full_payload_ref"]==value["after_release_payload_ref"],
      "original producer and explicit NEW math consumer identities separated")
    stage.combine(D.obj(combined["baseline_receipt_ref"]),D.obj(combined["preprojection_consumed_ref"]),
      D.CAPTURE,combined["baseline_receipt_ref"],combined["preprojection_consumed_ref"])
    import consume_previous_host as previous
    hostproof=previous.consume(Path(D.RAW_ROOT),value["full_raw_consumer_ref"])
    recorded=D.obj(value["derived_old_host_consumer_ref"])
    D.need({k:v for k,v in recorded.items()if k!="current_clock"}==
      {k:v for k,v in hostproof.items()if k!="current_clock"},
      "independent complete original cleanup/resources/N1/SMI/real-cmdline replay")
    payload=D.obj(value["after_release_payload_ref"]);old_host=D.obj(F.HOST_REF)
    D.need(payload["payload"]==old_host["actual_payload"]and payload["original_host_before_ref"]==F.HOST_REF and
      payload["every_indexed_shard_whole_bytes_rehashed"]is True and
      payload["old_before_after_success_not_claimed"]is True,
      "actual NEW full-shard after-release rehash vs old before; no fake old completed-after")
    D.checked(payload["payload"]["index"])
    return combined
def consume(root,original_ref,expected):
    source=D.source(expected);root=Path(root)
    D.need(root.parent==D.ROOT.parent and re.fullmatch("run-skvq-capture014-offline-001-[a-zA-Z0-9-]+",root.name),
      "one new CPU runroot, not an old experiment/source tree")
    href=D.ref(root/"HOST_RESULT.json");host=D.obj(href)
    D.need(host["schema"]=="skvq.capture014.offline.owned-host/v1"and
      host["status"]=="RELEASED014_CPU_RAW_REPLAY_COMPLETE_PENDING_WHOLE"and host["source_ref"]==source and
      host["producer_source_ref"]==D.CAPTURE and host["original_failed_whole_ref"]==D.FAILED_ORIGINAL and
      host["primary"]is None and host["secondary"]==[]and len(host["owned"])==1 and
      host["total_seconds"]==H.TOTAL==3600 and host["cleanup_included_seconds"]==H.CLEANUP==180 and
      0<host["elapsed_seconds"]<=3600 and 0<=host["actual_cleanup_seconds"]<=180 and
      host["portfolio_cutoff_epoch"]==D.CUT and host["Devices_empty"]is True and
      host["no_NPU_observation"]is True and host["CPU_QUEUE_no_peer_admission"]is True and
      all(host[k]is False for k in("native_ready","model_ready","performance_ready","task_ready")),
      "actual new complete CPU-owned host; original FAILED not promoted")
    record=original(D.obj(original_ref),host_argv(root,source["sha256"]))
    D.need(json.loads(record["stdout"])==href,"new original external stdout binds exact new HOST_RESULT")
    D.original_modules(source)
    R=D.load("_skvq014_offline_cpu_resources",H.binding("resources.py"))
    mounts=H.mount_set(root,source);pre=H.mount_adapter()
    Controller=H.control_class(source,R,mounts,pre);e=host["owned"][0]
    D.need(host["donor_control_source_ref"]==Controller.donor_source_ref and
      host["exact_original_control_class_ast_sha256"]==Controller.donor_class_ast_sha256,
      "original immutable Control AST safety inherited, not old algorithm PASS")
    inspect_cleanup(e,source,Controller,mounts);resource_evidence(e,R)
    before=D.obj(e["mount_preflight_ref"]);after=pre.observe(mounts,"offline-consumer",source)
    D.need(before["passed"]is True and after["passed"]is True and before["source_ref"]==source and
      before["phase"]=="offline-consumer"and len(before["mounts"])==len(after["mounts"]),"exact current CPU full mount preflight")
    for a,b in zip(before["mounts"],after["mounts"]):
        D.need({k:v for k,v in a.items()if k!="identity"}=={k:v for k,v in b.items()if k!="identity"},
          "original/current exact CPU mount paths/types")
        keys=("dev","ino","mode")if a["kind"]=="directory"else tuple(a["identity"])
        D.need(all(a["identity"][k]==b["identity"][k]for k in keys),"actual CPU mount object identity")
    raw=D.obj(host["result"]["actual_child_cli_ref"])
    argv=[H.DOCKER,"exec",e["cid"],"/bin/bash","-c",
      'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"skvq-owned",H.PY,"-B",*H.guest_args(source,root)]
    D.need(raw["argv"]==argv and raw["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      raw["exit_code"]==0 and raw["terminated"]is True and raw["primary"]is None,"actual new CPU child exact argv/exit")
    for r in(raw["stdout"],raw["stderr"]):D.need(D.ref(r["path"])==r,"whole original new child logs; explicit empty stderr allowed")
    wr=host["result"]["workload_ref"]
    D.need(wr==D.ref(root/"work/CPU_WORKLOAD_RESULT.json")and
      json.loads(Path(raw["stdout"]["path"]).read_bytes())==wr,"actual complete workload Ref emitted by exact child")
    combined=workload(D.obj(wr),source,root);H.output_bytes(root)
    D.need(D.ref(root/"HOST_RESULT.json")==href,"immutable new original host result")
    import previous_failure as F
    return dict(schema="skvq.capture014.offline.whole/v1",
      status="RELEASED014_ALL256_RAW_DERIVED_CPU_WHOLE_CONSUMED_NOT_CALIBRATED",
      source_ref=source,producer_source_ref=D.CAPTURE,original_ref=original_ref,host_result_ref=href,
      original_failed_whole_ref=D.FAILED_ORIGINAL,original_capture_host_result_ref=F.HOST_REF,
      original_capture_child_ref=F.CAPTURE_CLI_REF,original_failed_consumer_child_ref=F.FAILED_CLI_REF,
      original_failed_whole_preserved=True,original_failed_whole_succeeded=False,
      workload_ref=wr,full_raw_consumer_ref=D.obj(wr)["full_raw_consumer_ref"],
      after_release_payload_ref=D.obj(wr)["after_release_payload_ref"],events=16384,qkv_bytes=256*H.GIB,
      preprojection_K_raw_bytes=32*H.GIB,whole_operation_consumed=True,Devices_empty=True,
      CPU_QUEUE_no_peer_admission=True,clock=D.obj(D.CAPTURE)["clock"],portfolio_cutoff_epoch=D.CUT,
      author_calibration_pending=True,author_global_grouping_equivalent=False,
      native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest-sha256");p.add_argument("--root");p.add_argument("--original-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,no_NPU=True,model_ready=False)));return
    D.need(a.root and a.original_ref_json and Path(a.output)==Path(a.root)/"DERIVED_WHOLE.json","exact new whole sink")
    rr=json.loads(Path(a.original_ref_json).read_bytes())
    print(json.dumps(D.publish(a.output,consume(a.root,rr,a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()
