"""Actual044 component and real043R2 bootstrap receipts; no old012 math grant."""
import hashlib,json
from pathlib import Path,PurePosixPath

def need(v,m):
 if not v:raise ValueError(m)

def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact immutable Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary actual Ref')
 h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
 need((size,h.hexdigest())==(r['bytes'],r['sha256']),'actual whole Ref bytes')
 return p

def obj(r):return json.loads(checked(r).read_bytes())

def source(r,pin):
 m=obj(r);need(m['root']==pin['root']and m['files']==pin['files']and m['default_enabled']is False,'actual exact reviewed source inventory')
 need(m.get('prepared_template',m.get('activation_template_ref'))==pin['template'],'actual source bound from this exact reviewed template')
 for leaf in m['files'].values():checked(leaf)
 return m

def argument_object(text):
 # Stored exec records preserve one transport-escaped JSON argv layer.
 try:return json.loads(text)
 except json.JSONDecodeError:
  need(text.startswith('{\\"')and text.endswith('}'),'only observed JSON-object argv encoding')
  return json.loads(json.loads('"'+text+'"'))

def terminal(tr,source_ref,owner_ref,script):
 v=obj(tr);v=v.get('structuredContent',v);r=v['operation']['result']['record']
 need(v['schema']=='agentweb.operation/v1'and v['terminal']is v['succeeded']is True and r['state']=='completed'and r['exitCode']==0 and r['timedOut']is r['cancelled']is False and r['error']is None,'actual successful terminal, not owner bool')
 need(v['operation']['routeDecision']in('peer_direct','upstream_local_peer')and v['operation']['targetPeerId']=='lgw_a6109c51076a4a2c9d2674ca5a8704a0','actual direct precise peer')
 if script=='mainhost.py':
  need((tr['bytes'],tr['sha256'])==(3032,'223d010aaa64f14f82ad52a050eac46812e367e7175c04b4364dcad3a5f0ec40')and r['id']=='exec-0000000000000934','exact actual044 terminal snapshot')
  need(r['command']=='/usr/bin/python3'and r['cwd']=='/opt/host/vnf/austinov/model-tuning-lab','actual044 canonical direct invocation')
  args=r['args'];need(len(args)==10 and args[3]=='--source-ref'and args[5:7]==['--execute','--cpu-preflight-ref']and args[8]=='--output','exact actual044 argv shape')
  need(argument_object(args[4])==source_ref and args[9]==str(PurePosixPath(owner_ref['path']).parent),'actual044 terminal source/output')
 else:
  need(script=='host_ticket.py'and (tr['bytes'],tr['sha256'])==(2766,'2f22245163089883fd6b54954b09804a228796a04afc01683e4b1476ff9f8eab')and r['id']=='exec-0000000000000920','exact actual043R2 observed terminal snapshot')
  need(r['command']=='/usr/bin/env'and r['cwd']is None and r['args'][:2]==['MXR_DL_EXTERNAL_OUTPUT008_ENABLE=1','/usr/bin/python3'],'only exact prior absolute env command with recorded nullcwd')
  args=r['args'][2:];need(len(args)==8 and args[3:5]==['--execute','--source-sha256']and args[5]==source_ref['sha256']and args[6]=='--prerequisite-ref','exact prior043R2 absolute invocation/source')
  need(argument_object(args[7])==dict(bytes=136215,path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_MXR039_PREREQUISITE_043_001.json',sha256='f620ae4bc10577465bff7fbb3af67ce424f2cca7c09805aa13f5f55dfce525f4'),'exact prior043R2 prerequisite argument')
 need(args[:3]==['-I','-B',str(PurePosixPath(source_ref['path']).parent/script)]and '--execute'in args,'exact absolute script, isolated Python and original action')
 need(owner_ref['path']in r['stdout'],'actual terminal publishes same owner path')
 return True

def consume(plan):
 need(type(plan)is dict and set(plan)=={'component_source','component_owner','component_terminal','short_source','short_owner','short_terminal'},'complete actual044+043 receipts required; no template or old012 substitute')
 pins=json.loads((Path(__file__).resolve().parent/'PREDECESSOR_PINS.json').read_bytes())
 cm=source(plan['component_source'],pins['owned044']);need(cm['component044_source']==pins['component044'],'same immutable044 algorithm')
 co=obj(plan['component_owner']);terminal(plan['component_terminal'],plan['component_source'],plan['component_owner'],'mainhost.py')
 need(co['schema']=='mxr.block-refinement-owned/v044'and co['source']==plan['component_source']and co['primary']is None and co['secondary']==[]and co['released']is True and co['cpu_preflight']is False,'actual044 numeric and cleanup complete')
 cr=obj(co['result']);need(cr['schema']=='mxr.block-refinement-owned-consumer/v044'and cr['source']==plan['component_source']and cr['component_source']==pins['component044']and cr['complete']is cr['pass_gate']is True and cr['case_outputs']==[3]*9 and cr['independent_exit']==0,'actual allnine/three repeat numeric PASS')
 independent=obj(cr['independent']);need(independent['source']==pins['component044']and independent['complete']is independent['pass_gate']is True and len(independent['rows'])==9,'independent original gate actual044')
 need([r['name']for r in independent['rows']]==pins['case_names']and all(r['pass_gate']is True and r['all_tile_head_pass']is True and r['legacy_short_bitwise']is True for r in independent['rows']),'complete actual shape/tile/head/oldshort bitwise witnesses')
 sm=obj(plan['short_source']);need(sm['root']==pins['short043']['root']and sm['files']==pins['short043']['files']and sm['default_enabled']is False,'exact short043R2 source, not old012 algorithm')
 for leaf in sm['files'].values():checked(leaf)
 so=obj(plan['short_owner']);terminal(plan['short_terminal'],plan['short_source'],plan['short_owner'],'host_ticket.py')
 need(so['source']==plan['short_source']and so['schema']=='mxr.observerless-once-short48-owned-host/v1'and so['primary']is None and so['secondary']==[]and so['all_created_containers_release_verified']is True and so['short_all4_48GDN_gate']['passed']is True,'actual released043R2 bootstrap48')
 rows=so['actual48_GDN_output_state_consumers'];need([r['rank']for r in rows]==[0,1,2,3],'four real short ranks')
 prefixes=[]
 for row in rows:
  x=obj(row['result']);need(x['capture_source']==plan['short_source']and x['gdn_frame_gate_pass']is True and x['reference_contract']=='mxr.independent-canonical-working-storage/v043'and len(x['rows'])==len(x['layer_prefixes'])==48,'same actual full short working-domain consumer')
  need(all(r['tokens']==129 and r['pass_gate']is True for r in x['rows']),'exact actual129 shape')
  prefixes.append(set(x['layer_prefixes']))
 need(len(prefixes[0])==48 and all(p==prefixes[0]for p in prefixes),'all4 same48 actual GDN prefixes')
 return dict(actual044_operator_pass=True,bootstrap_short043_pass=True,bootstrap_is_not044_fullmodel_numeric=True,old012_grants_no_math=True,long_qualified=False,performance_ready=False,readset=list(plan.values())+[co['result'],cr['independent']]+[r['result']for r in rows])
