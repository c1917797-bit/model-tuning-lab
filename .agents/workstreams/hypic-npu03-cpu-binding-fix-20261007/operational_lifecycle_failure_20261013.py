#!/usr/bin/env python3
"""Read-only independent audit of the aborted operational run, not acceptance."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/operational-lifecycle-20261013-disabled")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(ok,message):
    if not ok:raise ValueError(message)
def classify(terminal,stop,guard,has_health,has_smoke):
    cid=terminal["container_id"]
    need(terminal["completed"] is False and "lane guard detected foreign" in terminal["error"],"not the retained isolation failure")
    need(not has_health and not has_smoke,"unexpected serving/request evidence")
    need(stop["container_id"]==guard["owned_container_id"]==cid,"ownership")
    need(all(stop.get(k) is True for k in ["container_removed","owned_npus_released","port_released"]),"release")
    need(stop["service_reached_health"] is False and stop["prehealth_top_error"] is None and stop["service_log_error"] is None,"release evidence incomplete")
    need(guard["samples"]>0 and not guard["probe_errors"] and bool(guard["foreign"]),"foreign-process evidence")
    found=[dict(at_utc=e["at_utc"],**p) for e in guard["foreign"] for p in e["processes"]]
    need(all(p["physical_npu"] in range(4) and p.get("container_id") and p["container_id"]!=cid for p in found),"external ownership")
    return dict(decision="ISOLATION_FAILED_BEFORE_HEALTH",lifecycle_pass=False,
        scored_requests=0,operational_responses=0,uninstalled_started=False,
        exact_owned_release=True,guard_samples=guard["samples"],foreign_observations=found,
        source_at_health_proven=False,quality_or_performance_claim=False,
        old_quality_decision_changed=False,all_skill_acceptance=False)
def evaluate():
    frozen=read(HERE/"operational_lifecycle_20261013.json")
    for n,h in frozen["files"].items():need(sha(HERE/n)==h,"support drift")
    need(sha(HERE/"native_lifecycle_contract.json")==frozen["legacy_contract_sha256"],"legacy drift")
    c,t,s,g,i=[read(ROOT/p) for p in ["contract.json","terminal.json","hypic-only/service-stop.json","hypic-only/lane-guard.json","container-inspect.json"]]
    need(c["frozen"]==frozen and c["preregistration_sha256"]==sha(HERE/"operational_lifecycle_20261013.json"),"contract identity")
    need(c["git_commit"]=="059f343a4c33d6ad5024a15eeb6cf9d9138aaa87","executed checkpoint")
    need(i["Id"]==t["container_id"],"initial container")
    spec=dict(binds=sorted(i["HostConfig"]["Binds"]),env=sorted(i["Config"]["Env"]),
        command=i["Config"]["Cmd"],devices=i["HostConfig"]["Devices"],
        image=i["Image"],cpuset=i["HostConfig"]["CpusetCpus"])
    need(hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(",",":")).encode()).hexdigest()==frozen["phase_spec_sha256"]["disabled"],"actual specification")
    devices=[d["PathOnHost"] for d in spec["devices"] if re.fullmatch(r"/dev/davinci\d+",d["PathOnHost"])]
    need(devices==["/dev/davinci"+str(x) for x in range(4)],"physical scope")
    logs=list((ROOT/"hypic-only").glob("service.full.*.log"))
    need(len(logs)==1 and sha(logs[0])==s["service_log_sha256"],"retained full log")
    need(not ROOT.with_name("operational-lifecycle-20261013-uninstalled").exists(),"unexpected second stage")
    result=classify(t,s,g,(ROOT/"hypic-only/service-start.json").exists(),(ROOT/"smoke.json").exists())
    result["artifact_hashes"]={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob("*") if p.is_file()}
    return result
if __name__=="__main__":print(json.dumps(evaluate(),sort_keys=True,indent=2))
