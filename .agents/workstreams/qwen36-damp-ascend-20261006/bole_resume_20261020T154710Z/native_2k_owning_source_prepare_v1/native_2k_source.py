"""Exact native2048/1 metadata-source validation; no device/controller."""
import ast,hashlib,importlib.util,json,time
from pathlib import Path
SCOPE=dict(kind='native-prefill-geometry-only',input_tokens=2048,output_tokens=1,request_count=1,concurrency=1,
 physical_NPUs=[4,5,6,7],common_environment={'HCCL_DETERMINISTIC':'true'},phase_seconds=3600,cleanup_seconds=180)
AUTH_SCHEMA='native2k.MAIN-reviewed-metadata-execution-authority/v1'
REVIEW_SCHEMA='native2k.MAIN-metadata-execution-review/v1'
TEST_FILES=('test_native_2k.py',)
def need(v,s):
 if not v:raise ValueError(s)
def review_value(m):
 return dict(source_root=m['root'],output_root=m['output_root'],files=m['files'],renderer_refs=m['native_2k_renderer_refs'],
  parent_template=m['native_2k_parent_template'],input_processor_runtime_ref=m['native_2k_input_processor_ref'],
  completion_serving_ref=m['native_2k_completion_serving_ref'],protocol=m['native_2k_observation'])
def execution_window(C,m,*,clock=True,require_phase=False):
 ref=m.get('native_2k_authority_ref');need(ref is not None,'new native2k authority unbound; no old131/current-window inference')
 a=C.obj(ref)
 need(type(a)is dict and set(a)=={'schema','approved','start_epoch','cutoff_epoch','scope','MAIN_review_ref'}and
  a['schema']==AUTH_SCHEMA and a['approved']is True and a['scope']==SCOPE and
  type(a['start_epoch'])is type(a['cutoff_epoch'])is int and a['cutoff_epoch']-a['start_epoch']>=3780,
  'distinct approved finite native2k window and unchanged3600+180')
 review=C.obj(a['MAIN_review_ref'])
 need(review.get('approved')is True and review.get('schema')==REVIEW_SCHEMA and review.get('scope')==SCOPE and
  review.get('source_review')==review_value(m),'exact real MAIN source/file/runtime/renderer review, not caller PASS')
 if clock:
  now=time.time();need(a['start_epoch']<=now<a['cutoff_epoch']and(not require_phase or now+3780<=a['cutoff_epoch']),'active finite new native2k window; no renewal')
 return a
def _renderer(C,m):
 refs=m['native_2k_renderer_refs'];r=refs['prepare_native_2k.py']
 # Review and every whole producer/input Ref are checked BEFORE executable import.
 execution_window(C,m,clock=False)
 for v in refs.values():C.checked(v)
 spec=importlib.util.spec_from_file_location('_native2k_reviewed_renderer',r['path'])
 module=importlib.util.module_from_spec(spec);exec(compile(C.checked(r).read_bytes(),r['path'],'exec'),module.__dict__)
 return module
def expected(C,m):
 renderer=_renderer(C,m)
 return renderer.render(authority_ref=m['native_2k_authority_ref'],permit_materialized=True,io=C)
def enumerate_tests(m):
 import sourceio as C
 out=[]
 for name in TEST_FILES:
  for cls in ast.parse(C.checked(m['files'][name]).read_bytes()).body:
   if isinstance(cls,ast.ClassDef):
    out.extend(name+':'+cls.name+'.'+x.name for x in cls.body if isinstance(x,ast.FunctionDef)and x.name.startswith('test_'))
 need(len(out)==len(set(out))==9,'nine exact source-only native2048 controls, not old20')
 return sorted(out)
def source(C,sr,m,*,clock=True):
 need(C.ref(C.__file__)==m['files']['contract090.py']and C.ref(__file__)==m['files']['native_2k_source.py']and
  str(Path(C.__file__).resolve().parent)==m['root'],'actual deployed source gate/helper identity, not cached foreign owner')
 need(sr['path']==str(Path(m['root'])/'SOURCE_BOUND.json')and m['prepared_only']is False and m['default_enabled']is False,'actual bound defaultOFF source identity')
 need(m['performance_arm']=='native_ar'and m['native_speculative_config']is None and
  m['native_2k_observation']['input_tokens']==2048 and m['native_2k_observation']['output_tokens']==1 and
  m['service_required_sameimage_software_cases']==9,'explicit native metadata scope only')
 a=execution_window(C,m,clock=clock)
 template_ref=m['prepared_template'];template=C.obj(template_ref)
 need(template_ref['path']==str(Path(m['root'])/'SOURCE_TEMPLATE.json')and template['prepared_only']is True,'exact complete prepared-to-bound transition')
 want=expected(C,m);need(template==want['manifest'],'whole native2k exact renderer/inverse expected template')
 bound=dict(template,prepared_only=False,prepared_template=template_ref)
 need(m==bound,'only prepared/bound transition; unknown source fields refused')
 for r in m['files'].values():C.checked(r)
 for r in m['dependencies']:C.checked(r)
 need(m['authority_ref']==m['native_2k_authority_ref']and
  m['native_2k_input_processor_ref']['sha256']=='c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15','current authority and actual same-image assignment source')
 C.text_only_config(None,m)
 return a
def readset(C,sr,m):
 source(C,sr,m,clock=True)
 refs=[sr,m['prepared_template'],*m['files'].values(),*m['dependencies']]
 unique={}
 for r in refs:
  need(r['path']not in unique or unique[r['path']]==r,'unique whole native2k dependency identity');unique[r['path']]=r;C.checked(r)
 return list(unique.values())
def validate(C,sr):
 m=C.obj(sr);source(C,sr,m,clock=True)
 return dict(schema='bole.performance-successor-source-validation/v1',source=sr,source_validated=True,
  metadata_only_native2k=True,tests=enumerate_tests(m),readset=readset(C,sr,m),NPU=False,
  numerical_qualified=False,formal_performance=False,task_accuracy=False)
def dependency_contract(m):
 for key,name in(('performance_streaming_client','native_2k_client.py'),('performance_timing_donor','benchmark_shared_prefix.py')):
  need(m[key]==m['files'][name]and m[key]in m['dependencies'],'bound actual native2k runtime client/donor '+key)
 return True

def bind_template(C,tr,components):
 template=C.obj(tr);need(tr['path']==str(Path(template['root'])/'SOURCE_TEMPLATE.json')and template['prepared_only']is True,'real new reviewed template only')
 execution_window(C,template,clock=True,require_phase=True)
 want=expected(C,template);need(template==want['manifest']and components==template['component_refs'],'complete exact metadata template; historical components not2k qualification')
 root=Path(template['root']);need(not(root/'SOURCE_BOUND.json').exists()and not Path(template['output_root']).exists(),'new source/output; never overwrite')
 bound=dict(template,prepared_only=False,prepared_template=tr)
 sr=C.write(root/'SOURCE_BOUND.json',bound);readset(C,sr,bound);return sr
