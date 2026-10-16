"""Default-OFF ONE unchanged037 launch + bounded original-A32 refinement.

Three residual rounds / six FP32 products per tile, no D2H/synchronize/capture. No numerical or
service qualification is granted by this source. Existing512MiB pool naturally
backpressures to one longest in-flight inverse rather than raising its limit.
"""
import os
ENABLE='MXR_THIRD_RESIDUAL125_ENABLE'
MAX_TOKENS=40960
MAX_SEQUENCES=16
BLOCK_CHUNKS=64
def plan(boundaries,tokens):
 if type(boundaries)not in(tuple,list)or not 2<=len(boundaries)<=MAX_SEQUENCES+1 or type(tokens)is not int or not 0<tokens<=MAX_TOKENS:raise ValueError('bounded actual total tokens/segments')
 if any(type(x)is not int for x in boundaries)or boundaries[0]!=0 or boundaries[-1]!=tokens or any(a>b for a,b in zip(boundaries,boundaries[1:])):raise ValueError('complete monotonic CPU metadata')
 rows=[(seq,start,min(64,z-start))for seq,(a,z)in enumerate(zip(boundaries,boundaries[1:]))for start in range(a,z,64)]
 if not rows:raise ValueError('empty inverse dispatch')
 # Full contiguous chunks use one strided pack/scatter per group. Tail chunks
 # are independent matrices and collected separately, never padded as requests.
 groups=[];run=[];tails=[]
 def flush():
  if run:groups.append(list(run));run.clear()
 for row in rows:
  if row[2]<64:flush();tails.append(row);continue
  if run and(row[1]!=run[-1][1]+64 or len(run)==BLOCK_CHUNKS):flush()
  run.append(row)
 flush()
 for i in range(0,len(tails),BLOCK_CHUNKS):groups.append(tails[i:i+BLOCK_CHUNKS])
 return rows,groups
def budget(boundaries,tokens):
 rows,groups=plan(boundaries,tokens)
 # Six packed FP32 matrices + explicit FP32 scatter workspace and identity.
 scratch=7*BLOCK_CHUNKS*12*64*64*4+64*64*4
 input_bytes=tokens*12*64*4;converted=tokens*12*64*2;workspace=input_bytes;output=converted
 total=input_bytes+converted+workspace+output+scratch+len(boundaries)*4+64*64*2
 return dict(total_tokens=tokens,sequences=len(boundaries)-1,chunks=len(rows),groups=len(groups),official037_launches=1,FP32_bmm_launches=6*len(groups),input_bytes=input_bytes,converted_bytes=converted,X0_workspace_bytes=workspace,output_bytes=output,scratch_bytes=scratch,cu_bytes=len(boundaries)*4,minus_identity_bytes=64*64*2,keepalive_bytes=total,two_live_bytes=2*total,existing_formal_pool_bytes=512*1024**2,existing_diagnostic_pool_bytes=32*1024**2,formal_one_live_fit=total<=512*1024**2,formal_two_live_fit=2*total<=512*1024**2,backend_allocator_workspace_measured=False)
def storage_budget(A,cu32,planned):
 a=A.untyped_storage().nbytes();c=cu32.untyped_storage().nbytes()
 if type(a)is not int or type(c)is not int or a<A.numel()*A.element_size()or c<cu32.numel()*cu32.element_size():raise ValueError('actual backing storage metadata')
 return planned['keepalive_bytes']-planned['input_bytes']-cu32.numel()*4+a+c
def allocate(torch,A):
 n=BLOCK_CHUNKS*12
 return dict(**{name:torch.empty((n,64,64),dtype=torch.float32,device=A.device)for name in('ap','xp','M','R','delta','X1')},scatter=torch.empty((1,BLOCK_CHUNKS*64,12,64),dtype=torch.float32,device=A.device),eye=torch.eye(64,dtype=torch.float32,device=A.device))
