"""Independent FP64 block linear-system GDN oracle, not candidate code.
Derivation: u_i + beta_i sum_{j<i} exp(G_i-G_j) (k_i.k_j)u_j
 = beta_i(v_i-exp(G_i)k_i.S0). torch.linalg.solve_triangular solves it.
CPU Torch64 only, original state recurrence used independently in tests.
"""
def recurrence(torch,x,block=64):
 q,k,v,g,b=x['q'],x['k'],x['v'],x['g'],x['beta']
 if q.device.type!='cpu'or q.ndim!=4 or q.shape[0]!=1 or x.get('already_normalized')is not True:raise ValueError('actual complete normalized CPU boundary only')
 if q.shape!=k.shape or v.shape[:2]!=q.shape[:2]or v.shape[2]%q.shape[2]:raise ValueError('GQA geometry')
 if type(block)is not int or not 1<=block<=64:raise ValueError('bounded independent oracle block')
 cu=x['cu_seqlens'].tolist();T=q.shape[1];H=v.shape[2]
 if cu[0]!=0 or cu[-1]!=T or any(a>=z for a,z in zip(cu,cu[1:])):raise ValueError('complete packed segments')
 initial=x['initial_state']
 if tuple(initial.shape)!=(len(cu)-1,H,k.shape[-1],v.shape[-1]):raise ValueError('full state')
 group=H//q.shape[2];outputs=torch.empty(v.shape,dtype=torch.float64);final=[];scale=float(x['scale'])
 for segment,(start,stop)in enumerate(zip(cu,cu[1:])):
  s=initial[segment].double().clone()
  for a in range(start,stop,block):
   z=min(stop,a+block);n=z-a
   Q=q[0,a:z].double().repeat_interleave(group,dim=1).transpose(0,1)
   K=k[0,a:z].double().repeat_interleave(group,dim=1).transpose(0,1)
   V=v[0,a:z].double().transpose(0,1);G=g[0,a:z].double().transpose(0,1).cumsum(-1);B=b[0,a:z].double().transpose(0,1)
   lower=torch.ones((n,n),dtype=torch.bool).tril();strict=lower&~torch.eye(n,dtype=torch.bool)
   diff=G[:,:,None]-G[:,None,:];decay=torch.exp(diff.masked_fill(~lower,float('-inf')))
   lhs=(K@K.transpose(-1,-2))*decay*B[:,:,None]
   lhs=lhs.masked_fill(~strict,0)+torch.eye(n,dtype=torch.float64)
   rhs=B[:,:,None]*(V-torch.exp(G)[:,:,None]*(K@s))
   U=torch.linalg.solve_triangular(lhs,rhs,upper=False,unitriangular=True)
   O=(Q@K.transpose(-1,-2))*decay
   outputs[0,a:z]=(scale*(torch.exp(G)[:,:,None]*(Q@s)+O@U)).transpose(0,1)
   tail=torch.exp(G[:,-1,None]-G)
   s=torch.exp(G[:,-1])[:,None,None]*s+K.transpose(-1,-2)@(tail[:,:,None]*U)
  final.append(s)
 return outputs,torch.stack(final)
