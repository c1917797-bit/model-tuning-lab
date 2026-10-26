"""Independent selected-component interval/count validation; no device actions."""
import collections,json,re
GROUPS=("c1_packed_prepare","c1_prefix_alignment","mixed_native_prepare","layer_finite_validate")
def integer(x):return type(x)is int and x>=0
def audit_components(files,workers,manifest):
    if set(workers)!=set(range(4))or len(set(workers.values()))!=4 or len(files)!=4:
        raise ValueError("exact four owned worker files required")
    allsteps={};totals={g:{"calls":0,"inclusive_ns":0,"exclusive_observed_ns":0}for g in GROUPS}
    byrank={};pids=set()
    for name,data in files.items():
        match=re.fullmatch(r"compact-worker-([0-9]+)\.jsonl",name)
        if not match or not isinstance(data,bytes)or not data.endswith(b"\n")or len(data)>134217728:
            raise ValueError("bounded complete actual worker data required")
        pid=int(match.group(1))
        if pid not in workers.values()or pid in pids:raise ValueError("owned worker file identity differs")
        pids.add(pid);rank=next(k for k,v in workers.items()if v==pid)
        rows=[json.loads(x)for x in data.splitlines()];models={};receipts={};counts=collections.Counter()
        keyed=collections.defaultdict(collections.Counter)
        for i,e in enumerate(rows):
            if e.get("pid")!=pid or e.get("manifest_sha256")!=manifest:raise ValueError("raw worker source differs")
            kind=e.get("event");counts[kind]+=1
            if type(e.get("step"))is int and e.get("rank")==rank:keyed[e["step"]][kind]+=1
            if kind=="compact_model_rows_completed":
                if e["step"]in models:raise ValueError("duplicate completed model step")
                models[e["step"]]=e
            if kind!="r38_component_budget_step":continue
            step=e.get("step")
            if not integer(step)or e.get("rank")!=rank or step in receipts or i<2 or i+1>=len(rows):
                raise ValueError("component step/order/identity differs")
            model,fence,flush=rows[i-2],rows[i-1],rows[i+1]
            if(model.get("event")!="compact_model_rows_completed"or fence.get("event")!="r36_evidence_step_durable"
               or flush.get("event")!="r38_component_budget_flush"):
                raise ValueError("model/durable/budget/flush adjacency required")
            ids=e.get("request_ids")
            if(not isinstance(ids,list)or not ids or len(ids)!=len(set(ids))
               or any(x.get("rank")!=rank or x.get("step")!=step or x.get("request_ids")!=ids for x in(model,fence,flush))):
                raise ValueError("original model request identity differs")
            if(e.get("original_function_arguments_results_exceptions_unchanged")is not True
               or e.get("original_evidence_unfiltered")is not True or e.get("r36_completion_fence_precedes_receipts")is not True
               or flush.get("extra_receipt_records")!=2 or flush.get("flush_record_own_write_time_unmeasured")is not True):
                raise ValueError("original evidence or probe-overhead declaration missing")
            gs=e.get("groups")
            if type(gs)is not dict or set(gs)!=set(GROUPS):raise ValueError("complete four component groups required")
            for g,r in gs.items():
                if(set(r)!={"calls","inclusive_ns","exclusive_observed_ns","max_ns","failures"}
                   or any(not integer(x)for x in r.values())or r["failures"]
                   or not r["exclusive_observed_ns"]<=r["inclusive_ns"]
                   or not r["max_ns"]<=r["inclusive_ns"]
                   or(not r["calls"]and any(r.values()))):
                    raise ValueError("complete successful bounded component counters required")
                for k in totals[g]:totals[g][k]+=r[k]
            if(not integer(e.get("root_interval_union_ns"))or not integer(e.get("probe_metadata_ns"))
               or not integer(e.get("calls"))or not 0<e["calls"]<=100000
               or e["calls"]!=sum(r["calls"]for r in gs.values())
               or e["root_interval_union_ns"]!=sum(r["exclusive_observed_ns"]for r in gs.values())
               or not integer(flush.get("first_receipt_emit_ns"))):
                raise ValueError("nested exclusive/root union/call closure differs")
            receipts[step]=e
            key=(step,tuple(ids))
            allsteps.setdefault(key,{})[rank]={"union_ns":e["root_interval_union_ns"],
                "probe_metadata_ns":e["probe_metadata_ns"],"first_receipt_emit_ns":flush["first_receipt_emit_ns"],
                "groups":gs}
        if set(receipts)!=set(models)or not receipts or len(receipts)>256 or counts["r38_component_budget_flush"]!=len(receipts):
            raise ValueError("every actual selected completed step needs one bounded receipt pair")
        for step,e in receipts.items():
            gs=e["groups"];n=keyed[step]
            if(gs["c1_packed_prepare"]["calls"]!=n["c1_layer_precommit_validated"]
               or gs["mixed_native_prepare"]["calls"]!=n["c1_layer_precommit_validated"]
               or gs["layer_finite_validate"]["calls"]!=n["c1_layer_precommit_validated"]+n["c2_layer_precommit_validated"]
               or gs["c1_prefix_alignment"]["calls"]>gs["c1_packed_prepare"]["calls"]
               or(n["c1_prefix_terminal_route"]and not gs["c1_prefix_alignment"]["calls"])):
                raise ValueError("actual component calls differ from original layer/route receipts")
        byrank[str(rank)]={"pid":pid,"steps":len(receipts),"calls":sum(e["calls"]for e in receipts.values()),
            "root_union_ns":sum(e["root_interval_union_ns"]for e in receipts.values())}
    if any(set(v)!=set(range(4))for v in allsteps.values()):
        raise ValueError("actual step/request identity lacks four-rank receipts")
    maxrank_union=sum(max(v["union_ns"]for v in values.values())for values in allsteps.values())
    group_budget={g:{"per_step_maxrank_exclusive_ns":sum(max(v["groups"][g]["exclusive_observed_ns"]for v in values.values())for values in allsteps.values()),
                     "per_step_maxrank_inclusive_ns":sum(max(v["groups"][g]["inclusive_ns"]for v in values.values())for values in allsteps.values())}for g in GROUPS}
    return {"completed_fourrank_steps":len(allsteps),"per_rank":byrank,"raw_group_totals_not_service_time":totals,
        "per_step_maxrank_root_union_ns":maxrank_union,"group_conditional_budgets":group_budget,
        "per_step_maxrank_probe_metadata_ns":sum(max(v["probe_metadata_ns"]for v in values.values())for values in allsteps.values()),
        "per_step_maxrank_first_receipt_emit_ns":sum(max(v["first_receipt_emit_ns"]for v in values.values())for values in allsteps.values()),
        "extra_receipt_records":len(allsteps)*4*2,"second_receipt_write_unmeasured":True,
        "scope":"Observed selected original CPU calls include queued NPU waits and nested probe effects. Inclusive groups overlap; do not add group budgets or four ranks as service savings. No causal/removable/speed claim."}
