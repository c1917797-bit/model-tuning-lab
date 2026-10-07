"""Independent direct scalar and CPU-FP64 unsplit attention; no native/candidate imports."""
import math
def direct(query,keys,values,scale):
 if not keys:return [0.]*len(query),float("-inf")
 logits=[math.fsum(q*k for q,k in zip(query,key))*scale for key in keys]
 m=max(logits);weights=[math.exp(x-m) for x in logits];total=math.fsum(weights)
 return [math.fsum(w*v[j] for w,v in zip(weights,values))/total for j in range(len(query))],m+math.log(total)
def compose(states,dimension):
 live=[(out,lse) for out,lse,present in states if present]
 if not live:return [0.]*dimension,float("-inf")
 if not all(math.isfinite(lse) and len(out)==dimension and all(math.isfinite(v) for v in out) for out,lse in live):raise ValueError("defined nonfinite state")
 m=max(lse for _,lse in live);weights=[math.exp(lse-m) for _,lse in live];z=math.fsum(weights)
 return [math.fsum(w*out[j] for w,(out,_) in zip(weights,live))/z for j in range(dimension)],m+math.log(z)
def cpu_double(query,keys,values,visible):
 import torch
 # BF16 originals are transferred before conversion; direct full-support,
 # per-query/head matmul and softmax, not partial states or native LSE.
 q=query.detach().cpu().double();k=keys.detach().cpu().double();v=values.detach().cpu().double()
 out=torch.zeros_like(q);lse=torch.full(q.shape[:-1],float("-inf"),dtype=torch.float64)
 for b in range(q.shape[0]):
  for r,n in enumerate(visible[b]):
   if not n:continue
   logits=q[b,:,r]@k[b,0,:n].T/math.sqrt(q.shape[-1])
   out[b,:,r]=torch.softmax(logits,dim=-1)@v[b,0,:n]
   lse[b,:,r]=torch.logsumexp(logits,dim=-1)
 return out,lse
