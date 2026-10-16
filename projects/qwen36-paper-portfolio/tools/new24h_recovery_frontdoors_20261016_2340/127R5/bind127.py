"""Bind the one actual TimeoutExpired producer. No workload launch."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import host as H,provenance127 as V,raw_closure043 as RAW,readset127 as INDEX
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-anchor-consumer-recovery-new24h-v1-127-repair5'
EVIDENCE=dict(path='/opt/host/vnf/austinov/run-dl088r6r2-consumer-fault-evidence-MAIN-20261016-001/ACTUAL_EVIDENCE.json',bytes=15353,sha256='cc4ea59d1c90f43f0513585dc731aa53380598dd287646434a742eb8d2d5b81e')
PREVIOUS=dict(path='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-anchor-recovery127repair2-MAIN-20261016-NEW24H-001/RESULT.json',bytes=1195,sha256='a6a7da8ecd050196f373826d22fd1b158e1f130ff5b2491cdad5f22773221b8b')
def bind(tr,budget_ref=None):
 import clock127r4 as CLOCK
 H.need(budget_ref is not None,'pending actual measured complete-workload budget profile')
 budget=H.obj(budget_ref);CLOCK.profile({'cpu_budget_profile':budget});H.obj(budget['measurement_ref'])
 t=H.obj(tr);H.need(str(P)==ROOT and tr['path']==ROOT+'/SOURCE_TEMPLATE.json'and t['root']==ROOT and t['bound']is False,'exact deployed pending template')
 H.need(budget_ref==t['files']['BUDGET_PROFILE127R5.json']and budget==t['cpu_budget_profile'],'exact source-owned new operational profile, not arbitrary measured PASS')
 for r in t['files'].values():H.validate_ref_streamed(r)
 e=H.obj(EVIDENCE);m,prod=V.validate(e,H.obj);r=e['refs'];writer=INDEX.Writer(P/'BIND_INDEX127.sqlite',H.validate_ref_streamed);add=writer.add
 previous=H.obj(PREVIOUS);H.need(previous['schema']=='deltalog.fresh-bridge-owned-host/v5'and previous['stage']=='cpu'and previous['NPU']is False and previous['physical']==[]and previous['primary']=="ValueError('aggregate actual host+child peak RSS exceeds256MiB')"and previous['secondary']==[]and previous['result']is None and previous['stopped_retained']is True and previous['source']==previous['target_source'],'preserve actual R2 preguest RSS failure, not qualification')
 H.need(previous['source']['path']=='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-anchor-consumer-recovery-new24h-v1-127-repair2/SOURCE_MANIFEST.json'and previous['source']['bytes']==42689810,'exact old large manifest remains opaque streamed evidence')
 add(PREVIOUS);add(previous['source'])
 for ref in [tr,EVIDENCE,*r.values(),*[x['ref']for x in e['inspect'].values()]]:add(ref)
 for ref in t['external_refs']:add(ref)
 add(budget_ref);add(budget['measurement_ref'])
 import previous_reader127r4 as PR
 prior_reader=PR.validate(H.obj,r['source'])
 for prior in PR.REFS.values():add(prior)
 sys.path.insert(0,str(Path(r['source']['path']).parent))
 oldhost=H.load(m['files']['host.py'],'_127_original_host');_,_,_,closure,_=oldhost.target_closure(r['source'])
 for ref in closure:add(ref)
 # The full original storage continuation readset, not generic historical JSON.
 b=H.load(m['files']['storage_bridge088r6.py'],'_127_storage_readset')
 oldC=H.load(m['files']['bridge_io.py'],'_127_original_contract')
 policy=H.load(m['files']['collection_policy.py'],'_127_original_collection_policy');policy.require_complete(oldC,prod,r['source'])
 for ref in b.readset(oldC,m):add(ref)
 parent=Path(r['producer']['path']).parent
 pending=[x['raw']for x in prod['records']]+prod['actual_sidecar_records'];seen=set()
 def raw_metadata_refs(v):
  if type(v)is dict:
   if set(v)=={'path','bytes','sha256'}:
    q=Path(v['path'])
    # Captured runtime source identities are evidence, not host files. The
    # original consumer verifies those via its exact runtime-source mapping.
    if q.parent==parent and q.suffix=='.pt':pending.append(v)
   else:
    for value in v.values():raw_metadata_refs(value)
  elif type(v)in(list,tuple):
   for value in v:raw_metadata_refs(value)
 while pending:
  ref=pending.pop();H.need(Path(ref['path']).parent==parent,'only exact original raw-parent data')
  if ref['path']in seen:H.need(writer.get(ref['path'])==ref,'one exact raw identity');continue
  seen.add(ref['path']);add(ref);raw_metadata_refs(RAW.metadata(ref,add))
  for blob in RAW.closure(ref,add):add(blob)
 arm=H.ref(parent.parent/'ACTUAL_OWNER.json');add(arm);a=H.obj(arm);cid=e['small_documents']['numeric_cleanup']['cid']
 plan_ref=H.ref(parent.parent/'PLAN.json');add(plan_ref);device_ref=H.ref(parent/'DEVICE.json');add(device_ref);handshake_ref=H.ref(parent/'MAIN_ARM.json');add(handshake_ref)
 plan=H.obj(plan_ref);add(plan['cpu_preflight']);V.arm(a,H.obj(device_ref),H.obj(handshake_ref),plan_ref,plan,prod,m,cid)
 description=writer.emit(P/'RECOVERY_READSET127.jsonl');writer.close()
 for ref in INDEX.Index(description,H.validate_ref_streamed):H.validate_ref_streamed(ref)
 result=dict(m,previous_reader_failure=prior_reader,cpu_budget_profile=budget,cpu_budget_profile_ref=budget_ref,root=ROOT,files=t['files'],prepared_template=tr,prepared_only=False,bound=True,
  consumer_contract_schema='deltalog.anchor-consumer-source/v127',producer_source=r['source'],
  original_source_ref=r['source'],original_producer_ref=r['producer'],original_failed_owner_ref=r['owner'],
  original_strict_ref=r['strict'],actual_fault_evidence_ref=EVIDENCE,original_arm_ref=arm,original_plan_ref=plan_ref,original_device_ref=device_ref,original_handshake_ref=handshake_ref,
  recovery_readset_index=description,previous_recovery_failure_ref=PREVIOUS,previous_recovery_source_ref=previous['source'],storage_accounting_policy_source_ref=r['source'],
  original_timeout_seconds=V.TIMEOUT,allowed_fault='exact-original-domain-TimeoutExpired-shared590',
  execution_scope='CPU-only anchors-only independent operational recovery; old owner FAIL retained',
  default_enabled=False,model_ready=False,performance_ready=False)
 result.pop('recovery_refs',None);H.need(len(json.dumps(result,sort_keys=True,allow_nan=False).encode('utf8'))<=1024**2,'small manifest<=1MiB; never embed blob array')
 H.write(P/'SOURCE_MANIFEST.json',result);print(json.dumps(H.ref(P/'SOURCE_MANIFEST.json')));return 0
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--template-ref',required=True);ap.add_argument('--budget-profile-ref');a=ap.parse_args()
 if not a.execute:print('disabled');return 0
 return bind(json.loads(a.template_ref),json.loads(a.budget_profile_ref)if a.budget_profile_ref else None)
if __name__=='__main__':raise SystemExit(main())
