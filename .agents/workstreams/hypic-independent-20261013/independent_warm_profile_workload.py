"""Same-process private-shape warmup diagnostic; not a changed algorithm or formal benchmark."""
import hashlib,json,urllib.request,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from independent_formal_warmups import build_warmups,execute_warmups

def validate_profile_spec(contract):
    spec=contract.get("profile_diagnostic")
    if not isinstance(spec,dict) or set(spec)!={"requests","output_tokens","max_iterations","delay_iterations"}:
        raise ValueError("exact diagnostic profile specification required")
    if contract.get("formal_performance") or contract.get("formal_quality") or not contract.get("formal_token_artifact"):
        raise ValueError("profiling cannot be a formal performance/quality unit")
    if any(type(x) is not int for x in spec.values()):
        raise ValueError("integer diagnostic bounds required")
    if spec["requests"]!=16 or spec["output_tokens"]!=64 or not 1<=spec["max_iterations"]<=16 or not 0<=spec["delay_iterations"]<=128:
        raise ValueError("bounded c16/64-token profile required")
    return dict(spec)

def profiler_config(spec):
    return {"profiler":"torch","torch_profiler_dir":"/scratch/profile",
        "torch_profiler_with_stack":False,"torch_profiler_with_memory":False,
        "ignore_frontend":True,"max_iterations":spec["max_iterations"],
        "delay_iterations":spec["delay_iterations"]}

def http_profile(port,action):
    if action not in ("start_profile","stop_profile"):raise ValueError("unsupported profile action")
    req=urllib.request.Request("http://127.0.0.1:"+str(port)+"/"+action,data=b"",method="POST")
    with urllib.request.urlopen(req,timeout=300) as response:
        if response.status!=200:raise RuntimeError("profile control HTTP failure")
        return {"status":response.status,"action":action}

def run_profile_workload(artifact_spec,spec,*,send,control,guard,record,require_material_ready):
    path=Path(artifact_spec["path"])
    if not path.is_absolute() or path.is_symlink() or path.stat().st_size>33554432:
        raise ValueError("bounded immutable input required")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=artifact_spec["sha256"]:
        raise ValueError("profile input drift")
    artifact=json.loads(data)
    execute_warmups(build_warmups(artifact),send=send,guard=guard,record=record,
                    require_material_ready=require_material_ready)
    cases=artifact["requests"][:spec["requests"]]
    if len(cases)!=16 or any(len(x["token_ids"])!=32768 for x in cases):
        raise ValueError("same formal c16 input required")
    def one(case):
        began=time.monotonic()
        guard()
        try:
            payload={"model":"qwen3.5","prompt":case["token_ids"],"temperature":0,"seed":0,
                     "max_tokens":spec["output_tokens"],"ignore_eos":True}
            response=send(payload)
            if response["usage"]["prompt_tokens"]!=32768 or response["usage"]["completion_tokens"]!=64:
                raise ValueError("diagnostic response token mismatch")
            return {"index":case["index"],"ok":True,"response":response,"elapsed_seconds":time.monotonic()-began}
        except Exception as exc:
            return {"index":case["index"],"ok":False,"error":{"type":type(exc).__name__,"message":str(exc)}}
    warm_results=[]
    with ThreadPoolExecutor(max_workers=16) as pool:
        for future in as_completed([pool.submit(one,x) for x in cases]):
            item=future.result();warm_results.append(item)
            record(dict(item,event="profile-private-warmup",scored=False))
            guard()
    if len(warm_results)!=16 or not all(x["ok"] for x in warm_results):
        raise RuntimeError("private-shape warmup failed; no profiler start")
    guard();started=control("start_profile")
    record({"event":"profile-start","scored":False,"response":started,"spec":spec,
            "private_shape_warmup_requests":16})
    results=[]
    try:
        with ThreadPoolExecutor(max_workers=16) as pool:
            for future in as_completed([pool.submit(one,x) for x in cases]):
                item=future.result();results.append(item)
                record(dict(item,event="profile-response",scored=False))
                guard()
    finally:
        stopped=control("stop_profile")
        record({"event":"profile-stop","scored":False,"response":stopped})
    return {"valid":len(results)==16 and all(x["ok"] for x in results),
            "results":results,"private_warmup_results":warm_results,"input_sha256":artifact_spec["sha256"],
            "scope":"same-process private-shape-warmed c16/32768/64 diagnostic; no formal performance or quality claim"}
