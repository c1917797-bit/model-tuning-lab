"""Untimed real precision facts; only original106 apply changes HF32 flags."""
import hashlib
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def observe(torch,common_source,policy,phase):
 flags=dict(enabled=torch.are_deterministic_algorithms_enabled(),warn_only=torch.is_deterministic_algorithms_warn_only_enabled())
 h=dict(matmul=torch.npu.matmul.allow_hf32,conv=torch.npu.conv.allow_hf32)
 need(all(type(x)is bool for x in[*flags.values(),*h.values()]),'actual Boolean precision/deterministic flags')
 need(h==dict(matmul=False,conv=False),'same explicit common HF32OFF context')
 return dict(schema='deltalog.actual-precision-context/v122R3',common_source=common_source,policy=dict(policy),HF32=h,deterministic=flags,phase=phase)
def apply(torch,common,common_source,phase):
 need(ref(common.__file__)==common_source,'exact same106 common precision source')
 before=dict(enabled=torch.are_deterministic_algorithms_enabled(),warn_only=torch.is_deterministic_algorithms_warn_only_enabled())
 policy=common.apply_precision(torch);v=observe(torch,common_source,policy,phase)
 need(v['deterministic']==before,'common policy must not change deterministic configuration')
 return v
def stable(torch,before,phase):
 after=observe(torch,before['common_source'],before['policy'],phase);validate_pair(before,after,before['common_source']);return after
def validate_pair(before,after,source):
 for v in(before,after):
  need(v['schema']=='deltalog.actual-precision-context/v122R3'and v['common_source']==source,'same source-bound precision receipt')
  need(v['HF32']==dict(matmul=False,conv=False)and all(type(x)is bool for x in v['HF32'].values()),'actual HF32OFF')
  need(set(v['deterministic'])=={'enabled','warn_only'}and all(type(x)is bool for x in v['deterministic'].values()),'actual deterministic flags, not asserted defaults')
 need(before['deterministic']==after['deterministic']and before['policy']==after['policy'],'precision context changed during actual phase')
 return True
