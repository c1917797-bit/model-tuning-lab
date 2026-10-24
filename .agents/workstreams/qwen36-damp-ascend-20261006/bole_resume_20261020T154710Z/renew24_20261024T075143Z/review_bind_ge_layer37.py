"""MAIN exact GE64 source review and original bind, no device launch."""
import hashlib,json,sys,runpy,types
from pathlib import Path
D=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/good_enough_layer37_renew_v2_20261024")
OUT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261024T075143Z")
T={'path':str(D/'prepared-source/SOURCE_TEMPLATE.json'),'bytes':39049,'sha256':'38230f9dd07e03ce324191ab0130b6a56a7a73472efd8d571136b8230bb2d946'}
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def publish(n,v):
 p=OUT/n;raw=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
 with p.open('xb')as f:f.write(raw);f.flush();import os;os.fsync(f.fileno())
 return ref(p)
expected={'prepare_successor.py':(13345,'af3be04ae2f3eedff8e94485a46a468ee0212dc819c78c4b523d36bd770990a0'),'successor_bindings.py':(4378,'a50c7aecc694ff5fbbac926cffbff814830d6a0cf92066277f07a80967024bb8')}
for n,(size,sha)in expected.items():
 r=ref(D/n);need((r['bytes'],r['sha256'])==(size,sha),'exact independently read GE source')
ns={'__file__':str(D/'prepare_successor.py'),'__name__':'_MAIN_GE_source_audit'}
exec(compile((D/'prepare_successor.py').read_bytes(),str(D/'prepare_successor.py'),'exec'),ns)
m=ns['validate_template'](T);b=ns['render']();ns['inverse'](b)
need(len(m['files'])==64 and m['software_cases']==m['software_tests']==96,'whole64 and original96')
need(m['window']==dict(start=1792828303,cutoff=1792914703),'current fixed window')
need(not any(Path(p).exists()for p in m['outputs'].values()),'unique actual GE output roots')
review=dict(schema='ge.MAIN-layer37-successor-source-review/v1',decision='approve',prepared_template_ref=T,source_file_refs=m['files'],parent_source_ref=m['parent_source_ref'],migration_builder_ref=m['migration_builder_ref'],preparation_window_ref=m['preparation_window_ref'],resources=m['resources'],math_thresholds_unchanged=True,original96_tests_retained=True)
rr=publish('GE_LAYER37_MAIN_SOURCE_REVIEW.json',review)
a=dict(schema='ge.MAIN-reviewed-layer37-successor-authority/v1',approved=True,preparation_window_ref=m['preparation_window_ref'],prepared_template_ref=T,source_root=m['root'],outputs=m['outputs'],physical=[6],protected=[0,1,2,3],start_epoch=1792828303,cutoff_epoch=1792914703,resources=m['resources'],MAIN_review_ref=rr)
ar=publish('GE_LAYER37_AUTHORITY.json',a)
bound=ns['bind'](T,ar)
result=dict(schema='MAIN.GE-layer37-source-binding/v1',review_ref=rr,authority_ref=ar,**bound,full64_source=True,original96_cases_retained=True,NPU=False)
publish('GE_LAYER37_SOURCE_BIND_RESULT.json',result)
print(json.dumps(result,sort_keys=True))
