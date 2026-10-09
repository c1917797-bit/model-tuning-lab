"""Default OFF disjoint producer. Original run_case and every oracle untouched.
Only actual assigned case scope differs; NEVER advertises original128 PASS.
"""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
import shard_contract as sc
def cpu_audit(a,own,manifest):
 c,source,files=sc.native()
 sc.need(not any(Path("/dev").glob("davinci*")),"actual CPU-only Devices[] has no accelerator nodes")
 before=set(sys.modules)
 for filename in sc.OWN:
  compile((sc.ROOT/filename).read_text(),str(sc.ROOT/filename),"exec")
 import unittest
 suite=unittest.defaultTestLoader.loadTestsFromName("test_shards")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 sc.need(result.wasSuccessful(),"actual new packet whole stdlib")
 sc.need(not any(k=="torch" or k.startswith(("torch.","torch_npu")) for k in set(sys.modules)-before),"new CPU software must not initialize/import backend")
 out=Path("/sparq-results/PACKET_CPU.json")
 report=dict(schema="sparq.disjoint4-no-device-packet/v1",status="software-checked",packet_source=own,
  native_source=source,native_files=files,tests=result.testsRun,device_nodes=[],npu_executed=False,
  argv=[sys.executable,"-B",*sys.argv],pid=os.getpid(),ready=False)
 ref=sc.publication(out,report);print("MAIN_SPARQ_DISJOINT_CPU "+json.dumps({"report":ref}),flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
 for flag in ("execute","cpu-audit-only","source-audit-only"):g.add_argument("--"+flag,action="store_true")
 for key in ("source-manifest","output","device-proof","allocation"):p.add_argument("--"+key,type=Path)
 for key in ("source-manifest","device-proof","allocation"):p.add_argument("--"+key+"-sha256")
 p.add_argument("--shard-id",type=int);a=p.parse_args()
 if not (a.execute or a.cpu_audit_only or a.source_audit_only):
  print(json.dumps(dict(status="disabled",ready=False,npu_executed=False)));return
 own,manifest=sc.own_identity(a.source_manifest,a.source_manifest_sha256)
 c,source,files=sc.native()
 if a.source_audit_only:
  print(json.dumps(dict(source=own,native_source=source,ready=False)));return
 if a.cpu_audit_only:return cpu_audit(a,own,manifest)
 plan=json.loads(sc.read_ref(dict(path=str(a.allocation),sha256=a.allocation_sha256)))
 shard=sc.assigned(plan,a.shard_id)
 proof_ref=c.bound(a.device_proof,a.device_proof_sha256)
 argv=[sys.executable,"-B",*sys.argv]
 sc.need(argv==sc.shard_argv(a.output,proof_ref,dict(path=str(a.allocation),sha256=a.allocation_sha256),own,a.shard_id),"single exact new shard image CLI")
 from shard_proof import validate_proof
 proof=validate_proof(a.device_proof,a.device_proof_sha256,source,files,argv)
 sc.need(proof["packet_source"]==own and proof["shard_id"]==a.shard_id and proof["allocation_ref"]==dict(path=str(a.allocation),sha256=a.allocation_sha256),"actual packet/allocation/proof closure")
 packet_cpu=json.loads(sc.read_ref(proof["packet_cpu"]))
 sc.need(packet_cpu["status"]=="software-checked" and packet_cpu["packet_source"]==own and packet_cpu["native_source"]==source and packet_cpu["npu_executed"] is False,"actual same-image packet CPU before canary")
 sc.need(a.output and a.output.is_absolute() and Path("/sparq-results") in a.output.parents and ".." not in a.output.parts and
  not a.output.exists() and a.output.parent.is_dir(),"new exact original owned shard root")
 sc.need(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
  os.environ.get("PYTHONDONTWRITEBYTECODE")=="1" and all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")) and
  len(os.sched_getaffinity(0))==1,"original actual one guest CPU/thread/logical0")
 a.output.mkdir(exist_ok=False);began=time.monotonic()
 # Parent owns ONE whole lease including CPU, all canaries, four matrices and cleanup.
 deadline=proof["common_deadline_monotonic"]-sc.CLEANUP_SECONDS
 sc.need(time.monotonic()<deadline and proof["common_deadline_monotonic"]-proof["common_created_monotonic"]==5400,"shared original5400 with90cleanup, no per-shard reset")
 clock=sc.own_clock(manifest)
 process=dict(pid=os.getpid(),argv=argv,cgroup=Path("/proc/self/cgroup").read_text(),stat=Path("/proc/self/stat").read_text(),
  cmdline_sha256=hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest())
 cases=[];primary=None
 report=dict(schema=sc.SHARD_SCHEMA,status="running",packet_source=own,source_manifest=source,sources_before=files,
  precision_contract=__import__("contract").PROTOCOL,limits=__import__("contract").LIMITS,execution_clock=c.EXECUTION_CLOCK,
  aggregate_execution_clock=clock,original_ba508_numeric_status="failed-not-promoted",original011_numeric_status="failed-not-promoted",
  paper_cutoff="2026-10-08T19:00:00Z",portfolio_cutoff="2026-10-09T11:17:31Z",
  shard_id=a.shard_id,physical=shard["physical"],logical=0,allocation_sha256=sc.digest(plan),
  assigned_cases=shard["assigned_cases"],completed_cases=0,completed_steps=0,cases=cases,device_proof=proof_ref,
  native_no_device_abi=proof["native_no_device_abi"],script_sha256=manifest["files"]["shard_numeric.py"],
  started_ns=time.time_ns(),actual_container_process=process,npu_executed=False,ready=False,service_ready=False,
  model_executed=False,performance_evaluated=False,accuracy_evaluated=False)
 try:
  import torch,torch_npu
  from preflight import recheck_preinit
  abi=c.load(proof["native_no_device_abi"]);recheck_preinit(torch,torch_npu,abi,source,files)
  report["preinit_actual_exports"]=abi["actual_exports"]
  import vllm_ascend.ops
  from vllm_ascend.device.device_op import DeviceOperator,BaseDeviceAdaptor
  import vllm_ascend.device.device_op as actual_device
  sc.need(str(Path(actual_device.__file__))=="/vllm-workspace/vllm-ascend/vllm_ascend/device/device_op.py" and
   c.sha(Path(actual_device.__file__))=="de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47","actual native writer original source")
  sc.need(DeviceOperator is BaseDeviceAdaptor and callable(torch_npu._npu_paged_attention),"original exact native API")
  torch.set_num_threads(1)
  from vllm_ascend.utils import enable_custom_op
  from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
  torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
  sc.need(torch.npu.device_count()==1 and torch.npu.current_device()==0 and torch.npu.get_device_name(0)=="Ascend910B4","actual this-card one logical0 mapping")
  sc.need(enable_custom_op(),"original native bootstrap");init_device_properties_triton()
  validate_proof(a.device_proof,a.device_proof_sha256,source,files,argv,now_ns=report["started_ns"])
  from matrix import run_case
  for cell in shard["assigned_cases"]:
   b,m,correction,t=sc.coordinate(cell)
   sc.need(time.monotonic()<deadline,"original common deadline; no retry")
   start=time.monotonic_ns()
   case=run_case(torch,torch_npu,DeviceOperator,a.output,b,m,correction,t,deadline)
   cref=c.bound(a.output/("case-"+cell["case_id"]+".json"),c.sha(a.output/("case-"+cell["case_id"]+".json")))
   # Timing is diagnostic scheduling metadata, never a throughput claim.
   cases.append({k:case[k] for k in ("batch","mode","reallocation","trial")}|dict(actual_case_ref=cref,
    original_global_seed=cell["seed"],elapsed_monotonic_ns=time.monotonic_ns()-start))
   report.update(completed_cases=len(cases),completed_steps=160*len(cases),npu_executed=True)
  report["status"]="shard_passed";sc.check_headers(report,plan,a.shard_id)
 except BaseException as error:
  primary=error;report.update(status="failed",error=repr(error))
  try:sc.publication(a.output/"FAILURE.json",dict(original=repr(error),retry_allowed=False,ready=False))
  except BaseException as extra:report["secondary_failure_receipt_error"]=repr(extra)
  raise
 finally:
  try:
   _,after=c.source_identity(Path(source["path"]).parent,Path(source["path"]),source["sha256"],"runtime")
   own_after,_=sc.own_identity(a.source_manifest,a.source_manifest_sha256)
   sc.need(after==files and own_after==own,"both immutable math/runtime and dispatch sources")
   report["sources_after"]=after
  except BaseException as extra:
   report["secondary_source_error"]=repr(extra)
   if primary is None:primary=extra;report.update(status="failed",error=repr(extra))
  report["elapsed_seconds"]=time.monotonic()-began
  try:
   rr=sc.publication(a.output/"REPORT.json",report)
   print("MAIN_SPARQ_DISJOINT_REPORT "+json.dumps(dict(report=rr,status=report["status"],packet_source=own,shard_id=a.shard_id)),flush=True)
  except BaseException as extra:
   if primary is None:raise
   print(json.dumps(dict(original_error=repr(primary),secondary_report_error=repr(extra))),flush=True)
  if primary is not None and sys.exc_info()[0] is None:raise primary
if __name__=="__main__":main()
