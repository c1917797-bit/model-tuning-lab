"""Typed106 call boundary; no shared unverified public module namespace."""
import contextlib,hashlib,importlib.util,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
START,CUT=1792134133,1792220533
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary immutable input')
 h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 need((n,h.hexdigest())==(r['bytes'],r['sha256']),'exact bytes/SHA');return p
def obj(r):return json.loads(checked(r).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def original025_ref3(r):
 need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'exact original025 Ref2 or Ref3 ABI')
 current=ref(r['path']);need(r['sha256']==current['sha256']and('bytes'not in r or r['bytes']==current['bytes']),'original025 reference bytes/SHA unchanged')
 return current
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def source(sr,*,pair=False):
 m=obj(sr);need(m['schema']=='deltalog.actual-production-pair-source/v122'and m['root']==str(P)and m['default_enabled']is False and m['prepared_only']is False,'actual bound122 source')
 template=obj(m['prepared_template']);need(template['root']==m['root']and template['files']==m['files']and template['prepared_only']is True,'exact bound122 template and full file closure')
 need(m['window']==dict(start=START,cutoff=CUT)and START<=time.time()<CUT,'fixed NEW24H');checked(m['authority_ref'])
 for name,r in m['files'].items():need(r['path']==str(P/name),'own file namespace');checked(r)
 if pair:need(m['stage']=='pair'and m['health_owner_ref']is not None,'actual production health/equivalence predecessor required')
 return m
@contextlib.contextmanager
def context(m):
 pm=obj(m['production_source_ref']);need(pm.get('schema')=='deltalog.production-source/v106'and pm.get('prepared_only')is False,'actual106 bound source, not prepared future source')
 pins=m['production_template'];need(pm['prepared_template']==pins['ref']and pm['files']==pins['files'],'exact106R3 runtime source')
 names=('qualification106','common106','live106','snapshot_owner106');saved={n:sys.modules.get(n)for n in names};path=list(sys.path);loaded={}
 try:
  sys.path.insert(0,pm['root'])
  for n in names:
   r=pm['files'][n+'.py'];s=importlib.util.spec_from_file_location(n,checked(r));v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);loaded[n]=v
  yield loaded,pm
 finally:
  sys.path[:]=path
  for n,v in saved.items():
   if v is None:sys.modules.pop(n,None)
   else:sys.modules[n]=v
def qualify_production(m):
 with context(m)as(v,pm):q=v['qualification106'].qualify(m['production_qualification_ref'],m['production_source_ref'])
 pm,model,o,p,b=component_inputs(m);plan=obj(p['plan']);smoke=obj(plan['smoke']);consumer=obj(smoke['independent_consumer']);r=b['files']['preregister.py']
 s=importlib.util.spec_from_file_location('_122_actual088_preregister',checked(r));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 need(g.admit_smoke(smoke,pm['component_source_ref'],consumer)['diagnostic160_admitted']is True,'actual source-bound16 predecessor of160, not just Meta')
 return q
def health_gate(owner,report,sr,production_sr,qref):
 need(owner['schema']=='deltalog.production-health-owned/v122'and owner['source']==sr and owner['primary']is None and owner['secondary']==[]and owner['released']is True,'actual successful health owner/release')
 need(report['schema']=='deltalog.production-health-equivalence/v122'and report['source']==sr and report['production_source']==production_sr and report['production_qualification']==qref and report['NPU']is True,'actual same-source NPU production-health evidence')
 need(report['all_model216_decode_bitwise']is True and report['all320_flush_bitwise']is True and report['valid_health']['all_finite']is True and report['dead_nan_pass']is True and report['invalid_live_sticky']is True and report['invalid_output_sticky']is True,'full production finite/equivalence gate, not Meta/canary')
 rows=report['rows'];need(len(rows)==320 and {(r['batch'],r['step'])for r in rows}=={(b,s)for b in(1,16)for s in range(160)}and all(r['flush_bitwise']is True for r in rows),'all actual320 flush rows')
 mr=report['model_rows'];need(len(mr)==216 and len({r['raw']['path']for r in mr})==216 and all(r['decode_bitwise']is True for r in mr),'all actual216 independent-model decode records, not component-only samples')
 need(report['health_scope']=='observed decode outputs and materialized logical states; not all cache/aux cells','honest health coverage')
 need(report['invalid_health']['all_finite']is False and set(report['output_negative_health'])=={'NaN','Inf'}and all(v['all_finite']is False and v['outside_timing']is True for v in report['output_negative_health'].values()),'actual separately executed sticky NaN and Inf device controls')
 need(report['qualified']is False and report['performance']is False,'health gate is predecessor, not performance')