def _correct_blocks(torch,A,X0,groups,output,scratch,trace=None):
 for rows in groups:
  n=len(rows)*12;ap,xp,M,R,delta,X1=(scratch[k][:n]for k in('ap','xp','M','R','delta','X1'));eye=scratch['eye']
  contiguous=all(length==64 for _,_,length in rows)and all(z[1]==a[1]+64 for a,z in zip(rows,rows[1:]))
  if contiguous:
   begin=rows[0][1];end=rows[-1][1]+64;count=len(rows)
   ap.view(count,12,64,64).copy_(A[0,begin:end].view(count,64,12,64).permute(0,2,1,3))
   xp.view(count,12,64,64).copy_(X0[0,begin:end].view(count,64,12,64).permute(0,2,1,3))
  else:
   ap.zero_();xp.copy_(eye.expand_as(xp))
   for i,(_,start,length)in enumerate(rows):
    ap[i*12:(i+1)*12,:length].copy_(A[0,start:start+length].permute(1,0,2))
    xp[i*12:(i+1)*12,:length,:length].copy_(X0[0,start:start+length,:,:length].permute(1,0,2))
  saved={}if trace is not None else None
  if saved is not None:saved.update(A32=ap.clone(),X0=xp.clone())
  M.copy_(ap);M.add_(eye)
  for iteration in range(3):
   torch.bmm(M,xp,out=R);R.neg_();R.add_(eye)
   torch.bmm(xp,R,out=delta);torch.add(xp,delta,out=X1)
   if saved is not None:saved.update(**{'X'+str(iteration+1):X1.clone(),'R'+str(iteration+1):R.clone()})
   if iteration<2:xp.copy_(X1)
  if saved is not None:trace.append(dict(rows=rows,**saved))
  if contiguous:
   scatter=scratch['scatter'][:,:end-begin]
   scatter.view(count,64,12,64).permute(0,2,1,3).copy_(X1.view(count,12,64,64))
   output[:,begin:end].copy_(scatter)
  else:
   for i,(_,start,length)in enumerate(rows):output[0,start:start+length,:,:length].copy_(X1[i*12:(i+1)*12,:length,:length].permute(1,0,2))
 return output
def cpu_with_X0(torch,A,X0,boundaries):
 """Software equation/index equivalence, not an independent NPU oracle."""
 if A.device.type!='cpu'or A.dtype!=torch.float32 or A.shape!=X0.shape or not A.is_contiguous()or tuple(A.shape[2:])!=(12,64):raise ValueError('CPU actual-shape originalA32/X0')
 _,groups=plan(boundaries,A.shape[1]);return _correct_blocks(torch,A,X0,groups,torch.zeros_like(A,dtype=torch.bfloat16),allocate(torch,A))
def eager(solver,A,cu32,chunks,dtype,pool,event_backend,boundaries,*,trace=None):
 if os.environ.get(ENABLE)!='1':raise RuntimeError('044 OFF')
 torch=solver.torch;rows,groups=plan(boundaries,A.shape[1]);b=budget(boundaries,A.shape[1])
 if A.device.type!='npu'or A.device!=solver.device or A.dtype!=torch.float32 or A.ndim!=4 or A.shape[0]!=1 or tuple(A.shape[2:])!=(12,64)or not A.is_contiguous()or dtype!=torch.bfloat16 or cu32.dtype!=torch.int32 or cu32.device!=A.device or cu32.numel()!=len(boundaries)or chunks!=len(rows):raise ValueError('source-bound eager Qwen local H12/chunk64 BF16 domain')
 if solver.is_capturing():raise RuntimeError('graph unqualified')
 if getattr(getattr(torch.npu,'matmul',None),'allow_hf32',None)is not False:raise RuntimeError('same common HF32off must precede BOTH pair arms')
 if pool.max_bytes!=512*1024**2 or pool.max_entries!=2:raise ValueError('existing formal512MiB/2entries pool required; diagnostic32MiB insufficient')
 ticket=pool.reserve(storage_budget(A,cu32,b)+(8*len(rows)*12*64*64*4 if trace is not None else 0))
 try:
  converted=A.to(torch.float16).contiguous();workspace=torch.zeros_like(converted,dtype=torch.float32);output=torch.zeros_like(A,dtype=dtype);scratch=allocate(torch,A)
  ticket.arm((A,cu32,converted,workspace,output,solver.minus_identity,*scratch.values()));stream=event_backend.current_key();ticket.entering_foreign_launch()
  solver.launch(converted,cu32,chunks,workspace)
  if event_backend.current_key()!=stream:raise RuntimeError('037 stream changed')
  _correct_blocks(torch,A,workspace,groups,output,scratch,trace)
  if trace is not None:
   for group in trace:
    for value in group.values():
     if torch.is_tensor(value):ticket.retain_extra(value)
  if event_backend.current_key()!=stream:raise RuntimeError('refinement stream changed')
  ticket.seal(event_backend.record(stream));return output
 except BaseException:
  if ticket.foreign_launch_entered:pool.quarantine(ticket)
  else:pool.abort_before_foreign_launch(ticket)
  raise
