"""New121 storage seam. No arithmetic, source/CPU or numeric gate equivalence."""
import json
from pathlib import Path
SOURCE121=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-121/SOURCE_MANIFEST.json',bytes=2003,sha256='311f70dfa8fdf683a2ab5efed747890c9ed40b3afc492494ff118a37a2213a2a')
SOURCE119=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-119/SOURCE_MANIFEST.json',bytes=937,sha256='aa574e91699c6b5bca8cfac66abab893a00a03bb5ef4eb87f851d73bc15faed6')
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061');EVIDENCE=ROOT/'seal-evidence121-MAIN-001/EVIDENCE121.json'
ACTUAL_EVIDENCE=dict(path=str(EVIDENCE),bytes=7329,sha256='44bcabef7286307cfa2d7ceb05213a877c34001c2534aebc8bb2630d2ddcfbd6')
ACTUAL_PLAN=dict(path=str(ROOT/'PLAN_STORAGE121_MAIN_001.json'),bytes=5113,sha256='53c39b74af92178a13852e70791bef93fd1ecc767c31da25d8600551b7ddc3ae')
ACTUAL_GENERATION=dict(path=str(ROOT/'STORAGE_LEDGER061.15.json'),bytes=2802,sha256='153d35ff3e896987be52e01d3cc8ca6918d29a9b22fdc50bd59a161174ba5583')
def require_evidence(C,raw):
 C.need(type(raw)is str,'actual121 evidence mandatory');r=json.loads(raw);C.need(r==ACTUAL_EVIDENCE,'exact source-bound121 evidence path/bytes/hash');C.checked(r);return r
def api(C,m):
 C.need(m['storage121_source_ref']==SOURCE121,'exact reviewed121 source');s=C.obj(SOURCE121)
 C.need(s['schema']=='deltalog.closed-storage-source/v121'and s['max_total_bytes']==80*2**30 and s['min_free_bytes']==100*2**30 and s['prior_source']==SOURCE119,'unchanged121 limits/prior')
 for r in s['files'].values():C.checked(r)
 return C.load(s['files']['sealed121.py'],'_088R5_exact121')
def generations():return sorted(ROOT.glob('STORAGE_LEDGER061.*.json'),key=lambda p:int(p.name.split('.')[1]))
def chain(C,S,e,er):
 before=e['baseline_ledger_ref'];previous=C.obj(before);number=int(Path(before['path']).name.split('.')[1]);found=False
 for p in generations():
  n=int(p.name.split('.')[1])
  if n<=number:continue
  C.need(n==number+1,'no missing new121 ledger generation');r=C.ref(p);v=C.obj(r)
  C.need(v['previous_ledger_ref']==before and v['sealed_evidence_ref']==er and v['storage069_template_ref']==SOURCE121,'exact append-only121 source/evidence/predecessor')
  C.need(v['root']==previous['root']and v['authority_ref']==previous['authority_ref']and v['reservations'][:len(previous['reservations'])]==previous['reservations']and len(v['reservations'])in(len(previous['reservations']),len(previous['reservations'])+1),'old reservations/authority untouched, one new phase only')
  before=r;previous=v;number=n;found=True
 C.need(found,'actual independent121 seal required');return before
def accept_existing(C,m,er,authority):
 S=api(C,m);C.need(er==ACTUAL_EVIDENCE,'actual121 fixed evidence');e,base,closed=S.validate(er,SOURCE121);p=C.obj(e['plan_ref']);C.need(e['plan_ref']==ACTUAL_PLAN and base['authority_ref']==authority and len(closed)==11,'actual121 all11 closed phases/same authority/plan')
 expected=int(Path(e['baseline_ledger_ref']['path']).name.split('.')[1])+1;latest=generations()[-1];C.need(latest.name=='STORAGE_LEDGER061.%d.json'%expected,'binder only pristine actual121 seal, not spent reservation');r=C.ref(latest);C.need(chain(C,S,e,er)==r,'actual121 source chain')
 C.need(r==ACTUAL_GENERATION,'exact actual seal15 bytes/hash');m['storage121_plan_ref']=e['plan_ref'];return r
def closed_stat(S,row):
 snap=S.read(row['tree_ref']);expected=[{k:v for k,v in r.items()if k!='sha256'}for r in snap['files']]
 S.need(S.prior().tree(row['leaf'],False)==expected and sum(x['bytes']for x in expected)==row['frozen_bytes'],'closed phase stat/inode/size/mtime changed; retain failure')
