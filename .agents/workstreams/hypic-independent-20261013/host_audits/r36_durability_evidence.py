"""Independent raw-record/byte-offset checks for selected-step durable fences."""
import json,re

def audit_durable_files(files,response_ids,workers,manifest,*,enabled):
    if(type(enabled)is not bool or set(workers)!=set(range(4))or len(set(workers.values()))!=4
       or type(files)is not dict or len(files)!=4):
        raise ValueError("exact four-worker durable evidence set required")
    if(not response_ids or len(set(response_ids))!=len(response_ids)
       or any(type(x)is not str or not x for x in response_ids)):
        raise ValueError("unique actual HTTP cohort required")
    models={};seals={};seen_pids=set()
    for name,data in files.items():
        match=re.fullmatch(r"compact-worker-([0-9]+)\.jsonl",name)
        if(match is None or type(data)is not bytes or not 0<len(data)<=134217728
           or not data.endswith(b"\n")):raise ValueError("bounded complete worker JSONL required")
        pid=int(match.group(1))
        if pid not in workers.values()or pid in seen_pids:raise ValueError("worker file ownership differs")
        seen_pids.add(pid);rank=next(k for k,v in workers.items()if v==pid)
        lines=data.splitlines(keepends=True);rows=[json.loads(line)for line in lines]
        offsets=[0]
        for line in lines:offsets.append(offsets[-1]+len(line))
        previous_seal=-1;file_models={};file_seals={}
        for index,event in enumerate(rows):
            if(type(event)is not dict or event.get("pid")!=pid or event.get("manifest_sha256")!=manifest):
                raise ValueError("original raw record worker/source differs")
            kind=event.get("event")
            if kind=="r35_evidence_io_budget_step":raise ValueError("timing observer must be off in all arms")
            if kind not in("compact_model_rows_completed","r36_evidence_step_durable"):continue
            step=event.get("step");ids=event.get("request_ids");key=(rank,step)
            if(type(step)is not int or step<0 or event.get("rank")!=rank
               or type(ids)is not list or not 1<=len(ids)<=64
               or any(type(x)is not str or not x for x in ids)or len(set(ids))!=len(ids)):
                raise ValueError("actual model-step/request identity required")
            if kind=="compact_model_rows_completed":
                if key in file_models:raise ValueError("duplicate actual completed model step")
                file_models[key]=(index,event);continue
            if not enabled:raise ValueError("disabled control emitted durability treatment")
            if key in file_seals or key not in file_models:raise ValueError("missing or duplicate model/fence")
            model_index,model=file_models[key]
            integer_fields=("original_start_count","original_end_count","original_start_bytes","original_end_bytes",
                "original_written_events","original_written_bytes","original_fsync_requests",
                "deferred_fsync_requests","completion_fsync_calls","receipt_fsync_calls")
            if any(type(event.get(k))is not int or event[k]<0 for k in integer_fields):
                raise ValueError("nonnegative integer durable counters required")
            start=event["original_start_count"];end=event["original_end_count"]
            if(not previous_seal<start<end==index or model_index!=index-1
               or event["original_start_bytes"]!=offsets[start]or event["original_end_bytes"]!=offsets[end]
               or event["original_written_events"]!=end-start
               or event["original_written_bytes"]!=offsets[end]-offsets[start]
               or event["original_fsync_requests"]!=end-start
               or event["deferred_fsync_requests"]!=end-start-1
               or event["completion_fsync_calls"]!=1 or event["receipt_fsync_calls"]!=1
               or event.get("completion_fsync_returned_before_receipt")is not True
               or event.get("callback_returns_after_receipt_fsync")is not True
               or ids!=model["request_ids"]):
                raise ValueError("original byte range/completion/durable fence does not reconcile")
            selected=rows[start:end]
            if(any(e.get("rank",rank)!=rank or e.get("step",step)!=step for e in selected)
               or any(e.get("event")in("r36_evidence_step_durable","r35_evidence_io_budget_step")for e in selected)
               or sum(e.get("event")=="compact_model_rows_completed"for e in selected)!=1):
                raise ValueError("selected step contains mixed or nested completion evidence")
            file_seals[key]=event;previous_seal=index
        if not file_models or(enabled and set(file_seals)!=set(file_models)):
            raise ValueError("one durable fence per actual completed model step required")
        models.update({k:e for k,(_,e)in file_models.items()});seals.update(file_seals)
    native={x for event in models.values()for x in event["request_ids"]};joined={}
    for api in response_ids:
        found=[x for x in native if x.startswith(api+"-")]
        if len(found)!=1:raise ValueError("unique actual HTTP/native durability association required")
        joined[api]=found[0]
    summaries=[]
    for rank in range(4):
        selected=[(k,e)for k,e in models.items()if k[0]==rank and set(joined.values()).intersection(e["request_ids"])]
        covered=set().union(*(set(e["request_ids"])for k,e in selected))if selected else set()
        if not set(joined.values())<=covered:raise ValueError("actual cohort four-rank durability coverage missing")
        summary={"rank":rank,"timed_associated_model_steps":len(selected)}
        if enabled:
            receipts=[seals[k]for k,e in selected]
            summary.update({"original_written_events":sum(e["original_written_events"]for e in receipts),
                "original_written_bytes":sum(e["original_written_bytes"]for e in receipts),
                "original_fsync_requests":sum(e["original_fsync_requests"]for e in receipts),
                "deferred_fsync_requests":sum(e["deferred_fsync_requests"]for e in receipts),
                "source_completion_and_receipt_fsync_calls":sum(e["completion_fsync_calls"]+e["receipt_fsync_calls"]for e in receipts)})
        summaries.append(summary)
    return {"selected_step_durability_valid":True,"enabled":enabled,"http_requests":len(response_ids),
        "actual_completed_model_steps":len(models),"durable_fences":len(seals),"ranks":summaries,
        "fsync_syscall_trace_proven":False,"speed_gain_inferred":False,
        "scope":"Source-bound successful controller plus complete raw byte/count/fence and cohort checks. Fence receipt follows completion sync and is itself synced before callback returns by verified policy. Not a syscall trace, performance result, or durability guarantee for an interrupted incomplete step."}
