#!/usr/bin/env python3
"""Default-OFF single entry for ABI/numerics/source audit/actual receipt consumer."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
from contract import *
def parser():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
 for flag in ("host-execute","no-device-abi","inside-canary","execute","inspect-abi","source-audit-only","consume"):g.add_argument("--"+flag,action="store_true")
 for stem in ("source-manifest","launch-proof","terminal","execution-authority","report","no-device-abi-ref"):
  p.add_argument("--"+stem,type=Path);p.add_argument("--"+stem+"-sha256")
 p.add_argument("--output-dir",type=Path);p.add_argument("--host-output-root",type=Path);p.add_argument("--expected-peer")
 return p
def cgroup_memory():
 choices=[Path("/sys/fs/cgroup/memory.max"),Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")]
 p=next((x for x in choices if x.is_file()),None);require(p is not None,"actual guest memory cgroup control")
 text=p.read_text().strip();require(text.isdigit() and int(text)==8*1024**3,"actual guest exact8GiB")
 return {"path":str(p),"value":int(text),"proc_cgroup":Path("/proc/self/cgroup").read_text()}
def no_device_abi(a,source,files):
 require(a.output_dir==Path("/flashinfer-results") and a.output_dir.is_dir(),"owned exact ABI output alias required")
 require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1",
  "explicit no-autoload/no-bytecode before Torch import")
 require(all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")) and
  len(os.sched_getaffinity(0))==1,"actual no-device guest one CPU/threads")
 cg=cgroup_memory();out=a.output_dir/"NO_DEVICE_ABI.json";require(not out.exists(),"new immutable no-device ABI path; never overwrite")
 def nodes():
  return sorted(str(p) for p in Path("/dev").iterdir() if p.name.startswith("davinci") or p.name in ("devmm_svm","hisi_hdc"))
 def inventory():
  rows=[]
  for fd in Path("/proc/self/fd").iterdir():
   try:target=os.readlink(fd)
   except FileNotFoundError:continue
   if __import__("re").fullmatch(r"/dev/davinci[0-9]+",target):rows.append({"fd":fd.name,"target":target})
  return sorted(rows,key=lambda x:x["fd"])
 device_nodes=nodes();require(device_nodes==[],"actual CPU guest has Ascend nodes; not isolated no-device")
 before=inventory();require(before==[],"actual no-device entry already holds compute FD")
 report={"schema":"flashinfer.no-device-native-abi/v5","status":"running","source_manifest":source,
  "sources_before":files,"sources_after":None,"image_id":IMAGE,"script_sha256":sha(__file__),
  "native_script_sha256":files["native.py"],"actual_argv":[sys.executable,"-B",*sys.argv],
  "pid":os.getpid(),"process_cgroup":Path("/proc/self/cgroup").read_text(),"affinity":sorted(os.sched_getaffinity(0)),
  "cgroup":cg,"actual_guest_device_nodes_before":device_nodes,"actual_guest_device_nodes_after":None,"device_inventory_before":before,"device_inventory_after":None,
  "device_initialized_before":None,"device_initialized_after":None,
  "primary_error":None,"secondary_errors":[],"npu_executed":False,"numerical_verified":False,"serving_ready":False}
 primary=None
 try:
  import torch,torch_npu,importlib.metadata,importlib.util
  from native import uninitialized,inspect_schemas
  uninitialized(torch_npu);report["device_initialized_before"]=False
  torch.set_num_threads(1)
  report["actual_exports"]=inspect_schemas(torch)
  spec=importlib.util.find_spec("vllm_ascend")
  require(spec and spec.submodule_search_locations and len(spec.submodule_search_locations)==1,"actual installed Ascend package root")
  cp=Path(spec.submodule_search_locations[0])/"attention/context_parallel"
  from host import cann_version_source,H
  vp,version=cann_version_source()
  native=Path(torch_npu._C.__file__)
  report["actual_imported_origins"]={name:bound(module.__file__,sha(module.__file__)) for name,module in (("torch",torch),("torch_npu",torch_npu))}
  report["actual_stack"]={"vllm_ascend":importlib.metadata.version("vllm-ascend"),
   "torch":torch.__version__,"torch_npu":torch_npu.__version__,"cann":version}
  report["actual_runtime_sources"]={alias:bound(path,sha(path)) for alias,path in
   (("attention_cp",cp/"attention_cp.py"),("common_cp",cp/"common_cp.py"),
    ("torch_npu_library",native),("vllm_ascend_library",H.NATIVE),("cann_version",vp),
    ("cann_env","/usr/local/Ascend/cann-9.1.0/set_env.sh"))}
  mapped={}
  for line in Path("/proc/self/maps").read_text().splitlines():
   fields=line.split()
   if len(fields)>=6 and fields[-1].startswith("/") and ".so" in fields[-1] and any(v in fields[-1].lower() for v in ("torch_npu","opapi","vllm")):
    p=Path(fields[-1])
    if p.is_file() and not p.is_symlink():mapped[str(p)]=sha(p)
  report["actually_mapped_libraries"]=mapped
  uninitialized(torch_npu);report["device_initialized_after"]=False
  report["actual_guest_device_nodes_after"]=nodes();require(report["actual_guest_device_nodes_after"]==[],"CPU guest Ascend nodes unexpectedly appeared")
  report["device_inventory_after"]=inventory();require(report["device_inventory_after"]==[],"actual schema-only entry created compute FD")
  _,report["sources_after"]=source_identity(a.source_manifest,a.source_manifest_sha256)
  report["status"]="actual-schema-checked";validate_no_device_abi(report,source,files)
 except BaseException as error:
  primary=error;report.update(status="failed",primary_error=repr(error))
 finally:
  try:
   _,report["sources_after"]=source_identity(a.source_manifest,a.source_manifest_sha256)
   require(report["sources_after"]==files,"actual no-device sources drift")
   report["device_inventory_after"]=inventory();report["actual_guest_device_nodes_after"]=nodes()
  except BaseException as error:report["secondary_errors"].append(repr(error))
  if report["secondary_errors"]:report["status"]="failed"
  report["ended_utc"]=datetime.now(timezone.utc).isoformat()
  ref=write_new(out,report)
  print("MAIN_FLASHINFER_NATIVE_STATE_V5_NO_DEVICE "+json.dumps({"no_device_abi":ref,"status":report["status"],
   "source_manifest":source,"entry_script_sha256":files["main.py"]}),flush=True)
 if primary is not None:raise primary
 require(not report["secondary_errors"],"actual no-device secondary errors retained")
 return ref
def run_device(a,source,files):
 require(all((a.launch_proof,a.launch_proof_sha256,a.output_dir)),"MAIN exact launch Ref and unique output required")
 lr=bound(a.launch_proof,a.launch_proof_sha256);launch=load_ref(lr)
 expected_argv=[sys.executable,"-B",*sys.argv]
 validate_launch(launch,source,files,expected_argv,launch_ref=lr)
 ndref=launch["evidence"]["no_device_abi"];nd=validate_no_device_abi(load_ref(ndref),source,files)
 require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","logical0/no bytecode")
 require(all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")),"actual one CPU library threads")
 require(len(os.sched_getaffinity(0))==1,"actual guest singleton affinity, not os.cpu_count")
 cg=cgroup_memory()
 out=a.output_dir
 require(out.is_absolute() and ".." not in out.parts and Path("/flashinfer-results") in out.parents and not out.exists() and out.parent.is_dir(),"new owned /flashinfer-results leaf; no overwrite/retry")
 out.mkdir(exist_ok=False);started=time.monotonic();deadline=min(started+5280,started+(datetime.fromisoformat(CUT)-datetime.now(timezone.utc)).total_seconds()-120)
 require(deadline>started,"fixed portfolio cutoff cleanup reserve")
 process={"pid":os.getpid(),"argv":expected_argv,"cmdline_sha256":hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest(),
   "cgroup":Path("/proc/self/cgroup").read_text(),"stat":Path("/proc/self/stat").read_text()}
 report={"schema":"flashinfer.native-state-numerics/v5","status":"running","claim":"native attention-state substrate kernel gate only",
   "source_manifest":source,"sources_before":files,"launch_proof":lr,"launch_identity":launch,
   "protocol":protocol(),"started_utc":datetime.now(timezone.utc).isoformat(),"script_sha256":sha(__file__),"actual_container_process":process,"cgroup":cg,"no_device_abi":ndref,"cases":[],
   "npu_executed":None,"npu_execution_state":"not-yet-dispatched","serving_ready":False,"model_lifecycle_verified":False}
 primary=None;abi_ref=None;case_progress_refs=[]
 def save_report():
  require(out.resolve()==out and not out.is_symlink(),"exact owned result directory")
  (out/"report.json").write_bytes(canonical(report)+b"\n")
 def save_case(case):
  coords="b%d-q%d-%s-t%d"%(case["batch"],case["query_width"],case["mode"],case["trial"])
  # Per-case full evidence is written once per terminal transition; the
  # running progress receipt is small and preserves pending checkpoint Ref.
  if case["status"] in ("passed","failed"):
   path=out/(coords+".json");path.write_bytes(canonical(case)+b"\n")
  else:
   p=out/(coords+"-progress.json");p.write_bytes(canonical({"schema":"flashinfer.native-state-progress/v5","coordinates":coords,
      "completed_steps":len(case["steps"]),"pending_raw_step":case.get("pending_raw_step")})+b"\n")
 try:
  import torch,torch_npu
  from native import verify_preinit
  preinit=verify_preinit(torch,torch_npu,nd)
  report["preinit_actual_exports"]=preinit
  torch.set_num_threads(1)
  from vllm_ascend.utils import enable_custom_op
  from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
  torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
  require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual physical6-only logical0")
  require(enable_custom_op(),"actual native bootstrap");init_device_properties_triton()
  from native import resolve
  exports,mapped=resolve(torch,torch_npu,launch)
  abi_ref=write_new(out/"ABI.json",{"schema":"flashinfer.actual-native-abi/v5","image_id":IMAGE,
    "source_manifest":source,"sources":files,"launch_proof":lr,"no_device_abi":ndref,"preinit_actual_exports":preinit,"actual_stack":launch["stack"],
    "actual_exports":exports,"actually_mapped_libraries":mapped,"natural_log_lse":True,
    "public_api_family_source":"vllm-ascend/v0.23.0 attention_cp.py/common_cp.py",
    "bnsd_out_lse_support_numerically_verified":False,"npu_graph_support_verified":False,
    "npu_device_context_created":True,"serving_ready":False})
  report["actual_native_abi"]=abi_ref;report["actual_exports"]=exports;report["actually_mapped_libraries"]=mapped
  save_report()
  if a.inspect_abi:
   report["status"]="actual-schema-only-numerics-pending"
  else:
   from numerics import run_case
   for batch in range(1,17):
    for qw in (1,4):
     for mode,trial in MODES:
      require(time.monotonic()<deadline,"bounded original phase/cutoff; no retry")
      report["npu_execution_state"]="native-numerics-attempt-started"
      report["active_case"]="b%d-q%d-%s-t%d"%(batch,qw,mode,trial);save_report()
      case=run_case(torch,torch.device("npu:0"),out,batch,qw,mode,trial,save_case,deadline)
      coords="b%d-q%d-%s-t%d"%(batch,qw,mode,trial)
      cr=bound(out/(coords+".json"),sha(out/(coords+".json")))
      report["cases"].append({k:case[k] for k in ("batch","query_width","mode","trial")}|{"actual_case_ref":cr})
      report["npu_executed"]=True;report["npu_execution_state"]="actual-case-completed";save_report()
   report["status"]="passed";report["completeness"]=validate_cases(report)
  report["unverified"]=["FlashInfer native load-balanced scheduling/tiling deficiency","real vLLM TP4/16FA48GDN allocator/model consumer",
    "matched fixed1024 C16 benefit","final no-thinking2048 normalEOS C32 tasks","MAIN original terminal/PID/owned-stop authority separate"]
 except BaseException as error:
  primary=error;report.update(status="failed",error=repr(error))
  if report.get("active_case"):
   cp=out/(report["active_case"]+".json")
   if cp.is_file():report["failure_case_ref"]=bound(cp,sha(cp))
  raise
 finally:
  report["ended_ns"]=time.time_ns();report["phase_elapsed_seconds"]=time.monotonic()-started
  try:
   _,after=source_identity(a.source_manifest,a.source_manifest_sha256);report["sources_after"]=after
   require(after==files,"actual complete source before/after")
   save_report()
  except BaseException as secondary:
   if primary is None:
    report.update(status="failed",error=repr(secondary))
    try:save_report()
    except BaseException as save_error:print(json.dumps({"original_error":repr(secondary),"save_error":repr(save_error)}),flush=True)
    raise
   report["secondary_finalize_error"]=repr(secondary)
   try:save_report()
   except BaseException as save_error:print(json.dumps({"original_error":repr(primary),"secondary_error":repr(secondary),"save_error":repr(save_error)}),flush=True)
  if (out/"report.json").is_file():
   rr=bound(out/"report.json",sha(out/"report.json"))
   print("MAIN_FLASHINFER_NATIVE_STATE_V5_REPORT "+json.dumps({"report":rr,"status":report["status"],
      "source_manifest":source,"producer_script_sha256":sha(__file__),"launch_proof":lr}),flush=True)
def main(argv=None):
 a=parser().parse_args(argv)
 if not (a.host_execute or a.no_device_abi or a.inside_canary or a.execute or a.inspect_abi or a.source_audit_only or a.consume):
  print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
      "actual_deployment_ABI_source_host_producer_and_numerics_pending":True}));return 0
 require(a.source_manifest and a.source_manifest_sha256,"complete source Ref required")
 source,files=source_identity(a.source_manifest,a.source_manifest_sha256)
 if a.source_audit_only:
  print(json.dumps({"source_audit_passed":True,"source_manifest":source,"files":files,"npu_executed":False,"serving_ready":False}));return 0
 if a.no_device_abi:
  no_device_abi(a,source,files);return 0
 if a.host_execute or a.inside_canary:
  from host import execute,inside_canary
  if a.host_execute:execute(a,source,files)
  else:inside_canary(a,source,files)
  return 0
 if a.consume:
  from consumer import consume
  print(json.dumps(consume(a,source,files),sort_keys=True));return 0
 run_device(a,source,files);return 0
if __name__=="__main__":sys.exit(main())
