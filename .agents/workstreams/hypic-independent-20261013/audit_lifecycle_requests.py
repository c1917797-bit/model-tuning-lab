"""Independent bounded lifecycle request and semantic journal audit."""
def audit_lifecycle_requests(records,journal,semantic,stage,expected_payloads):
    if stage not in ("disabled","enabled","uninstalled") or len(expected_payloads)!=3:
        raise ValueError("explicit stage and frozen three-request protocol required")
    if len(records)!=3 or any(type(r.get("index"))is not int for r in records) or [r.get("index")for r in records]!=[0,1,2]:
        raise ValueError("exact ordered lifecycle response cohort required")
    linked=[{k:v for k,v in e.items()if k!="event"}for e in journal if e.get("event")=="response"]
    if linked!=records:raise ValueError("lifecycle response journal drift")
    ids=[]
    for i,r in enumerate(records):
        payload=r.get("payload",{});expected=expected_payloads[i]
        if payload!=expected or expected.get("max_tokens")!=(1 if i==0 else 64) or expected.get("ignore_eos")is not True:
            raise ValueError("actual lifecycle payload differs from frozen input")
        response=r.get("response",{});usage=response.get("usage",{});choices=response.get("choices",[])
        if not isinstance(response.get("id"),str) or not response["id"] or len(choices)!=1 or not isinstance(choices[0].get("text"),str):
            raise ValueError("complete lifecycle completion response required")
        if type(usage.get("prompt_tokens"))is not int or usage["prompt_tokens"]!=len(expected["prompt"]) or type(usage.get("completion_tokens"))is not int or usage["completion_tokens"]!=expected["max_tokens"]:
            raise ValueError("exact bounded lifecycle token accounting required")
        ids.append(response["id"])
    if len(set(ids))!=3:raise ValueError("unique lifecycle completion IDs required")
    expected_semantic={"model":"qwen3.5","messages":[{"role":"user","content":"Calculate 2 + 2. Reply with only the integer."}],
        "temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":False}}
    if semantic.get("event")!="lifecycle-semantic" or semantic.get("stage")!=stage or semantic.get("payload")!=expected_semantic:
        raise ValueError("same frozen native semantic control required")
    if [e for e in journal if e.get("event")=="lifecycle-semantic"]!=[semantic]:
        raise ValueError("semantic durable journal mismatch")
    response=semantic.get("response",{});choices=response.get("choices",[]);usage=response.get("usage",{})
    sid=response.get("id")
    if not isinstance(sid,str) or not sid or sid in ids or len(choices)!=1 or not isinstance(choices[0].get("message",{}).get("content"),str):
        raise ValueError("distinct complete semantic response required")
    if choices[0]["message"]["content"].strip().rstrip(".")!="4" or type(usage.get("completion_tokens"))is not int or not 1<=usage["completion_tokens"]<=32:
        raise ValueError("bounded native semantic answer failed")
    return {"lifecycle_requests_verified":True,"stage":stage,"completion_ids":ids,"semantic_id":sid,
        "scope":"three frozen bounded requests plus native semantic control only; activation, numerical correctness, source, isolation, release and rollback separate"}
