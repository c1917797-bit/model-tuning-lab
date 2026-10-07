#!/usr/bin/env python3
"""In-memory MAIN-only four-group KVBuffer launcher draft; default OFF. Never a service authority."""
import argparse, hashlib, importlib.util, json, math, os, re, shutil, stat, subprocess, sys, time, traceback, types
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
RESULT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006")
BASE=PROJECT/"tools/split_dispatch_v1"
RUNNER=PROJECT/"tools/middle_batch_gate_v1/run.py"
SPLIT_PACKET_SHA="eb2fd0cae186db8b73749255bc8f1ceba5ef1d57f67e2a557126b8bbb37517a9"
RUNNER_SHA="16ed62857871e4576694802bd45afb2a3ec70d726f90f2687860689b92ef3a10"
GROUPS={4:(2,14,15),5:(7,11,13),6:(3,4,9,12),7:(5,6,8,10)}
RELEASE_GROUPS={4:(1,8,9,16),5:(2,7,10,15),6:(3,6,11,14),7:(4,5,12,13)}
OWNER="kvbuffer-middle-main-v1"; PORTFOLIO_DEADLINE="2026-10-09T11:17:31Z"; GIB=1024**3
MEMORY=8*GIB; RESERVE=8*GIB
RELEASE_DIR=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v2"
RELEASE_PINS={
 str(RELEASE_DIR/"v2_release.py"):"e60e399cc2710796d8e9c2b6c418bbf2063ba05f9a93e1b87d4a47e55844fb0b",
 str(RELEASE_DIR/"v2_contract.py"):"666b0e8956cb371b8c03bcba8fa51dd4d4eec207108366e06590fe7a763e3815",
 str(ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v1/diag_contract.py"):"b1d6096bb5852a8de3c500e0519c1f95e78e6ea078e279c3f1c5a49929860c11"}
META14_REF=dict(path=str(RESULT/"preflight-middle-meta14-v1/results/report.json"),sha256="1c417ac0cae44e11842bd2a9434acd1cf537568f2bf19878ebb19dca64c65e75")
def require(ok,why):
 if not ok:raise ValueError(why)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def closure():
 require(hashlib.sha256(RUNNER.read_bytes()).hexdigest()==RUNNER_SHA,"NEW runner drift")
 packet=json.loads((BASE/"PACKET.json").read_text())
 for n,h in packet["sources"].items():
  require(hashlib.sha256((BASE/n).read_bytes()).hexdigest()==h,"existing split producer drift")
 original=load(BASE/"controller.py","_main_middle_original_dispatch")
 packet,pins,producer,bridge,split,host,fh=original.source_audit(SPLIT_PACKET_SHA)
 middle=load(RUNNER,"_main_middle_driver")
 here=RUNNER.parent
 drivers={str(p.relative_to(here)):original.c.sha(p) for p in sorted(here.rglob("*"))
          if p.is_file() and "__pycache__" not in p.parts}
 require(drivers=={"run.py":RUNNER_SHA},"review NEW runtime closure again if directory grows")
 require(all(original.c.sha(p)==h for p,h in RELEASE_PINS.items()),"shared release source closure drift/missing")
 return original,original.c,packet,{**pins,str(BASE/"PACKET.json"):SPLIT_PACKET_SHA,str(RUNNER):RUNNER_SHA,**RELEASE_PINS},bridge,split,host,fh,middle,drivers
def spec(card,slug):
 name="kvbuffer_middle_c%d_%s"%(card,slug.replace("-","_")); root=RESULT/("middle-main-"+slug)/("card%d"%card)
 mounts=[(str(ROOT),str(ROOT),True),(str(RESULT/"build-p1-v1"),"/kvbuffer-results/build-p1-v1",True),
         (str(RESULT/"meta-p1-v1"),"/kvbuffer-results/meta-p1-v1",True),(str(root/"results"),"/kvbuffer-results",False),
         (str(root/"launch"),"/kvbuffer-launch",True),("/usr/local/Ascend/driver","/usr/local/Ascend/driver",True)]
 argv=["/usr/bin/docker","create","--name",name,"--label","model-tuning-lab.owner="+OWNER,
       "--label","model-tuning-lab.joint="+slug,"--label","model-tuning-lab.group="+str(card),
       "--network","none","--memory","8g","--memory-swap","8g","--cpus","1","--cap-drop","ALL",
       "--security-opt","no-new-privileges","--device","/dev/davinci%d:/dev/davinci0"%card]
 for n in ("davinci_manager","devmm_svm","hisi_hdc"):argv+=["--device","/dev/"+n+":/dev/"+n]
 for source,target,ro in mounts:argv+=["--mount","type=bind,source=%s,target=%s%s"%(source,target,",readonly" if ro else "")]
 argv+=["-e","ASCEND_RT_VISIBLE_DEVICES=0","-e","PYTHONDONTWRITEBYTECODE=1","-e","OMP_NUM_THREADS=1",
        "-e","KVBUFFER_MIDDLE_BATCH_EXECUTE=1","-w",str(ROOT),"--entrypoint","/bin/bash",
        "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1","-c","exec sleep infinity"]
 return dict(physical_card=card,batches=list(GROUPS[card]),container_name=name,job_root=str(root),
             launch_root=str(root/"launch"),output_root=str(root/"results"),create_argv=argv)
def raw_ceiling(card):
 t=max(GROUPS[card]);payload=5195776*(t+3)+22688*t+5640
 return ((payload+16*1024**2+4095)//4096)*4096 # FP32 output upper bound + explicit serialization policy.
def disk_need(seconds):
 return RESERVE+sum(raw_ceiling(k) for k in GROUPS)+4*64*1024**2+math.ceil(seconds/30)*4*4*1024**2
def checked_spec(entry,job,cid,c,owner=OWNER):
 require(entry["Id"]==cid and re.fullmatch("[0-9a-f]{64}",cid) and
         entry["Image"]==c.IMAGE and entry["Name"]=="/"+job["container_name"],"exact source-bound owned container")
 h=entry["HostConfig"];config=entry["Config"];argv=job["create_argv"]
 require(h.get("Privileged") is False and h.get("Memory")==MEMORY and h.get("MemorySwap")==MEMORY and
  h.get("NanoCpus")==10**9 and h.get("NetworkMode")=="none" and h.get("IpcMode")!="host" and
  not h.get("DeviceRequests") and set(h.get("CapDrop",[]))=={"ALL"} and
  any(s in ("no-new-privileges","no-new-privileges=true") for s in h.get("SecurityOpt",[])),"actual bounded nonprivileged worker")
 labels=dict(argv[i+1].split("=",1) for i,x in enumerate(argv) if x=="--label")
 require(labels.get("model-tuning-lab.owner")==owner and
         all((config.get("Labels") or {}).get(k)==v for k,v in labels.items()),"actual explicit owner/joint/group")
 devices={p.split(":")[0]:p.split(":")[1] for i,x in enumerate(argv) if x=="--device" for p in [argv[i+1]]}
 require(len(h.get("Devices",[]))==len(devices)==4 and
  {d["PathOnHost"]:d["PathInContainer"] for d in h["Devices"]}==devices and
  devices.get("/dev/davinci%d"%job["physical_card"])=="/dev/davinci0","physical4-7 single-card map only")
 mounts={}
 for i,x in enumerate(argv):
  if x=="--mount":
   v=argv[i+1].split(",");f=dict(s.split("=",1) for s in v if "=" in s);mounts[f["target"]]=(f["source"],"readonly" not in v)
 require(len(entry["Mounts"])==len(mounts),"complete actual mounts")
 for m in entry["Mounts"]:
  require(m.get("Type")=="bind" and m["Destination"] in mounts,"unexpected mount")
  s,rw=mounts[m["Destination"]];require(Path(m["Source"]).resolve()==Path(s).resolve() and m["RW"] is rw,"exact mount permissions")
 require(config.get("WorkingDir")==str(ROOT) and config.get("Entrypoint")==["/bin/bash"] and
  config.get("Cmd")==["-c","exec sleep infinity"],"actual worker starter")
 env=dict(x.split("=",1) for x in config.get("Env",[]) if "=" in x)
 require(all(env.get(k)==v for k,v in {"ASCEND_RT_VISIBLE_DEVICES":"0","PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"1"}.items()),"visible/thread/bytecode constraints")
 for i,x in enumerate(argv):
  if x=="-e":
   k,v=argv[i+1].split("=",1);require(env.get(k)==v,"source-bound explicit environment drift")
 return entry
def release_helper(c):
 # Shared reviewed calibration helper, not a second release protocol or RPC reconstruction.
 require(all(c.sha(p)==h for p,h in RELEASE_PINS.items()),"reviewed shared release source drift/missing")
 path=RELEASE_DIR/"v2_contract.py";existing=sys.modules.get("v2_contract")
 require(existing is None or Path(existing.__file__).resolve()==path,"unrelated v2_contract already loaded")
 if str(RELEASE_DIR) not in sys.path:sys.path.insert(0,str(RELEASE_DIR))
 contract=importlib.import_module("v2_contract")
 require(Path(contract.__file__).resolve()==path and c.sha(path)==RELEASE_PINS[str(path)],"actual shared contract module identity")
 helper=load(RELEASE_DIR/"v2_release.py","_main_kvbuffer_shared_release")
 require(helper.v1() is contract.v1(),"shared original frozen diag module identity")
 return helper
def release_guard(config,cmd,c,host):
 require(config.get("release_authority_kind")=="host_job_cleanup_observed",
         "MAIN explicit host-job cleanup authority required; aged RPC is not an automatic fallback")
 h=release_helper(c)
 require(config.get("release_helper_sources")==RELEASE_PINS,"MAIN exact reviewed shared release source authority")
 expected_refs=[dict(path=str(h.ROOT/"launch"/name),sha256=digest) for name,digest in h.HOST_REFS.items()]
 require(config.get("release_host_job_refs")==expected_refs,"MAIN explicit actual host-job immutable Ref set")
 require(config.get("release_plan")==dict(path=str(h.ROOT/"launch/EXECUTION_PLAN.json"),sha256=h.PLAN_SHA) and
         config.get("release_admission")==dict(path=str(h.ROOT/"admission.json"),sha256=h.ADMISSION_SHA) and
         config.get("release_stops")==dict(path=str(h.ROOT/"launch/STOP_RETAIN.json"),sha256=h.HOST_REFS["STOP_RETAIN.json"]),
         "exact original plan/admission/stop Refs; never a substitute terminal")
 authority=h.host_job()
 require(authority["authority_kind"]=="host_job_cleanup_observed" and
         authority["references"]==expected_refs and authority["awmcp_terminal_reconstructed"] is False and
         authority["numerical_pass_claimed"] is False,"shared host-job release-only scope")
 expected_proofs=[dict(path=str(h.ROOT/("physical%d"%card)/"device-proof.json"),sha256=h.SHAS[card]) for card in GROUPS]
 require(config.get("release_device_proofs")==expected_proofs,"MAIN explicit four actual producer device proofs")
 refs,proofs=h.references([r["path"] for r in expected_proofs],[r["sha256"] for r in expected_proofs])
 proc_before=h.no_exec_clients() # Fresh exact original-CID host-client scan, not historical PID invention.
 plan=c.clean(c.read_ref(config["release_plan"]));admission=c.clean(c.read_ref(config["release_admission"]));stops=c.clean(c.read_ref(config["release_stops"]))
 require(len(plan["shards"])==len(stops)==4 and set(admission["cards"])==set(map(str,GROUPS)),"actual four source-bound prior leases")
 byid={v["id"]:v for v in stops};ids=set();observed=[];inspects={}
 for e in plan["shards"]:
  card=e["physical_card"];require(e["batches"]==list(RELEASE_GROUPS[card]),"actual MA070e balanced groups, not another prior job")
  a=admission["cards"][str(card)];cid=a["container_id"];ids.add(cid)
  require(e["container_name"]==a["container_name"] and e["create_argv_sha256"]==a["create_argv_sha256"] and
          c.digest(c.canonical(e["docker_create_argv"]))==e["create_argv_sha256"],"prior actual create lease identity")
  stop=byid.get(cid,{});require(stop.get("name")==e["container_name"] and stop.get("status") in ("exited","created") and stop.get("deleted") is False,"actual retained prior stop record")
  actual=cmd.json("prior-stopped-inspect",["/usr/bin/docker","inspect",cid])[0]
  host.inspect_proof(actual,e,cid) # Exact frozen full CPU/RAM/mount/argv lease inspector remains required.
  require(actual["State"].get("Running") is False and actual["State"].get("Pid")==0,"prior must actually be stopped; never stop unrelated/live parent")
  inspects[cid]=actual;observed.append(dict(id=cid,actual_state=actual["State"]))
 require(len(ids)==4,"four unique prior leases")
 stopped=h.stopped(proofs,inspects.get);proc_after=h.no_exec_clients()
 return dict(authority=authority,source_helpers=RELEASE_PINS,device_proofs=refs,stopped=stopped,
             full_lease_inspects=observed,fresh_host_exec_scans=[proc_before,proc_after],
             rpc_terminal_reconstructed=False,scope="release only, not numerical PASS")
def gate_argv(job,cid,c):
 return ["/usr/bin/docker","exec",cid,"/bin/bash","-c",c.WAIT,"kvbuffer-middle-await-c"+str(job["physical_card"]),
         "/kvbuffer-launch/RELEASE",c.PYTHON,"-B",str(RUNNER),"--execute","--batches",*map(str,job["batches"]),
         "--physical-device",str(job["physical_card"]),"--identity","/kvbuffer-launch/identity.json","--output-dir","/kvbuffer-results/gate"]
def actual_pid(pid,cid,host,argv):
 row=host.owner_pid(pid,cid);actual=[s.decode() for s in Path("/proc",str(pid),"cmdline").read_bytes().split(b"\0") if s]
 require(actual==argv,"actual exact process argv")
 text=Path("/proc",str(pid),"status").read_text();m=re.search(r"^NSpid:\s+([0-9 \t]+)$",text,re.M)
 require(m and list(map(int,m[1].split()))[0]==pid,"actual host/namespace PID chain")
 return {**row,"argv":actual,"namespace_pids":list(map(int,m[1].split()))}
def resources(cmd,c,host,fh,jobs,protected=None,remaining=10800):
 raw,_=cmd.run("fresh-npu-smi",[c.NPU_SMI,"info"]);rows=host.parse_processes(raw);telemetry=fh.telemetry(raw)
 require(set(telemetry)==set(range(8)),"complete fresh real telemetry")
 fingerprint=host.protected_fingerprint(rows);require(protected is None or fingerprint==protected,"protected0-3 identity changed")
 byid={v["id"]:v for v in jobs.values() if "id" in v}
 for card in GROUPS:
  for r in rows[card]:
   j=jobs.get(card);require(j and j.get("waiting") and r["pid"]==j["waiting"]["pid"],"unknown/external real target process")
   native=actual_pid(r["pid"],j["id"],host,j["gate_argv"][j["gate_argv"].index(c.PYTHON):])
   require(native["start_ticks"]==j["waiting"]["start_ticks"],"PID identity changed instead of exec")
   if "actual_gate" not in j:j["actual_gate"]=c.write_new(Path(j["audit"])/"ACTUAL_GATE_NPU_PID.json",dict(process=native,npu_smi=raw,physical_card=card,separate_canary_not_gate=True))
  if not rows[card]:c.idle_card(telemetry[card])
 running,_=cmd.run("live-IDs",["/usr/bin/docker","ps","--quiet","--no-trunc"])
 for cid in running.splitlines():
  e=cmd.json("live-owner-inspect",["/usr/bin/docker","inspect",cid])[0];labels=e["Config"].get("Labels") or {}
  if any(k.startswith("model-tuning-lab.") for k in labels):require(cid in byid,"unknown live MAIN owner; no fake relabel or stop")
 engine=cmd.json("joint-engine",["/usr/bin/docker","info","--format","{{json .}}"]);require(type(engine.get("NCPU")) is int and engine["NCPU"]>=5,"four CPUs plus host reserve")
 meminfo=Path("/proc/meminfo").read_text();m=re.search(r"^MemAvailable:\s*(\d+)\s+kB",meminfo,re.M);require(m,"ordinaryRAM parse")
 available=int(m[1])*1024;growth=0;groups={}
 for card,j in jobs.items():
  if "id" not in j:continue
  e=cmd.json("owned-cgroup-inspect",["/usr/bin/docker","inspect",j["id"]])[0];checked_spec(e,j,j["id"],c)
  require(e["State"]["Running"],"own retained worker unexpectedly stopped")
  cg=host.cgroup_record(e,j["id"],MEMORY,1);require(type(cg["memory_peak_bytes"]) is int and 0<=cg["memory_current_bytes"]<=cg["memory_peak_bytes"]<=MEMORY,"actual cgroup current/peak/cap")
  groups[str(card)]=cg;growth+=MEMORY-cg["memory_current_bytes"]
 need=RESERVE+growth+(4-len(groups))*MEMORY;free=shutil.disk_usage(RESULT).free
 raw_observations=[]
 for card,j in jobs.items():
  files=list((Path(j["output_root"])/"gate").glob("raw-step-*.pt"));require(len(files)<=1,"unexpected raw residency; retain all")
  for p in files:
   try:s=p.lstat()
   except FileNotFoundError:raw_observations.append(dict(path=str(p),concurrently_disappeared=True,passed_inferred=False));continue
   require(stat.S_ISREG(s.st_mode) and s.st_size<=raw_ceiling(card),"actual raw exceeds explicit source-shaped policy; do not delete/clip")
   raw_observations.append(dict(path=str(p),bytes=s.st_size,ceiling=raw_ceiling(card)))
  report=Path(j["output_root"])/"gate/report.json"
  if report.exists():require(report.is_file() and not report.is_symlink() and report.stat().st_size<=64*1024**2,"bounded original report")
 record=dict(observed_ns=time.time_ns(),meminfo=meminfo,available=available,joint_ram_required=need,cgroups=groups,
             free_disk_bytes=free,disk_required=disk_need(remaining),remaining=remaining,npu_smi=raw,protected=fingerprint,
             docker_info=engine,raw_checkpoints=raw_observations)
 c.write_new(cmd.audit/("BUDGET-%d.json"%record["observed_ns"]),record) # actual raw evidence precedes interpreting limits
 require(available>=need and free>=disk_need(remaining),"joint ordinaryRAM/disk budget")
 host.mount_budget(cmd)
 return record
def formal_clock(config,now=None):
 # Separate KVBuffer clock: MAIN supplies the real start; no autonomous signing/reset or DAMP clock mutation.
 start=datetime.fromisoformat(config["formal_start_utc"].replace("Z","+00:00"))
 end=datetime.fromisoformat(config["deadline_utc"].replace("Z","+00:00"))
 portfolio=datetime.fromisoformat(PORTFOLIO_DEADLINE.replace("Z","+00:00"));now=now or datetime.now(timezone.utc)
 require(start.tzinfo is not None and end.tzinfo is not None and now.tzinfo is not None and
  start<=now and 0<(end-start).total_seconds()<=86400 and end<=portfolio,
  "MAIN real KVBuffer formal start/deadline within24h and portfolio; never borrow/reset DAMP clock")
 require(now.timestamp()+600+max(config["phase_seconds"].values())+180<=end.timestamp(),
  "KVBuffer remaining window includes single phase/setup/cleanup; never extend")
 return dict(formal_start=start,deadline=end,portfolio_deadline=portfolio)
def meta14_prerequisite(config,c,packet,split):
 # Actual immutable report only; this positive Meta prerequisite is never an NPU/graph/service authority.
 require(config.get("middle_meta14")==META14_REF,"explicit MAIN-issued actual Meta14 Ref required")
 m=c.clean(c.read_ref(config["middle_meta14"]));old=c.clean(c.read_ref(packet["artifacts"]["meta"]))
 legacy={**{str(BASE/n):h for n,h in packet["sources"].items()},**packet["frozen_dependencies"]}
 require(len(legacy)==49 and m.get("sources_before")==legacy==m.get("sources_after"),"actual complete Meta49 source closure before/after")
 require(m.get("status")=="actual_14_positive_Meta_pass" and "error" not in m and
  m.get("schema")==old["schema"] and m.get("prepare_schema")==old["prepare_schema"],
  "actual decode/prepare Torch schemas; never relabel original schema field")
 require(m.get("library_sha256")==split.LIBRARY_SHA and m.get("build_receipt_sha256")==split.BUILD_SHA and
  type(m.get("loaded_libraries")) is dict and m["loaded_libraries"].get(packet["artifacts"]["library"]["path"])==split.LIBRARY_SHA and
  all(type(p) is str and p.startswith("/") and "(deleted)" not in p and type(h) is str and re.fullmatch("[0-9a-f]{64}",h) for p,h in m["loaded_libraries"].items()),
  "actual mapped candidate SO and build; not schema/source bytes alone")
 require(m.get("meta")==[dict(T=t,slots=t+3,shape=[t,12,128],dtype="torch.bfloat16") for t in range(2,16)] and
  m.get("output_alias_checks") is True,"all14 trueT positive Meta and producer whole-matrix nonalias proof")
 require(all(m.get(k) is False for k in ("npu_executed","physical_nd_proven","graph_proven","service_ready")) and
  m.get("scope")=="actual no-device dynamic load/schema/positive Meta only" and
  m.get("meta_negative_validation")=="not implemented by this unchanged Meta kernel" and
  m.get("torch")==old["torch"] and m.get("torch_npu")==old["torch_npu"],"Meta scope/real image versions; no promotion")
 start=datetime.fromisoformat(m["started_utc"]);end=datetime.fromisoformat(m["completed_utc"])
 require(start.tzinfo is not None and end.tzinfo is not None and start<end,"actual ordered completed Meta timestamps")
 return dict(report=config["middle_meta14"],status=m["status"],positive_batches=list(range(2,16)),
  npu_executed=False,scope="positive Meta prerequisite only; actual device identity/terminal still required")
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-audit",action="store_true");p.add_argument("--inputs");p.add_argument("--inputs-sha256");a=p.parse_args(argv)
 if not a.execute and not a.source_audit:print(json.dumps(dict(status="OFF",npu_executed=False)));return 0
 original,c,packet,pins,bridge,split,host,fh,middle,drivers=closure()
 if a.source_audit:print(json.dumps(dict(status="source-only",source_count=len(pins),groups=GROUPS,npu_executed=False)));return 0
 require(os.environ.get("KVBUFFER_MIDDLE_MAIN_EXECUTE")=="1","MAIN explicit launch opt-in")
 config=c.clean(c.read_ref(dict(path=a.inputs,sha256=a.inputs_sha256)))
 require(config.get("main_approved") is True,"MAIN-issued exact original refs/budgets; preparation never signs formal start")
 slug=config["run_slug"];require(re.fullmatch("[a-z0-9][a-z0-9-]{0,40}",slug),"fresh bounded name")
 phase=config["phase_seconds"];require(set(phase)==set(map(str,GROUPS)) and all(type(v) is int and 1800<=v<=10800 for v in phase.values()),"explicit single-attempt budgets")
 clock=formal_clock(config);end=clock["deadline"]
 procargv=[s.decode() for s in Path("/proc/self/cmdline").read_bytes().split(b"\0") if s];require(procargv.count("-c")==1,"MAIN actual a_exec in-memory script expected")
 program=procargv[procargv.index("-c")+1];program_sha=hashlib.sha256(program.encode()).hexdigest()
 require(config.get("main_program_sha256")==program_sha,"MAIN exact source-reviewed program, no self-issued expected authority")
 meta_prereq=meta14_prerequisite(config,c,packet,split) # Before output creation or any Docker/device action.
 root=RESULT/("middle-main-"+slug);require(not root.exists(),"unique output, no retry/overwrite")
 root.mkdir();audit=root/"audit";audit.mkdir();cmd=original.Commands(audit)
 jobs={k:spec(k,slug) for k in GROUPS};processes={};primary=None;cleaned={}
 adapter=types.SimpleNamespace(**vars(c));adapter.inspect_proof=lambda e,j,i:checked_spec(e,j,i,c)
 stop=types.FunctionType(original.stop_owned.__code__,{**vars(original),"c":adapter},original.stop_owned.__name__,original.stop_owned.__defaults__,original.stop_owned.__closure__)
 class CleanupCommands(original.Commands):
  def run(self,label,argv,timeout=90,allowed=(0,)):
   return super().run(label,argv,min(timeout,25 if argv[:2]==["/usr/bin/docker","stop"] else 5),allowed)
 cleanup_attempted=set();setup_started=time.monotonic()
 def cleanup(j):
  card=j["physical_card"];require(card not in cleanup_attempted,"one exact cleanup attempt, no hidden retry")
  cleanup_attempted.add(card);directory=Path(j["audit"])/"cleanup";directory.mkdir()
  local=CleanupCommands(directory);result=stop(local,j,j["id"])
  cmd.secondary_errors.extend(local.secondary_errors);return result
 def setup_clock():
  require(time.monotonic()-setup_started<=600 and datetime.now(timezone.utc).timestamp()+max(phase.values())+180<=end.timestamp(),"setup budget/deadline, no late release")
 try:
  release=c.write_new(audit/"PARENT_RELEASE.json",release_guard(config,cmd,c,host))
  first=resources(cmd,c,host,fh,jobs,remaining=max(phase.values()));protected=first["protected"]
  c.write_new(audit/"PROGRAM.json",dict(source=program,sha256=program_sha,actual_process_argv=procargv,source_dependencies=pins,inputs=dict(path=a.inputs,sha256=a.inputs_sha256),middle_meta14=meta_prereq))
  for card,j in jobs.items():
   setup_clock()
   original.no_overlap_created_name(cmd,j["container_name"])
   for k in ("job_root","launch_root","output_root"):Path(j[k]).mkdir()
   j["audit"]=str(Path(j["job_root"])/"audit");Path(j["audit"]).mkdir()
   raw,_=cmd.run("create-card%d"%card,j["create_argv"]);cid=raw.strip();require(re.fullmatch("[0-9a-f]{64}",cid),"create ID uncertain; do not infer ownership")
   j["id"]=cid;checked_spec(cmd.json("created-inspect",["/usr/bin/docker","inspect",cid])[0],j,cid,c)
   cmd.run("start-sleep",["/usr/bin/docker","start",cid]);checked_spec(cmd.json("started-inspect",["/usr/bin/docker","inspect",cid])[0],j,cid,c)
   resources(cmd,c,host,fh,jobs,protected,remaining=max(phase.values()))
   j["image_source"]=original.image_sources(cmd,cid,packet)
   canary,_=cmd.run("canary-card%d"%card,["/usr/bin/docker","exec",cid,"/bin/bash","-c",fh.BOOTSTRAP,
      "kvbuffer-middle-separate-canary",c.PYTHON,"-B","-c",fh.CANARY_CODE,str(card),c.digest(c.canonical(j["create_argv"])),fh.CANARY_SHA],timeout=90)
   cv=c.clean(canary);require(cv["status"]=="actual_canary_pass" and cv["expected_physical_card"]==card and
    cv["create_argv_sha256"]==c.digest(c.canonical(j["create_argv"])) and cv["canary_program_sha256"]==fh.CANARY_SHA,"actual separate canary identity")
   j["canary"]=c.ref(cmd.audit/("%04d-canary-card%d.stdout"%(cmd.index,card)))
  for card,j in jobs.items():
   setup_clock()
   cid=j["id"];j["gate_argv"]=gate_argv(j,cid,c);j["stdout"]=str(Path(j["audit"])/"gate.stdout");j["stderr"]=str(Path(j["audit"])/"gate.stderr")
   with Path(j["stdout"]).open("xb") as out,Path(j["stderr"]).open("xb") as err:processes[card]=subprocess.Popen(j["gate_argv"],stdout=out,stderr=err,cwd=str(ROOT))
   j["started"]=time.monotonic();until=time.monotonic()+30
   while time.monotonic()<until:
    text,_=cmd.run("wait-PID",["/usr/bin/docker","top",cid,"-eo","pid,args"]);found=[]
    for line in text.splitlines()[1:]:
     pid,_,args=line.strip().partition(" ")
     if pid.isdigit() and "kvbuffer-middle-await-c"+str(card) in args:found.append(int(pid))
    require(len(found)<=1,"ambiguous wait PID")
    if found:
     j["waiting"]=actual_pid(found[0],cid,host,j["gate_argv"][3:]);break
    time.sleep(.1)
   require("waiting" in j,"actual waiting PID required before release")
   waiting=c.write_new(Path(j["audit"])/"WAIT_PID.json",j["waiting"])
   checked_spec(cmd.json("mapping-inspect",["/usr/bin/docker","inspect",cid])[0],j,cid,c)
   mapping=c.ref(cmd.audit/("%04d-mapping-inspect.stdout"%cmd.index))
   fresh=resources(cmd,c,host,fh,jobs,protected,remaining=max(phase.values()))
   freshref=c.write_new(Path(j["audit"])/"FRESH_PRELAUNCH.json",fresh)
   ident=dict(schema="kvbp.middle-batch-launch-identity/v1",image_id=c.IMAGE,physical_devices=[card],logical_to_physical={"0":card},
       fresh_idle_verified=True,nonprivileged=True,source_canary_passed=True,memory_cgroup_bytes=MEMORY,protocol=middle.protocol(j["batches"],card),
       library_sha256=split.LIBRARY_SHA,
       build_receipt_sha256=split.BUILD_SHA,meta_receipt_sha256=split.META_SHA,repo_sources=split.REPO_PINS,native_sources=split.NATIVE_PINS,
       driver_sources=drivers,native_library_sha256=middle.NATIVE_SO_SHA,preflight_utc=datetime.now(timezone.utc).isoformat(),
       evidence=dict(separate_canary=j["canary"],mapping=mapping,waiting_bash=waiting,host_processes=freshref,image_sources=j["image_source"],parent_release=release,middle_meta14=meta_prereq["report"]),
       observed_role="prelaunch_wait_bash_not_native",actual_gate_process_confirmation_required=True)
   j["identity"]=c.write_new(Path(j["launch_root"])/"identity.json",ident)
   require(all(c.sha(p)==h for p,h in pins.items()),"source drift before exclusive release")
   c.write_new(Path(j["launch_root"])/"RELEASE",dict(identity=j["identity"],main_program_sha256=program_sha,not_a_pass=True))
  last_budget=0
  while any(p.poll() is None for p in processes.values()):
   now=datetime.now(timezone.utc);require(now.timestamp()+180<end.timestamp(),"fixed cleanup reserve")
   for card,p in processes.items():
    if p.poll() is None:require(time.monotonic()-jobs[card]["started"]<=phase[str(card)],"single bounded phase timeout; no retry")
    require(p.poll() in (None,0),"actual original gate nonzero; retain failure before cleanup")
   if time.monotonic()-last_budget>=30:
    remaining=max(max(0,phase[str(k)]-(time.monotonic()-j["started"])) for k,j in jobs.items())
    resources(cmd,c,host,fh,jobs,protected,remaining);last_budget=time.monotonic()
   else:
    raw,_=cmd.run("gate-NPU-PIDs",[c.NPU_SMI,"info"]);rows=host.parse_processes(raw)
    require(host.protected_fingerprint(rows)==protected,"protected0-3 changed")
    for card,j in jobs.items():
     for r in rows[card]:
      require(r["pid"]==j["waiting"]["pid"],"unknown target PID")
      seen=actual_pid(r["pid"],j["id"],host,j["gate_argv"][j["gate_argv"].index(c.PYTHON):]);require(seen["start_ticks"]==j["waiting"]["start_ticks"],"PID reuse")
      if "actual_gate" not in j:j["actual_gate"]=c.write_new(Path(j["audit"])/"ACTUAL_GATE_NPU_PID.json",dict(process=seen,physical_card=card,npu_smi=raw,separate_canary_not_gate=True))
   time.sleep(1)
  for card,j in jobs.items():
   require("actual_gate" in j and processes[card].returncode==0,"actual original zero + NPU PID required")
   reportref=c.ref(Path(j["output_root"])/"gate/report.json");report=c.clean(c.read_ref(reportref,limit=64*1024**2));identity=c.clean(c.read_ref(j["identity"]))
   require(report.get("schema")=="kvbp.intermediate-native-gate/v1" and report.get("status")=="intermediate_batches_kernel_native_eager_graph_pass" and
    "error" not in report and report.get("npu_executed") is True and report.get("serving_ready") is False and
    report.get("performance_measurement_admitted") is False and report.get("launch_identity")==identity and
    report.get("launch_identity_sha256")==j["identity"]["sha256"] and report.get("protocol")==middle.protocol(j["batches"],card),"complete NEW report/identity/scope")
   require(report.get("loaded_libraries",{}).get("/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so")==split.LIBRARY_SHA and
    report.get("loaded_libraries",{}).get(middle.NATIVE_SO)==middle.NATIVE_SO_SHA,"actual mapped two libraries")
   require(len(report["cases"])==4*len(j["batches"]),"no duplicate or omitted true-T cases")
   for t in j["batches"]:bridge.validate_cases({"cases":[v for v in report["cases"] if v["batch"]==t]},t)
   require(all(c.sha(p)==h for p,h in pins.items()),"source drift after gate")
   cleaned[card]=cleanup(j)
   execution=dict(argv=j["gate_argv"],cwd=str(ROOT),exit_code=processes[card].returncode,stdout=c.ref(j["stdout"]),stderr=c.ref(j["stderr"]),
                  report=reportref,identity=j["identity"],actual_gate_pid=j["actual_gate"],cleanup=cleaned[card],source_after={p:c.sha(p) for p in pins},
                  main_program_sha256=program_sha,middle_meta14=meta_prereq,service_ready=False,performance=False)
   child=c.write_new(Path(j["audit"])/"CHILD.json",execution)
   print("MAIN_KVBUFFER_MIDDLE_SHARD "+json.dumps(dict(physical_card=card,batches=j["batches"],child=child,report=reportref)),flush=True)
  raw,_=cmd.run("exact-release-NPUs",[c.NPU_SMI,"info"]);rows=host.parse_processes(raw)
  require(all(not rows[k] for k in GROUPS) and host.protected_fingerprint(rows)==protected,"actual cards released/protected identities unchanged")
  print("MAIN_KVBUFFER_MIDDLE_COMPLETE "+json.dumps(dict(cases=56,feedback_steps=8960,source_after={p:c.sha(p) for p in pins},service_ready=False,performance=False)),flush=True)
  return 0
 except BaseException as e:
  primary=e
  original.secondary("original-launch-failure",lambda:c.write_new(audit/"PRIMARY_FAILURE.json",dict(error=repr(e),traceback=traceback.format_exc(),known_jobs=jobs,source_after={p:c.sha(p) for p in pins},no_retry=True)),cmd.secondary_errors)
  raise
 finally:
  for card,p in processes.items():
   if p.poll() is None:original.secondary("terminate-only-local-docker-client",p.terminate,cmd.secondary_errors)
  for card,j in jobs.items():
   if "id" in j and card not in cleanup_attempted:original.secondary("exact-own-stop-retain",lambda j=j:cleanup(j),cmd.secondary_errors)
  for card,p in processes.items():
   original.secondary("collect-original-client-outcome",lambda p=p:p.wait(timeout=5),cmd.secondary_errors)
   j=jobs[card]
   original.secondary("raw-original-execution",lambda j=j,p=p:c.write_new(Path(j["audit"])/"EXECUTION_FINAL.json",
       dict(argv=j["gate_argv"],cwd=str(ROOT),exit_code=p.returncode,error=None if primary is None else repr(primary),
            stdout=c.ref(j["stdout"]),stderr=c.ref(j["stderr"]),outcome_may_be_incomplete=p.poll() is None)),cmd.secondary_errors)
if __name__=="__main__":raise SystemExit(main())
