"""Case evidence replay, explicitly not overall Paper-to-Ascend/29Skill acceptance."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
SKILLS={"paper-to-ascend","ascend-canary-implementation","ascend-benchmark-evidence",
        "chicaihong01-host-maintenance","runtime-monkeypatch-delivery","ascend-model-quality-evaluation"}
STATUS="PARTIAL_BOUNDED_VERIFIED_NOT_FULL_FUNCTIONAL_ACCEPTANCE"
def check_scope(c):
    if c.get("status")!=STATUS or c.get("full_goal_accepted")is not False:
        raise ValueError("partial scope must remain explicit")
    mapped=[m["skill"] for m in c["skill_mapping"]]
    if len(mapped)!=len(SKILLS) or set(mapped)!=SKILLS or set(c["skill_sources"])!=SKILLS:
        raise ValueError("exact six mapped source-bound Skills required")
    if not c.get("remaining"):raise ValueError("missing full-goal gaps")
    p=c["new_valid_phase"]
    if (type(p.get("requests"))is not int or p.get("requests")!=40
            or type(p.get("independent_audit_exit"))is not int or p.get("independent_audit_exit")!=0
            or any(p.get(k)is not False for k in ("optimization_accepted","quality_accepted","lifecycle_accepted"))):
        raise ValueError("single phase must not become full acceptance")
    for n in (p["summary"],p["contract"]):
        if n not in c["evidence"]:raise ValueError("phase document hash missing")
    return p

def verify_bindings(base,bindings):
    base=Path(base).resolve()
    for name,spec in bindings.items():
        digest=spec["sha256"]
        if (not isinstance(name,str) or Path(name).is_absolute()
                or not isinstance(digest,str) or not re.fullmatch("[0-9a-f]{64}",digest)):
            raise ValueError("relative source/hash binding required")
        path=base/name
        if path.is_symlink() or not path.resolve().is_relative_to(base) or not path.is_file():
            raise ValueError("unsafe/missing bound evidence")
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError("bound evidence drift: "+name)

def replay_phase(base,contract):
    # Keep the legacy auditor's relative-source contract in an owned child,
    # without changing the caller cwd or querying currently leased devices.
    return json.loads(subprocess.check_output([sys.executable,"-B",
        str(Path(base)/"audit_r15_terminal.py"),"--contract",str(contract)],
        cwd=base,text=True,timeout=600))

def validate_case(path,*,document_only=False):
    path=Path(path)
    if path.is_symlink():raise ValueError("case symlink rejected")
    c=json.loads(path.read_text());phase=check_scope(c);base=path.resolve().parent
    verify_bindings(base,c["evidence"])
    repo=base.parents[2]
    verify_bindings(repo,{".agents/skills/"+name+"/SKILL.md":{"sha256":sha}
                          for name,sha in c["skill_sources"].items()})
    summary=json.loads((base/phase["summary"]).read_text())
    contract=json.loads((base/phase["contract"]).read_text())
    expected=summary["independent_audit"]["report"]
    if (summary["raw_root"]!=phase["raw_root"] or contract["raw_root"]!=phase["raw_root"]
            or summary["independent_audit"]["exit"]!=0
            or summary["independent_audit"]["operation"]!=phase["audit"]
            or summary.get("controller_exit")!=0
            or contract.get("performance_group")!="G3" or contract.get("performance_round")!=1
            or contract.get("tp")!=4 or contract.get("physical_npus")!=[0,1,2,3]
            or expected.get("live_release_verified")is not True
            or expected.get("terminal_unit_valid")is not True
            or expected.get("timing",{}).get("requests")!=40
            or expected.get("hot",{}).get("accepted_hot_coverage")is not True
            or expected.get("hot",{}).get("denominator")!=40):
        raise ValueError("bounded phase source/denominator/mechanism/release mismatch")
    if not document_only:
        sources=contract["cache_diagnostic"]["source_sha256"]
        if "audit_r15_terminal.py"not in sources:raise ValueError("bound replay auditor required")
        verify_bindings(base,{n:{"sha256":h} for n,h in sources.items()})
        actual=replay_phase(base,base/phase["contract"])
        recorded=dict(expected);recorded.pop("live_release_verified",None)
        if actual!=recorded:raise ValueError("raw/source/physical/journal/timing replay differs")
    return {"case_document_bindings_verified":True,"mapped_skills":sorted(SKILLS),
            "evidence_files":len(c["evidence"]),"raw_phase_replay_verified":not document_only,
            "recorded_release_is_historical":True,
            "scope":"one bounded full40 evidence chain replay only; no fresh occupancy,matchedspeedup,quality,lifecycle or29functional acceptance"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--case",required=True)
    p.add_argument("--document-only",action="store_true");a=p.parse_args()
    print(json.dumps(validate_case(a.case,document_only=a.document_only)))
