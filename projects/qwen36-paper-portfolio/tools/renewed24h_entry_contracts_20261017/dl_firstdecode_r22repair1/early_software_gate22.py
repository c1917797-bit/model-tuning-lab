"""A source/template/full-suite receipt is necessary, never component math."""
import json
from pathlib import Path
DEFERRED=['test_actual017_binding.ActualBinding.test_real_template_original017_adapt_and_private_bind','test_overlay.Tests.test_allcold_and_actual_namespace']

def software_ref(O,guest,inspect,owner_ref):
 O.need(type(guest)is dict and set(guest)=={'path','bytes','sha256'}and guest['path']=='/adakv-results/SOFTWARE.json','only exact prepared-stage software guest alias')
 root=Path(owner_ref['path']).parent
 rw=[x for x in inspect['Mounts']if x['RW']]
 O.need(len(rw)==1 and rw[0]['Source']==str(root)and rw[0]['Destination']=='/adakv-results','one exact stopped-inspect RW namespace join')
 r=dict(guest,path=str(root/'SOFTWARE.json'));O.obj_file(r);return r
def consume(O,m,tr,owner_ref):
 policy=m['early_software_policy'];O.need(type(policy['prepared_owner_source'])is dict,'actual reviewed early-owner source pin pending')
 own=O.obj(owner_ref);sr=own['source'];source=O.obj(sr);prepared=O.obj(policy['prepared_owner_source'])
 O.need(source['prepared_template']==policy['prepared_owner_source']and source['files']==prepared['files']and source['prepared_only']is False,'exact bound early CPU owner, not template bool')
 O.need(owner_ref['path']==policy['owner_output_root']+'/consumer/RESULT.json'and own['schema']=='deltalog.prebind-software-owned/v22'and own['primary']is None and own['secondary']==[]and own['resource_release_verified']is True and own['stopped_retained']is True and own['Devices']==[]and own['NPU']is False and own['qualified']is False,'actual complete released Devices[] prebind CPU job')
 report=O.obj(own['stage_result']);O.need(report['schema']=='deltalog.prebind-software-owned-complete/v22'and report['source']==sr and report['model_template']==tr and report['primary']is None,'same real model template, not previous attempt')
 # Recompute a Ref only at the exact own output path, then reopen immutably.
 path=Path(owner_ref['path']).parent/'FINAL_INSPECT.json';b=path.read_bytes();import hashlib
 ir=dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest());x=O.obj(ir);s=x['State'];h=x['HostConfig']
 O.need(x['Id']==own['cid']and x['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and not x.get('ExecIDs')and s['Running']is False and s['Pid']==0 and s['ExitCode']==0 and s['OOMKilled']is False and h['Devices']==[]and not h.get('DeviceRequests')and h['ReadonlyRootfs']is True,'same retained exact CPU inspect, no virtual admission')
 rr=software_ref(O,report['software_ref'],x,owner_ref);software=O.obj(rr)
 O.need(software['schema']=='deltalog.actual-prebind-software/v22'and software['template']==tr and software['discovered']==software['executed']==m['software_cases']-2 and software['original_discovered']==m['software_cases']and software['deferred_to_original_model_cpu']==DEFERRED and software['full_model_suite_executed']is False and software['skipped']==0 and software['full_suite_pass']is True and software['primary']is None and software['prepared_only']is True and software['model_source_created']is False and software['Devices']==[]and software['NPU']is False and software['qualified']is False,'actual complete prepared-stage suite before expensive closed bind; original full model CPU still required')
 refs=[owner_ref,sr,policy['prepared_owner_source'],own['stage_result'],rr,ir,*source['files'].values()]
 for r in refs:O.obj_file(r)
 return dict(schema='deltalog.prebind-software-consumption/v22',template=tr,actual_owner=owner_ref,source=sr,report=rr,original_guest_report_ref=report['software_ref'],deferred_to_original_model_cpu=DEFERRED,full_model_suite_executed=False,readset=refs,qualified=False,NPU=False)
def require(O,m,tr):
 policy=m['early_software_policy'];O.need(type(policy['prepared_owner_source'])is dict,'source-owned early CPU ticket not ready')
 path=Path(policy['owner_output_root'])/'consumer/RESULT.json';b=path.read_bytes();import hashlib
 return consume(O,m,tr,dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
