"""Host-only replay of pinned profiling/observer lessons; no current device query."""
import argparse,hashlib,json
from pathlib import Path
import sys
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits.r32_gate_cast_decision import load_arm

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(path):
    p=Path(path).resolve();w=p.parent;root=w.parents[2]
    ledger=json.loads(p.read_bytes())
    if ledger["full_reproduction_accepted"]is not False:
        raise ValueError("learning cannot accept the paper")
    for rel,digest in ledger["evidence_sha256"].items():
        target=(w/rel).resolve()
        if not target.is_relative_to(w)or target.is_symlink()or sha(target)!=digest:
            raise ValueError("lesson evidence binding drift")
    for rel,digest in ledger["maintainer_documents_sha256"].items():
        target=(root/rel).resolve()
        if not target.is_relative_to(root)or target.is_symlink()or sha(target)!=digest:
            raise ValueError("maintainer document binding drift")
    hardware=Path(ledger["hardware"]["path"])
    if sha(hardware)!=ledger["hardware"]["sha256"]:
        raise ValueError("four-rank hardware report drift")
    parsed=json.loads(hardware.read_bytes())
    if len(parsed["ranks"])!=4 or any(set(r["devices"])!={str(i)}for i,r in enumerate(parsed["ranks"])):
        raise ValueError("actual rank/device hardware identity incomplete")
    _,a1,binding=load_arm("A1",ledger["A1"]["path"],ledger["observer_definition"])
    if binding["audit_sha256"]!=ledger["A1"]["sha256"]or a1["hot"]["denominator"]!=16:
        raise ValueError("actual A1 evidence replay differs")
    if a1["gate_cast"]["timed_observations"]!=1152:
        raise ValueError("actual namespace join counterexample drift")
    pair=json.loads((w/"R30_FIRST_PAIR_DECISION_20261025.json").read_bytes())
    if (pair.get("status")!="VALID_MECHANISM_NO_NET_SPEED_GAIN"
            or pair.get("full_goal_accepted")is not False
            or not pair["G3"]["tpot_ms"]>pair["G1"]["tpot_ms"]
            or abs((pair["G3"]["tpot_ms"]/pair["G1"]["tpot_ms"]-1)*100-pair["delta"]["tpot_percent"])>1e-9):
        raise ValueError("historical negative pair was promoted or arithmetic changed")
    return{"artifact_and_A1_evidence_replay":"PASS","current_device_query":False,
        "new_npu_work":False,"full_reproduction_accepted":False,
        "scope":"historical hashes,4rank hardware and actual source-bound A1 observation only; not independent blind Skill behavior or29functional acceptance"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--ledger",required=True)
    print(json.dumps(verify(p.parse_args().ledger),sort_keys=True))
