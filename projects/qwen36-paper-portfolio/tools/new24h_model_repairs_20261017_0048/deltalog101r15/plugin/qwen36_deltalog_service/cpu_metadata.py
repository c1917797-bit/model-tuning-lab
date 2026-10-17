"""CPU-only checks for a future source-bound builder mirror. Not installed.

This cannot authorize execution: the exact builder CPU->device provenance
adapter is deliberately absent until the actual source is inspected.
"""
from dataclasses import dataclass

def need(v,m):
 if not v:raise ValueError(m)

def _ints(xs):
 need(type(xs) in (list,tuple) and all(type(x)is int for x in xs),'already-CPU integer metadata; no Tensor conversion')
 return tuple(xs)

@dataclass(frozen=True)
class CheckedCPU:
 decode:tuple
 prefill:tuple
 individual_decode_lengths:tuple
 prefill_has_initial:tuple
 slots:int

def check_cpu(decode,prefill,individual_decode_lengths,prefill_has_initial,slots):
 d,p,s=map(_ints,(decode,prefill,individual_decode_lengths))
 need(type(slots)is int and slots>0,'positive real arena slot count')
 need(type(prefill_has_initial) in(list,tuple)and all(type(x)is bool for x in prefill_has_initial),'CPU native initial-state mask')
 h=tuple(prefill_has_initial)
 need(len(d)<=16 and len(h)==len(p),'non-spec decode and exact prefill mask length')
 need(all(0<=x<slots for x in d+p),'slot bounds')
 need(len(set(d))==len(d)and len(set(p))==len(p)and not set(d)&set(p),'no concurrent duplicates or mixed temporal alias')
 need(s==(0,)+(1,)*len(d),'native individual lengths, not cumulative prefix lengths')
 return CheckedCPU(d,p,s,h,slots)

def tensor_identity(t):
 # Shape/stride/pointers only. Never reads values or synchronizes a device.
 return (tuple(t.shape),tuple(t.stride()),t.storage_offset(),t.data_ptr(),str(t.dtype),str(t.device))

def require_same_native_view(actual,native,n):
 expected=native[:n]
 need(tensor_identity(actual)==tensor_identity(expected),'native first-num-decoded view, not separately reconstructed indices')

def activate(*args,**kwargs):
 raise RuntimeError('BLOCKED: exact actual builder CPU-source/copy/reorder/version provenance not bound; no production activation')
