"""Consume an existing093 seal, never create or silently advance a ledger."""
from pathlib import Path
SOURCE093=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-093/SOURCE_MANIFEST.json',bytes=5812,sha256='d0cb8fef914cb8a077a691ec19f23724dadc92d0a2a2dd1284f09321edcb1e88')
EVIDENCE093=dict(path='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/seal-evidence093-MAIN-001/EVIDENCE093.json',bytes=8586,sha256='4a8b900e24289b8c8c85421ce394474a75da95a15ddf198943f6203a681269f9')
GENERATION8=dict(path='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/STORAGE_LEDGER061.8.json',bytes=1992,sha256='15c32c1633fc206b695998f47babe4e255fc8d992cc27d5c87b0798c8cb6e6fe')
def require_evidence(C,raw):
 import json
 C.need(type(raw)is str,'actual sealed093 evidence argument is required')
 r=json.loads(raw);C.need(r==EVIDENCE093,'exact actual093 evidence Ref3, not pending or future PASS');return r
def api(C,m):
 C.need(m['storage093_source_ref']==SOURCE093,'only reviewed093 source, never arbitrary storage helper')
 s=C.obj(SOURCE093);C.need(s['schema']=='deltalog.closed-storage-source/v093'and s['max_total_bytes']==80*2**30 and s['min_free_bytes']==100*2**30,'same80/100')
 for r in[*s['files'].values(),*s['dependencies']]:C.checked(r)
 return C.load(s['files']['sealed_storage093.py'],'_088R2_actual093')
def accept_existing(C,m,evidence,authority):
 C.need(evidence==EVIDENCE093,'exact actual093 evidence, runtime hash verification still mandatory')
 S=api(C,m);e,base,closed=S.validate(evidence,authority,True)
 C.need(e['source_manifest_ref']==SOURCE093 and len(closed)==6,'actual six-phase093 evidence')
 latest=S.ref(S.old().generations(S.ROOT)[-1]);C.need(latest==GENERATION8,'binder consumes exact already-created8, unknown/reserved generation refused')
 C.need(S.chain(e,SOURCE093,evidence)==latest,'actual immutable seal8 chain')
 return latest
def install(C,m,storage):
 S=api(C,m);actual=accept_runtime_generation(C,m,S)
 S.install(storage,m['storage_seal_evidence_ref'],m['storage_authority_ref'],SOURCE093)
 return S
def accept_runtime_generation(C,m,S):
 # SubsequentCPU/N16/N160 reservations append to the exact admitted seal8.
 bound=m['storage_seal_generation_ref'];C.need(bound==GENERATION8,'bound actual original8 only');v=C.obj(bound)
 C.need(v['sealed_evidence_ref']==m['storage_seal_evidence_ref']and v['storage069_template_ref']==SOURCE093,'same captured093 generation; prepared088 identity is separate')
 e,_,_=S.validate(m['storage_seal_evidence_ref'],m['storage_authority_ref'],True);return S.chain(e,SOURCE093,m['storage_seal_evidence_ref'])
def readset(C,m):
 s=C.obj(SOURCE093);C.need(m['storage093_source_ref']==SOURCE093,'exact093 source');refs=[SOURCE093,*s['files'].values(),*s['dependencies'],m['storage_seal_generation_ref']]
 def collect(v):
  if type(v)is dict:
   if set(v)=={'path','bytes','sha256'}:refs.append(v)
   else:
    for x in v.values():collect(x)
  elif type(v)is list:
   for x in v:collect(x)
 e=C.obj(m['storage_seal_evidence_ref']);collect(e);prior=C.obj(e['prior_evidence_ref']);collect(prior)
 for p in e['phases']:
  q=C.obj(p['quiescent_ref']);collect(q)
 # Root-ledger Ref mounts already existed inR1; exact history is still read RO.
 for r in refs:C.checked(r)
 return refs
