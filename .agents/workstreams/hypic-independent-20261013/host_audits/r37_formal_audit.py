"""Independent final-source R37 full40 transport/mechanism/durability audit."""
import argparse,hashlib,json,os,socket,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r37_formal_policy as policy
from host_audits import r30b_graph_formal_audit as retained
from host_audits.r36_durability_evidence import audit_durable_files
def audit(path,*,live_release=False):
    cp=Path(path).resolve();root=cp.parent
    if Path.cwd().resolve()!=root:raise ValueError("owning formal workstream cwd required")
    c=json.loads(cp.read_bytes());checked=policy.check(c,root=root,require_new_root=False)
    report=retained.audit_r18_base(cp,live_release=live_release)
    raw=Path(c["raw_root"]);launch=json.loads((raw/"launch.json").read_bytes())
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
    expected={"role":c["r37_role"],"algorithm_on":on,"step_durability":on,
        "io_observer":False,"prefix_observer":False,
        "actual_workload":"unchanged independent_formal_workload.run_formal_workload"}
    if launch.get("r37_launch_identity")!=expected:raise ValueError("actual formal workload/delivery receipt differs")
    cfg,manifest=retained.components._manifest(c,root)
    events=retained.components._events(raw,"compact-worker-")
    if on:
        wanted={"INDEPENDENT_GRAPH_HYPIC":"1","INDEPENDENT_GRAPH_MANIFEST":"/probe/"+c["successor_manifest"],
                "INDEPENDENT_GRAPH_RAW":"/scratch/diagnostics","INDEPENDENT_EVIDENCE_STEP_DURABILITY":"1",
                "INDEPENDENT_EVIDENCE_IO_BUDGET":"0","INDEPENDENT_PREFIX_TERMINAL_ONLY":"0"}
        if(retained.native.OLD_COMPACT&env.keys()or any(env.get(k)!=v for k,v in wanted.items())
           or not env.get("PYTHONPATH","").startswith("/probe/step_durability_r36:/probe:")):
            raise ValueError("actual default-off source-bound durability activation differs")
        workers={int(k):v for k,v in report["hot"]["worker_pids"].items()}
        for event in("graph_native_worker_import_verified","graph_candidate_hooks_installed"):
            rows=[e for e in events if e.get("event")==event]
            if len(rows)!=4 or{e["pid"]for e in rows}!=set(workers.values())or any(
                e.get("manifest_sha256")!=manifest or e.get("profile",e.get("graph_profile"))!=retained.PROFILE for e in rows):
                raise ValueError("four actual graph source activations required")
        if any(e.get("source_owned_native_compile_warmup")is not True for e in events if e.get("event")=="graph_candidate_hooks_installed"):
            raise ValueError("native compile warmup activation absent")
        if any(e.get("event","").startswith(("r33_prefix_terminal_","r35_evidence_io_"))for e in events):
            raise ValueError("diagnostic shape oracle/timing observer entered formal run")
        files={p.name:p.read_bytes()for p in(raw/"diagnostics").glob("compact-worker-*.jsonl")}
        unit=json.loads((raw/"performance-unit.json").read_bytes())
        ids=[x["metrics"]["request_id"]for x in unit["results"]]
        report["durability"]=audit_durable_files(files,ids,workers,manifest,enabled=True)
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
        for port in range(c["hccl_ports"][0],c["hccl_ports"][1]+1):port_free(port)
    report.update(formal_r37_full40_valid=True,graph=info,policy=checked["policy"],
        prerequisite=checked["prerequisite"],runtime_python_identical_to_R36=True,
        native_speed_gain_proven=False,full_goal_complete=False,
        scope="One actual final-source full40/c16/fixed1024 G1 or G3 arm. No speed claim without matched pair; repetitions/PDC/fullquality/lifecycle separate.")
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True)
    a=p.parse_args();d=audit(a.contract,live_release=a.live_release);data=(json.dumps(d,sort_keys=True)+"\n").encode()
    with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(json.dumps({"formal_r37_full40_valid":True,"output":a.output,"sha256":hashlib.sha256(data).hexdigest(),"timing":d["timing"],"live_release_verified":d.get("live_release_verified",False)}))
