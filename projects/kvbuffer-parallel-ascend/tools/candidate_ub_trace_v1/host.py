#!/usr/bin/env python3
"""MAIN-only copy-only UB trace host. Default OFF; one physical6 non-timing lease."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,sys,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/kvbuffer-parallel-ascend/tools/candidate_ub_trace_v1"
LEASE=ROOT/"projects/kvbuffer-parallel-ascend/tools/b16_saved_step_diagnostic_lease6_v2/host.py"
LEASE_SHA="804ec5342da9233be4a98bc509e4e675a22dfebf38079ce4813bd8afe1a77381"
BUILDER=HERE/"build_no_device.py"
BUILDER_SHA="69154b044ea3eeb14d165b02700d1f5fee77ba0eaec74d867439202cb42df3e9"
META_SHA="08facc204b0a8cfa6201e3bec87b6d8a3179ce76e3d204693aaf433c064fe088"
ENTRY=HERE/"entry.py"
OUT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/candidate-ub-trace-diagnostic-v1-20261007")
BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-candidate-ub-trace-v1-20261007-1140")
NAME="kvbuffer_candidate_ub_trace_v1_diagnostic_20261007"
OWNER="kvbuffer-candidate-ub-trace-diagnostic-v1"
LIB=BUILD/"build/libqwen36_gdn_kvbuffer_native_order_trace_v1_ops.so"
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
        values=original();values[str(BUILD)]=(str(BUILD),False);return values
    l.mounts=mounts
    return l
def trace_sources():
    require(sha(BUILDER)==BUILDER_SHA and sha(HERE/"meta_probe.py")==META_SHA,"compiled source producers")
    b=module(BUILDER,"_kvbp_trace_builder")
    return b.manifest()
def refs_from_args(a):
    return {"library":{"path":str(LIB),"sha256":a.trace_library_sha256},
        "build":{"path":str(BUILD/"build-receipt.json"),"sha256":a.trace_build_sha256},
        "meta":{"path":str(BUILD/"meta-receipt.json"),"sha256":a.trace_meta_sha256}}
def check_receipts(refs,manifest,sources):
    require(set(refs)=={"library","build","meta"},"exact trace artifact keys")
    for r in refs.values():
        require(type(r)==dict and set(r)=={"path","sha256"} and re.fullmatch("[0-9a-f]{64}",r["sha256"]) and
                sha(r["path"])==r["sha256"],"actual immutable trace artifact")
    build=json.loads(Path(refs["build"]["path"]).read_bytes())
    meta=json.loads(Path(refs["meta"]["path"]).read_bytes())
    require(build["schema"]=="kvbp.candidate-ub-trace-build/v1" and
            build["status"]=="compiled_no_device" and build["npu_executed"] is False and
            build["image_id"]=="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1" and
            build["namespace"]=="qwen36_kvbuffer_native_order_trace_v1" and build["npu_arch"]=="dav-2201" and
            build["sources"]==manifest["operator_sources"] and build["sources_before"]==sources and
            build["sources_after"]==sources and build["library_sha256"]==refs["library"]["sha256"] and
            len(build["commands"])==2 and all(c["exit_code"]==0 for c in build["commands"]) and
            build["exported_kernel"]["name"]=="qwen36_gdn_kvbuffer_native_order_trace_v1_kernel" and
            build["exported_kernel"]["defined"] is True and build["exported_kernel"]["type"] in ("T","W"),
            "real no-device ASC build provenance")
    require(meta["schema"]=="kvbp.candidate-ub-trace-meta/v1" and
            meta["status"]=="actual-load-schema-meta-only" and meta["library"]==refs["library"] and
            meta["positive_cases"]==2 and len(meta["negative_cases"])==12 and
            meta["npu_executed"] is False and meta["numeric_verified"] is False and
            meta["serving_ready"] is False and
            meta["source_manifest_sha256"]=="e970dca058a7e7d01e964c85b9580a5dde00b5929e5ae16ea064f34b07557cdf" and
            meta["mapped_library_lines"] and not any("(deleted)" in s for s in meta["mapped_library_lines"]),
            "real load/schema/Meta provenance only")
    return build,meta
def source_snapshot(l):
    h,c,r,m,s=l.sources();tm,ts=trace_sources()
    combined={**s,**ts,str(LEASE):LEASE_SHA,str(Path(__file__).resolve()):sha(__file__),str(ENTRY):sha(ENTRY)}
    require(len(s)==64 and all(sha(p)==v for p,v in combined.items()),"complete original/new source identity")
    return h,c,r,m,s,tm,ts,combined
def execute(a):
    require(sha(__file__)==a.script_sha256 and sha(ENTRY)==a.entry_sha256,"MAIN exact new host/entry")
    l=configured();h,c,r,m,s,tm,ts,before=source_snapshot(l)
    refs=refs_from_args(a);check_receipts(refs,tm,ts)
    require(OUT.parent.is_dir() and not OUT.exists() and not OUT.is_symlink(),"NEW unique output, no retry")
    require(datetime.now(timezone.utc)+timedelta(seconds=l.CAP)<=l.CUTOFF,"fixed cutoff includes cleanup")
    resource=l.resources();smi=l.run([l.SMI,"info"]);require(smi["exit_code"]==0,"actual fresh SMI")
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
            "trace_source_manifest":{"path":str(HERE/"SOURCE_MANIFEST.json"),
                "sha256":"e970dca058a7e7d01e964c85b9580a5dde00b5929e5ae16ea064f34b07557cdf"},
            "complete_trace_sources":before,"evidence":{"resources":rr,"container_inspect":ir,
            "canary_child":can,"canary":cp}}
        identity_ref=l.write(OUT/"identity.json",identity);c.validate_identity(identity,16,6,r,m,s,h.REFS)
        args=[str(ENTRY),"--execute","--script-sha256",a.entry_sha256,"--identity",identity_ref["path"],
            "--output-dir","/kvbuffer-results/diagnostic"]
        for key,label in (("library","trace-library"),("build","trace-build"),("meta","trace-meta")):
            args+=["--"+label,refs[key]["path"],"--"+label+"-sha256",refs[key]["sha256"]]
        child=l.observe_child(cid,"diagnostic",h.legacy().exec_argv(cid,args),str(ENTRY),deadline,a.script_sha256,protected)
        require(source_snapshot(l)[-1]==before,"complete sources unchanged")
        l.write(OUT/"RESULT.json",{"status":"copy-only-trace-child-completed","child":child,"identity":identity_ref,
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
