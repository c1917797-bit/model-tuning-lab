"""MAIN-only trueB1..16 × eager/graph160 standalone SparQ token gate.
Default OFF. No model/serving/E2E/task authority. No launch/compile action.
"""
from __future__ import annotations
import argparse,json,hashlib,math,os,sys,time
from pathlib import Path
from sparq_token_v4.core import HEADS,DIM,BLOCK,SLOTS,require
from sparq_token_v4.proof import validate_proof
from receipt import sha,bound,source_identity,canonical,write_new,MODES,BATCHES,image_argv
LIMITS={"relative_rms":.005,"cosine":.99998}
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
def run_case(torch,npu,writer,root,b,mode,correction,trial,deadline):
    from sparq_token_v4.core import GraphTokenWorkspace,MeanPool,MeanBook,Guarded
    case="b%d-%s-mean%d-t%d"%(b,mode,correction,trial);pages=18;capacity=pages*BLOCK;slots_total=18
    torch.manual_seed(49585+b+100*trial)
    kguard=Guarded(torch,(slots_total*pages+1,BLOCK,1,DIM),torch.bfloat16,"npu:0")
    vguard=Guarded(torch,(slots_total*pages+1,BLOCK,1,DIM),torch.bfloat16,"npu:0")
    kc=kguard.value;vc=vguard.value;kc.zero_();vc.zero_();refk=kc.clone();refv=vc.clone()
    workspace=GraphTokenWorkspace(kc.device,b,pages,128,32,1);mean=MeanPool(kc.device,slots=slots_total);book=MeanBook(slots_total)
    slots=list(range(b));versions={s:1 for s in slots+[16,17]};lengths={s:2048-3*s for s in slots};lengths.update({16:33,17:65})
    inputs_guard={}
    def allocate_input(name,shape,dtype):
        g=Guarded(torch,shape,dtype,kc.device);inputs_guard[name]=g;g.value.zero_();return g.value
    q=allocate_input("q",(b,HEADS,DIM),torch.bfloat16)
    nk=allocate_input("nk",(b,1,DIM),torch.bfloat16);nv=allocate_input("nv",(b,1,DIM),torch.bfloat16)
    mapping=allocate_input("mapping",(b,),torch.int64)
    leases=allocate_input("leases",(b,),torch.int64);leases.copy_(torch.tensor(slots,dtype=torch.int64,device=kc.device))
    previous=torch.zeros_like(q);reference_previous=torch.zeros_like(q)
    for s in slots+[16,17]:
        n=lengths[s];k=torch.randn((n,1,DIM),device=kc.device,dtype=torch.bfloat16)*.05;v=torch.randn_like(k)*.05
        indices=torch.arange(s*capacity,s*capacity+n,device=kc.device,dtype=torch.int64)
        writer.reshape_and_cache(key=k,value=v,key_cache=kc,value_cache=vc,slot_mapping=indices)
        refk.view(-1,1,DIM)[s*capacity:s*capacity+n].copy_(k)
        refv.view(-1,1,DIM)[s*capacity:s*capacity+n].copy_(v)
        mean.prefill(s,v);book.begin("native-slot-%d"%s,versions[s],s,n)
    torch.npu.synchronize()
    require(torch.equal(kc,refk) and torch.equal(vc,refv),"complete original native cache prefill")
    tensors={"kc":kc,"vc":vc,"q":q,"nk":nk,"nv":nv,"mapping":mapping,"leases":leases,
             "rows":workspace.rows,"lengths":workspace.lengths,"sum":mean.sums,"counts":mean.counts,
             "selected_k":workspace.key,"selected_v":workspace.value,"native_out":workspace.output}
    tensors.update({"workspace_"+name:t for name,t in workspace.tensors().items()})
    require(all(t.device.type=="npu" and t.is_contiguous() and npu.get_npu_format(t)==2 for t in tensors.values()),
            "actual contiguous ND buffers")
    paused_sums=mean.sums[16:].clone();paused_counts=mean.counts[16:].clone()
    identity=pointers(tensors);graph=None;result=None;raw={};step=-1;step_refs=[]
    def run():
        writer.reshape_and_cache(key=nk,value=nv,key_cache=kc,value_cache=vc,slot_mapping=mapping)
        mean.append(leases,nv)
        return workspace.run(q,kc,vc,mean.means(leases),reallocation=bool(correction))
    def topology():
        rows=[[s*pages+j for j in range(pages)] for s in slots]
        workspace.rows.copy_(torch.tensor(rows,dtype=torch.int64,device=kc.device))
        workspace.lengths.copy_(torch.tensor([lengths[s]+1 for s in slots],dtype=torch.int32,device=kc.device))
        mapping.copy_(torch.tensor([s*capacity+lengths[s] for s in slots],dtype=torch.int64,device=kc.device))
        leases.copy_(torch.tensor(slots,dtype=torch.int64,device=kc.device));return rows
    try:
        rows=topology();q.fill_(.05)
        if mode=="graph":
            snapshots={k:t.clone() for k,t in tensors.items()}
            run();torch.npu.synchronize()
            for k,t in tensors.items():t.copy_(snapshots[k])
            graph=torch.npu.NPUGraph()
            with torch.npu.graph(graph):result=run()
            torch.npu.synchronize()
            for k,t in tensors.items():t.copy_(snapshots[k])
        worst=0.;min_cos=1.
        for step in range(160):
            require(time.monotonic()<deadline,"fixed phase/cutoff no retry")
            if step%11==0:
                slots=slots[1:]+slots[:1];previous=previous.roll(-1,0);reference_previous=reference_previous.roll(-1,0)
            if step==80:
                s=slots[0];book.finish("native-slot-%d"%s,versions[s]);versions[s]+=1
                start=s*capacity
                kc[s*pages:(s+1)*pages].zero_();vc[s*pages:(s+1)*pages].zero_()
                refk[s*pages:(s+1)*pages].zero_();refv[s*pages:(s+1)*pages].zero_()
                ik=torch.randn((1,1,DIM),device=kc.device,dtype=torch.bfloat16)*.05;iv=torch.randn_like(ik)*.05
                idx=torch.tensor([start],device=kc.device,dtype=torch.int64)
                writer.reshape_and_cache(key=ik,value=iv,key_cache=kc,value_cache=vc,slot_mapping=idx)
                refk.view(-1,1,DIM)[start:start+1].copy_(ik);refv.view(-1,1,DIM)[start:start+1].copy_(iv)
                mean.reset(s);mean.prefill(s,iv);lengths[s]=1;previous[0].zero_();reference_previous[0].zero_()
                book.begin("native-slot-%d"%s,versions[s],s,1)
            rows=topology();seed=torch.randn_like(q)*.1
            q.copy_((seed.float()+.01*previous.float().tanh()).to(q.dtype))
            rq=(seed.float()+.01*reference_previous.float().tanh()).to(q.dtype)
            nk.copy_(torch.randn_like(nk)*.05);nv.copy_(torch.randn_like(nv)*.05)
            inputs={k:t.clone() for k,t in (("q",q),("nk",nk),("nv",nv),("mapping",mapping),("leases",leases))}
            immutable_workspace=("rows","lengths","logical","logical_page","offset","batch_index","pa_table","budget_tensor")
            workspace_before={k:getattr(workspace,k).clone() for k in immutable_workspace}
            raw={"kc_before":kc.clone(),"vc_before":vc.clone(),"kc":kc,"vc":vc,"refk":refk,"refv":refv,
                 "q":q,"rq":rq,"nk":nk,"nv":nv,"mapping":mapping,"mean":mean.sums,"counts":mean.counts,
                 "scratch_k":workspace.key,"scratch_v":workspace.value,"input_before":inputs,"workspace_before":workspace_before,
                 "workspace_tensors":workspace.tensors(),"workspace_guards":[g.backing for g in workspace._guards],"mean_guards":[g.backing for g in mean._guards],
                 "native_output":workspace.output,"corrected_output":workspace.corrected,"native_cache_outer_guards":(kguard.backing,vguard.backing),
                 "native_input_guards":{k:g.backing for k,g in inputs_guard.items()},"slot_generations":dict(versions),"slot_lengths":dict(lengths)}
            for i,s in enumerate(slots):
                pos=s*capacity+lengths[s]
                refk.view(-1,1,DIM)[pos:pos+1].copy_(nk[i:i+1]);refv.view(-1,1,DIM)[pos:pos+1].copy_(nv[i:i+1])
                book.append("native-slot-%d"%s,versions[s],s,lengths[s])
            if graph is None:result=run()
            else:graph.replay()
            torch.npu.synchronize()
            out,selected,alpha,_=result;current=[lengths[s]+1 for s in slots]
            require(torch.equal(kc,refk) and torch.equal(vc,refv),"complete native KV including all paused/guards")
            require(all(torch.equal(t,inputs[k]) for k,t in (("q",q),("nk",nk),("nv",nv),("mapping",mapping),("leases",leases))) and all(torch.equal(getattr(workspace,k),v) for k,v in workspace_before.items()),"all original inputs/static and per-step topology untouched")
            require(workspace.guards() and mean.guards() and kguard.intact() and vguard.intact() and all(g.intact() for g in inputs_guard.values()),"all actual full-cache/input/workspace/mean prefix-suffix guards and pointer offsets")
            book.native_live(["native-slot-%d"%s for s in slots+[16,17]])
            require(torch.equal(mean.sums[16:],paused_sums) and torch.equal(mean.counts[16:],paused_counts),
                    "both genuine paused request mean states untouched")
            require(workspace.key[-1].count_nonzero().item()==0 and workspace.value[-1].count_nonzero().item()==0,
                    "selected scratch guard page untouched")
            expected,reference_supports,means,refalpha=golden(torch,rq,refk,refv,rows,current,32,128,1,bool(correction))
            candidate_math,candidate_supports,candidate_means,candidate_alpha=golden(torch,q,refk,refv,rows,current,32,128,1,bool(correction))
            # q uses native prior output; rq retains its independent mathematical prior.
            # Same-query support tests implementation. Cross-feedback divergence is diagnostic,
            # never erased by sharing feedback or silently promoted to dense equivalence.
            support_divergence=[not torch.equal(a,b) for a,b in zip(candidate_supports,reference_supports)]
            raw.update(candidate_same_query_golden=candidate_math,candidate_independent_support=candidate_supports,
                reference_feedback_support=reference_supports,cross_feedback_support_divergence=support_divergence)
            # Compare maintained sums with direct full history, never call candidate to get golden.
            actual_mean=mean.means(leases)
            require(bool(torch.allclose(actual_mean.detach().cpu().double(),means,rtol=1e-5,atol=1e-7)),"per-lease cumulative V mean versus direct historical golden")
            require(all(torch.equal(selected[i,:min(current[i],128)].detach().cpu(),support) for i,support in enumerate(candidate_supports)),
                    "same-candidate-query token support equals independent GQA formula; not reference feedback equality")
            fp64=expected;expected=expected.to(out.dtype).double();actual=out.detach().cpu().double()
            er=expected.square().mean(-1).sqrt();rel=(actual-expected).square().mean(-1).sqrt()/er
            cos=torch.nn.functional.cosine_similarity(actual,expected,dim=-1)
            finite=bool(torch.isfinite(out).all().item() and torch.isfinite(fp64).all().item())
            raw.update(output=out,expected_cpu_fp64=fp64,expected_bf16_rounded=expected,support=selected,alpha=alpha,reference_alpha=refalpha)
            good=finite and bool((er>0).all().item()) and bool((rel<=.005).all().item()) and bool((cos>=.99998).all().item())
            require(pointers(tensors)==identity,"captured real native/persistent state pointer drift")
            row={"step":step,"batch":b,"mode":mode,"reallocation":bool(correction),"trial":trial,"finite":finite,
                 "relative_rms":rel.detach().cpu().tolist() if finite else None,"cosine":cos.detach().cpu().tolist() if finite else None,
                 "full_native_cache_bitwise":True,"selected_scratch_guard":True,"input_untouched":True,
                 "mean_request_lease_checked":True,"support_independent":True,"support_independent_query":"candidate-feedback-q",
                 "reference_feedback_independent":True,"reference_feedback_support_equal":not any(support_divergence),
                 "cross_feedback_support_divergence":support_divergence,"dense_attention_equivalence_claimed":False,"pointer_identity":True,"workspace_mean_guards":True,"all_topology_immutable":True,"oracle_cpu_fp64":True,"per_head_metric":True,"native_cache_input_outer_guards":True}
            step_refs.append(write_new(root/("step-"+case+"-%03d.json"%step),row));require(good,"own-query-feedback SparQ token selected/mixed golden")
            worst=max(worst,max(x for heads in row["relative_rms"] for x in heads));min_cos=min(min_cos,min(x for heads in row["cosine"] for x in heads))
            previous.copy_(out);reference_previous.copy_(expected.to(device=out.device,dtype=out.dtype))
            for s in slots:lengths[s]+=1
        report={"batch":b,"mode":mode,"reallocation":bool(correction),"trial":trial,"steps":160,"status":"passed",
                "worst_relative_rms":worst,"minimum_cosine":min_cos,"actual_workspace_bytes":workspace.bytes,
                "actual_mean_bytes":mean.bytes,"mean_payload_bytes":mean.payload_bytes,"actual_native_cache_backing_bytes":kguard.bytes()+vguard.bytes(),"actual_native_input_backing_bytes":sum(g.bytes() for g in inputs_guard.values()),"actual_step_refs":step_refs,"model_graph_supported":False,"service_ready":False}
        write_new(root/("case-"+case+".json"),report);return report
    except BaseException as error:
        try:
            with (root/("failure-"+case+"-%03d.pt"%step)).open("xb") as stream:torch.save(raw_cpu(torch,raw),stream)
        except BaseException as secondary:
            try:write_new(root/("raw-failure-"+case+".json"),{"original":repr(error),"secondary":repr(secondary)})
            except BaseException:pass
        raise
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
    a.output.mkdir(exist_ok=False);began=time.monotonic();cut=__import__("datetime").datetime.fromisoformat("2026-10-09T11:17:31+00:00")
    deadline=min(began+5280,began+(cut-__import__("datetime").datetime.now(__import__("datetime").timezone.utc)).total_seconds()-120)
    require(deadline>began,"fixed cutoff and cleanup reserve")
    write_new(a.output/"START.json",{"source_manifest":source,"sources":files,"limits":LIMITS,"batches":list(range(1,17)),"modes":[list(x) for x in MODES],"npu_executed":False})
    process={"pid":os.getpid(),"argv":argv,"cgroup":Path("/proc/self/cgroup").read_text(),"stat":Path("/proc/self/stat").read_text(),"cmdline_sha256":hashlib.sha256(Path("/proc/self/cmdline").read_bytes()).hexdigest()}
    cases=[];primary=None;report={"schema":"sparq.token-numeric/v4","status":"running","source_manifest":source,"sources_before":files,"limits":LIMITS,"cases":cases,
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
