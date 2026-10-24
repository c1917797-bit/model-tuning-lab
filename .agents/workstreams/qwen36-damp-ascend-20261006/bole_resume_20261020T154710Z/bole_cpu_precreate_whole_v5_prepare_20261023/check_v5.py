"""Bounded source-only V5 groups; never materializes source or authority."""
import argparse,ast,hashlib,importlib.util,json,resource,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
WS=HERE.parent
def need(x,label):
 if not x:raise ValueError(label)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--group',choices=('short','formal','format'));a=p.parse_args()
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
 resource.setrlimit(resource.RLIMIT_CPU,(150,150))
 if a.group is None:print(json.dumps(dict(enabled=False,NPU=False)));return
 if a.group=='format':
  for q in HERE.glob('*.py'):
   raw=q.read_bytes();compile(raw,str(q),'exec')
   need(raw.endswith(b'\n')and not raw.endswith(b'\n\n'),'one EOF newline')
   need(all(not line.endswith((b' ',b'\t'))for line in raw.splitlines()),'no trailing whitespace')
  print(json.dumps(dict(group=a.group,PASS=True,NPU=False)));return
 if a.group=='short':
  S=load(HERE/'runtime_lossless_imports.py','_V5short')
  b=S.render();S.inverse(b)
  need(b['manifest']['qualification_authority_ref']is None,'no fabricated authority')
  need(b['manifest']['cpu_precreate_intent']['role']=='cpu-preflight','typed CPU role')
  need(b['manifest']['fastpath_numeric_qualification']['input_tokens']==32768,'actual32K')
  need(b['manifest']['fastpath_numeric_qualification']['output_tokens']==8,'actualshort8')
  need(b['manifest']['root']==str(HERE/'prepared-source-short8-v5'),'distinct short V5 identity')
  old=json.loads((WS/'bole_deviceless_cpu_release_prepare_v4_20261023/prepared-source-short8-v4/SOURCE_BOUND.json').read_bytes())
  allowed={'contract090.py','qualification_source_validate.py','qualification_source_producer.py','runtime_lossless_imports.py','host_service.py','owned_create.py','owned_substrate.py','cpu_precreate_policy.py','adapt_cpu_precreate.py'}
  need(set(b['files'])==set(old['files'])|{'cpu_precreate_policy.py','adapt_cpu_precreate.py'},'exact two new source helpers')
  unchanged=[]
  for n,r in old['files'].items():
   if n not in allowed:
    raw=Path(r['path']).read_bytes();need(len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256'],'old fullRef '+n);need(raw==b['files'][n],'unchanged byte '+n);unchanged.append(n)
  F=load(HERE/'formal_runtime.py','formal_composer')
  P=load(HERE/'short8_source_pin.py','_V5pin')
  D=F.module(F.DELTA,'_original_pin_delta')
  om,of=D.parent();P.unchanged(of,b['files'],om,b['manifest'])
  print(json.dumps(dict(group=a.group,PASS=True,files=len(b['files']),unchanged_vs_V4=len(unchanged),full_inverse=True,original_math_unchanged=True,authority=None,NPU=False)))
 else:
  F=load(HERE/'formal_runtime.py','formal_composer')
  b=F.render(HERE/'formal-source-set-v5',arm='bole',trial=0);F.inverse(b)
  need(b['manifest']['cpu_precreate_intent']['role']=='cpu-preflight','formal typed CPU role')
  need(b['files']['cpu_precreate_policy.py']==(HERE/'cpu_precreate_policy.py').read_bytes(),'same source-owned helper')
  need(b['files']['adapt_cpu_precreate.py']==(HERE/'adapt_cpu_precreate.py').read_bytes(),'same exact adapter')
  old=F._F.render(HERE/'formal-source-set-v5',arm='bole',trial=0)
  allow={'formal_composer.py','performance_prerequisite.py','short8_source_pin.py','cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py','owned_substrate.py','host_service.py','owned_create.py'}
  need(set(b['files'])==set(old['files'])|{'short8_source_pin.py','cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py'},'exact formal helper additions')
  for n in set(old['files'])-allow:need(b['files'][n]==old['files'][n],'unchanged formal byte '+n)
  sys.modules['formal_composer']=F
  C=load(WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/check_whole.py','_V5formal46')
  result=C.check()
  print(json.dumps(dict(group=a.group,PASS=True,files=len(b['files']),full_inverse=True,formal46=result,math_resource_unchanged=True,NPU=False),default=str))
if __name__=='__main__':main()
