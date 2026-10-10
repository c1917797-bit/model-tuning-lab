"""Independent stdlib terminal/owned-resource consumer; no Docker/Torch execution.
This consumes actual immutable host outputs only, not fresh admission or E2E.
MAIN must separately preserve and consume its original AW operation.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
sys.path.insert(0,str(BASE))
from io_contract import require,reference,publish_json
import current_contract as C
from physical_hbm import actual_hbm
import mount_preflight as M
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
def read(ref):
    C.checked(ref);return json.loads(Path(ref["path"]).read_bytes())
def consume_protected(value,baseline,owned,host_pid,smi_ref,active):
    require(type(host_pid)is int and host_pid>1,"actual original controller host PID")
    known={e["cid"]:e["phase"] for e in owned}
    require(type(value)is dict and set(value)=={"smi","actual","original","boundary","owned_cids",
      "owned_host_pids","current_cid","current_phase"} and value["smi"]==smi_ref and
      value["original"]==baseline,"complete source-bound protected raw/SMI/baseline")
    cids=value["owned_cids"]
    require(type(cids)is list and len(cids)==len(set(cids)) and set(cids)<=set(known) and
      value["owned_host_pids"]==[host_pid] and
      value["current_cid"] in cids and known[value["current_cid"]]==value["current_phase"],
      "actual already-owned cohort and original host identity; no borrowed protected scope")
    if active:
        require(value["current_phase"]=="tp4-capture" and
          all(e["cid"] in cids for e in owned if e["phase"]=="tp4-capture"),
          "active capture cannot omit its own CID from protected gate")
    expected=C.protected_module().protected_boundary(baseline,value["actual"],cids,[host_pid])
    require(value["boundary"]==expected,"independent exact protected-boundary replay; external churn not immutability")
    return expected
def consume(root):
    root=Path(root);before=reference(root/"HOST_RESULT.json");v=json.loads((root/"HOST_RESULT.json").read_text())
    require(v["schema"]=="SKVQ_HOST_CAPTURE_RESULT_V1" and v["max_total_seconds"]==7200 and
      v["cleanup_included_seconds"]==180 and 0<=v["actual_cleanup_spent_seconds"]<=180 and
      0<v["elapsed_seconds"]<=7200,"original whole phase including cleanup")
    source=C.source();require(v["source_lock"]==source,"exact current host producer source")
    lock=read(source);require(lock["schema"]=="skvq.current72h.preprojection.sources/v1","actual current sources")
    require(v["current_clock"]["protocol_ref"]==C.CLOCK and v["current_clock"]["portfolio_cutoff_epoch"]==C.CUT and
      v["portfolio_deadline_utc"]=="2026-10-12T07:00:25Z","actual original unchanged portfolio clock")
    for r in lock["files"]+lock["dependencies"]:C.checked(r)
    if v["status"]=="FAILED":
        return dict(schema="SKVQ_HOST_FAILED_RETAINED_V1",status="ORIGINAL_FAILURE_RETAINED_NOT_PROMOTED",
          host_result=before,primary=v["primary"],secondary=v["secondary"],native_ready=False)
    require(v["status"]=="FULL_NATIVE_BASELINE_CAPTURE_CONSUMED_NOT_CALIBRATED" and
      v["primary"] is None and v["secondary"]==[],"actual host completed without primary/secondary")
    require(v["native_ready"] is False and v["model_ready"] is False and v["e2e32768_pending"] is True,"no native calibration/service/E2E promotion")
    require(len(v["owned"])==3 and len({x["cid"] for x in v["owned"]})==3 and
      [x["phase"] for x in v["owned"]]==["preflight","tp4-capture","independent-consumer"],"three distinct sequential own fresh guests")
    end=0.;records=[]
    for i,e in enumerate(v["owned"]):
        require(re.fullmatch("[0-9a-f]{64}",e["cid"]) and e["released"] is True,"complete owned CID + actual release")
        rel=read(e["release_ref"]);require(rel["cid"]==e["cid"] and rel["retained"] is True and
          rel["deleted"] is False and rel["released"] is True and rel["noOOM"] is True and not rel.get("secondary"),"actual own cleanup terminal")
        stopped=read(rel["stop"]);require(stopped["exit_code"]==0 and stopped["argv"]==["/usr/bin/docker","stop","--time","15",e["cid"]] and
          stopped["actual_wrapped_argv"]==["/usr/bin/prlimit","--as=unlimited","--",*stopped["argv"]],"actual exact-owned Docker-only AS stop argv/exit")
        raw=read(rel["inspect"]);require(raw["exit_code"]==0,"actual final inspect command exited0")
        xs=json.loads(raw["stdout"]);require(len(xs)==1,"one exact owned inspect");x=xs[0];h=x["HostConfig"];c=x["Config"]
        require(x["Id"]==e["cid"] and x["Name"]=="/"+e["name"] and x["Image"]==IMAGE and c["Image"]==IMAGE and
          c["Labels"].get("model-tuning-lab.owner")=="skvq-current72h-preprojection-v1-007" and
          c["Labels"].get("model-tuning-lab.source")==e["source"] and e["source"]==v["source_lock"]["sha256"],"actual owner/name/image/source")
        state=x["State"];require(not state["Running"] and state["Pid"]==0 and not x.get("ExecIDs") and not state["OOMKilled"],"actual exact stopped/Pid0/noExec/noOOM")
        require(h["Memory"]==e["mem"]==((8 if i==0 else (64 if i==1 else 2))*2**30) and h["MemorySwap"]==e["mem"] and h["NanoCpus"]==4*10**9 and
          h["CpusetCpus"]==e["cpuset"] and h["CgroupnsMode"]=="host" and h["NetworkMode"]=="none" and not h["Privileged"] and
          h["IpcMode"]=="private" and h["ShmSize"]==2*2**30 and h["PidsLimit"]==1024 and
          set(h.get("CapDrop") or [])=={"ALL"} and set(h.get("SecurityOpt") or [])=={"no-new-privileges"} and
          not h.get("DeviceRequests") and not h.get("DeviceCgroupRules"),"actual resource/isolation full readback")
        want=({"/dev/davinci"+str(n):"/dev/davinci"+str(n-4) for n in range(4,8)}|
          {"/dev/"+n:"/dev/"+n for n in ("davinci_manager","devmm_svm","hisi_hdc")}) if i==1 else {}
        ds=h.get("Devices") or []
        require(len(ds)==len(want) and {d["PathOnHost"]:d["PathInContainer"] for d in ds}==want and
          all(d["CgroupPermissions"]=="rwm" for d in ds),"no borrowed Devices[]/0-3 mapping")
        ms=x["Mounts"];expect={d:(s,bool(rw)) for d,(s,rw) in e["mounts"].items()}
        require(len(ms)==len(expect) and len({m["Destination"] for m in ms})==len(ms) and
          all(m["Type"]=="bind" for m in ms) and {m["Destination"]:(m["Source"],m["RW"]) for m in ms}==expect,"mounts actual semantic set")
        M.consume(read(e["mount_preflight_ref"]),expect,e["phase"],source)
        pins=json.loads((BASE/"source_pins.json").read_text())
        require(len(pins["sources"])==8,"exact eight source inputs")
        for pin in pins["sources"]:
            path=pin["snapshot"]
            require(expect.get(path)==(path,False) and reference(path)["sha256"]==pin["sha256"],
              "independent actual read-only donor snapshot mount and byte binding")
        rs=read(e["resource_ref"]);a=rs["allocation"]
        hc=a["host_cpu"];gc=a["guest_cpus"];rc=a["reserve_cpus"]
        require(len(gc)==4 and len(rc)==2 and len({hc,*gc,*rc})==7 and a["total"]==7 and
          hc in rs["host_cpu"]["effective_cpus"] and set(gc+rc)<=set(rs["daemon_cpu"]["effective_cpus"]) and
          rs["host_cpu"]["effective_capacity"]>=1 and rs["daemon_cpu"]["effective_capacity"]>=6,"actual host/daemon seven distinct CPU slots")
        common={r["key"]:r["capacity"] for r in rs["host_cpu"]["quota_ancestors"]}
        for r in rs["daemon_cpu"]["quota_ancestors"]:
            if r["key"] in common:
                for cap in (r["capacity"],common[r["key"]]):require(cap is None or cap>=7,"actual common ancestor total7")
        floor=e["mem"]+512*2**20+8*2**30
        require(rs["ordinary_floor_bytes"]==floor and rs["memory"]["MemAvailable"]>=floor and
          rs["memory"]["SwapTotal"]==rs["memory"]["SwapFree"],"ordinary summed RAM, no HugeTLB borrowing")
        host={r["key"]:r for r in rs["host_memory"]["ancestors"]}
        for r in rs["daemon_memory"]["ancestors"]:
            if r["key"] in host:
                for z in (r,host[r["key"]]):require(z["limit"] is None or z["limit"]-z["used"]>=floor,"actual common memory total")
        if i==1:require(rs["disk_available_bytes"]>=320*2**30,"fresh full QKV/preprojection320GiB disk")
        records.append(dict(cid=e["cid"],resource_ref=e["resource_ref"],release=e["release_ref"]))
    import input_dependency as D
    dependency,dependency_lock,dependency_source=D.lock()
    require(dependency_source==source,"current dependency/host source context")
    dependency_mounts=D.mounts()
    for e in v["owned"]:
        expect={d:(s,bool(rw))for d,(s,rw)in e["mounts"].items()}
        require(all(expect.get(k)==value for k,value in dependency_mounts.items()),"all exact source-bound package directories remain readonly in each actual owned guest")
    D.consume(read(reference(root/"cpu/INPUT_DEPENDENCY.json")),source,dependency_lock,dependency)
    depcli=read(reference(root/"cpu/INPUT_DEPENDENCY_CLI.json"))
    require(depcli["exit_code"]==0 and depcli["argv"]==["/usr/local/python3.12.13/bin/python3","-I","-B",str(C.ROOT/"input_dependency.py"),"--execute","--source-manifest-sha256",source["sha256"],"--output",str(root/"cpu/INPUT_DEPENDENCY.json")],"real fresh dependency CLI original exit/source/output")
    buildercli=read(reference(root/"cpu/INPUT_BUILDER_CLI.json"))
    require(buildercli["exit_code"]==0 and buildercli["argv"]==["/usr/local/python3.12.13/bin/python3","-I","-B",str(C.ROOT/"input_entry.py"),"--execute","--source-manifest-sha256",source["sha256"],"--dependency-ref-json",str(root/"cpu/INPUT_DEPENDENCY_REF.json"),"--output",str(root/"cpu/run-skvq-train-inputs-001-main")],"actual original-body builder through source-bound fresh child bootstrap")
    cpu=json.loads((root/"cpu/ACTUAL23.json").read_text())
    require(cpu["status"]=="ACTUAL23_CLI_SOFTWARE_ONLY" and cpu["total"]==23 and len(cpu["results"])==2,"actual Devices[] complete23")
    expected_tests=(reference(Path(__file__).resolve().parent/"SOFTWARE_TESTS_15.py"),
      reference("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-tp4-qkv-loader-order-v1-001/SOFTWARE_TESTS.py"))
    for r,count,expected in zip(cpu["results"],(15,8),expected_tests):
        require(r["exit_code"]==0 and ("Ran "+str(count)+" tests") in r["stderr"],"actual original software stdout/stderr/exit")
        require(r["source"]==expected and r["argv"][-1]==r["source"]["path"] and
          reference(r["source"]["path"])==r["source"],"actual complete corrected15/original8 CLI source; no inherited old15 PASS")
    consumed=read(v["result"]["consumer"])
    require(consumed["current_source_ref"]==source,"current complete raw consumer source")
    pre=read(consumed["preprojection_consumed_ref"]);base=read(consumed["baseline_receipt_ref"])
    from consume_stage import combine
    combine(base,pre,source,consumed["baseline_receipt_ref"],consumed["preprojection_consumed_ref"])
    require(pre["projection_source_lock_ref"]==source,"actual new projection source; not old expired caller")
    admission=read(read(base["producer_ref"])["admission_ref"])
    require(admission["current_source_ref"]==source and admission["current_clock"]["protocol_ref"]==C.CLOCK and
      admission["owned_cid"]==v["owned"][1]["cid"]and admission["inside_output_root"]==str(root/"run-skvq-capture-projection-001-main"),
      "actual fresh capture source/owned cohort admission")
    n1=read(admission["n1_ref"])
    require(n1["status"]=="SKVQ_ALL4_TINY_N1_CHECKED"and n1["source_ref"]==source and len(n1["ranks"])==4 and
      n1["effective_capture_configuration_checked"]is True,"actual same-source all4 preweights check")
    cfg=read(n1["actual_configuration_ref"]);cpu_config=read(reference(root/"cpu/ACTUAL_ENGINE_CONFIG.json"))
    from engine_config import match_partial
    match_partial(cpu_config,cfg,source)
    for rank,rref in enumerate(n1["ranks"]):
        nv=read(rref)
        from n1_format import consume_row
        consume_row(nv,source)
        require(nv["status"]=="ACTUAL_TINY_CHECKED"and nv["rank"]==rank and nv["source_ref"]==source and
          nv["input"]==[1.,2.]and nv["output"]==[4.,5.]and type(nv["format"])is int and nv["format"]==2 and
          nv["identity"]==nv["after_identity"],"each real all4 tiny identity/output/sync")
    require(consumed["events"]==16384 and consumed["qkv_bytes"]==256*2**30 and
      consumed["global_QKV_head_order_verified_from_actual_bound_loader"] is True and
      consumed["native_ready"] is False and consumed["model_ready"] is False,"actual complete native baseline consumer, not SKVQ PASS")
    proofs=[]
    for r in v["actual_npu_observations"]:
        x=read(r)
        smi=read(x["smi"]);require(smi["exit_code"]==0 and smi["argv"]==["/usr/local/sbin/npu-smi","info"],"actual SMI original")
        consume_protected(read(x["protected_boundary_ref"]),v["protected0_3"],v["owned"],v["host_pid"],x["smi"],bool(x["proofs"]))
        require(x["actual_hbm"]==[actual_hbm(smi["stdout"],card)for card in(4,5,6,7)],"all4 physical HBM3GiB reserve independently re-read")
        for p in x["proofs"]:
            require(p["physical"] in (4,5,6,7) and p["chip"]==0 and v["owned"][1]["cid"] in p["cgroup"] and
              p["namespace_pids"][0]==p["pid"] and p["start_ticks"]>0 and p["argv"],"actual own per-card PID/start/cgroup/argv")
            actual=hashlib.sha256(bytes([0]).join(z.encode() for z in p["argv"])+bytes([0])).hexdigest()
            require(actual==p["cmdline_sha256"],"actual original proc NUL argv digest")
            proofs.append(p)
    require({p["physical"] for p in proofs}=={4,5,6,7},"all actual four-card capture process evidence, not declarations")
    require(reference(root/"HOST_RESULT.json")==before,"immutable original terminal")
    return dict(schema="SKVQ_HOST_CAPTURE_RAW_CONSUMED_V1",status="FULL_BASELINE_RAW_CAPTURE_HOST_CONSUMED_NOT_AUTHOR_CALIBRATION",
      actual_input_dependency_ref=reference(root/"cpu/INPUT_DEPENDENCY.json"),host_result=before,owned=records,full_raw_consumer=v["result"]["consumer"],actual23=True,actual_four_card_proofs=len(proofs),
      author_calibration_pending=True,packed_cache_provider_pending=True,service_and_32768_e2e_pending=True,
      actual_weight_publisher_identity_pending=True,protected_owned_boundary_checked=True,external_protected_unchanged_claimed=False,current_source_ref=source,preprojection_consumed_ref=consumed["preprojection_consumed_ref"],
      current_clock=C.clock(),MAIN_original_operation_authority_pending=True,native_ready=False,model_ready=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256");p.add_argument("--root");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"native_ready":False,"model_ready":False}));return
    C.configure(a.source_manifest_sha256)
    print(json.dumps(publish_json(a.output,consume(a.root)),sort_keys=True))
if __name__=="__main__":main()
