"""MAIN-only trueB1..16 × eager/graph160 standalone SparQ token gate.
Default OFF. No model/serving/E2E/task authority. No launch/compile action.
"""
from __future__ import annotations
import argparse,json,hashlib,math,os,sys,time
from pathlib import Path
from sparq_token_v4.core import HEADS,DIM,BLOCK,SLOTS,require
from sparq_token_v4.proof import validate_proof
from receipt import sha,bound,source_identity,canonical,write_new,MODES,BATCHES,image_argv,CUT,PORTFOLIO_CUT,EXECUTION_CLOCK
LIMITS={"relative_rms":.005,"cosine":.99998}
from contract import PROTOCOL as PRECISION_CONTRACT
def raw_cpu(torch,v):
    if isinstance(v,torch.Tensor):return v.detach().cpu()
    if isinstance(v,dict):return {k:raw_cpu(torch,x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [raw_cpu(torch,x) for x in v]
    return v
def assert_cpu_fp64(torch,*tensors):
    require(tensors and all(t.dtype==torch.float64 and t.device.type=="cpu" for t in tensors),
            "independent CPU-FP64 golden operands/results including original V and mean")
def golden(torch,query,kc,vc,rows,lengths,rank,budget,local,reallocation):
    """Independent CPU-FP64 direct support/output from original BF16 history."""
    query=query.detach().cpu().double();kc=kc.detach().cpu();vc=vc.detach().cpu()
    out=torch.empty_like(query,dtype=torch.float64);supports=[];means=[];alphas=[]
    for i,(q,row,n) in enumerate(zip(query,rows,lengths)):
        p=(n+BLOCK-1)//BLOCK;ids=torch.tensor(row[:p],dtype=torch.long,device=q.device)
        key=kc.index_select(0,ids).view(-1,DIM)[:n].double()
        val=vc.index_select(0,ids).view(-1,DIM)[:n].double()
        assert_cpu_fp64(torch,q,key,val)
        dims=torch.argsort(q.double().abs().sum(0),descending=True,stable=True)[:rank]
        numerator=q.double().index_select(1,dims).abs().sum(1);denominator=q.double().abs().sum(1)
        tau=torch.sqrt(torch.where(denominator>0,DIM*numerator/denominator,torch.ones_like(denominator)))
        prob=torch.softmax((q.double().index_select(1,dims)@key.index_select(1,dims).T)/tau[:,None],-1)
        recent=min(n,local);k=min(n,budget)
        ranking=prob.sum(0);previous=torch.argsort(ranking[:n-recent] if recent else ranking,descending=True,stable=True)[:k-recent]
        latest=torch.arange(n-recent,n,device=q.device,dtype=torch.long) if recent else previous[:0]
        selected=torch.cat((previous,latest)).sort().values;supports.append(selected)
        nk=key.index_select(0,selected);nv=val.index_select(0,selected)
        weights=torch.softmax((q.double()@nk.T)/math.sqrt(DIM),-1)
        assert_cpu_fp64(torch,q,nk,nv,weights,prob)
        exact=weights@nv;alpha=prob.index_select(1,selected).sum(1);mean=val.mean(0)
        assert_cpu_fp64(torch,exact,alpha,mean)
        out[i].copy_(alpha[:,None]*exact+(1-alpha[:,None])*mean if reallocation else exact)
        means.append(mean);alphas.append(alpha)
    means=torch.stack(means);alphas=torch.stack(alphas)
    assert_cpu_fp64(torch,out,means,alphas)
    return out,supports,means,alphas
def pointers(tensors):
    return {k:(t.data_ptr(),t.untyped_storage().data_ptr(),t.storage_offset(),t.untyped_storage().nbytes(),list(t.shape),list(t.stride()),str(t.dtype))
            for k,t in tensors.items()}
def native_slot_capacity(slots,pages,initial_max,steps):
    require(all(type(v) is int and v>0 for v in (slots,pages,initial_max,steps)) and
            initial_max+steps<=pages*BLOCK and slots*pages*BLOCK<=2**31-1,
            "static exact native slot index range fits int32; full160 sequence capacity")
    return slots*pages*BLOCK
def native_slot_layout(torch,npu,indices,tokens,cache):
    require(type(tokens) is int and tokens>0 and indices.shape==(tokens,) and
            indices.dtype==torch.int32 and indices.device==cache.device and indices.device.type=="npu" and
            indices.is_contiguous() and npu.get_npu_format(indices)==2 and
            cache.ndim==4 and cache.shape[1:]==(BLOCK,1,DIM) and cache.dtype==torch.bfloat16 and
            cache.is_contiguous() and npu.get_npu_format(cache)==2,
            "actual ATB native slot int32/ND/contiguous/on-cache-device and BF16 native cache layout")
def run_case(torch,npu,writer,root,b,mode,correction,trial,deadline):
    from matrix import run_case as author_ann_run_case
    return author_ann_run_case(torch,npu,writer,root,b,mode,correction,trial,deadline)

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group()
    for name in ("execute","host-execute","inside-canary","source-audit-only"):g.add_argument("--"+name,action="store_true")
    p.add_argument("--output",type=Path);p.add_argument("--device-proof",type=Path);p.add_argument("--device-proof-sha256")
    p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256")
    p.add_argument("--host-output-root",type=Path);p.add_argument("--native-abi",type=Path);p.add_argument("--native-abi-sha256")
    p.add_argument("--batches",default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16");p.add_argument("--steps",type=int,default=160)
    a=p.parse_args()
    if not (a.execute or a.host_execute or a.inside_canary or a.source_audit_only):print(json.dumps({"status":"disabled","ready":False,"npu_executed":False}));return
    require(a.source_manifest and a.source_manifest_sha256,"explicit source Ref required")
    root=Path(__file__).resolve().parent
    source,files=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime" if (a.execute or a.inside_canary) else "host")
    if a.source_audit_only:
        print(json.dumps({"source_audit_passed":True,"source_manifest":source,"files":files,"npu_executed":False,"ready":False}));return
    if a.host_execute or a.inside_canary:
        from host import execute,inside_canary
        if a.host_execute:execute(a,source,files)
        else:inside_canary(a,source,files)
        return
    require(a.output is not None and a.output.is_absolute() and Path("/sparq-results") in a.output.parents and ".." not in a.output.parts and not a.output.exists() and a.output.parent.is_dir() and a.steps==160,"new owned finite gate root/frozen160")
    require(a.batches==BATCHES,"full fixed B1..16 matrix; no shard admission")
    proof_ref=bound(a.device_proof,a.device_proof_sha256)
    argv=[sys.executable,"-B",*sys.argv]
    proof=validate_proof(a.device_proof,a.device_proof_sha256,source,files,argv)
    require(argv==image_argv(root,a.output,proof_ref,source),"single exact frozen image CLI")
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1" and
      all(os.environ.get(k)=="1" for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")) and len(os.sched_getaffinity(0))==1,"actual one logical0/CPU/thread environment")
    a.output.mkdir(exist_ok=False);began=time.monotonic();cut=__import__("datetime").datetime.fromisoformat(CUT)
    deadline=min(began+5280,began+(cut-__import__("datetime").datetime.now(__import__("datetime").timezone.utc)).total_seconds()-120)
    require(deadline>began,"fixed cutoff and cleanup reserve")
    write_new(a.output/"START.json",{"source_manifest":source,"sources":files,"limits":LIMITS,"batches":list(range(1,17)),"modes":[list(x) for x in MODES],"execution_clock":EXECUTION_CLOCK,"paper_cutoff":"2026-10-08T19:00:00Z","portfolio_cutoff":"2026-10-09T11:17:31Z","npu_executed":False})
    process={"pid":os.getpid(),"argv":argv,"cgroup":Path("/proc/self/cgroup").read_text(),"stat":Path("/proc/self/stat").read_text(),"cmdline_sha256":hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest()}
    cases=[];primary=None;report={"schema":"sparq.token-numeric/v6-author-ann-FP32-compensation","status":"running","source_manifest":source,"sources_before":files,"limits":LIMITS,"cases":cases,
      "paper_cutoff":"2026-10-08T19:00:00Z","portfolio_cutoff":"2026-10-09T11:17:31Z","precision_contract":PRECISION_CONTRACT,"execution_clock":EXECUTION_CLOCK,"original_ba508_numeric_status":"failed-not-promoted","original009_numeric_status":"failed-not-promoted","original011_numeric_status":"failed-not-promoted",
      "device_proof":proof_ref,"native_no_device_abi":proof["native_no_device_abi"],"started_ns":time.time_ns(),"script_sha256":files["numeric_gate.py"],"actual_container_process":process,
      "npu_executed":None,"service_ready":False,"model_executed":False,"performance_evaluated":False,"accuracy_evaluated":False}
    try:
        import torch,torch_npu
        from preflight import recheck_preinit
        actual_abi=__import__("receipt").load(proof["native_no_device_abi"])
        recheck_preinit(torch,torch_npu,actual_abi,source,files)
        report["preinit_actual_exports"]=actual_abi["actual_exports"]
        import vllm_ascend.ops
        from vllm_ascend.device.device_op import DeviceOperator,BaseDeviceAdaptor
        import vllm_ascend.device.device_op as actual_device
        require(str(Path(actual_device.__file__))=="/vllm-workspace/vllm-ascend/vllm_ascend/device/device_op.py" and sha(Path(actual_device.__file__))=="de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47","actual imported original native writer source")
        require(DeviceOperator is BaseDeviceAdaptor and callable(torch_npu._npu_paged_attention),"actual pinned native writer/PA bindings; no guessed fallback")
        torch.set_num_threads(1)
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        require(torch.npu.device_count()==1 and torch.npu.current_device()==0 and torch.npu.get_device_name(0)=="Ascend910B4","actual image/native910B single logical0")
        require(enable_custom_op(),"actual native bootstrap");init_device_properties_triton()
        validate_proof(a.device_proof,a.device_proof_sha256,source,files,argv,now_ns=report["started_ns"])
        for b in range(1,17):
            for m,t in MODES:
                for correction in (0,1):
                    require(time.monotonic()<deadline,"fixed phase/cutoff no retry")
                    case=run_case(torch,torch_npu,DeviceOperator,a.output,b,m,correction,t,deadline)
                    cr=bound(a.output/("case-b%d-%s-mean%d-t%d.json"%(b,m,correction,t)),sha(a.output/("case-b%d-%s-mean%d-t%d.json"%(b,m,correction,t))))
                    cases.append({k:case[k] for k in ("batch","mode","reallocation","trial")}|{"actual_case_ref":cr})
                    report["npu_executed"]=True
        report["status"]="passed"
    except BaseException as error:
        primary=error;report.update(status="failed",error=repr(error))
        try:write_new(a.output/"FAILURE.json",{"original":repr(error),"retry_allowed":False,"ready":False})
        except BaseException as secondary:report["secondary_failure_receipt_error"]=repr(secondary)
        raise
    finally:
        try:
            _,after=source_identity(root,a.source_manifest,a.source_manifest_sha256,"runtime");report["sources_after"]=after
            require(after==files,"actual full sources before/after")
        except BaseException as secondary:
            report["secondary_source_error"]=repr(secondary)
            if primary is None:report.update(status="failed",error=repr(secondary));primary=secondary
        report["elapsed_seconds"]=time.monotonic()-began
        try:
            rr=write_new(a.output/"REPORT.json",report)
            print("MAIN_SPARQ_TOKEN_V5_REPORT "+json.dumps({"report":rr,"status":report["status"],"source_manifest":source,"script_sha256":files["numeric_gate.py"],"device_proof":proof_ref}),flush=True)
        except BaseException as secondary:
            if primary is None:raise
            print(json.dumps({"original_error":repr(primary),"secondary_report_error":repr(secondary)}),flush=True)
        if primary is not None and report["status"]=="failed" and sys.exc_info()[0] is None:raise primary
if __name__=="__main__":main()
