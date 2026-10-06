#!/usr/bin/env python3
"""NEW true-T2..15 correctness driver. MAIN owns execution; default OFF."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

GROUPS={4:(2,14,15),5:(7,11,13),6:(3,4,9,12),7:(5,6,8,10)}
CONTRACT_SHA="32dd50050a28de0038aa847f55068e58efba98be07d15229b2e1f36eef4ae880"
NATIVE_SO="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SO_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,why):
 if not ok: raise ValueError(why)
def load(path,name,expected):
 require(sha(path)==expected,"frozen module source drift: "+str(path))
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod
def protocol(batches,physical):
 require(type(physical) is int and tuple(batches)==GROUPS.get(physical),"exact balanced true-T shard required")
 return dict(batches=list(batches),physical_device=physical,logical_device=0,
  slots={str(t):t+3 for t in batches},eager_trials=1,graph_trials=3,
  steps_per_case=160,feedback=True,output_limit=.00303,
  complete_and_per_head_l2_limit=2e-6,
  graph_active_schedule={str(t):[t] for t in batches},
  real_token_batches_only=True,reset_steps=[64,112],required_flushes=True,
  retry="none",scope="intermediate-kernel-only-not-model-E2E-or-task-accuracy")
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--execute",action="store_true");p.add_argument("--audit-only",action="store_true")
 p.add_argument("--batches",type=int,nargs="+");p.add_argument("--physical-device",type=int,choices=tuple(GROUPS))
 p.add_argument("--identity",type=Path);p.add_argument("--output-dir",type=Path)
 p.add_argument("--library",type=Path,default=Path("/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"))
 p.add_argument("--build-receipt",type=Path,default=Path("/kvbuffer-results/build-p1-v1/build-receipt.json"))
 p.add_argument("--meta-receipt",type=Path,default=Path("/kvbuffer-results/meta-p1-v1/report.json"))
 a=p.parse_args(argv)
 if not a.execute and not a.audit_only:
  print(json.dumps(dict(status="OFF",groups=GROUPS,npu_executed=False,serving_ready=False)))
  return 0
 require(not (a.execute and a.audit_only),"choose source-only OR explicit execution")
 require(a.batches is not None and a.physical_device is not None,"exact shard arguments required")
 pp=protocol(a.batches,a.physical_device)
 here=Path(__file__).resolve().parent;project=here.parents[1]
 c=load(project/"tools/split_gate_v1/contract.py","_middle_kvbp_frozen_contract",CONTRACT_SHA)
 checked=c.receipts(a.build_receipt,a.meta_receipt,a.library,project)
 oracle=load(project/"tools/native_oracle_probe.py","_middle_kvbp_frozen_oracle",
             c.REPO_PINS["tools/native_oracle_probe.py"])
 require(oracle.OUT_LIMIT==.00303 and oracle.STATE_LIMIT==2e-6 and
  tuple(oracle.PADDING_ACTIVE)==(0,1,3,7,12,15,16,16),"original numerical protocol differs")
 drivers={str(f.relative_to(here)):sha(f) for f in sorted(here.rglob("*"))
          if f.is_file() and "__pycache__" not in f.parts}
 if a.audit_only:
  print(json.dumps(dict(status="source_audit_pass",protocol=pp,frozen_receipts=checked,
   driver_sources=drivers,npu_executed=False,serving_ready=False,
   loaded_runtime_or_device_verified=False),sort_keys=True))
  return 0
 require(os.environ.get("KVBUFFER_MIDDLE_BATCH_EXECUTE")=="1","explicit MAIN opt-in missing")
 require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
  os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","single logical0/no bytecode required")
 require(a.identity is not None and a.output_dir is not None,"MAIN identity/fresh output required")
 out=a.output_dir.resolve()
 require(Path("/kvbuffer-results") in out.parents and not out.exists(),"new output only")
 ident=json.loads(a.identity.read_text())
 require(ident.get("schema")=="kvbp.middle-batch-launch-identity/v1" and
  ident.get("image_id")==c.IMAGE,"NEW MAIN identity/image required, not old split identity")
 require(ident.get("physical_devices")==[a.physical_device] and
  ident.get("logical_to_physical")=={"0":a.physical_device} and
  ident.get("fresh_idle_verified") is True and ident.get("nonprivileged") is True and
  ident.get("source_canary_passed") is True,"fresh actual mapping/source/canary required")
 require(ident.get("memory_cgroup_bytes")==c.CGROUP_BYTES and ident.get("protocol")==pp,
         "8GiB/exact NEW protocol required")
 require(ident.get("library_sha256")==c.LIBRARY_SHA and
  ident.get("build_receipt_sha256")==c.BUILD_SHA and ident.get("meta_receipt_sha256")==c.META_SHA and
  ident.get("repo_sources")==c.REPO_PINS and ident.get("native_sources")==c.NATIVE_PINS and
  ident.get("driver_sources")==drivers and ident.get("native_library_sha256")==NATIVE_SO_SHA,
  "complete existing and NEW source identities required")
 require(type(ident.get("evidence")) is dict and ident["evidence"],"independent MAIN evidence required")
 ts=datetime.fromisoformat(ident["preflight_utc"].replace("Z","+00:00"))
 require(ts.tzinfo is not None and 0<=(datetime.now(timezone.utc)-ts).total_seconds()<=600,
         "fresh MAIN preflight required")
 native={n:sha(n) for n in c.NATIVE_PINS}
 require(native==c.NATIVE_PINS and sha(NATIVE_SO)==NATIVE_SO_SHA,"actual native image bytes differ")
 cg=c.cgroup_limit()
 out.mkdir(parents=True,exist_ok=False)
 report=dict(schema="kvbp.intermediate-native-gate/v1",status="running",claim="kernel-only",
  created_ns=time.time_ns(),script_sha256=sha(__file__),driver_sources=drivers,
  launch_identity=ident,launch_identity_sha256=sha(a.identity),protocol=pp,
  frozen_receipts=checked,native_sources=native,cgroup=cg,cases=[],
  serving_ready=False,performance_measurement_admitted=False)
 def save():
  (out/"report.json").write_text(json.dumps(oracle.finite_json(report),indent=2,allow_nan=False)+"\n")
 save()
 try:
  import torch,torch_npu
  oracle.torch=torch;oracle.torch_npu=torch_npu
  from vllm_ascend.utils import enable_custom_op
  from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
  torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
  require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual one-device domain required")
  require(enable_custom_op(),"native operators unavailable");init_device_properties_triton()
  torch.ops.load_library(str(a.library.resolve()))
  report["native_schema"]=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)
  report["candidate_schema"]=str(torch.ops.qwen36_kvbuffer_parallel_fp32.decode.default._schema)
  require(report["candidate_schema"]==oracle.EXPECTED_SCHEMA and
   report["candidate_schema"]==json.loads(a.meta_receipt.read_text())["schema"],"loaded mutable schema differs")
  report["native_schema_sha256"]=hashlib.sha256(report["native_schema"].encode()).hexdigest()
  report["candidate_schema_sha256"]=hashlib.sha256(report["candidate_schema"].encode()).hexdigest()
  loaded={}
  for line in Path("/proc/self/maps").read_text().splitlines():
   f=line.split()
   if len(f)>=6 and f[-1].startswith("/") and ".so" in f[-1] and Path(f[-1]).is_file():
    if any(w in f[-1].lower() for w in ("kvbuffer","vllm","cust_op","opapi","torch_npu")):
     loaded[f[-1]]=sha(f[-1])
  require(loaded.get(str(a.library.resolve()))==c.LIBRARY_SHA and
   loaded.get(NATIVE_SO)==NATIVE_SO_SHA,"actual loaded candidate/native identities required")
  report["loaded_libraries"]=loaded
  report["runtime"]=dict(torch=torch.__version__,torch_npu=torch_npu.__version__,
   logical_device_count=1,logical_device=0,device_name=torch.npu.get_device_name(0),
   physical_device_proof="MAIN fresh external proof, not inferred from logical0")
  save()
  for batch in a.batches:
   for mode,trials in (("eager",1),("graph",3)):
    for trial in range(trials):oracle.run_case(batch,mode,trial,report,save,out)
  expected={(t,"eager",0) for t in a.batches}|{(t,"graph",i) for t in a.batches for i in range(3)}
  observed={(v["batch"],v["mode"],v["trial"]) for v in report["cases"]}
  require(len(report["cases"])==len(expected) and observed==expected and
   all(v["status"]=="passed" and len(v["steps"])==160 and
       all(r["passed"] and r["active"]==v["batch"] for r in v["steps"])
       for v in report["cases"]),"complete genuine middle-T matrix required")
  require({n:sha(project/n) for n in c.REPO_PINS}==c.REPO_PINS and
   {n:sha(n) for n in c.NATIVE_PINS}==native and
   {str(f.relative_to(here)):sha(f) for f in sorted(here.rglob("*"))
    if f.is_file() and "__pycache__" not in f.parts}==drivers,"source changed during execution")
  report["status"]="intermediate_batches_kernel_native_eager_graph_pass"
  report["npu_executed"]=True
  report["not_validated"]=["other-shards","48-layer-model-lifecycle","mixed-prefill-fallback",
   "matched-E2E","TTFT/TPOT","GSM8K/LongBench","production-performance"]
 except BaseException as error:
  report.update(status="failed",error=repr(error));raise
 finally:
  report["completed_ns"]=time.time_ns();save()
 return 0
if __name__=="__main__":raise SystemExit(main())
