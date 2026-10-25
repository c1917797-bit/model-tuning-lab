"""Replay artifact lifecycle learning from real immutable R33 control data."""
import argparse,ast,hashlib,json,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.verify_profile_id_learning import verify as verify_previous
from host_audits import r33_prefix_terminal_trial as owner
from host_audits.r30b_graph_formal_audit import parse_info_graph
from host_audits.r33_prefix_terminal_evidence import first_shape_rows
from audit_full40_hot_coverage import _audit_hot
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify(path):
    p=Path(path).resolve();ledger=json.loads(p.read_bytes());w=p.parent
    if sha(__file__)!=ledger["lifecycle_verifier_source_sha256"]:
        raise ValueError("actual lifecycle verifier source drift")
    previous=verify_previous(p)
    case=json.loads((w/"R33_A1_CONTROL_TOOLING_FAILURE_20261025.json").read_bytes())
    sealed=case["review"]
    cp=w/case["contract"]
    if sha(cp)!=case["contract_sha256"]:raise ValueError("original control contract changed")
    c=json.loads(cp.read_bytes());owner.check_contract(c,source_root=w,require_new_root=False)
    raw=Path(c["raw_root"])
    for name,digest in sealed["raw_sha256"].items():
        if Path(name).name!=name or sha(raw/name)!=digest:raise ValueError("control raw evidence drift")
    terminal=json.loads((raw/"result.json").read_bytes())
    release=json.loads((raw/"release.json").read_bytes());start=json.loads((raw/"service-start.json").read_bytes())
    if(terminal["valid"]is not False or terminal["error"]["type"]!="FileNotFoundError"
       or "service.log"not in terminal["error"]["message"]or release["removed"]is not True
       or release["owned_container"]!=start["container_id"]):
        raise ValueError("actual failed phase and exact historical release required")
    journal=[json.loads(x)for x in(raw/"events.jsonl").read_text().splitlines()]
    warm=[x for x in journal if x.get("event")=="r33-private-warmup"]
    if(len(warm)!=48 or any(not x["ok"]or x["response"]["usage"]["prompt_tokens"]!=32768
            or x["response"]["usage"]["completion_tokens"]!=64 for x in warm)
       or any(x.get("event")in("r33-begin","r33-response")for x in journal)):
        raise ValueError("warm versus measured scope changed")
    if {x["wave"]for x in warm}!={0,1,2}:raise ValueError("actual three warm waves required")
    info=parse_info_graph((raw/"service.log").read_bytes())
    events=owner.retained.components._events(raw,"compact-worker-")
    cfg,manifest=owner.retained.components._manifest(c,w)
    hot=_audit_hot(events,[x["response"]["id"]for x in warm],manifest_sha256=manifest,expected_count=48)
    if not hot["accepted_hot_coverage"]or len(hot["covered"])!=48:
        raise ValueError("actual fourworker warm cohort evidence missing")
    state=first_shape_rows(events,info["workers"],manifest)
    if len(state)!=8 or any(x.get("terminal_only")is not False for x in state):
        raise ValueError("actual control-only private state evidence changed")
    for rank in range(4):
        if {x["length"]for x in state if x["rank"]==rank}!={8,39}:
            raise ValueError("actual shape scope differs")
    observed=[x for x in events if x.get("event")=="r33_prefix_terminal_observed"]
    if not observed or any(x.get("terminal_only")is not False for x in observed):
        raise ValueError("control was relabeled enabled")
    samples=[x["snapshot"]for x in journal if x.get("event")=="isolation"]
    owner.retained.audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    # Source-bound actual producer writes terminal service.log in a finally block.
    base_tree=ast.parse(Path(owner.base.__file__).read_text())
    def writes_final_log(nodes):
        for node in nodes:
            for item in ast.walk(node):
                if(isinstance(item,ast.Call)and isinstance(item.func,ast.Attribute)
                   and item.func.attr=="write_text"
                   and any(isinstance(x,ast.Constant)and x.value=="service.log"for x in ast.walk(item.func.value))):
                    return True
        return False
    if not any(isinstance(n,ast.Try)and writes_final_log(n.finalbody)for n in ast.walk(base_tree)):
        raise ValueError("actual terminal producer lifecycle changed")
    return {"historical_A1_profile_replay":previous["artifact_and_A1_evidence_replay"],
        "R33_warm_component_replayed":True,"warm_requests":48,"private_control_state_checks":8,
        "R33_full_arm_valid":False,"enabled_candidate_proven":False,
        "source_producer_lifecycle_verified":True,"current_device_query":False,"new_npu_work":False,
        "full_reproduction_accepted":False,"blind_skill_behavior_verified":False,"all29_functional_verified":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--ledger",required=True)
    print(json.dumps(verify(p.parse_args().ledger),sort_keys=True))
