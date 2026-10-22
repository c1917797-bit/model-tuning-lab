"""Default-OFF one-shot MAIN TP4 replay controller over exact existing safety APIs."""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LOCK = "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock"
OUTPUT_CAP = 64 * 2**20
PHASE = 600
CLEANUP = 180
FALSES = dict(diagnostic_only=True, numerical_qualified=False,
              candidate_qualification=False, formal_performance=False, task_accuracy=False)


def need(value, why):
    if not value:
        raise ValueError(why)


def ref(path):
    p=Path(path)
    need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),
         "ordinary exact source")
    before=p.stat()
    need(0<=before.st_size<=2*2**20,"bounded complete controller input/source")
    b=p.read_bytes()
    after=p.stat()
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    need(identity(before)==identity(after) and len(b)==before.st_size,"stable complete controller input/source")
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def checked(r):
    need(type(r) is dict and set(r)=={"path","bytes","sha256"} and type(r["bytes"]) is int
         and 0<=r["bytes"]<=2*2**20 and ref(r["path"])==r,"complete bounded immutable Ref3")
    return Path(r["path"])


def obj(r):
    return json.loads(checked(r).read_bytes())


def load(r,name):
    need(name not in sys.modules,"fresh private controller namespace")
    p=checked(r);s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m)
    need(ref(p)==r,"import did not alter source")
    return m


def output_bytes(root):
    total=0
    for p in root.rglob("*"):
        need(not p.is_symlink(),"no symlink in sole owned output")
        if p.is_file():total+=p.stat().st_size
    return total


def terminal_logs(c,child,stdout,stderr):
    value=dict(exit_code=child.poll(),termination_observed=child.poll() is not None,
               stdout_path=str(stdout),stderr_path=str(stderr),
               logs_frozen_after_termination=child.poll() is not None)
    if child.poll() is not None:
        value.update(stdout=c.ref(stdout),stderr=c.ref(stderr))
    return value


def manifest(ir):
    x=obj(ir)
    need(type(x) is dict and set(x)=={"schema","controller_ref","common_ref","namespace_ref",
          "base_source_ref","authority_ref","replay_manifest_ref","replay_worker_ref","variant",
          "output_root","owner_name","lock_path","image","phase_seconds","cleanup_seconds",
          "output_cap_bytes","same_image_software_ref"} and
          x["schema"]=="bole.collective-replay-controller-input/v1","closed controller contract")
    need(x["controller_ref"]==ref(__file__) and x["image"]==IMAGE and x["lock_path"]==LOCK
         and x["phase_seconds"]==PHASE and x["cleanup_seconds"]==CLEANUP
         and x["output_cap_bytes"]==OUTPUT_CAP,"exact source/image/clock/lock/output policy")
    need(x["variant"] in ("default","deterministic_true") and
         type(x["owner_name"]) is str and re.fullmatch("bole-collective-[a-z0-9-]{1,50}",x["owner_name"]),
         "one exact fresh source-owned name")
    root=Path(x["output_root"])
    need(root.parent==Path("/opt/host/vnf/austinov") and
         root.name.startswith("run-bole-native-ar-collective-replay-") and not root.exists()
         and not any(p.is_symlink() for p in (root,*root.parents)),"fresh private adapter-compatible root")
    authority=obj(x["authority_ref"])
    need(type(authority["start_epoch"]) is int and type(authority["cutoff_epoch"]) is int
         and authority["phase_seconds"]==3600 and authority["cleanup_seconds"]==180,
         "original immutable batch and safety cleanup preserved")
    for key in ("common_ref","namespace_ref","base_source_ref","replay_worker_ref",
                "replay_manifest_ref","same_image_software_ref"):checked(x[key])
    return x,authority


