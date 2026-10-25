"""Independent R31 transport/mechanism/source/release audit.
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
from host_audits import r31_warm_graph_profile as owner
from host_audits.r30b_graph_formal_audit import parse_info_graph
from audit_full40_hot_coverage import _audit_hot
native=owner.retained.native
components=owner.retained.components
ENTRY="host_audits/r31_warm_profile_audit.py"

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(path,*,live_release=False):
    cp=Path(path).resolve();root=cp.parent
    if root!=Path.cwd().resolve():raise ValueError("owning workstream cwd required")
    c=native._read(cp);raw=Path(c["raw_root"])
    own=c.get("r31_host_audit",{}).get("source_sha256")
    native._sources(root,own)
    if own.get(ENTRY)!=sha(__file__):raise ValueError("actual independent auditor hash required")
    native._sources(root,c["host_controller_source_sha256"])
    if c["controller_sha256"]!=owner.BASE_SHA or c["base_controller_sha256"]!=owner.BASE_SHA:
        raise ValueError("actual unchanged profile base required")
    spec=owner.validate_profile_spec(c)
    prior=owner.profile_prerequisite(c,root)
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
            or launch.get("r31_profile",{}).get("host_sources")!=c["host_controller_source_sha256"]
            or launch["r31_profile"].get("profile")!=spec):
        raise ValueError("actual HOST/profile/base launch identity mismatch")
    argv=launch["argv"];env=native._environment(argv)
    if (json.loads(native._option(argv,"--profiler-config"))!=owner.profiler_config(spec)
            or json.loads(native._option(argv,"--compilation-config"))!=native.COMPILATION
            or env.get("VLLM_LOGGING_LEVEL")!="INFO"or "--enforce-eager"in argv
            or "--no-enable-prefix-caching"not in argv or "--enable-prefix-caching"in argv):
        raise ValueError("actual same graph/INFO/noPDC/official profile argv required")
    unit=native._read(raw/"profile-unit.json")
    if unit.get("valid")is not True or unit.get("input_sha256")!=c["formal_token_artifact"]["sha256"]:
        raise ValueError("immutable profile input/result identity mismatch")
    ids=[]
    for key in("private_warmup_results","results"):
        rows=unit[key]
        if len(rows)!=16 or {r["index"]for r in rows}!=set(range(16)):
            raise ValueError("exact private-shape warm16 and profile16 required")
        for r in rows:
            response=r.get("response",{})
            if (r.get("ok")is not True or response.get("usage",{}).get("prompt_tokens")!=32768
                    or response["usage"].get("completion_tokens")!=64):
                raise ValueError("successful exact32768/64 response required")
            if key=="results":ids.append(response["id"])
    journal=[json.loads(x)for x in native._read(raw/"events.jsonl",json_value=False).decode().splitlines()]
    names=[e.get("event")for e in journal]
    if (names.count("profile-private-warmup")!=16 or names.count("profile-start")!=1
            or names.count("profile-response")!=16 or names.count("profile-stop")!=1
            or max(i for i,n in enumerate(names)if n=="profile-private-warmup")>names.index("profile-start")
            or not all(names.index("profile-start")<i<names.index("profile-stop")for i,n in enumerate(names)if n=="profile-response")):
        raise ValueError("actual same-process warm/profile lifecycle required")
    samples=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    if not samples or any(s.get("foreign")for s in samples):
        raise ValueError("continuous owned physical isolation missing")
    info=parse_info_graph(native._read(raw/"service.log",json_value=False))
    physical=owner.retained.audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    on=c["performance_group"]=="G3";events=components._events(raw,"compact-worker-")
    report={"profile_transport_mechanism_valid":True,"profiled_requests":16,"private_shape_warmup":16,
        "output_tokens":64,"source_bindings":len(sources),"isolation_samples":len(samples),
        "graph":info,"physical":physical,"source_prerequisite":prior,"live_release_verified":False}
    if on:
        if (env.get("INDEPENDENT_GRAPH_HYPIC")!="1"
                or env.get("INDEPENDENT_GRAPH_MANIFEST")!="/probe/"+c["successor_manifest"]
                or not env.get("PYTHONPATH","").startswith("/probe/graph_candidate/bootstrap:/probe:")):
            raise ValueError("actual independent graph activation required")
        hot=_audit_hot(events,ids,manifest_sha256=manifest,expected_count=16)
        if not hot["accepted_hot_coverage"]or hot["worker_pids"]!=info["workers"]:
            raise ValueError("all16actual same-stepfourworker48/16 hot coverage missing")
        hot["helper_scope_literal"]=hot.pop("scope")
        hot["scope"]="bounded16same-stepfourrank48C1/16C2; legacy helper literal says full40 but explicit denominator here is16"
        report["hot"]=hot
        report.update(components._algorithm_evidence(c,cfg,report,events,manifest,True))
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
    traces=[p for p in(raw/"profile").rglob("*")if p.is_file()]
    if not traces or any(p.is_symlink()for p in traces):raise ValueError("regular bounded official profile output missing")
    total=sum(p.stat().st_size for p in traces)
    if total>c["profile_byte_limit"]:raise ValueError("profiler output exceeded frozen storage bound")
    report["profile_inventory"]={"files":len(traces),"bytes":total,
        "profiler_info":[{"path":str(p.relative_to(raw)),"sha256":sha(p)}for p in traces if p.name.startswith("profiler_info")],
        "trace_integrity_and_cost_attribution":"PENDING_SEPARATE_FOURWORKER_KERNEL_TIMELINE_ANALYSIS"}
    report["raw_sha256"]={n:sha(raw/n)for n in("result.json","release.json","events.jsonl","profile-unit.json","launch.json","service-start.json","service.log")}
    report["worker_sha256"]={p.name:sha(p)for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}if on else{}
    report["scope"]="bounded warmedc16/32768/64 collection/source/HTTP/hot/physical/release only. Trace completeness, costs, causal treatment, formal1024 performance/full quality/lifecycle remain separate."
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True)
    a=p.parse_args();r=audit(a.contract,live_release=a.live_release);data=(json.dumps(r,sort_keys=True)+"\n").encode()
    out=Path(a.output)
    with out.open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"profile_transport_mechanism_valid":r["profile_transport_mechanism_valid"],
        "output":str(out),"sha256":hashlib.sha256(data).hexdigest(),"profiled_requests":16,
        "hot_covered":len(r.get("hot",{}).get("covered",[])),"isolation_samples":r["isolation_samples"],
        "live_release_verified":r["live_release_verified"],"profile_inventory":r["profile_inventory"],"scope":r["scope"]}))
