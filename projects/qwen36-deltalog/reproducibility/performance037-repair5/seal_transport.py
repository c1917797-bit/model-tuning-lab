"""Emit an apply_patch for transport inventories; never perform source writes."""
import base64,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-production-screen-new48h-20261015-037-repair4')
REMOTE='/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/NEW48H/deltalog-production-screen-PF037R5'
exclude={'SOURCE_DELTA.json','CHANGES.diff','DELIVERY.json','SEALED_FILES.json'}
def ref(path,b):return dict(path=path,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def encode(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
files={f.relative_to(P).as_posix():f.read_bytes()for f in P.rglob('*')if f.is_file()and '__pycache__'not in f.parts and f.name not in exclude}
for k,b in files.items():
 b.decode('utf8');assert b'\r'not in b and b.endswith(b'\n'),k
math=('qwen36_deltalog_screen/runtime.py','qwen36_deltalog_screen/primitives.py','qwen36_deltalog_screen/health.py','qwen36_deltalog_screen/runtime_helpers.py','qwen36_deltalog_screen/integration.py','qwen36_deltalog_screen/cpu_metadata.py','qwen36_deltalog_screen/builder_mirror.py','production_numeric.py','finite_numeric.py','snapshot_publication.py','worker_receipt.py','worker_snapshot_owner.py','test_validation_edges.py','dependencies/publication_common.py','dependencies/direct_round013.py','dependencies/numeric_oracle.py','paired_driver.py','server_entry.py','pair_consume.py','whole_consume.py','owned_create.py','cap48_provider.py')
for name in math:assert files[name]==(OLD/name).read_bytes(),'protected production math/protocol/owner unchanged '+name
import sys
sys.path.insert(0,str(P));from test_receiver import source_identity
assert source_identity(json.loads(files['CONFIGURATION_TEMPLATE.json']),json.loads(files['COMMANDS.json']),files['owned_substrate.py'].decode(),files['host_validate.py'].decode(),files['host_pair.py'].decode())
pins=json.loads(files['receivers/DOMAIN_PINS.json'])
assert pins['model036_template']['sha256']=='82cc86940c1cd77a533415d809649f73847b552926bd1b2504730172c8377470'
assert pins['reviewed_domain_template_ref']['sha256']=='e9243ee9acc0f066421dc7e3b11285533a8df3c8478830afe40be6e25f18dd49'
delta=[];diff=[]
for k,b in sorted(files.items()):
 prior=OLD/k;old=prior.read_bytes()if prior.is_file()else b''
 delta.append(dict(file=k,current=ref(REMOTE+'/'+k,b),baseline=ref(str(prior),old)if prior.is_file()else None,byte_identical=prior.is_file()and old==b))
 if k.endswith('.py')and old!=b:diff.extend(difflib.unified_diff(old.decode().splitlines(True),b.decode().splitlines(True),fromfile='PF037R4/'+k,tofile='PF037R5/'+k))
files['CHANGES.diff']=''.join(diff).encode()
files['SOURCE_DELTA.json']=encode(dict(schema='deltalog.PF037R5-pin-only-source-delta/v037',protected_unchanged=list(math),files=delta,default_enabled=False,NPU=False,qualification=False))
inventory=dict(schema='deltalog.PF037R5-transport-inventory/v037',remote_root=REMOTE,files=[dict(relative=k,**ref(REMOTE+'/'+k,b))for k,b in sorted(files.items())],source_manifest_bound=False,NPU=False,qualification=False)
delivery=dict(schema='deltalog.PF037R5-byte-exact-delivery/v037',remote_root=REMOTE,files=[dict(relative=k,**ref(REMOTE+'/'+k,b),base64=base64.b64encode(b).decode())for k,b in sorted(files.items())],prepared_only=True,NPU=False,qualification=False)
new={'CHANGES.diff':files['CHANGES.diff'],'SOURCE_DELTA.json':files['SOURCE_DELTA.json'],'SEALED_FILES.json':encode(inventory),'DELIVERY.json':encode(delivery)}
print('*** Begin Patch')
for k,b in new.items():
 print('*** Add File: '+(P/k).as_posix())
 for line in b.decode().splitlines():print('+'+line)
print('*** End Patch')
