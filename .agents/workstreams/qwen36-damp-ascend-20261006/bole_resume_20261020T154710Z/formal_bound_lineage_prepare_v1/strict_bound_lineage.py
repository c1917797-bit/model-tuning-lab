"""Prepared-six -> future bound-owner lineage. No freeze, authority creation or dispatch."""
import argparse,ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from contextlib import contextmanager
HERE=Path(__file__).resolve().parent
ASSETS=[
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/performance_followup_delta.py",
    "bytes": 13502,
    "sha256": "44efc35427a39e769fea98835f3f060415c1448d4c72c024e6aeeb8ad854c2e2"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/paired_contract.py",
    "bytes": 3230,
    "sha256": "bffc44f386b42a1262ec9109a28fb7cf607c0ae7f0c75d7032d443941448468c"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/validated_performance_policy.py",
    "bytes": 3175,
    "sha256": "3a3189f5df52ffc58a282a4cf4c1a63cd23468e76e834c37842d3303cf9b7e1f"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/paired_receipt_consumer.py",
    "bytes": 6349,
    "sha256": "d9652156fed1e01508700131db570d673e0b7862971c48534bde81537996a0a6"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/followup_binding_delta.py",
    "bytes": 4459,
    "sha256": "729f40c4b4e86443d364ed02db34046946cb383c4ee4265c25d9e38672130895"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/followup_source_validate.py",
    "bytes": 7021,
    "sha256": "6c4f010c543eca6bf42c29c97d88d7039019f9dcef68099bb8ea3690115aaae7"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/performance_followup_prepare_20261022T203100Z/paired_prepare.py",
    "bytes": 8912,
    "sha256": "31c5b9119108b99e949b37567a1bae46225befe0bf9fff0139e919e54132b74b"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/render_strict_timing.py",
    "bytes": 8221,
    "sha256": "3ae1379a5a60c0bf7c5dc0615b8661a92421ede86a5093d92ab2edc6e8262e0a"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/strict_token_timing.py",
    "bytes": 5679,
    "sha256": "c84ac3234d01473acd9afebf2e15865b201e344fb39776a442fc68e37186225b"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/three_trial_sources.py",
    "bytes": 6006,
    "sha256": "dcca5dda8a852ce0e92acb4f61d796fbf0afcd3565659a1fd76fac69823e14cd"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/checked_pair_math.py",
    "bytes": 5927,
    "sha256": "5bcca18a36a8f736d7871fd30e5aba2f22d62d2cd6884d2624e627d78104030a"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fixed1024_sse_timing_client_v1/fixed1024_client.py",
    "bytes": 6215,
    "sha256": "0639cbe6e00a4c54eab3f9afe4886b47fbcc10737756b4fcbe46e57ae389dbf8"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fixed1024_sse_timing_client_v1/independent_reader.py",
    "bytes": 12992,
    "sha256": "9ffba3df8c2417e2249f368ebe7573f093e6a45f62e5bcefc1186259f08f273c"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fixed1024_sse_timing_client_v1/evidence.py",
    "bytes": 1679,
    "sha256": "9fc7ec4a4737c1edd386b6e7926367d1a12b2b35ed237faad1005a972caa7ab4"
  },
  {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/formal_pair_ready_prepare_v1/three-trial-proposal-v1/THREE_TRIAL_SOURCES.json",
    "bytes": 3456,
    "sha256": "387be3568be42ef0375968603e316db52af7b1f04c5a687afc75963646db98ba"
  }
]
ASSET_MAP={Path(r['path']).name:r for r in ASSETS}
ORIGINAL_FSV=ASSET_MAP['followup_source_validate.py']
PREPARED_SET=ASSET_MAP['THREE_TRIAL_SOURCES.json']
ORDER=('performance_followup_delta','paired_contract','validated_performance_policy','paired_receipt_consumer',
       'followup_binding_delta','followup_source_validate','paired_prepare','render_strict_timing','three_trial_sources')
SOURCE_SCHEMA='bole.strict-six-source-owner-lineage/v1'
BOUND_SET_SCHEMA='bole.actual-exact-six-bound-source-lineage/v1'
def need(v,s):
 if not v:raise ValueError(s)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def refbytes(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def ref(p):return refbytes(p,Path(p).read_bytes())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and 0<=r['bytes']<=128*2**20,'complete bounded Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(z.is_symlink()for z in(p,*p.parents)),'ordinary exact whole-source Ref')
 a=p.stat();b=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)and refbytes(p,b)==r,'stable actual whole-source Ref')
 return b
def obj(r):return json.loads(checked(r))
def once(t,a,b):
 need(t.count(a)==1,'one complete original source seam');return t.replace(a,b,1)
