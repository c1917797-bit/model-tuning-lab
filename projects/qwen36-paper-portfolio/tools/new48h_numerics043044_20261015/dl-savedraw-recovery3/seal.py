"""Mechanical LF exact delivery; not an execution receipt."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog043r3-sidecar-cpu-recovery-new48h-v1-001-repair3'
def data(x):return(json.dumps(x,indent=2,sort_keys=True)+'\n').encode()
def ref(n,b):return dict(path=ROOT+'/'+n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 files={}
 for p in P.rglob('*'):
  if not p.is_file()or '__pycache__'in p.parts or p.name in('SOURCE_MANIFEST.json','SOURCE_TEMPLATE.json','BYTE_EXACT_DELIVERY.json','COMMANDS.json'):continue
  b=p.read_bytes();assert b'\r'not in b,p
  if p.suffix=='.py':ast.parse(b)
  files[p.relative_to(P).as_posix()]=b
 m=dict(schema='deltalog.saved043R3-recovery-preparation/v1',root=ROOT,files={n:ref(n,b)for n,b in files.items()},prepared_only=True,NPU=False,original_host_FAILURE_unchanged=True,actual_CPU=False)
 b=data(m);(P/'SOURCE_TEMPLATE.json').write_bytes(b);tr=ref('SOURCE_TEMPLATE.json',b)
 cmds={p:['/usr/bin/python3','-I','-B',ROOT+'/run_recovery.py','--execute','--template-ref',json.dumps(tr),'--phase',p]+([]if p=='bind'else['--host-cpu','MAIN_FRESH_HOST_CPU','--guest-cpu','MAIN_FRESH_GUEST_CPU'])for p in('bind','sourceaudit','cpu')}
 command=data(dict(template=tr,commands=cmds,parameter_note='CPU IDs from MAIN fresh resources; no NPU commands'))
 (P/'COMMANDS.json').write_bytes(command);files.update({'SOURCE_TEMPLATE.json':b,'COMMANDS.json':command})
 payload=dict(root=ROOT,template=tr,files=[dict(relative_path=n,ref=ref(n,b),text=b.decode())for n,b in files.items()],prepared_only=True,actual_CPU=False,NPU=False)
 (P/'BYTE_EXACT_DELIVERY.json').write_bytes(data(payload));print(json.dumps(dict(template=tr,files=len(files))))
if __name__=='__main__':main()
