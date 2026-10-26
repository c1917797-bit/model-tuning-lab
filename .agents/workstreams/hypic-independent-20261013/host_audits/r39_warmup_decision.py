"""HOST-only predeclared R39 three-arm raw-audit replay and protocol decision."""
import argparse,copy,hashlib,json,math,os,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r39_warmup_audit import audit
PLAN_COMMIT="026b571b5b46a4401643fb55c5e41b82d43fad2f"
PLAN_NAME="R39_TARGET_PATH_WARMUP_CAUSAL_PLAN_20261026.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def calculate(a1,b1,a2,extra):
    if any(type(x)not in(int,float)or not math.isfinite(x)or x<=0 for x in(a1,b1,a2,extra)):
        raise ValueError("positive actual unit and explicit warmup durations required")
    control=(a1+a2)/2;drift=abs(a2-a1)/control*100;gain=(control-b1)/control*100
    saved=control-b1
    state=("INCONCLUSIVE_CONTROL_DRIFT"if drift>5 else
           "SUPPORTED_BOUNDED_TARGET_WARMUP_COUNT_EFFECT"if gain>=5 else"INSUFFICIENT_TARGET_WARMUP_GAIN")
    return {"state":state,"A1_seconds":a1,"B1_seconds":b1,"A2_seconds":a2,
        "control_mean_seconds":control,"control_drift_percent":drift,"measured_unit_gain_percent":gain,
        "accept_gain_percent_at_least":5,"max_control_drift_percent":5,
        "B1_extra_full_target_warmup_seconds":extra,"B1_measured_plus_extra_warmup_seconds":b1+extra,
        "single_unit_including_extra_warmup_gain_percent":(control-b1-extra)/control*100,
        "arithmetic_extra_cost_over_observed_unit_saving":extra/saved if saved>0 else None,
        "arithmetic_ratio_not_an_amortization_or_future_speed_prediction":True}
def run(contracts,reports):
    if len(contracts)!=3 or len(reports)!=3:raise ValueError("all three actual arms required")
    root=Path(contracts[0]).resolve().parent
    if root!=Path.cwd().resolve()or any(Path(p).resolve().parent!=root for p in contracts):
        raise ValueError("owning workstream and exact three contracts required")
    plan=(root/PLAN_NAME).read_bytes()
    relative=str((root/PLAN_NAME).relative_to(root.parent.parent.parent))
    frozen=subprocess.check_output(["git","show",PLAN_COMMIT+":"+relative],cwd=str(root))
    if plan!=frozen:raise ValueError("pre-A1 published decision policy changed")
    policy=json.loads(plan)["progression"]
    if policy["accept_effect_gain_percent_at_least"]!=5 or policy["max_control_drift_percent"]!=5:
        raise ValueError("predeclared five-percent gates required")
    cs=[];accepted=[];refs=[]
    for i,(cp,ap)in enumerate(zip(contracts,reports)):
        cp=Path(cp).resolve();ap=Path(ap)
        if not ap.is_absolute()or ap.is_symlink()or not ap.is_file():raise ValueError("exact original absolute audit required")
        c=json.loads(cp.read_bytes());original=json.loads(ap.read_bytes());arm=("A1","B1","A2")[i]
        if(c["r39_arm"]!=arm or c["r39_target_warmup_count"]!=(2 if arm=="B1"else 0)
           or original.get("valid")is not True or original.get("live_release_verified")is not True
           or original.get("r39_trial",{}).get("arm")!=arm):
            raise ValueError("actual valid/released original arm required")
        replay=json.loads(json.dumps(audit(cp,live_release=False),sort_keys=True))
        expected=copy.deepcopy(original);expected["live_release_verified"]=False
        if replay!=expected:raise ValueError("independent full raw audit replay differs: "+arm)
        cs.append(c);accepted.append(original)
        refs.append({"arm":arm,"contract":cp.name,"contract_sha256":sha(cp),"audit":str(ap),
                     "audit_sha256":sha(ap),"independent_full_raw_replay":True})
    keys=("image","model","model_config_sha256","cpu_set","physical_npus","tp","port","hccl_ports",
          "formal_token_artifact","graph_runtime","enable_prefix_caching","enable_thinking",
          "cache_diagnostic","study_source_map_sha256","host_controller_source_sha256",
          "r38_protocol","r39_warm_descriptors","successor_manifest","absolute_stop_utc")
    for c in cs[1:]:
        if any(c.get(k)!=cs[0].get(k)for k in keys):raise ValueError("matched source/input/model/ruler identity differs")
    if len({c["raw_root"]for c in cs})!=3 or len({c["container_name"]for c in cs})!=3:
        raise ValueError("three distinct immutable attempts required")
    for i in(1,2):
        previous=cs[i]["r39_previous_audit"]
        if previous["path"]!=refs[i-1]["audit"]or previous["sha256"]!=refs[i-1]["audit_sha256"]:
            raise ValueError("actual predecessor audit chain differs")
    result=calculate(*(a["diagnostic_makespan_seconds"]for a in accepted),
                     accepted[1]["target_warmups"]["extra_target_warmup_seconds"])
    return dict(result,schema="hypic-r39-three-arm-decision/v1",arms=refs,
        predeclared_plan_commit=PLAN_COMMIT,plan_sha256=hashlib.sha256(plan).hexdigest(),
        all_arms_actual16_and_fourworker_hot=True,all_original_audits_recorded_exact_live_release=True,
        measured_single_variable="0/2/0 extra full target warmup requests; four cache preparations common",
        algorithm_changed=False,compiler_cause_proven=False,native_speed_gain_proven=False,
        full_goal_complete=False,scope="One bounded protocol contrast only. A warmup-count effect is not a compiler diagnosis, algorithm/native/formal40 speed gain, full paired quality, lifecycle or paper acceptance.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contracts",nargs=3,required=True)
    p.add_argument("--audits",nargs=3,required=True);p.add_argument("--output",required=True)
    a=p.parse_args();r=run(a.contracts,a.audits);data=(json.dumps(r,sort_keys=True)+"\n").encode()
    with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"state":r["state"],"measured_unit_gain_percent":r["measured_unit_gain_percent"],
        "control_drift_percent":r["control_drift_percent"],"output":a.output,
        "sha256":hashlib.sha256(data).hexdigest(),"scope":r["scope"]}))