@contextmanager
def renderer_modules():
 # Fixed, reviewed preparation modules only. Restore names even on failure;
 # never accept a caller module or an already-imported lookalike.
 for r in ASSETS:checked(r)
 sentinel=object();old={n:sys.modules.get(n,sentinel)for n in ORDER};oldpath=list(sys.path)
 loaded={}
 try:
  for name in ORDER:
   r=ASSET_MAP[name+'.py'];p=Path(r['path']);sys.path.insert(0,str(p.parent))
   spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec)
   sys.modules[name]=m;exec(compile(checked(r),str(p),'exec'),m.__dict__);loaded[name]=m
  yield loaded
 finally:
  sys.path[:]=oldpath
  for n,v in old.items():
   if v is sentinel:sys.modules.pop(n,None)
   else:sys.modules[n]=v
STRICT_REVIEW_FUNCTION="def strict_source_review(m):\n    # Source authority is separate from source shape. No self-supplied helper\n    # or generated template is MAIN review evidence.\n    a=execution_window(m,clock=False,require_phase=False)\n    review=json.loads(read_ref(a['MAIN_review_ref']))\n    v=review.get('strict_source_bindings')\n    need(type(v)is dict and set(v)=={'schema','prepared_source_set_ref','renderer_dependencies','sources'} and\n         v['schema']=='bole.MAIN-exact-six-strict-source-review/v1' and\n         v['prepared_source_set_ref']==m['strict_prepared_source_set_ref'] and\n         v['renderer_dependencies']==m['strict_renderer_dependencies'] and\n         type(v['sources'])is list and len(v['sources'])==6,\n         'actual MAIN exact-six strict source review is unbound')\n    seen=set();match=[]\n    for row in v['sources']:\n        need(type(row)is dict and set(row)=={'trial_index','arm','source_root','output_root','files','prepared_source_ref'} and\n             type(row['trial_index'])is int and row['trial_index']in range(3) and row['arm']in('native_ar','bole') and\n             (row['trial_index'],row['arm'])not in seen,'exact six unique MAIN-reviewed trial/arm source bindings')\n        seen.add((row['trial_index'],row['arm']))\n        if row['trial_index']==m['strict_trial_index'] and row['arm']==m['performance_arm']:\n            match.append(row)\n    need(len(match)==1 and match[0]==dict(trial_index=m['strict_trial_index'],arm=m['performance_arm'],\n         source_root=m['root'],output_root=m['output_root'],files=m['files'],\n         prepared_source_ref=m['strict_prepared_source_ref']),\n         'MAIN review pins actual source/output roots, all file bytes and prepared trial lineage')\n    return True"
def validator_delta(raw):
 before="""    expected=P.render_pair(base_root=Path(m['followup_preparation_root']),permit_materialized=True,
                           authority_ref=m['followup_authority_ref'])['arms'][m['performance_arm']]
    need(template==expected['manifest'],'complete exact source renderer/inverse manifest')
    P.inverse_files(expected)"""
 after="""    strict_program=read_ref(m['files']['strict_bound_lineage.py'])
    strict_source_review(m)
    import importlib.util
    strict_spec=importlib.util.spec_from_file_location('_actual_reviewed_strict_lineage',m['files']['strict_bound_lineage.py']['path'])
    STRICT=importlib.util.module_from_spec(strict_spec)
    exec(compile(strict_program,m['files']['strict_bound_lineage.py']['path'],'exec'),STRICT.__dict__)
    need(C.ref(STRICT.__file__)==m['files']['strict_bound_lineage.py'],'actual complete source-owned MAIN-reviewed strict lineage helper')
    expected=STRICT.expected(m)
    need(template==expected['manifest'],'complete exact strict source renderer/inverse manifest')
    STRICT.inverse_files(expected)"""
 text=once(raw.decode(),before,after)
 text=once(text,'def validate(sr):',STRICT_REVIEW_FUNCTION+'\n\ndef validate(sr):')
 inverse=once(text,after,before)
 inverse=once(inverse,STRICT_REVIEW_FUNCTION+'\n\n','')
 need(inverse.encode()==raw,'complete original validator inverse')
 # In particular preserve the unconditional independent numerical gate.
 tree=ast.parse(raw);new=ast.parse(text)
 for name in ('require_fastpath_admission','execution_window','authority_shape'):
  a=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name)
  b=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name==name)
  need(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'complete original admission/authority body unchanged '+name)
 return text.encode()
