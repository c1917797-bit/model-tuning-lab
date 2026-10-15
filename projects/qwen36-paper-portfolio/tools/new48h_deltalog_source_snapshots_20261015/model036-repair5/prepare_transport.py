"""Emit only byte-exact patch for immutable MODEL036R5 bridge-pin successor."""
import base64,difflib,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=Path(str(P).replace('036-repair5','036-repair4'))
BRIDGE=P.parent/'deltalog-diagnostic-bridge-owned-new48h-20261015-035-repair4'
REMOTE='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-model-directRNE-smoke-v1-MODEL036-repair5'
def ref(path,b):return dict(path=path,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def data(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
tr=(BRIDGE/'SOURCE_TEMPLATE.json').read_bytes()
assert len(tr)==27796 and hashlib.sha256(tr).hexdigest()=='e9243ee9acc0f066421dc7e3b11285533a8df3c8478830afe40be6e25f18dd49'
bridge=json.loads(tr);assert len(bridge['files'])==68
excluded={'SOURCE_TEMPLATE.json','SOURCE_DELTA.json','CHANGES.diff','BYTE_EXACT_DELIVERY.json'}
files={f.relative_to(P).as_posix():f.read_bytes()for f in P.rglob('*')if f.is_file()and '__pycache__'not in f.parts and f.name not in excluded}
for k,b in files.items():b.decode('utf8');assert b'\r'not in b and b.endswith(b'\n'),k
assert hashlib.sha256(files['tensor_consumer.py']).hexdigest()=='e3ff9d02f43b9c3537c370343fdab4b2612b19fd9cd3e667ef8be547765226e0'
protected=('tensor_consumer.py','tensor_observer.py','trace_plugin.py','run_owned.py','entry.py','client.py','consume_trajectory.py','request_identity.py','identity_events.py','owner_overlay.py','host_ticket.py','dependencies/numeric_oracle.py','dependencies/direct_round013.py','domain_qualification.py','consume.py','test_direct_model_reference.py','test_tensor_controls.py')
for k in protected:assert files[k]==(OLD/k).read_bytes(),'unexpected math/owner/consumer change '+k
oldroot=json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes())['root']
delta=[];diff=[]
for k,b in sorted(files.items()):
 f=OLD/k;old=f.read_bytes()if f.is_file()else b''
 delta.append(dict(file=k,current=ref(REMOTE+'/'+k,b),baseline=ref(oldroot+'/'+k,old)if f.is_file()else None,byte_identical=f.is_file()and old==b))
 if old!=b:diff.extend(difflib.unified_diff(old.decode().splitlines(True),b.decode().splitlines(True),fromfile='MODEL036R4/'+k,tofile='MODEL036R5/'+k))
files['CHANGES.diff']=''.join(diff).encode();files['SOURCE_DELTA.json']=data(dict(schema='deltalog.MODEL036R5-source-delta/v036-repair5',protected_byte_identical=list(protected),files=delta,model_math_changed=False,NPU=False))
m=json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes())
def change(v):
 if type(v)is str:return v.replace(oldroot,REMOTE)
 if type(v)is list:return [change(x)for x in v]
 if type(v)is dict:return {k:change(x)for k,x in v.items()}
 return v
m=change(m)
m.update(root=REMOTE,prepared_only=True,plugin_source=None,composite_source_ref=None,composite_cpu_owner_ref=None,bridge024_source_ref=None,bridge024_owner_ref=None,bridge024_qualification_api_ref=None,expected_bound_bridge_ref=None,reviewed_domain_files=bridge['files'],reviewed_domain_template_ref=ref(bridge['root']+'/SOURCE_TEMPLATE.json',tr))
m['runtime_identity']=dict(owner='deltalog-MODEL036R5-new48h-MAIN-20261015-001',container_prefix='deltalog-MODEL036R5-',run_id='NEW48H_MODEL036R5_001')
m['output_root']='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-deltalog-MODEL036R5-main-NEW48H_MODEL036R5_001'
m['software_cases']=48
m['bridge_binding_policy']='actual existing SOURCE_MANIFEST Ref must match final reviewed035repair4 template/root/files/contract; resolve null only during real binder, never future PASS'
m['pending']=['actual035repair4 bound source/full160 original success owner/domain/release','actualMODEL036R5 binding/sourceaudit/sameimage48/parser/model/selected directRNE results','PF037R5/accuracy exactcontract receivers','full48 numerical/model/task/performance qualification not supplied'];m['mandatory_unfinished_gates']=m['pending']
m['files']={k:ref(REMOTE+'/'+k,b)for k,b in sorted(files.items())}
deps={r['path']:r for r in m['dependencies']if '/deltalog-diagnostic-bridge-owned-new48h-v1-035'not in r['path']}
for r in [m['reviewed_domain_template_ref'],*bridge['files'].values()]:deps[r['path']]=r
m['dependencies']=list(deps.values());files['SOURCE_TEMPLATE.json']=data(m)
sys.path.insert(0,str(P));from test_source_identity import check
assert check(m,json.loads(files['COMMANDS.json']))
delivery=dict(schema='deltalog.MODEL036R5-byte-exact-delivery/v036-repair5',remote_root=REMOTE,prepared_only=True,NPU=False,files=[dict(relative=k,**ref(REMOTE+'/'+k,b),base64=base64.b64encode(b).decode())for k,b in sorted(files.items())])
new={k:files[k]for k in('CHANGES.diff','SOURCE_DELTA.json','SOURCE_TEMPLATE.json')};new['BYTE_EXACT_DELIVERY.json']=data(delivery)
if '--template-only'in sys.argv:new={'SOURCE_TEMPLATE.json':files['SOURCE_TEMPLATE.json']}
else:
 assert (P/'SOURCE_TEMPLATE.json').read_bytes()==files['SOURCE_TEMPLATE.json'],'actual template must be tested before final transport seal'
 new.pop('SOURCE_TEMPLATE.json')
print('*** Begin Patch')
for k,b in new.items():
 print('*** Add File: '+(P/k).as_posix())
 for line in b.decode().splitlines():print('+'+line)
print('*** End Patch')
