"""Local source serialization only; no remote calls or runtime ledger writes."""
import ast,base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-093'
def enc(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 import sys
 sys.path.insert(0,str(P));import sealed_storage093 as S,capture093 as C
 names=['sealed_storage093.py','capture093.py','bind_plan.py','test093.py','HANDOFF.md','seal_source093.py','evidence/ledger7-observed.json','evidence/owners-observed.json','evidence/cids-observed.json','evidence/operation-notfound-observed.json']
 # Projections are normalized JSON locators, never advertised as original remote bytes.
 for n in names:
  if n.startswith('evidence/'):(P/n).write_bytes(enc(json.loads((P/n).read_bytes())))
 files={n:(P/n).read_bytes()for n in names}
 for n,b in files.items():
  assert b'\r'not in b and b.endswith(b'\n'),n
  if n.endswith('.py'):ast.parse(b)
 baseline=json.loads(files['evidence/ledger7-observed.json'])['ledger']
 m=dict(schema='deltalog.closed-storage-source/v093',root=ROOT,prepared_only=True,default_enabled=False,files={n:ref(ROOT+'/'+n,b)for n,b in files.items()},dependencies=[S.OLD,S.SOURCE,S.BASE,C.AUTH,C.CURRENT,baseline['sealed_evidence_ref'],baseline['storage069_template_ref']],source_069=S.SOURCE,baseline_ledger_ref=S.BASE,closed_names=list(S.NAMES),max_total_bytes=80*S.GIB,min_free_bytes=100*S.GIB,evidence_cap_bytes=C.MAX,operation_receipts_unavailable=True,qualification=False,READY=False)
 raw=enc(m);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw);cmd=['/usr/bin/python3','-I','-B',ROOT+'/capture093.py'];plan=ROOT+'/PLAN093.json';cmds=dict(source=sr,software=['/usr/bin/python3','-I','-B',ROOT+'/test093.py'],bind_plan=['/usr/bin/python3','-I','-B',ROOT+'/bind_plan.py','--execute','--source-ref',json.dumps(sr),'--unavailable-ref','ACTUAL_CPU_NOT_FOUND_REF3','--unavailable-ref','ACTUAL_N16_NOT_FOUND_REF3','--unavailable-ref','ACTUAL_N160_NOT_FOUND_REF3','--output',plan],preflight=[*cmd,'--execute','--phase','preflight','--template-ref',json.dumps(sr),'--plan-ref','ACTUAL_PLAN_REF3'],capture=[*cmd,'--execute','--phase','capture','--template-ref',json.dumps(sr),'--plan-ref','ACTUAL_PLAN_REF3'],seal=[*cmd,'--execute','--phase','seal','--template-ref',json.dumps(sr),'--evidence-ref','ACTUAL_CAPTURED_EVIDENCE_REF3'],placeholders_are_required_actual_Ref3=True,no_current_seal_claimed=True,host_AS_bytes=512*2**20,collector_timeout_seconds=600,cleanup_reserve_seconds=90)
 # Actual historical storage module is read only; no inherited path alias.
 m['dependencies'].append(dict(path=S.SOURCE['path'].rsplit('/',1)[0]+'/storage061.py',bytes=5543,sha256='ca8c1ee593cb94825736dca93f28834c720bb8baccaa3c65adcfa3f4c956161c'))
 raw=enc(m);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw);cmds['source']=sr
 for kind in('preflight','capture','seal'):cmds[kind][cmds[kind].index('--template-ref')+1]=json.dumps(sr)
 cmds['bind_plan']=['/usr/bin/python3','-I','-B',ROOT+'/bind_plan.py','--execute','--source-ref',json.dumps(sr),'--unavailable-ref',json.dumps(m['files']['evidence/operation-notfound-observed.json']),'--output',plan]
 cb=enc(cmds);(P/'COMMANDS093.json').write_bytes(cb);files['SOURCE_MANIFEST.json']=raw;files['COMMANDS093.json']=cb
 bb=enc(dict(schema='deltalog.closed-storage-delivery/v093',root=ROOT,READY=False,files=[dict(relative=n,**ref(ROOT+'/'+n,b),base64=base64.b64encode(b).decode())for n,b in sorted(files.items())]));(P/'BYTE_EXACT_DELIVERY093.json').write_bytes(bb);print(json.dumps(dict(source=sr,delivery=ref(str(P/'BYTE_EXACT_DELIVERY093.json'),bb),files=len(files))))
if __name__=='__main__':main()
