#!/usr/bin/env python3
"""Default-OFF actual CPU schema preflight. No NPU APIs or native numerics."""
import argparse, importlib.metadata, json, os, resource, sys, time
from pathlib import Path
FI=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v3")
sys.path.insert(0,str(FI))
import contract as c

def inventory():
    return sorted({str(p) for pat in ("davinci*","devmm_svm","hisi_hdc") for p in Path("/dev").glob(pat)})

def produce(a):
    started=time.monotonic()
    source,files=c.source_identity(a.source_manifest,a.source_manifest_sha256)
    c.require(a.producer_sha256==c.sha(__file__),"actual producer source")
    c.require(a.output==Path("/abi-results/report.json") and not a.output.exists(),"exact new output")
    report=dict(schema="flashinfer.no-device-native-schema/v1",passed=False,
        source_manifest=source,sources_before=files,producer_sha256=a.producer_sha256,
        image=c.IMAGE,npu_executed=False,model_executed=False,meta_executed=False,
        workspace_allocation_verified=False,lse_layout_verified=False,graph_verified=False)
    try:
        report["device_inventory_before"]=inventory()
        c.require(not inventory(),"no device/control nodes exposed")
        c.require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and
            os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="","no-device backend autoload disabled")
        c.require(all(os.environ.get(k)=="1" for k in
            ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")),"single CPU threads")
        c.require(len(os.sched_getaffinity(0))==1,"actual singleton CPU affinity")
        from main import cgroup_memory
        report["cgroup"]=cgroup_memory()
        import torch, torch_npu
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        c.require(not torch_npu.npu.is_initialized(),"explicit CPU import must not initialize NPU")
        from host import cann_version_source
        vp,version=cann_version_source()
        report["versions"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
            "vllm_ascend":importlib.metadata.version("vllm-ascend"),"cann":version}
        c.require(report["versions"]["vllm_ascend"]=="0.23.0","actual v0.23 installation")
        mods={"torch":torch,"torch_npu":torch_npu,"torch_npu_native":torch_npu._C}
        import vllm_ascend
        mods["vllm_ascend"]=vllm_ascend
        report["actual_imported_origins"]={k:{"path":str(Path(v.__file__).resolve()),
            "sha256":c.sha(Path(v.__file__).resolve())} for k,v in mods.items()}
        cp=Path(vllm_ascend.__file__).resolve().parent/"attention/context_parallel"
        report["actual_runtime_sources"]={k:{"path":str(p),"sha256":c.sha(p)} for k,p in
            (("attention_cp",cp/"attention_cp.py"),("common_cp",cp/"common_cp.py"),("cann_version",vp))}
        report["model_seam_source_snapshots"]={}
        snapshots=a.output.parent/"source_snapshots"
        snapshots.mkdir(exist_ok=False)
        pkg=Path(vllm_ascend.__file__).resolve().parent
        for alias,relative in (("attention_v1","attention/attention_v1.py"),("model_runner_v1","worker/model_runner_v1.py")):
            src=pkg/relative
            if not src.is_file():
                report["model_seam_source_snapshots"][alias]={"runtime_path":str(src),"available":False}
                continue
            c.require(not src.is_symlink() and src.stat().st_size<=2*1024**2,"bounded ordinary installed model source")
            before=c.sha(src);dst=snapshots/(alias+".py")
            with src.open("rb") as inp,dst.open("xb") as output:
                for chunk in iter(lambda:inp.read(1024*1024),b""):output.write(chunk)
                output.flush();os.fsync(output.fileno())
            c.require(c.sha(src)==before==c.sha(dst),"runtime snapshot drift")
            report["model_seam_source_snapshots"][alias]={"available":True,
                "runtime_ref":{"path":str(src),"sha256":before},"snapshot_ref":c.bound(dst,before)}
        report["actually_mapped_libraries"]={}
        for line in Path("/proc/self/maps").read_text().splitlines():
            fs=line.split()
            if len(fs)>=6 and fs[-1].startswith("/") and ".so" in fs[-1] and any(s in fs[-1].lower() for s in ("torch_npu","opapi","cust_op","vllm")):
                p=Path(fs[-1])
                if p.is_file() and not p.is_symlink():report["actually_mapped_libraries"][str(p)]=c.sha(p)
        pin=report["actual_imported_origins"]["torch_npu_native"]
        c.require(report["actually_mapped_libraries"].get(pin["path"])==pin["sha256"],"actual mapped TorchNPU origin")
        from native import REQUIRED
        required_exports=(("npu_fused_infer_attention_score","default"),
            ("npu_fused_infer_attention_score","out"),
            ("_npu_fused_infer_attention_score_get_max_workspace","default"),
            ("npu_attention_update","default"))
        report["actual_exports"]={}
        failures=[]
        for name,overload in required_exports:
            key=name+"."+overload
            try:
                schema=getattr(getattr(torch.ops.npu,name),overload)._schema
                names={arg.name for arg in schema.arguments}
                need={"lse","local_out","update_type"} if name=="npu_attention_update" else set(REQUIRED)
                if overload=="out":need|={"attention_out","softmax_lse","workspace"}
                row={"schema":str(schema),"arguments":sorted(names),"missing_arguments":sorted(need-names),
                    "return_types":[str(ret.type) for ret in schema.returns]}
                report["actual_exports"][key]=row
                if need-names:failures.append(key+":missing="+str(sorted(need-names)))
            except BaseException as error:
                report["actual_exports"][key]={"error":repr(error)}
                failures.append(key+":"+repr(error))
        report["schema_failures"]=failures
        c.require(not failures,"actual required schemas do not match prepared entry: "+repr(failures))
        c.require(not torch_npu.npu.is_initialized(),"schema introspection initialized device")
        report["device_inventory_after"]=inventory()
        c.require(not inventory(),"device inventory changed")
        _,after=c.source_identity(a.source_manifest,a.source_manifest_sha256)
        report["sources_after"]=after
        c.require(after==files,"complete authored source before/after")
        report["passed"]=True
    except BaseException as error:
        report["primary_error"]=repr(error)
        raise
    finally:
        report.update(duration_seconds=time.monotonic()-started,
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            actual_argv=[sys.executable,*sys.argv],affinity=sorted(os.sched_getaffinity(0)))
        ref=c.write_new(a.output,report)
        print("MAIN_FLASHINFER_NO_DEVICE_SCHEMA_V1 "+json.dumps({"report":ref,"passed":report["passed"],"npu_executed":False}),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest",type=Path)
    p.add_argument("--source-manifest-sha256")
    p.add_argument("--producer-sha256")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False}));return
    c.require(all((a.source_manifest,a.source_manifest_sha256,a.producer_sha256,a.output)),"explicit source and output Refs")
    produce(a)
if __name__=="__main__":main()
