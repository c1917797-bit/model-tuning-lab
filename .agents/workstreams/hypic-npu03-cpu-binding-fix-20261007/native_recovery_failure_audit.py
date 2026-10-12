#!/usr/bin/env python3
"""Retain failed semantic controls; distinguish deactivation from correctness."""
import argparse,json,hashlib
from pathlib import Path
import native_lifecycle as n
import native_recovery as r
import native_recovery_audit as audit
HERE=Path(__file__).resolve().parent
OUT=n.RAW/"native-recovery-20261012-disabled-failure-audit.json"
def read(p):return json.loads(Path(p).read_text())
def evaluate():
    assert n.sha(r.CONTRACT)=="10e9be3d1ed36b4c235788d2453d570b13e01ff653a6b6e583ab8d0193ffe877"
    try:audit.evaluate("disabled")
    except ValueError as exc:assert str(exc)=="canary semantic or natural finish failed",str(exc)
    else:raise AssertionError("disabled semantic failure changed")
    # Frozen evaluator validates all source/spec/request/isolation/release gates
    # before the exact semantic/natural-stop failure. No old gate is replaced.
    import hotpath_quality_full as q
    cases,evaluator=q.cases();sample=next(x for x in cases if x["index"]==59)
    summaries={}
    roots={m:n.root(m) for m in ("enabled","disabled")}
    for mode,root in roots.items():
        target=read(root/"target.json")["response"];choice=target["choices"][0]
        prediction,correct=evaluator.score_case("longbenchv2",choice["message"]["content"],sample["reference"])
        assert (prediction,correct,sample["reference"],choice["finish_reason"],target["usage"]["completion_tokens"])==("A",False,"D","length",2048)
        guard=read(root/"hypic-only/lane-guard.json")
        stop=read(root/"hypic-only/service-stop.json")
        summaries[mode]=dict(prediction=prediction,reference="D",correct=correct,
            finish_reason=choice["finish_reason"],completion_tokens=2048,
            isolation_samples=guard["samples"],
            exact_owned_release=all(stop[k] for k in ("container_removed","owned_npus_released","port_released")),
            event_count=len((root/"hypic-only/hypic-evidence.jsonl").read_text().splitlines()),
            response_text_sha256=hashlib.sha256(choice["message"]["content"].encode()).hexdigest(),
            artifact_hashes={str(p.relative_to(root)):n.sha(p) for p in root.rglob("*") if p.is_file()})
    assert summaries["disabled"]["event_count"]==0
    inspects={m:read(p/"container-inspect.json") for m,p in roots.items()}
    def normalize(value,mode):return value.replace("native-lifecycle-20261012-"+mode,"native-lifecycle-20261012-MODE")
    commands={m:normalize(i["Config"]["Cmd"][2],m) for m,i in inspects.items()}
    assert commands["enabled"]==commands["disabled"],"control command drift"
    envs={m:dict(x.split("=",1) for x in i["Config"]["Env"]) for m,i in inspects.items()}
    envs={m:{k:normalize(v,m) for k,v in e.items()} for m,e in envs.items()}
    changed={k for k in envs["enabled"].keys()|envs["disabled"].keys() if envs["enabled"].get(k)!=envs["disabled"].get(k)}
    assert changed=={"VLLM_ASCEND_HYPIC_ENABLE"},changed
    assert sorted(inspects["enabled"]["HostConfig"]["Binds"])==sorted(inspects["disabled"]["HostConfig"]["Binds"])
    assert read(roots["enabled"]/"contract.json")["fingerprint"]==read(roots["disabled"]/"contract.json")["fingerprint"]
    environments={m:read(p/"environment.json") for m,p in roots.items()}
    for key in ("os_arch","driver_version_sha256","tokenizer_and_model_config_sha256"):
        assert environments["enabled"][key]==environments["disabled"][key],"environment drift: "+key
    return dict(schema="hypic-native-recovery-failed-pair/v1",decision="FAILED_SEMANTIC_GUARD",
        original_enabled_decision_changed=False,disabled_control_source_and_activation_valid=True,
        one_switch_command_and_fingerprint_match=True,semantic_recovery_pass=False,
        controls=summaries,uninstalled_admission=False,package_promotion_ready=False,
        population_quality_or_performance_claim=False,
        inference="Both controls failed this sample at max2048; enabling HYPIC is not necessary for the observed wrong/truncated response. This neither establishes a causal root nor negates r19 population quality loss.",
        reopening="No unchanged retry. A future diagnostic requires a new prospectively justified question; original roots and gates stay frozen.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args()
    result=evaluate()
    if a.write:
        with OUT.open("x") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    else:assert read(OUT)==result,"retained paired failure audit drift"
    print(json.dumps(dict(path=str(OUT),sha256=n.sha(OUT),
        result={k:v for k,v in result.items() if k!="controls"},
        controls={m:{k:v for k,v in s.items() if k!="artifact_hashes"} for m,s in result["controls"].items()})))
