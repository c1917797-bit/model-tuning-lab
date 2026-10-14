"""Independent all-response score replay; never overrides mechanism evidence."""
import hashlib

def audit_arm(rows,inputs,score):
    if len(inputs)!=127 or [x["index"] for x in inputs]!=list(range(127)):
        raise ValueError("full input denominator required")
    expected={(r,i) for r in range(1,4) for i in range(127)}
    keys=[(x["repetition"],x["index"]) for x in rows]
    if len(rows)!=381 or set(keys)!=expected or len(set(keys))!=381:
        raise ValueError("full unique381 response denominator required")
    ids=set();correct=0;failed=0;truncated=0
    for row in rows:
        source=inputs[row["index"]]
        if row["sample_id"]!=source["sample_id"] or row["segment_sha256"]!=source["segment"]["tokens_sha256"]:
            raise ValueError("sample/segment identity mismatch")
        if row.get("attempts")!=1 or row.get("retries")!=0:
            raise ValueError("declared retry protocol mismatch")
        if not row["ok"]:
            failed+=1
            if row.get("correct") is not False or not row.get("error"):
                raise ValueError("failure record concealed")
            continue
        rid=row.get("request_id")
        if not isinstance(rid,str) or not rid or rid in ids:raise ValueError("duplicate/missing service request identity")
        ids.add(rid)
        text=row["response_text"]
        if hashlib.sha256(text.encode()).hexdigest()!=row["response_sha256"]:
            raise ValueError("response hash drift")
        prediction,accepted=score("longbenchv2",text,source["reference"])
        if row["prediction"]!=prediction or row["correct"]!=bool(accepted):
            raise ValueError("score replay mismatch")
        finish=row["finish_reason"];count=row["completion_tokens"]
        if finish not in ("stop","length") or type(count) is not int or not 0<=count<=1024:
            raise ValueError("quality generation evidence invalid")
        if row.get("truncated")!=(finish=="length"):raise ValueError("truncation record mismatch")
        correct+=bool(accepted);truncated+=finish=="length"
    return {"requests":381,"successful":len(ids),"failed":failed,"correct":correct,
        "accuracy_all_requests_pct":100*correct/381,"truncated":truncated}

def audit_pair(baseline,candidate,inputs,score):
    a=audit_arm(baseline,inputs,score);b=audit_arm(candidate,inputs,score)
    return {"baseline":a,"candidate":b,"delta_pp":b["accuracy_all_requests_pct"]-a["accuracy_all_requests_pct"],
        "scope":"full score/response identity replay only; source/isolation/hot-path/quality decision independently required"}
