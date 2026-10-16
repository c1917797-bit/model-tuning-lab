"""Mechanical successor assembly. Does not execute a backend or bind future receipts."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parent/'deltalog-mixed-precast-new48h-20261015-043-repair3'
K=P.parent/'deltalog-split-scale-new48h-20261016-051'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new48h-v1-052'
OUT='/opt/host/vnf/austinov/deltalog-split-scale-numeric-new48h-052'
EDITS={}
def put(n,b):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b.replace(b'\r\n',b'\n'))
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def ref(n,b):return dict(path=ROOT+'/'+n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def change(n,a,b,count=1):
 s=(P/n).read_text(encoding='utf8');assert s.count(a)==count,(n,a,s.count(a));put(n,s.replace(a,b).encode());EDITS.setdefault(n,[]).append([a,b])
def main():
 old=json.loads((B/'SOURCE_TEMPLATE.json').read_bytes());oldroot=old['root']
 for n in old['files']:
  raw=(B/n).read_bytes();text=raw.decode()
  edits=()if n.startswith(('fixtures/','fixtures043/','fixtures_repair3/'))or not n.endswith('.py')else((oldroot,ROOT),('deltalog-mixed-precast-new48h-043-repair3','deltalog-split-scale-numeric-new48h-052'),('2610154301','2610165101'))
  for a,b in edits:
   if a in text:EDITS.setdefault(n,[]).append([a,b]);text=text.replace(a,b)
  put(n,text.encode())
 put('terminal_fence.py',(P.parent/'deltalog-mixed-precast-new48h-20261015-043-repair5/terminal_fence.py').read_bytes())
 # Never reuse the old whole-library qualification for the changed readout.
 change('qwen36_deltalog_fresh/provider.py',"life['library']!=m['library_ref']", "life['library']!=m['state_predecessor_library_ref']")
 change('qwen36_deltalog_fresh/provider.py','return m,life','from split_build052 import admit\n admit(m,_obj,_ref)\n return m,life')
 change('qwen36_deltalog_fresh/provider.py',"lib=m['library_ref'];C.require_digest(lib['path'],C.LIBRARY_SHA)","lib=m['library_ref'];C.require_digest(lib['path'],lib['sha256']);C.LIBRARY_SHA=lib['sha256']")
 change('qwen36_deltalog_fresh/contract.py',"NAMESPACE='qwen36_deltalog_key_projection'","NAMESPACE='qwen36_deltalog_split_scale_v051'")
 change('qwen36_deltalog_fresh/contract.py',"LIBRARY_SHA='298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7'","LIBRARY_SHA=None # Set only after exact actual051 build admission; never an old B010 certificate.")
 change('sidecar_capture.py',"namespace='qwen36_deltalog_readout_sidecar_v015'","namespace='qwen36_deltalog_split_scale_sidecar_v051'")
 # Same API, genuine CPU load+Meta is required by the unchanged entry gate.
 put('meta051.py',(K/'meta_abi.py').read_bytes())
 put('meta043.py',b'''"""Actual051 dual Meta through the original CPU preflight stage."""\ndef run(torch,m,C):\n from meta051 import run as actual\n z=actual(torch,m['split_build_ref'],m['split_kernel_source_ref'])\n C.need(z['libraries']==[m['library_ref'],m['debug_library']],'actual051 exact two libraries')\n return dict(z,debug_library=m['debug_library'],debug_build=m['debug_build_ref'],registrations=z['rows'])\n''')
 cases="'cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness'"
 change('npu_controls.py',"'cancellation','overflow')",cases+")")
 change('npu_controls.py',"elif name=='negative-zero':base[0].fill_(-0.)","elif name=='negative-zero':base[0].fill_(-0.)\n  elif name=='finite-final-normalized-query':base[0].fill_(1e38)\n  elif name=='finite-final-unscaled-query':base[0].fill_(1e37)\n  elif name=='cancellation-permuted':base[0,:,:,:64]=.125;base[0,:,:,64:]=-.125\n  elif name=='gqa-vtile-witness':\n   for head in range(12):base[0,head,:64,:]=(head+1)*.0001;base[0,head,64:,:]=-(head+1)*.0002")
 change('npu_controls.py','  capture(q,k,v,g,beta,','  if name==\'finite-final-normalized-query\':q.fill_(128**-.5)\n  capture(q,k,v,g,beta,')
 change('npu_controls.py',"  capture(q,k,v,g,beta,","  if name=='gqa-vtile-witness':\n   for head in range(4):q[0,head].fill_(head+1)\n  capture(q,k,v,g,beta,")
 change('producer.py','boundary_controls=npu_controls.run(torch,h,sidecar)','boundary_controls=npu_controls.run(torch,h,sidecar)\n  from regression052 import run as replay_firstfault\n  boundary_controls.extend(replay_firstfault(torch,sidecar,m,C))')
 tail=",'original-B16-step80','original-B16-step137'"
 change('domain_consumer.py',"'cancellation','overflow'],'all real NPU numeric boundary controls'",cases+tail+"],'all real NPU numeric boundary controls'")
 change('collection_policy.py','len(side)==2*steps+25','len(side)==2*steps+31')
 change('collection_policy.py',"'cancellation','overflow'],'all7 actual boundary controls retained'",cases+tail+"],'all13 actual boundary controls retained'")
 change('domain_consumer.py',"len(all043)==2*producer['steps']+25","len(all043)==2*producer['steps']+31")
 change('domain_consumer.py',"  audit043=sidecar_audit.audit(","  if rr043['path'] in {x['raw']['path']for x in controls if x['case'].startswith('original-B16-')}:\n   import regression052,bridge_io\n   regression052.audit(torch,m,bridge_io,next(x for x in controls if x['raw']==rr043),av043)\n  audit043=sidecar_audit.audit(")
 oldblock=" for rr043 in all043:\n  av043=torch.load(checked(rr043),map_location='cpu',weights_only=False)\n  if rr043['path'] in {x['raw']['path']for x in controls if x['case'].startswith('original-B16-')}:\n   import regression052,bridge_io\n   regression052.audit(torch,m,bridge_io,next(x for x in controls if x['raw']==rr043),av043)\n  audit043=sidecar_audit.audit(torch,R,precast,av043,overflow=rr043['path']in overflow,numeric=rr043['path']not in mixed043)\n  sidecar_rows.append(dict(raw=rr043,**audit043))"
 change('domain_consumer.py',oldblock," from sidecar_receipt052 import one as persist_actual_sidecar\n for index043,rr043 in enumerate(all043):\n  sidecar_rows.append(persist_actual_sidecar(torch,R,precast,rr043,source_ref,producer_ref,m,output,index043,mixed043,overflow,controls,checked))")
 change('host.py',"OWNER='deltalog-mixed-precast-new48h-MAIN-043-repair3'","OWNER='deltalog-split-scale-numeric-new48h-MAIN-052'")
 change('host.py',"refs.extend([m['debug_library'],m['debug_build_ref'],m['debug_kernel_source_ref']])","refs.extend([m['debug_library'],m['debug_build_ref'],m['debug_kernel_source_ref'],m['split_kernel_source_ref'],m['firstfault_ref'],m['state_predecessor_library_ref'],m['regression137_raw_ref'],*m['regression137_secondary_refs']])")
 change('test_collection_contract.py','range(2*steps+25)','range(2*steps+31)')
 change('test_collection_contract.py',"'cancellation','overflow'))])",cases+tail+"))])")
 change('inverse_repair3.py',"def undo(name,text):","def undo(name,text):\n from inverse052 import undo as undo052\n text=undo052(name,text)")
 change('test_031.py',"self.assertEqual(hashlib.sha256((P/n).read_bytes()).hexdigest(),m['files'][n]['sha256'])","from inverse052 import undo\n   self.assertEqual(hashlib.sha256(undo(n,(P/n).read_text(encoding='utf8')).encode()).hexdigest(),m['files'][n]['sha256'])")
 change('test_mount_closure.py',"manifest.update(composite_source_ref=external,composite_cpu_owner_ref=external,lifecycle_source_ref=external)","manifest.update(composite_source_ref=external,composite_cpu_owner_ref=external,lifecycle_source_ref=external,library_ref=external,debug_library=external,debug_build_ref=external,debug_kernel_source_ref=external)")
 change('test_aggregate_controls.py','from pathlib import Path','from pathlib import Path\nfrom unittest.mock import patch')
 change('test_aggregate_controls.py',"scope=dict(vars(C));exec(","scope=dict(vars(C),m={'software_aggregate_only':True});exec(")
 change('test_aggregate_controls.py',"body.append(ast.Return(ast.Name('sidecar_rows',ast.Load())))","body.insert(0,ast.parse(\"output=producer['_software_output']\").body[0]);body.append(ast.Return(ast.Name('sidecar_rows',ast.Load())))")
 change('test_aggregate_controls.py',"scope=dict(vars(C),m={'software_aggregate_only':True})","scope=dict(vars(C),m={'software_aggregate_only':True},source_ref={'software-only':True},producer_ref={'software-only':True})")
 change('test_aggregate_controls.py','class Aggregate(unittest.TestCase):','class Aggregate(unittest.TestCase):\n def setUp(self):\n  self.regression_patch=patch(\'regression052.audit\',side_effect=lambda t,m,c,row,side: row[\'software_fixture\']is True);self.regression_patch.start()\n def tearDown(self):self.regression_patch.stop()')
 change('test_aggregate_controls.py','  for j in range(50):',"  for case in('original-B16-step80','original-B16-step137'):\n   capture(*[x.clone()for x in normal]);controls.append(dict(case=case,raw=capture.take(),software_fixture=True))\n  for j in range(50):")
 change('test_aggregate_controls.py','p=dict(records=[],steps=16,','p=dict(_software_output=str(root/\'DOMAIN.json\'),records=[],steps=16,')
 change('test_aggregate_controls.py','self.assertEqual(len(rows),57)','self.assertEqual(len(rows),63)')
 change('test_aggregate_controls.py','set(npu_controls.CASES)','set(npu_controls.CASES)|{\'original-B16-step80\',\'original-B16-step137\'}')
 change('test_aggregate_controls.py',"(base[s,h]@q[j,h//3].float())*(128**-.5)","(base[s,h]@(q[j,h//3].float()*2**-4))*((128**-.5)*16)")
 # Static pins are regenerated only for the actual changed source, not weakened.
 s=(P/'domain_consumer.py').read_text();tree=ast.parse(s);node=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINNED'for t in n.targets));pins=ast.literal_eval(node.value)
 for n in pins:pins[n]=hashlib.sha256((P/n).read_bytes()).hexdigest()
 lines=s.splitlines(True);lines[node.lineno-1:node.end_lineno]=['PINNED = '+repr(pins)+'\n'];put('domain_consumer.py',''.join(lines).encode())
 # New sources written separately with apply_patch are part of the complete closure.
 put('EDITS052.json',data(EDITS))
 names=set(old['files'])|{'assemble052.py','split_build052.py','bind052.py','run052.py','regression052.py','meta051.py','test_052.py','HANDOFF052.md','inverse052.py','EDITS052.json','REGRESSION_INPUTS.json','ACTUAL051_BUILD.json','sidecar_receipt052.py'}
 for n in names:put(n,(P/n).read_bytes())
 m=json.loads(json.dumps(old).replace(oldroot,ROOT).replace('deltalog-mixed-precast-new48h-043-repair3','deltalog-split-scale-numeric-new48h-052'))
 m.update(root=ROOT,exact_output_root=OUT,prepared_only=True,library_ref=None,debug_library=None,debug_build_ref=None,debug_kernel_source_ref=None,state_predecessor_library_ref=old['library_ref'],split_build_ref=None,split_kernel_source_ref=json.loads((K/'PACKET_MANIFEST.json').read_bytes())['build_source'])
 m['reviewed_split_build_ref']=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-split-scale051-build-new48h-MAIN-20261015-001/cpu-preflight/producer/build/RESULT.json',bytes=8847,sha256='3010d9b0a73d2f7b62b6294c8c01fa68176f1e911bee4b43ca7b1ac72bf00a68')
 m['validation_contract']['seed_base']=2610165101
 ri=json.loads((P/'REGRESSION_INPUTS.json').read_bytes());m['regression137_raw_ref']=ri['rows'][-1]['raw'];m['regression137_secondary_refs']=ri['secondary_refs']
 m['numeric052_scope']={'seed':2610165101,'boundary_cases':13,'old_point_failures_preserved':True,'new_library_requires_actual_build_and_same_source_Meta':True,'model_ready':False}
 m['firstfault_ref']={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dlbridge035r4-numeric160-new48h-MAIN-20261015-001/numeric/result/mixed-B16-080.pt','bytes':151267875,'sha256':'6057c3726a57f778116e8dd1ff7eef6e2aed9c7d4c4213f286c21d18be58171b'}
 m['files']={n:ref(n,(P/n).read_bytes())for n in sorted(names)}
 put('SOURCE_TEMPLATE.json',data(m));tr=ref('SOURCE_TEMPLATE.json',data(m));base=['/usr/bin/python3','-I','-B',ROOT+'/run052.py','--execute','--template-ref',json.dumps(tr)]
 commands={phase:base+['--phase',phase]for phase in('bind','sourceaudit','cpu','numeric16','numeric160')}
 commands['bind']+=['--original035-source-ref','ACTUAL035R4_SOURCE_REF3_JSON','--build-ref',json.dumps(m['reviewed_split_build_ref'])]
 for phase in('sourceaudit','cpu','numeric16','numeric160'):commands[phase]+=['--host-cpu','ACTUAL_HOST_CPU','--guest-cpu','ACTUAL_GUEST_CPU']
 for phase in('numeric16','numeric160'):commands[phase]+=['--cpu-owner-ref','ACTUAL052_CPU_OWNER_REF3_JSON']
 commands['numeric160']+=['--smoke-owner-ref','ACTUAL052_NUMERIC16_OWNER_REF3_JSON']
 put('COMMANDS052.json',data(dict(template=tr,commands=commands,preconditions={'MAIN_validated_and_explicitly_created_exact_output_parent':OUT,'all_phase_outputs_must_be_absent':True,'fresh_aggregate_CPU_RAM_NPU_ledger_required':True},actual_build_receipt_known=True,actual_build_consumed_by052=False,actual_Meta=False,actual_NPU=False,model_ready=False)))
 files=[dict(relative_path=n,ref=r,text=(P/n).read_bytes().decode('utf8'))for n,r in m['files'].items()];files.append(dict(relative_path='SOURCE_TEMPLATE.json',ref=tr,text=data(m).decode()))
 for f in files:
  raw=f['text'].encode();assert b'\r'not in raw and len(raw)==f['ref']['bytes'] and hashlib.sha256(raw).hexdigest()==f['ref']['sha256']
  if f['relative_path'].endswith('.py'):ast.parse(raw)
 put('BYTE_EXACT_DELIVERY052.json',data(dict(schema='deltalog.prepared-split-numeric/v052',template=tr,files=files,prepared_only=True,actual_NPU=False)))
 print(json.dumps(dict(template=tr,files=len(files))))
if __name__=='__main__':main()
