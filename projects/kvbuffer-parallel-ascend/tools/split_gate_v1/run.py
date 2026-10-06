#!/usr/bin/env python3
"""MAIN-only NPU execution primitive; import/stdlib tests never load Torch."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
import sys,time
from contract import (CGROUP_BYTES,LIBRARY_SHA,NATIVE_PINS,REPO_PINS,protocol,receipts,
 require,sha,validate_identity,cgroup_limit)

def load_frozen_probe(project):
 path=Path(project)/"tools/native_oracle_probe.py"
 require(sha(path)==REPO_PINS["tools/native_oracle_probe.py"],"original oracle source drift")
 spec=importlib.util.spec_from_file_location("_frozen_kvbp_native_oracle",path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 require(mod.OUT_LIMIT==.00303 and mod.STATE_LIMIT==2e-6 and
  tuple(mod.PADDING_ACTIVE)==(0,1,3,7,12,15,16,16),"numerical protocol changed")
 return mod

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--batch",choices=(1,16),type=int,required=True)
 p.add_argument("--physical-device",choices=(5,6),type=int,required=True)
 p.add_argument("--identity",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True)
 p.add_argument("--library",type=Path,default=Path("/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"))
 p.add_argument("--build-receipt",type=Path,default=Path("/kvbuffer-results/build-p1-v1/build-receipt.json"))
 p.add_argument("--meta-receipt",type=Path,default=Path("/kvbuffer-results/meta-p1-v1/report.json"))
 a=p.parse_args();here=Path(__file__).resolve().parent;project=here.parents[1]
 require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
  os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","single logical0/no-bytecode environment")
 out=a.output_dir.resolve()
 require(Path("/kvbuffer-results") in out.parents and not out.exists(),"new independent output only")
 driver_sources={str(f.relative_to(here)):sha(f) for f in sorted(here.rglob("*")) if f.is_file()}
 ident=json.loads(a.identity.read_text());pp=validate_identity(ident,a.batch,a.physical_device,driver_sources)
 checked=receipts(a.build_receipt,a.meta_receipt,a.library,project)
 native={n:sha(n) for n in NATIVE_PINS};require(native==NATIVE_PINS,"native same-image source drift")
 cg=cgroup_limit()
 out.mkdir(parents=True,exist_ok=False)
 report=dict(schema="kvbp.split-native-gate/v1",status="running",claim="kernel-only",
  created_ns=time.time_ns(),script_sha256=sha(__file__),driver_sources=driver_sources,
  launch_identity=ident,launch_identity_sha256=sha(a.identity),protocol=pp,
  frozen_receipts=checked,native_sources=native,cgroup=cg,cases=[])
 def save():
  # Reuse the frozen oracle's nonfinite-safe serializer after it has loaded.
  val=oracle.finite_json(report) if oracle is not None else report
  (out/"report.json").write_text(json.dumps(val,indent=2,allow_nan=False)+"\n")
 oracle=None;save()
 try:
  oracle=load_frozen_probe(project)
  # Torch/device imports occur ONLY when MAIN invokes main after admission.
  import torch,torch_npu
  oracle.torch=torch;oracle.torch_npu=torch_npu
  from vllm_ascend.utils import enable_custom_op
  from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
  torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
  require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual visible logical-device domain")
  require(enable_custom_op(),"native operators unavailable");init_device_properties_triton()
  torch.ops.load_library(str(a.library.resolve()))
  report["native_schema"]=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)
  report["candidate_schema"]=str(torch.ops.qwen36_kvbuffer_parallel_fp32.decode.default._schema)
  require(report["candidate_schema"]==oracle.EXPECTED_SCHEMA,"actual mutable schema drift")
  require(report["candidate_schema"]==json.loads(a.meta_receipt.read_text())["schema"],"loaded/Meta schema differs")
  report["native_schema_sha256"]=hashlib.sha256(report["native_schema"].encode()).hexdigest()
  report["candidate_schema_sha256"]=hashlib.sha256(report["candidate_schema"].encode()).hexdigest()
  loaded={}
  for line in Path("/proc/self/maps").read_text().splitlines():
   fields=line.split()
   if len(fields)>=6 and fields[-1].startswith("/") and ".so" in fields[-1]:
    path=fields[-1]
    if any(word in path.lower() for word in ("kvbuffer","vllm","cust_op","opapi","torch_npu")) and Path(path).is_file():
     loaded[path]=sha(path)
  require(loaded.get(str(a.library.resolve()))==LIBRARY_SHA,"actual loaded candidate library differs")
  report["loaded_libraries"]=loaded
  report["runtime"]=dict(torch=torch.__version__,torch_npu=torch_npu.__version__,
   logical_device_count=torch.npu.device_count(),logical_device=torch.npu.current_device(),
   device_name=torch.npu.get_device_name(0),
   physical_device_proof="MAIN independent fresh canary/mapping receipt, not inferred fromlogical0")
  save()
  for mode,trials in (("eager",1),("graph",3)):
   for trial in range(trials):oracle.run_case(a.batch,mode,trial,report,save,out)
  require(len(report["cases"])==4 and all(c["status"]=="passed" and len(c["steps"])==160 for c in report["cases"]),
   "single-batch160step/eager+threegraph coverage")
  report["status"]="single_batch_kernel_native_eager_graph_pass"
  report["not_validated"]=["other-split-batch","48-layer-model-lifecycle","matched-E2E","task-accuracy"]
 except BaseException as error:
  report.update(status="failed",error=repr(error));raise
 finally:report["completed_ns"]=time.time_ns();save()
if __name__=="__main__":main()
