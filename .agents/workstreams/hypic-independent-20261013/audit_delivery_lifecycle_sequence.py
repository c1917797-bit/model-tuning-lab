"""Independent ordered disable/enable/uninstall-restart lifecycle composition."""
import hashlib,json,subprocess
from datetime import datetime,timedelta
from pathlib import Path
from audit_delivery_lifecycle_terminal import audit as audit_stage

IDENTITY=("delivery_adapter","image","model","model_config_sha256","physical_npus","tp","port","hccl_ports","cpu_set",
    "formal_token_artifact","max_output_tokens","lifecycle_private_output_tokens","enable_thinking",
    "enable_prefix_caching","enforce_eager","completion","controller_sha256","absolute_stop_utc")

def _utc(value):
    if not isinstance(value,str):raise ValueError("explicit lifecycle UTC required")
    try:t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:raise ValueError("valid lifecycle UTC required")
    if t.utcoffset()!=timedelta(0):raise ValueError("timezone-aware UTC required")
    return t

def audit_sequence_records(stages):
    if len(stages)!=3 or [s["contract"].get("lifecycle_stage")for s in stages]!=["disabled","enabled","uninstalled"]:
        raise ValueError("ordered disabled/enabled/uninstalled stages required")
    contracts=[s["contract"]for s in stages];base=contracts[0]
    if base.get("delivery_adapter")is not True:raise ValueError("explicit delivery adapter lifecycle required")
    if any(k not in c for c in contracts for k in IDENTITY) or any(c[k]!=base[k]for c in contracts for k in IDENTITY):
        raise ValueError("same source/image/model/input/protocol lifecycle required")
    packages=[c.get("cache_diagnostic")for c in contracts]
    if not packages[0] or packages[0]!=packages[1] or packages[2]is not None:
        raise ValueError("same mounted package then removed startup package required")
    expected_sources=packages[0]["source_sha256"]
    if not expected_sources or contracts[2].get("baseline_host_source_sha256")!=expected_sources:
        raise ValueError("same complete host source checkpoint across restart required")
    cids=[];roots=[];intervals=[];previous_end=None
    for stage in stages:
        c=stage["contract"];name=c["lifecycle_stage"];r=stage["audit"];release=stage["release"];start=stage["start"];pre=stage["preflight"]
        if r.get("lifecycle_stage_audited")is not True or r.get("stage")!=name or r.get("startup",{}).get("startup_controls_verified")is not True or r.get("transport",{}).get("lifecycle_requests_verified")is not True:
            raise ValueError("independently audited stage required")
        if name=="enabled":
            if r.get("hot",{}).get("accepted_hot_coverage")is not True or r.get("hot",{}).get("denominator")!=2 or not r.get("physical"):
                raise ValueError("enabled fourworker mechanism stage required")
        elif r.get("hot")is not None:raise ValueError("disabled/uninstalled activation is forbidden")
        cid=start.get("container_id")
        if release.get("owned_container")!=cid or release.get("removed")is not True or release.get("final_physical_processes")!=[]:
            raise ValueError("each exact own stage released required")
        if pre.get("processes")!=[] or pre.get("foreign")!=[]:
            raise ValueError("each stage requires actual empty preflight")
        begin=_utc(pre.get("utc"));end=_utc(release.get("utc"))
        if begin>=_utc(c["absolute_stop_utc"]) or end<begin or previous_end is not None and begin<previous_end:
            raise ValueError("release-before-next-start chronology required")
        previous_end=end;cids.append(cid);roots.append(stage["raw_root"])
        intervals.append({"stage":name,"preflight":pre["utc"],"released":release["utc"]})
    if len(set(cids))!=3 or any(not isinstance(x,str)or len(x)!=64 for x in cids) or len(set(roots))!=3:
        raise ValueError("new isolated instance and immutable raw root for each stage required")
    return {"lifecycle_sequence_audited":True,"stages":["disabled","enabled","uninstalled"],"container_ids":cids,
        "intervals":intervals,"source_bindings":len(expected_sources),
        "hot_inprocess_uninstall_claimed":False,"prior_performance_quality_verified":False,
        "scope":"bounded service startup disable/enable/remove-package restart and exact release only; not performance/quality/production/29Skill acceptance"}

def audit_sequence(contract_paths,*,live_release=False):
    paths=[Path(p).resolve()for p in contract_paths]
    if len(paths)!=3 or len(set(paths))!=3 or len({p.parent for p in paths})!=1:
        raise ValueError("three distinct contracts in same package checkpoint required")
    stages=[];hashes=[]
    for path in paths:
        c=json.loads(path.read_text());raw=Path(c["raw_root"])
        result=audit_stage(path,live_release=False)
        journal=[json.loads(x)for x in (raw/"events.jsonl").read_text().splitlines()]
        pre=[e["snapshot"]for e in journal if e.get("event")=="preflight"]
        if len(pre)!=1:raise ValueError("one preflight snapshot per lifecycle stage required")
        start=json.loads((raw/"service-start.json").read_text());release=json.loads((raw/"release.json").read_text())
        stages.append(dict(contract=c,audit=result,preflight=pre[0],start=start,release=release,raw_root=str(raw.resolve())))
        hashes.append({"contract_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "raw_root":str(raw),"result_sha256":hashlib.sha256((raw/"result.json").read_bytes()).hexdigest(),
            "release_sha256":hashlib.sha256((raw/"release.json").read_bytes()).hexdigest()})
    result=audit_sequence_records(stages)
    if live_release:
        from formal_r15_tp4 import snapshot,port_free
        for cid in result["container_ids"]:
            q=subprocess.run(["docker","inspect",cid],capture_output=True,text=True)
            if q.returncode==0 or q.stdout.strip()!="[]"or not("No such object"in q.stderr or"No such container"in q.stderr):
                raise ValueError("all exact lifecycle containers must be absent")
        if snapshot()["processes"]:raise ValueError("physical0-3 not empty at final audit")
        port_free(stages[-1]["contract"]["port"])
    result.update(stage_audits=[s["audit"]for s in stages],artifacts=hashes,live_release_verified=live_release)
    return result
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contracts",nargs=3,required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit_sequence(a.contracts,live_release=a.live_release)))
