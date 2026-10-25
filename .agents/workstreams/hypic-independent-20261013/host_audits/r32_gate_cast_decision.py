"""HOST-only preregistered A/B/A decision over independently re-audited R32 arms."""
import argparse,hashlib,json,math,os
from pathlib import Path
from host_audits import r32_gate_cast_audit as reviewer

def decision(a1,b1,a2):
    values=(a1,b1,a2)
    if any(type(x)not in(int,float)or not math.isfinite(x)or x<=0 for x in values):
        raise ValueError("positive finite actual unprofiled makespans required")
    mean_a=(a1+a2)/2
    drift=abs(a2-a1)/mean_a*100
    gain=(1-b1/mean_a)*100
    state=("INCONCLUSIVE_CONTROL_DRIFT"if drift>5
           else"SUPPORTED_BOUNDED_GATE_CAST_EFFECT"if gain>=5
           else"INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD")
    return {"state":state,"A1_seconds":a1,"B1_seconds":b1,"A2_seconds":a2,
        "control_mean_seconds":mean_a,"control_relative_drift_percent":drift,
        "B_gain_percent":gain,"drift_limit_percent":5,"screen_gain_percent":5,
        "scope":"One integrated16/c16/32768/64 A/B/A diagnostic; not formal1024 repeated performance, fullquality or wholepaper acceptance.",
        "full_goal_complete":False}

def canonical(x):return json.loads(json.dumps(x,sort_keys=True))

def load_arm(arm,path):
    cp=Path("GATE_CAST_R32_"+arm+"_20261025_CONTRACT.json").resolve()
    c=json.loads(cp.read_bytes())
    if c.get("r32_arm")!=arm:raise ValueError("exact arm contract required")
    p=Path(path)
    if not p.is_absolute()or p.is_symlink()or p.stat().st_size>4*1024**2:
        raise ValueError("bounded absolute original independent audit required")
    data=p.read_bytes();sealed=json.loads(data)
    if sealed.get("live_release_verified")is not True:
        raise ValueError("prior independent live-release audit required")
    fresh=reviewer.audit(cp,live_release=False)
    previous=dict(sealed,live_release_verified=False)
    if canonical(previous)!=canonical(fresh):
        raise ValueError("saved independent audit differs from fresh immutable evidence")
    if fresh.get("bounded_gate_cast_arm_valid")is not True or fresh["gate_cast"]["arm"]!=arm:
        raise ValueError("valid exact R32 arm evidence required")
    if fresh["gate_cast"]["hoisted"]is not(arm=="B1"):
        raise ValueError("one exact gate-placement switch required")
    return c,fresh,{"contract":cp.name,"contract_sha256":hashlib.sha256(cp.read_bytes()).hexdigest(),
        "audit":str(p),"audit_sha256":hashlib.sha256(data).hexdigest()}

def audit_pair(paths):
    rows=[load_arm(arm,paths[arm])for arm in("A1","B1","A2")]
    contracts=[x[0]for x in rows]
    keys=("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports",
        "cpu_set","enable_thinking","enable_prefix_caching","max_output_tokens",
        "enforce_eager","graph_runtime","formal_token_artifact","profile_diagnostic",
        "host_controller_source_sha256","study_source_map_sha256","absolute_stop_utc")
    for key in keys:
        if any(c.get(key)!=contracts[0].get(key)for c in contracts[1:]):
            raise ValueError("matched identity/protocol/source changed: "+key)
    if any(c["cache_diagnostic"]["source_sha256"]!=contracts[0]["cache_diagnostic"]["source_sha256"]for c in contracts[1:]):
        raise ValueError("A/B runtime source maps differ")
    configs=[]
    for c in contracts:
        m=json.loads(Path(c["successor_manifest"]).read_bytes())
        configs.append(json.loads(Path(m["config"]).read_bytes()))
    if configs[0]!=configs[2]or{k for k in configs[0]if configs[0][k]!=configs[1][k]}!={"c1_gate_cast_hoist"}:
        raise ValueError("more than one behavioral configuration variable changed")
    result=decision(*(x[1]["diagnostic_makespan_seconds"]for x in rows))
    result["arms"]=[x[2]for x in rows]
    result["independent_audits_replayed"]=True
    result["raw_results_rewritten"]=False
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arm in("a1","b1","a2"):p.add_argument("--"+arm+"-audit",required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    result=audit_pair({"A1":a.a1_audit,"B1":a.b1_audit,"A2":a.a2_audit})
    data=(json.dumps(result,sort_keys=True)+"\n").encode()
    out=Path(a.output)
    with out.open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"output":str(out),"sha256":hashlib.sha256(data).hexdigest(),"decision":result}))
