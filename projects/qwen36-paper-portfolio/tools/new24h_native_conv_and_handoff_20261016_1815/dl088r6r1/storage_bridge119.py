"""088R3 exact119 storage seam. No numerical or phase-evidence equivalence."""
from pathlib import Path
import json
SOURCE119=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-119/SOURCE_MANIFEST.json',bytes=937,sha256='aa574e91699c6b5bca8cfac66abab893a00a03bb5ef4eb87f851d73bc15faed6')
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
EVIDENCE_PATH=ROOT/'seal-evidence119-MAIN-001/EVIDENCE119.json'
def require_evidence(C,raw):
 C.need(type(raw)is str,'actual119 evidence required');r=json.loads(raw);C.need(type(r)is dict and set(r)=={'path','bytes','sha256'}and r['path']==str(EVIDENCE_PATH),'exact119 evidence path/Ref3');C.checked(r);return r
def api(C,m):
 C.need(m['storage119_source_ref']==SOURCE119,'exact reviewed119 source');s=C.obj(SOURCE119)
 C.need(s['schema']=='deltalog.closed-storage-source/v119'and s['max_total_bytes']==80*2**30 and s['min_free_bytes']==100*2**30,'unchanged80/100')
 for r in s['files'].values():C.checked(r)
 return C.load(s['files']['sealed119.py'],'_088R3_actual119')
def generations():return sorted(ROOT.glob('STORAGE_LEDGER061.*.json'),key=lambda p:int(p.name.split('.')[1]))
def chain(C,S,e,er):
 before=S.BASE;previous=C.obj(before);items=generations();C.need(items and items[-1].name!='STORAGE_LEDGER061.11.json','actual separate119 seal required')
 for p in items:
  number=int(p.name.split('.')[1])
  if number<=11:continue
  r=C.ref(p);v=C.obj(r);C.need(v['previous_ledger_ref']==before and v['sealed_evidence_ref']==er and v['storage069_template_ref']==SOURCE119,'exact119 append-only chain')
  C.need(v['root']==previous['root']and v['authority_ref']==previous['authority_ref']and v['reservations'][:len(previous['reservations'])]==previous['reservations'],'old roots/rows/auth untouched')
  C.need(len(v['reservations'])in(len(previous['reservations']),len(previous['reservations'])+1),'one new reservation only');before=r;previous=v
 return before
def accept_existing(C,m,er,authority):
 S=api(C,m);e,base,closed=S.validate(er,SOURCE119);C.need(e['authority_ref']==authority,'exact actual authority');p=generations()[-1];C.need(p.name=='STORAGE_LEDGER061.12.json','binder accepts only actual fresh seal12');r=C.ref(p);C.need(chain(C,S,e,er)==r,'actual119 sealed chain');return r
def closed_stat(S,row):
 snap=S.read(row['tree_ref']);expected=[{k:v for k,v in r.items()if k!='sha256'}for r in snap['files']]
 S.need(S.tree(row['leaf'],False)==expected and sum(r['bytes']for r in expected)==row['frozen_bytes'],'closed phase changed: stop retain')
def install(C,m,storage):
 S=api(C,m);er=m['storage_seal_evidence_ref'];e,base,closed=S.validate(er,SOURCE119);C.need(e['authority_ref']==m['storage_authority_ref'],'exact119 authority');bound=m['storage_seal_generation_ref'];C.need(Path(bound['path']).name=='STORAGE_LEDGER061.12.json','bound actualseal12');C.obj(bound);chain(C,S,e,er)
 C.need(storage.ROOT==ROOT and storage.LIMIT==80*2**30 and storage.FREE==100*2**30,'same storage limits')
 storage._seal_context=dict(template_ref=SOURCE119,evidence_ref=er)
 def rows(ledger):
  rr=ledger['reservations'];C.need(len({x['leaf']for x in rr})==len(rr),'unique phase ledger')
  for x in rr:C.need(set(x)=={'leaf','stage','budget_bytes'}and x['stage']in('cpu','numeric')and type(x['budget_bytes'])is int and x['budget_bytes']==(1 if x['stage']=='cpu'else 33)*2**30 and Path(x['leaf']).parent==ROOT,'original allocations')
  return rr
 def commitment(root,ledger):
  C.need(Path(root)==ROOT,'same authorized filesystem');chain(C,S,e,er);rr=rows(ledger);C.need(rr[:len(base['reservations'])]==base['reservations'],'old reservations never edited')
  for p in closed:closed_stat(S,p)
  total,amounts=storage.scan(root,[Path(x['leaf'])for x in rr]);frozen={p['leaf']:p['frozen_bytes']for p in closed};return total,storage.committed_bytes(total,amounts,[frozen.get(x['leaf'],x['budget_bytes'])for x in rr])
 storage.reserved=lambda ledger:sum(x['budget_bytes']for x in rows(ledger));storage.commitment=commitment
 return type('Final119',(),{'final_verify':staticmethod(lambda r:S.validate(r,SOURCE119))})
def readset(C,m):
 from typed_readset088r4 import readset as typed_readset
 refs,indices=typed_readset(C,m,SOURCE119,api)
 return refs
