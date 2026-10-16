"""Mechanical JSON byte delivery serializer only; never dispatches experiments."""
import base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-native-prefill-owned-new24h-v1-081'
DONOR=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-split-scale-numeric-new24h-20261016-069-repair1')
GUEST=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-native-prefill-counterfactual-new24h-079')
def data(x):return(json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def ref(path,b):return dict(path=path,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 m=json.loads((DONOR/'SOURCE_TEMPLATE.json').read_bytes());g=json.loads((GUEST/'SOURCE_MANIFEST.json').read_bytes());gr=ref(g['root']+'/SOURCE_MANIFEST.json',(GUEST/'SOURCE_MANIFEST.json').read_bytes())
 names=['owner081.py','test_owner081.py','HANDOFF.md','seal081.py'];files={n:(P/n).read_bytes()for n in names}
 for n,b in files.items():
  if b'\r'in b or not b.endswith(b'\n'):raise ValueError('LF-only '+n)
 donor=m['files']['host.py'];assert ref(donor['path'],(DONOR/'host.py').read_bytes())==donor
 pipe=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/NEW48H/deltalog-v7-20261014-001/pipeline.py',bytes=40280,sha256='1df9ce6cac75b68e0f8781c40a2445887a00494941c9cde9488abafe735ab07c')
 deps=dict(pipeline=pipe,cpu=dict(path=pipe['path'].replace('pipeline.py','cpu_capacity.py'),bytes=5043,sha256='992cfcb419eabbf69902f9358c703815c268d3f99b00ae9e410a291d374d456d'),host=dict(path='/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py',bytes=Path('C:/Users/Huawei/paper-piercing-handoff/NEW48H-20261014/DL_FULL_MATRIX_HOST.py').stat().st_size,sha256='ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86'),old=dict(path='/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py',bytes=Path('C:/Users/Huawei/paper-piercing-handoff/NEW48H-20261014/DL_SAVED_NATIVE_ORDER_HOST.py').stat().st_size,sha256='86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc'))
 own=dict(schema='deltalog.native-prefill-owned-source/v081',root=ROOT,default_enabled=False,authority_ref=g['authority_ref'],guest_source=gr,donor_host=donor,dependencies=deps,files={n:ref(ROOT+'/'+n,b)for n,b in files.items()},physical=5,logical=0,resources=dict(guest_bytes=8*2**30,host_bytes=2**29,reserve_bytes=8*2**30,whole_seconds=900,guest_seconds=600,cleanup_seconds=90,raw_bytes=256*2**20,output_bytes=2**30),qualified=False,NPU_executed=False,READY=False)
 raw=data(own);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw)
 common=['/usr/bin/python3','-I','-B',ROOT+'/owner081.py'];commands=dict(schema='deltalog.native-prefill-owned-commands/v081',source=sr,default_off=common,source_audit=common+['--source-audit','--source-ref',json.dumps(sr,separators=(',',':'))],execute=common+['--execute','--source-ref',json.dumps(sr,separators=(',',':')),'--host-cpu','MAIN_ACTUAL_HOST_CPU','--guest-cpu','MAIN_ACTUAL_DISJOINT_GUEST_CPU','--output','/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-native081-MAIN-20261016-001'],qualified=False,MAIN_only=True)
 cb=data(commands);(P/'COMMANDS.json').write_bytes(cb);files.update({'SOURCE_MANIFEST.json':raw,'COMMANDS.json':cb})
 bundle=dict(schema='deltalog081.source-only-byteexact/v1',root=ROOT,NPU=False,READY=False,files=[dict(relative=n,**ref(ROOT+'/'+n,b),base64=base64.b64encode(b).decode())for n,b in sorted(files.items())]);bb=data(bundle);(P/'BYTE_EXACT_DELIVERY.json').write_bytes(bb)
 print(json.dumps(dict(source=sr,delivery=ref(str(P/'BYTE_EXACT_DELIVERY.json'),bb),files=len(files))))
if __name__=='__main__':main()
