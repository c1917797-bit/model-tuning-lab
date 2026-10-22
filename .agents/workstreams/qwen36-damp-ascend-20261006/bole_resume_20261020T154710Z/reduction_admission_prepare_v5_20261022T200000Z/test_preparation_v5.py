"""Device-free preparation regression; no Docker/model/NPU calls."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WS = ROOT.parent
BASE = WS/'textonly_main_admission_v1_20261022T171000Z'
PREFIX = 'reduction_'
CIDS = {'79c06ff95a70e957a5afd7e7ac1dc46932e7b45e4afde72fd56d0d4f996eab7c',
        '4e17856a927a9bbccce9d145db5151c1c14e1688357124f9773fd878ac6003ec'}
def need(value, why):
    if not value:
        raise AssertionError(why)
def tree(path):
    return ast.parse(path.read_bytes(), filename=str(path))
def constants(path):
    result = {}
    for node in tree(path).body:
        if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result
def func(path, name):
    rows=[n for n in tree(path).body if isinstance(n, ast.FunctionDef) and n.name==name]
    need(len(rows)==1, 'unique function '+name)
    return ast.dump(rows[0], include_attributes=False)
def run(path, args=()):
    child=subprocess.run([sys.executable,'-I','-B',str(path),*args],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10)
    return child
def static_path(path, name):
    nodes=[n for n in tree(path).body if isinstance(n,ast.Assign)
           and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
           and n.targets[0].id==name]
    need(len(nodes)==1, 'one path assignment '+name)
    node=nodes[0].value
    need(isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
         and node.func.id=='Path' and len(node.args)==1 and not node.keywords,
         'literal actual Path expression '+name)
    return Path(ast.literal_eval(node.args[0]))
def audit_fields(path):
    candidates=[]
    for node in ast.walk(tree(path)):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='dict':
            values={kw.arg:kw.value for kw in node.keywords}
            schema=values.get('schema')
            if isinstance(schema,ast.Constant) and schema.value=='bole.boundary-source-admission/v1':
                candidates.append(set(values))
    need(len(candidates)==1,'one actual source admission producer')
    return candidates[0]
def required_audit_fields(path):
    nodes=[n for n in tree(path).body if isinstance(n,ast.FunctionDef) and n.name=='source_inputs']
    return {n.slice.value for n in ast.walk(nodes[0])
            if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name)
            and n.value.id=='audit' and isinstance(n.slice,ast.Constant)}

rows=[]
for path in sorted(ROOT.glob('*.py')):
    tree(path)
    rows.append({'test':'syntax','path':str(path),'pass':True})
for arm in ('ON','OFF'):
    launch=ROOT/('main_admission_'+arm+'_v5.py')
    snapshot=ROOT/('final_snapshot_'+arm+'_v5.py')
    cfg=json.loads((ROOT/('CONFIG.'+arm+'.template.json')).read_text())
    constant=constants(launch)
    builder=WS/'reduction_probe_prepare_v5_20261022T200000Z'/arm/'prepare_boundary.py'
    auditor=builder.parent/'audit_boundary_source.py'
    source=static_path(builder,'ROOT')
    output=static_path(builder,'OUT')
    need(static_path(launch,'SOURCE')==static_path(snapshot,'NEW_SOURCE')==source
         and Path(cfg['source_root'])==source, 'actual builder/launcher/snapshot/config SOURCE join')
    need(static_path(launch,'OUTPUT')==static_path(snapshot,'NEW_OUTPUT')==output
         and Path(cfg['output_root'])==output, 'actual builder/launcher/snapshot/config OUTPUT join')
    need(static_path(auditor,'ROOT')==source
         and static_path(auditor,'OUT')==Path(str(output)+'-SOURCE-AUDIT'),
         'actual builder/auditor source and output join')
    need(required_audit_fields(launch)<=audit_fields(auditor),
         'actual auditor emits every original admission-consumed audit field')
    need(constant['REVIEWED_FROZEN'] is False and constant['SNAPSHOT_PROGRAM_PIN'] is None
         and constant['HISTORICAL_CONTEXT_PIN'] is None, 'draft cannot dispatch')
    need(constant['IMAGE']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',
         'pinned original image')
    need(len(cfg['old_owners'])==10 and len({x['cid'] for x in cfg['old_owners']})==10
         and CIDS <= {x['cid'] for x in cfg['old_owners']}, 'V4 BOTH owners, original8')
    need(cfg['template'] is True and cfg['current_owned_substrate_ref'] is None
         and cfg['snapshot_ref'] is None and cfg['source_ref'] is None,
         'future evidence explicit, never fabricated')
    for name in ('need','canonical','parse','typed_ref','load_exact','original_labels',
                 'stopped','command_ok','inspect_receipt','exact_created_argv',
                 'historical_host_result','snapshot_inputs','source_inputs',
                 'current_live_checks','require_exec_limits'):
        need(func(launch,name)==func(BASE/'main_admission_textonly_v1.py',name),
             'original predicate/function preserved: '+name)
    for program in (launch,snapshot):
        child=run(program)
        need(child.returncode==0 and child.stderr=='','real default OFF clean CLI')
        disabled=json.loads(child.stdout)
        need(disabled['enabled'] is False and disabled['NPU'] is False
             and disabled['resources_admitted'] is False,'OFF result')
        helpchild=run(program,['--help'])
        need(helpchild.returncode==0 and 'usage:' in helpchild.stdout,'real help CLI')
    blocked=run(launch,['--execute','--config-ref','{}','--review-ref','{}'])
    need(blocked.returncode==2 and json.loads(blocked.stdout)['dispatch_performed'] is False
         and 'draft is not frozen/reviewed' in json.loads(blocked.stdout)['error'],
         'unfrozen execute fails before source/model/resource work')
    snapblocked=run(snapshot,['--execute-readonly'])
    snapvalue=json.loads(snapblocked.stdout)
    need(snapblocked.returncode==2 and snapvalue['complete'] is False
         and any('draft is not frozen/reviewed' in x for x in snapvalue['errors']),
         'unfrozen snapshot fails before live read helper')
    rows.append({'test':'arm-original-predicates/default-OFF/help/unfrozen-refusal',
                 'arm':arm,'pass':True})
hist=ROOT/'historical_owner_context_reduction_v5.py'
need(constants(hist)['NEW_OWNED'] is None, 'no guessed current substrate identity')
need(len(constants(hist)['TEXTONLY_CIDS'])==2,'latest two exact owner allowlist')
allrefs=[]
for path in sorted(ROOT.iterdir()):
    if path.is_file():
        b=path.read_bytes()
        allrefs.append({'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
print(json.dumps({'schema':'bole.reduction-admission-preparation-software/v1',
    'tests':rows,'passed':True,'source_refs':allrefs,'CPU_only':True,
    'containers_created':False,'NPU':False,'dispatch_performed':False,
    'source_frozen':False,'MAIN_review_performed':False,'resources_admitted':False,
    'numerical_qualified':False,'formal_performance':False,'task_accuracy':False},
    sort_keys=True))