def review(rr,ir,x):
    r=obj(rr)
    need(r.get("schema")=="bole.collective-replay-main-review/v1" and
         r.get("input_ref")==ir and r.get("controller_ref")==x["controller_ref"]
         and r.get("approved") is True and r.get("NPU_executed") is False
         and r.get("same_image_software_ref")==x["same_image_software_ref"],
         "actual explicit MAIN source/admission review required")
    cpu=obj(x["same_image_software_ref"])
    need(cpu.get("schema")=="bole.collective-replay-sameimage-software/v1"
         and cpu.get("passed") is True and cpu.get("devices")==[]
         and cpu.get("worker_ref")==x["replay_worker_ref"]
         and cpu.get("controller_ref")==x["controller_ref"] and cpu.get("NPU") is False
         and cpu.get("image")==IMAGE,"real pinned-image device-free software evidence")
    return r


def command(c,cid,x):
    need(re.fullmatch("[0-9a-f]{64}",cid or ""),"actual full owned CID")
    args=["-m","torch.distributed.run","--standalone","--nnodes=1","--nproc-per-node=4",
          "--local-addr=127.0.0.1",x["replay_worker_ref"]["path"],"--execute",
          "--manifest-ref",json.dumps(x["replay_manifest_ref"],sort_keys=True),
          "--output",str(Path(x["output_root"])/"dense"/"worker-results")]
    argv=c.docker_argv(cid,args)
    need(argv[:3]==["/usr/bin/docker","exec",cid],"original source-bound exec prefix")
    if x["variant"]=="deterministic_true":
        argv[2:2]=["--env","HCCL_DETERMINISTIC=true"]
    return argv


@contextlib.contextmanager
def main_lock(path):
    need(path==LOCK and Path(path).is_file() and not Path(path).is_symlink(),"existing shared MAIN lock")
    with open(path,"r+b",buffering=0) as stream:
        fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        identity=os.fstat(stream.fileno());need(Path(path).stat().st_ino==identity.st_ino,"same lock inode")
        yield dict(path=path,device=identity.st_dev,inode=identity.st_ino,pid=os.getpid())
        need(Path(path).stat().st_ino==identity.st_ino,"shared lock not replaced during run")


def source_plan(ir):
    x,a=manifest(ir)
    C=load(x["common_ref"],"_collective_exact_common")
    on=C.obj(x["base_source_ref"])
    NS=load(x["namespace_ref"],"_collective_exact_namespace")
    need(NS.NAMES and callable(NS.open_namespace),"exact existing namespace API")
    worker=load(x["replay_worker_ref"],"_collective_exact_worker")
    m,raw,refs=worker.validate_manifest(x["replay_manifest_ref"],0)
    need(m["variant"]==x["variant"],"same replay variant")
    # No helper admission or Docker operation is called in a source plan.
    return x,a,C,NS,on,worker,refs


@contextlib.contextmanager
def recorded_lock(path,report,root,C):
    with main_lock(path) as lock:
        try:
            yield lock
            report["namespace_scope_returned"]=True
        except BaseException as error:
            report["completed"]=False
            report["namespace_scope_returned"]=False
            fault=dict(type=type(error).__name__,message=str(error),
                       traceback=traceback.format_exc(limit=12))
            if report["primary"] is None:report["primary"]=fault
            else:report["secondary"].append(fault)
        finally:
            if root.is_dir():
                try:
                    stat=Path(path).stat()
                    unchanged=(stat.st_dev,stat.st_ino)==(lock["device"],lock["inode"])
                except OSError:
                    unchanged=False
                if not unchanged:
                    report["completed"]=False
                    report["secondary"].append("shared lock inode changed before final receipt")
                C.write(root/"RESULT.json",report)


