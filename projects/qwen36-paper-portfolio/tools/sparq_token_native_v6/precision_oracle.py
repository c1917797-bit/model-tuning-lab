"""Registered finite-precision support contract; independent CPU oracle.
No candidate/core calls, no NPU imports, no epsilon tie rule.
"""
import math,struct
PROTOCOL="sparq.fp32-support-fp64-output/v1"
def need(ok,message):
 if not ok:raise ValueError(message)
def bits32(v):
 need(type(v) is float and math.isfinite(v),"finite ordinary FP32 score")
 raw=struct.pack(">f",v)
 need(struct.unpack(">f",raw)[0]==v,"score must already be exactly binary32")
 return raw.hex()
def classify(scores,support32,support64,channels32,channels64,budget=128,local=1):
 n=len(scores);k=min(n,budget);forced=min(n,local)
 need(type(budget) is int and budget>0 and type(local) is int and 0<=local<=budget and n>0,"exact live selection domain")
 need(all(type(v) is float and math.isfinite(v) and bits32(v) for v in scores),"all independent ranking values are finite FP32")
 def ids(v):
  return type(v) is list and len(v)==k and all(type(i) is int and 0<=i<n for i in v) and v==sorted(set(v))
 need(ids(support32) and ids(support64),"unique ordered exact support size/domain")
 need(type(channels32) is list and channels32==channels64 and len(channels32)==32 and len(set(channels32))==32 and all(type(i) is int and 0<=i<256 for i in channels32),"FP32/FP64 independent channel identity; channel precision divergence not admitted")
 prior=list(range(n-forced));take=k-forced
 ordered=sorted(prior,key=lambda i:(-scores[i],i))
 expected=sorted(ordered[:take]+list(range(n-forced,n)))
 need(support32==expected,"strict stable independent FP32 support; wrong tied ID still fails")
 if take:
  cutoff=scores[ordered[take-1]]
  upper=[i for i in prior if scores[i]>cutoff]
  ties=[i for i in prior if scores[i]==cutoff]
  cutoff_bits=bits32(cutoff)
 else:upper=[];ties=[];cutoff_bits=None
 changed=sorted(set(support32)^set(support64))
 need(not changed or (take>0 and set(changed)<=set(ties)),"FP64 support divergence outside exact FP32 cutoff tie; no epsilon/ULP allowance")
 return {"protocol":PROTOCOL,"length":n,"budget":budget,"local":local,
  "support32":support32,"support64":support64,"channels32":channels32,"channels64":channels64,
  "cutoff_bits":cutoff_bits,"strictly_above":upper,"cutoff_equal":ties,
  "changed_ids":changed,"exact_cutoff_tie_explains_fp64":bool(changed),
  "strict_stable_cpu32_support":True,"nonzero_score_tolerance":False}
def validate_witness(w):
 need(type(w) is dict and w.get("protocol")==PROTOCOL and
  w.get("strict_stable_cpu32_support") is True and w.get("nonzero_score_tolerance") is False,"registered strict precision witness")
 n,budget,local=w["length"],w["budget"],w["local"]
 need(type(n) is int and n>0 and type(budget) is int and budget==128 and type(local) is int and local==1,"frozen live domain and selector")
 k=min(n,budget);forced=min(n,local);take=k-forced
 a,b=w["support32"],w["support64"];upper,ties=w["strictly_above"],w["cutoff_equal"]
 for v in (a,b):
  need(type(v) is list and len(v)==k and v==sorted(set(v)) and all(type(i) is int and 0<=i<n for i in v),"serialized exact ordered support")
 for v in (upper,ties):
  need(type(v) is list and v==sorted(set(v)) and all(type(i) is int and 0<=i<n-forced for i in v),"serialized strict/tie domains")
 need(not set(upper)&set(ties) and len(upper)<=take and len(upper)+len(ties)>=take,"exact cutoff partition")
 need(a==sorted(upper+ties[:take-len(upper)]+list(range(n-forced,n))),"stable lower-ID exact cutoff fill")
 if take:
  need(type(w["cutoff_bits"]) is str and len(w["cutoff_bits"])==8,"exact finite binary32 cutoff")
  need(bits32(struct.unpack(">f",bytes.fromhex(w["cutoff_bits"]))[0])==w["cutoff_bits"],"finite canonical score bits")
 else:need(w["cutoff_bits"] is None and not upper and not ties,"all-forced empty prior domain")
 changed=sorted(set(a)^set(b))
 need(changed==w["changed_ids"] and (not changed or set(changed)<=set(ties)) and
  w["exact_cutoff_tie_explains_fp64"]==bool(changed),"whole exact tie difference; no borrowed boolean")
 need(type(w["channels32"]) is list and w["channels32"]==w["channels64"] and len(w["channels32"])==32 and len(set(w["channels32"]))==32 and all(type(i) is int and 0<=i<256 for i in w["channels32"]),"independent channel equality")
 return True
