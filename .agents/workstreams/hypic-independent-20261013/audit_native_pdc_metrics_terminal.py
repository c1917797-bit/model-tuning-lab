"""Independent native-only/full40 aggregate PDC observation terminal audit."""
import hashlib,json
from pathlib import Path
from audit_r15_terminal import audit_r15
from native_pdc_metrics import audit_delta
from formal_pdc_metrics_tp4 import check_contract

def audit_native_pdc(contract_path,*,live_release=False):
    p=Path(contract_path);c=json.loads(p.read_text());check_contract(c)
    if c["performance_group"]=="G4":
        from audit_formal_pdc_terminal import audit_pdc_terminal
        report=audit_pdc_terminal(p,live_release=live_release)
    else:report=audit_r15(p,live_release=live_release)
    raw=Path(c["raw_root"]);f=raw/"native-pdc-observation.json"
    if f.is_symlink():raise ValueError("observer symlink rejected")
    receipt=json.loads(f.read_text());start=json.loads((raw/"service-start.json").read_text())
    if (receipt.get("schema")!="native-pdc-metrics/v1" or receipt.get("error")
            or receipt.get("container_id")!=start["container_id"]
            or receipt.get("image")!=c["image"]
            or receipt.get("contract_sha256")!=hashlib.sha256(p.read_bytes()).hexdigest()
            or receipt.get("official_logger_sha256")!=c["native_pdc_metrics"]["official_logger_sha256"]
            or receipt.get("observer_sources")!=c["native_pdc_metrics"]["source_sha256"]):
        raise ValueError("native observer source/identity/error mismatch")
    measured=audit_delta(receipt["before"],receipt["after"])
    if receipt.get("audit")!=measured:raise ValueError("independent observer recompute mismatch")
    report["native_pdc_observed"]=measured
    report["native_pdc_observation_sha256"]=hashlib.sha256(f.read_bytes()).hexdigest()
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit_native_pdc(a.contract,live_release=a.live_release)))
