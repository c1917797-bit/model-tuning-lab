"""Generate only apply_patch; seal transport after actual source ABI tests."""
import base64,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-single-frame-sidecar-new48h-v1-040-repair1'
def ref(path,b):return dict(path=path,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def data(x):return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
old=json.loads((BASE/'deltalog040-actual016-bound-source.json').read_bytes())
actual016=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-precast-empirical-new48h-v1-016/BOUND_NUMERIC_SOURCE.json',bytes=53261,sha256='7d61ca178c78ee8d883d608d644931c555fe44b3ad36c5cdbfea71bb464a7045')
raw=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dlbridge035r4-numeric160-new48h-MAIN-20261015-001/numeric/result/mixed-B16-080.pt',bytes=151267875,sha256='6057c3726a57f778116e8dd1ff7eef6e2aed9c7d4c4213f286c21d18be58171b')
failed=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dlbridge035r4-numeric160-new48h-MAIN-20261015-001/RESULT.json',bytes=1673,sha256='825cfa7ac6246ebb839192e39898d405dedd9ab71746dea2b6874e0f23ce8fc9')
source035=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-diagnostic-bridge-owned-new48h-v1-035-repair4/SOURCE_MANIFEST.json',bytes=26248,sha256='e5566351d02b04792b871f67092876f69b7fb58bbc81c36d21360fb328ec6524')
outputs={k:'/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-frame040repair1-'+k+'-new48h-MAIN-20261015-001'for k in('cpu','numeric')}
commands=dict(schema='deltalog.single-frame-sidecar-commands/v040',root=ROOT,diagnostic_only=True,NPU_executed=False,cutoff_epoch=1792135097,source_sha256='MAIN_REVIEWED040_SOURCE_SHA256',outputs=outputs,stages={k:dict(command='/usr/bin/python3',args=['-I','-B',ROOT+'/run_stage.py','--execute','--source-sha256','MAIN_REVIEWED040_SOURCE_SHA256','--stage',k,'--host-cpu','MAIN_FRESH_HOST_CPU','--guest-cpu','MAIN_FRESH_GUEST_CPU'])for k in('audit','cpu','numeric')},physical=[4],next='MAIN reviews exact SOURCE SHA; actual Devices[] CPU owner first, then same-source singleton frame+secondCPU consumer; no automatic dispatch')
excluded={'SOURCE_MANIFEST.json','DELIVERY.json','INVENTORY.json','COMMANDS.json','SOURCE_DELTA.json'}
files={f.relative_to(P).as_posix():f.read_bytes()for f in P.rglob('*')if f.is_file()and '__pycache__'not in f.parts and f.relative_to(P).as_posix()not in excluded};files['COMMANDS.json']=data(commands)
for k,b in files.items():b.decode();assert b'\r'not in b and b.endswith(b'\n'),k
fixture=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-diagnostic-bridge-owned-new48h-v1-035-repair4/qwen36_deltalog_fresh/native_fixture.py',bytes=16179,sha256='a19e49b0295e03df4b5771910932e59018d4353623f2edd27a5e7d8a1b2a46e6')
dependencies=[fixture,actual016,raw,failed,source035,old['libraries']['key_projection'],old['debug_build_ref'],old['debug_library'],old['debug_kernel_source_ref'],old['kernel_source_ref'],old['build_ref'],old['authority_ref'],old['observer_ref']]
m=dict(schema='deltalog.lifecycle-kernel-source/v007',root=ROOT,default_enabled=False,diagnostic040=True,repair1=True,fixture_source_ref=fixture,window=dict(start=1791962297,cutoff=1792135097),saved_raw_ref=raw,failed160_owner_ref=failed,actual035_source_ref=source035,actual016_source_ref=actual016,production_ref=old['libraries']['key_projection'],original_kernel_source_ref=old['kernel_source_ref'],debug_build_ref=old['debug_build_ref'],debug_library=old['debug_library'],debug_kernel_source_ref=old['debug_kernel_source_ref'],authority_ref=old['authority_ref'],observer_ref=old['observer_ref'],meta_ref=None,numeric_ref=None,dependencies=dependencies,files={k:ref(ROOT+'/'+k,b)for k,b in sorted(files.items())},outputs=outputs,software_cases=14,resources=dict(cpu_owner_seconds=720,numeric_consumer_owner_seconds=2880,numeric_seconds=1800,consumer_seconds=600,cleanup_seconds=90,guest_bytes=8589934592,host_bytes=536870912,ordinary_reserve_bytes=8589934592,raw_cap_bytes=1073741824),qualification=False,model_ready=False,pending=['MAIN sourceaudit','actual sameimage CPU/Meta14','actual owned singleton4 whole16 transparency','actual independent CPU precast/RNE diagnosis and exact release'])
assert m['files']['oracle.py']['sha256']=='cd395a05dbfcb21f1104d617afb1fab6f80374016585e9096ca24d85c2cae97a'and m['files']['direct_round.py']['sha256']=='60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d'
files['SOURCE_MANIFEST.json']=data(m)
if '--manifest-only'in sys.argv:new={k:files[k]for k in('COMMANDS.json','SOURCE_MANIFEST.json')}
else:
 assert (P/'SOURCE_MANIFEST.json').read_bytes()==files['SOURCE_MANIFEST.json']and(P/'COMMANDS.json').read_bytes()==files['COMMANDS.json'],'actual source metadata must be tested before seal'
 inventory=dict(schema='deltalog040-byte-exact/v040',root=ROOT,source=ref(ROOT+'/SOURCE_MANIFEST.json',files['SOURCE_MANIFEST.json']),files=[dict(relative=k,**ref(ROOT+'/'+k,b))for k,b in sorted(files.items())],NPU=False,qualification=False)
 delivery=dict(inventory,files=[dict(relative=k,**ref(ROOT+'/'+k,b),base64=base64.b64encode(b).decode())for k,b in sorted(files.items())]);new={'INVENTORY.json':data(inventory),'DELIVERY.json':data(delivery)}
print('*** Begin Patch')
for k,b in new.items():
 target=P/k
 if target.exists():
  print('*** Update File: '+target.as_posix());print('@@')
  for line in target.read_text().splitlines():print('-'+line)
 else:print('*** Add File: '+target.as_posix())
 for line in b.decode().splitlines():print('+'+line)
print('*** End Patch')
