"""Complete 128-case/20480-step producer body for MAIN-reviewed successor.
This module never launches containers or initializes a device. Default OFF.
Own writer/lease/guard/reuse/feedback geometry comes from actual frozen driver;
ANN arithmetic and independent author/FP64 acceptance are new, not old011 PASS.
"""
import time,math
from pathlib import Path
from contract import require,PROTOCOL,COMMIT,LIMITS,BASE,source_pins,write_new
from ann_workspace import ANNWorkspace,substrate
from literal_author import build as build_literal,reference as literal_reference
from independent_oracle import author_feedback,fp64_reselect_diagnostic,source_legality,metric
HEADS,DIM,BLOCK,SLOTS=6,256,128,16
def raw_cpu(torch,v):
 if isinstance(v,torch.Tensor):return v.detach().cpu()
 if isinstance(v,dict):return {k:raw_cpu(torch,x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [raw_cpu(torch,x) for x in v]
 return v
def pointers(tensors):
 return {k:(t.data_ptr(),t.untyped_storage().data_ptr(),t.storage_offset(),t.untyped_storage().nbytes(),list(t.shape),list(t.stride()),str(t.dtype)) for k,t in tensors.items()}
def native_slot_capacity(slots,pages,initial_max,steps):
 require(all(type(v) is int and v>0 for v in (slots,pages,initial_max,steps)) and initial_max+steps<=pages*BLOCK and slots*pages*BLOCK<=2**31-1,
  "static exact native slot int32 capacity and original160 steps")
def native_slot_layout(torch,npu,indices,tokens,cache):
 require(type(tokens) is int and tokens>0 and indices.shape==(tokens,) and indices.dtype==torch.int32 and indices.device==cache.device and indices.device.type=="npu" and
 indices.is_contiguous() and npu.get_npu_format(indices)==2 and cache.ndim==4 and cache.shape[1:]==(BLOCK,1,DIM) and cache.dtype==torch.bfloat16 and
 cache.is_contiguous() and npu.get_npu_format(cache)==2,"actual ATB int32/ND slot and BF16 native cache layout")
def run_case(torch,npu,writer,root,b,mode,correction,trial,deadline):
    base=substrate();MeanPool,MeanBook,Guarded=base.MeanPool,base.MeanBook,base.Guarded
    objects=build_literal(torch)
    case="b%d-%s-mean%d-t%d"%(b,mode,correction,trial);pages=18;capacity=pages*BLOCK;slots_total=18
    native_slot_capacity(slots_total,pages,2048,160)
    torch.manual_seed(49585+b+100*trial)
    kguard=Guarded(torch,(slots_total*pages+1,BLOCK,1,DIM),torch.bfloat16,"npu:0")
    vguard=Guarded(torch,(slots_total*pages+1,BLOCK,1,DIM),torch.bfloat16,"npu:0")
    kc=kguard.value;vc=vguard.value;kc.zero_();vc.zero_();refk=kc.clone();refv=vc.clone()
    workspace=ANNWorkspace(kc.device,b,pages,128,32,1);mean=MeanPool(kc.device,slots=slots_total);book=MeanBook(slots_total)
    slots=list(range(b));versions={s:1 for s in slots+[16,17]};lengths={s:2048-3*s for s in slots};lengths.update({16:33,17:65})
    inputs_guard={}
    def allocate_input(name,shape,dtype):
        g=Guarded(torch,shape,dtype,kc.device);inputs_guard[name]=g;g.value.zero_();return g.value
    q=allocate_input("q",(b,HEADS,DIM),torch.bfloat16)
    nk=allocate_input("nk",(b,1,DIM),torch.bfloat16);nv=allocate_input("nv",(b,1,DIM),torch.bfloat16)
    mapping=allocate_input("mapping",(b,),torch.int32)
    native_slot_layout(torch,npu,mapping,b,kc)
    leases=allocate_input("leases",(b,),torch.int64);leases.copy_(torch.tensor(slots,dtype=torch.int64,device=kc.device))
    previous=torch.zeros_like(q);reference_previous=torch.zeros_like(q)
    for s in slots+[16,17]:
        n=lengths[s];k=torch.randn((n,1,DIM),device=kc.device,dtype=torch.bfloat16)*.05;v=torch.randn_like(k)*.05
        indices=torch.arange(s*capacity,s*capacity+n,device=kc.device,dtype=torch.int32)
        native_slot_layout(torch,npu,indices,n,kc)
        writer.reshape_and_cache(key=k,value=v,key_cache=kc,value_cache=vc,slot_mapping=indices)
        refk.view(-1,1,DIM)[s*capacity:s*capacity+n].copy_(k)
        refv.view(-1,1,DIM)[s*capacity:s*capacity+n].copy_(v)
        mean.prefill(s,v);book.begin("native-slot-%d"%s,versions[s],s,n)
    torch.npu.synchronize()
    require(torch.equal(kc,refk) and torch.equal(vc,refv),"complete original native cache prefill")
    tensors={"kc":kc,"vc":vc,"q":q,"nk":nk,"nv":nv,"mapping":mapping,"leases":leases,
             "rows":workspace.rows,"lengths":workspace.lengths,"sum":mean.sums,"counts":mean.counts,
             "selected_k":workspace.key,"selected_v":workspace.value,"author_weighted_selected_out":workspace.output}
    tensors.update({"workspace_"+name:t for name,t in workspace.tensors().items()})
    require(all(t.device.type=="npu" and t.is_contiguous() and npu.get_npu_format(t)==2 for name,t in tensors.items()),
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
        live_lengths=[lengths[s]+1 for s in slots]
        workspace.lengths.copy_(torch.tensor(live_lengths,dtype=torch.int32,device=kc.device))
        positions=[s*capacity+lengths[s] for s in slots]
        require(len(set(positions))==b and all(0<=p<slots_total*capacity for p in positions),
                "exact unique native host slot positions within int32-admitted backing")
        mapping.copy_(torch.tensor(positions,dtype=torch.int32,device=kc.device))
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
                idx=torch.tensor([start],device=kc.device,dtype=torch.int32)
                native_slot_layout(torch,npu,idx,1,kc)
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
                 "native_input_guards":{k:g.backing for k,g in inputs_guard.items()},
                 "slot_generations":dict(versions),"slot_lengths":dict(lengths)}
            for i,s in enumerate(slots):
                pos=s*capacity+lengths[s]
                refk.view(-1,1,DIM)[pos:pos+1].copy_(nk[i:i+1]);refv.view(-1,1,DIM)[pos:pos+1].copy_(nv[i:i+1])
                book.append("native-slot-%d"%s,versions[s],s,lengths[s])
            if graph is None:result=run()
            else:
                graph.replay()
            torch.npu.synchronize()
            out,selected,alpha,channels=result;current=[lengths[s]+1 for s in slots]
            require(torch.equal(kc,refk) and torch.equal(vc,refv),"complete native KV including all paused/guards")
            require(all(torch.equal(t,inputs[k]) for k,t in (("q",q),("nk",nk),("nv",nv),("mapping",mapping),("leases",leases))) and all(torch.equal(getattr(workspace,k),v) for k,v in workspace_before.items()),"all original inputs/static and per-step topology untouched")
            require(workspace.guards() and mean.guards() and kguard.intact() and vguard.intact() and all(g.intact() for g in inputs_guard.values()),"all actual full-cache/input/workspace/mean prefix-suffix guards and pointer offsets")
            book.native_live(["native-slot-%d"%s for s in slots+[16,17]])
            require(torch.equal(mean.sums[16:],paused_sums) and torch.equal(mean.counts[16:],paused_counts),
                    "both genuine paused request mean states untouched")
            require(workspace.key[-1].count_nonzero().item()==0 and workspace.value[-1].count_nonzero().item()==0,
                    "selected scratch guard page untouched")
            # Two independent literal selector calls use their OWN q/rq.
            # No candidate support/channels/alpha enters either FP64 reference.
            feedback=author_feedback(torch,objects,rq,refk,refv,rows,current,bool(correction))
            same=author_feedback(torch,objects,q,refk,refv,rows,current,bool(correction))
            diagnostic_feedback=fp64_reselect_diagnostic(torch,rq,refk,refv,rows,current,bool(correction))
            diagnostic_same=fp64_reselect_diagnostic(torch,q,refk,refv,rows,current,bool(correction))
            raw.update(independent_literal_q=same["raw_source_selector_trace"],
                independent_literal_rq=feedback["raw_source_selector_trace"],
                FP64_reselect_q_DIAGNOSTIC_ONLY=diagnostic_same,FP64_reselect_rq_DIAGNOSTIC_ONLY=diagnostic_feedback)
            expected=feedback["output"];means=feedback["means"];refalpha=feedback["alphas"]
            support_divergence=[set(a.tolist())!=set(b.tolist()) for a,b in zip(same["supports"],feedback["supports"])]
            require(bool(torch.allclose(mean.means(leases).detach().cpu().double(),means,rtol=1e-5,atol=1e-7)),
                    "per-lease cumulative V mean versus complete independent history")
            legal=[]
            for i,(row,n) in enumerate(zip(rows,current)):
                page_ids=torch.tensor(row[:(n+127)//128],dtype=torch.int64,device=kc.device)
                source_k=kc.index_select(0,page_ids).view(-1,DIM)[:n]
                source_v=vc.index_select(0,page_ids).view(-1,DIM)[:n]
                k=min(n,128)
                legal.append(source_legality(torch,q[i],source_k,channels[i],selected[i],
                    workspace.score[i],workspace.ranking[i],workspace.capacity))
                require(bool(workspace.selected_valid[i,:k].all()) and not bool(workspace.selected_valid[i,k:].any()),
                    "complete valid support then exclusively masked static graph tails")
                ids=selected[i,:k]
                packed_k=workspace.key[i,:,0,:];packed_v=workspace.value[i,:,0,:]
                require(torch.equal(packed_k[:k],source_k.index_select(0,ids)) and
                    torch.equal(packed_v[:k],source_v.index_select(0,ids)) and
                    packed_k[k:].count_nonzero().item()==0 and packed_v[k:].count_nonzero().item()==0,
                    "actual entire selected scratch exact independently gathered native K/V and zero tails")
            conditional_output=same["output"];literal_output=same["literal_output"]
            conditional_metric=metric(torch,out,conditional_output)
            literal_metric=metric(torch,out,literal_output)
            fp64_reselect_diagnostic_metric=metric(torch,out,diagnostic_same["output"])
            require(conditional_metric["passed"] and literal_metric["finite"],
                    "NEW FP32 compensation: own BF16 literal selector + independent full FP64 .005/.99998 hard; literal deviation fully reported, not parity")
            raw.update(author_literal_output=literal_output,author_conditional_fp64=conditional_output,
                independent_same_query_fp64=same["output"],independent_feedback_fp64=expected,
                author_legal_topk=legal,conditional_metric=conditional_metric,literal_metric=literal_metric,
                FP64_reselect_diagnostic_metric=fp64_reselect_diagnostic_metric,author_score=workspace.score,
                author_rank=workspace.ranking,author_importance=workspace.importance,author_scale=workspace.scale,
                author_weights=workspace.weights,static_tail_mask=workspace.selected_valid)
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
            row.update(precision_contract=PROTOCOL,author_commit=COMMIT,author_literal_outside_capture=True,
                       original011_status="FAILED-not-promoted",literal_author_mathematical_domain="all heads nonzero original coverage",
                       author_legal_topk=legal,nonzero_score_tolerance=False,CPU32_stable_ID_required=False,
                       author_conditional_fp64_metric=conditional_metric,author_literal_output_metric=literal_metric,
                       author_literal_output_hard_gate=False,literal_output_deviation_complete_every_head=True,
                       finite_precision_variant="FP32 alpha/softmax/V-MV/mean compensation; one BF16 output",
                       original_BF16_dual_gate_status="FAILED-not-promoted",
                       FP64_reselect_diagnostic_metric=fp64_reselect_diagnostic_metric,
                       FP64_reselect_formal=False,reference_selector="own BF16 literal author q/rq independent",
                       author_reference_q_selector_witness=same["selector_witnesses"],
                       author_reference_rq_selector_witness=feedback["selector_witnesses"],
                       candidate_data_used_by_formal_reference=False,full_original_qKV_FP64_recomputed=True,
                       literal_selector_observation_restored=True,
                       native_PA_executed=False,actual_current_lengths=current,actual_slot_order=list(slots),
                       actual_slot_generations={str(s):versions[s] for s in slots+[16,17]},
                       static_tails_zero=True,selected_native_KV_exact=True,
                       graph_capture_scope="actual native writer + mean append + registered FP32-compensation ANN only",
                       literal_reference_never_captured=True)
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

def full_matrix(torch,npu,writer,root,deadline):
 """Called only AFTER new whole-source no-device ABI + exact owner proof/canary.
 No v7 report, kernel fragment or fixed-checkpoint witness grants permission.
 """
 require(root.is_absolute() and root.is_dir() and not list(root.iterdir()) and time.monotonic()<deadline,"new empty original full matrix root/deadline")
 cases=[]
 for b in range(1,17):
  for mode,trial in (("eager",0),("graph",0),("graph",1),("graph",2)):
   for correction in (0,1):
    report=run_case(torch,npu,writer,root,b,mode,correction,trial,deadline)
    cases.append({k:report[k] for k in ("batch","mode","reallocation","trial")}|{"actual_case_ref":dict(path=str(root/("case-b%d-%s-mean%d-t%d.json"%(b,mode,correction,trial))),sha256=__import__("contract").sha(root/("case-b%d-%s-mean%d-t%d.json"%(b,mode,correction,trial))))})
 require(len(cases)==128,"all original128 cases")
 return cases
def main():
 import argparse,json,sys
 p=argparse.ArgumentParser();p.add_argument("--source-audit-only",action="store_true");a=p.parse_args()
 if a.source_audit_only:print(json.dumps({"source":source_pins(),"ready":False,"host_successor_pending":True}));return
 print(json.dumps({"enabled":False,"torch_imported":"torch" in sys.modules,"numerical_ready":False,"complete_matrix_producer_present":True,"host_successor_pending":True}))
if __name__=="__main__":main()
