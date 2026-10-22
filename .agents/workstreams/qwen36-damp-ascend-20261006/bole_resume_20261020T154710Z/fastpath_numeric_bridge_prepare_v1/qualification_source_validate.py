"""Short8 FAST qualification-only source gate. Never grants formal performance."""
import ast
import hashlib
import json
from pathlib import Path
import time

SCHEMA='bole.followup-whole-source-validation/v1'
QUAL_SCHEMA='bole.fastpath-short8-qualification-whole-source/v1'
AUTH_SCHEMA='bole.MAIN-reviewed-fastpath-short8-qualification-authority/v1'
REVIEW_SCHEMA='bole.MAIN-fastpath-short8-qualification-source-review/v1'
SCOPE=dict(input_tokens=131,output_tokens=8,concurrency=1,generations=2,arm='bole',
           physical_NPUs=[4,5,6,7],common_environment={'HCCL_DETERMINISTIC':'true'},
           phase_seconds=3600,cleanup_seconds=180,formal_performance=False)
TEST_FILES=('test_short_state_digest.py','test_digest_reader.py',
            'test_short_dependency_contract.py','test_qualification_entry.py')
TEST_COUNT=25

def need(v,s):
    if not v:raise ValueError(s)

def exact(actual,expected):
    if type(actual)is not type(expected):return False
    if type(expected)is dict:
        return set(actual)==set(expected)and all(exact(actual[k],v)for k,v in expected.items())
    if type(expected)is list:
        return len(actual)==len(expected)and all(exact(a,b)for a,b in zip(actual,expected))
    return actual==expected

def read_ref(r,cap=128*2**20):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and
         0<=r['bytes']<=cap,'bounded complete exact Ref3')
    p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),
                         'ordinary exact source/authority file without links')
    before=p.stat();raw=p.read_bytes();after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)and
         len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256'],'stable complete Ref3 identity')
    return raw

def authority_shape(a):
    need(type(a)is dict and set(a)=={'schema','approved','start_epoch','cutoff_epoch','scope','MAIN_review_ref'}and
         a['schema']==AUTH_SCHEMA and a['approved']is True and exact(a['scope'],SCOPE)and
         type(a['start_epoch'])is int and type(a['cutoff_epoch'])is int and
         a['cutoff_epoch']-a['start_epoch']>=3600+180,
         'distinct actual reviewed short8 qualification authority; never a formal1024/old window')
    return a

def qualification_shape(m):
    need(m['qualification_source_schema']==QUAL_SCHEMA and m['default_enabled']is False and
         m['performance_arm']=='bole'and m['performance_ready']is False and m['numerical_qualified']is False,
         'defaultOFF qualification candidate only, never performance admission')
    p=m['fastpath_numeric_qualification']
    need(exact(p,dict(schema='bole.fastpath-numeric-qualification-profile/v1',enabled=True,input_tokens=131,
        output_tokens=8,generations=2,logical_frame_cap=384*2**20,independent_reference=True,
        formal_performance=False)),'exact typed short8 qualifier, no160/1024 scope promotion')
    need(m['performance_profile']['scope']['input_tokens']==131 and
         m['performance_profile']['scope']['output_tokens']==8 and
         m['performance_profile']['scope']['concurrency']==1 and
         m['service_experiment']['max_output_tokens']==8 and
         m['profile']['HTTP_output_tokens']==8 and m['performance_client_contract']['output_tokens']==8,
         'real worker, host and client declarations agree on short8')
    return True

def execution_window(m,*,clock,require_phase):
    qualification_shape(m)
    ref=m.get('qualification_authority_ref')
    need(ref is not None,'actual short8 qualification execution authority is unbound; no default or clock renewal')
    a=authority_shape(json.loads(read_ref(ref)))
    review=json.loads(read_ref(a['MAIN_review_ref']))
    need(review.get('schema')==REVIEW_SCHEMA and review.get('approved')is True and
         exact(review.get('scope'),SCOPE)and review.get('source_root')==m['root']and
         review.get('output_root')==m['output_root']and review.get('files')==m['files']and
         review.get('parent_preparation_readset')==m['qualification_parent_preparation_readset']and
         review.get('historical_short_source')==m['qualification_historical_short_source'],
         'actual MAIN review pins complete source bytes/roots and parent readset, not caller PASS')
    if clock:
        now=time.time()
        need(a['start_epoch']<=now<a['cutoff_epoch']and
             (not require_phase or now+3600+180<=a['cutoff_epoch']),
             'whole phase+cleanup inside actual authority; no old/current deadline reset')
    return a

def active_cutoff():
    import sourceio as C
    root=Path(__file__).resolve().parent;m=C.obj(C.ref(root/'SOURCE_BOUND.json'))
    need(m['root']==str(root)and C.ref(__file__)==m['files']['qualification_source_validate.py'],
         'actual source-owned qualification cutoff helper')
    return execution_window(m,clock=True,require_phase=False)['cutoff_epoch']