def qualify(sr,*,pair=True):
 m=source(sr,pair=pair);q=qualify_production(m)
 if pair:
  o=obj(m['health_owner_ref']);validation=obj(o['source']);need(validation['files']==m['files']and validation['production_source_ref']==m['production_source_ref']and validation['stage']=='validation','same122 runtime validation source')
  report=obj(o['numeric']);health_gate(o,report,o['source'],m['production_source_ref'],m['production_qualification_ref']);health_input_join(m,report)
  cleanup=obj(o['cleanup']);need(cleanup['stopped']is True and cleanup['retained']is True and cleanup['errors']==[],'actual original health owner cleanup receipt')
 return m,q
def readset(m):
 with context(m)as(v,pm):refs=v['qualification106'].readset(m['production_source_ref'])
 model=obj(pm['model_source_ref']);refs+=model['dependencies']
 _,_,co,producer,_=component_inputs(m);plan=obj(producer['plan']);smoke=obj(plan['smoke']);refs +=[plan['smoke'],smoke['independent_consumer'],smoke['result']]
 refs +=[m['prepared_template'],m['production_source_ref'],m['production_qualification_ref'],m['authority_ref'],m['production_template']['ref'],*m['files'].values(),*m['dependencies']]
 if m.get('health_owner_ref'):
  o=obj(m['health_owner_ref']);refs +=[m['health_owner_ref'],o['source'],o['numeric'],o['cleanup']]
 return list({r['path']:r for r in refs}.values())
def component_inputs(m):
 pm=obj(m['production_source_ref']);model=obj(pm['model_source_ref']);o=obj(pm['component_owner_ref']);p=obj(o['result']);bridge=obj(model['bridge024_source_ref'])
 need(p['steps']==160 and p['primary']is None and len(p['actual_mixed_sidecar_records'])==320,'actual complete160 input ledger')
 return pm,model,o,p,bridge
def model_inputs(m):
 pm=obj(m['production_source_ref']);mo=obj(pm['model_owner_ref']);c=obj(mo['independent_smoke_consumer']);t=obj(c['selected_tensor_ref'])
 need(t['source']==pm['model_source_ref']and t['modified_decode_arithmetic_pass']is True and len(t['records'])==240,'actual240 independent model tensor evidence')
 rows=[r for r in t['records']if r['identity']['kind']=='decode'];need(len(rows)==216,'all216 selected model decode checkpoints')
 return rows
def health_input_join(m,report):
 pm,model,o,p,bridge=component_inputs(m);want=[r for r in p['records']if r['kind']=='mixed']
 need([(r['batch'],r['step'],r['raw'])for r in report['rows']]==[(r['batch'],r['step'],r['raw'])for r in want],'ordered exact320 retained raw input closure')
 rows=model_inputs(m);need([(r['identity'],r['raw'])for r in report['model_rows']]==[(r['identity'],r['independent']['actual_sidecar_ref'])for r in rows],'ordered exact216 actual independent-model sidecar closure')
 need(report['library']==pm['library_ref']and report['mapped']and report['actual_component_source']==pm['component_source_ref']and report['actual_component_owner']==pm['component_owner_ref'],'same actual051 mapped DSO/component')
def bootstrap_cann(m):
 import importlib.machinery
 pm=obj(m['production_source_ref']);model=obj(pm['model_source_ref']);refs=[r for r in model['dependencies']if Path(r['path']).name=='cann_python.py'];need(len(refs)==1,'one actual101 source-pinned CANN helper')
 r=refs[0];s=importlib.util.spec_from_file_location('_122_actual011_cann',checked(r));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
 c.cached();c.file_identity(c.ENV,c.ENV_BYTES,c.ENV_SHA);direct=c.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[c.ROOT]));need(Path(c.ROOT).is_dir(),'actual fixed CANN root')
 if c.ROOT not in sys.path:sys.path.insert(0,c.ROOT)
 need(c.spec_identity(importlib.util.find_spec('acl'))==direct,'current interpreter same exact CANN namespace, not PYTHONPATH-only')
 return c.ROOT
def smoke_gate(owner,report,sr):
 need(owner['schema']=='deltalog.production-owned-single-pair/v122'and owner['source']==sr and owner['primary']is None and owner['secondary']==[]and owner['source_before']==owner['source_after']and len(owner['arms'])==2,'actual complete same-source smoke pair')
 need(report['schema']=='deltalog.actual-single-pair-independent/v122'and report['source']==sr and report['smoke_pair']is True and report['acceptance']is False and report['formal_three_rounds']is False,'actual independently consumed small pair, not formal result')
