"""LF byte-exact thin-owner source freeze; no execution/qualification."""
import argparse,ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;COMP=P.parent/'mxr-block-refinement-new48h-044';OLD=P.parent/'mxr-working-domain-heldout-new48h-042'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-block-refinement-owned-new48h-v1-044';OUT='/cache/cch/qwen36-paper-preparation-20261007/lowbit'
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def ref(n,b):return dict(path=ROOT+'/'+n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def emit(rows):
 print('*** Begin Patch')
 for n,b in rows.items():
  print('*** Add File: '+(P/n).as_posix())
  for s in b.decode().splitlines():print('+'+s)
 print('*** End Patch')
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--template',action='store_true');p.add_argument('--seal',action='store_true');p.add_argument('--artifact');a=p.parse_args();cm=json.loads((COMP/'SOURCE_MANIFEST.json').read_bytes());cb=(COMP/'SOURCE_MANIFEST.json').read_bytes()
 for name,r in cm['files'].items():
  b=(COMP/name).read_bytes();assert(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'sealed component unchanged '+name
 skip={'SOURCE_TEMPLATE.json','SOURCE_MANIFEST.json','COMMANDS.json','BYTE_EXACT_DELIVERY.json','SOFTWARE_REPORT.json'}
 files={q.relative_to(P).as_posix():q.read_bytes()for q in P.rglob('*')if q.is_file()and'__pycache__'not in q.parts and q.name not in skip}
 for n,b in files.items():
  assert b'\r'not in b and b.endswith(b'\n'),n
  if n.endswith('.py'):ast.parse(b)
 m=dict(schema='mxr.block-refinement-owned-source/v044',root=ROOT,default_enabled=False,prepared_only=True,window=dict(start=1791962297,cutoff=1792135097),files={n:ref(n,b)for n,b in sorted(files.items())},component044_source=dict(path=cm['root']+'/SOURCE_MANIFEST.json',bytes=len(cb),sha256=hashlib.sha256(cb).hexdigest()),owned042_source=cm['actual042_source'],component_budgets=cm['budgets'],model_ready=False,performance_ready=False,scope='ninecase operator numeric only; original042 Controller/Joint/DEVICE-SMI-ARM/cleanup reused')
 if a.template:emit({'SOURCE_TEMPLATE.json':data(m)});return
 assert a.seal and(P/'SOURCE_TEMPLATE.json').read_bytes()==data(m),'fresh exact source first';tr=ref('SOURCE_TEMPLATE.json',data(m))
 template=['/usr/bin/python3','-I','-B',ROOT+'/bind.py','--execute','--template-ref',json.dumps(tr)]
 common=['/usr/bin/python3','-I','-B',ROOT+'/mainhost.py','--source-ref','ACTUAL_BOUND_OWNED044_SOURCE_REF3_JSON']
 commands=dict(schema='mxr044-owned-thin-commands/v1',template=tr,environment={'MXR_SAVED_FRAME_HOST_ENABLE':'1'},canonical_cwd='/opt/host/vnf/austinov/model-tuning-lab',bind=template,sourceaudit=common+['--source-audit-only'],CPU=common+['--execute','--cpu-preflight','--output',OUT+'/run-mxr-block-refinement044-CPU_001'],NPUthenCPU=common+['--execute','--cpu-preflight-ref','ACTUAL_SAME_SOURCE_044_CPU_OWNER_REF3_JSON','--output',OUT+'/run-mxr-block-refinement044-NPU_001'],budget=cm['budgets'],no_autorun=True,NPU=False,model_ready=False)
 payload=[dict(relative_path=n,ref=ref(n,b),text=b.decode())for n,b in sorted(files.items())]+[dict(relative_path='SOURCE_TEMPLATE.json',ref=tr,text=data(m).decode())]
 values={'COMMANDS.json':data(commands),'BYTE_EXACT_DELIVERY.json':data(dict(schema='mxr044-owned-byteexact-source/v1',template=tr,files=payload,NPU=False,model_ready=False,software_report=json.loads((P/'SOFTWARE_REPORT.json').read_bytes())if(P/'SOFTWARE_REPORT.json').exists()else None))}
 emit({a.artifact:values[a.artifact]}if a.artifact else values)
if __name__=='__main__':main()
