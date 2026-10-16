"""Independent full127x3 cohort, scoring and producer-order audit."""
import hashlib
from independent_quality_schedule import quality_schedule

def audit_full_quality_cohort(rows,unit,journal,*,score,batch_samples=8):
    schedule=quality_schedule(rows,batch_samples=batch_samples)
    if unit.get("requests")!=381 or unit.get("successful")!=381 or unit.get("retries")!=0 or unit.get("concurrency_bound")!=batch_samples:
        raise ValueError("full381 same-ruler no-retry cohort required")
    results=unit.get("results",[])
    if len(results)!=381:raise ValueError("complete381 responses required")
    cases={};ids=set();correct=0;truncated=0
    for item in results:
        index=item.get("index");repeat=item.get("repetition")
        if type(index)is not int or index not in range(127) or type(repeat)is not int or repeat not in (1,2,3) or (repeat,index)in cases:
            raise ValueError("exact127x3 unique sample/repetition inventory required")
        row=rows[index];rid=item.get("request_id");text=item.get("response_text")
        if item.get("ok")is not True or type(item.get("attempts"))is not int or item["attempts"]!=1 or type(item.get("retries"))is not int or item["retries"]!=0:
            raise ValueError("all completed requests and actual no-retry evidence required")
        if item.get("sample_id")!=row["sample_id"] or item.get("segment_sha256")!=row["segment"]["tokens_sha256"]:
            raise ValueError("frozen sample/segment identity drift")
        if not isinstance(rid,str) or not rid or rid in ids or not isinstance(text,str) or item.get("response_sha256")!=hashlib.sha256(text.encode()).hexdigest():
            raise ValueError("unique request/exact response hash required")
        count=item.get("completion_tokens");finish=item.get("finish_reason")
        if type(count)is not int or not 0<=count<=1024 or finish not in ("stop","length") or item.get("truncated")is not (finish=="length"):
            raise ValueError("actual max1024 ending/truncation evidence required")
        prediction,expected=score("longbenchv2",text,row["reference"])
        if type(item.get("correct"))is not bool or item["correct"]!=bool(expected) or item.get("prediction")!=prediction:
            raise ValueError("independent rescoring differs from stored result")
        correct+=bool(expected);truncated+=finish=="length";ids.add(rid);cases[(repeat,index)]=item
    if set(cases)!={(r,i)for r in (1,2,3)for i in range(127)} or unit.get("correct")!=correct:
        raise ValueError("complete denominator/aggregate score mismatch")
    relevant=[x for x in journal if x.get("event")in ("quality-public-producer","quality-scored-response")]
    cursor=0;producer_ids=set();lengths={}
    for row in rows:
        segment=row["segment"];digest=segment["tokens_sha256"];length=segment["end"]-segment["start"]
        if digest in lengths and lengths[digest]!=length:raise ValueError("ambiguous public segment length")
        lengths[digest]=length
    for block in schedule:
        for digest in block["producer_digests"]:
            if cursor>=len(relevant):raise ValueError("missing unscored producer")
            e=relevant[cursor];cursor+=1
            if e.get("event")!="quality-public-producer" or e.get("scored")is not False or e.get("repetition")!=block["repetition"] or e.get("batch")!=block["batch"] or e.get("segment_sha256")!=digest:
                raise ValueError("same ordered material warmup protocol required")
            response=e.get("response",{});rid=response.get("id");usage=response.get("usage",{});choices=response.get("choices",[])
            if not isinstance(rid,str) or not rid or rid in ids or rid in producer_ids or usage.get("prompt_tokens")!=lengths[digest] or type(usage.get("completion_tokens"))is not int or not 0<=usage["completion_tokens"]<=1 or len(choices)!=1 or choices[0].get("finish_reason")not in ("stop","length"):
                raise ValueError("complete unique bounded public producer evidence required")
            producer_ids.add(rid)
        seen=set()
        for _ in block["sample_indexes"]:
            if cursor>=len(relevant):raise ValueError("missing scored response")
            e=relevant[cursor];cursor+=1;index=e.get("index")
            if e.get("event")!="quality-scored-response" or e.get("scored")is not True or e.get("repetition")!=block["repetition"] or index not in block["sample_indexes"] or index in seen:
                raise ValueError("complete scored batch before next producer required")
            if {k:v for k,v in e.items()if k not in ("event","scored")}!=cases[(block["repetition"],index)]:
                raise ValueError("raw journal/unit scoring response drift")
            seen.add(index)
    if cursor!=len(relevant):raise ValueError("extra producer/scored responses outside frozen denominator")
    return {"accepted_full_quality_cohort":True,"requests":381,"samples":127,"repetitions":3,
            "correct":correct,"accuracy":correct/381,"truncated":truncated,"natural_stop":381-truncated,
            "unscored_producers":len(producer_ids),"retries":0,
            "scope":"complete nonthinking1024 cohort and independently rescored outputs only; source/hot/physical/release/paired quality decision separate"}
