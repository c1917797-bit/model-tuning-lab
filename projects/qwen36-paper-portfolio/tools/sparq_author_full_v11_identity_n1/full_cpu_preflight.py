"""Owned Devices[] static/NumPy source probe; runtime receiver imports wait for N1.
No Torch/vLLM import, hardware query, weights, canary or source exemption.
"""
import argparse,json,os,sys
from pathlib import Path
import source_contract as c,gdn_source,gdn_stream
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",npu_executed=False,ready=False)));return
 c.require(a.source_manifest_sha256 and a.output,"actual source and new owned CPU output")
 source,files=c.source(str(c.ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
 c.require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1" and
  len(os.sched_getaffinity(0))==1 and all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")),
  "actual CPU-only one-thread/affinity static observer")
 observed=dict(schema="sparq.full-model-no-device-static/v2",source=source,files=files,pid=os.getpid(),
  runtime_framework_imported=False,device_query_called_by_probe=False,runner_import_pending_admitted_N1=True,
  installed_runtime_sources=c.RUNTIME_PINS,first_exception=None,ready=False,npu_executed=False,model_executed=False)
 try:
  for path,want in c.RUNTIME_PINS.items():
   c.bound(path,want)
   if path.endswith(".py"):compile(Path(path).read_text(),path,"exec")
  nodes=[str(p) for p in Path("/dev").iterdir() if p.name.startswith(("davinci","devmm","hisi_hdc","npu"))]
  fds=[]
  for path in Path("/proc/self/fd").iterdir():
   try:target=os.readlink(path)
   except FileNotFoundError:continue
   if target.startswith(("/dev/davinci","/dev/devmm","/dev/hisi_hdc")):fds.append(target)
  observed["actual_device_nodes"]=nodes;observed["actual_device_fds"]=fds
  c.require(nodes==[] and fds==[],"actual Devices[] namespace and process no device exposure")
  import numpy
  c.require(all(callable(getattr(numpy,name,None)) for name in ("frombuffer","bitwise_and","equal")),"actual NumPy checker exports")
  observed["GDN_stream_checker"]=dict(protocol=gdn_stream.PROTOCOL,source=c.bound(gdn_stream.__file__,files["gdn_stream.py"]),
   numpy=dict(version=numpy.__version__,file=c.bound(Path(numpy.__file__).resolve(),c.sha(Path(numpy.__file__).resolve()))),
   state_arithmetic_executed=False,actual_initialized_shape_and_joint_budget_pending=True)
  observed["deployed_GDN_sources"]=gdn_source.sources()
  c.require(not any(k=="torch" or k.startswith(("torch.","torch_npu","vllm")) for k in sys.modules),
   "CPU static probe must not import hardware-dependent runtime")
  observed["status"]="source-static-checked"
 except BaseException as error:
  observed["first_exception"]=repr(error);observed["status"]="failed";c.write(a.output,observed);raise
 ref=c.write(a.output,observed);print("MAIN_SPARQ_FULL_CPU "+json.dumps(dict(result=ref,status=observed["status"])),flush=True)
if __name__=="__main__":main()
