"""Independent R5 whole3600 / cleanup90 / maximum child2700; no completion guarantee."""
import math,time
WHOLE=3600.;CLEANUP=90.;CHILD=2700.;FINAL=300.;PRE=420.;MARGIN=90.
def positive(v,name):
 if type(v)not in(int,float)or not math.isfinite(v)or v<=0:raise ValueError(name)
 return float(v)
def profile(m):
 p=m.get('cpu_budget_profile')
 if type(p)is not dict or set(p)!={'schema','measurement_ref','final_fence_reserve_seconds','cleanup_reserve_seconds','predicted_child_seconds','safety_margin_seconds'}or p['schema']!='deltalog.registered-CPU-recovery-profile/v127-repair5':raise ValueError('pending source-bound measured budget profile')
 positive(p['final_fence_reserve_seconds'],'positive measured final fence reserve');positive(p['predicted_child_seconds'],'positive measured complete child bound');positive(p['safety_margin_seconds'],'positive safety margin')
 if p['cleanup_reserve_seconds']!=CLEANUP or p['predicted_child_seconds']!=CHILD or p['final_fence_reserve_seconds']!=FINAL or p['safety_margin_seconds']!=MARGIN:raise ValueError('exact new operational registration')
 return p
def child_cap(deadline,p,now=None):
 left=deadline-(time.monotonic()if now is None else now)-CLEANUP-p['final_fence_reserve_seconds']-p['safety_margin_seconds']
 if left<=0:raise ValueError('no child time remains inside whole3600 and all reserves')
 return min(CHILD,left)
def remaining(deadline,*,now=None):
 left=deadline-(time.monotonic()if now is None else now)
 if left<=0:raise ValueError('whole CPU3600 deadline including source fences')
 return left
