"""Thin explicit022 component API boundary; NEVER claims model admission."""
import hashlib,importlib.util,json,time
from pathlib import Path
from . import contract as C
ROOT=Path(__file__).resolve().parent.parent
def need(v,m):
 if not v:raise RuntimeError(m)
def ref(p):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary immutable Ref path');b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact Ref3');return json.loads(Path(r['path']).read_bytes())
def source(sr):
 m=obj(sr);need(m['schema']=='deltalog.production-screen-source/v037'and m['root']==str(ROOT)and m['default_enabled']is False and m['mode']=='performance-screen-only'and m['prepared_only']is False,'new independently frozen runtime screen source')
 need(m['window']==dict(start=1791962297,cutoff=1792135097)and 1791962297<=time.time()<1792135097,'unchanged fixed clock')
 for r in m['files'].values():need(ref(r['path'])==r,'whole actual023 closure')
 return m
def certificate(c,cr,library,schema):
 need(c['schema']=='deltalog.composite-component-qualification/v022'and c['source']==cr,'real022 typed component scope')
 for key in('strict324','original_numeric325','strict325_composed','old002_failure_unchanged'):
  need(c[key]is True,'complete strict composite component '+key)
 need(type(c['strict137_join'])is dict and c['strict137_join']['actual_tensor_join']is True,'actual guarded/raw bytejoin, not a fabricated Boolean')
 need(c['original019_strict_pass']is False,'old019 failure remains unchanged')
 for key in('model_ready','performance_ready','task_ready','graph','PDC'):need(c[key]is False,'component cannot authorize '+key)
 need(c['library']==library and c['operator_schema']==schema,'same actual production library/schema')
 return c
def consume(sr,composite_source_ref):
 m=source(sr);need(composite_source_ref==m['composite_source_ref'],'source-bound actual022 composite, no borrowed certificate')
 api=m['composite_api_ref'];need(ref(api['path'])==api,'exact reviewed022 API source')
 spec=importlib.util.spec_from_file_location('_deltalog023_actual022_admission',api['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 need(callable(getattr(module,'admit_receipt',None)),'actual022 lightweight owned CPU receipt API required; never run raw consumer in workers')
 c=certificate(module.admit_receipt(composite_source_ref,m['composite_cpu_owner_ref']),composite_source_ref,m['library_ref'],m['operator_schema'])
 need(c['certificate_ref']==m['composite_certificate_ref']and c['CPU_owner']==m['composite_cpu_owner_ref'],'frozen actual022 owned certificate and owner receipt')
 saved=obj(c['certificate_ref']);need(all(saved[k]==c[k]for k in saved),'light admission preserves every actual stored certificate field')
 component=obj(c['component_source']);need(component['libraries']=={'key_projection':m['library_ref']}and component['build_ref']==m['production_build_ref'],'component binds separate actual production build')
 build=obj(m['production_build_ref']);need(build['schema']=='deltalog-key-projection-actual-build/v010'and build['primary']is None and build['source_manifest']==component['kernel_source_ref'],'actual unchanged B010 build source')
 need({x['arm']:x['library']for x in build['artifacts']}=={'key_projection':m['library_ref']},'actual B010 artifact inventory')
 need(ref(m['library_ref']['path'])==m['library_ref']and m['library_ref']['sha256']==C.LIBRARY_SHA,'exact original production DSO; debug is not model compute')
 ad=dict(schema='deltalog.actual-component-to-model-bridge/v023',runtime_source=sr,composite_source=composite_source_ref,composite_api=api,component_source=c['component_source'],component_only=True,model_ready=False,performance_ready=False,task_ready=False,graph=False,PDC=False)
 return ad,m
