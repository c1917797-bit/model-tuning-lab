"""Bounded prepare-thread cost diagnostic; never enabled by formal defaults."""
from time import perf_counter_ns,thread_time_ns
from independent_prompt_snapshot import freeze_prompt_tokens
from independent_prefill_prompt_snapshot import freeze_prefill_prompt_tokens

def measure_prompt_snapshot(request_ids,states,computed,scheduled,*,reverse=False):
    ids=tuple(request_ids);computed=tuple(computed);scheduled=tuple(scheduled)
    if not ids or len(ids)>128 or type(reverse)is not bool:
        raise ValueError("bounded explicit snapshot probe required")
    measured={};outputs={}
    def run(name,call):
        wall=perf_counter_ns();cpu=thread_time_ns()
        outputs[name]=call()
        measured[name]={"wall_ns":perf_counter_ns()-wall,"thread_cpu_ns":thread_time_ns()-cpu}
    calls={"original":lambda:freeze_prompt_tokens(ids,states),
           "prefill_only":lambda:freeze_prefill_prompt_tokens(ids,states,
                computed_tokens=computed,scheduled_tokens=scheduled,enabled=True)}
    order=("prefill_only","original") if reverse else ("original","prefill_only")
    for name in order:run(name,calls[name])
    retained=[];omitted=[];tokens=0
    for rid,done,count in zip(ids,computed,scheduled):
        original=outputs["original"][rid];current=outputs["prefill_only"][rid]
        if original is None:
            if current is not None:raise ValueError("unsupported prompt changed")
            continue
        if count==1 and done>=len(original):
            if current is not None:raise ValueError("completed decode was not omitted")
            omitted.append(rid);tokens+=len(original)
        else:
            if current!=original:raise ValueError("required prefill snapshot changed")
            retained.append(rid)
    return outputs["prefill_only"],{"event":"prompt_snapshot_opportunity",
        "request_ids":list(ids),"computed_tokens":list(computed),"scheduled_tokens":list(scheduled),
        "omitted_decode_ids":omitted,"retained_prefill_ids":retained,
        "omitted_prompt_tokens":tokens,"measurements":measured,"order":list(order),
        "scope":"bounded same-metadata prepare-thread CPU/wall diagnostic, not formal latency"}
