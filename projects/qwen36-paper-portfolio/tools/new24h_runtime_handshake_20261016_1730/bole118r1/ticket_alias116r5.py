"""Exact released CPU single-RW mount translation; never broad prefix replace."""
import json
from pathlib import Path
def resolve(C,sr,m,owner_ref,cv,stage):
 root=Path(owner_ref['path']).parent
 C.need(Path(owner_ref['path']).name=='RESULT.json'and root==Path(m['output_root'])/'cpu','actual source CPU owner path')
 C.need(cv['source']==sr and cv['cid']and cv['stage_result']['path']==str(root/'preflight/STAGE_RESULT.json'),'CPU owner/stage path join')
 r=stage['actual_abi_ref'];guest='/adakv-results/preflight/ACTUAL_FIA_ABI.json';host=root/'preflight/ACTUAL_FIA_ABI.json'
 C.need(r['path']in(guest,str(host)),'only exact FIA ABI filename/location')
 ir=C.ref(root/'FINAL_INSPECT.json');x=C.obj(ir);h=x['HostConfig'];cfg=x['Config'];st=x['State']
 C.need(x['Id']==cv['cid']and x['Image']==m['image']and st['Running']is False and st['Pid']==0 and st['ExitCode']==0 and st['OOMKilled']is False and not x.get('ExecIDs'),'actual same CID natural stopped CPU success')
 C.need(cfg['Labels'].get('qwen36.owner')=='bole-tree-CPUCONV118ABIR1','actual new CPU owner label')
 C.need(not h.get('Devices')and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')and h['ReadonlyRootfs']is True and h['Privileged']is False,'actual Devices[] restricted CPU')
 mounts=x['Mounts'];rw=[v for v in mounts if v['RW']]
 C.need(len(rw)==1 and rw[0]['Source']==str(root)and rw[0]['Destination']=='/adakv-results'and rw[0]['Type']=='bind','sole exact CPU output RW binding')
 C.need(not any(v['Destination']in('/adakv-results/preflight','/adakv-results/preflight/ACTUAL_FIA_ABI.json')for v in mounts),'no nested shadow mount')
 cmd=cfg['Cmd'];source_pos=cmd.index('--source-ref')
 C.need(json.loads(cmd[source_pos+1])==sr and cmd[-2:]==['--output','/adakv-results/preflight']and m['files']['cpu116.py']['path']in cmd,'actual source-bound CPU child argv')
 mapped=dict(r,path=str(host));C.checked(mapped)
 return mapped,ir