def independent(torch,query,kc,vc,rows,lengths,support64,rank=32,budget=128,local=1,capacity=2304):
 """Original BF16 history -> CPU32 selector and separate CPU64 conditional PA.
 CPU32 and CPU64 are both reconstructed; selected candidate tensors not trusted.
 """
 qcpu=query.detach().cpu();kcpu=kc.detach().cpu();vcpu=vc.detach().cpu()
 need(qcpu.dtype==kcpu.dtype==vcpu.dtype==torch.bfloat16 and
  qcpu.shape==(len(lengths),6,256) and kcpu.shape==vcpu.shape and kcpu.shape[1:]==(128,1,256),
  "original BF16 cache/query geometry")
 proofs=[];supports=[];channels=[];pa=[];mixed=[];alphas=[]
 for q,row,n,s64 in zip(qcpu,rows,lengths,support64):
  need(type(n) is int and 0<n<=capacity and len(row)>=(n+127)//128,"known original history")
  ids=torch.tensor(row[:(n+127)//128],dtype=torch.long,device="cpu")
  key=kcpu.index_select(0,ids).reshape(-1,256)[:n]
  val=vcpu.index_select(0,ids).reshape(-1,256)[:n]
  q32=q.float();key32=key.float()
  c32=torch.argsort(q32.abs().sum(0),descending=True,stable=True)[:rank]
  c64=torch.argsort(q.double().abs().sum(0),descending=True,stable=True)[:rank]
  qs=q32.index_select(1,c32);covered=qs.abs().sum(1);total=q32.abs().sum(1)
  tau=torch.sqrt(torch.where(total>0,256*covered/total,torch.ones_like(total)))
  # Match admitted full static domain; invalid padding is exactly -inf before softmax.
  logits=torch.full((6,capacity),float("-inf"),dtype=torch.float32,device="cpu")
  logits[:,:n].copy_((qs@key32.index_select(1,c32).T)/tau[:,None])
  probs=torch.softmax(logits,-1);ranking=probs[:,:n].sum(0)
  need(all(t.dtype==torch.float32 and t.device.type=="cpu" for t in (q32,key32,qs,tau,logits,probs,ranking)),"all selector arithmetic explicit independent CPU32")
  take=min(n,budget)-min(n,local)
  prior=torch.argsort(ranking[:n-min(n,local)],descending=True,stable=True)[:take]
  latest=torch.arange(n-min(n,local),n,dtype=torch.long,device="cpu")
  selected=torch.cat((prior,latest)).sort().values
  proof=classify(ranking.tolist(),selected.tolist(),s64.tolist(),c32.tolist(),c64.tolist(),budget,local)
  validate_witness(proof);proofs.append(proof);supports.append(selected);channels.append(c32)
  # A separate FP64 calculation uses original history and the independently validated domain.
  q64=q.double();key64=key.double();val64=val.double()
  nk=key64.index_select(0,selected);nv=val64.index_select(0,selected)
  weights=torch.softmax((q64@nk.T)/math.sqrt(256),-1)
  exact=weights@nv
  dims=c64;cov=q64.index_select(1,dims).abs().sum(1);tot=q64.abs().sum(1)
  tau64=torch.sqrt(torch.where(tot>0,256*cov/tot,torch.ones_like(tot)))
  prob64=torch.softmax((q64.index_select(1,dims)@key64.index_select(1,dims).T)/tau64[:,None],-1)
  alpha64=prob64.index_select(1,selected).sum(1);mean64=val64.mean(0)
  need(all(t.dtype==torch.float64 and t.device.type=="cpu" for t in (q64,key64,val64,weights,exact,alpha64,mean64)),"independent conditional CPU64 including V and mean")
  pa.append(exact);mixed.append(alpha64[:,None]*exact+(1-alpha64[:,None])*mean64);alphas.append(alpha64)
 return {"witnesses":proofs,"supports":supports,"channels":channels,
  "conditional_pa":torch.stack(pa),"conditional_mixed":torch.stack(mixed),"conditional_alpha":torch.stack(alphas)}
def metrics(torch,actual,expected,dtype):
 a=actual.detach().cpu().double();e=expected.to(dtype).double()
 need(a.shape==e.shape and a.shape[-2:]==(6,256),"every request/head numerical metric")
 er=e.square().mean(-1).sqrt()
 rel=(a-e).square().mean(-1).sqrt()/er
 cos=torch.nn.functional.cosine_similarity(a,e,dim=-1)
 finite=bool(torch.isfinite(a).all() and torch.isfinite(e).all() and (er>0).all())
 passed=finite and bool((rel<=.005).all()) and bool((cos>=.99998).all())
 return {"relative_rms":rel.tolist() if finite else None,"cosine":cos.tolist() if finite else None,"finite":finite,"passed":passed}
