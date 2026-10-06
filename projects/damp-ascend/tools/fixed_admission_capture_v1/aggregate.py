"""Bitwise common-observer comparison. Reports only first GDN seam divergence."""
from __future__ import annotations
import argparse
from pathlib import Path
from diag_contract import (LAYERS,RANK_LIMIT,canonical_event,events,file_sha,load,require,
                           snapshot_signature,source_contract,write_new)

def raw_check(snapshot):
    ref=snapshot.get("raw") or snapshot.get("previous_after")
    require(ref is not None,"snapshot raw reference unavailable")
    path=Path(ref["path"])
    require(path.is_file() and path.stat().st_size==snapshot["num_bytes"] and
            file_sha(path)==snapshot["sha256"]==ref["sha256"],"raw snapshot/hash mismatch")

def arm(root):
    root=Path(root)
    run=load(root/"RUN.json")
    require(run["batch_size"]==1 and run["enforce_eager"] and not run["prefix_cache"] and
            not run["chunked_prefill"] and run["generation"]["max_tokens"]==33,
            "arm protocol mismatch")
    client=events(root/"client.jsonl")
    require(len(client)==1 and client[0]["output_tokens"]==33,"one complete33 output required")
    require((root/"CLIENT_COMPLETE.json").is_file(),"client completion receipt missing")
    result={}
    for rank in range(4):
        rows=events(root/("trace-rank-"+str(rank))/"events.jsonl")
        started=[x for x in rows if x["kind"]=="started"]
        bindings=[x for x in rows if x["kind"]=="bindings"]
        commits=[x for x in rows if x["kind"]=="turn_commit"]
        done=[x for x in rows if x["kind"]=="complete"]
        require(len(started)==len(bindings)==len(done)==1,"trace worker start/bind/complete missing")
        require(started[0]["rank"]==rank and started[0]["physical"]==rank+4,
                "actual rank/card identity mismatch")
        require(len(bindings[0]["layers"])==48 and
                {x["layer"] for x in bindings[0]["layers"]}==set(LAYERS),"real48 receiver bindings incomplete")
        require([x["turn"] for x in commits]==list(range(33)) and
                all(len(x["layers"])==48 and set(x["layers"])==set(LAYERS) and
                    x["native_return_preserved"] for x in commits),"native33×48 coverage incomplete")
        require(done[0]["raw_bytes"]<=RANK_LIMIT,"raw budget exceeded")
        require(not any(x["kind"] in ("native_failure","observer_failure") for x in rows),
                "arm contains retained diagnostic/native failure")
        before={(x["turn"],x["layer"]):x for x in rows if x["kind"]=="core_before"}
        after={(x["turn"],x["layer"]):x for x in rows if x["kind"]=="core_after"}
        wanted={(t,l) for t in range(33) for l in LAYERS}
        require(set(before)==set(after)==wanted and len([x for x in rows if x["kind"]=="core_before"])==1584
                and len([x for x in rows if x["kind"]=="core_after"])==1584,"exact raw coverage incomplete/duplicate")
        for key,b in before.items():
            a=after[key]
            require(b["ssm_previous_after_consistent"] and b["pointers"]==a["pointers"],
                    "state continuity/pointers failed")
            require(b["conv_previous_after_consistency_asserted"] is False,
                    "conv must not be mislabeled recurrent SSMequality")
            for name,s in b["inputs"].items():
                require(s["finite"],"nonfinite before snapshot")
                raw_check(s)
            for s in a["after"].values():
                require(s["finite"],"nonfinite after snapshot")
                raw_check(s)
        result[rank]={"started":started[0],"before":before,"after":after,
                      "commits":commits,"turns":[x for x in rows if x["kind"]=="turn_begin"]}
    return run,client[0],result

