"""HOST-only preregistered A/B/A decision over independently re-audited R36 arms."""
import argparse,hashlib,json,math,os,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r36_step_durability_audit as reviewer

def decision(a1,b1,a2):
    values=(a1,b1,a2)
    if any(type(x)not in(int,float)or not math.isfinite(x)or x<=0 for x in values):
        raise ValueError("positive finite actual unprofiled makespans required")
    mean_a=(a1+a2)/2
    drift=abs(a2-a1)/mean_a*100
    gain=(1-b1/mean_a)*100
    state=("INCONCLUSIVE_CONTROL_DRIFT"if drift>5
           else"SUPPORTED_BOUNDED_STEP_DURABILITY_EFFECT"if gain>=5
           else"INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD")
    return {"state":state,"A1_seconds":a1,"B1_seconds":b1,"A2_seconds":a2,
        "control_mean_seconds":mean_a,"control_relative_drift_percent":drift,
        "B_gain_percent":gain,"drift_limit_percent":5,"screen_gain_percent":5,
        "scope":"One integrated16/c16/32768/64 A/B/A diagnostic; not formal1024 repeated performance, fullquality or wholepaper acceptance.",
        "comparison":"Same HYPIC implementation: selected-step vs original evidence durability. No native G1 comparison.",
        "native_speed_gain_proven":False,"r30_native_comparison_unchanged":True,"full_goal_complete":False}

def canonical(x):return json.loads(json.dumps(x,sort_keys=True))

def load_arm(arm,path,definition=None):
    cp=Path("STEP_DURABILITY_R36_"+arm+"_R2_20261025_CONTRACT.json").resolve()
    c=json.loads(cp.read_bytes())
    if c.get("r33_arm")!=arm:raise ValueError("exact arm contract required")
    p=Path(path)
    if not p.is_absolute()or p.is_symlink()or p.stat().st_size>4*1024**2:
        raise ValueError("bounded absolute original independent audit required")
    data=p.read_bytes();sealed=json.loads(data)
    if sealed.get("live_release_verified")is not True:
        raise ValueError("prior independent live-release audit required")
    fresh=reviewer.audit(cp,live_release=False,definition=definition)
    previous=dict(sealed,live_release_verified=False)
    if canonical(previous)!=canonical(fresh):
        raise ValueError("saved independent audit differs from fresh immutable evidence")
    if fresh.get("bounded_step_durability_screen_valid")is not True or c["r33_arm"]!=arm:
        raise ValueError("valid exact R36 arm evidence required")
    if(fresh["prefix_terminal"]["terminal_only"]is not False
       or fresh["durability"]["enabled"]is not(arm=="B1")
       or fresh["durability"]["selected_step_durability_valid"]is not True):
        raise ValueError("exact durability-only treatment and original prefix path required")
    return c,fresh,{"contract":cp.name,"contract_sha256":hashlib.sha256(cp.read_bytes()).hexdigest(),
        "audit":str(p),"audit_sha256":hashlib.sha256(data).hexdigest()}

def validate_matched(contracts,manifests,configs):
    if len(contracts)!=3 or [c.get("r33_arm")for c in contracts]!=["A1","B1","A2"]:
        raise ValueError("ordered exact A1/B1/A2 cohort required")
    keys=("image","model","model_config_sha256","physical_npus","tp","port","hccl_ports",
        "cpu_set","enable_thinking","enable_prefix_caching","max_output_tokens",
        "enforce_eager","graph_runtime","formal_token_artifact","profile_diagnostic",
        "host_controller_source_sha256","study_source_map_sha256","absolute_stop_utc","r33_protocol",
        "r36_code_checkpoint","r36_role","r36_host_audit","renewed_authority")
    for key in keys:
        if any(c.get(key)!=contracts[0].get(key)for c in contracts[1:]):
            raise ValueError("matched identity/protocol/source changed: "+key)
    if contracts[0].get("r36_role")!="SELECTED_STEP_DURABILITY_SINGLE_VARIABLE_SCREEN":
        raise ValueError("declared durability screen required")
    if any(c["cache_diagnostic"]["source_sha256"]!=contracts[0]["cache_diagnostic"]["source_sha256"]for c in contracts[1:]):
        raise ValueError("A/B runtime source maps differ")
    if any(c["cache_diagnostic"]["compact_manifest"]!=c["successor_manifest"]for c in contracts):
        raise ValueError("actual launch and checked manifest slots differ")
    if len(manifests)!=3 or len(configs)!=3 or configs[0]!=configs[1]or configs[0]!=configs[2]:
        raise ValueError("all original algorithm configurations must be identical")
    if configs[0].get("r33_prefix_terminal_only")is not False:
        raise ValueError("rejected prefix-output treatment cannot be enabled")
    if manifests[0]!=manifests[2]or"step_durability"in manifests[0]:
        raise ValueError("both controls require identical original durability manifest")
    candidate=dict(manifests[1]);setting=candidate.pop("step_durability",None)
    if(candidate!=manifests[0]or setting!={"enabled":True,"profile":"selected-model-step-durability-v1"}
       or any("evidence_io_budget"in m for m in manifests)):
        raise ValueError("only the declared step-durability manifest metadata may change")
    return True

def audit_pair(paths,definition=None):
    rows=[load_arm(arm,paths[arm],definition)for arm in("A1","B1","A2")]
    contracts=[x[0]for x in rows];manifests=[];configs=[]
    for c in contracts:
        m=json.loads(Path(c["successor_manifest"]).read_bytes())
        manifests.append(m);configs.append(json.loads(Path(m["config"]).read_bytes()))
    validate_matched(contracts,manifests,configs)
    result=decision(*(x[1]["diagnostic_makespan_seconds"]for x in rows))
    result["arms"]=[x[2]for x in rows]
    result["independent_audits_replayed"]=True
    result["raw_results_rewritten"]=False
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arm in("a1","b1","a2"):p.add_argument("--"+arm+"-audit",required=True)
    p.add_argument("--definition",required=False)
    p.add_argument("--output",required=True);a=p.parse_args()
    result=audit_pair({"A1":a.a1_audit,"B1":a.b1_audit,"A2":a.a2_audit},a.definition)
    data=(json.dumps(result,sort_keys=True)+"\n").encode()
    out=Path(a.output)
    with out.open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"output":str(out),"sha256":hashlib.sha256(data).hexdigest(),"decision":result}))
