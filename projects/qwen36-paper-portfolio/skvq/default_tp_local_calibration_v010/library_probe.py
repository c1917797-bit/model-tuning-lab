"""DEFAULT OFF same-image Devices[] dependency probe; no model or NPU import."""
import argparse,inspect,json,os,platform,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common as C
def current_modules():
    import torch,numpy,sklearn,threadpoolctl
    from sklearn.cluster import KMeans
    values=dict(torch=torch,numpy=numpy,sklearn=sklearn,actual_sklearn_KMeans=KMeans,
      threadpoolctl=threadpoolctl,actual_threadpool_info=threadpoolctl.threadpool_info)
    return values
def verify(ref,packet,*,captured=False):
    value=C.bound(ref)
    C.need(value["schema"]=="skvq.default-tp-local.library-probe/v1"and
      value["status"]=="ACTUAL_CPU_FITTING_DEPENDENCIES_IMPORTED_ONLY"and value["source_ref"]==packet and
      value["Devices_empty"]is True and value["torch_npu_imported"]is False and value["NPU_initialized"]is False and
      value["calibration_executed"]is False and value["native_ready"]is False and value["model_ready"]is False,
      "actual current-source CPU dependency observation, not fitting/device authority")
    C.need(value["actual_python"]["major_minor"]==[3,12]and value["actual_python"]["machine"]=="aarch64",
      "same660 CPython3.12 aarch64; software fixture not deployment")
    names={"torch","numpy","sklearn","actual_sklearn_KMeans","threadpoolctl","actual_threadpool_info"}
    C.need(set(value["actual_modules"])==names,"complete exact fitting module origin set")
    from module_snapshots import verify as verify_module_snapshots
    verify_module_snapshots(value,ref,packet)
    C.need(type(captured)is bool,"explicit live or captured module namespace")
    if not captured:
        for origin in value["actual_modules"].values():
            C.need(C.reference(origin["path"])==origin,"actual dependency bytes unchanged")
    C.need(value["actual_cpu_threads"]==dict(intra=1,interop=1)and
      all(type(x.get("num_threads"))is int and x["num_threads"]==1 for x in value["actual_threadpools"]),
      "actual one-thread fitting libraries")
    return value
def match_loaded(probe):
    values=current_modules()
    for name,module in values.items():
        C.need(C.reference(inspect.getfile(module))==probe["actual_modules"][name],
          "fresh child same actual module bytes, no stub or different dependency")
    C.need("torch_npu"not in sys.modules,"CPU fitting must not import native NPU framework")
    return values
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,model_ready=False,native_ready=False)));return
    packet=C.source(a.source_manifest_sha256);C.cpu_only()
    C.need(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0","explicit no automatic NPU backend import")
    C.need(sys.version_info[:2]==(3,12)and platform.machine()=="aarch64","actual same660 Python ABI")
    C.need(all(os.environ.get(k)=="1"for k in("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")),
      "pre-import thread allocation")
    modules=current_modules();torch=modules["torch"]
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    C.need("torch_npu"not in sys.modules,"actual CPU import path did not import NPU backend")
    value=dict(schema="skvq.default-tp-local.library-probe/v1",status="ACTUAL_CPU_FITTING_DEPENDENCIES_IMPORTED_ONLY",
      source_ref=packet,Devices_empty=True,torch_npu_imported=False,NPU_initialized=False,
      actual_python=dict(executable=sys.executable,version=sys.version,major_minor=list(sys.version_info[:2]),machine=platform.machine()),
      actual_modules={k:C.reference(inspect.getfile(v))for k,v in modules.items()},
      versions={k:modules[k].__version__ for k in("torch","numpy","sklearn","threadpoolctl")},
      actual_cpu_threads=dict(intra=torch.get_num_threads(),interop=torch.get_num_interop_threads()),
      actual_threadpools=modules["threadpoolctl"].threadpool_info(),
      calibration_executed=False,native_ready=False,model_ready=False)
    out=C.output_root(a.output)
    from module_snapshots import capture
    value["actual_module_snapshots_ref"]=capture(value["actual_modules"],out,packet)
    ref=C.publish(out/"LIBRARY_PROBE.json",value);verify(ref,packet);print(json.dumps(ref,sort_keys=True))
if __name__=="__main__":main()
