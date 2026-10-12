#!/usr/bin/env python3
"""Additional provenance audit; original semantic/control auditor is unchanged."""
import argparse,json
from pathlib import Path
import native_lifecycle as native
import native_lifecycle_audit as frozen
import native_recovery as recovery
def evaluate(mode):
    manifest,prior=recovery.identity();recovery.admit(mode,prior)
    root=native.root(mode)
    receipt=json.loads((root/"recovery-admission.json").read_text())
    if not (receipt["manifest"]==manifest and receipt["manifest_sha256"]==native.sha(recovery.CONTRACT)
        and receipt["mode"]==mode and receipt["original_enabled_decision"]=="FAILED_SEMANTIC_GUARD"
        and receipt["recovery_only"] is True and receipt["original_progression_resumed"] is False
        and receipt["quality_or_performance_claim"] is False):
        raise ValueError("recovery admission changed")
    result=frozen.evaluate(mode)
    result.update(recovery_only=True,enabled_canary_pass=False,package_promotion_ready=False,
                  original_progression_resumed=False,r19_verdict_changed=False)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=recovery.MODES,required=True)
    p.add_argument("--write",action="store_true");a=p.parse_args();result=evaluate(a.mode)
    out=native.RAW/("native-recovery-20261012-"+a.mode+"-audit.json")
    if a.write:
        with out.open("x") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    else:
        assert json.loads(out.read_text())==result,"recovery audit drift"
    print(json.dumps(dict(path=str(out),sha256=native.sha(out),
        result={k:v for k,v in result.items() if k!="artifact_hashes"})))