def rebind(m,files):
 root=Path(m['root']);old={json.dumps(r,sort_keys=True):n for n,r in m['files'].items()}
 current={n:refbytes(root/n,b)for n,b in files.items()}
 def visit(v):
  if type(v)is dict and set(v)=={'path','bytes','sha256'}:
   n=old.get(json.dumps(v,sort_keys=True))
   if n is not None:return current[n]
  if type(v)is dict:return {k:visit(x)for k,x in v.items()}
  if type(v)is list:return [visit(x)for x in v]
  return v
 result=visit(m);result['files']=current;return result
def render_pair(base,trial_index,*,authority_ref=None):
 base=Path(base)
 need(base.is_absolute()and '..'not in base.parts and type(trial_index)is int and trial_index in range(3),'exact prospective trial root/index')
 with renderer_modules()as mods:
  source_set=mods['three_trial_sources'].validate(PREPARED_SET)
  strict=mods['render_strict_timing'].render(base,permit_materialized=True)
  prior=mods['paired_prepare'].render_pair(base_root=base,permit_materialized=True)
  result={}
  for arm,part in strict['arms'].items():
   before=copy.deepcopy(part);m=copy.deepcopy(part['manifest']);files=dict(part['files'])
   source_ref=source_set['trials'][trial_index]['arms'][arm];parent=obj(source_ref)
   need(parent['performance_arm']==arm,'actual exact reviewed trial/arm template')
   # Prove strict source bytes equal reviewed prepared source, except the
   # same two exact output constants necessitated by new own output roots.
   for n,b in files.items():
    old=checked(parent['files'][n])
    if n=='contract090.py':
     need(mods['three_trial_sources'].output_inverse(b,m['output_root'])==
          mods['three_trial_sources'].output_inverse(old,parent['output_root']),'only own output literal differs from reviewed trial')
    else:need(b==old,'whole exact reviewed prepared algorithm/operator/common source '+n)
   files['followup_source_validate.py']=validator_delta(files['followup_source_validate.py'])
   files['strict_bound_lineage.py']=Path(__file__).read_bytes()
   m=rebind(m,files)
   m.update(strict_bound_source_schema=SOURCE_SCHEMA,strict_prepared_source_set_ref=PREPARED_SET,
      strict_prepared_source_ref=source_ref,strict_trial_index=trial_index,
      strict_renderer_dependencies=ASSETS,followup_authority_ref=authority_ref,
      pending_current_authority=authority_ref is None)
   extra=[PREPARED_SET,source_ref,*ASSETS]
   if authority_ref is not None:
    a=mods['followup_source_validate'].authority_shape(obj(authority_ref))
    review=obj(a['MAIN_review_ref'])
    need(review.get('schema')=='bole.MAIN-performance-execution-review/v1'and review.get('approved')is True and
         review.get('scope')==mods['followup_source_validate'].SCOPE,'real existing current performance review, not created here')
    extra += [authority_ref,a['MAIN_review_ref']]
   d={r['path']:r for r in m['dependencies']}
   for r in extra:
    need(r['path']not in d or d[r['path']]==r,'unambiguous exact renderer/readset authority dependency')
    d[r['path']]=r
   m['dependencies']=list(d.values())
   result[arm]=dict(manifest=m,files=files,strict_before=before,paired_before=prior['arms'][arm],
       source_bound=False,formal_performance=False)
   inverse_files(result[arm],modules=mods)
  return result
def inverse_files(part,*,modules=None):
 files=dict(part['files']);before=part['strict_before'];parent=part['paired_before']
 need(set(files)==set(before['files'])|{'strict_bound_lineage.py'},'only one source-owned lineage helper added')
 files.pop('strict_bound_lineage.py')
 files['followup_source_validate.py']=checked(ORIGINAL_FSV)
 need(files==before['files'],'exact full FSV/helper inverse to reviewed strict source')
 restored=dict(files)
 for n,row in before['strict_timing_inverse'].items():
  if row['before']is None:restored.pop(n)
  else:
   b=parent['files'][n]
   need(row['before']==refbytes(Path(before['manifest']['root'])/n,b),'whole exact strict original inverse Ref')
   restored[n]=b
 need(restored==parent['files'],'complete strict timing inverse to original paired owner')
 if modules is not None:modules['paired_prepare'].inverse_files(parent)
 else:
  with renderer_modules()as mods:mods['paired_prepare'].inverse_files(parent)
 return True
def expected(m):
 need(m.get('strict_bound_source_schema')==SOURCE_SCHEMA and m['strict_prepared_source_set_ref']==PREPARED_SET and
      m['strict_renderer_dependencies']==ASSETS,'actual exact reviewed lineage/version/dependency closure')
 part=render_pair(Path(m['followup_preparation_root']),m['strict_trial_index'],
      authority_ref=m['followup_authority_ref'])[m['performance_arm']]
 need(m['strict_prepared_source_ref']==part['manifest']['strict_prepared_source_ref'],'correct trial/arm lineage')
 return part
