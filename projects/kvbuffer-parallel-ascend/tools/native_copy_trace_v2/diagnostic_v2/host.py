#!/usr/bin/env python3
"""MAIN-only native-copy observation host. Default OFF; physical6 non-timing."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,sys,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/kvbuffer-parallel-ascend/tools/native_copy_trace_v2/diagnostic_v2"
LEASE=ROOT/"projects/kvbuffer-parallel-ascend/tools/b16_saved_step_diagnostic_lease6_v2/host.py"
LEASE_SHA="804ec5342da9233be4a98bc509e4e675a22dfebf38079ce4813bd8afe1a77381"
BUILDER=HERE.parent/"build_no_device_v3.py"
BUILDER_SHA="9e3fac5cfd2e5a6281fdfeb3d1a5199cb8bc9678cf0fc55addce4463a86a5a91"
META_SHA="ec026d42225ffc1f24cde74b689fecf97bdd0bf554fa5645168620169eed1f76"
ENTRY=HERE/"protocol.py"
OUT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/native-copy-trace-diagnostic-v2-20261007-1440")
BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-copy-trace-v3-20261007-1400")
NAME="kvbuffer_native_copy_trace_diagnostic_v2_20261007_1440"
OWNER="kvbuffer-native-copy-trace-diagnostic-v2"
LIB=BUILD/"build/libqwen36_native_recurrent_copy_trace_v2_ops.so"
def require(v,s):
    if not v:raise ValueError(s)
def sha(p):
    p=Path(p);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def module(path,name):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp)
    sys.modules[name]=m;sp.loader.exec_module(m);return m
def configured():
    require(sha(LEASE)==LEASE_SHA,"immutable physical6 lease implementation")
    l=module(LEASE,"_kvbp_trace_lease6")
    l.OUT=OUT;l.NAME=NAME;l.OWNER=OWNER
    original=l.mounts
    def mounts():
        values=original();values[str(BUILD)]=(str(BUILD),False)
        candidate=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/candidate-ub-trace-diagnostic-v2-20261007")
        values[str(candidate)]=(str(candidate),False);return values
    l.mounts=mounts
    return l
def native_contract():
    sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE))
    import native_contract as n
    return n
def trace_sources():
    return native_contract().sources()
def refs_from_args(a):
    refs={"library":{"path":str(LIB),"sha256":a.trace_library_sha256},
      "build":{"path":str(BUILD/"build-receipt.json"),"sha256":a.trace_build_sha256},
      "meta":{"path":str(BUILD/"meta-receipt.json"),"sha256":a.trace_meta_sha256}}
    require(refs==native_contract().REFS,"explicit actual native artifact pins")
    return refs
def check_receipts(refs,manifest,sources):
    return native_contract().consume(refs,manifest,sources)
def source_snapshot(l):
    h,c,r,m,s=l.sources();tm,ts=trace_sources()
    combined={**s,**ts,str(LEASE):LEASE_SHA,str(Path(__file__).resolve()):sha(__file__),str(ENTRY):sha(ENTRY),
        str(HERE/"native_contract.py"):sha(HERE/"native_contract.py"),
        str(HERE/"tiling_contract.py"):sha(HERE/"tiling_contract.py")}
    require(len(s)==64 and all(sha(p)==v for p,v in combined.items()),"complete original/new source identity")
    return h,c,r,m,s,tm,ts,combined
def execute(a):
    require(sha(__file__)==a.script_sha256 and sha(ENTRY)==a.entry_sha256,"MAIN exact new host/entry")
    l=configured();h,c,r,m,s,tm,ts,before=source_snapshot(l)
    refs=refs_from_args(a);check_receipts(refs,tm,ts)
    require(OUT.parent.is_dir() and not OUT.exists() and not OUT.is_symlink(),"NEW unique output, no retry")
    require(datetime.now(timezone.utc)+timedelta(seconds=l.CAP)<=l.CUTOFF,"fixed cutoff includes cleanup")
    resource=l.resources()
    require(resource["memory"]["MemAvailable"]>=l.MEM+l.RESERVE+2*1024**3,"summed2GiB prep + 8GiB numeric + unchanged8GiB reserve")
    require(json.loads(resource["engine"]["stdout"])["NCPU"]>=5,"summed CPU capacity")
    smi=l.run([l.SMI,"info"]);require(smi["exit_code"]==0,"actual fresh SMI")
    h.idle_one(smi["stdout"],6);protected=h.protected(smi["stdout"])
    exists=l.run([l.DOCKER,"ps","-a","--filter","name=^/"+NAME+"$","--format","{{.ID}}"])
    require(exists["exit_code"]==0 and not exists["stdout"].strip(),"NEW unique owned container")
    OUT.mkdir();deadline=time.monotonic()+l.CAP
    rr=l.write(OUT/"resources-original.json",{**resource,"smi":smi,"protected0_3":protected,
        "deadline_seconds":l.CAP,"cleanup":l.CLEANUP,"trace_artifacts":refs,"complete_sources":before})
    argv=[l.DOCKER,"create","--name",NAME,"--label","model-tuning-lab.owner="+OWNER,
        "--label","model-tuning-lab.run="+NAME,"--label","model-tuning-lab.producer-sha256="+a.script_sha256,
        "--network","none","--cap-drop","ALL","--security-opt","no-new-privileges","--memory",str(l.MEM),
        "--memory-swap",str(l.MEM),"--cpus","1","--pids-limit","512","--env","ASCEND_RT_VISIBLE_DEVICES=0",
        "--env","TORCH_DEVICE_BACKEND_AUTOLOAD=0","--env","PYTHONDONTWRITEBYTECODE=1","--env","OMP_NUM_THREADS=1"]
    for src,dst in l.devices().items():
        require(Path(src).exists(),"actual device node");argv+=["--device",src+":"+dst]
    for dst,(src,rw) in l.mounts().items():
        require(Path(src).is_dir(),"actual mount source")
        argv+=["--mount","type=bind,src="+src+",dst="+dst+("" if rw else ",readonly")]
    argv+=["--workdir",str(ROOT),"--entrypoint","/bin/bash",l.IMAGE,"-c","exec sleep infinity"]
    created,_=l.capture("create",argv);cid=created["stdout"].strip()
    require(re.fullmatch("[0-9a-f]{64}",cid),"actual exact CID")
    primary=None
    try:
        l.inspect(cid,a.script_sha256);l.capture("start",[l.DOCKER,"start",cid])
        can=l.observe_child(cid,"canary",h.legacy().exec_argv(cid,[str(Path(__file__).resolve()),
            "--inside-canary","--script-sha256",a.script_sha256]),str(Path(__file__).resolve()),
            deadline,a.script_sha256,protected)
        cp={"path":str(OUT/"canary.json"),"sha256":sha(OUT/"canary.json")}
        require(json.loads(Path(cp["path"]).read_bytes())["sources"]==s,"actual frozen source canary")
        _,ir=l.inspect(cid,a.script_sha256)
        identity={"schema":"kvbp.split-launch-identity/v2","image_id":l.IMAGE,"protocol":c.protocol(16,6),
            "physical_devices":[6],"logical_to_physical":{"0":6},"fresh_idle_verified":True,"nonprivileged":True,
            "source_canary_passed":True,"memory_cgroup_bytes":l.MEM,"source_manifest":r,"sources":s,
            "artifact_refs":h.REFS,"preflight_utc":datetime.now(timezone.utc).isoformat(),
            "lease_scope":{"physical":[6],"other_cards_observed_only":True,"timing_authorized":False},
            "diagnostic_script":{"path":str(ENTRY),"sha256":a.entry_sha256},"trace_artifact_refs":refs,
            "trace_source_manifest":{"path":str(HERE.parent/"SOURCE_MANIFEST_V3.json"),"sha256":"ab34453481db93db73acf66461b93e8a2213cde0d0001fbbc80556fdd0c6d5ba"},
            "trace_runtime_sources":{key:{"path":str(HERE/name),"sha256":sha(HERE/name)}
                for key,name in (("protocol","protocol.py"),("host","host.py"),("contract","native_contract.py"))},
            "complete_trace_sources":before,"evidence":{"resources":rr,"container_inspect":ir,
            "canary_child":can,"canary":cp}}
        identity_ref=l.write(OUT/"identity.json",identity);c.validate_identity(identity,16,6,r,m,s,h.REFS)
        args=[str(ENTRY),"--execute","--script-sha256",a.entry_sha256,"--identity",identity_ref["path"],
            "--output-dir","/kvbuffer-results/diagnostic"]
        for key,label in (("library","trace-library"),("build","trace-build"),("meta","trace-meta")):
            args+=["--"+label,refs[key]["path"],"--"+label+"-sha256",refs[key]["sha256"]]
        child=l.observe_child(cid,"diagnostic",h.legacy().exec_argv(cid,args),str(ENTRY),deadline,a.script_sha256,protected)
        require(source_snapshot(l)[-1]==before,"complete sources unchanged")
        l.write(OUT/"RESULT.json",{"status":"native-copy-only-trace-child-completed","child":child,"identity":identity_ref,
            "matrix_verified":False,"e2e_verified":False,"serving_ready":False,"cause_proved":False})
    except BaseException as e:
        primary=e
        try:l.write(OUT/"host-error.json",{"primary":repr(e),"container":cid,"sources":s,"complete_sources":before})
        except BaseException as secondary:
            print(json.dumps({"primary":repr(e),"secondary_save":repr(secondary)}),flush=True)
        raise
    finally:
        try:
            l.inspect(cid,a.script_sha256,min(30,max(1,deadline-time.monotonic())))
            l.capture("stop",[l.DOCKER,"stop","--time","15",cid],min(30,max(1,deadline-time.monotonic())))
            x,ir=l.inspect(cid,a.script_sha256,min(30,max(1,deadline-time.monotonic())))
            require(not x["State"]["Running"] and x["State"]["Pid"]==0 and not x.get("ExecIDs") and
                not x["State"]["OOMKilled"],"own exact stopped/Pid0/noExec/noOOM")
            l.write(OUT/"STOP_RETAIN.json",{"container_id":cid,"inspect":ir,"stopped":True,"retained":True,"deleted":False})
            last,lr=l.capture("release-smi",[l.SMI,"info"])
            require(h.protected(last["stdout"])==protected,"protected0-3 unchanged")
            h.idle_one(last["stdout"],6);after=source_snapshot(l)[-1];require(after==before,"sources unchanged")
            l.write(OUT/"POST_RELEASE.json",{"smi":lr,"protected0_3":protected,"sources_before":before,"sources_after":after})
        except BaseException as e:
            print(json.dumps({"primary":repr(primary),"secondary_cleanup":repr(e)}),flush=True)
            if primary is None:raise
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
    g.add_argument("--execute",action="store_true");g.add_argument("--inside-canary",action="store_true")
    p.add_argument("--script-sha256");p.add_argument("--entry-sha256")
    p.add_argument("--trace-library-sha256");p.add_argument("--trace-build-sha256");p.add_argument("--trace-meta-sha256")
    a=p.parse_args(argv)
    if a.inside_canary:
        require(a.script_sha256 and sha(__file__)==a.script_sha256,"explicit inside host SHA");configured().inside_canary()
    elif a.execute:
        require(all((a.script_sha256,a.entry_sha256,a.trace_library_sha256,a.trace_build_sha256,a.trace_meta_sha256)),
            "explicit MAIN source/artifact SHA");execute(a)
    else:print(json.dumps({"default_enabled":False,"npu_executed":False,"physical":6,"out":str(OUT),
        "memory_cap":8*1024**3,"timing_authorized":False,"matrix_verified":False,"serving_ready":False}))
if __name__=="__main__":main()
