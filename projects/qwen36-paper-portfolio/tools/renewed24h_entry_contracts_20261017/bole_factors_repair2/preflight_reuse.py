"""Exact source-delta edge for already executed R1 CPU root-pair evidence.

The original evidence stays R1/source/owner/paths. New R2 still runs its full
software, actual read-only-root Torch/dill startup and fresh installed ABI.
Only the unchanged CPU root comparison is reused, not the failed NPU stage.
"""
from pathlib import Path

OLD_ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-saved-fa-factor-owned-renew24h-v1-001-repair1'
CPU_ROOT='/opt/host/vnf/austinov/run-bole-saved-fa-factor-repair1-MAIN-RENEW24H_001/factors/cpu'
def R(path,n,sha):return dict(path=path,bytes=n,sha256=sha)
SOURCE=R(OLD_ROOT+'/SOURCE_MANIFEST.json',31740,'0c9cfef77f5ecb709731d0ac08302c9c75f80ba21accc25b10274bcf3cb4d3b8')
OWNER=R(CPU_ROOT+'/RESULT.json',836,'d92a457919cc8f6b8561e14e6235ff93dd1a4319b5610b4d23ece18e592792f4')
STAGE=R(CPU_ROOT+'/preflight/STAGE_RESULT.json',1358,'902fcc8815d34b04e683cd77143247db4895d8df17c940aaecf4d1216b83451c')
ROOT_STAGE=R(CPU_ROOT+'/preflight/ROOT_PAIR_STAGE.json',1112,'5d38a6d679ea9fdf8a42d2416b14413525cd8e7639824fcea723b8a4022dd90f')
INSPECT=R(CPU_ROOT+'/FINAL_INSPECT.json',83110,'7bda398801c68be12ae60d85d3e97ba845978b87512d7ff9844e675fc8a45827')
PIN=dict(source=SOURCE,owner=OWNER,stage=STAGE,root_stage=ROOT_STAGE,final_inspect=INSPECT)
UNCHANGED=('factor.py','run_factor.py','root_pair.py','root_pair_stage.py','decision_gate.py','abi116.py',
           'consume_factor.py','probe115.py','tree_fa115.py','cpu_root_alias.py','ticket_alias116r5.py')

def validate(C,m):
 C.need(m['preflight_reuse']==PIN,'exact actual R1 CPU proof set, no future/synthetic PASS')
 old=C.obj(SOURCE);owner=C.obj(OWNER);stage=C.obj(STAGE);inspection=C.obj(INSPECT)
 C.need(old['prepared_only']is False and old['root']==OLD_ROOT and old['image']==m['image']and
        old['actual_diagnostic_source']==m['actual_diagnostic_source']and old['actual_diagnostic_owner']==m['actual_diagnostic_owner'],
        'exact same saved original inputs/reference/image domain, not another producer')
 refs=[SOURCE,OWNER,STAGE,INSPECT,ROOT_STAGE]
 for name in UNCHANGED:
  a,b=old['files'][name],m['files'][name]
  C.need((a['bytes'],a['sha256'])==(b['bytes'],b['sha256']),'exact unchanged root-pair/FA/ABI critical source '+name)
  C.checked(a);C.checked(b);refs.append(a)
 C.need(owner['schema']=='bole.tree-owned-CPU/vFAfactor'and owner['source']==SOURCE and owner['stage_result']==STAGE and
        owner['stage_ref']is None and owner['primary']is None and owner['secondary']==[]and
        owner['resource_release_verified']is owner['stopped_retained']is True and owner['Devices']==[]and owner['NPU']is False,
        'original real completed Devices[] CPU owner; never the R1 NPU FAIL')
 C.need(stage['schema']=='bole.tree-CPU-stage/vFAfactor'and stage['source']==SOURCE and stage['primary']is None and
        stage['NPU']is False and stage['actual_meta']['pass_gate']is True,'original actual source-bound CPU10+root-pair result')
 H=inspection['HostConfig']
 C.need(inspection['Id']==owner['cid']and inspection['Image']==m['image']and inspection['State']['Running']is False and
        inspection['State']['Pid']==0 and inspection['State']['ExitCode']==0 and not inspection['State']['OOMKilled']and
        not inspection.get('ExecIDs')and not H.get('Devices')and not H.get('DeviceRequests')and
        H['Memory']==H['MemorySwap']==8*2**30 and H['NanoCpus']==10**9 and H['ReadonlyRootfs']is True,
        'actual R1 natural stopped exact CPU CID/image/resources/noExec/noOOM')
 # Use the unchanged source-pinned original alias implementation, retaining
 # the old exact RW mount and complete old argv/source join.
 A=C.load(m['files']['ticket_alias116r5.py'],'_factor_reuse_exact_old_ABI_alias')
 abi,ir=A.resolve(C,SOURCE,old,OWNER,owner,stage);C.need(ir==INSPECT,'actual original final-inspect bytes')
 refs.append(abi)
 root_alias=C.load(m['files']['cpu_root_alias.py'],'_factor_reuse_exact_old_root_alias')
 mapped=root_alias.resolve(C,stage['root_pair_stage_ref'],cpu_owner_ref=OWNER,owner=owner,final_inspect_ref=INSPECT)
 C.need(mapped==ROOT_STAGE,'actual old root-pair stage, no reserialized report laundering')
 root=C.obj(mapped)
 C.need(root['source']==SOURCE and root['schema']=='bole.actual-native-root-repeat-pre-diagnostic/v1'and
        root['diagnostic_complete']is True and root['NPU']is root['operator_executed']is root['qualified']is False and
        len(root['reports'])==4,'same original complete root-pair values')
 for rank,rr in enumerate(root['reports']):
  actual=root_alias.resolve(C,rr,cpu_owner_ref=OWNER,owner=owner,final_inspect_ref=INSPECT);row=C.obj(actual)
  C.need(row['diagnostic_source']==SOURCE and row['rank']==rank and row['NPU']is row['qualified']is False and
         row['first_root_input_identical']is row['all_initial_cache_and_weights_identical']is True,
         'exact old all4 initial operand/cache/weights equality, no reassignment of source')
  refs.append(actual)
 control_ref=stage['software_controls']
 C.need(control_ref['path']=='/adakv-results/preflight/SOFTWARE_CONTROLS.json','only exact original controls guest alias')
 control_ref=dict(control_ref,path=CPU_ROOT+'/preflight/SOFTWARE_CONTROLS.json')
 controls=C.obj(control_ref);refs.append(control_ref)
 C.need(controls['source']==SOURCE and controls['exit_code']==0 and 'Ran 10 tests'in controls['stderr']and
        'OK'in controls['stderr']and 'FAILED'not in controls['stderr'],'original actual complete10-controls receipt')
 refs=list({r['path']:r for r in refs}.values())
 return dict(schema='bole.factor-exact-R1-root-pair-reuse/v1',original_source=SOURCE,original_CPU_owner=OWNER,
    original_stage=STAGE,original_root_stage=ROOT_STAGE,original_final_inspect=INSPECT,root_pair_refs=refs,
    unchanged_critical_files=list(UNCHANGED),original_NPU_failure_unchanged=True,
    new_R2_startup_and_software_still_required=True,qualified=False)

def consume(C,m,value):
 expected=validate(C,m);C.need(value==expected,'whole exact source-bound reuse proof, not a hand-written PASS');return expected
