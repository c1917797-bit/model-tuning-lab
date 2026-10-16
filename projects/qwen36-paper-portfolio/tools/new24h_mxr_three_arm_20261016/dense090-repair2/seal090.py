"""Source-only metadata serializer. Never schedules a model."""
import ast,base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/dense-e2e-opportunity-new24h-v1-090-repair2'
AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json',bytes=3481,sha256='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28')
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 import sys
 sys.path.insert(0,str(P));import owned_substrate as O,contract090 as C
 names=['contract090.py','host090.py','server090.py','client090.py','consume090.py','preflight090.py','test_090.py','native_receipt090.py','snapshot_publication.py','owned_create.py','owned_substrate.py','external025.py','cap48_provider.py','guest_canary.py','worker_snapshot_owner.py','dependencies/original005_server_entry.py','dense_opportunity090/__init__.py','dense_opportunity090-0.0.1.dist-info/METADATA','dense_opportunity090-0.0.1.dist-info/entry_points.txt','HANDOFF090.md','seal090.py']
 files={n:(P/n).read_bytes()for n in names}
 for n,b in files.items():
  if b'\r'in b or not b.endswith(b'\n'):raise ValueError('LF only '+n)
  if n.endswith('.py'):ast.parse(b)
 m=dict(schema='dense.e2e-opportunity-source/v090',root=ROOT,default_enabled=False,authority_ref=AUTH,files={n:ref(ROOT+'/'+n,b)for n,b in files.items()},dependencies=[AUTH,C.DRIVER,*O.REFS.values()],profiles=list(C.PROFILES),measured_requests=C.MEASURED,warmup_requests=C.WARMUPS,output_tokens=1024,concurrency=1,common=dict(HF32=False,eager=True,async_scheduling=False,prefix_cache=False,mamba_cache_mode='none',profiling=False),resources=dict(guest_model_GiB=48,initial_RAM_GiB=56.5,guest_CPU_GiB=8,host_GiB=.5,RAMreserve_GiB=8,whole_seconds=3600,shared_cleanup_seconds=180,opt_initial_GiB=40.5,Docker_reserve_GiB=8.5),candidate_qualification=False,actual_executed=False,READY=False)
 raw=data(m);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw)
 command=['/usr/bin/python3','-I','-B',ROOT+'/host090.py'];C.output_argument(C.OUTPUT_POSIX);assert C.OUT.as_posix()==C.OUTPUT_POSIX;cb=data(dict(source=sr,default_off=command,source_audit=command+['--source-audit','--source-ref',json.dumps(sr,separators=(',',':'))],execute=['/usr/bin/env','DENSE_OPPORTUNITY090_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1',*command,'--execute','--source-ref',json.dumps(sr,separators=(',',':')),'--output',C.OUTPUT_POSIX],NPU_executed=False,READY=False));(P/'COMMANDS090.json').write_bytes(cb);files.update({'SOURCE_MANIFEST.json':raw,'COMMANDS090.json':cb})
 bb=data(dict(schema='dense090.byteexact-source/v1',root=ROOT,READY=False,files=[dict(relative=n,**ref(ROOT+'/'+n,b),base64=base64.b64encode(b).decode())for n,b in sorted(files.items())]));(P/'BYTE_EXACT_DELIVERY090.json').write_bytes(bb);print(json.dumps(dict(source=sr,delivery=ref(str(P/'BYTE_EXACT_DELIVERY090.json'),bb),files=len(files))))
if __name__=='__main__':main()
