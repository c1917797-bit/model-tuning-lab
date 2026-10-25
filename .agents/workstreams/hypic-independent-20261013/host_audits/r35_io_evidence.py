"""Independent checks for source-bound selected-step evidence IO observations."""
def audit_io_records(events,response_ids,workers,manifest):
    models={};rows={}
    for event in events:
        kind=event.get("event")
        if kind not in("compact_model_rows_completed","r35_evidence_io_budget_step"):continue
        rank=event.get("rank");key=(rank,event.get("step"))
        if(rank not in workers or event.get("pid")!=workers[rank]
           or event.get("manifest_sha256")!=manifest or type(key[1])is not int):
            raise ValueError("IO model/worker/source identity mismatch")
        target=models if kind=="compact_model_rows_completed"else rows
        if key in target:raise ValueError("duplicate model/IO step")
        target[key]=event
    if not models or set(rows)!=set(models):raise ValueError("one budget per actual selected model step required")
    integer_fields=("original_emit_calls","original_written_events","original_written_bytes","original_filtered_calls",
        "original_fsync_calls","emit_interval_union_ns","emit_interval_sum_ns",
        "fsync_interval_union_ns","fsync_interval_sum_ns","selected_envelope_ns","observed_threads")
    core=("compact_gdn_body_composed","compact_c2_queries_completed","compact_model_rows_completed")
    for key,row in rows.items():
        model=models[key]
        if row.get("request_ids")!=model.get("request_ids")or not row["request_ids"]or len(set(row["request_ids"]))!=len(row["request_ids"]):
            raise ValueError("IO/model request set differs")
        if any(type(row.get(k))is not int or row[k]<0 for k in integer_fields):
            raise ValueError("nonnegative integer IO measurements required")
        if(not 1<=row["observed_threads"]<=32 or row["original_emit_calls"]<1
           or row["original_emit_calls"]!=row["original_written_events"]
           or row["original_filtered_calls"]!=0
           or row["original_fsync_calls"]!=row["original_written_events"]
           or not 0<=row["fsync_interval_union_ns"]<=row["emit_interval_union_ns"]<=row["selected_envelope_ns"]
           or row["fsync_interval_union_ns"]>row["fsync_interval_sum_ns"]
           or row["fsync_interval_sum_ns"]>row["emit_interval_sum_ns"]
           or row["emit_interval_union_ns"]>row["emit_interval_sum_ns"]
           or row.get("original_fsync_preserved")is not True
           or row.get("extra_budget_row_intended")!=1
           or row.get("extra_budget_row_excluded_from_observation")is not True):
            raise ValueError("original write/fsync or interval accounting differs")
        groups=row.get("groups")
        if type(groups)is not dict or not groups or len(groups)>128 or "r35_evidence_io_budget_step"in groups:
            raise ValueError("bounded nonrecursive event groups required")
        if(sum(x["calls"]for x in groups.values())!=row["original_emit_calls"]
           or sum(x["emit_ns"]for x in groups.values())!=row["emit_interval_sum_ns"]
           or sum(x["fsync_ns"]for x in groups.values())!=row["fsync_interval_sum_ns"]):
            raise ValueError("event groups do not reconcile")
        for kind in core:
            actual=sum(e.get("event")==kind and(e.get("rank"),e.get("step"))==key for e in events)
            if groups.get(kind,{}).get("calls",0)!=actual:raise ValueError("core raw-event/budget count differs")
    native={x for m in models.values()for x in m["request_ids"]}
    joined={}
    for api in response_ids:
        found=[x for x in native if isinstance(x,str)and x.startswith(api+"-")]
        if len(found)!=1:raise ValueError("unique source-owned HTTP/native IO association required")
        joined[api]=found[0]
    summaries=[]
    for rank in range(4):
        selected=[row for(rank_id,step),row in rows.items()if rank_id==rank and set(joined.values()).intersection(row["request_ids"])]
        covered=set().union(*(set(x["request_ids"])for x in selected))if selected else set()
        if not set(joined.values())<=covered:raise ValueError("actual timed IO cohort coverage missing")
        summaries.append({"rank":rank,"associated_steps":len(selected),
            "original_emit_calls":sum(x["original_emit_calls"]for x in selected),
            "original_fsync_calls":sum(x["original_fsync_calls"]for x in selected),
            "emit_step_unions_ns":sum(x["emit_interval_union_ns"]for x in selected),
            "fsync_step_unions_ns":sum(x["fsync_interval_union_ns"]for x in selected),
            "original_written_bytes":sum(x["original_written_bytes"]for x in selected),
            "extra_budget_rows":len(selected)})
    return {"actual_selected_step_io_valid":True,"all_observed_model_steps":len(rows),
        "http_requests":len(response_ids),"ranks":summaries,
        "maximum_rank_emit_step_unions_ns":max(x["emit_step_unions_ns"]for x in summaries),
        "maximum_rank_fsync_step_unions_ns":max(x["fsync_step_unions_ns"]for x in summaries),
        "whole_service_saving_inferred":False,"fsync_or_durability_treatment":False,
        "scope":"Timed-request-associated selected model steps only. Per-rank sums of step unions, not a four-rank walltime sum or guaranteed removable service cost; extra diagnostic rows and outside-context/native-progress excluded."}
