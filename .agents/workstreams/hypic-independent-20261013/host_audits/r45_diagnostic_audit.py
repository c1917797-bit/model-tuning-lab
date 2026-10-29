"""Independent R45 observational full40/warm2/math/source/release and compiler evidence audit."""
import argparse,hashlib,json,os,socket,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r45_diagnostic_policy as policy
from host_audits import r45_compilation_evidence as compilation
from host_audits import r30b_graph_formal_audit as retained
from host_audits.r36_durability_evidence import audit_durable_files
from host_audits.r40_formal_warm_evidence import audit_warmups
from host_audits.r45_diagnostic_controller import identity
from audit_full40_hot_coverage import _audit_hot
def audit_clock(samples,workers,proof):
    data=policy.clock_proof(proof);namespace=data["host_time_namespace"];seen=set()
    for sample in samples:
        clock=sample.get("r45_clock",{})
        if clock.get("host_time_namespace")!=namespace or clock.get("host_clock")!=data["host_clock"]:
            raise ValueError("actual source CLOCK_MONOTONIC namespace/implementation drift")
        observed=clock.get("process_time_namespaces")
        if type(observed)is not dict:raise ValueError("actual physical process time namespaces absent")
        for row in sample.get("owners",[]):
            nspid=row.get("nspid")
            if row.get("owned")is not True or not nspid or nspid[-1]not in workers.values():
                continue
            pid=row["pid"]
            if observed.get(str(pid))!=namespace:raise ValueError("actual worker time namespace not proven")
            seen.add(nspid[-1])
    if seen!=set(workers.values()):raise ValueError("four actual source/physical worker clock bindings required")
    return {"clock_binding_valid":True,"host_time_namespace":namespace,"worker_inner_pids":sorted(seen),
        "source_proof":proof,"request_clock_scope":"Original float monotonic timestamps are outward-rounded by one ULP, not claimed exact ns.",
        "scope":"Same Linux CLOCK_MONOTONIC implementation and live host/physical-worker time namespace; no cross-rank duration sum."}

