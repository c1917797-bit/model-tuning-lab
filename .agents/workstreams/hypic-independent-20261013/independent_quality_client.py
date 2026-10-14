"""Full paired quality execution; no service ownership or old treatment code."""
import concurrent.futures,hashlib,json,urllib.request
from independent_quality_schedule import quality_schedule

def http_quality(port,payload,*,guard,timeout=2400):
    if type(port) is not int or not 1<=port<=65535:raise ValueError("valid loopback port required")
    guard()
    request=urllib.request.Request("http://127.0.0.1:"+str(port)+"/v1/completions",
        data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    chunks=[];size=0
    with urllib.request.urlopen(request,timeout=timeout) as response:
        while True:
            guard();chunk=response.read(65536)
            if not chunk:break
            size+=len(chunk)
            if size>8388608:raise ValueError("bounded quality response exceeded")
            chunks.append(chunk)
    guard()
    result=json.loads(b"".join(chunks))
    if not isinstance(result,dict):raise ValueError("quality response object required")
    return result

def quality_payload(row):
    ids=row["token_ids"]
    if not ids or any(type(x) is not int or x<0 for x in ids):
        raise ValueError("frozen token input required")
    return {"model":"qwen3.5","prompt":ids,"temperature":0,"seed":0,
            "max_tokens":1024,"ignore_eos":False,"stream":False}

def validate_response(response,row):
    request_id=response.get("id");choices=response.get("choices")
    if not isinstance(request_id,str) or not request_id or not isinstance(choices,list) or len(choices)!=1:
        raise ValueError("exact service identity/choice required")
    choice=choices[0];usage=response.get("usage",{})
    if usage.get("prompt_tokens")!=len(row["token_ids"]):
        raise ValueError("frozen prompt token count mismatch")
    count=usage.get("completion_tokens")
    if type(count) is not int or not 0<=count<=1024:
        raise ValueError("quality output ruler mismatch")
    if choice.get("finish_reason") not in ("stop","length") or not isinstance(choice.get("text"),str):
        raise ValueError("terminal text/end reason required")
    return request_id,choice["text"],choice["finish_reason"],count

def run_quality(rows,*,send,prepare,score,guard,record,batch_samples=10):
    schedule=quality_schedule(rows,batch_samples=batch_samples)
    results=[]
    for unit in schedule:
        guard()
        # Both arms use identical producer/request order. prepare decides only
        # whether to check HYPIC material receipts; it cannot remove samples.
        prepare(unit)
        def one(index):
            row=rows[index];item={"index":index,"repetition":unit["repetition"],
                "sample_id":row["sample_id"],"segment_sha256":row["segment"]["tokens_sha256"],
                "attempts":1,"retries":0}
            try:
                guard();response=send(quality_payload(row));guard()
                request_id,text,finish,count=validate_response(response,row)
                prediction,correct=score("longbenchv2",text,row["reference"])
                item.update(ok=True,request_id=request_id,response_text=text,
                    response_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    prediction=prediction,correct=bool(correct),finish_reason=finish,
                    completion_tokens=count,truncated=finish=="length")
            except Exception as exc:
                item.update(ok=False,correct=False,error={"type":type(exc).__name__,"message":str(exc)})
            return item
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_samples) as executor:
            futures=[executor.submit(one,i) for i in unit["sample_indexes"]]
            for future in concurrent.futures.as_completed(futures):
                item=future.result();record(item);results.append(item)
    results.sort(key=lambda x:(x["repetition"],x["index"]))
    return {"requests":381,"successful":sum(x["ok"] for x in results),
        "correct":sum(x["correct"] for x in results),"retries":0,
        "concurrency_bound":batch_samples,"results":results,
        "scope":"quality scores only; fourworker hot/isolation/source acceptance separate"}
