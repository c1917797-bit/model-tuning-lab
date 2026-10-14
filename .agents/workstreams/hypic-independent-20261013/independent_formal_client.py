"""Full-denominator matched-performance client; caller owns service and guard."""
import concurrent.futures
import json
import time
import urllib.request
from independent_stream_metrics import measure_stream

def completion_payload(case):
    if len(case["token_ids"])!=32768:
        raise ValueError("formal32768 input required")
    return {"model":"qwen3.5","prompt":case["token_ids"],
            "temperature":0,"seed":0,"max_tokens":1024,"ignore_eos":True,
            "stream":True,"stream_options":{"include_usage":True}}

def http_measure(port,payload,*,guard,timeout=1800):
    if type(port) is not int or not 1<=port<=65535:raise ValueError("invalid port")
    guard()
    req=urllib.request.Request("http://127.0.0.1:"+str(port)+"/v1/completions",
        data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    started=time.monotonic()
    with urllib.request.urlopen(req,timeout=timeout) as response:
        def guarded_lines():
            for line in response:
                guard();yield line
        result=measure_stream(guarded_lines(),started=started,clock=time.monotonic)
    guard()
    if not isinstance(result["request_id"],str) or not result["request_id"]:
        raise ValueError("missing service request identity")
    if result["completion_tokens"]!=1024 or result["usage"].get("prompt_tokens")!=32768:
        raise ValueError("formal input/output token count mismatch")
    if result["finish_reason"]!="length":raise ValueError("fixed output boundary missing")
    return result

def run_full40(cases,*,send,guard,record):
    """No automatic retry, no hidden drops; every index gets a terminal record.

    The supplied record callback must durably journal on the controller thread.
    Service admission/isolation and warmups are separate caller responsibilities.
    """
    cases=tuple(cases)
    if len(cases)!=40 or tuple(c["index"] for c in cases)!=tuple(range(40)):
        raise ValueError("exact ordered full40 denominator required")
    payloads=[completion_payload(c) for c in cases]
    guard()
    def one(index):
        try:
            guard()
            metrics=send(payloads[index])
            guard()
            return {"index":index,"ok":True,"metrics":metrics}
        except Exception as exc:
            return {"index":index,"ok":False,
                    "error":{"type":type(exc).__name__,"message":str(exc)}}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures={executor.submit(one,i):i for i in range(40)}
        for future in concurrent.futures.as_completed(futures):
            item=future.result();record(item);results.append(item)
    results.sort(key=lambda x:x["index"])
    assert len(results)==40
    return {"valid":all(x["ok"] for x in results),"requests":40,
            "concurrency":16,"retries":0,"results":results}
