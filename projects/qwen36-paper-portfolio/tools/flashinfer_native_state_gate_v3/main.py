#!/usr/bin/env python3
"""Default-OFF single entry for ABI/numerics/source audit/actual receipt consumer."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
from contract import *
def parser():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
 for flag in ("host-execute","inside-canary","execute","inspect-abi","source-audit-only","consume"):g.add_argument("--"+flag,action="store_true")
 for stem in ("source-manifest","launch-proof","terminal","execution-authority","report"):
  p.add_argument("--"+stem,type=Path);p.add_argument("--"+stem+"-sha256")
 p.add_argument("--output-dir",type=Path);p.add_argument("--host-output-root",type=Path);p.add_argument("--expected-peer")
 return p
def cgroup_memory():
 choices=[Path("/sys/fs/cgroup/memory.max"),Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")]
 p=next((x for x in choices if x.is_file()),None);require(p is not None,"actual guest memory cgroup control")
 text=p.read_text().strip();require(text.isdigit() and int(text)==8*1024**3,"actual guest exact8GiB")
 return {"path":str(p),"value":int(text),"proc_cgroup":Path("/proc/self/cgroup").read_text()}
def run_device(a,source,files):
 require(all((a.launch_proof,a.launch_proof_sha256,a.output_dir)),"MAIN exact launch Ref and unique output required")
 lr=bound(a.launch_proof,a.launch_proof_sha256);launch=load_ref(lr)
 expected_argv=[sys.executable,"-B",*sys.argv]
 validate_launch(launch,source,files,expected_argv,launch_ref=lr)
 require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","logical0/no bytecode")
 require(all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")),"actual one CPU library threads")
 require(len(os.sched_getaffinity(0))==1,"actual guest singleton affinity, not os.cpu_count")
 cg=cgroup_memory()
 out=a.output_dir
 require(out.is_absolute() and ".." not in out.parts and Path("/flashinfer-results") in out.parents and not out.exists() and out.parent.is_dir(),"new owned /flashinfer-results leaf; no overwrite/retry")
 out.mkdir(exist_ok=False);started=time.monotonic();deadline=min(started+5280,started+(datetime.fromisoformat(CUT)-datetime.now(timezone.utc)).total_seconds()-120)
 require(deadline>started,"fixed portfolio cutoff cleanup reserve")
 process={"pid":os.getpid(),"argv":expected_argv,"cmdline_sha256":hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest(),
   "cgroup":Path("/proc/self/cgroup").read_text(),"stat":Path("/proc/self/stat").read_text()}
 report={"schema":"flashinfer.native-state-numerics/v3","status":"running","claim":"native attention-state substrate kernel gate only",
   "source_manifest":source,"sources_before":files,"launch_proof":lr,"launch_identity":launch,
   "protocol":protocol(),"started_utc":datetime.now(timezone.utc).isoformat(),"script_sha256":sha(__file__),"actual_container_process":process,"cgroup":cg,"cases":[],
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
   p=out/(coords+"-progress.json");p.write_bytes(canonical({"schema":"flashinfer.native-state-progress/v3","coordinates":coords,
      "completed_steps":len(case["steps"]),"pending_raw_step":case.get("pending_raw_step")})+b"\n")
 try:
  import torch,torch_npu
  torch.set_num_threads(1)
  from vllm_ascend.utils import enable_custom_op
  from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
  torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
  require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual physical6-only logical0")
  require(enable_custom_op(),"actual native bootstrap");init_device_properties_triton()
  from native import resolve
  exports,mapped=resolve(torch,torch_npu,launch)
  abi_ref=write_new(out/"ABI.json",{"schema":"flashinfer.actual-native-abi/v3","image_id":IMAGE,
    "source_manifest":source,"sources":files,"launch_proof":lr,"actual_stack":launch["stack"],
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
   print("MAIN_FLASHINFER_NATIVE_STATE_V3_REPORT "+json.dumps({"report":rr,"status":report["status"],
      "source_manifest":source,"producer_script_sha256":sha(__file__),"launch_proof":lr}),flush=True)
def main(argv=None):
 a=parser().parse_args(argv)
 if not (a.host_execute or a.inside_canary or a.execute or a.inspect_abi or a.source_audit_only or a.consume):
  print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
      "actual_deployment_ABI_source_host_producer_and_numerics_pending":True}));return 0
 require(a.source_manifest and a.source_manifest_sha256,"complete source Ref required")
 source,files=source_identity(a.source_manifest,a.source_manifest_sha256)
 if a.source_audit_only:
  print(json.dumps({"source_audit_passed":True,"source_manifest":source,"files":files,"npu_executed":False,"serving_ready":False}));return 0
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
