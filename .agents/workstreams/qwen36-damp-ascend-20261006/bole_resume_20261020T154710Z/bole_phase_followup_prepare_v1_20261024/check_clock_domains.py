"""Host-only full domain clock seam checks; no source materialize or authority."""
import importlib.util,sys,json,hashlib,types
from pathlib import Path
W=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
HERE=Path(__file__).resolve().parent
V3=W/'bole_phase_clock_prepare_v1_20261024/phase_runtime_renderer_v3/assets'
OLD=W/'bole_v16_followup_prepare_v2_20261024'
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
D=load(HERE/'clock_delta.py','_exact_followup_clock')
A=load(V3/'adapt_phase_clock.py','_existing_phase_adapter')
raw=(V3/'shared_phase_clock.py').read_bytes()
assert len(raw)==10121 and hashlib.sha256(raw).hexdigest()=='d110f4cfc4fd2a3298ea2a0a66206452f6320b3c28a0b0f5c8f1d1581edfa587'
H=types.ModuleType('_derived_followup_clock');exec(compile(D.helper(raw),'shared_phase_clock.py','exec'),H.__dict__)
r=dict(path='/fixture/formal',bytes=1,sha256='1'*64);old=dict(path='/fixture/historical',bytes=1,sha256='2'*64)
assert H.authority_reference(dict(formal_source_schema='bole.current32k-fixed1024-whole/v1',formal_authority_ref=r,qualification_authority_ref=old))==r
assert H.authority_reference(dict(qualification_source_schema='bole.fastpath-32k160-lossless-whole-source/v1',qualification_authority_ref=r))==r
for m in [dict(formal_source_schema='wrong',formal_authority_ref=r,qualification_authority_ref=old),dict(formal_source_schema='bole.current32k-fixed1024-whole/v1',formal_authority_ref=None,qualification_authority_ref=old),dict(qualification_source_schema='wrong',qualification_authority_ref=r)]:
 try:H.authority_reference(m)
 except ValueError:pass
 else:raise AssertionError('wrong clock domain admitted')
assert H.current_window(dict(start_epoch=1792828303,cutoff_epoch=1792914703))
for start,end in [(1792740953,1792827353),(1792828303,1792914704),(1792828304,1792914703)]:
 try:H.current_window(dict(start_epoch=start,cutoff_epoch=end))
 except ValueError:pass
 else:raise AssertionError('changed campaign admitted')
print(json.dumps(dict(domain_controls=9,source_only=True,NPU=False)),flush=True)
for domain,arms,file in [('related160',['rawON','rawOFF'],'related_qualification.py'),('formal',['native_ar','bole'],'formal_runtime.py')]:
 M=load(OLD/file,'_existing_'+domain)
 for arm in arms:
  base=HERE/('clock-review-'+domain+'-'+arm)
  b=M.render(base_root=base)if domain=='related160'else M.render(base,arm=arm)
  M.inverse(b)
  files,delta=D.adapt(b['files'],domain,A,raw)
  assert D.inverse(files,delta)==b['files']
  for n,v in files.items():
   if n.endswith('.py'):compile(v,n,'exec')
  assert all(files[n]==v for n,v in b['files'].items()if n not in delta)
  print(json.dumps(dict(domain=domain,arm=arm,files=len(files),changed=sorted(delta),whole_inverse=True,
    original_nonclock_bytes_unchanged=True,source_bound=False,NPU=False,timefit='UNPROVEN')),flush=True)
