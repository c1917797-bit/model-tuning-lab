"""Actual FULL packet CPU-only import/source probe; OFF unless MAIN calls ON.
Must run inside inspected owned Devices[] guest; no weights, canary or NPU ops.
"""
import argparse,json,os,sys,time
from pathlib import Path
import source_contract as c,gdn_source
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",npu_executed=False,ready=False)));return
 c.require(a.source_manifest_sha256 and a.output,"actual source and new owned CPU output")
 source,files=c.source(str(c.ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
 c.require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1" and
  len(os.sched_getaffinity(0))==1 and all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")),
  "actual CPU-only one-thread/affinity import observer")
 observed=dict(schema="sparq.full-model-no-device-source/v1",source=source,files=files,pid=os.getpid(),
  imports=[],first_exception=None,ready=False,npu_executed=False)
 try:
  import torch,torch_npu
  before=torch.npu.is_initialized();observed["initialized_before"]=before
  import vllm_ascend.ops
  observed["imports"].append("vllm_ascend.ops")
  import vllm_ascend.attention.attention_v1 as attention
  import vllm_ascend.worker.model_runner_v1 as runner
  import vllm_ascend.compilation.acl_graph as acl
  observed["imports"]+=["attention_v1","model_runner_v1","acl_graph"]
  c.runtime_sources(attention,runner,acl);modules=gdn_source.runtime()
  observed["imports"]+=list(modules);observed["deployed_GDN_sources"]=gdn_source.sources()
  from common import COMMON
  observed["common"]=COMMON;observed["torch"]=torch.__version__;observed["torch_npu"]=torch_npu.__version__
  observed["initialized_after"]=torch.npu.is_initialized()
  fds=[]
  for pth in Path("/proc/self/fd").iterdir():
   try:target=os.readlink(pth)
   except FileNotFoundError:continue
   if target.startswith(("/dev/davinci","/dev/devmm","/dev/hisi_hdc")):fds.append(target)
  observed["actual_device_fds"]=fds
  c.require(before is False and observed["initialized_after"] is False and not fds,"no device initialization/FD in Devices[] source probe")
  for obj,name in ((runner.NPUModelRunner,"_model_forward"),(attention.AscendAttentionBackendImpl,"update_graph_params"),(acl.ACLGraphWrapper,"__call__")):
   c.require(callable(getattr(obj,name)),"actual FULL execution seam export "+name)
  import long_workspace,no_pa_full,long_independent_oracle,gdn_stream,numpy
  c.bound(long_independent_oracle.__file__,files["long_independent_oracle.py"])
  c.bound(gdn_stream.__file__,files["gdn_stream.py"])
  c.require(all(callable(getattr(numpy,name,None)) for name in ("frombuffer","bitwise_and","equal")),
   "actual NumPy complete IEEE bit scan exports, not fake arithmetic proof")
  observed["GDN_stream_checker"]=dict(protocol=gdn_stream.PROTOCOL,source=c.bound(gdn_stream.__file__,files["gdn_stream.py"]),
   numpy=dict(version=numpy.__version__,file=c.bound(Path(numpy.__file__).resolve(),c.sha(Path(numpy.__file__).resolve()))),
   state_arithmetic_executed=False,actual_initialized_shape_and_joint_budget_pending=True)
  observed["long_reference_protocol"]=long_independent_oracle.PROTOCOL
  observed["long_reference_arithmetic_not_executed"]=True
  no_pa_full.original_post_order(no_pa_full.verified_sources()["model_runner_v1.py"])
  inherited=long_workspace.numeric_source()
  observed["author_workspace_source"]=dict(path=str(c.KERNEL/"ann_workspace.py"),sha256=long_workspace.WORKSPACE_SHA)
  observed["inherited_run_unchanged"]=inherited.ANNWorkspace.run.__module__==inherited.__name__
  observed["mean_configuration"]=False
  observed["status"]="source-import-checked";observed["model_executed"]=False
 except BaseException as error:
  observed["first_exception"]=repr(error);observed["status"]="failed"
  c.write(a.output,observed);raise
 ref=c.write(a.output,observed);print("MAIN_SPARQ_FULL_CPU "+json.dumps(dict(result=ref,status=observed["status"])),flush=True)
if __name__=="__main__":main()
