"""MAIN source review and finite authority material, no Docker or NPU."""
import hashlib,json,sys,types
from pathlib import Path
D=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_phase_clock_prepare_v1_20261024/phase_runtime_renderer_v4")
OUT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261024T075143Z")
PIN={'runtime_lossless_imports.py':(7246,'c663f0beb42e05ec569b3618a97cb659f780cc4559cf93ffa30ab0a34c9c33d7'),'assets/shared_phase_clock.py':(10121,'d110f4cfc4fd2a3298ea2a0a66206452f6320b3c28a0b0f5c8f1d1581edfa587'),'assets/adapt_phase_clock.py':(2026,'b1b7fbe6ecda968b7c4fdbebe2f1cf43950984d5aaf983eec4d3d28c71a86cac'),'qualification_source_producer.py':(6847,'8bb91b8f9b5be5ceb85e7897289969abba5ad93bdebb8c99ccaccf29455c9721')}
def need(v,s):
 if not v: raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def publish(name,v):
 raw=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode();p=OUT/name
 with p.open('xb') as f:f.write(raw);f.flush();import os;os.fsync(f.fileno())
 return ref(p,raw)
for n,pin in PIN.items():
 p=(D.parent/'phase_runtime_renderer_v3'/n)if n.startswith('assets/')else D/n;raw=p.read_bytes();need(not p.is_symlink() and (len(raw),hashlib.sha256(raw).hexdigest())==pin,'exact independently read preparation '+n)
path=D/'runtime_lossless_imports.py';ns=types.ModuleType('_MAIN_phase_review_v4');ns.__file__=str(path);sys.modules[ns.__name__]=ns
exec(compile(path.read_bytes(),str(path),'exec'),ns.__dict__)
b=ns.render(permit_materialized=False);ns.inverse(b);m=b['manifest']
need(len(b['files'])==472 and set(b['delta'])=={'contract090.py','host_service.py','external025.py','owned_create.py','shared_phase_clock.py','adapt_phase_clock.py','runtime_lossless_imports.py'},'only seven reviewed changes')
for n,raw in b['files'].items():
 need(ref(Path(m['root'])/n,raw)==m['files'][n],'all generated source Ref3 identities')
 if n.endswith('.py'):compile(raw,n,'exec')
# Every helper/parent dependency is checked on host; generated source Refs are
# verified by complete rendered bytes here, physically rechecked after materialize.
own={r['path']:b['files'][n] for n,r in m['files'].items()}
count=0
for r in [*m['short2k_helper_refs'].values(),*m['qualification_parent_preparation_readset'].values(),m['qualification_historical_short_source'],*m['dependencies']]:
 if r['path'] in own:need(ref(r['path'],own[r['path']])==r,'exact future generated dependency')
 else:
  p=Path(r['path']);need(not any(x.is_symlink()for x in(p,*p.parents)),'ordinary external dependency')
  raw=p.read_bytes();need(ref(p,raw)==r,'entire external dependency identity')
 count+=1
need(m['phase_clock_contract']=={'schema':'bole.shared-existing-phase/v1','phase_seconds':3600,'cleanup_seconds':180,'guest_readonly':True},'one inherited original phase')
validator=types.ModuleType('_MAIN_short8_validator');exec(compile(b['files']['qualification_source_validate.py'],'qualification_source_validate.py','exec'),validator.__dict__)
validator.qualification_shape(m)
review=dict(schema=validator.REVIEW_SCHEMA,approved=True,scope=validator.SCOPE,source_root=m['root'],output_root=m['output_root'],files=m['files'],parent_preparation_readset=m['qualification_parent_preparation_readset'],historical_short_source=m['qualification_historical_short_source'],short2k_helper_refs=m['short2k_helper_refs'])
review_ref=publish('BOLE_PHASE_V4_MAIN_SOURCE_REVIEW.json',review)
authority=dict(schema=validator.AUTH_SCHEMA,approved=True,start_epoch=1792828303,cutoff_epoch=1792914703,scope=validator.SCOPE,MAIN_review_ref=review_ref)
validator.authority_shape(authority)
authority_ref=publish('BOLE_PHASE_V4_AUTHORITY.json',authority)
bound_preview=ns.render(permit_materialized=False,authority_ref=authority_ref);ns.inverse(bound_preview)
need(bound_preview['files']==b['files'] and bound_preview['manifest']['qualification_authority_ref']==authority_ref,'actual authority branch preserves exact source and current authority')
validator.execution_window(bound_preview['manifest'],clock=True,require_phase=True)
result=dict(actual_authority_branch_passed=True,schema='MAIN.bole-v4-source-review-result/v1',files=472,changed=sorted(b['delta']),whole_inverse=True,dependency_checks=count,review_ref=review_ref,authority_ref=authority_ref,NPU=False,numeric_qualified=False,materialized=False,cutoff_epoch=1792914703)
publish('BOLE_PHASE_V4_MAIN_SOURCE_REVIEW_RESULT.json',result)
print(json.dumps(result,sort_keys=True))
