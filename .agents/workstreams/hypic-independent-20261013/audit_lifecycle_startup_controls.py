"""Independent audit of captured exact-worker lifecycle startup controls."""
import re
KEYS={"INDEPENDENT_COMPACT_HYPIC","INDEPENDENT_COMPACT_MANIFEST","PYTHONPATH","VLLM_SERVER_DEV_MODE"}
def audit_startup_controls(record,c,samples,start,launch,*,package_root):
    stage=c.get("lifecycle_stage");cid=start.get("container_id");argv=launch.get("argv",[])
    if stage not in ("disabled","enabled","uninstalled") or not isinstance(cid,str) or not re.fullmatch("[0-9a-f]{64}",cid):
        raise ValueError("explicit lifecycle stage/exact CID required")
    if record.get("event")!="lifecycle-worker-startup-controls" or record.get("stage")!=stage or record.get("container_id")!=cid:
        raise ValueError("captured startup record identity mismatch")
    found=[s for s in samples if s.get("utc")==record.get("snapshot_utc")]
    if len(found)!=1 or found[0].get("foreign"):raise ValueError("exact clean capture snapshot required")
    snapshot=found[0]
    if argv.count("--host")!=1 or argv[argv.index("--host")+1]!="127.0.0.1":
        raise ValueError("lifecycle server must be loopback only")
    env={}
    for i,arg in enumerate(argv):
        if arg=="-e":
            if i+1>=len(argv) or "="not in argv[i+1]:raise ValueError("complete launch environment required")
            name,value=argv[i+1].split("=",1)
            if name in env:raise ValueError("ambiguous launch environment")
            env[name]=value
    mounted=package_root+":/probe:ro"in argv
    diagnostic=c.get("cache_diagnostic")
    if stage=="uninstalled":
        if diagnostic is not None or mounted or any(":/probe"in x for x in argv):
            raise ValueError("uninstalled package still in startup path")
        if any(k in env for k in ("INDEPENDENT_COMPACT_HYPIC","INDEPENDENT_COMPACT_MANIFEST","PYTHONPATH")):
            raise ValueError("uninstalled bootstrap environment injected")
        expected_switch=None;expected_manifest=None
    else:
        if not diagnostic or not mounted:raise ValueError("same exact lifecycle package must be mounted")
        expected_switch="1"if stage=="enabled"else"0"
        expected_manifest="/probe/"+diagnostic["compact_manifest"]
        if env.get("INDEPENDENT_COMPACT_HYPIC")!=expected_switch or env.get("INDEPENDENT_COMPACT_MANIFEST")!=expected_manifest or not env.get("PYTHONPATH","").startswith("/probe/compact_bootstrap:/probe:"):
            raise ValueError("declared switch/bootstrap/manifest mismatch")
    workers=record.get("workers",[])
    if len(workers)!=4 or any(type(w.get("physical_npu"))is not int or type(w.get("host_pid"))is not int for w in workers) or {w["physical_npu"]for w in workers}!=set(range(4)) or len({w["host_pid"]for w in workers})!=4:
        raise ValueError("four exact independent physical workers required")
    mapping={}
    for w in workers:
        owners=[o for o in snapshot.get("owners",[])if o.get("npu")==w["physical_npu"] and o.get("pid")==w["host_pid"]]
        if len(owners)!=1:raise ValueError("worker not in physical capture snapshot")
        owner=owners[0];ns=w.get("nspid")
        if owner.get("owned")is not True or owner.get("ownership_status")!="owned-cgroup" or not re.search(r"(?:/docker/|/docker-)"+cid+r"(?:\.scope)?(?:/|\n|$)",owner.get("cgroup","")):
            raise ValueError("worker cgroup is not exact owned container")
        if not isinstance(ns,list) or len(ns)<2 or any(type(n)is not int or n<=0 for n in ns) or ns!=owner.get("nspid") or ns[0]!=w["host_pid"]:
            raise ValueError("captured namespace identity drift")
        controls=w.get("controls",{})
        if set(controls)!=KEYS or any(v is not None and not isinstance(v,str)for v in controls.values()):
            raise ValueError("only whitelisted startup controls may be retained")
        if controls["INDEPENDENT_COMPACT_HYPIC"]!=expected_switch or controls["INDEPENDENT_COMPACT_MANIFEST"]!=expected_manifest:
            raise ValueError("actual worker switch/manifest differs from declared stage")
        if controls["VLLM_SERVER_DEV_MODE"]not in (None,"0") or env.get("VLLM_SERVER_DEV_MODE")not in (None,"0"):
            raise ValueError("development control interface must remain disabled")
        pythonpath=controls["PYTHONPATH"]
        if stage=="uninstalled":
            if "/probe"in (pythonpath or ""):raise ValueError("uninstalled worker retains package path")
        elif pythonpath!=env["PYTHONPATH"]:raise ValueError("actual worker bootstrap differs from launch")
        mapping[w["physical_npu"]]=dict(host_pid=w["host_pid"],nspid=ns)
    return {"startup_controls_verified":True,"stage":stage,"workers":mapping,"loopback_only":True,
        "scope":"captured exact-worker startup controls only; model requests/hot-path/source/release/three-state rollback audited separately"}
