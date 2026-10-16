"""Mechanical immutable source metadata/delivery; no build or future artifact."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-new48h-v1-051'
OLD='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-readout-sidecar-v015'
def data(x):return(json.dumps(x,indent=2,sort_keys=True)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 files={}
 for p in P.rglob('*'):
  if not p.is_file()or '__pycache__'in p.parts or p.name in('SOURCE_MANIFEST.json','PACKET_MANIFEST.json','BYTE_EXACT_DELIVERY.json','COMMANDS.json'):continue
  b=p.read_bytes();b.decode('utf8');assert b'\r'not in b and b.endswith(b'\n'),p
  if p.suffix=='.py':ast.parse(b)
  files[p.relative_to(P).as_posix()]=b
 km=dict(schema='deltalog-split-scale-source/v051',default_enabled=False,files=[dict(path=k.removeprefix('kernel/'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for k,b in sorted(files.items())if k.startswith('kernel/')],production_namespace='qwen36_deltalog_split_scale_v051',debug_namespace='qwen36_deltalog_split_scale_sidecar_v051',source_only=True,numeric_qualified=False)
 files['kernel/SOURCE_MANIFEST.json']=data(km)
 m=json.loads((P/'BASE_OWNER_TEMPLATE.json').read_bytes());m.update(root=ROOT+'/build_owner',stage='CPU-split-scale-production-debug-build-only',ready=False,actual_build_result=None,actual_cohort_ref=None,delta='fixed-D128 defaultscale q*=exact2^-4; output*=16*scale; nondefault kernel tiling uses original earlyscale path; state/log math unchanged; no qualification')
 for k in list(m['files']):
  if k!='cache_scan.py':m['files'][k]=ref(ROOT+'/build_owner/'+k,files['build_owner/'+k])
 hostnames=['B010_ORIGINAL_SOURCE.json','verify_inverse.py','sidecar_inverse015.py',*sorted(k for k in files if k.startswith('kernel/'))]
 m['build_host_refs']=[ref(ROOT+'/'+k,files[k])for k in hostnames]
 m['mechanical_verifier']=ref(ROOT+'/verify_inverse.py',files['verify_inverse.py']);m['build_script_ref']=ref(ROOT+'/kernel/build_pair.py',files['kernel/build_pair.py']);m['build_source_manifest']=ref(ROOT+'/kernel/SOURCE_MANIFEST.json',files['kernel/SOURCE_MANIFEST.json'])
 m['source_only']=True;m['actual_same_image']=None;m['numeric_qualified']=False
 files['build_owner/SOURCE_MANIFEST.json']=data(m);own=ref(ROOT+'/build_owner/SOURCE_MANIFEST.json',files['build_owner/SOURCE_MANIFEST.json'])
 base=json.loads((P/'BASE_COMMANDS.json').read_bytes())
 def replace(v):
  if isinstance(v,str):return v.replace(OLD,ROOT).replace('dl-readout-sidecar015-build','dl-split-scale051-build')
  if isinstance(v,list):return[replace(x)for x in v]
  if isinstance(v,dict):return{k:replace(x)for k,x in v.items()}
  return v
 cmds={k:replace(base[k])for k in('binder','source_audit','compile')}
 for command in cmds.values():
  a=command['args']
  if '--self-sha256'in a:a[a.index('--self-sha256')+1]=m['files']['bind_cohort.py']['sha256']
  if '--owner-source-ref'in a:a[a.index('--owner-source-ref')+1]=json.dumps(own)
  if '--source-sha256'in a:a[a.index('--source-sha256')+1]=own['sha256']
 commands=dict(schema='deltalog.split-scale-build-main-commands/v051',default_enabled=False,owner_source=own,commands=cmds,build_result_path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-split-scale051-build-new48h-MAIN-20261015-001/cpu-preflight/producer/build/RESULT.json',Meta_child_only=['python','-I','-B',ROOT+'/meta_abi.py','--execute','--build-ref','ACTUAL_PASSED_BUILD_REF_JSON','--source-ref',json.dumps(m['build_source_manifest']),'--output','ACTUAL_NEW_OWNED_CPU_META_JSON'],NPU_dispatch_allowed=False,reason='actual pair build/Meta/numerical owned receiver and preregistered complete gates pending; no future library refs')
 files['COMMANDS.json']=data(commands)
 packet=dict(schema='deltalog.split-scale-source-packet/v051',root=ROOT,files={k:ref(ROOT+'/'+k,b)for k,b in sorted(files.items())},owner=own,build_source=m['build_source_manifest'],default_enabled=False,prepared_only=True,NPU=False,compiled=False,Meta_pass=False,numeric_qualified=False,model_ready=False,cutoff=1792135097)
 files['PACKET_MANIFEST.json']=data(packet)
 for k,b in files.items():
  if k.endswith('SOURCE_MANIFEST.json')or k in('PACKET_MANIFEST.json','COMMANDS.json'):(P/k).write_bytes(b)
 payload=dict(schema='deltalog.split-scale-byte-exact/v051',root=ROOT,packet=ref(ROOT+'/PACKET_MANIFEST.json',files['PACKET_MANIFEST.json']),files=[dict(relative_path=k,ref=ref(ROOT+'/'+k,b),text=b.decode())for k,b in sorted(files.items())],source_only=True,NPU=False)
 (P/'BYTE_EXACT_DELIVERY.json').write_bytes(data(payload));print(json.dumps(dict(packet=payload['packet'],files=len(files),owner=own)))
if __name__=='__main__':main()
