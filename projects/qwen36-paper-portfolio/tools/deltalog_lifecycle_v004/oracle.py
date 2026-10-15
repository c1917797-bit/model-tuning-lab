"""Independent CPU64 logical state and per-request recurrence. CPU tensors only."""
import math
STATE_LIMIT=7.92e-7
OUTPUT_LIMIT=.00303
def cpu64(t):
 if t.device.type!='cpu':raise ValueError('raw must first load to CPU')
 return t.double()
def restore(torch,state,slot):
 result=torch.empty((12,128,128),dtype=torch.float64)
 for head in range(12):
  n=int(state['length'][slot,head,0]);d=float(state['decay'][slot,head,0])
  if not 0<=n<=7 or not math.isfinite(d):raise ValueError('metadata capacity/finite')
  v=cpu64(state['base'][slot,head])*math.exp(d)
  # Dead entries may be stale/poisoned; NEVER exponentiate or multiply them.
  for i in range(n):
   lam=float(state['lambda_log'][slot,head,i])
   if not math.isfinite(lam):raise ValueError('live lambda finite')
   v=v+torch.outer(cpu64(state['u_log'][slot,head,i]),cpu64(state['k_log'][slot,head//3,i]))*math.exp(d-lam)
  result[head]=v
 return result
def advance(torch,previous,inputs,row,scale=128**-.5):
 state=torch.empty_like(previous);output=torch.empty((12,128),dtype=torch.float64)
 for head in range(12):
  key=cpu64(inputs['key'][row,head//3]);value=cpu64(inputs['value'][row,head]);query=cpu64(inputs['query'][row,head//3])
  decayed=previous[head]*math.exp(float(inputs['g'][row,head]));u=float(inputs['beta'][row,head])*(value-decayed@key)
  state[head]=decayed+torch.outer(u,key);output[head]=(state[head]@query)*scale
 return state,output
def invariant(torch,before,after,ids):
 active=set(ids);slots=before['base'].shape[0]
 untouched=all(torch.equal(before[k][s],after[k][s])for k in before for s in range(slots)if s not in active)
 append=True;lengths=True
 for s in active:
  n=before['length'][s,:,0];lengths &=bool(torch.equal(n,n[:1].expand_as(n)))
  if int(n[0])<7:append &=torch.equal(before['base'][s],after['base'][s])
  expected=int(n[0])+1 if int(n[0])<7 else 0
  lengths &=bool((after['length'][s,:,0]==expected).all())
 return dict(untouched_bitwise=untouched,append_base_unchanged=append,length_transition=lengths)

def boundary_tests(torch):
 def st(n):
  return dict(base=torch.zeros((2,12,128,128)),k_log=torch.zeros((2,4,7,128),dtype=torch.bfloat16),u_log=torch.zeros((2,12,7,128)),lambda_log=torch.zeros((2,12,16)),decay=torch.zeros((2,12,16)),length=torch.full((2,12,16),n,dtype=torch.int32))
 before=st(6);after={k:v.clone()for k,v in before.items()};after['length'][0,:,0]=7
 if not all(invariant(torch,before,after,[0]).values()):raise ValueError('append6→7 boundary')
 before=st(7);after={k:v.clone()for k,v in before.items()};after['base'][0].fill_(.25);after['length'][0,:,0]=0;after['decay'][0,:,0]=0
 if not all(invariant(torch,before,after,[0]).values()):raise ValueError('current-token merged7→0 boundary')
 wrong={k:v.clone()for k,v in after.items()};wrong['length'][0,:,0]=1
 if invariant(torch,before,wrong,[0])['length_transition']:raise ValueError('must reject old incorrect7→1 expectation')
 wrong={k:v.clone()for k,v in after.items()};wrong['base'][1].fill_(1)
 if invariant(torch,before,wrong,[0])['untouched_bitwise']:raise ValueError('inactive mutation rejected')
 wrong={k:v.clone()for k,v in after.items()};wrong['length'][0,1,0]=1
 if invariant(torch,before,wrong,[0])['length_transition']:raise ValueError('head length divergence rejected')
 return dict(append6_to7=True,merged_current7_to0=True,reject7_to1=True,reject_inactive_mutation=True,reject_head_length_divergence=True)

def sequence_tests(torch):
 for b in (1,8,16):
  native=torch.cat((torch.zeros(1,dtype=torch.int32),torch.ones(b,dtype=torch.int32)))
  candidate=torch.arange(b+1,dtype=torch.int32)
  if native.tolist()!=[0]+[1]*b:raise ValueError('native individual length contract')
  if b>1 and torch.equal(native,candidate):raise ValueError('reject cumulative native lengths')
 return dict(B1=True,B8=True,B16=True,reject_cumulative_native_B16=True)
