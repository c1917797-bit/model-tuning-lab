"""Genuine025 Controller/Joints with explicitly registered window/budget deltas.

Never invokes old AdaKV run/main, source(), component() or expired algorithm gates.
This loading alone grants no source/numeric/device/model qualification.
"""
import hashlib,importlib.util,sys
from pathlib import Path
BASE='/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-tp4-model-once-v1-025'
REFS={
 'model_contract':dict(path=BASE+'/model_contract.py',bytes=13660,sha256='82243c277890aef7c24ea5eb5fbfa0658b314a39c01d7b2a7ddf34b2bf363e9f'),
 'safety_host':dict(path=BASE+'/safety_host.py',bytes=22338,sha256='20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'),
 'host_once':dict(path=BASE+'/host_once.py',bytes=18170,sha256='36844e41895b95e810b54ecae32994a96b21258ae8ad8d88fccaac19f035cf8c')}
def raw(ref):
 p=Path(ref['path']);b=p.read_bytes()
 if p.is_symlink()or(len(b),hashlib.sha256(b).hexdigest())!=(ref['bytes'],ref['sha256']):raise ValueError('actual complete025 source')
 return b
def derive_host(b):
 if(len(b),hashlib.sha256(b).hexdigest())!=(REFS['host_once']['bytes'],REFS['host_once']['sha256']):raise ValueError('actual complete025 source before deltas')
 pairs=[(b'self.deadline=start+5400',b'self.deadline=start+3600'),
        (b'remaining=90-self.cleanup_used',b'remaining=180-self.cleanup_used'),
        (b'self.recovery_deadline=now+90',b'self.recovery_deadline=now+180')]
 original=b
 for before,after in pairs:
  if b.count(before)!=1:raise ValueError('exact025 Joint budget delta')
  b=b.replace(before,after)
 inverse=b
 for before,after in reversed(pairs):
  if inverse.count(after)!=1:raise ValueError('inverse unique Joint delta')
  inverse=inverse.replace(after,before)
 if inverse!=original:raise ValueError('whole original025 inverse')
 return b,pairs
def load_source(name,ref,body=None):
 b=raw(ref)
 if name in sys.modules:raise ValueError('fresh private host process required; never replaceforeign source')
 spec=importlib.util.spec_from_file_location(name,ref['path']);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 try:exec(compile(b if body is None else body,ref['path'],'exec'),m.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 return m
def load(output_root=None):
 c=load_source('model_contract',REFS['model_contract'])
 # Whole genuine actual025 IO/helper remains. Only new explicit task scope.
 c.CUTOFF=1792313000;c.CUT='2026-10-18T08:43:20+00:00'
 S=load_source('safety_host',REFS['safety_host'])
 S.PHASE=3600;S.CLEANUP=180;S.OWNER='bole-three-node131-repair18'
 original_env=S.environment
 def environment(cpu=False):
  value=original_env(cpu)
  value.update(VLLM_PLUGINS='ascend',TRITON_CACHE_DIR='/adakv-results/triton',
   VLLM_CACHE_ROOT='/adakv-results/vllm-cache',TORCHINDUCTOR_CACHE_DIR='/adakv-results/inductor')
  return value
 S.environment=environment
 body,pairs=derive_host(raw(REFS['host_once']))
 H=load_source('_mxr_actual025_host_once',REFS['host_once'],body)
 if not(S.MEM==64*c.GIB and S.RESERVE+S.HOST_MEM+S.MEM==73*c.GIB and S.PHYSICAL==(4,5,6,7)):raise ValueError('original73GiB/devicebudget')
 from cap48_provider import prepare
 H._cap48_source_bound_contract=prepare(S,c)
 import contract090 as C,external025
 selected=C.OUT if output_root is None else Path(output_root)
 if selected not in(C.OUT,C.CPU_OUT):raise ValueError('only the two registered131 owned roots')
 import output_scan131r8 as SCAN
 SCAN.install(c,S,selected)
 external025.OUT=selected;external025.install(c,S,H)
 return c,S,H,pairs


