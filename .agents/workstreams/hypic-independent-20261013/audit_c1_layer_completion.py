"""Independent source-bound C1 completion receipt join; no task-quality claim."""
import math
from collections import defaultdict


def audit_c1_completion(events,worker_pids,*,manifest_sha256,enabled=True,require_shadow=True):
    if set(worker_pids)!=set(range(4)) or len(set(worker_pids.values()))!=4:
        raise ValueError("four independently established worker PIDs required")
    installs=[x for x in events if x.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or {x.get("pid") for x in installs}!=set(worker_pids.values()):
        raise ValueError("four exact activations required")
    if any(x.get("manifest_sha256")!=manifest_sha256 or
           x.get("c1_layer_completion_barrier") is not enabled or
           x.get("c1_layer_shadow_validation") is not require_shadow or
           x.get("default_disabled") is not True for x in installs):
        raise ValueError("explicit source-bound completion/shadow flags required")
    kinds={"c1_layer_precommit_validated","c1_layer_completion_shadow_checked"}
    if not enabled:
        if require_shadow or any(x.get("event") in kinds for x in events):
            raise ValueError("completion treatment marker in disabled arm")
        return {"c1_completion_disabled_verified":True,"workers":worker_pids}
    public=defaultdict(set);gates={};commits=defaultdict(dict);shadows={}
    relevant=kinds|{"compact_public_state_published","compact_gdn_body_composed","mixed_native_gdn_completed"}
    for index,x in enumerate(events):
        kind=x.get("event")
        if kind not in relevant:continue
        rank=x.get("rank");layer=x.get("layer")
        if rank not in worker_pids or x.get("pid")!=worker_pids[rank] or x.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("worker or source drift")
        if not isinstance(layer,str) or not layer:raise ValueError("layer required")
        if kind=="compact_public_state_published":public[rank].add(layer);continue
        if type(x.get("step")) is not int or x["step"]<0:raise ValueError("step required")
        key=(rank,x["step"],layer)
        if kind=="c1_layer_precommit_validated":
            requests=x.get("requests",[])
            if key in gates or not requests or len(set(requests))!=len(requests) or any(not isinstance(r,str) or not r for r in requests):
                raise ValueError("duplicate or invalid precommit membership")
            if (x.get("finite") is not True or x.get("actual_slot_commit")!="not_started"
                    or type(x.get("tensors")) is not int or not 3<=x["tensors"]<=3*len(requests)):
                raise ValueError("private all-request finite gate missing")
            gates[key]=(index,x)
        elif kind=="c1_layer_completion_shadow_checked":
            sk=(rank,layer);rid=x.get("request_id")
            if sk in shadows or not require_shadow or not isinstance(rid,str) or not rid:
                raise ValueError("unexpected or duplicate layer shadow")
            metrics=x.get("metrics",[])
            if x.get("atol")!=.01 or x.get("rtol")!=.003 or x.get("passed") is not True or len(metrics)!=3 or {m.get("tensor") for m in metrics}!={"output","state","conv"}:
                raise ValueError("complete frozen shadow required")
            for m in metrics:
                if m.get("passed") is not True or any(type(m.get(k)) not in (int,float) or not math.isfinite(m[k]) or m[k]<0 for k in ("max_abs","rms","max_scaled")) or m["max_scaled"]>1:
                    raise ValueError("invalid shadow numerical residual")
            shadows[sk]=(index,key,rid)
        else:
            rid=x.get("request_id")
            if not isinstance(rid,str) or not rid or rid in commits[key] or x.get("finite") is not True:
                raise ValueError("duplicate or invalid completed request")
            commits[key][rid]=(index,x)
    if set(gates)!=set(commits):raise ValueError("precommit/completion group mismatch")
    for key,(index,gate) in gates.items():
        if set(gate["requests"])!=set(commits[key]):
            raise ValueError("precommit/completion membership mismatch")
        if any(i<=index for i,_ in commits[key].values()):
            raise ValueError("actual commit receipt before finite gate")
    for sk,(index,key,rid) in shadows.items():
        if key not in gates or rid not in commits[key] or not index<gates[key][0]:
            raise ValueError("shadow not before exact request precommit")
        receipt=commits[key][rid][1]
        if receipt["event"]!="compact_gdn_body_composed" or receipt.get("skipped_body_tokens",0)<=0:
            raise ValueError("shadow did not cover hot C1")
    for rank in range(4):
        if len(public[rank])!=48:raise ValueError("48 public C1 layers required")
        if require_shadow and {layer for r,layer in shadows if r==rank}!=public[rank]:
            raise ValueError("all48 hot C1 serialized shadows required per rank")
    return {"c1_layer_completion_verified":True,"workers":worker_pids,
            "precommit_groups":len(gates),"serialized_shadow_groups":len(shadows),
            "scope":"source-bound finite precommit/order/full-private serialized shadow receipts; transport, physical, release, performance and task quality separate"}
