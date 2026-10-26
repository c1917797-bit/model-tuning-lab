"""Standalone HOST-only R40 pair decision; excluded from the frozen launch closure."""
import argparse,copy,hashlib,json,math,os,subprocess
from pathlib import Path
from host_audits.r40_formal_audit import audit
PLAN="R40_EQUAL_TARGET_WARM_FORMAL_PLAN_20261026.json"
PLAN_COMMIT="b18abb1d57ff714bca4c454d17bfcf5306417fd3"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def calculate(g1,g3):
    keys=("weighted_tpot_ms","ttft_p95_ms")
    for row in(g1,g3):
        if any(type(row.get(k))not in(int,float)or not math.isfinite(row[k])or row[k]<=0 for k in keys):
            raise ValueError("actual finite positive TPOT and TTFTP95 summaries required")
    delta={k:100*(g3[k]/g1[k]-1)for k in keys}
    proceed=delta["weighted_tpot_ms"]<0 and delta["ttft_p95_ms"]<=0
    return {"state":"PROVISIONAL_FIRST_PAIR_POSITIVE_NOT_REPEATED_ACCEPTANCE"if proceed else"VALID_FIRST_PAIR_NO_NET_GAIN_OR_TAIL_REGRESSION",
        "delta_percent":delta,"allow_repetition_matrix":proceed,"comparison":"G3/G1-1; lower is better",
        "first_pair_only":True,"full_goal_complete":False}
def run(contracts,audits):
    if len(contracts)!=2 or len(audits)!=2:raise ValueError("two actual original arm contracts/audits required")
    root=Path.cwd().resolve()
    if any(Path(p).resolve().parent!=root for p in contracts):raise ValueError("owning workstream contracts required")
    rel=str((root/PLAN).relative_to(root.parent.parent.parent))
    plan=(root/PLAN).read_bytes()
    if subprocess.check_output(["git","show",PLAN_COMMIT+":"+rel],cwd=str(root))!=plan:
        raise ValueError("published pre-G1 plan changed")
    policy=json.loads(plan)["progression"]
    if(policy["first_pair"]!=["G1","G3"]or policy["fresh_same_source_baseline"]is not True
       or policy["require_net_gain"]is not True or policy["ttft_p95_must_not_regress"]is not True
       or policy["stop_on_invalid_or_clear_negative"]is not True):
        raise ValueError("predeclared primary/tail progression differs")
    cs=[];reports=[];refs=[]
    for group,cp,ap in zip(("G1","G3"),contracts,audits):
        cp=Path(cp).resolve();ap=Path(ap)
        if not ap.is_absolute()or ap.is_symlink()or not ap.is_file():raise ValueError("original absolute audit required")
        c=json.loads(cp.read_bytes());original=json.loads(ap.read_bytes())
        if(c["performance_group"]!=group or original.get("formal_r40_full40_valid")is not True
           or original.get("live_release_verified")is not True
           or original.get("r40_launch_identity",{}).get("group")!=group):
            raise ValueError("actual complete independently valid/released arm required")
        expected=copy.deepcopy(original);expected["live_release_verified"]=False
        replay=json.loads(json.dumps(audit(cp,live_release=False),sort_keys=True))
        if replay!=expected:raise ValueError("complete original raw replay differs: "+group)
        cs.append(c);reports.append(original);refs.append({"group":group,"contract":cp.name,
            "contract_sha256":sha(cp),"audit":str(ap),"audit_sha256":sha(ap),"full_original_raw_replay":True})
    keys=("image","model","model_config_sha256","cpu_set","physical_npus","tp","port","hccl_ports",
        "formal_token_artifact","host_controller_source_sha256","study_source_map_sha256",
        "enable_thinking","enable_prefix_caching","enforce_eager","max_output_tokens","performance_round",
        "r40_target_warmup_count","r40_warm_descriptors","absolute_stop_utc")
    if any(cs[0].get(k)!=cs[1].get(k)for k in keys):raise ValueError("matched actual source/model/input/ruler identity differs")
    common0=cs[0]["baseline_host_source_sha256"];common1=cs[1]["cache_diagnostic"]["source_sha256"]
    if common0!=common1 or cs[0]["raw_root"]==cs[1]["raw_root"]or cs[0]["container_name"]==cs[1]["container_name"]:
        raise ValueError("same source map and two immutable attempts required")
    previous=cs[1]["r40_previous_audit"]
    if previous["path"]!=refs[0]["audit"]or previous["sha256"]!=refs[0]["audit_sha256"]:
        raise ValueError("actual native predecessor audit binding differs")
    result=calculate(*(r["timing"]for r in reports))
    result.update(schema="hypic-r40-first-pair-decision/v1",arms=refs,predeclared_plan_commit=PLAN_COMMIT,
        predeclared_plan_sha256=hashlib.sha256(plan).hexdigest(),source_bindings=len(common0),runtime_python=438,
        measured_requests_each_arm=40,output_tokens=1024,concurrency=16,common_cache_preparations=4,
        actual_target_warmups_each_arm=2,target_warm_cost={g:r["target_warmups"]for g,r in zip(("G1","G3"),reports)},
        timing={g:r["timing"]for g,r in zip(("G1","G3"),reports)},all_original_audits_record_exact_live_release=True,
        matched_first_pair_raw_valid=True,repeated_performance_accepted=False,formal_quality_accepted=False,lifecycle_accepted=False,
        scope="One actual equal2targetwarm+4cacheprep full40 pair only; primary/tail screen governs expansion. Extra warm costs retained, old negatives untouched; no compiler diagnosis or fullpaper/repetition/quality/lifecycle/29Skill acceptance.")
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contracts",nargs=2,required=True)
    p.add_argument("--audits",nargs=2,required=True);p.add_argument("--output",required=True)
    a=p.parse_args();r=run(a.contracts,a.audits);data=(json.dumps(r,sort_keys=True)+"\n").encode()
    with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"state":r["state"],"delta_percent":r["delta_percent"],"output":a.output,
        "sha256":hashlib.sha256(data).hexdigest(),"allow_repetition_matrix":r["allow_repetition_matrix"],"scope":r["scope"]}))
