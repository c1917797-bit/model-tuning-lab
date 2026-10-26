"""Independent R39 target-warmup contrast with original bounded16 raw audit."""
import argparse,hashlib,json,os,socket,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r39_warmup_controller as owner
from host_audits.r39_warmup_evidence import audit_target_warmups
from host_audits.r38_component_evidence import audit_components
from host_audits.r36_durability_evidence import audit_durable_files
from host_audits.r30b_graph_formal_audit import parse_info_graph
from audit_full40_hot_coverage import _audit_hot
native=owner.native
components=owner.components
ENTRY="host_audits/r39_warmup_audit.py"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(path,*,live_release=False):
    cp=Path(path).resolve();root=cp.parent;c=native._read(cp);raw=Path(c["raw_root"])
    if root!=Path.cwd().resolve():raise ValueError("owning workstream cwd required")
    binding=c["r39_host_audit"]["source_sha256"];native._sources(root,binding)
    if binding.get(ENTRY)!=sha(__file__):raise ValueError("actual independent auditor source required")
    checked=owner.check_contract(c,source_root=root,require_new_root=False)
    cfg,manifest=components._manifest(c,root)
    terminal=native._read(raw/"result.json");release=native._read(raw/"release.json")
    start=native._read(raw/"service-start.json");launch=native._read(raw/"launch.json")
    if(terminal.get("valid")is not True or terminal.get("error")or terminal.get("guard_errors")
       or terminal.get("responses")!=16 or terminal.get("physical_devices_seen")!=[0,1,2,3]
       or release.get("removed")is not True or release.get("port_free")is not True
       or release.get("final_physical_processes")!=[] or release.get("owned_container")!=start.get("container_id")
       or start.get("image")!=c["image"]or set(start.get("devices",[]))!={"/dev/davinci"+str(i)for i in range(4)}):
        raise ValueError("actual HTTP terminal/ownership/release incomplete")
    receipt=launch.get("r38_observation",{})
    if(launch.get("controller_sha256")!=owner.BASE_SHA or launch.get("base_controller_sha256")!=owner.BASE_SHA
       or launch.get("host_controller_sha256")!=c["host_controller_sha256"]
       or receipt.get("protocol")!=owner.SPEC or receipt.get("formal_performance")is not False
       or receipt.get("host_sources")!=c["host_controller_source_sha256"]):
        raise ValueError("actual bounded HOST launch identity differs")
    argv=launch["argv"];env=native._environment(argv)
    expected={"INDEPENDENT_GRAPH_HYPIC":"1","INDEPENDENT_GRAPH_MANIFEST":"/probe/"+c["successor_manifest"],
        "INDEPENDENT_COMPONENT_COST_BUDGET":"1","INDEPENDENT_EVIDENCE_STEP_DURABILITY":"1",
        "INDEPENDENT_EVIDENCE_IO_BUDGET":"0","INDEPENDENT_PREFIX_TERMINAL_ONLY":"0","VLLM_LOGGING_LEVEL":"INFO",
        "TRITON_CACHE_DIR":"/scratch/compiled-cache"}
    if(any(env.get(k)!=v for k,v in expected.items())or not env.get("PYTHONPATH","").startswith("/probe/component_budget_r38:/probe:")
       or "--profiler-config"in argv or "--enforce-eager"in argv or "--no-enable-prefix-caching"not in argv
       or "--enable-prefix-caching"in argv or json.loads(native._option(argv,"--compilation-config"))!=native.COMPILATION):
        raise ValueError("actual source-bound graph/diagnostic/noPDC launch differs")
    unit=native._read(raw/"performance-unit.json");responses=native._read(raw/"responses.json")
    if(unit.get("valid")is not True or unit.get("protocol")!=owner.SPEC or unit.get("formal_performance")is not False
       or unit.get("input_sha256")!=c["formal_token_artifact"]["sha256"]or unit.get("summary")is not None
       or unit.get("retries")!=0 or unit.get("results")!=responses or len(responses)!=16
       or [r["index"]for r in responses]!=list(range(16))):
        raise ValueError("exact diagnostic16 and immutable input/result required")
    ids=[]
    for r in responses:
        m=r.get("metrics",{})
        if(r.get("ok")is not True or m.get("completion_tokens")!=1024 or m.get("usage",{}).get("prompt_tokens")!=32768
           or m.get("finish_reason")!="length"or not m.get("request_id")):
            raise ValueError("actual fixed32768/1024 transport missing")
        ids.append(m["request_id"])
    if len(set(ids))!=16:raise ValueError("actual HTTP identities not unique")
    journal=[json.loads(x)for x in native._read(raw/"events.jsonl",json_value=False).decode().splitlines()]
    names=[e.get("event")for e in journal];warm=[e for e in journal if e.get("event")=="warmup"]
    measured=[e for e in journal if e.get("event")=="r38-response"]
    if([(e["kind"],e["ordinal"])for e in warm]!=[("pic-producer",0),("pic-producer",1),("native-prefix",0),("native-prefix",1)]
       or any(e.get("scored")is not False for e in warm+measured)
       or names.count("r38-begin")!=1 or names.count("r38-end")!=1 or len(measured)!=16
       or max(i for i,n in enumerate(names)if n=="warmup")>=names.index("r38-begin")
       or not all(names.index("r38-begin")<i<names.index("r38-end")for i,n in enumerate(names)if n=="r38-response")
       or sorted([{k:v for k,v in r.items()if k not in("event","scored")}for r in measured],key=lambda r:r["index"])!=responses):
        raise ValueError("actual warm/diagnostic lifecycle or durable terminal records differ")
    samples=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    if not samples or any(s.get("foreign")for s in samples):raise ValueError("continuous owned isolation missing")
    info=parse_info_graph(native._read(raw/"service.log",json_value=False))
    physical=owner.prior.graph.evidence.audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    events=components._events(raw,"compact-worker-")
    hot=_audit_hot(events,ids,manifest_sha256=manifest,expected_count=16)
    if not hot["accepted_hot_coverage"]or hot["worker_pids"]!=info["workers"]:
        raise ValueError("all16 same-step fourworker48C1/16C2 hot coverage missing")
    hot["legacy_helper_scope"]=hot.pop("scope")
    hot["scope"]="Explicit16 actual same-step fourworker48C1/16C2; legacy helper literal does not change denominator."
    report={"valid":True,"diagnostic_requests":16,"output_tokens":1024,"source_bindings":checked["source_bindings"],
        "graph":info,"physical":physical,"hot":hot,"isolation_samples":len(samples),"prerequisite":checked["prerequisite"],
        "live_release_verified":False,"new_performance_or_quality_acceptance":False}
    report.update(components._algorithm_evidence(c,cfg,report,events,manifest,True))
    files={p.name:p.read_bytes()for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}
    report["durability"]=audit_durable_files(files,ids,info["workers"],manifest,enabled=True)
    report["components"]=audit_components(files,info["workers"],manifest)
    warm_proof=audit_target_warmups(journal,unit,c)
    expected_trial={"arm":c["r39_arm"],"target_warmup_count":c["r39_target_warmup_count"],
        "warm_descriptors":c["r39_warm_descriptors"],"common_cache_preparations":4,
        "study_source_map_sha256":c["study_source_map_sha256"],"host_sources":c["host_controller_source_sha256"],
        "algorithm_changed":False,"formal_performance":False}
    if launch.get("r39_trial")!=expected_trial:raise ValueError("actual R39 single variable source/arm receipt differs")
    report["r39_trial"]=expected_trial;report["target_warmups"]=warm_proof
    if warm_proof["warm_request_ids"]:
        warm_hot=_audit_hot(events,warm_proof["warm_request_ids"],manifest_sha256=manifest,expected_count=2)
        if not warm_hot["accepted_hot_coverage"]or warm_hot["worker_pids"]!=info["workers"]:
            raise ValueError("both full target warmups require actual fourworker48C1/16C2 hot evidence")
        warm_hot["legacy_helper_scope"]=warm_hot.pop("scope")
        warm_hot["scope"]="Exact two unscored full target warmups, not measured denominator."
        report["target_warmups"]["hot"]=warm_hot
    measured_steps=[e for e in events if e.get("event")=="r38_component_budget_step"and any(
        any(rid==http or rid.startswith(http+"-")for http in ids)for rid in e.get("request_ids",[]))]
    if not measured_steps:raise ValueError("actual measured component-step evidence absent")
    report["first_use_signal"]={"max_measured_single_C1_call_ns":max(e["groups"]["c1_packed_prepare"]["max_ns"]for e in measured_steps),
        "scope":"Observed CPU-call peak only; no compiler or removable-time cause established."}
    span=unit.get("diagnostic_makespan_seconds")
    if type(span)not in(int,float)or not 0<span<1800:raise ValueError("bounded actual observation span required")
    report["diagnostic_makespan_seconds"]=span
    report["scope"]="One R39 warmup-count arm; explicit four cache preparations and0or2 full target warmups. Same runtime/math/guards and measured16/c16/fixed1024; full three-arm cause decision, native/formal performance and quality remain separate."
    if live_release:
        p=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        if p.returncode==0 or not any(x in p.stderr for x in("No such object","No such container")):
            raise ValueError("exact owned container absence not verified")
        for port in [c["port"]]+list(range(c["hccl_ports"][0],c["hccl_ports"][1]+1)):
            with socket.socket()as s:s.bind(("0.0.0.0",port))
        current=owner.base.snapshot()
        if current["processes"]or current["foreign"]:raise ValueError("current physical0-3 not empty")
        report["live_release_verified"]=True
    report["raw_sha256"]={n:sha(raw/n)for n in("result.json","release.json","events.jsonl","performance-unit.json","responses.json","launch.json","service-start.json","service.log")}
    report["worker_sha256"]={name:hashlib.sha256(data).hexdigest()for name,data in files.items()}
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True)
    a=p.parse_args();r=audit(a.contract,live_release=a.live_release);data=(json.dumps(r,sort_keys=True)+"\n").encode()
    with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"valid":r["valid"],"output":a.output,"sha256":hashlib.sha256(data).hexdigest(),
        "live_release_verified":r["live_release_verified"],"components":r["components"],"scope":r["scope"]}))
