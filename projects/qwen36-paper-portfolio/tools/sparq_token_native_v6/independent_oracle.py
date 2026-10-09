"""Independent eager source-stage and CPU-FP64 references.
No candidate imports. Arbitrary exact top-k ties are legal; non-ties are not.
CPU-FP64 complete selected output, means and independent-feedback checks retain
RMS .005/cos .99998. Full-domain dense output is diagnostic, not task accuracy.
"""
import math
from contract import require,topk_legal,LIMITS
def metric(torch,actual,expected):
 actual=actual.detach().cpu().double();expected=expected.detach().cpu().double()
 require(actual.shape==expected.shape and expected.dtype==torch.float64 and expected.device.type=="cpu","full CPU-FP64 output geometry")
 rounded=expected.to(torch.bfloat16).double()
 denominator=rounded.square().mean(-1).sqrt()
 rms=(actual-rounded).square().mean(-1).sqrt()/denominator
 cosine=torch.nn.functional.cosine_similarity(actual,rounded,dim=-1)
 finite=bool(torch.isfinite(actual).all() and torch.isfinite(expected).all() and (denominator>0).all())
 passed=finite and bool((rms<=LIMITS["relative_rms"]).all() and (cosine>=LIMITS["cosine"]).all())
 return {"finite":finite,"passed":passed,"relative_rms":rms.tolist() if finite else None,"cosine":cosine.tolist() if finite else None}
def rank_geometry(q,key,capacity):
 """Exact component-only layout metadata. No candidate numerical operands."""
 n=key.shape[0]
 require(type(capacity) is int and capacity==2304 and q.shape==(6,256) and
  key.shape==(n,256) and type(n) is int and 0<n<=capacity,
  "registered18x128 capacity and actual complete live domain including short requests")
 return n
def native_stage(torch,q,key,dims,capacity):
 """Own BF16 per-head Q/K dot; independent fixed-capacity FP32 SUM(0).
 Masked -Inf padding is introduced only AFTER own live BF16 score staging.
 The author's current token sentinel is n-1, never the capacity tail.
 """
 n=rank_geometry(q,key,capacity)
 importance=q.abs().sum(0)
 projected_key=key.index_select(-1,dims)
 logits=[]
 for query in q:
  projected=query.index_select(0,dims)
  scale=projected.abs().sum(-1)
  scale.div_(query.abs().sum(-1));scale.mul_(query.shape[-1]);scale.pow_(.5)
  logits.append((projected.div(scale) @ projected_key.T).float())
 score=torch.stack(logits)
 padded=torch.full((6,capacity),float("-inf"),dtype=torch.float32,device=score.device)
 padded[:,:n].copy_(score);padded[:,n-1]=torch.finfo(torch.float32).max
 ranking=padded.sum(0)[:n]
 return importance,score,ranking
def source_legality(torch,q,key,dims,selected,witness_score,witness_ranking,capacity):
 n=rank_geometry(q,key,capacity);dims=dims.detach();selected=selected[:min(n,128)].detach()
 require(witness_score.shape==(6,capacity) and witness_ranking.shape==(capacity,) and
  witness_score.dtype==witness_ranking.dtype==torch.float32,
  "actual captured full fixed-capacity score/rank, no inferred or reconstructed candidate stage")
 importance,score,ranking=native_stage(torch,q,key,dims,capacity)
 # Channels are validated against original dtype reduction, without stable ID.
 channels=topk_legal(importance.detach().cpu().float().tolist(),dims.cpu().tolist(),32)
 require(torch.equal(score,witness_score[:,:n]),"independent original-dtype per-head score versus actual captured stage; no backend ULP relaxation")
 require(torch.equal(ranking,witness_ranking[:n]),"independent fixed-capacity per-request FP32 logit GQA SUM incl author +Inf local sentinel")
 # Historical cropped reduction is diagnostic ONLY; it never replaces a gate.
 cropped=score.clone();cropped[:,-1]=torch.finfo(torch.float32).max
 cropped=cropped.sum(0)
 cropped_differences=(cropped!=ranking).nonzero().flatten().detach().cpu().tolist()
 support=topk_legal(ranking.detach().cpu().tolist(),selected.cpu().tolist(),min(n,128),forced=(n-1,))
 return {"channel_contract":channels,"support_contract":support,"reference":"independent original-dtype per-head NPU operators",
   "nonzero_score_tolerance":False,"CPU32_stable_ID_spec":False,"rank_sentinel_final_finiteness_exempt_only":True,
   "rank_layout":{"protocol":"per-request-FP32-SUM0-fixed-capacity/v1","capacity":capacity,"live_length":n,
    "own_inputs":True,"candidate_rank_or_score_used":False,"current_sentinel":n-1,
    "cropped_reduction_diagnostic_only":True,"cropped_vs_registered_difference_tokens":cropped_differences}}
