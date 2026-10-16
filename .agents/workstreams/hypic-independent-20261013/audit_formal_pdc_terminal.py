"""G4 full40 terminal entry point; G2 requires separate native-only observations."""
import hashlib,json
from pathlib import Path
from audit_r15_terminal import audit_r15
from audit_formal_full40_pdc import bind_full40_pic_starts,audit_full40_pdc

def validate_contract(c,base):
    if (c.get("performance_group")!="G4" or c.get("enable_prefix_caching")is not True
            or not c.get("cache_diagnostic") or not c.get("formal_performance")):
        raise ValueError("only explicit formal G4 treatment/PDC accepted")
    binding=c.get("pdc_observer_audit",{})
    required={"audit_formal_full40_pdc.py","audit_formal_pdc_terminal.py",
              "independent_pdc_progress_audit.py"}
    if set(binding)!=required:raise ValueError("exact prospective PDC auditor binding required")
    for name,digest in binding.items():
        if hashlib.sha256((Path(base)/name).read_bytes()).hexdigest()!=digest:
            raise ValueError("PDC auditor source drift: "+name)

def audit_pdc_terminal(contract_path,*,live_release=False):
    path=Path(contract_path);c=json.loads(path.read_text());validate_contract(c,path.parent)
    report=audit_r15(path,live_release=live_release)
    raw=Path(c["raw_root"]);unit=json.loads((raw/"performance-unit.json").read_text())
    mapping=report["request_map"];workers=report["hot"]["worker_pids"]
    spec=c["formal_token_artifact"]
    starts=bind_full40_pic_starts(spec["path"],spec["sha256"],unit["results"],mapping)
    events=[];scheduler=[]
    for prefix,target in (("compact-worker-",events),("compact-scheduler-",scheduler)):
        files=sorted((raw/"diagnostics").glob(prefix+"*.jsonl"))
        if not files:raise ValueError("actual PDC evidence files missing")
        for f in files:
            if f.is_symlink():raise ValueError("evidence symlink rejected")
            target.extend(json.loads(line) for line in f.read_text().splitlines())
    mp=path.parent/c["cache_diagnostic"]["compact_manifest"]
    report["full40_pdc"]=audit_full40_pdc(events,scheduler,mapping,workers,starts,
        manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest())
    report["pdc_audit_source_sha256"]=c["pdc_observer_audit"]
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit_pdc_terminal(a.contract,live_release=a.live_release)))
