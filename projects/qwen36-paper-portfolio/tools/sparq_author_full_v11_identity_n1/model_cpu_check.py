"""MAIN-only owned Devices[] independent whole-model CPU-FP64 trace check.
OFF by default. No selector/native PA rerun, no weights load, no NPU operations.
"""
import argparse,json,os
from pathlib import Path
import source_contract as c
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 for n in ("source","component","trace"):
  p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
 p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",ready=False,npu_executed=False)));return
 refs={n:c.bound(getattr(a,n),getattr(a,n+"_sha256")) for n in ("source","component","trace")}
 source,files=c.source(refs["source"]["path"],refs["source"]["sha256"])
 authority=c.component(refs["component"],replay=True)
 c.require(a.output and a.output.is_absolute() and Path("/cache/cch") in a.output.parents and not a.output.exists(),
  "new exact CPU-check result, no replacement")
 c.require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and len(os.sched_getaffinity(0))==1,
  "owned no-device CPU one-core source gate")
 raw=dict(schema="sparq.full64-CPU-raw-before/v1",source=source,refs=refs,pid=os.getpid(),
  proc_stat=Path("/proc/self/stat").read_text(),proc_cgroup=Path("/proc/self/cgroup").read_text(),
  proc_argv=Path("/proc/self/cmdline").read_bytes().decode().rstrip("\0").split("\0"),
  env={k:os.environ.get(k) for k in ("ASCEND_RT_VISIBLE_DEVICES","TORCH_DEVICE_BACKEND_AUTOLOAD","OMP_NUM_THREADS")},
  no_candidate_call=True,npu_executed=False,ready=False)
 before_ref=c.write(a.output.parent/"CPU_RAW_BEFORE.json",raw)
 observed=dict(schema="sparq.actual-full64-CPU-check/v1",source=source,source_files=files,refs=refs,raw_before=before_ref,
  first_exception=None,status="failed",npu_executed=False,model_ready=False,ready=False)
 try:
  import torch,torch_npu
  torch.set_num_threads(1)
  observed["initialized_before"]=torch.npu.is_initialized()
  c.require(observed["initialized_before"] is False,"actual no-device CPU before import check")
  from consume_model import consume_trace
  observed["check"]=consume_trace(refs["trace"],source,authority)
  observed["initialized_after"]=torch.npu.is_initialized()
  fds=[]
  for path in Path("/proc/self/fd").iterdir():
   try:target=os.readlink(path)
   except FileNotFoundError:continue
   if target.startswith(("/dev/davinci","/dev/devmm","/dev/hisi_hdc")):fds.append(target)
  observed["actual_device_fds"]=fds
  c.require(observed["initialized_after"] is False and fds==[],"actual no-device CPU check never initializes accelerator")
  observed["status"]="checked";observed["torch"]=torch.__version__;observed["torch_npu"]=torch_npu.__version__
 except BaseException as error:
  observed["first_exception"]=repr(error);c.write(a.output,observed);raise
 ref=c.write(a.output,observed);print("MAIN_SPARQ_FULL_MODEL_CPU "+json.dumps(dict(result=ref,status="checked")),flush=True)
if __name__=="__main__":main()
