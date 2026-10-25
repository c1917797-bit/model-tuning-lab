"""Independent R33 prefix terminal evidence and pre-timing shape-prefix proof."""
import hashlib,json,re
from pathlib import Path
SHA=re.compile(r"^[0-9a-f]{64}$")
def first_shape_rows(events,workers,manifest):
    rows=[e for e in events if e.get("event")=="r33_prefix_terminal_first_shape_verified"]
    for e in rows:
        rank=e.get("rank");shape=e.get("shapes")
        if(rank not in workers or e.get("pid")!=workers[rank]
           or e.get("manifest_sha256")!=manifest or e.get("passed")is not True
           or e.get("full_terminal_state")is not True
           or not e.get("device","").startswith("npu")or type(shape)is not list
           or hashlib.sha256(json.dumps(shape,separators=(",",":")).encode()).hexdigest()!=e.get("shape_sha256")):
            raise ValueError("actual source-bound private NPU shape proof missing")
    return rows
def pre_timing_proof(raw,workers,manifest):
    raw=Path(raw);events=[];prefixes={}
    files=sorted((raw/"diagnostics").glob("compact-worker-*.jsonl"))
    if len(files)!=4:raise ValueError("four actual worker evidence streams required")
    for p in files:
        data=p.read_bytes();end=data.rfind(b"\n")+1
        if end<=0:raise ValueError("complete worker evidence prefix required")
        data=data[:end];prefixes[p.name]={"bytes":end,"sha256":hashlib.sha256(data).hexdigest()}
        events.extend(json.loads(x)for x in data.splitlines())
    rows=first_shape_rows(events,workers,manifest);sets={r:set()for r in range(4)}
    for rank in sets:
        own=[e for e in rows if e["rank"]==rank]
        if not {8,39}<={e["length"]for e in own}:
            raise ValueError("common warmup lacks actual length8/39 proof before timing")
        sets[rank]={e["shape_sha256"]for e in own}
    return {"actual_shape_warmup_verified":True,"expected_lengths":[8,39],
        "workers":workers,"shapes":{r:sorted(s)for r,s in sets.items()},
        "worker_prefixes":prefixes,"manifest_sha256":manifest}
def audit_observed(events,ids,workers,manifest,terminal_only,proof):
    installs=[e for e in events if e.get("event")=="r33_prefix_terminal_installed"]
    if(len(installs)!=4 or{e.get("pid")for e in installs}!=set(workers.values())
       or any(e.get("terminal_only")is not terminal_only or e.get("prefix_only")is not True
              or e.get("suffix_unchanged")is not True or e.get("state_math_changed")is not False for e in installs)):
        raise ValueError("actual fourworker prefix-only installation required")
    rows=first_shape_rows(events,workers,manifest)
    if {e["rank"]for e in rows}!=set(range(4)):raise ValueError("fourrank actual private state proof required")
    native={e.get("request_id")for e in events if e.get("event")=="compact_gdn_body_composed"}
    joined={}
    for api in ids:
        found=[x for x in native if isinstance(x,str)and x.startswith(api+"-")]
        if len(found)!=1:raise ValueError("unique source-owned HTTP/native ID join required")
        joined[api]=found[0]
    observed=[e for e in events if e.get("event")=="r33_prefix_terminal_observed"]
    for e in observed:
        length=e.get("length");rank=e.get("rank")
        if(type(length)is not int or not 1<=length<=64 or e.get("phase")!="prefix"
            or rank not in workers or e.get("pid")!=workers[rank]
            or e.get("manifest_sha256")!=manifest or e.get("terminal_only")is not terminal_only
            or e.get("output_matmul_dispatch_sites_skipped")!=(length if terminal_only else 0)
            or not SHA.fullmatch(e.get("shape_sha256",""))):
            raise ValueError("prefix-only dispatch/source/rank evidence mismatch")
    timed=[e for e in observed if set(joined.values()).intersection(e.get("request_ids",[]))]
    if not timed or any(e.get("first_shape_already_validated")is not True
        or e["shape_sha256"]not in proof["shapes"].get(str(e["rank"]),proof["shapes"].get(e["rank"],[]))for e in timed):
        raise ValueError("timed prefix shape not proven in original warm prefix")
    return {"terminal_only":terminal_only,"observations":len(observed),
        "timed_wave_observations":len(timed),"actual_private_npu_state_checks":len(rows),
        "source_output_matmul_sites_skipped":sum(e["output_matmul_dispatch_sites_skipped"]for e in observed),
        "scope":"source executed output sites and wave association, not hardware kernel count or individual exposure"}
