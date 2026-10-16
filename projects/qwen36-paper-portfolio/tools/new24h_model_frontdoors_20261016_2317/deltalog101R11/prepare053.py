"""Local source metadata only; exact final052 pins required, no actual PASS."""
import ast,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-model-new24h-v1-058'
OLD=P.parent/'deltalog-model-precast-smoke-new48h-20261015-045-repair3'
def data(x):return(json.dumps(x,indent=2,sort_keys=True)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 import argparse
 a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('--final052-template',type=Path,required=True);a.add_argument('--bytes',type=int,required=True);a.add_argument('--sha256',required=True);a.add_argument('--seal',action='store_true');v=a.parse_args()
 b=v.final052_template.read_bytes();assert len(b)==v.bytes and hashlib.sha256(b).hexdigest()==v.sha256,'final MAIN-reviewed052 template only';t=json.loads(b);tr=ref(t['root']+'/SOURCE_TEMPLATE.json',b)
 assert t['prepared_only']is True and t['validation_contract']['seed_base']==2610165101
 assert t['window']==dict(start=1792134133,cutoff=1792220533),'new056 window, not old052'
 (P/'packet_predecessor.py').write_bytes(('"""Exact reviewed056 source only, no actual qualification."""\nimport json\nTEMPLATE_REF=json.loads('+repr(json.dumps(tr,separators=(',',':')))+')\nFILES=json.loads('+repr(json.dumps(t['files'],separators=(',',':')))+')\n').encode('utf8'))
 old=json.loads((OLD/'SOURCE_TEMPLATE.json').read_bytes());oldroot=old['root']
 files={}
 for p in P.rglob('*'):
  if not p.is_file()or '__pycache__'in p.parts or p.name in('SOURCE_MANIFEST.json','SOURCE_TEMPLATE.json','BYTE_EXACT_DELIVERY.json','SOURCE_DELTA.json','CHANGES.diff','REVIEWED_052_TEMPLATE.json'):continue
  bb=p.read_bytes();assert b'\r'not in bb and bb.endswith(b'\n'),p
  if p.suffix=='.py':ast.parse(bb)
  files[p.relative_to(P).as_posix()]=bb
 import packet_contract as K
 def replace(x):
  if isinstance(x,str):return x.replace(oldroot,ROOT).replace('MODEL045R3','MODEL058')
  if isinstance(x,list):return[replace(i)for i in x]
  if isinstance(x,dict):return{k:replace(i)for k,i in x.items()}
  return x
 m=replace(old);m.update(root=ROOT,output_root=K.OUTPUT,runtime_identity=K.IDENTITY,software_cases=K.SOFTWARE_CASES,prepared_only=True,plugin_source=None,bridge024_source_ref=None,bridge024_owner_ref=None,component_cpu_owner_ref=None,production_build_ref=None,split_kernel_source_ref=t['split_kernel_source_ref'],split_qualification_api_ref=None,debug_library=None,debug_build_ref=None,debug_kernel_source_ref=None,library_ref=None,expected_bound_bridge_ref=None,reviewed_domain_template_ref=tr,reviewed_domain_files=t['files'],admission_mode='actual052-split-scale-diagnostic-only')
 import window_overlay as W
 m.update(window={'start':W.START,'cutoff':W.CUT},authority=W.AUTHORITY,authority_sha256=W.AUTHORITY['sha256'],cutoff_epoch=W.CUT)
 pm=dict(schema='deltalog.real-qwen-service-bridge-source/v023',root=ROOT+'/plugin',default_enabled=False,mode='diagnostic-bridge-only',prepared_only=True,window=m['window'],files={k.removeprefix('plugin/'):ref(ROOT+'/'+k,bb)for k,bb in files.items()if k.startswith('plugin/')})
 for k in('composite_api_ref',):pm[k]=t[k]
 pb=data(pm);(P/'plugin/SOURCE_TEMPLATE.json').write_bytes(pb);files['plugin/SOURCE_TEMPLATE.json']=pb;m['plugin_template_ref']=ref(ROOT+'/plugin/SOURCE_TEMPLATE.json',pb)
 m['pending']=['actual052 same-source CPU+Meta and numeric160 full351sidecar/328records/13controls/release','actual053 sameimage no-device source and parser/IPC preflight','actual TP4x48 loaded-target/source/metadata/10token two-request and selected3layers independent FP32 tensor smoke','source-aware production receiver/PF/ACC actual qualification; no future result']
 m['mandatory_unfinished_gates']=m['pending'];m['scope']='diagnostic-model-smoke-after-actual052-split-scale160-only'
 m['dependencies']=[*m['dependencies'],W.AUTHORITY,tr,*t['files'].values(),t['split_kernel_source_ref']]
 m['files']={k:ref(ROOT+'/'+k,bb)for k,bb in sorted(files.items())}
 (P/'SOURCE_TEMPLATE.json').write_bytes(data(m))
 if v.seal:
  files['SOURCE_TEMPLATE.json']=data(m)
  payload=dict(schema='deltalog.split-scale-model-byte-exact/v053',root=ROOT,template=ref(ROOT+'/SOURCE_TEMPLATE.json',data(m)),source_only=True,NPU=False,files=[dict(relative_path=k,ref=ref(ROOT+'/'+k,bb),text=bb.decode('utf8'))for k,bb in sorted(files.items())])
  (P/'BYTE_EXACT_DELIVERY.json').write_bytes(data(payload))
 print(json.dumps(dict(template=ref(ROOT+'/SOURCE_TEMPLATE.json',data(m)),prepared_only=True,NPU=False)))
if __name__=='__main__':main()
