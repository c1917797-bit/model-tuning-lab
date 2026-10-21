"""Source-bound predecessor and independent runtime-only evidence readers."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import he_policy as H
import lock_evidence as L
MARKER='BOLE_HE_RUNTIME_DIAGNOSTIC_V2 '
INTERPRETER_MARKER='BOLE_HE_RUNTIME_INTERPRETER_V2 '


def predecessor(owner_ref,HE_owned_ref,HE_release_ref):
    refs={}
    def add(r):
        a=C.ref(C.checked(r));refs[a['path']]=a;return a
    def obj(r):add(r);return C.obj(r)
    er=add(C.ref(P/'PREVIOUS_CPU_EXPECTED.json'));C.need(er['sha256']==C.PREVIOUS_EXPECTED_SHA,'exact frozen failedv10/source inventory')
    expected=obj(er);v=obj(owner_ref)
    C.need(v['schema']=='bole.actual-finite-task-CPU-owner/v3'and v['diagnostic_only']is False
           and v['primary']['phase']=='he-controls'and v['secondary']==[]
           and v['source_input_before']==v['source_input_after']and v['private_namespace_restored_by_identity']is True
           and v['source_image_CPU_owner_software_controls_verified']is False and v['model_executed']is False,
           'retained source-stable failedHE owner, never a full qualification')
    x=obj(v['inputs_ref']);C.need(x['image_id']==C.IMAGE and set(x['files'])==set(expected['CPU_source']),'actual exact previous CPUv10 code source')
    for n,r in x['files'].items():
        a=add(r);w=expected['CPU_source'][n]
        C.need((a['bytes'],a['sha256'])==(w['bytes'],w['sha256'])and v['source_input_before'].get(a['path'])==a['sha256'],
               'actual previous v10 whole code before/after '+n)
    child=obj(v['summary']['CPU']['report']);p=child['payload'];release=obj(v['summary']['CPU_release'])
    C.need(child['inputs_ref']==v['inputs_ref']and child['mode']=='prepare-decode'
           and child['readset_before']==child['readset_after']and p['pure_controls_pass']is True
           and p['all_input_source_gold_template_verified']is True and p['forbidden_import_attempts']==[]
           and p['counts']=={'GSM8K':1319,'HumanEval':164,'MMLU':14042}
           and release['stopped']is True and release['retained']is True and release['errors']==[],
           'actual successful complete firstCPU phase and actual stopped CPU child')
    decoder=obj(p['decoder_ref']);coverage=decoder['coverage']
    C.need(coverage['counts']==p['counts']and coverage['complete_official_source_gold_and_template_coverage']is True,
           'actual full15525 first-phase provenance, not header-only counts')
    stage=obj(p['HE_stage_ref']);C.need(stage['schema']=='bole.he-sandbox-stage/v1'and stage['kind']=='controls'
           and stage['phase']=='software-controls'and stage['image_id']==C.IMAGE,'actual public fixed known control stage')
    cap=obj(stage['capsule_ref']);C.need(cap['schema']=='bole.he-public-source-capsule/v1','actual original evaluator capsule')
    def rows(root,entries):
        for row in entries:
            q=Path(row['relative']);C.need(not q.is_absolute()and'..'not in q.parts,'ordinary declared public stage file')
            add(dict(path=str(Path(root)/q),bytes=row['bytes'],sha256=row['sha256']))
    rows(stage['source_root'],cap['files']);rows(stage['suite_root'],cap['official_package_files'])
    inp=obj(C.ref(Path(stage['input_root'])/'INPUTS.json'));rows(stage['input_root'],inp['files'])
    C.need(inp['kind']=='controls'and inp['case_labels']==['correct','wrong','timeout'],'public known controls only; no task samples')
    for name,key in(('he_worker.py','original_he_worker'),('task_contract.py','original_task_contract')):
        a=add(C.ref(Path(stage['source_root'])/name));w=expected[key]
        C.need((a['bytes'],a['sha256'])==(w['bytes'],w['sha256']),'unchanged original public worker/runtime guard '+name)
    e=obj(HE_owned_ref);hr=obj(HE_release_ref)
    C.need(e['image']==C.IMAGE and e['arm']=='cpu-preflight'and e['guest_cpus']==[145]
           and e['source']==p['bound_task_source_ref']and hr['container']==e['cid']
           and hr['stopped']is True and hr['retained']is True and hr['deleted']is False and hr['errors']==[],
           'actual old HE owned identity stopped retained before diagnostic')
    want=H.argv(e['name'],C.IMAGE,stage['source_root'],stage['suite_root'],stage['input_root'],stage['capsule_ref']['sha256'],'controls')
    C.need(e['create_argv']==want,'exact original env-i/public-only HE control argv')
    creation=obj(e['create_receipt']);C.need(creation['exit_code']==0 and creation['stdout'].strip()==e['cid']
        and creation['requested_argv']==want,'actual old HE create receipt fullCID/argv join')
    after=obj(hr['after_inspect']);rows_actual=json.loads(after['stdout'])
    C.need(after['exit_code']==0 and after['requested_argv']==['/usr/bin/docker','inspect',e['cid']]and len(rows_actual)==1,'actual final oldHE inspect')
    a=rows_actual[0]
    C.need(a['Id']==e['cid']and a['Name']=='/'+e['name']and a['Image']==C.IMAGE and a['State']['Running']is False
           and a['State']['Pid']==0 and not a.get('ExecIDs')and a['HostConfig']['RestartPolicy']['Name']=='no',
           'old HE fullCID/source lifetime is retired; no task/model inference')
    for key in('before_inspect','stop_receipt'):add(hr[key])
    binding=obj(v['summary']['HE_binding']);C.need(binding['container_id']==e['cid']and binding['uid']==65534 and binding['Devices']==[],'actual oldHE bound uid/Devices identity')
    return dict(stage_ref=p['HE_stage_ref'],stage=stage,capsule=cap,refs=list(refs.values()),HE_owned=e)


def parse_probe(text,capsule_sha):
    C.need(type(text)is str and len(text.encode())<=2**20,'bounded1MiB diagnostic stdout/stderr')
    rows=[line[len(MARKER):]for line in text.splitlines()if line.startswith(MARKER)]
    C.need(len(rows)==1,'one complete actual diagnostic observation')
    v=json.loads(rows[0]);C.need(v['schema']=='bole.actual-HE-runtime-isolation-diagnostic/v2'and v['capsule_sha256']==capsule_sha,
        'same actual source-bound probe capsule')
    py=v['interpreter'];C.need(type(py)is dict and set(py)=={'version','version_info','implementation','executable'}
        and all(type(py[k])is str and 0<len(py[k].encode())<=2048 for k in('version','implementation','executable'))
        and type(py['version_info'])is list and len(py['version_info'])==5
        and all(type(py['version_info'][i])is int and py['version_info'][i]>=0 for i in(0,1,2,4))
        and type(py['version_info'][3])is str and py['version_info'][3]in('alpha','beta','candidate','final'),
        'bounded actual interpreter identity; no inferred or predetermined version')
    early=[line[len(INTERPRETER_MARKER):]for line in text.splitlines()if line.startswith(INTERPRETER_MARKER)]
    C.need(len(early)==1 and json.loads(early[0])==py,'same actual early interpreter receipt retained even before source guard')
    env=v['environment'];names=v['sys_class_net_names']
    C.need(set(env)=={'ASCEND_VISIBLE_DEVICES','HOME'}and all(value is None or type(value)is str for value in env.values())
        and type(names)is list and names==sorted(set(names))and len(names)<=64 and all(type(n)is str for n in names),
        'only two permitted actual env values and bounded actual sys interface names')
    expected=dict(ASCEND_VISIBLE_DEVICES_empty=env['ASCEND_VISIBLE_DEVICES']=='',HOME_tmp=env['HOME']=='/tmp',
        sys_class_interfaces_loopback_only=set(names)<={'lo'})
    C.need(v['conditions']==expected and all(type(n)is bool for n in v['conditions'].values())
        and type(v['proc_self_net_dev'])is str and len(v['proc_self_net_dev'].encode())<=65536
        and type(v['net_namespace_link'])is str and len(v['net_namespace_link'])<=256,
        'independent three-condition replay with actual proc network view and namespace')
    guard=v['original_runtime_guard'];C.need(guard['called']is True and type(guard['passed'])is bool
        and((guard['passed']is True and guard['error']is None)or(guard['passed']is False and type(guard['error'])is str)),
        'original guard actually called; failure remains a failure observation')
    C.need(v['diagnostic_only']is True and all(v[k]is False for k in('evaluator_executed','generated_code_executed','task_score_produced',
        'full_software_qualification_accepted','network_safety_accepted','NPU')),'runtime-only observation never qualification or code execution')
    return v


def consume(owner_ref):
    v=C.obj(owner_ref);C.need(v['schema']=='bole.actual-HE-runtime-diagnostic-owner/v2'and v['primary']is None and v['secondary']==[]
        and v['diagnostic_observation_complete']is True and v['private_namespace_restored_by_identity']is True
        and v['source_input_before']==v['source_input_after']and v['full_software_qualification_accepted']is False,
        'actual complete retained diagnostic owner with exact inverse; no qualification')
    x=C.inputs(v['inputs_ref']);s=v['summary'];stage=C.obj(x['stage_ref']);raw=C.checked(s['logs_ref']).read_text()
    import main_quiescence as Q
    policy=Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref'])
    lock=L.validate(C.obj(s['inherited_lock_ref']),x['main_quiescence_ref'],policy['serial_schedule']['external_lock_path'])
    C.need(lock['owner_pid']==v['actual_host_pid']and lock['owner_start_ticks']==v['actual_host_start_ticks'],
        'pre-create inherited lock belongs to this exact actual owner lifetime')
    observation=parse_probe(raw,stage['capsule_ref']['sha256']);C.need(C.obj(s['observation_ref'])==observation,'independent actual log replay')
    owned=C.obj(s['owned_ref']);release=C.obj(s['release_ref']);binding=C.obj(s['binding_ref']);argv=C.obj(s['create_argv_ref'])
    want=H.argv(owned['name'],C.IMAGE,stage['source_root'],stage['suite_root'],stage['input_root'],stage['capsule_ref']['sha256'],'controls')
    want[want.index('/source/he_worker.py')]='/source/he_runtime_probe.py'
    C.need(argv==owned['create_argv']==want and owned['source']==v['inputs_ref']and release['container']==owned['cid']
        and release['stopped']is True and release['retained']is True and release['errors']==[]
        and binding['container_id']==owned['cid']and binding['uid']==65534 and binding['Devices']==[]
        and binding['cpu']['effective_cpus']==[145]and binding['cpu']['effective_capacity']==1
        and binding['memory']['effective_bytes']==2*C.GIB,'actual source/fullCID/nonprivileged/CPU/memory/retirement joins')
    created=C.obj(owned['create_receipt']);C.need(created['exit_code']==0 and created['stdout'].strip()==owned['cid']
        and created['requested_argv']==want,'actual successful same-source create receipt joins complete CID/argv')
    H.inspect_actual(C.obj(s['inspect_ref']),expected_id=owned['cid'],expected_image=C.IMAGE,expected_argv=want,
        source_root=stage['source_root'],suite_root=stage['suite_root'],input_root=stage['input_root'])
    for path,sha in v['source_input_before'].items():C.checked(dict(path=path,sha256=sha))
    return dict(schema='bole.independent-HE-runtime-isolation-diagnostic/v2',owner_ref=owner_ref,observation=observation,
        inherited_owner_lock_evidence_joined=True,inherited_lock_ref=s['inherited_lock_ref'],
        actual_diagnostic_evidence_joined=True,original_guard_passed=observation['original_runtime_guard']['passed'],
        full_software_qualification_accepted=False,network_safety_accepted=False,generated_code_executed=False,NPU=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--consume',action='store_true');p.add_argument('--owner-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.consume:print('{"enabled":false,"full_software_qualification_accepted":false,"NPU":false}');return 0
    C.need(a.owner_ref and a.output,'explicit completed actual diagnostic and new readback output')
    print(json.dumps(C.write(a.output,consume(json.loads(a.owner_ref)))));return 0


if __name__=='__main__':raise SystemExit(main())
