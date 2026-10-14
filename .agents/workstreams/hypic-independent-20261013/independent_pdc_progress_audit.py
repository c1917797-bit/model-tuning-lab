"""Independent scalar audit; physical/source/material checks remain separate."""
def audit_initial_prefix(events,request_id,*,pic_start,native_prefix=8192):
    if not request_id or type(pic_start) is not int or pic_start<native_prefix:
        raise ValueError("frozen request/PIC geometry required")
    progress=[x for x in events if x.get("event")=="native_request_progress"
              and x.get("request_id")==request_id]
    proof=[];pids=set()
    for rank in range(4):
        rows=[x for x in progress if x.get("rank")==rank]
        first=[x for x in rows if x.get("first_observed") is True]
        if len(first)!=1:raise ValueError("exact first preparation per rank required")
        x=first[0]
        for field in ("rank","computed_tokens","scheduled_tokens","step","pid"):
            if type(x.get(field)) is not int:raise ValueError("integer progress identity/count required")
        if not native_prefix<=x["computed_tokens"]<=pic_start or x["scheduled_tokens"]<=1:
            raise ValueError("initial native prefix reuse not proven")
        if x["pid"]<=0 or x["pid"] in pids:raise ValueError("four independent worker PIDs required")
        if any(y.get("step",-1)<x["step"] for y in rows):
            raise ValueError("earlier preparation contradicts first receipt")
        pids.add(x["pid"]);proof.append(x)
    if set(x.get("rank") for x in progress)-set(range(4)):
        raise ValueError("unexpected TP rank")
    if len(set(x["computed_tokens"] for x in proof))!=1:
        raise ValueError("ranks disagree on initial computed prefix")
    return {"request_id":request_id,"initial_computed_tokens":proof[0]["computed_tokens"],
            "ranks":4,"worker_pids":sorted(pids),
            "scope":"initial native runner prefix reuse only; not physical/material/performance acceptance"}
