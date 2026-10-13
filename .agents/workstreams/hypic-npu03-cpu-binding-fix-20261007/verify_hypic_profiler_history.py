#!/usr/bin/env python3
"""Read-only ledger replay; plugin identity is not controller byte identity."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
FILE=HERE/"HYPIC_PROFILER_HISTORY_REVIEW_20261013.json"
BASE=Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
PAIRS=((1,"prefill"),(2,"prefill"),(2,"decode"),(3,"decode"),
       (4,"decode"),(5,"decode"),(6,"decode"))

def require(value,reason):
    if not value:raise RuntimeError(reason)

def validate_manifest(m):
    require(m["schema"]=="hypic-profiler-history-review/v1","schema")
    expected=[(str(BASE/f"profiler-hypic-hotcold-20261009-r{i}"),p) for i,p in PAIRS]
    require([(a["root"],a["phase"]) for a in m["attempts"]]==expected,"attempt inventory")
    require(m["source_provenance"]["prefill_r2_executed_controller_bytes"]==
            "not-proven-in-retained-evidence","unproved controller promoted")
    require(m["source_provenance"]["contracts_record_plugin_commit_not_controller_digest"] is True,
            "plugin/controller boundary")
    require(m["quality_decision_changed"] is False and m["full_skill_promotion"] is False
            and m["new_device_work"] is False,"scope")
    require([a["outcome"] for a in m["attempts"]]==
            ["isolation-invalid","capture-valid","isolation-invalid",
             "admission-rejected","isolation-invalid","isolation-invalid","capture-valid"],
            "outcome reinterpretation")
    pre=m["attempts"][3]
    require(pre["release"] is None and pre["guard"] is None and not pre["capture_present"],
            "missing r3 receipts invented")
    return True

def replay(m):
    validate_manifest(m)
    for a in m["attempts"]:
        root=Path(a["root"]);p=root/a["phase"]
        for name,item in a["receipts"].items():
            raw=(p/name).read_bytes()
            require(len(raw)==item["size"] and hashlib.sha256(raw).hexdigest()==item["sha256"],
                    "receipt drift: "+str(p/name))
        result=json.loads((p/"result.json").read_text())
        contract=json.loads((p/"contract.json").read_text())
        require(result["valid"]==a["result_valid"] and result["errors"]==a["errors"] and
                result["release"]==a["release"] and (result["capture"] is not None)==a["capture_present"],
                "terminal interpretation drift")
        require(result["contract_sha256"]==a["receipts"]["contract.json"]["sha256"],"contract binding")
        require(contract["physical_npus"]==[0,1,2,3] and contract["source_commit"]==
                "c12060cd47e7575ead059983d7a8bb4704165c98","plugin/lane identity")
        require(not any(k in contract for k in ("controller_sha256","controller_git_blob","controller_commit")),
                "new controller authority available; re-review")
        gp=root/("hypic-only-"+a["phase"])/"lane-guard.json"
        if a["guard"] is None:
            require(not gp.exists(),"new r3 guard available; re-review")
        else:
            raw=gp.read_bytes();guard=json.loads(raw)
            require(hashlib.sha256(raw).hexdigest()==a["guard"]["sha256"],"guard hash")
            require(all(guard[k]==a["guard"][k] for k in ("samples","foreign","probe_errors")),"guard fields")
        if a["release"] is None:
            require(not (p/"release.json").exists(),"new r3 release available; re-review")
        else:
            require(all(a["release"][k] is True for k in
                        ("container_removed","owned_workers_released","port_released")),"release")
    rel=str((HERE/"hypic_profiler_capture.py").relative_to(REPO))
    for version in m["source_provenance"]["tracked_versions"]:
        rev=version["commit"]
        raw=subprocess.check_output(["git","show",rev+":"+rel],cwd=REPO)
        blob=subprocess.check_output(["git","rev-parse",rev+":"+rel],cwd=REPO,text=True).strip()
        require(blob==version["git_blob"] and hashlib.sha256(raw).hexdigest()==version["sha256"],
                "retained Git version drift")
    first=m["source_provenance"]["tracked_versions"][0]
    require(first["git_blob"]=="9f181ebb075ec458cc08e8450a0979f5c64946eb","first retained version")
    require(any("20261009-r4" in line for line in first["identity_lines"]),"r4 is not r2")
    return {"retained_phases":7,"capture_valid":2,"isolation_invalid":4,"admission_rejected":1,
            "release_receipts_proven":6,"release_receipt_unavailable":1,
            "prefill_controller_bytes_proven":False,"no_device_work":True}

if __name__=="__main__":
    print(json.dumps(replay(json.loads(FILE.read_text())),sort_keys=True))
