"""Independent R33 unprofiled prefix-terminal/private-state/source/release audit.
Trace-kernel/critical-path attribution remains a separately required analysis.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r33_prefix_terminal_trial as owner
from host_audits.r30b_graph_formal_audit import parse_info_graph
from audit_full40_hot_coverage import _audit_hot
native=owner.retained.native
components=owner.retained.components
ENTRY="host_audits/r33_prefix_terminal_audit.py"

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

from host_audits.r33_prefix_terminal_evidence import audit_observed,pre_timing_proof,first_shape_rows

def audit(path,*,live_release=False,definition=None):
    cp=Path(path).resolve();root=cp.parent
    if root!=Path.cwd().resolve():raise ValueError("owning workstream cwd required")
    c=native._read(cp);raw=Path(c["raw_root"])
    own=c.get("r33_host_audit",{}).get("source_sha256")
    native._sources(root,own)
    if own.get(ENTRY)!=sha(__file__):raise ValueError("exact R33 independent auditor binding required")
    native._sources(root,c["host_controller_source_sha256"])
    if c["controller_sha256"]!=owner.BASE_SHA or c["base_controller_sha256"]!=owner.BASE_SHA:
        raise ValueError("actual unchanged profile base required")
    spec=owner.SPEC
    owner.check_contract(c,source_root=root,require_new_root=False)
    prior=owner.prerequisite(c,root)
    cfg,manifest=components._manifest(c,root)
    sources=c.get("baseline_host_source_sha256")or c["cache_diagnostic"]["source_sha256"]
    native._sources(root,sources)
    terminal=native._read(raw/"result.json");release=native._read(raw/"release.json")
    start=native._read(raw/"service-start.json");launch=native._read(raw/"launch.json")
    if (terminal.get("valid")is not True or terminal.get("error")or terminal.get("guard_errors")
            or terminal.get("responses")!=16 or terminal.get("physical_devices_seen")!=[0,1,2,3]
            or release.get("removed")is not True or release.get("port_free")is not True
            or release.get("final_physical_processes")!=[]
            or release.get("owned_container")!=start.get("container_id")
            or start.get("image")!=c["image"]
            or set(start.get("devices",[]))!={"/dev/davinci"+str(i)for i in range(4)}):
        raise ValueError("terminal HTTP/ownership/continuous isolation/release incomplete")
    if (launch.get("controller_sha256")!=owner.BASE_SHA
            or launch.get("base_controller_sha256")!=owner.BASE_SHA
            or launch.get("host_controller_sha256")!=c["host_controller_sha256"]
            or launch.get("r33_trial",{}).get("host_sources")!=c["host_controller_source_sha256"]
            or launch["r33_trial"].get("diagnostic")!=spec):
        raise ValueError("actual HOST/profile/base launch identity mismatch")
    argv=launch["argv"];env=native._environment(argv)
    if ("--profiler-config"in argv
            or launch["r33_trial"].get("profiler_enabled")is not False
            or launch["r33_trial"].get("arm")!=c["r33_arm"]
            or json.loads(native._option(argv,"--compilation-config"))!=native.COMPILATION
            or env.get("VLLM_LOGGING_LEVEL")!="INFO"
            or env.get("TRITON_CACHE_DIR")!="/scratch/compiled-cache"
            or "--enforce-eager"in argv
            or "--no-enable-prefix-caching"not in argv or "--enable-prefix-caching"in argv):
        raise ValueError("actual same graph/INFO/noPDC/official profile argv required")
    unit=native._read(raw/"performance-unit.json")
    if unit.get("valid")is not True or unit.get("input_sha256")!=c["formal_token_artifact"]["sha256"]:
        raise ValueError("immutable profile input/result identity mismatch")
    ids=[]
    for key in("private_warmup_results","results"):
        rows=unit[key]
        if len(rows)!=(48 if key=="private_warmup_results"else 16)or {r["index"]for r in rows}!=set(range(16)):
            raise ValueError("exact private-shape warm48 and measured16 required")
        for r in rows:
            response=r.get("response",{})
            if (r.get("ok")is not True or response.get("usage",{}).get("prompt_tokens")!=32768
                    or response["usage"].get("completion_tokens")!=64):
                raise ValueError("successful exact32768/64 response required")
            if key=="results":ids.append(response["id"])
    journal=[json.loads(x)for x in native._read(raw/"events.jsonl",json_value=False).decode().splitlines()]
    names=[e.get("event")for e in journal]
    if (names.count("r33-private-warmup")!=48 or names.count("r33-begin")!=1
            or names.count("r33-response")!=16 or names.count("r33-end")!=1
            or max(i for i,n in enumerate(names)if n=="r33-private-warmup")>names.index("r33-begin")
            or not all(names.index("r33-begin")<i<names.index("r33-end")for i,n in enumerate(names)if n=="r33-response")):
        raise ValueError("actual same-process warm/profile lifecycle required")
    samples=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    if not samples or any(s.get("foreign")for s in samples):
        raise ValueError("continuous owned physical isolation missing")
    info=parse_info_graph(native._read(raw/"service.log",json_value=False))
    physical=owner.retained.audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    on=c["performance_group"]=="G3";events=components._events(raw,"compact-worker-")
    report={"bounded_prefix_terminal_arm_valid":True,"diagnostic_requests":16,"private_shape_warmup":48,
        "output_tokens":64,"source_bindings":len(sources),"isolation_samples":len(samples),
        "graph":info,"physical":physical,"source_prerequisite":prior,"live_release_verified":False}
    if on:
        if (env.get("INDEPENDENT_GRAPH_HYPIC")!="1"
                or env.get("INDEPENDENT_GRAPH_MANIFEST")!="/probe/"+c["successor_manifest"]
                or not env.get("PYTHONPATH","").startswith("/probe/prefix_terminal_r33:/probe:")):
            raise ValueError("actual independent graph activation required")
        hot=_audit_hot(events,ids,manifest_sha256=manifest,expected_count=16)
        if not hot["accepted_hot_coverage"]or hot["worker_pids"]!=info["workers"]:
            raise ValueError("all16actual same-stepfourworker48/16 hot coverage missing")
        hot["helper_scope_literal"]=hot.pop("scope")
        hot["scope"]="bounded16same-stepfourrank48C1/16C2; legacy helper literal says full40 but explicit denominator here is16"
        report["hot"]=hot
        clean_cfg={k:v for k,v in cfg.items()if k not in owner.EXPERIMENT_KEYS}
        report.update(components._algorithm_evidence(c,clean_cfg,report,events,manifest,True))
    elif events or (raw/"diagnostics").exists()or any(k.startswith("INDEPENDENT_")for k in env):
        raise ValueError("native control cannot import independent algorithm")
    if live_release:
        p=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        if p.returncode==0 or not any(x in p.stderr for x in("No such object","No such container")):
            raise ValueError("exact owned container absence not verified")
        with socket.socket()as s:s.bind(("0.0.0.0",c["port"]))
        current=owner.base.snapshot()
        if current["processes"]or current["foreign"]:raise ValueError("current physical0-3 not empty")
        report["live_release_verified"]=True
    proofs=[e for e in journal if e.get("event")=="r33-warm-proof"]
    if len(proofs)!=1 or names.index("r33-warm-proof")>names.index("r33-begin"):
        raise ValueError("one source-bound actual warm proof before timing required")
    proof=proofs[0]
    if unit.get("warm_proof")!={k:v for k,v in proof.items()if k not in("event","scored")}:
        raise ValueError("journal/unit warm proof differs")
    warm_events=[]
    for name,receipt in proof["worker_prefixes"].items():
        if Path(name).name!=name or not name.startswith("compact-worker-"):
            raise ValueError("owned worker prefix name required")
        data=(raw/"diagnostics"/name).read_bytes()[:receipt["bytes"]]
        if hashlib.sha256(data).hexdigest()!=receipt["sha256"]or not data.endswith(b"\n"):
            raise ValueError("original pre-timer evidence prefix changed")
        warm_events.extend(json.loads(x)for x in data.splitlines())
    warm_rows=first_shape_rows(warm_events,info["workers"],manifest)
    for rank in range(4):
        own_rows=[e for e in warm_rows if e["rank"]==rank]
        if not{8,39}<={e["length"]for e in own_rows}:raise ValueError("actual warm shapes absent")
        expected=sorted({e["shape_sha256"]for e in own_rows})
        if proof["shapes"].get(str(rank),proof["shapes"].get(rank))!=expected:
            raise ValueError("actual warm shape set differs")
    if env.get("INDEPENDENT_PREFIX_TERMINAL_ONLY")!=("1"if c["r33_arm"]=="B1"else"0"):
        raise ValueError("actual single treatment environment switch differs")
    observed=audit_observed(events,ids,info["workers"],manifest,c["r33_arm"]=="B1",proof)
    span=unit.get("diagnostic_makespan_seconds")
    if unit.get("profiler_enabled")is not False or type(span)not in(int,float)or not 0<span<1800:
        raise ValueError("positive unprofiled actual makespan required")
    report["prefix_terminal"]=observed
    report["diagnostic_makespan_seconds"]=span
    report["warm_proof"]=proof
    traces=[p for p in(raw/"profile").rglob("*")if p.is_file()]
    if traces:raise ValueError("unprofiled R33 cannot contain profiler output")
    report["raw_sha256"]={n:sha(raw/n)for n in("result.json","release.json","events.jsonl","performance-unit.json","launch.json","service-start.json","service.log")}
    report["worker_sha256"]={p.name:sha(p)for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}if on else{}
    report["scope"]="Unprofiled integrated16/c16/32768/64 prefix-terminal arm with48warm and actual original warm shape prefix. Not formal1024/fullquality/lifecycle."
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--definition",required=False)
    p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True)
    a=p.parse_args();r=audit(a.contract,live_release=a.live_release,definition=a.definition);data=(json.dumps(r,sort_keys=True)+"\n").encode()
    out=Path(a.output)
    with out.open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"bounded_prefix_terminal_arm_valid":r["bounded_prefix_terminal_arm_valid"],
        "output":str(out),"sha256":hashlib.sha256(data).hexdigest(),"diagnostic_requests":16,
        "hot_covered":len(r.get("hot",{}).get("covered",[])),"isolation_samples":r["isolation_samples"],
        "live_release_verified":r["live_release_verified"],"scope":r["scope"]}))
