"""Whole-source followup validator. New performance authority is mandatory; V6 is not qualification."""
import hashlib
import json
from pathlib import Path
import time
import ast

SCHEMA='bole.followup-whole-source-validation/v1'
AUTH_SCHEMA='bole.MAIN-reviewed-fastpath-performance-execution-authority/v1'
SCOPE=dict(input_tokens=131,output_tokens=1024,concurrency=1,
           arms=['native_ar','bole'],physical_NPUs=[4,5,6,7],
           common_environment={'HCCL_DETERMINISTIC':'true'},phase_seconds=3600,cleanup_seconds=180)
TEST_FILES=('test_bole_performance_profile.py','test_bole_performance_lifecycle.py',
 'test_actual_service_callbacks.py','test_performance_streaming.py',
 'test_performance_binding_delta.py','test_observation_only.py')


def need(v,s):
    if not v:raise ValueError(s)


def read_ref(r,cap=4*2**20):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'} and type(r['bytes'])is int and
         0<=r['bytes']<=cap,'complete bounded actual Ref3')
    p=Path(r['path']);need(p.is_absolute() and p.is_file() and not any(x.is_symlink()for x in(p,*p.parents)),
                          'ordinary actual source/ref')
    before=p.stat();raw=p.read_bytes();after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns) and
         len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'stable complete actual Ref3')
    return raw


def authority_shape(a):
    need(type(a)is dict and set(a)=={'schema','approved','start_epoch','cutoff_epoch','scope','MAIN_review_ref'} and
         a['schema']==AUTH_SCHEMA and a['approved']is True and a['scope']==SCOPE and
         type(a['start_epoch'])is int and type(a['cutoff_epoch'])is int and
         a['cutoff_epoch']-a['start_epoch']>=2*(3600+180),
         'distinct MAIN-approved performance pair scope/window; not old or V6 correctness authority')
    return a


def execution_window(m,*,clock,require_phase):
    r=m.get('followup_authority_ref')
    need(r is not None,'new performance authority unbound; old correctness window cannot execute fastpath')
    a=authority_shape(json.loads(read_ref(r)))
    review=json.loads(read_ref(a['MAIN_review_ref']))
    need(review.get('approved')is True and review.get('schema')=='bole.MAIN-performance-execution-review/v1'
         and review.get('scope')==SCOPE,'actual distinct MAIN performance execution review')
    if clock:
        now=time.time()
        need(a['start_epoch']<=now<a['cutoff_epoch'] and
             (not require_phase or now+3600+180<=a['cutoff_epoch']),
             'full real phase and cleanup within newly approved window; no resets')
    return a


def active_cutoff():
    import sourceio as C
    root=Path(__file__).resolve().parent
    m=C.obj(C.ref(root/'SOURCE_BOUND.json'))
    need(m['root']==str(root) and C.ref(__file__)==m['files']['followup_source_validate.py'],
         'actual complete source-owned cutoff helper')
    return execution_window(m,clock=True,require_phase=False)['cutoff_epoch']


def require_fastpath_admission(m):
    # Intentionally unbound, not a caller-supplied PASS boolean. MAIN must add
    # the actual independent fastpath numerical consumer only after its real
    # evidence schema exists, then review/freeze that new complete source.
    raise ValueError('actual fastpath NPU numerical admission adapter remains unbound; V6 boundary repeatability cannot authorize performance')


def enumerate_tests(m):
    cases=[]
    for name in TEST_FILES:
        for cls in ast.parse(read_ref(m['files'][name])).body:
            if isinstance(cls,ast.ClassDef):
                cases.extend(name+':'+cls.name+'.'+fn.name for fn in cls.body
                    if isinstance(fn,ast.FunctionDef)and fn.name.startswith('test_'))
    need(len(cases)==len(set(cases))==46,'same exact original46 current software controls')
    return sorted(cases)


def validate(sr):
    # Imports are from the actual new source-owned package and pinned below.
    import sourceio as C
    import paired_prepare as P
    import followup_binding_delta as B
    import paired_receipt_consumer as JOIN
    import paired_contract as PAIR
    import performance_followup_delta as D
    import validated_performance_policy as FAST
    m=json.loads(read_ref(sr));root=Path(m['root'])
    need(root==Path(sr['path']).parent and m['prepared_only']is False and m['default_enabled']is False
         and m['followup_source_schema']==SCHEMA,'actual defaultOFF complete bound source')
    for name,mod in(('sourceio.py',C),('paired_prepare.py',P),('followup_binding_delta.py',B),
                     ('paired_receipt_consumer.py',JOIN),('paired_contract.py',PAIR),
                     ('performance_followup_delta.py',D),('validated_performance_policy.py',FAST),
                     ('followup_source_validate.py',__import__(__name__))):
        need(C.ref(mod.__file__)==m['files'][name],'actual loaded exact source helper '+name)
    template_ref=m['prepared_template'];template=json.loads(read_ref(template_ref))
    need(Path(template_ref['path'])==root/'SOURCE_TEMPLATE.json' and template['prepared_only']is True,
         'actual immutable prepared template, not manufactured qualification')
    expected=P.render_pair(base_root=Path(m['followup_preparation_root']),permit_materialized=True,
                           authority_ref=m['followup_authority_ref'])['arms'][m['performance_arm']]
    need(template==expected['manifest'],'complete exact source renderer/inverse manifest')
    P.inverse_files(expected)
    normalized=dict(m);normalized['prepared_only']=True;normalized.pop('prepared_template')
    need(normalized==template,'binding changes only prepared state and actual template Ref')
    for name,raw in expected['files'].items():
        ref=m['files'][name]
        need(Path(ref['path'])==root/name and read_ref(ref,128*2**20)==raw,
             'whole-source exact reconstruction, not allowed-name or AST subset '+name)
    # Keep original component numerical/predecessor reopen exactly, not a new
    # arithmetic gate or a V6 repeatability-to-performance promotion.
    import bind_model
    need(C.ref(bind_model.__file__)==m['files']['bind_model.py'],'original actual component readset helper')
    readset=bind_model.readset(sr)
    import command_contract
    need(C.ref(command_contract.__file__)==m['files']['command_contract.py'],'actual complete command closure helper')
    readset+=command_contract.validate(C,sr,m)
    for r in m['dependencies']:read_ref(r,128*2**20)
    execution_window(m,clock=False,require_phase=False)
    return dict(schema=SCHEMA,source=sr,source_validated=True,readset=readset,
        execution_authority_bound=True,tests=enumerate_tests(m),tests_executed=False,
        actual_NPU_two_generation_qualified=False,
        fastpath_numerical_qualified=False,whole_model_pass=False,
        performance_admitted=False,formal_performance=False,NPU=False)
