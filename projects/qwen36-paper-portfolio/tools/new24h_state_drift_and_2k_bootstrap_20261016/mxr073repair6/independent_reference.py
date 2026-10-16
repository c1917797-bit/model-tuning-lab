"""Independent CPU64 GDN recurrence; not candidate/chunk/triangular logic."""
def recurrence(torch,x):
 q,k,v,g,b=x['q'],x['k'],x['v'],x['g'],x['beta']
 if q.device.type!='cpu' or q.ndim!=4 or q.shape[0]!=1:raise ValueError('actual packed CPU input')
 if not(q.shape==k.shape and v.shape[:2]==q.shape[:2] and v.shape[2]%q.shape[2]==0):raise ValueError('actual GQA geometry')
 cu=x['cu_seqlens'].tolist()
 if cu[0]!=0 or cu[-1]!=q.shape[1]or any(a>=z for a,z in zip(cu,cu[1:])):raise ValueError('actual complete packed segments')
 # Source-native normalizer outputs in the original q/k dtype. No candidate arithmetic.
 if x.get('already_normalized')is True:q,k=q.double(),k.double()
 else:
  q=torch.nn.functional.normalize(q.float(),p=2,dim=-1).to(q.dtype).double()
  k=torch.nn.functional.normalize(k.float(),p=2,dim=-1).to(k.dtype).double()
 group=v.shape[2]//q.shape[2];q=q.repeat_interleave(group,dim=2);k=k.repeat_interleave(group,dim=2)
 v,g,b=v.double(),g.double(),b.double()
 initial=x['initial_state'].double();scale=float(x.get('scale',q.shape[-1]**-.5))
 outputs=torch.empty_like(v);final=[]
 if initial.shape!=(len(cu)-1,v.shape[2],k.shape[-1],v.shape[-1]):raise ValueError('real complete initial state')
 for segment,(a,z)in enumerate(zip(cu,cu[1:])):
  s=initial[segment].clone()
  for t in range(a,z):
   s=s*torch.exp(g[0,t])[:,None,None]
   predicted=torch.einsum('hkv,hk->hv',s,k[0,t])
   delta=(v[0,t]-predicted)*b[0,t,:,None]
   s=s+k[0,t,:,:,None]*delta[:,None,:]
   outputs[0,t]=torch.einsum('hk,hkv->hv',q[0,t]*scale,s)
  final.append(s)
 return outputs,torch.stack(final)
