"""CPU/source controls only. Tripwires forbid Docker, child commands and tensor imports."""
import ast, copy, importlib.util, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WS=ROOT.parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
M=load('_v7_admission',ROOT/'main_admission_ON_v7_startup.py')
history=load('_v7_history',ROOT/'historical_owner_context_v7_startup.py')
snap=load('_v7_snapshot',ROOT/'final_snapshot_ON_v7_startup.py')
rows=[]
def check(value,name):
    if not value:raise AssertionError(name)
    rows.append(name)
for p in ROOT.glob('*.py'):ast.parse(p.read_bytes())
for program,args in ((ROOT/'main_admission_ON_v7_startup.py',[]),
                     (ROOT/'final_snapshot_ON_v7_startup.py',[])):
    r=subprocess.run([sys.executable,'-I','-B',str(program),*args],capture_output=True,text=True,timeout=10)
    check(r.returncode==0 and json.loads(r.stdout)['enabled'] is False,'actual default OFF '+program.name)
r=subprocess.run([sys.executable,'-I','-B',str(ROOT/'main_admission_ON_v7_startup.py'),
    '--execute','--config-ref','{}','--review-ref','{}'],capture_output=True,text=True,timeout=10)
check(r.returncode==2 and json.loads(r.stdout)['dispatch_performed'] is False,'unfrozen execute refused')
cfg=json.loads((ROOT/'CONFIG.ON.template.json').read_bytes())
check(cfg['template'] is True and cfg['source_ref'] is None and cfg['snapshot_ref'] is None,'pending evidence not fabricated')
check(str(M.SOURCE)==cfg['source_root']==str(snap.NEW_SOURCE) and
      str(M.OUTPUT)==cfg['output_root']==str(snap.NEW_OUTPUT) and
      str(M.EVIDENCE)==cfg['evidence_root'] and
      M.EVIDENCE!=WS.parent/'run-bole-reduction-main-admission-ON_v5_20261022T200000Z',
      'actual source/output/evidence producer identities agree and no old evidence reuse')
check(len(cfg['old_owners'])==16 and len(M.OLD_CIDS)==16,'sixteen owner registry')
extra,refs=snap.extra_identities()
check(len(extra)==6 and {r['id'] for r in extra}=={r['cid'] for r in cfg['old_owners'][-6:]},
      'actual source-typed snapshot extras')
def forbidden(*a,**k):raise AssertionError('no external command allowed in source controls')
for name in ('run','Popen','check_output','check_call','call'):setattr(subprocess,name,forbidden)
import builtins
old_import=builtins.__import__
def guarded(name,*a,**k):
    if name.split('.')[0] in ('torch','torch_npu'):raise AssertionError('no tensor import')
    return old_import(name,*a,**k)
builtins.__import__=guarded
C=load('_v7_control_common',WS/'native_ar_fsum_oracle_v1/ar_owner_common.py')
NS=load('_v7_control_namespace',WS/'native_ar_fsum_oracle_v1/ar_saved_namespace.py')
base=json.loads((WS/'bound-boundary-ON-v4-textonly_20261022T171000Z/SOURCE_BOUND.json').read_bytes())
current=json.loads((WS/'bound-reduction-ON-v7-startup_20261022T215000Z/SOURCE_BOUND.json').read_bytes())
check(current['output_root']==cfg['output_root'],'actual frozen V7 output identity')
os.environ['DENSE090_EXTERNAL_OUTPUT_ENABLE']='1'
output='/opt/host/vnf/austinov/run-bole-native-ar-v7-history-source-control-no-owner'
rs=M.Readset()
snapshot={k:{'containers':[]} for k in ('inspect_before','inspect_old_after')}
for spec in cfg['old_owners']:
    cleanup=rs.obj(spec['cleanup_ref'])
    receipt=rs.obj(cleanup['after_inspect'])
    full=json.loads(receipt['stdout'])[0]
    row=dict(Id=full['Id'],Name=full['Name'],Image=full['Image'],State=full['State'],
             ExecIDs=full.get('ExecIDs'),labels={k:v for k,v in full['Config']['Labels'].items()
                 if k.startswith('model-tuning-lab.')},mounts=full['Mounts'])
    for key in snapshot:snapshot[key]['containers'].append(copy.deepcopy(row))
with NS.open_namespace(C,dict(output_root=output,authority=base['authority_ref']),base) as (c,S,H,proof):
    current_owned=current['files']['owned_substrate.py']
    history.NEW_OWNED=(current_owned['bytes'],current_owned['sha256'])
    owners,contexts,proofs=M.historical_owners(rs,cfg,snapshot,S,current,history)
    check(len(owners)==16 and len(contexts)==16 and len(proofs)==16,
          'actual sixteen full create/inspect/stop-retain/release/result histories accepted')
    check(sum(p['historical_host_outcome']['kind']=='completed-standalone-replay-lifecycle-only' for p in proofs)==2,
          'replay lifetime not production TP/model qualification')
    bad=copy.deepcopy(cfg);bad['old_owners'][-3]['kind']='model'
    try:M.historical_owners(rs,bad,snapshot,S,current,history)
    except ValueError:pass
    else:raise AssertionError('replay classified as model accepted')
    check(True,'replay/model schema confusion refused')
    for spec in cfg['old_owners'][-2:]:
        owned=rs.obj(spec['owned_ref']);result=rs.obj(spec['host_result_ref']);cleanup=rs.obj(spec['cleanup_ref'])
        check(M.historical_host_result(rs,spec,owned,result,cleanup)['kind']=='completed-failed-V6-health-lifecycle-only',
              'actual V6 failure retained '+owned['arm'])
        result=copy.deepcopy(result);result['primary']=None
        try:M.historical_host_result(rs,spec,owned,result,cleanup)
        except ValueError:pass
        else:raise AssertionError('V6 failure silently promoted to null primary')
    check(True,'V6 null-primary mutation refused')
    badsnap=copy.deepcopy(snapshot)
    badsnap['inspect_old_after']['containers'][-1]['State']['Running']=True
    try:M.historical_owners(rs,cfg,badsnap,S,current,history)
    except ValueError:pass
    else:raise AssertionError('running historical owner accepted')
    check(True,'running replay owner refused')
rs.verify_again()
check(not Path(output).exists(),'source control created no output/owner')
print(json.dumps(dict(passed=True,controls=rows,NPU=False,Docker=False,source_frozen=False,
                      resources_admitted=False,MAIN_review_performed=False)))