def audit(path,*,live_release=False):
    cp=Path(path).resolve();root=cp.parent
    if Path.cwd().resolve()!=root:raise ValueError("owning formal workstream cwd required")
    c=json.loads(cp.read_bytes());checked=policy.check(c,root=root,require_new_root=False)
    report=retained.audit_r18_base(cp,live_release=live_release)
    raw=Path(c["raw_root"]);launch=json.loads((raw/"launch.json").read_bytes())
    journal=[json.loads(l)for l in(raw/"events.jsonl").read_text().splitlines()]
    unit=json.loads((raw/"performance-unit.json").read_bytes())
    warm_proof=audit_warmups(journal,unit,c);report["target_warmups"]=warm_proof
    argv=launch["argv"];env=retained.native._environment(argv);on=checked["policy"]["algorithm_on"]
    if(launch.get("controller_sha256")!=policy.BASE_SHA or launch.get("base_controller_sha256")!=policy.BASE_SHA
       or launch.get("host_controller_sha256")!=c["host_controller_sha256"]
       or any(launch.get("graph_runtime",{}).get(k)!=v for k,v in c["graph_runtime"].items())
       or json.loads(retained.native._option(argv,"--compilation-config"))!=retained.native.COMPILATION
       or retained.native._option(argv,"--tensor-parallel-size")!="4"
       or retained.native._option(argv,"--data-parallel-size")!="1"
       or retained.native._option(argv,"--max-model-len")!="40960"
       or retained.native._option(argv,"--max-num-batched-tokens")!="40960"
       or retained.native._option(argv,"--max-num-seqs")!="32"
       or "--enforce-eager"in argv or "--no-enable-prefix-caching"not in argv
       or "--enable-prefix-caching"in argv or "--profiler-config"in argv
       or env.get("VLLM_LOGGING_LEVEL")!="INFO"):
        raise ValueError("actual formal owner/profile/INFO/native launch mismatch")
    expected=identity(c)
    if launch.get("r45_launch_identity")!=expected:raise ValueError("actual formal workload/delivery receipt differs")
    cfg,manifest=retained.components._manifest(c,root)
    events=retained.components._events(raw,"compact-worker-")
    if on:
        wanted={"INDEPENDENT_COMPILATION_BUDGET":"1","INDEPENDENT_GRAPH_HYPIC":"1","INDEPENDENT_GRAPH_MANIFEST":"/probe/"+c["successor_manifest"],
                "INDEPENDENT_GRAPH_RAW":"/scratch/diagnostics","INDEPENDENT_EVIDENCE_STEP_DURABILITY":"1",
                "INDEPENDENT_EVIDENCE_IO_BUDGET":"0","INDEPENDENT_PREFIX_TERMINAL_ONLY":"0",
                "INDEPENDENT_COMPONENT_COST_BUDGET":"0"}
        if(retained.native.OLD_COMPACT&env.keys()or any(env.get(k)!=v for k,v in wanted.items())
           or not env.get("PYTHONPATH","").startswith("/probe/compilation_budget_r45:/probe:")):
            raise ValueError("actual default-off source-bound durability activation differs")
        workers={int(k):v for k,v in report["hot"]["worker_pids"].items()}
        for event in("graph_native_worker_import_verified","graph_candidate_hooks_installed"):
            rows=[e for e in events if e.get("event")==event]
            if len(rows)!=4 or{e["pid"]for e in rows}!=set(workers.values())or any(
                e.get("manifest_sha256")!=manifest or e.get("profile",e.get("graph_profile"))!=retained.PROFILE for e in rows):
                raise ValueError("four actual graph source activations required")
        if any(e.get("source_owned_native_compile_warmup")is not True for e in events if e.get("event")=="graph_candidate_hooks_installed"):
            raise ValueError("native compile warmup activation absent")
        if any(e.get("event","").startswith(("r33_prefix_terminal_","r35_evidence_io_","r38_component_budget_"))for e in events):
            raise ValueError("diagnostic shape oracle/timing observer entered formal run")
        files={p.name:p.read_bytes()for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}
        unit=json.loads((raw/"performance-unit.json").read_bytes())
        ids=[x["metrics"]["request_id"]for x in unit["results"]]
        report["durability"]=audit_durable_files(files,ids+warm_proof["warm_request_ids"],workers,manifest,enabled=True)
        warm_hot=_audit_hot(events,warm_proof["warm_request_ids"],manifest_sha256=manifest,expected_count=2)
        if not warm_hot["accepted_hot_coverage"]or warm_hot["worker_pids"]!=workers:
            raise ValueError("actual two target warmups require fourworker48C1/16C2")
        warm_hot["legacy_helper_scope"]=warm_hot.pop("scope")
        warm_hot["scope"]="Exactly two actual unscored target warmups; measured denominator remains40."
        report["target_warmups"]["hot"]=warm_hot
    elif(any(k.startswith("INDEPENDENT_")for k in env)or any(":/probe"in x for x in argv)
         or(raw/"diagnostics").exists()):
        raise ValueError("native G1 mounted or imported algorithm")
    report.update(retained.components._algorithm_evidence(c,cfg,report,events,manifest,on))
    info=retained.parse_info_graph((raw/"service.log").read_bytes())
    if on and info["workers"]!={int(k):v for k,v in report["hot"]["worker_pids"].items()}:
        raise ValueError("native graph worker/mechanism identity differs")
    journal=[json.loads(l)for l in(raw/"events.jsonl").read_text().splitlines()]
    samples=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    start=json.loads((raw/"service-start.json").read_bytes())
    report["physical"]=retained.audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    if live_release:
        from formal_r15_tp4 import port_free
        for port in [c["port"]]+list(range(c["hccl_ports"][0],c["hccl_ports"][1]+1)):
            with socket.socket()as s:s.bind(("0.0.0.0",port))
        from formal_r15_tp4 import snapshot
        current=snapshot()
        if current["processes"]or current["foreign"]:raise ValueError("current physical0-3 release incomplete")
    workers={int(k):v for k,v in report["hot"]["worker_pids"].items()}
    observations=[compilation.audit_worker([e for e in events if e.get("pid")==pid],pid=pid,rank=rank,manifest=manifest)for rank,pid in sorted(workers.items())]
    if any(row["calls"]==0 for row in observations):raise ValueError("actual per-worker compiler observation path not demonstrated")
    clock=audit_clock(samples,workers,c["r45_clock_proof"])
    report["compilation_observation"]=observations
    report["compilation_budget_upper"]=compilation.budget(observations,unit["results"],shared_monotonic_clock_proven=clock["clock_binding_valid"])
    report["compilation_clock"]=clock
    report.update(r45_diagnostic_transport_valid=True,graph=info,policy=checked["policy"],
        prerequisite=checked["prerequisite"],original438_runtime_unchanged=True,runtime_python=442,
        native_speed_gain_proven=False,full_goal_complete=False,
        scope="One unprofiled R45 compilation observation, original math/full40c16/fixed1024/warm2+prep4 and exact release verified. Observational timings and optimistic bounds are not exclusive removable blocking, net service gain, repeated performance or quality acceptance.")
    report["raw_sha256"]={n:policy.sha(raw/n)for n in("result.json","release.json","events.jsonl","performance-unit.json","responses.json","launch.json","service-start.json","service.log")}
    report["worker_sha256"]={p.name:policy.sha(p)for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}
    report["r45_launch_identity"]=expected
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True)
    a=p.parse_args();d=audit(a.contract,live_release=a.live_release);data=(json.dumps(d,sort_keys=True)+"\n").encode()
    with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"r45_diagnostic_transport_valid":True,"output":a.output,"sha256":hashlib.sha256(data).hexdigest(),"timing":d["timing"],"live_release_verified":d.get("live_release_verified",False)}))