def install(C,m,storage):
 S=api(C,m);er=m['storage_seal_evidence_ref'];C.need(er==ACTUAL_EVIDENCE and m['storage121_plan_ref']==ACTUAL_PLAN and m['storage_seal_generation_ref']==ACTUAL_GENERATION,'exact actual121 bindings');e,base,closed=S.validate(er,SOURCE121)
 C.need(len(closed)==11 and C.obj(e['plan_ref'])['prior_source_ref']==SOURCE119 and e['plan_ref']==m['storage121_plan_ref']and base['authority_ref']==m['storage_authority_ref'],'actual11/prior/plan/authority bindings')
 bound=m['storage_seal_generation_ref'];C.obj(bound);C.need(int(Path(bound['path']).name.split('.')[1])==int(Path(e['baseline_ledger_ref']['path']).name.split('.')[1])+1,'bound actual121 seal generation');chain(C,S,e,er)
 C.need(storage.ROOT==ROOT and storage.LIMIT==80*2**30 and storage.FREE==100*2**30,'same explicit80/100 policy');storage._seal_context=dict(template_ref=SOURCE121,evidence_ref=er)
 def rows(ledger):
  rr=ledger['reservations'];C.need(type(rr)is list and len({r['leaf']for r in rr})==len(rr),'unique retained phase rows')
  for r in rr:C.need(set(r)=={'leaf','stage','budget_bytes'}and r['stage']in('cpu','numeric')and type(r['budget_bytes'])is int and r['budget_bytes']==(1 if r['stage']=='cpu'else 33)*2**30 and Path(r['leaf']).parent==ROOT,'unchanged1/33GiB allocations')
  return rr
 def commitment(root,ledger):
  C.need(Path(root)==ROOT,'same exact authorized output filesystem');chain(C,S,e,er);rr=rows(ledger);C.need(rr[:len(base['reservations'])]==base['reservations'],'all historical rows unchanged')
  for p in closed:closed_stat(S,p)
  total,amounts=storage.scan(root,[Path(r['leaf'])for r in rr]);frozen={r['leaf']:r['frozen_bytes']for r in closed}
  return total,storage.committed_bytes(total,amounts,[frozen.get(r['leaf'],r['budget_bytes'])for r in rr])
 storage.reserved=lambda ledger:sum(r['budget_bytes']for r in rows(ledger));storage.commitment=commitment
 return type('Final121',(),{'final_verify':staticmethod(lambda r:S.validate(r,SOURCE121))})
def readset(C,m):
 # Keep reviewed field-typed79 dependency rule via the actual original R4 plan.
 S=api(C,m);er=m['storage_seal_evidence_ref'];C.need(er==ACTUAL_EVIDENCE and m['storage121_plan_ref']==ACTUAL_PLAN and m['storage_seal_generation_ref']==ACTUAL_GENERATION,'exact actual121 read closure');e=C.obj(er);C.need(e['schema']=='deltalog.closed-phase-storage-evidence/v121'and e['source_manifest_ref']==SOURCE121,'typed actual121 evidence')
 pr=e['plan_ref'];plan=C.obj(pr);C.need(plan['schema']=='deltalog.closed-storage-plan/v121'and plan['target_template_ref']==S.TARGET_TEMPLATE and plan['prior_source_ref']==SOURCE119,'typed original R4/119 plan, not arbitrary provenance');old=C.obj(plan['target_source_ref']);C.need(old['prepared_template']==S.TARGET_TEMPLATE and old['prepared_only']is False,'actual reviewed R4 predecessor')
 R=C.load(m['files']['typed_readset088r4.py'],'_088R5_original_typed79');B=C.load(m['files']['storage_bridge119.py'],'_088R5_original119api')
 refs,notes=R.readset(C,old,SOURCE119,B.api)
 refs += [SOURCE121,*C.obj(SOURCE121)['files'].values(),er,pr,plan['target_source_ref'],plan['target_template_ref'],e['baseline_ledger_ref'],m['storage_seal_generation_ref']]
 #121.verify_plan explicitly reads prior119 generations13/14 as well as12.
 for n in range(int(Path(old['storage_seal_generation_ref']['path']).name.split('.')[1])+1,int(Path(e['baseline_ledger_ref']['path']).name.split('.')[1])+1):refs.append(C.ref(ROOT/('STORAGE_LEDGER061.%d.json'%n)))
 for p in e['phases']:
  refs += [p['owner_ref'],p['create_ref'],p['cleanup_ref'],p['tree_ref'],*p['original_inspect_refs']]
 result={}
 for r in refs:C.checked(r);result[json.dumps(r,sort_keys=True)]=r
 return list(result.values())
