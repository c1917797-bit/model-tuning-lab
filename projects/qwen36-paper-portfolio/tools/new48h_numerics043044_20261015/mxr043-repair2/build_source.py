"""Default-OFF one immutable template -> actual042-bound diagnostic model source."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent
def obj(r):
 b=Path(r['path']).read_bytes()
 if(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('exact template/file')
 return json.loads(b)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');p.add_argument('--actual042-owner-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 t=obj(json.loads(a.template_ref));need=t['actual042_owner_ref']is None and t['root']==str(P)and t['default_enabled']is False
 if not need:raise ValueError('prepared source only, exact deployment root')
 for r in t['files'].values():
  b=Path(r['path']).read_bytes()
  if(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('reviewed model source bytes')
 s=importlib.util.spec_from_file_location('_043_admit',P/'admit042.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
 actual=json.loads(a.actual042_owner_ref);qualified=A.gate(actual);original=A.obj(A.SOURCE042)
 for name in ('refine.py','boundary_oracle.py'):
  if any(t['files'][name][key]!=original['files'][name][key]for key in('bytes','sha256')):raise ValueError('same042 refined math and independent oracle required')
 t['actual042_owner_ref']=actual;t['actual042_admission']=qualified;t['dependencies'].extend(qualified['readset']);t['status']='ACTUAL042_BOUND_MODEL_DIAGNOSTIC_ATTEMPT_ONLY';t['prepared_only']=False
 b=(json.dumps(t,sort_keys=True,indent=2)+'\n').encode();target=P/'SOURCE_MANIFEST.json'
 with target.open('xb')as f:f.write(b)
 print(json.dumps(dict(path=str(target),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),NPU=False,model_ready=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
