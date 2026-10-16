"""Pending exact spent R5 ledger/terminal continuation; no implicit seal/reset."""
import json,types
from pathlib import Path
import storage_bridge121 as original
import closed_overlay088r6 as O
require_evidence=original.require_evidence
def accept_existing(C,m,er,authority):
 C.need(er==original.ACTUAL_EVIDENCE,'original121 exact evidence');S=original.api(C,m);e,base,closed=S.validate(er,original.SOURCE121)
 C.need(base['authority_ref']==authority and len(closed)==11,'original authority/all11closed');m['storage121_plan_ref']=e['plan_ref'];O.validate(C,m,m['storage088r6_append_evidence_ref']);last,v=O.history(C);C.need(last==O.BASE,'binder only unspent17');return original.ACTUAL_GENERATION
def install(C,m,storage):
 S=original.api(C,m);er=m['storage_seal_evidence_ref'];C.need(er==original.ACTUAL_EVIDENCE and m['storage_seal_generation_ref']==original.ACTUAL_GENERATION and m['storage121_plan_ref']==original.ACTUAL_PLAN,'original121 bindings unchanged')
 e,base,closed=S.validate(er,original.SOURCE121);r=m['storage088r6_append_evidence_ref'];extra=O.validate(C,m,r);closed=closed+extra['phases'];tr=m['prepared_template'];t=C.obj(tr);C.need(t['files']==m['files']and t['root']==m['root'],'same R6 reviewed template/files')
 C.need(len(closed)==13 and storage.ROOT==O.ROOT and storage.LIMIT==80*O.G and storage.FREE==100*O.G,'13closed same80/100');O.history(C,tr,r);storage._seal_context=dict(template_ref=tr,evidence_ref=r)
 def rows(v):
  rr=v['reservations'];C.need(type(rr)is list and len({x['leaf']for x in rr})==len(rr),'unique actual ledger rows')
  for x in rr:C.need(set(x)=={'leaf','stage','budget_bytes'}and x['stage']in('cpu','numeric')and type(x['budget_bytes'])is int and x['budget_bytes']==(1 if x['stage']=='cpu'else 33)*O.G and Path(x['leaf']).parent==O.ROOT,'unchanged1/33GiB reservations')
  return rr
 def commitment(root,ledger):
  C.need(Path(root)==O.ROOT,'exact authorized root');latest,v=O.history(C,tr,r);rr=rows(ledger);C.need(rr[:len(v['reservations'])]==v['reservations']and len(rr)in(len(v['reservations']),len(v['reservations'])+1),'actual prefix or one pending reservation')
  for row in closed:original.closed_stat(S,row)
  total,amounts=storage.scan(root,[Path(x['leaf'])for x in rr]);frozen={x['leaf']:x['frozen_bytes']for x in closed};return total,storage.committed_bytes(total,amounts,[frozen.get(x['leaf'],x['budget_bytes'])for x in rr])
 storage.reserved=lambda ledger:sum(x['budget_bytes']for x in rows(ledger));storage.commitment=commitment
 def final(unused):
  S.validate(er,original.SOURCE121);O.validate(C,m,r);O.history(C,tr,r)
 return types.SimpleNamespace(final_verify=final)
def readset(C,m):
 refs=original.readset(C,m);r=m['storage088r6_append_evidence_ref'];e=O.validate(C,m,r);refs +=[r,O.BASE,O.SIXTEEN,O.R5_TEMPLATE,e['r5_source_ref']]
 for row in e['phases']:refs +=[row[k]for k in('owner_ref','create_ref','cleanup_ref','tree_ref')]
 for q in original.generations():
  if int(q.name.split('.')[1])>17:refs.append(C.ref(q))
 out={}
 for q in refs:C.checked(q);out[json.dumps(q,sort_keys=True)]=q
 return list(out.values())
