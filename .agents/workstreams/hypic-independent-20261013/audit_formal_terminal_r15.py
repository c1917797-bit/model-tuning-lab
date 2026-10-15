"""Independent terminal full40 transport/source/isolation audit, not quality."""
import hashlib
import json
from pathlib import Path
from independent_performance_summary import summarize_phase

def audit_unit(raw_root, contract_path):
    raw=Path(raw_root); contract= json.loads(Path(contract_path).read_text())
    if str(raw)!=contract["raw_root"]:raise ValueError("raw identity mismatch")
    result=json.loads((raw/"result.json").read_text())
    events=[json.loads(line) for line in (raw/"events.jsonl").read_text().splitlines()]
    terminals=[x for x in events if x.get("event")=="terminal"]
    if len(terminals)!=1 or terminals[0]["result"]!=result or result.get("valid") is not True:
        raise ValueError("successful exact terminal required")
    records=[x for x in events if x.get("event")=="measured-response"]
    summary=summarize_phase(records)
    unit=json.loads((raw/"performance-unit.json").read_text())
    if unit.get("valid") is not True or unit.get("requests")!=40 or unit.get("concurrency")!=16 or unit.get("retries")!=0:
        raise ValueError("frozen full40 client mismatch")
    if any(x.get("scored") is not True for x in records):raise ValueError("unscored measured record")
    if unit["results"]!=[{k:v for k,v in x.items() if k not in ("event","scored")} for x in records]:
        # Completion order differs from index order; compare complete records by index.
        a={x["index"]:{k:v for k,v in x.items() if k not in ("event","scored")} for x in records}
        b={x["index"]:x for x in unit["results"]}
        if a!=b:raise ValueError("journal/client record mismatch")
    samples=[x["snapshot"] for x in events if x.get("event")=="isolation"]
    if not samples or len(samples)!=result["isolation_samples"]:
        raise ValueError("isolation denominator mismatch")
    if any(x.get("foreign") for x in samples):raise ValueError("foreign process observed")
    release=json.loads((raw/"release.json").read_text())
    if release!=result["release"] or release.get("removed") is not True or release.get("port_free") is not True or release.get("final_physical_processes"):
        raise ValueError("release receipt incomplete")
    start=json.loads((raw/"service-start.json").read_text())
    if start["container_id"]!=release["owned_container"] or start["image"]!=contract["image"]:
        raise ValueError("owned service/image drift")
    if set(start["devices"])!={"/dev/davinci"+str(i) for i in range(4)}:
        raise ValueError("physical device declaration mismatch")
    expected=contract.get("baseline_host_source_sha256") or contract.get("cache_diagnostic",{}).get("source_sha256",{})
    if not expected:raise ValueError("complete bound source map required")
    drift=[name for name,digest in expected.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
    if drift:raise ValueError("source drift: "+repr(drift))
    if hashlib.sha256(Path("formal_r15_tp4.py").read_bytes()).hexdigest()!=contract["controller_sha256"]:
        raise ValueError("controller drift")
    if contract.get("independent_acceptance",{}).get("require_hypic_markers_absent"):
        if contract.get("cache_diagnostic") or list((raw/"diagnostics").glob("compact-*.jsonl")):
            raise ValueError("algorithm-off declaration/evidence contradicted")
        log=(raw/"service.log").read_text()
        if "compact_scheduler_installed" in log or "compact_model_rows_completed" in log:
            raise ValueError("algorithm activation marker in baseline")
    return {"terminal_unit_valid":True,"timing":summary,"isolation_samples":len(samples),
        "source_bindings":len(expected),"raw_sha256":{name:hashlib.sha256((raw/name).read_bytes()).hexdigest()
            for name in ("result.json","events.jsonl","performance-unit.json","release.json")},
        "scope":"full40 transport/timing and declared source/isolation/release receipts; actual physical release and hot/PDC/quality separate"}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);a=p.parse_args()
    c=json.loads(Path(a.contract).read_text())
    print(json.dumps(audit_unit(c["raw_root"],a.contract)))
