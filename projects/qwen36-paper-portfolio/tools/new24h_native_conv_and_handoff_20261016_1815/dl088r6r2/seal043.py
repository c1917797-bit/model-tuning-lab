"""LF, exact byte closure, typed commands. No deployment/execution."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,v):
 b=(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode();(P/n).write_bytes(b);return b
def main():
 m=json.loads((P/'SOURCE_TEMPLATE.json').read_text(encoding='utf8'));root=m['root'];files=[]
 for n,r in m['files'].items():
  b=(P/n).read_bytes()
  if b'\r'in b or dict(path=root+'/'+n,bytes=len(b),sha256=sha(b))!=r:raise ValueError('LF/exact source '+n)
  if n.endswith('.py'):ast.parse(b)
  files.append(dict(relative_path=n,ref=r,text=b.decode('utf8')))
 b=(P/'SOURCE_TEMPLATE.json').read_bytes();tr=dict(path=root+'/SOURCE_TEMPLATE.json',bytes=len(b),sha256=sha(b));files.append(dict(relative_path='SOURCE_TEMPLATE.json',ref=tr,text=b.decode()))
 base=['/usr/bin/python3','-I','-B',root+'/run043.py','--execute','--template-ref',json.dumps(tr)]
 cmds={p:base+['--phase',p]for p in('bind','sourceaudit','cpu','numeric16','numeric160')}
 cmds['bind']+=['--original035-source-ref','ACTUAL035R4_SOURCE_REF3_JSON']
 for p in('sourceaudit','cpu','numeric16','numeric160'):cmds[p]+=['--host-cpu','ACTUAL_HOST_CPU','--guest-cpu','ACTUAL_GUEST_CPU']
 for p in('numeric16','numeric160'):cmds[p]+=['--cpu-owner-ref','ACTUAL043_CPU_OWNER_REF3_JSON']
 cmds['numeric160']+=['--smoke-owner-ref','ACTUAL043_NUMERIC16_OWNER_REF3_JSON']
 put('COMMANDS043.json',dict(template=tr,commands=cmds,parameter_note='typed Ref3 JSON and fresh CPU IDs required; no placeholder is an executable receipt',default_enabled=False))
 put('BYTE_EXACT_DELIVERY043.json',dict(schema='deltalog.exact-prepared-payload/v043',template=tr,files=files,deployable=False,source_prepared=True,actual_CPU=False,actual_NPU=False,model_ready=False,performance_ready=False))
 print(json.dumps(dict(template=tr,files=len(files),LF=True,AST=True,prepared_only=True)))
if __name__=='__main__':main()
