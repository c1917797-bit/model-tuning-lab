"""MAIN-only bounded same-image CPU check. No devices, authority or source binding."""
import argparse, hashlib, json, os, pathlib, subprocess, time
P=pathlib.Path
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
DONOR="af87acbdcc1844f4b70565b9e03aed46e18703131e1185449f61409140f5a1de"
WS=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def need(v,s):
    if not v: raise ValueError(s)
def checked(r):
    p=P(r["path"]); raw=p.read_bytes()
    need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),"ordinary exact source")
    need(len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"],"source Ref mismatch")
    return raw
def cmd(a,seconds=30):
    p=subprocess.run(a,capture_output=True,text=True,timeout=seconds)
    return dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
def main():
    ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument("--packet");ap.add_argument("--run",action="store_true");a=ap.parse_args()
    if not a.run: print(json.dumps(dict(enabled=False,NPU=False)));return
    need(time.time()+600<=1792710600,"CPU check plus cleanup fits existing batch cutoff; no renewal")
    packet=json.loads(P(a.packet).read_text())
    need(set(packet)=={"schema","files","script","output_root","container_name"} and packet["schema"]=="bole.prepared-same-image-CPU-packet/v1","exact CPU packet")
    refs=packet["files"]; need(refs and len(refs)<=64,"bounded source file count")
    for r in refs:checked(r);need(P(r["path"]).parent==WS/"fastpath_numeric_bridge_prepare_v1","exact preparer source")
    need(packet["script"] in refs and P(packet["script"]["path"]).name=="check_source_imports.py","actual test entry")
    out=P(packet["output_root"]);name=packet["container_name"]
    need(out.parent==P("/opt/host/vnf/austinov") and out.name.startswith("run-bole-fastpath-prepared-same-image-") and not out.exists(),"new exact output")
    need(name.startswith("bole-fastpath-cpu-") and all(c.isalnum() or c=="-" for c in name),"exact CPU name")
    mem={x.split(":")[0]:int(x.split()[1])*1024 for x in P("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:")}
    need(mem["MemAvailable"]>=32*2**30,"8GiB CPU plus ordinary-memory reserve")
    need(os.statvfs("/cache/docker").f_bavail*os.statvfs("/cache/docker").f_frsize>=int(8.5*2**30),"Docker reserve")
    need(os.statvfs(out.parent).f_bavail*os.statvfs(out.parent).f_frsize>=2*2**30,"output reserve")
    pre=cmd(["docker","inspect",DONOR]);need(pre["exit"]==0,"known owned historical CPU inspect")
    donor=json.loads(pre["stdout"])[0]
    need(donor["Image"]==IMAGE and not donor["State"]["Running"] and not donor["HostConfig"].get("Devices") and not donor["HostConfig"].get("DeviceRequests"),"stopped no-device exact donor")
    # This fixture's declared renderer/source closure is wholly inside WS.
    # Do not inherit the historical run's thousands of unrelated evidence
    # mounts or its writable output leaf. No weights or device mounts.
    mounts=[]
    absent=cmd(["docker","inspect",name]);need(absent["exit"]!=0 and "No such" in absent["stderr"],"new container name")
    out.mkdir(mode=0o700);tag=hashlib.sha256(P(__file__).read_bytes()).hexdigest()
    report=dict(schema="bole.prepared-same-image-CPU-result/v1",packet=packet,controller_sha256=tag,
        NPU=False,authority_created=False,source_bound_created=False,numerical_qualified=False,
        formal_performance=False,started_epoch=time.time(),primary=None)
    cid=None
    try:
        argv=["docker","create","--runtime","runc","--name",name,"--label","bole.prepared.cpu="+tag,
              "--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges",
              "--cpus","1","--memory","8g","--memory-swap","8g","--pids-limit","2048",
              "--tmpfs","/tmp:rw,nosuid,nodev,size=512m","--tmpfs","/run:rw,nosuid,nodev,size=64m",
              "--log-opt","max-size=1m","--log-opt","max-file=1",
              "-e","PYTHONDONTWRITEBYTECODE=1","-e","TORCH_DEVICE_BACKEND_AUTOLOAD=0",
              "-e","OMP_NUM_THREADS=1","-e","OPENBLAS_NUM_THREADS=1","-e","MKL_NUM_THREADS=1"]
        for m in mounts:argv+=["--mount","type=bind,src="+m["Source"]+",dst="+m["Destination"]+",readonly"]
        argv+=["--mount","type=bind,src="+str(WS)+",dst="+str(WS)+",readonly",
               "--entrypoint","/bin/bash",IMAGE,"-c",
               "source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec /usr/local/python3.12.13/bin/python3 -B -I "+packet["script"]["path"]+" --check"]
        created=cmd(argv);need(created["exit"]==0,created["stderr"]);cid=created["stdout"].strip()
        ins=cmd(["docker","inspect",cid]);need(ins["exit"]==0,"created inspect")
        d=json.loads(ins["stdout"])[0];h=d["HostConfig"]
        need(d["Image"]==IMAGE and not h.get("Devices") and not h.get("DeviceRequests") and
             h["ReadonlyRootfs"] and not h["Privileged"] and h["NetworkMode"]=="none" and h["Runtime"]=="runc" and
             h["Memory"]==8*2**30 and h["NanoCpus"]==10**9 and
             all(not m["RW"] for m in d["Mounts"]),"actual no-device sandbox contract")
        report["before"]={k:d[k] for k in ("Id","Image","Mounts","HostConfig")}
        started=cmd(["docker","start",cid]);need(started["exit"]==0,started["stderr"])
        waited=cmd(["docker","wait",cid],300);need(waited["exit"]==0,"CPU wait command")
        logs=cmd(["docker","logs",cid]);report["logs"]=logs
        need(waited["stdout"].strip()=="0","same-image software process failed")
        objects=[]
        for line in logs["stdout"].splitlines():
            try: objects.append(json.loads(line))
            except ValueError: pass
        rows=[v for v in objects if isinstance(v,dict) and v.get("schema")=="bole.prepared-qualification-source-import-controls/v1"]
        need(len(rows)==1 and rows[0]["tests"]==25 and rows[0]["skipped"]==0 and
             rows[0]["all_tests_passed"] is True and rows[0]["synthetic_source_fixture_only"] is True and
             rows[0]["runtime_admission_rejected"] is True,"actual25 imported-source controls and prepared rejection")
        for r in refs:checked(r)
        report.update(software_pass=True,same_image=True,scope="prepared actual-source imports with explicit synthetic source fixture; not actual bound-source validation or NPU")
    except BaseException as e:
        report["primary"]=dict(type=type(e).__name__,message=str(e))
    finally:
        ins=cmd(["docker","inspect",name])
        if ins["exit"]==0:
            d=json.loads(ins["stdout"])[0]
            need(d["Config"]["Labels"].get("bole.prepared.cpu")==tag and d["Image"]==IMAGE,"only own exact container cleanup")
            cid=d["Id"]
            if d["State"]["Running"]:report["stop"]=cmd(["docker","stop","-t","10",cid],30)
            final=cmd(["docker","inspect",cid]);need(final["exit"]==0,"terminal inspect")
            d=json.loads(final["stdout"])[0]
            report["after"]=dict(id=cid,state=d["State"],devices=d["HostConfig"].get("Devices"),device_requests=d["HostConfig"].get("DeviceRequests"))
            need(not d["State"]["Running"] and d["State"]["Pid"]==0,"owned CPU terminal release")
        report["finished_epoch"]=time.time()
        with (out/"RESULT.json").open("x") as f:json.dump(report,f,sort_keys=True);f.write("\n");f.flush();os.fsync(f.fileno())
    print(json.dumps(dict(output=str(out/"RESULT.json"),primary=report["primary"],software_pass=report.get("software_pass",False),same_image=report.get("same_image",False),NPU=False)))
    if report["primary"] is not None:raise SystemExit(1)
if __name__=="__main__":main()
