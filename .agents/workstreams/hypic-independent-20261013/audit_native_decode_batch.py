"""Independent R7 receipt audit; does not substitute for transport or quality."""
import math
from collections import defaultdict

def audit_native_decode_batch(events,worker_pids,*,manifest_sha256):
    if set(worker_pids)!=set(range(4)) or len(set(worker_pids.values()))!=4:
        raise ValueError("four independently audited hot-worker PIDs required")
    public=defaultdict(set);native={};groups={};shadows={}
    installed=[x for x in events if x.get("event")=="compact_hypic_hooks_installed"]
    if len(installed)!=4 or {x.get("pid") for x in installed}!=set(worker_pids.values()):
        raise ValueError("exact four activations required")
    if any(x.get("manifest_sha256")!=manifest_sha256 or x.get("native_decode_batch") is not True or x.get("default_disabled") is not True for x in installed):
        raise ValueError("explicit source-bound default-off native batch activation missing")
    relevant={"compact_public_state_published","mixed_native_gdn_completed",
              "native_decode_batch_completed","native_decode_batch_shadow_checked"}
    for x in events:
        kind=x.get("event")
        if kind not in relevant:continue
        rank=x.get("rank")
        if rank not in worker_pids or x.get("pid")!=worker_pids[rank] or x.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("native batch worker/source drift")
        layer=x.get("layer")
        if not isinstance(layer,str) or not layer:raise ValueError("missing layer")
        if kind=="compact_public_state_published":public[rank].add(layer);continue
        if type(x.get("step")) is not int or x["step"]<0:raise ValueError("missing step")
        key=(rank,x["step"],layer)
        if kind=="mixed_native_gdn_completed":
            rid=x.get("request_id");nk=key+(rid,)
            if nk in native:raise ValueError("duplicate native receipt")
            native[nk]=x;continue
        requests=x.get("requests",[]);n=x.get("rows")
        if type(n) is not int or n<1 or len(requests)!=n or len(set(requests))!=n or any(not isinstance(r,str) or not r for r in requests):
            raise ValueError("invalid native batch membership")
        if kind=="native_decode_batch_completed":
            if key in groups:raise ValueError("duplicate native batch")
            slots=x.get("slots",[])
            if len(slots)!=n or len(set(slots))!=n or any(type(s) is not int or s<0 for s in slots):
                raise ValueError("duplicate or invalid private slots")
            if x.get("private_buffers") is not True or x.get("actual_slot_commit")!="deferred":
                raise ValueError("private deferred commit missing")
            groups[key]=x
        else:
            if key in shadows:raise ValueError("duplicate native shadow")
            if x.get("atol")!=.01 or x.get("rtol")!=.003 or x.get("passed") is not True:
                raise ValueError("shadow tolerance/pass drift")
            metrics=x.get("metrics",[])
            if len(metrics)!=n*3 or {(m.get("request_id"),m.get("tensor")) for m in metrics}!={(r,t) for r in requests for t in ("output","state","conv")}:
                raise ValueError("full per-request output/state/conv metrics required")
            if any(m.get("passed") is not True or any(type(m.get(k)) not in (int,float) or not math.isfinite(m[k]) or m[k]<0 for k in ("max_abs","rms","max_scaled")) or m["max_scaled"]>1 for m in metrics):
                raise ValueError("invalid numerical shadow residual")
            shadows[key]=x
    multi=defaultdict(set);calls=0;rows=0
    for key,g in groups.items():
        rank,step,layer=key
        for rid,slot in zip(g["requests"],g["slots"]):
            x=native.get(key+(rid,))
            if x is None or x.get("slot")!=slot or x.get("retained_rows")!=1 or x.get("skipped_body_tokens")!=0 or x.get("finite") is not True:
                raise ValueError("native batch completion/actual slot commit mismatch")
        calls+=1;rows+=g["rows"]
    for key,s in shadows.items():
        g=groups.get(key)
        if g is None or g["requests"]!=s["requests"] or g["rows"]!=s["rows"]:
            raise ValueError("shadow without exact completed batch")
        if s["rows"]>1:multi[key[0]].add(key[2])
    for rank in range(4):
        if len(public[rank])!=48 or multi[rank]!=public[rank]:
            raise ValueError("all48 linear layers require real multirow shadow on every rank")
    return {"native_decode_batch_verified":True,"workers":worker_pids,
            "multirow_shadow_layers":{r:len(xs) for r,xs in multi.items()},
            "batch_calls":calls,"native_rows":rows,
            "scope":"source-bound runtime numerical-control and deferred-commit receipts; no independent tensor dump, whole-model quality, transport, physical or performance claim"}
