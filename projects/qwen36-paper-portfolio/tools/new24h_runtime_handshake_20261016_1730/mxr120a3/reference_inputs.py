"""Independent CPU chunk64 equations with explicit documented storage boundaries.

Diagnostic proposal only: canonical CPU FP32 dot/exp are NOT instruction-exact
AscendC/Triton emulation. This module cannot grant a numerical qualification.
No candidate code, native operator, saved output or saved inverse is imported.
"""
def postnormalize(torch,x,*,source_eps=1e-6):
 """Independent pinned l2norm semantic boundary, not F.normalize(max(norm,eps))."""
 if source_eps!=1e-6:raise ValueError('fixed source epsilon, not experimental tuning')
 y=dict(x)
 for n in ('q','k'):
  a=x[n]
  if a.device.type!='cpu'or a.dtype!=torch.bfloat16:raise ValueError('BF16 CPU normalizer input')
  z=a.float();y[n]=(z*torch.rsqrt((z*z).sum(-1,keepdim=True)+1e-6)).to(a.dtype)
 y['already_normalized']=True;return y

def evaluate_captured_prefill(torch,capture):
 """DL raw captures.prefill entry; independent output ignores native result."""
 x=dict(capture['inputs'])
 if x.get('use_qk_l2norm_in_kernel')is not True:raise ValueError('actual raw pre-normalizer boundary required')
 if tuple(x['q'].shape[2:])!=(4,128)or tuple(x['v'].shape[2:])!=(12,128):raise ValueError('registered TP4-local Qwen geometry')
 if x['cu_seqlens'].tolist()not in([0,64],[0,129]):raise ValueError('explicit single-segment64 or129 draft only')
 return evaluate(torch,postnormalize(torch,x))

def evaluate(torch,x,*,storage_boundaries=True,chunk_size=64,actual_A=None,actual_G=None):
 q,k,v,g,beta=[x[n]for n in ('q','k','v','g','beta')]
 if any(t.device.type!='cpu'for t in (q,k,v,g,beta,x['initial_state'])):raise ValueError('CPU-only independent oracle')
 if q.ndim!=4 or q.shape[0]!=1 or q.shape!=k.shape or v.shape[:2]!=q.shape[:2]or v.shape[2]%q.shape[2]:raise ValueError('packed GQA geometry')
 if chunk_size!=64 or any(t.dtype!=torch.bfloat16 for t in(q,k,v)):raise ValueError('source-bound chunk64 BF16 inputs')
 cu=x['cu_seqlens'].tolist()
 if cu[0]!=0 or cu[-1]!=q.shape[1]or any(a>=z for a,z in zip(cu,cu[1:])):raise ValueError('complete nonempty segments')
 if x.get('already_normalized')is not True:raise ValueError('post-normalizer boundary required; no guessed epsilon')
 H=v.shape[2];D=q.shape[-1];V=v.shape[-1];group=H//q.shape[2]
 if x['initial_state'].shape!=(len(cu)-1,H,D,V):raise ValueError('initial state layout N,H,K,V')
 q=q.double().repeat_interleave(group,dim=2);k=k.double().repeat_interleave(group,dim=2);v=v.double();g=g.double();beta=beta.double()
 def f32(t):return t.float().double()if storage_boundaries else t
 def bf16(t):return t.to(torch.bfloat16).double()if storage_boundaries else t
 def mm(a,b):return f32(a@b)
 scale=float(x.get('scale',D**-.5));out=torch.empty_like(v);states=[];trace=[]
 for segment,(bos,eos)in enumerate(zip(cu,cu[1:])):
  # Native HType=INPUT_TYPE, including FP32 initial-state->BF16 CAST_RINT.
  state=bf16(x['initial_state'][segment].double())
  for start in range(bos,eos,64):
   stop=min(start+64,eos);n=stop-start
   Q,K,Vv=[t[0,start:stop].transpose(0,1)for t in(q,k,v)]
   G=f32(g[0,start:stop].transpose(0,1));BETA=beta[0,start:stop].transpose(0,1)
   C=f32(torch.cumsum(G,dim=-1)) if actual_G is None else actual_G[0,start:stop].transpose(0,1).double();E=f32(torch.exp(C));diff=f32(C[:,:,None]-C[:,None,:]);decay=f32(torch.exp(diff.clamp(max=0)))
   A=torch.tril(f32(f32(mm(K,K.transpose(-1,-2))*decay)*BETA[:,:,None]),diagonal=-1)
   if actual_A is not None:A=actual_A[0,start:stop].permute(1,0,2).double().contiguous()
   eye=torch.eye(n,dtype=torch.float64).expand(H,n,n)
   inverse=torch.linalg.solve_triangular(eye+A,eye,upper=False,unitriangular=True)
   B=bf16(inverse)  # solve_tril output_dtype=k.dtype, independent inverse.
   U=bf16(mm(B,f32(Vv*BETA[:,:,None])))
   W=bf16(mm(B,f32(f32(K*BETA[:,:,None])*E[:,:,None])))
   hstart=bf16(state)
   delta=f32(U-mm(W,hstart));vnew=bf16(delta)
   end_decay=f32(torch.exp(f32(C[:,-1:]-C)))
   decay_vnew=bf16(f32(delta*end_decay[:,:,None]))
   hend=f32(f32(hstart*f32(torch.exp(C[:,-1]))[:,None,None])+mm(K.transpose(-1,-2),decay_vnew))
   QK=mm(Q,K.transpose(-1,-2));masked=bf16(torch.tril(f32(QK*decay)))
   values=f32(f32(mm(Q,hstart)*E[:,:,None])+mm(masked,vnew))
   output=bf16(f32(values*scale));out[0,start:stop]=output.transpose(0,1)
   # FinalStateType=FP32, intermediate H output remains INPUT_TYPE=BF16.
   state=hend if stop==eos else bf16(hend)
   trace.append(dict(segment=segment,start=start,stop=stop,g_cumsum=C,A32=A,inverse_FP64=inverse,B=B,W=W,U=U,Hstart=hstart,vnew=vnew,decayed_vnew=decay_vnew,Hend=hend,masked_QK=masked,output=output))
  states.append(state)
 return dict(output=out,state=torch.stack(states),trace=trace,storage_boundaries=storage_boundaries,numerical_qualification_granted=False,reference_kind='independent-chunk-equations-canonical-storage-rounding',actual_Ascend_accumulation_order_qualified=False,actual_exp_qualified=False,actual027_consumed=False)