def binding_shape(m,template,template_ref):
 need(m['prepared_only']is False and m['default_enabled']is False and
      m['prepared_template']==template_ref and template['prepared_only']is True and
      m['performance_ready']is False and m['numerical_qualified']is False,'actual defaultOFF bound state; never numeric promotion')
 normalized=dict(m);normalized['prepared_only']=True;normalized.pop('prepared_template')
 need(normalized==template,'binding changes only prepared-state and exact immutable template Ref')
 return True
def validate_bound_source(sr):
 m=obj(sr);root=Path(m['root'])
 need(Path(sr['path'])==root/'SOURCE_BOUND.json','actual whole bound source identity, never PREPARED Ref')
 template_ref=m['prepared_template']
 need(Path(template_ref['path'])==root/'SOURCE_TEMPLATE.json','own exact immutable source template')
 template=obj(template_ref);binding_shape(m,template,template_ref)
 part=expected(m);need(template==part['manifest'],'whole actual rendered bound-source template equality')
 need(m['files']['strict_bound_lineage.py']==ref(root/'strict_bound_lineage.py'),'actual source-owned exact lineage module')
 for n,b in part['files'].items():need(checked(m['files'][n])==b,'every actual source byte matches renderer')
 inverse_files(part)
 # This structural result explicitly is NOT model/authority/worker admission.
 return m
def validate_six_bound(index_ref):
 v=obj(index_ref)
 need(set(v)=={'schema','prepared_source_set_ref','trials'}and v['schema']==BOUND_SET_SCHEMA and
      v['prepared_source_set_ref']==PREPARED_SET and type(v['trials'])is list and len(v['trials'])==3,'explicit complete six actual bound-source set')
 roots=set()
 for i,t in enumerate(v['trials']):
  need(set(t)=={'pair_index','arms'}and type(t['pair_index'])is int and t['pair_index']==i and set(t['arms'])=={'native_ar','bole'},'ordered distinct3x2 bound-source identities')
  for arm,sr in t['arms'].items():
   m=validate_bound_source(sr)
   need(m['strict_trial_index']==i and m['performance_arm']==arm and m['root']not in roots and m['output_root']not in roots,'each exact own bound trial/arm, no replay')
   roots.update((m['root'],m['output_root']))
 return v
def source_refs(v):return [dict(pair_index=t['pair_index'],native_ar=t['arms']['native_ar'],bole=t['arms']['bole'])for t in v['trials']]
def checked_bound_math(pairs,*,obj,index_ref):
 # Derive the ACTUAL tested existing consumer function. Only its owning
 # source-set reader is changed; all request/serial/common/threshold bodies stay.
 raw=checked(ASSET_MAP['checked_pair_math.py']);tree=ast.parse(raw)
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='checked_math')
 text=ast.get_source_segment(raw.decode(),node)
 before="""  import three_trial_sources as TRIALS
  source_set=TRIALS.validate(source_set_ref)
  common_source_set=TRIALS.refs(source_set)"""
 after="""  source_set=validate_six_bound(source_set_ref)
  common_source_set=source_refs(source_set)"""
 text=once(text,before,after)
 with renderer_modules():
  spec=importlib.util.spec_from_file_location('_strict_actual_math',ASSET_MAP['checked_pair_math.py']['path'])
  M=importlib.util.module_from_spec(spec);exec(compile(raw,ASSET_MAP['checked_pair_math.py']['path'],'exec'),M.__dict__)
  env=dict(M.__dict__,validate_six_bound=validate_six_bound,source_refs=source_refs)
  exec(compile(text,'exact-owning-layer-bound-consumer','exec'),env)
  result=env['checked_math'](pairs,obj=obj,source_set_ref=index_ref)
 result.update(prepared_identities_not_used_for_actual_owner=True,formal_qualification=False)
 return result
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--review',action='store_true');p.add_argument('--base',type=Path);p.add_argument('--trial-index',type=int);a=p.parse_args()
 if not a.review:
  need(a.base is None and a.trial_index is None,'explicit review only')
  print('{"enabled":false,"source_bound":false,"formal_performance":false,"HTTP":false,"NPU":false}');return
 need(a.base is not None and a.trial_index is not None,'exact prospective trial operands')
 parts=render_pair(a.base,a.trial_index)
 print(json.dumps(dict(arms={a:dict(root=x['manifest']['root'],files=len(x['files']),authority_ref=None)for a,x in parts.items()},
  source_bound=False,formal_performance=False,HTTP=False,NPU=False)))
if __name__=='__main__':main()