def run(ir,rr):
    x,a,C,NS,on,worker,input_refs=source_plan(ir)
    review(rr,ir,x)
    need(os.environ.get("DENSE090_EXTERNAL_OUTPUT_ENABLE")=="1",
         "explicit inherited private-output opt-in required in MAIN launch environment")
    need(a["start_epoch"]<=time.time() and time.time()+PHASE<a["cutoff_epoch"],
         "complete new bounded phase fits original unextended cutoff")
    start=time.monotonic();deadline=start+PHASE-CLEANUP
    report=dict(schema="bole.collective-replay-host/v1",**FALSES,input_ref=ir,review_ref=rr,
                completed=False,primary=None,secondary=[],cleanup=None,child=None,
                physical=[4,5,6,7],world_group_is_vllm_TP_group=False,
                default_unset_is_not_determinism_false=True)
    ctl=None;child=None;root=Path(x["output_root"])
    def interrupted(signum,frame):
        raise RuntimeError("controller signal "+str(signum))
    previous={s:signal.signal(s,interrupted) for s in (signal.SIGTERM,signal.SIGINT)}
    try:
        with recorded_lock(x["lock_path"],report,root,C) as lock:
            with NS.open_namespace(C,dict(output_root=x["output_root"],authority=x["authority_ref"]),on) as (c,S,H,namespace):
                need(c.IMAGE==IMAGE and S.PHYSICAL==(4,5,6,7) and S.MEM==32*c.GIB
                     and S.WORKSPACE==32*c.GIB and S.RESERVE==8*c.GIB
                     and S.HOST_MEM==512*2**20 and S.CLEANUP==180,"preserved original resource safety profile")
                root.mkdir(mode=0o700);report["lock"]=lock;report["namespace"]=namespace
                joint=H.Joint(start)
                try:
                    leaf=H.fresh_leaf(root/"dense");H.outputs(leaf);(leaf/"receipts").mkdir()
                    (leaf/"worker-results").mkdir()
                    ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start)
                    ctl.name=x["owner_name"]
                    report["admission"]=ctl.observe("collective-replay-admission",initial=True)
                    # Exact input file mounts; no model/checkpoint or broad historical output mounts.
                    refs={r["path"]:r for r in [ir,rr,x["replay_manifest_ref"],x["replay_worker_ref"],
                                              *input_refs]}
                    for r in refs.values():checked(r)
                    mounts={"/usr/local/Ascend/driver":("/usr/local/Ascend/driver",False),
                            str(leaf):(str(leaf),True),"/adakv-results":(str(leaf),True)}
                    for path in refs:
                        need(leaf not in Path(path).parents,"readonly source cannot overlap output")
                        mounts[path]=(path,False)
                    # Existing external025 owns cache paths, read-only rootfs and capped logging.
                    import external025
                    external025.prepare(leaf)
                    ctl.expected=dict(cid=None,name=ctl.name,image=IMAGE,arm="collective-replay",source=ir,
                        host_sha256=c.sha(S.__file__),guest_cpus=ctl.cpu["guest_cpus"],mounts=mounts)
                    old,_=ctl.call("unique-name",[S.DOCKER,"ps","-a","--filter","name=^/"+ctl.name+"$","--format","{{.ID}}"])
                    need(not old["stdout"].strip(),"no reuse of old owner")
                    ctl.create_owned({"safety_host.py":c.sha(S.__file__)})
                    inspected,iref=ctl.inspect()
                    need(not inspected["State"]["Running"],"new stopped exact owner")
                    need(not any(v.startswith("HCCL_DETERMINISTIC=") for v in inspected["Config"].get("Env",[])),
                         "image does not secretly set variant flag")
                    need(time.monotonic()<deadline,"remaining original phase before start")
                    ctl.call("start",[S.DOCKER,"start",ctl.cid],cap=60)
                    inspected,iref=ctl.inspect()
                    cv=S.H.cpu_view(inspected["State"]["Pid"])
                    need(cv["effective_cpus"]==ctl.expected["guest_cpus"] and
                         cv["effective_capacity"]==inspected["HostConfig"]["NanoCpus"]/10**9,
                         "actual unchanged guest CPU profile")
                    report["inspect"]=iref;report["cpu"]=cv
                    # Mapping evidence references the actual validated create/inspect.
                    argv=command(c,ctl.cid,x);report["requested_argv"]=argv
                    need(time.monotonic()<deadline,"remaining original phase before worker launch")
                    stdout=leaf/"torchrun.stdout";stderr=leaf/"torchrun.stderr"
                    ctl.server_started=datetime.datetime.now(datetime.timezone.utc)
                    with stdout.open("xb") as so,stderr.open("xb") as se:
                        child=subprocess.Popen(ctl.wrapper(argv),stdout=so,stderr=se,cwd=c.ROOT)
                    ctl.server=child;ctl.server_argv=argv
                    next_observation=0.
                    try:
                        while child.poll() is None:
                            need(time.monotonic()<deadline and time.time()+CLEANUP<a["cutoff_epoch"],
                                 "single phase deadline reached")
                            need(output_bytes(root)+2*2**20<=OUTPUT_CAP,"sole64MiB output including terminal reserve")
                            if time.monotonic()>=next_observation:
                                ctl.observe("collective-replay")
                                next_observation=time.monotonic()+5
                            time.sleep(.5)
                        need(child.returncode==0,"actual torchrun nonzero exit; raw stderr retained")
                    finally:
                        report["child"]=dict(host_pid=child.pid,exit_code=child.poll(),
                            stdout_path=str(stdout),stderr_path=str(stderr),
                            termination_observed=child.poll() is not None)
                    results=[]
                    for rank in range(4):
                        path=leaf/"worker-results"/("rank-%d"%rank)/"RESULT.json"
                        value=json.loads(path.read_bytes())
                        need(value["rank"]==rank and value["completed"] is True
                             and value["primary"] is None and value["cleanup_error"] is None
                             and value["input_refs_rechecked"] is True and value["collective_calls_completed"]==8
                             and value["candidate_qualification"] is False,"complete actual all-rank diagnostic")
                        results.append(c.ref(path))
                    report["rank_results"]=results
                    for r in input_refs:worker.checked(r,2*2**20)
                    report["completed"]=True
                except BaseException as error:
                    report["primary"]=dict(type=type(error).__name__,message=str(error),
                                           traceback=traceback.format_exc(limit=12))
                    if ctl is not None:ctl.primary=error
                finally:
                    if ctl is not None:
                        try:
                            cleanup=ctl.cleanup();report["cleanup"]=cleanup
                            receipt=c.obj(cleanup)
                            if not (receipt["stopped"] and receipt["retained"] and not receipt["errors"]):
                                report["completed"]=False
                        except BaseException as error:
                            report["secondary"].append("exact own cleanup: "+repr(error))
                            report["completed"]=False
                        report["secondary"].extend(ctl.secondary)
                    if child is not None:
                        try:
                            child.wait(timeout=15)
                        except subprocess.TimeoutExpired:
                            report["secondary"].append("owned foreground Docker CLI still live")
                            report["completed"]=False
                        report["child"].update(terminal_logs(c,child,stdout,stderr))
                    report["output_bytes_before_result"]=output_bytes(root)
                    report["whole_phase_seconds_before_result"]=time.monotonic()-start
                    if report["secondary"] or time.monotonic()-start>PHASE or time.time()>=a["cutoff_epoch"]:
                        report["completed"]=False
                    if report["output_bytes_before_result"]+128*1024>OUTPUT_CAP:
                        report["completed"]=False
                        report["secondary"].append("64MiB evidence budget exceeded")
    finally:
        for s,h in previous.items():signal.signal(s,h)
    return 0 if report["completed"] and report["primary"] is None else 1


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument("--execute",action="store_true");p.add_argument("--source-audit",action="store_true")
    p.add_argument("--inputs-ref");p.add_argument("--review-ref")
    args=p.parse_args()
    if not(args.execute or args.source_audit):
        print(json.dumps(dict(enabled=False,NPU=False,**FALSES)));return 0
    need(args.inputs_ref,"exact controller input Ref required")
    ir=json.loads(args.inputs_ref)
    if args.source_audit:
        x,a,C,NS,on,w,refs=source_plan(ir)
        print(json.dumps(dict(source_only=True,NPU=False,input_ref=ir,worker_inputs=len(refs),
                             main_review_pending=True,**FALSES)));return 0
    need(args.review_ref,"MAIN review Ref required before lock/create")
    return run(ir,json.loads(args.review_ref))


if __name__=="__main__":
    raise SystemExit(main())