def history(torch,kc,vc,row,n):
 pages=torch.tensor(row[:(n+127)//128],dtype=torch.int64,device="cpu")
 k=kc.detach().cpu().index_select(0,pages).view(-1,256)[:n].double()
 v=vc.detach().cpu().index_select(0,pages).view(-1,256)[:n].double()
 require(k.dtype==v.dtype==torch.float64 and k.device.type==v.device.type=="cpu","independent original K/V CPU-FP64 history, not FP32 V")
 return k,v
def scalar_softmax(values):
 high=max(values);weights=[math.exp(x-high) for x in values];den=sum(weights)
 return [x/den for x in weights]
def conditional(torch,query,key,value,channels,selected,reallocation):
 """High precision full-domain score/alpha and selected output, independent code.
 Dot/softmax/value operands all CPU-FP64. No use of candidate alpha/output.
 """
 query=query.detach().cpu().double();key=key.detach().cpu().double();value=value.detach().cpu().double()
 dims=channels.detach().cpu().long();support=selected.detach().cpu().long()
 numerator=query.index_select(1,dims).abs().sum(1);denominator=query.abs().sum(1)
 require(bool((denominator>0).all() and (numerator>0).all()),"literal author's nonzero per-head coverage domain; no hidden zero-query epsilon")
 tau=(query.shape[-1]*numerator/denominator).sqrt()
 approximate=torch.softmax((query.index_select(1,dims)/tau[:,None]) @ key.index_select(1,dims).T,-1)
 selected_key=key.index_select(0,support);selected_value=value.index_select(0,support)
 weights=torch.softmax((query/math.sqrt(query.shape[-1]))@selected_key.T,-1)
 alpha=approximate.index_select(1,support).sum(1)
 mean=value.mean(0)
 output=weights@selected_value
 if reallocation:output=alpha[:,None]*output+(1-alpha[:,None])*mean
 dense=torch.softmax((query/math.sqrt(query.shape[-1]))@key.T,-1)@value
 return {"output":output,"alpha":alpha,"mean":mean,"dense_diagnostic_output":dense}
def fp64_reselect_diagnostic(torch,query,kc,vc,rows,lengths,reallocation):
 """Diagnostic ONLY: FP64 discrete channel/token reselection is NOT the author BF16 selector. Never supplies formal feedback or a formal support/output gate."""
 out=[];supports=[];channels=[];means=[];alphas=[]
 for q,row,n in zip(query.detach().cpu().double(),rows,lengths):
  k,v=history(torch,kc,vc,row,n)
  importance=q.abs().sum(0);dims=importance.topk(32).indices
  covered=q.index_select(1,dims).abs().sum(1);total=q.abs().sum(1)
  require(bool((covered>0).all() and (total>0).all()),"full reference coverage domain")
  approx=(q.index_select(1,dims)/(256*covered/total).sqrt()[:,None])@k.index_select(1,dims).T
  rank=approx.clone();rank[:,-1]=float("inf");rank=rank.sum(0)
  selected=rank.topk(min(128,n)).indices
  result=conditional(torch,q,k,v,dims,selected,reallocation)
  out.append(result["output"]);supports.append(selected);channels.append(dims);means.append(result["mean"]);alphas.append(result["alpha"])
 return {"output":torch.stack(out),"supports":supports,"channels":channels,"means":torch.stack(means),"alphas":torch.stack(alphas),
  "oracle_dtype":"CPU-FP64 including V/mean","reference_feedback_never_shared":True}

def literal_support_witness(torch,reference,n):
 """Same exact source invocation supplies channels/support, not candidate data.
 Hook BF16 score is for support legality only, NEVER FP64 final/alpha logits.
 """
 dims=reference["channels"][0].detach()
 selected=reference["indices"][0].detach()
 score=reference["score_observation"][0].detach().float()
 require(score.shape==(6,n) and dims.shape==(32,) and selected.shape==(min(n,128),),"literal same-invocation trace geometry")
 ranking=score.clone();ranking[:,-1]=torch.finfo(torch.float32).max;ranking=ranking.sum(0)
 support=topk_legal(ranking.cpu().tolist(),selected.cpu().tolist(),min(n,128),forced=(n-1,))
 return {"support_contract":support,"literal_source_same_invocation":True,"outside_capture":True,
  "selector_feedback_never_shared":True,"candidate_selected_channels_score_alpha_used":False,
  "fp64_reselect_formal":False,"score_observation_used_only_for_legality":True}
def author_feedback(torch,objects,query,kc,vc,rows,lengths,reallocation):
 """Formal independent loop: own BF16 literal selector then own CPU-FP64
 q/K/V coverage/alpha/final-logits/softmax/full V-MV, no candidate operands.
 Reallocation alpha and final mean are recomputed from original complete
 history in FP64, not hook score/literal final scores or candidate mean.
 The literal complete BF16 output remains a separate mandatory comparison.
 """
 from literal_author import reference as literal_reference
 out=[];supports=[];channels=[];means=[];alphas=[];literal=[];witnesses=[];trace=[]
 require(query.dtype==torch.bfloat16 and len(rows)==len(lengths)==query.shape[0],"own original BF16 selector query/topology")
 for q,row,n in zip(query,rows,lengths):
  page_ids=torch.tensor(row[:(n+127)//128],dtype=torch.int64,device=kc.device)
  key=kc.index_select(0,page_ids).view(-1,256)[:n]
  value=vc.index_select(0,page_ids).view(-1,256)[:n]
  ref=literal_reference(torch,objects,q[None],key[None],value[None],reallocation,outside_capture=True)
  k,v=history(torch,kc,vc,row,n)
  dims=ref["channels"][0].detach().cpu().long();selected=ref["indices"][0].detach().cpu().long()
  result=conditional(torch,q,k,v,dims,selected,reallocation)
  out.append(result["output"]);supports.append(selected);channels.append(dims);means.append(result["mean"]);alphas.append(result["alpha"])
  literal.append(ref["output"][0].detach().cpu().double());witnesses.append(literal_support_witness(torch,ref,n))
  trace.append({"query":q.detach().cpu().clone(),"channels":dims.clone(),"support":selected.clone(),
   "literal_score_observation":ref["score_observation"].detach().cpu(),"literal_output":ref["output"].detach().cpu(),
   "literal_weights":ref["weights"].detach().cpu(),"FP64_output":result["output"],"FP64_alpha":result["alpha"],"FP64_mean":result["mean"]})
 return {"output":torch.stack(out),"supports":supports,"channels":channels,"means":torch.stack(means),"alphas":torch.stack(alphas),
  "literal_output":torch.stack(literal),"selector_witnesses":witnesses,"raw_source_selector_trace":trace,
  "oracle_dtype":"own CPU-FP64 complete original q/K/V; own BF16 literal discrete selector",
  "reference_feedback_never_shared":True,"candidate_data_used":False,"FP64_reselect_formal":False}
