"""Emit exact-source metadata/transport via apply_patch; never execute hardware."""
import argparse,ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'deltalog-mixed-precast-new48h-20261015-043-repair2'
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new48h-v1-052'
OUT='/opt/host/vnf/austinov/deltalog-split-scale-numeric-new48h-052'
def data(v):return(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
def ref(n,b):return dict(path=ROOT+'/'+n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def emit(values):
 print('*** Begin Patch')
 for k,b in values.items():
  print('*** Add File: '+(P/k).as_posix())
  for line in b.decode().splitlines():print('+'+line)
 print('*** End Patch')
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--template',action='store_true');ap.add_argument('--seal',action='store_true');ap.add_argument('--artifact',choices=('COMMANDS043.json','BYTE_EXACT_DELIVERY043.json'));a=ap.parse_args()
 import sys
 sys.path.insert(0,str(P));import inverse_repair3
 assert inverse_repair3.verify()
 for n in('oracle.py','precast.py','direct_round.py','sidecar_capture.py','sidecar_audit.py','raw_codec.py','per_request_increment.py','preregister.py','qwen36_deltalog_fresh/provider.py','qwen36_deltalog_fresh/primitives.py','qwen36_deltalog_fresh/runtime_helpers.py','qwen36_deltalog_fresh/transform.py','qwen36_deltalog_fresh/capture_evidence.py'):
  assert(P/n).read_bytes()==(OLD/n).read_bytes(),'operator/math/input/reference changed '+n
 def mathbody(path):
  tree=ast.parse(path.read_bytes());tree.body=[n for n in tree.body if not(isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINNED'for t in n.targets))];return ast.dump(tree,include_attributes=False)
 assert mathbody(P/'domain_consumer.py')==mathbody(OLD/'domain_consumer.py'),'independent domain arithmetic changed'
 skip={'SOURCE_TEMPLATE.json','SOURCE_MANIFEST.json','BYTE_EXACT_DELIVERY043.json','COMMANDS043.json','LOCAL_TEST_RESULT043.json'}
 files={q.relative_to(P).as_posix():q.read_bytes()for q in P.rglob('*')if q.is_file()and'__pycache__'not in q.parts and q.name not in skip}
 for k,b in files.items():
  assert b'\r'not in b and b.endswith(b'\n'),k
  if k.endswith('.py'):ast.parse(b)
 m=json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes());oldroot=m['root'];m=json.loads(json.dumps(m).replace(oldroot,ROOT).replace('deltalog-mixed-precast-new48h-043-repair2','deltalog-split-scale-numeric-new48h-052'))
 import collection_policy
 m.update(root=ROOT,exact_output_root=OUT,prepared_only=True,collection_policy=collection_policy.POLICY)
 m['files']={n:ref(n,b)for n,b in sorted(files.items())};m['collection_repair_scope']='defer BF16 point producer stop only; independent unchanged actualFP32/state/byte/fullcoverage gates decide, oldR2 FAIL retained'
 assert m['validation_contract']==json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes())['validation_contract']
 if a.template:emit({'SOURCE_TEMPLATE.json':data(m)});return
 assert a.seal and(P/'SOURCE_TEMPLATE.json').read_bytes()==data(m),'actual tested frozen source first'
 tr=ref('SOURCE_TEMPLATE.json',data(m));base=['/usr/bin/python3','-I','-B',ROOT+'/run043.py','--execute','--template-ref',json.dumps(tr)]
 commands={s:base+['--phase',s]for s in('bind','sourceaudit','cpu','numeric16','numeric160')};commands['bind']+=['--original035-source-ref','ACTUAL035R4_SOURCE_REF3_JSON']
 for s in('sourceaudit','cpu','numeric16','numeric160'):commands[s]+=['--host-cpu','ACTUAL_HOST_CPU','--guest-cpu','ACTUAL_GUEST_CPU']
 for s in('numeric16','numeric160'):commands[s]+=['--cpu-owner-ref','ACTUAL043R3_CPU_OWNER_REF3_JSON']
 commands['numeric160']+=['--smoke-owner-ref','ACTUAL043R3_NUMERIC16_OWNER_REF3_JSON']
 cmd=data(dict(template=tr,commands=commands,exact_output_root=OUT,parameter_note='only actual same-source CPU/16 releases permit160; oldR2 partial FAIL cannot authorize',default_enabled=False))
 payload=[dict(relative_path=n,ref=ref(n,b),text=b.decode())for n,b in sorted(files.items())];payload.append(dict(relative_path='SOURCE_TEMPLATE.json',ref=tr,text=data(m).decode()))
 values={'COMMANDS043.json':cmd,'BYTE_EXACT_DELIVERY043.json':data(dict(schema='deltalog.exact-prepared-payload/v043',template=tr,files=payload,deployable=False,source_prepared=True,actual_CPU=False,actual_NPU=False,model_ready=False,performance_ready=False))}
 if(P/'LOCAL_TEST_RESULT043.json').is_file():
  b=(P/'LOCAL_TEST_RESULT043.json').read_bytes();values['BYTE_EXACT_DELIVERY043.json']=data(dict(json.loads(values['BYTE_EXACT_DELIVERY043.json']),software_test_result=json.loads(b)))
 emit({a.artifact:values[a.artifact]}if a.artifact else values)
if __name__=='__main__':main()
