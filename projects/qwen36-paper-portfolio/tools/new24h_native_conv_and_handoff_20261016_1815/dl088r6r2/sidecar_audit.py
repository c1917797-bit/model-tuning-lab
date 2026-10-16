"""Independent CPU64 local recurrence for actual calls, not candidate math."""
import math
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
def audit(torch,R,P,s,*,overflow=False,numeric=True):
 b=s['before'];a=s['after'];d=s['debug_after']
 if not(len(b)==len(a)==len(d)==13):raise ValueError('all13 actual tensors required')
 if len(s['debug_before'])!=13 or not all(P.bits(torch,x,y)for x,y in zip(b,s['debug_before'])):raise ValueError('actual production/debug before bytes')
 if not all(P.bits(torch,x,y)for x,y in zip(a,d)):raise ValueError('production/debug six-state and input bytes')
 if not P.bits(torch,s['production_output'],s['debug_output']):raise ValueError('production/debug output bytes')
 if not all(P.bits(torch,b[k],a[k])for k in(0,1,2,3,4,11,12)):raise ValueError('inputs/sequence/slot mutated')
 if s['pointers_before']!=s['pointers_after']or s['debug_pointers_before']!=s['debug_pointers_after']or not P.bits(torch,s['sidecar_guards_before'],s['sidecar_guards_after']):raise ValueError('pointers/redzones')
 if not numeric:return dict(passed=True,numeric_checked_in_mixed_per_request=True,production_debug_bitwise=True,actual_input_immutable=True,actual_guard_pointer_pass=True)
 before=dict(zip(FIELDS,b[5:11]));after=dict(zip(FIELDS,a[5:11]));inputs=dict(zip(('query','key','value','g','beta'),b[:5]));truth=[];states=[];ids=b[12].flatten().tolist()
 if len(ids)!=len(set(ids))or not ids:raise ValueError('nonempty distinct active slots')
 for j,slot in enumerate(ids):
  expected,y=R.advance(torch,R.restore(torch,before,slot),inputs,j);truth.append(y);actual=R.restore(torch,after,slot)
  if not bool(torch.isfinite(expected).all()and torch.isfinite(actual).all()):raise ValueError('finite represented state')
  err=float((actual-expected).norm());norm=float(expected.norm());e=err/norm if norm else(0. if err==0 else math.inf);states.append(e)
 pred=P.evaluate(torch,s['actual_precast_FP32'],s['production_output'],torch.stack(truth))
 state_pass=all(math.isfinite(e)and e<=R.STATE_LIMIT for e in states)
 passed=state_pass and ((not pred['finite']and not pred['passed'])if overflow else pred['passed'])
 return dict(passed=passed,expected_overflow_rejection=overflow,actual_precast=pred,state_errors=states,production_debug_bitwise=True,actual_input_immutable=True,actual_guard_pointer_pass=True,reference='CPU64 local recurrence from captured before; NOT whole independent trajectory')
