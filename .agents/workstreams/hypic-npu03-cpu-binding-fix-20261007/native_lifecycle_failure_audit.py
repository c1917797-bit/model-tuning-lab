#!/usr/bin/env python3
"""Preserve an enabled lifecycle semantic failure without changing frozen gates."""
import argparse, hashlib, json
from pathlib import Path
import native_lifecycle_audit as frozen
HERE=Path(__file__).resolve().parent
RAW=Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
ROOT=RAW/"native-lifecycle-20261012-enabled"
OUT=RAW/"native-lifecycle-20261012-enabled-failure-audit.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def evaluate():
    assert sha(HERE/"native_lifecycle_contract.json")=="0f6578ca003e0e285bdf0432febc1281716056fe2544113d2649c76c7be4754c"
    assert sha(HERE/"native_lifecycle_audit.py")=="cada8bd5251a8919799f64b367d9758292d21f5ec08d4fd8a5e63a303c8ef5c0"
    try:
        frozen.evaluate("enabled")
    except ValueError as exc:
        assert str(exc)=="canary semantic or natural finish failed",str(exc)
    else:
        raise AssertionError("frozen semantic gate unexpectedly passed")
    # The frozen auditor completed identity, command, physical mapping, isolation,
    # release, activation and all request-payload checks before this exact failure.
    import hotpath_quality_full as c
    items,evaluator=c.cases();item=next(x for x in items if x["index"]==59)
    target=json.loads((ROOT/"target.json").read_text())["response"]
    choice=target["choices"][0]
    prediction,correct=evaluator.score_case("longbenchv2",choice["message"]["content"],item["reference"])
    assert (prediction,correct,item["reference"],choice["finish_reason"],target["usage"]["completion_tokens"])==("A",False,"D","length",2048)
    guard=json.loads((ROOT/"hypic-only/lane-guard.json").read_text())
    stop=json.loads((ROOT/"hypic-only/service-stop.json").read_text())
    ns=json.loads((ROOT/"hypic-only/worker-namespace-map.json").read_text())
    rows=[json.loads(x) for x in (ROOT/"hypic-only/hypic-evidence.jsonl").read_text().splitlines() if x]
    hot=[x for x in rows if x.get("event")=="worker_hot_request_verified"
         and x.get("request_id","").startswith("chatcmpl-hypic-native-lifecycle-enabled-s059-")
         and "-warm" not in x.get("request_id","")]
    assert {x["pid"] for x in hot}==set(ns["physical_npu_to_namespace_pid"].values())
    return dict(schema="hypic-native-lifecycle-failed-audit/v1",
      decision="FAILED_SEMANTIC_GUARD",controller_exit=0,requests_complete=3,
      prediction=prediction,reference=item["reference"],correct=correct,
      completion_tokens=2048,finish_reason="length",strict_target_hot_workers=4,
      skipped_prefix_tokens_by_pid={str(x["pid"]):x["skipped_prefix_tokens"] for x in hot},
      source_identity_request_payload_physical_isolation_release_valid=True,
      isolation_samples=guard["samples"],
      exact_owned_release=all(stop[k] for k in ["container_removed","owned_npus_released","port_released"]),
      source_commit="4429e35177979c874bf053ab29789e4773f39b22",
      canary_pass=False,full_quality_or_performance_claim=False,
      disabled_and_uninstalled_phases="not started; frozen progression stopped",
      root_cause="unproven; single hot response is not a paired quality or causal result",
      old_r19_verdict_changed=False,package_promotion_ready=False,
      artifact_hashes={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob("*") if p.is_file()})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args()
    result=evaluate()
    if a.write:
        with OUT.open("x") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    else:
        assert json.loads(OUT.read_text())==result,"retained failure audit drift"
    print(json.dumps(dict(path=str(OUT),sha256=sha(OUT),decision=result["decision"],
                         requests=3,hot_workers=4,isolation_samples=result["isolation_samples"],
                         exact_owned_release=result["exact_owned_release"],passed=False)))
