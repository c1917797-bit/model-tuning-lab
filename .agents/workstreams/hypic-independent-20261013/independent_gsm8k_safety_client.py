"""Full1319x3 native-task safety denominator; no artificial PIC warmup."""
import concurrent.futures,hashlib
from independent_quality_client import quality_payload,validate_response

def run_gsm8k_safety(rows,*,send,score,guard,record,concurrency=32):
    if len(rows)!=1319 or [x["index"] for x in rows]!=list(range(1319)):
        raise ValueError("full1319 safety denominator required")
    if len({x["sample_id"] for x in rows})!=1319:
        raise ValueError("duplicate GSM sample identity")
    if type(concurrency) is not int or not 1<=concurrency<=32:
        raise ValueError("frozen bounded safety concurrency required")
    results=[]
    for repetition in range(1,4):
        guard()
        def one(index):
            row=rows[index];item={"index":index,"repetition":repetition,
                "sample_id":row["sample_id"],"attempts":1,"retries":0}
            try:
                guard();payload=quality_payload(row);payload["stop"]=["Question"]
                response=send(payload);guard()
                request_id,text,finish,count=validate_response(response,row)
                prediction,correct=score("gsm8k",text,row["reference"])
                item.update(ok=True,request_id=request_id,response_text=text,
                    response_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    prediction=prediction,correct=bool(correct),finish_reason=finish,
                    completion_tokens=count,truncated=finish=="length")
            except Exception as exc:
                item.update(ok=False,correct=False,error={"type":type(exc).__name__,"message":str(exc)})
            return item
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures=[executor.submit(one,i) for i in range(1319)]
            for future in concurrent.futures.as_completed(futures):
                item=future.result();record(dict(item,event="gsm8k-safety-response",scored=True));results.append(item)
    results.sort(key=lambda x:(x["repetition"],x["index"]))
    return {"requests":3957,"successful":sum(x["ok"] for x in results),
        "correct":sum(x["correct"] for x in results),"retries":0,"concurrency":concurrency,
        "results":results,"scope":"native natural-task safety only;not HYPIC hot-path quality acceptance"}
