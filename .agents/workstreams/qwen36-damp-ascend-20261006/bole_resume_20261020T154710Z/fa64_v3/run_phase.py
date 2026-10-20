"""Bounded owner for BOLE FA64 diagnostics; exact owned container cleanup."""
import argparse,hashlib,json,os,subprocess,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
OUT=Path("/opt/host/vnf/austinov/run-bole-fa64-20261020T154710Z-v3")
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
DOCKER="/usr/bin/docker"
def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open("rb")as f:
  for block in iter(lambda:f.read(8388608),b""):h.update(block)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def write(p,obj):
 with Path(p).open("x")as f:json.dump(obj,f,sort_keys=True,allow_nan=False);f.write("\n")
 return ref(p)
def cmd(args,timeout=30):
 r=subprocess.run([DOCKER,*args],capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise RuntimeError("docker "+args[0]+": "+r.stderr[-2000:])
 return r.stdout.strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("phase",choices=["extract","replay"]);a=ap.parse_args()
 OUT.mkdir(exist_ok=True);out=OUT/a.phase;out.mkdir(exist_ok=False)
 before=ref(P/"fa64_replay.py");inputs=ref(P/"INPUTS.json");cid=None;primary=None
 name="bole-fa64-v3-"+a.phase+"-20261020t154710z"
 args=["create","--name",name,"--network=none","--memory=8g","--memory-swap=8g","--cpus=4","--pids-limit=512",
       "--read-only","--tmpfs=/tmp:rw,size=1073741824","--shm-size=1g",
       "--env","TORCH_DEVICE_BACKEND_AUTOLOAD=0","--env","OMP_NUM_THREADS=4","--env","MKL_NUM_THREADS=4",
       "--env","ASCEND_RT_VISIBLE_DEVICES="+("" if a.phase=="extract" else "0"),
       "--mount","type=bind,src="+str(P)+",dst="+str(P)+",readonly",
       "--mount","type=bind,src="+str(out)+",dst="+str(out)]
 data=json.loads((P/"INPUTS.json").read_text())
 if a.phase=="extract":
  for row in data["raw_ranks"]:
   for key in ("raw","receipt"):
    path=row[key]["path"];args+=["--mount","type=bind,src="+path+",dst="+path+",readonly"]
  guest=[str(P/"fa64_replay.py"),"extract","--inputs-ref",json.dumps(inputs),"--output",str(out/"data")]
 else:
  extraction=json.loads(Path("/opt/host/vnf/austinov/run-bole-fa64-20261020T154710Z-v2/extract/data/EXTRACT.json").read_text())
  frames=extraction["frames"];assert ref(frames["path"])==frames
  args+=["--mount","type=bind,src="+frames["path"]+",dst="+frames["path"]+",readonly"]
  snapshot=subprocess.check_output(["/usr/local/sbin/npu-smi","info"],text=True,timeout=20)
  assert "No running processes found in NPU 4" in snapshot
  (out/"NPU-BEFORE.txt").write_text(snapshot)
  for d in ("/dev/davinci4","/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"):
   assert Path(d).exists();args+=["--device",d+":"+("/dev/davinci0" if d=="/dev/davinci4" else d)]
  args+=["--mount","type=bind,src=/usr/local/Ascend/driver,dst=/usr/local/Ascend/driver,readonly"]
  guest=[str(P/"fa64_replay.py"),"replay","--frames-ref",json.dumps(frames),"--output",str(out/"data")]
 args+=["--cap-drop=ALL","--security-opt=no-new-privileges","--env","ASCEND_PROCESS_LOG_PATH=/tmp/ascend/log","--entrypoint","/bin/bash",IMAGE,"-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"bole-fa64","/usr/local/python3.12.13/bin/python3","-I","-B",*guest]
 admission=dict(phase=a.phase,source=before,inputs=inputs,image=IMAGE,argv=args,
                memory_available_kB=int(next(l.split()[1]for l in Path("/proc/meminfo").read_text().splitlines()if l.startswith("MemAvailable:"))),
                disk_available_bytes=os.statvfs(OUT).f_bavail*os.statvfs(OUT).f_frsize,
                max_memory_GiB=8,reserve_GiB=8,max_seconds=900,physical=[]if a.phase=="extract"else[4])
 assert admission["memory_available_kB"]*1024>17*2**30
 assert admission["disk_available_bytes"]>10*2**30
 write(out/"ADMISSION.json",admission)
 try:
  cid=cmd(args);write(out/"OWNED.json",dict(cid=cid,name=name,image=IMAGE))
  inspect=json.loads(cmd(["inspect",cid]))[0]
  assert inspect["Image"]==IMAGE and not inspect["HostConfig"]["Privileged"]
  actual=inspect["HostConfig"]["Devices"]or[]
  assert not actual if a.phase=="extract" else {d["PathOnHost"]for d in actual}=={"/dev/davinci4","/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"}
  start=time.monotonic()
  try:r=subprocess.run([DOCKER,"start","-a",cid],capture_output=True,text=True,timeout=900)
  except subprocess.TimeoutExpired as e:
   primary="phase timeout";raise
  (out/"stdout.txt").write_text(r.stdout);(out/"stderr.txt").write_text(r.stderr)
  write(out/"CHILD.json",dict(exit_code=r.returncode,elapsed=time.monotonic()-start,stdout=ref(out/"stdout.txt"),stderr=ref(out/"stderr.txt")))
  if r.returncode:raise RuntimeError("guest failed exit="+str(r.returncode))
  assert ref(P/"fa64_replay.py")==before
 except BaseException as e:
  primary=repr(e);write(out/"FAILURE.json",dict(error=primary,traceback=traceback.format_exc()))
 finally:
  if cid:
   state=json.loads(cmd(["inspect",cid,"--format","{{json .State}}"]))
   if state["Running"]:cmd(["stop","-t","10",cid])
   state=json.loads(cmd(["inspect",cid,"--format","{{json .State}}"]))
   write(out/"CLEANUP.json",dict(cid=cid,state=state,retained=True,stopped=not state["Running"],primary=primary))
 if primary:raise RuntimeError(primary)
 print(json.dumps(dict(phase=a.phase,output=str(out),primary=primary)))
if __name__=="__main__":main()