def require_fastpath_admission(m):
    # Existing host API name retained, but this source can ONLY collect numeric
    # qualification data. The separate formal1024 validator is never changed.
    need(m['prepared_only']is False,'prepared source never executes')
    execution_window(m,clock=True,require_phase=True)
    return dict(schema='bole.short8-qualification-observation-admission/v1',
        qualification_collection_only=True,fastpath_numerical_qualified=False,
        performance_admitted=False,formal_performance=False,NPU_result_created=False)

def enumerate_tests(m):
    cases=[]
    for name in TEST_FILES:
        for cls in ast.parse(read_ref(m['files'][name])).body:
            if isinstance(cls,ast.ClassDef):
                cases.extend(name+':'+cls.name+'.'+fn.name for fn in cls.body
                    if isinstance(fn,ast.FunctionDef)and fn.name.startswith('test_'))
    need(len(cases)==len(set(cases))==TEST_COUNT,'exact20 original short controls plus5 qualification controls')
    return sorted(cases)

def dependency_contract(m):
    # Filled by the exact whole-source renderer with the unchanged actual short
    # donor dependency_contract body, not a relaxed replacement.
    raise ValueError('source renderer must install original short dependency_contract')

def validate(sr):
    import sourceio as C
    root=Path(sr['path']).parent;m=json.loads(read_ref(sr))
    need(m['prepared_only']is False and Path(m['root'])==root and
         root==Path(__file__).resolve().parent,'actual own bound short qualification source')
    qualification_shape(m)
    # Verify actual MAIN review and every external preparation byte BEFORE
    # importing its renderer. Merely failing after unreviewed code executes
    # would not be a fail-closed source gate.
    execution_window(m,clock=False,require_phase=False)
    for name,ref in m['qualification_parent_preparation_readset'].items():read_ref(ref)
    read_ref(m['files']['qualification_short_prepare.py'])
    read_ref(m['files']['qualification_source_producer.py'])
    read_ref(m['files']['qualification_parent_renderer.py'])
    read_ref(m['files']['qualification_tap_delta.py'])
    import qualification_short_prepare as Q
    import qualification_source_producer as B
    import qualification_parent_renderer as R
    for name,mod in(('sourceio.py',C),('qualification_short_prepare.py',Q),
                    ('qualification_source_producer.py',B),('qualification_parent_renderer.py',R),
                    ('qualification_source_validate.py',__import__(__name__))):
        need(C.ref(mod.__file__)==m['files'][name],'actual source-owned loaded helper '+name)
    # Parent preparation imports are allowed only as fully pinned renderer
    # dependencies. They are not candidate worker implementations.
    # Q isolates the complete pinned external renderer namespace only while
    # rebuilding. Source-owned FAST worker modules are restored byte-for-byte
    # and by module object, not confused with external formal-policy modules.
    template_ref=m['prepared_template'];template=json.loads(read_ref(template_ref))
    need(Path(template_ref['path'])==root/'SOURCE_TEMPLATE.json'and template['prepared_only']is True,
         'actual prepared template, not invented numerical qualification')
    expected=Q.render(base_root=Path(m['qualification_preparation_root']),permit_materialized=True,
        parent_pair_preparation_root=Path(m['qualification_parent_pair_preparation_root']),
        historical_short_source_ref=m['qualification_historical_short_source'],
        authority_ref=m['qualification_authority_ref'],
        parent_preparation_readset=m['qualification_parent_preparation_readset'])
    need(template==expected['manifest'],'complete exact short source reconstruction, not AST/name subset')
    Q.inverse(expected)
    need(m['qualification_source_binding_pending']is False,'actual source binding transition completed')
    actual=dict(m);actual['prepared_only']=True;actual['qualification_source_binding_pending']=True
    actual.pop('prepared_template')
    need(actual==template,'binding changes only prepared/binding state and actual immutable template Ref')
    for name,raw in expected['files'].items():
        need(Path(m['files'][name]['path'])==root/name and read_ref(m['files'][name])==raw,
             'full source bytes and exact location '+name)
    import bind_model
    need(C.ref(bind_model.__file__)==m['files']['bind_model.py'],'original independent component readset helper')
    readset=bind_model.readset(sr)
    import command_contract
    need(C.ref(command_contract.__file__)==m['files']['command_contract.py'],'actual new producer command closure')
    readset+=command_contract.validate(C,sr,m)
    for ref in m['dependencies']:read_ref(ref)
    authority=execution_window(m,clock=False,require_phase=False)
    readset.extend([sr,template_ref,*m['files'].values(),*m['dependencies'],
        *m['qualification_parent_preparation_readset'].values(),
        m['qualification_historical_short_source'],m['qualification_authority_ref'],authority['MAIN_review_ref']])
    complete={}
    for ref in readset:
        need(ref['path']not in complete or complete[ref['path']]==ref,'unambiguous complete source readset')
        complete[ref['path']]=ref
    readset=list(complete.values())
    return dict(schema=SCHEMA,qualification_source_schema=QUAL_SCHEMA,source=sr,source_validated=True,
        readset=readset,tests=enumerate_tests(m),tests_executed=False,
        qualification_observation_source_only=True,actual_NPU_two_generation_qualified=False,
        fastpath_numerical_qualified=False,whole_model_pass=False,
        performance_admitted=False,formal_performance=False,NPU=False)