def compare(left,right):
    lrun,lclient,lr=arm(left); rrun,rclient,rr=arm(right)
    require({k:v for k,v in lrun.items() if k!="capture_enabled"} ==
            {k:v for k,v in rrun.items() if k!="capture_enabled"},"common run config differs")
    require(lclient["prompt_token_sha256"]==rclient["prompt_token_sha256"],"input fingerprint changed")
    differences=[]
    for rank in range(4):
        l,r=lr[rank],rr[rank]
        for k in ("packet","core_source","runner_source","recurrent_schema"):
            require(l["started"][k]==r["started"][k],"actual native source/schema changed: "+k)
        # Native library path/hash must be identical; inode is stable immutableimage
        # per process, while absolute virtual mapping addresses may differ.
        require({k:l["started"]["native_library"][k] for k in ("path","sha256","deleted")}==
                {k:r["started"]["native_library"][k] for k in ("path","sha256","deleted")},
                "actual mapped native binary changed")
        for t in range(33):
            require(l["commits"][t]["layers"]==r["commits"][t]["layers"],"native execution order differs")
            lp,rp=l["turns"][t]["parameters"],r["turns"][t]["parameters"]
            la=dict(lp);ra=dict(rp)
            linput=la.pop("input_ids");rinput=ra.pop("input_ids")
            lembed=la.pop("inputs_embeds");rembed=ra.pop("inputs_embeds")
            require(la==ra,"native runner admission/positions/args differ")
            require((lembed is None)==(rembed is None),"native embedding ABI changed")
            if lembed is not None and snapshot_signature(lembed)!=snapshot_signature(rembed):
                differences.append({"turn":t,"rank":rank,"layer":-1,"seam":"runner_inputs_embeds"})
            if linput is not None and rinput is not None and snapshot_signature(linput)!=snapshot_signature(rinput):
                differences.append({"turn":t,"rank":rank,"layer":-1,"seam":"runner_input_ids"})
            require((linput is None)==(rinput is None),"native input_ids admission ABI changed")
            for layer in LAYERS:
                key=(t,layer); lb,rb=l["before"][key],r["before"][key]
                require(canonical_event(lb)==canonical_event(rb),"native core args/slot/layout admission differs")
                for seam in ("mixed_qkv","b","a","ssm_before","conv_before"):
                    if snapshot_signature(lb["inputs"][seam])!=snapshot_signature(rb["inputs"][seam]):
                        differences.append({"turn":t,"rank":rank,"layer":layer,"seam":seam,
                                            "stage":"before_native_GDN"})
                for seam in ("g","beta","ssm_after","conv_after","core_output"):
                    if snapshot_signature(l["after"][key]["after"][seam])!=snapshot_signature(r["after"][key]["after"][seam]):
                        differences.append({"turn":t,"rank":rank,"layer":layer,"seam":seam,
                                            "stage":"after_native_GDN"})
    outputs_equal=lclient["output_token_ids"]==rclient["output_token_ids"]
    first_token=next((i for i,(a,b) in enumerate(zip(lclient["output_token_ids"],
              rclient["output_token_ids"])) if a!=b),None)
    differences.sort(key=lambda x:(x["turn"],x["layer"],x["rank"],x["seam"]))
    return {"schema":"damp-fixed-admission-comparison/v1",
            "status":"bitwise_pass" if not differences and outputs_equal else "bitwise_divergence",
            "left":str(left),"right":str(right),"output_ids_bitwise_equal":outputs_equal,
            "first_token_difference":first_token,"first_GDN_observed_difference":differences[0] if differences else None,
            "difference_count":len(differences),"ranks":4,"layers_per_rank":48,"native_turns":33,
            "FA_logit_full_chain_observed":False,"performance_measurement":False,
            "full_calibration_admitted":False,"source_lock_issued":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--left",required=True);p.add_argument("--right",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args();source_contract()
    result=compare(a.left,a.right);write_new(a.output,result)
    require(result["status"]=="bitwise_pass","bitwise divergence retained; do not issue SOURCE_LOCK")
if __name__=="__main__":
    main()
