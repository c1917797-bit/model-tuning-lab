"""Independent R32 unprofiled diagnostic/hoist/private-shape/source/release audit.
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
from host_audits import r32_gate_cast_trial as owner
from host_audits.r30b_graph_formal_audit import parse_info_graph
from audit_full40_hot_coverage import _audit_hot
native=owner.retained.native
components=owner.retained.components
ENTRY="host_audits/r32_gate_cast_audit.py"

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit_gate_cast_evidence(events,ids,info,manifest,arm):
    observed=[e for e in events if e.get("event")=="c1_gate_cast_placement_observed"]
    shadows=[e for e in events if e.get("event")=="c1_gate_cast_first_shape_checked"]
    installs=[e for e in events if e.get("event")=="c1_gate_cast_placement_installed"]
    wanted=arm=="B1"
    workers=info["workers"];pids=set(workers.values())
    if (len(installs)!=4 or {e.get("pid")for e in installs}!=pids
            or any(e.get("hoisted")is not wanted for e in installs)):
        raise ValueError("actual four-worker gate-cast installation absent")
    if not observed or {e.get("rank")for e in observed}!=set(range(4)):
        raise ValueError("actual gate-cast dispatch observations missing")
    for e in observed:
        length=e.get("length")
        if (type(length)is not int or not 1<=length<=64 or e.get("pid")!=workers[e["rank"]]
                or e.get("hoisted")is not wanted
                or e.get("gate_conversion_dispatch_sites")!=(2 if wanted else 2*length)
                or e.get("manifest_sha256")!=manifest):
            raise ValueError("actual gate-cast source/dispatch/rank identity mismatch")
    if (not shadows or {e.get("rank")for e in shadows}!=set(range(4))
            or any(e.get("passed")is not True or e.get("full_private_output_and_state")is not True
                or not e.get("device","").startswith("npu") or e.get("hoisted")is not wanted
                or e.get("pid")!=workers[e["rank"]] or e.get("manifest_sha256")!=manifest for e in shadows)):
        raise ValueError("same actual NPU inputs private output/state equality missing")
    measured_ids=set(ids)
    timed=[e for e in observed if measured_ids.intersection(e.get("request_ids",[]))]
    if not timed or any(e.get("first_shape_already_validated")is not True for e in timed):
        raise ValueError("measured gate shapes were not validated in same-process warmup")
    return {"arm":arm,"hoisted":wanted,"observations":len(observed),
        "actual_npu_private_shape_checks":len(shadows),
        "dispatch_sites":sum(e["gate_conversion_dispatch_sites"]for e in observed),
        "scope":"Source-executed Tensor.to dispatch sites, not hardware-copy count; wave association only"}


def audit(path,*,live_release=False):
    cp=Path(path).resolve();root=cp.parent
    if root!=Path.cwd().resolve():raise ValueError("owning workstream cwd required")
    c=native._read(cp);raw=Path(c["raw_root"])
    own=c.get("r32_host_audit",{}).get("source_sha256")
    native._sources(root,own)
    if own.get(ENTRY)!=sha(__file__):raise ValueError("actual independent auditor hash required")
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
            or launch.get("r32_trial",{}).get("host_sources")!=c["host_controller_source_sha256"]
            or launch["r32_trial"].get("diagnostic")!=spec):
        raise ValueError("actual HOST/profile/base launch identity mismatch")
    argv=launch["argv"];env=native._environment(argv)
    if ("--profiler-config"in argv
            or launch["r32_trial"].get("profiler_enabled")is not False
            or launch["r32_trial"].get("arm")!=c["r32_arm"]
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
    if (names.count("r32-private-warmup")!=16 or names.count("r32-begin")!=1
            or names.count("r32-response")!=16 or names.count("r32-end")!=1
            or max(i for i,n in enumerate(names)if n=="r32-private-warmup")>names.index("r32-begin")
            or not all(names.index("r32-begin")<i<names.index("r32-end")for i,n in enumerate(names)if n=="r32-response")):
        raise ValueError("actual same-process warm/profile lifecycle required")
    samples=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    if not samples or any(s.get("foreign")for s in samples):
        raise ValueError("continuous owned physical isolation missing")
    info=parse_info_graph(native._read(raw/"service.log",json_value=False))
    physical=owner.retained.audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    on=c["performance_group"]=="G3";events=components._events(raw,"compact-worker-")
    report={"bounded_gate_cast_arm_valid":True,"diagnostic_requests":16,"private_shape_warmup":16,
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
    gate_cast=audit_gate_cast_evidence(events,ids,info,manifest,c["r32_arm"])
    span=unit.get("diagnostic_makespan_seconds")
    if unit.get("profiler_enabled")is not False or type(span)not in(int,float)or not 0<span<1800:
        raise ValueError("positive unprofiled actual makespan required")
    report["gate_cast"]=gate_cast
    report["diagnostic_makespan_seconds"]=span
    traces=[p for p in(raw/"profile").rglob("*")if p.is_file()]
    if traces:raise ValueError("unprofiled R32 cannot contain profiler output")
    report["raw_sha256"]={n:sha(raw/n)for n in("result.json","release.json","events.jsonl","performance-unit.json","launch.json","service-start.json","service.log")}
    report["worker_sha256"]={p.name:sha(p)for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}if on else{}
    report["scope"]="Unprofiled integrated16/c16/32768/64 gate-placement arm; private-shape/source/HTTP/hot/physical/release only. A/B/A decision, formal1024 repeats/fullquality/lifecycle remain separate."
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True)
    a=p.parse_args();r=audit(a.contract,live_release=a.live_release);data=(json.dumps(r,sort_keys=True)+"\n").encode()
    out=Path(a.output)
    with out.open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"bounded_gate_cast_arm_valid":r["bounded_gate_cast_arm_valid"],
        "output":str(out),"sha256":hashlib.sha256(data).hexdigest(),"diagnostic_requests":16,
        "hot_covered":len(r.get("hot",{}).get("covered",[])),"isolation_samples":r["isolation_samples"],
        "live_release_verified":r["live_release_verified"],"scope":r["scope"]}))
