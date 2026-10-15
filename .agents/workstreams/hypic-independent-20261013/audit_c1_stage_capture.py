"""Independent sealed first-divergence audit; no producer or runtime imports."""
import hashlib,json,math,re
from pathlib import Path
import numpy as np

def sampled_head_fp64_recurrence(q,k,v,log_g,beta,initial):
    """Independent direct recurrence on captured normalized one-head inputs.
    This is a mathematical reference, not expected bitwise BF16 kernel output.
    """
    arrays=[np.asarray(x,dtype=np.float64) for x in (q,k,v,log_g,beta,initial)]
    q,k,v,log_g,beta,initial=arrays
    if (q.ndim!=2 or k.shape!=q.shape or v.ndim!=2 or v.shape[0]!=q.shape[0]
            or not 1<=q.shape[0]<=32768 or not 1<=q.shape[1]<=128
            or not 1<=v.shape[1]<=128 or log_g.shape!=(len(q),)
            or beta.shape!=log_g.shape or initial.shape!=(q.shape[1],v.shape[1])
            or any(not np.isfinite(x).all() for x in arrays)):
        raise ValueError("finite bounded sampled head recurrence geometry required")
    state=initial.copy();out=[];scale=q.shape[1]**-.5
    for qi,ki,vi,gi,bi in zip(q,k,v,log_g,beta):
        state=state*np.exp(gi)
        correction=vi-ki@state
        state=state+bi*np.outer(ki,correction)
        out.append((qi@state)*scale)
    if not np.isfinite(state).all():raise ValueError("nonfinite FP64 reference")
    return np.stack(out),state

ORDER=("inputs","prefix_terminal","cached_composition","suffix_seed","final")
FIELDS={"inputs":{"q","k","v","g","beta","initial"},"prefix_terminal":{"state"},
    "cached_composition":{"transition","zero_state","state"},"suffix_seed":{"state"},
    "final":{"state","conv","output"}}

def audit_capture(root,*,expected_identity,manifest_sha256,atol=.01,rtol=.003):
    root=Path(root)
    if not root.is_dir() or root.is_symlink():raise ValueError("regular capture directory required")
    if (atol,rtol)!=(.01,.003):raise ValueError("frozen numerical tolerance required")
    mp=root/"manifest.json"
    if mp.is_symlink() or not mp.is_file() or mp.stat().st_size>1024*1024:
        raise ValueError("bounded regular manifest required")
    raw=mp.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest_sha256:raise ValueError("manifest digest")
    m=json.loads(raw)
    if (m.get("schema")!="hypic-first-divergence/v1" or m.get("identity")!=expected_identity
            or m.get("failed_request_id") not in expected_identity["requests"]
            or type(m.get("max_bytes"))is not int or not 1<=m["max_bytes"]<=64*1024*1024
            or type(m.get("max_records"))is not int or not 1<=m["max_records"]<=32
            or not 1<=len(m.get("records",[]))<=m["max_records"]):
        raise ValueError("exact identity/schema/frozen bounds required")
    known={"manifest.json"};payload=0;records={};file_total=0
    for e in m["records"]:
        key=(e.get("side"),e.get("request_id"),e.get("stage"),e.get("window"))
        if (key in records or key[0] not in ("packed","serial")
                or key[1] not in expected_identity["requests"] or key[2] not in ORDER
                or key[3] not in ("prefix","suffix","body")
                or set(e.get("tensors",{}))!=FIELDS[key[2]]
                or type(e.get("source_start"))is not int or type(e.get("source_end"))is not int
                or not 0<=e["source_start"]<e["source_end"]<=40960):
            raise ValueError("exact unique paired stage coordinates required")
        arrays={}
        for name,meta in e["tensors"].items():
            filename=meta.get("file","")
            if not re.fullmatch(r"[0-9]{2}-[a-z_]+\.npy",filename) or filename in known:
                raise ValueError("unique flat tensor path required")
            known.add(filename);p=root/filename
            shape=meta.get("shape")
            if (p.is_symlink() or not p.is_file() or not isinstance(shape,list) or len(shape)>5
                    or any(type(x)is not int or x<=0 for x in shape)
                    or meta.get("dtype")!="float32" or math.prod(shape)*4!=meta.get("nbytes")
                    or type(meta.get("file_bytes"))is not int or p.stat().st_size!=meta["file_bytes"]
                    or not meta["nbytes"]<=meta["file_bytes"]<=meta["nbytes"]+4096):
                raise ValueError("bounded exact tensor geometry required")
            payload+=meta["nbytes"];file_total+=meta["file_bytes"]
            if payload>m["max_bytes"] or file_total>m["max_bytes"]+32*12*4096:
                raise ValueError("capture byte bound")
            if hashlib.sha256(p.read_bytes()).hexdigest()!=meta.get("sha256"):
                raise ValueError("tensor digest")
            value=np.load(p,allow_pickle=False)
            if value.dtype!=np.float32 or list(value.shape)!=shape or not np.isfinite(value).all():
                raise ValueError("finite exact sampled FP32 tensor required")
            arrays[name]=value.astype(np.float64)
        records[key]=(e,arrays)
    if {p.name for p in root.iterdir()}!=known or payload!=m.get("payload_bytes"):
        raise ValueError("extra files or payload accounting mismatch")
    pairs=[]
    for key,(e,a) in records.items():
        if key[0]!="packed":continue
        other=("serial",*key[1:])
        if other not in records:raise ValueError("missing paired actual reference")
        ref,b=records[other]
        if any(e[k]!=ref[k] for k in ("source_start","source_end")):
            raise ValueError("paired source coordinate drift")
        for name in sorted(a):
            if a[name].shape!=b[name].shape:raise ValueError("paired shape drift")
            delta=np.abs(a[name]-b[name]);scaled=delta/(atol+rtol*np.abs(b[name]))
            pairs.append(dict(request_id=key[1],stage=key[2],window=key[3],tensor=name,
                max_abs=float(delta.max()),max_scaled=float(scaled.max()),
                exact_equal=bool(np.all(delta==0)),
                passed=bool(np.all(scaled<=1))))
    if len(records)!=2*sum(k[0]=="packed" for k in records):
        raise ValueError("unpaired serial record")
    coverage={rid:{p["stage"] for p in pairs if p["request_id"]==rid}
              for rid in expected_identity["requests"]}
    if any(set(ORDER)!=stages for stages in coverage.values()):
        raise ValueError("all five stages required per selected request")
    def dependency_order(p):
        if p['stage']=='inputs':return 0 if p['window']=='prefix' else 4
        return {'prefix_terminal':1,'cached_composition':2,'suffix_seed':3,'final':5}[p['stage']]
    pairs.sort(key=lambda p:(dependency_order(p),p["request_id"],p["window"],p["tensor"]))
    failures=[p for p in pairs if not p["passed"]]
    nonidentical=[p for p in pairs if not p['exact_equal']]
    return dict(sampled_pairs=len(pairs),first_observed_divergence=failures[0] if failures else None,
        first_nonidentical_sample=nonidentical[0] if nonidentical else None,
        comparisons=pairs,scope="same-coordinate selected-head samples only; not full tensors, task quality or native/PIC semantic equivalence")
