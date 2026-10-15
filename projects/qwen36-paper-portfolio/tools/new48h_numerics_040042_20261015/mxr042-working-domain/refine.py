"""Default-OFF original-A32 Newton correction around unchanged037 launch.

One saved-model-frame diagnostic candidate, NOT a qualified service/timing path.
No device/backend imports. No CPU inverse or native-solve substitution.
"""
import os

ENABLE='MXR_ORIGINAL_A32_RESIDUAL027_ENABLE'
MAX_TOKENS=192
MAX_CHUNKS=4

def plan(boundaries,tokens):
 if type(boundaries)not in(list,tuple)or len(boundaries)<2 or boundaries[0]!=0 or boundaries[-1]!=tokens:raise ValueError('complete source-bound CPU cu boundaries')
 if any(type(x)is not int for x in boundaries)or any(a>b for a,b in zip(boundaries,boundaries[1:])):raise ValueError('integer monotonic CPU boundaries')
 if type(tokens)is not int or not 0<tokens<=MAX_TOKENS:raise ValueError('bounded saved-frame tokens only')
 rows=[(s,start,min(64,eos-start))for s,(bos,eos)in enumerate(zip(boundaries,boundaries[1:]))for start in range(bos,eos,64)]
 if not 0<len(rows)<=MAX_CHUNKS:raise ValueError('bounded saved-frame chunks only')
 return rows

def pack(torch,A,X0,boundaries):
 if A.dtype!=torch.float32 or X0.dtype!=torch.float32 or A.shape!=X0.shape or A.ndim!=4 or A.shape[0]!=1 or tuple(A.shape[2:])!=(12,64)or A.device!=X0.device:raise ValueError('actual original A32 and original037 FP32 workspace')
 rows=plan(boundaries,A.shape[1]);n=len(rows)*12
 ap=torch.zeros((n,64,64),dtype=torch.float32,device=A.device)
 xp=torch.eye(64,dtype=torch.float32,device=A.device).expand(n,64,64).clone()
 for i,(_,start,length)in enumerate(rows):
  ap[i*12:(i+1)*12,:length,:].copy_(A[0,start:start+length].permute(1,0,2))
  xp[i*12:(i+1)*12,:length,:length].copy_(X0[0,start:start+length,:,:length].permute(1,0,2))
 return ap,xp,rows

def correction(torch,original_A_tiles,X0_tiles):
 """R=I-M X0; X1=X0+X0 R, M=I+ORIGINAL A32. Two FP32 bmm."""
 if original_A_tiles.dtype!=torch.float32 or X0_tiles.dtype!=torch.float32 or original_A_tiles.shape!=X0_tiles.shape or original_A_tiles.ndim!=3 or tuple(original_A_tiles.shape[1:])!=(64,64)or original_A_tiles.device!=X0_tiles.device:raise ValueError('same actual FP32 tile domain')
 eye=torch.eye(64,dtype=torch.float32,device=original_A_tiles.device)
 M=original_A_tiles+eye
 R=eye-torch.bmm(M,X0_tiles)
 delta=torch.bmm(X0_tiles,R)
 X1=X0_tiles+delta
 return X1,dict(M=M,R=R,delta=delta,eye=eye)

def scatter(torch,X1,rows,shape):
 if tuple(X1.shape)!=(len(rows)*12,64,64):raise ValueError('complete corrected head/chunk tiles')
 out=torch.zeros(shape,dtype=torch.float32,device=X1.device)
 for i,(_,start,length)in enumerate(rows):out[0,start:start+length,:,:length].copy_(X1[i*12:(i+1)*12,:length,:length].permute(1,0,2))
 return out

def precision_policy(torch):
 """Call ONCE before ALL native/candidate arms in the isolated owned process."""
 if os.environ.get(ENABLE)!='1':raise RuntimeError('explicit new027 optin required')
 matmul=getattr(getattr(torch,'npu',None),'matmul',None)
 if matmul is None or type(getattr(matmul,'allow_hf32',None))is not bool:raise RuntimeError('UNVERIFIED actual torch.npu.matmul.allow_hf32 API; do not guess CANN precision')
 before=matmul.allow_hf32;matmul.allow_hf32=False
 if matmul.allow_hf32 is not False:raise RuntimeError('actual HF32-off readback required')
 return dict(schema='mxr.actual-common-FP32-matmul-policy/v042',before=before,allow_hf32=False,common_to_all_arms=True,scope='isolated eager saved-frame process',FP32_accuracy_still_requires_actual_NPU_oracle=True)

def eager(solver,A,cu32,chunks,dtype,pool,event_backend,boundaries,*,trace=None):
 if os.environ.get(ENABLE)!='1':raise RuntimeError('new027 OFF')
 torch=solver.torch;rows=plan(boundaries,A.shape[1]);tile_n=len(rows)*12
 if chunks!=len(rows)or dtype not in(torch.bfloat16,torch.float16)or A.dtype!=torch.float32 or A.device.type!='npu' or cu32.dtype!=torch.int32:raise ValueError('exact bounded actual NPU/FP32/int32 launch')
 if solver.is_capturing():raise RuntimeError('graph unqualified')
 matmul=getattr(torch.npu,'matmul',None)
 if matmul is None or getattr(matmul,'allow_hf32',None)is not False:raise RuntimeError('common actual FP32 policy not established before all arms')
 # Original input + half conversion + X0 + corrected workspace + final16bit;
 # six packed FP32 matrices, identity and original-I/cu. All strong retained.
 budget=A.numel()*16+tile_n*64*64*4*7+64*64*4*2+cu32.numel()*cu32.element_size()+solver.minus_identity.numel()*solver.minus_identity.element_size()
 ticket=pool.reserve(budget)
 try:
  converted=A.to(torch.float16).contiguous();workspace=torch.zeros_like(converted,dtype=torch.float32)
  ticket.arm((A,converted,workspace,cu32,solver.minus_identity))
  stream=event_backend.current_key();ticket.entering_foreign_launch();solver.launch(converted,cu32,chunks,workspace)
  if event_backend.current_key()!=stream:raise RuntimeError('foreign037 stream changed; quarantine')
  ap,xp,rows=pack(torch,A,workspace,boundaries)
  for v in(ap,xp):ticket.retain_extra(v)
  X1,intermediate=correction(torch,ap,xp)
  for v in(X1,*intermediate.values()):ticket.retain_extra(v)
  corrected=scatter(torch,X1,rows,workspace.shape);output=corrected.to(dtype)
  ticket.retain_extra(corrected);ticket.retain_extra(output)
  if event_backend.current_key()!=stream:raise RuntimeError('correction stream changed; quarantine')
  if trace is not None:trace.update(A32_tiles=ap,X0_FP32=workspace,X0_tiles=xp,R=intermediate['R'],X1_tiles=X1,X1_FP32=corrected)
  ticket.seal(event_backend.record(stream));return output
 except BaseException:
  if ticket.foreign_launch_entered:pool.quarantine(ticket)
  else:pool.abort_before_foreign_launch(ticket)
  raise
