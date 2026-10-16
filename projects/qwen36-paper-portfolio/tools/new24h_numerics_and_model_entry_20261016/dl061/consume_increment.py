"""Independent CPU64 live-only represented-state oracle; no candidate import."""
import math
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
def equalbytes(torch,a,b):
 return a.dtype==b.dtype and a.shape==b.shape and torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
def check(torch,row):
 before,after=row['before'],row['after'];ids=row['ids'].flatten().tolist()
 if not row['actual_NPU']or not ids or len(ids)!=len(set(ids)):raise ValueError('actual nonempty distinct NPU selection')
 slots=before['base'].shape[0];worst=0.;zero=partial=False
 for s in range(slots):
  if s not in ids:
   if not all(equalbytes(torch,before[n][s],after[n][s])for n in FIELDS):raise ValueError('foreign slot mutated')
   continue
  expected=before['base'][s].double().clone()
  for h in range(12):
   length=int(before['length'][s,h,0]);decay=float(before['decay'][s,h,0]);zero|=length==0;partial|=0<length<7
   if not 0<=length<=7:raise ValueError('length')
   expected[h]*=math.exp(decay)
   for j in range(length):
    u=before['u_log'][s,h,j].double();k=before['k_log'][s,h//3,j].double();c=math.exp(decay-float(before['lambda_log'][s,h,j]))
    expected[h]+=c*u[:,None]*k[None,:]
  actual=after['base'][s].double()
  if not bool(torch.isfinite(expected).all()and torch.isfinite(actual).all()):raise ValueError('live finite')
  ratio=float((actual-expected).norm()/expected.norm())if float(expected.norm())else(0. if bool((actual==0).all())else float('inf'))
  if not math.isfinite(ratio)or ratio>7.92e-7:raise ValueError('original FP32 state limit')
  worst=max(worst,ratio)
  if not all(bool((after[n][s]==0).all())for n in('decay','length')):raise ValueError('reset')
  if not all(equalbytes(torch,before[n][s],after[n][s])for n in('k_log','u_log','lambda_log')):raise ValueError('payload rewritten')
 return dict(state_error=worst,length0=zero,partial_live=partial,foreign_unchanged=True)
