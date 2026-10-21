"""Only the bounded HE import preflight. No tokenizer or model dispatch."""
import json
from pathlib import Path
import owner_common as C
import main_quiescence as Q

P=Path(__file__).resolve().parent
FILES=('owner_common.py','owner_namespace.py','he_owned.py','main_quiescence.py','lock_evidence.py',
       'network_evidence.py','he_admission.py','he_policy.py','binding.py','preflight_contract.py',
       'prepare_preflight.py','preflight_host.py','preflight_evidence.py','test_preflight_pure.py')
PUBLIC=('he_worker.py','task_contract.py','he_network_guard.py','HE_NETWORK_PROTOCOL.json',
        'network_uapi/if.h','network_uapi/if_arp.h','network_uapi/route.h','network_uapi/ipv6_route.h')
DATA=('DEPENDENCY_EXPECTED.json','PREVIOUS_CPU_EXPECTED.json','CPU12_ACTUAL_REFS.json')


def predecessor(owner_ref,HE_owned_ref,HE_release_ref):
    refs={}
    def add(r):
        a=C.ref(C.checked(r));refs[a['path']]=a;return a
    def obj(r):add(r);return C.obj(r)
    actual=obj(C.ref(P/'CPU12_ACTUAL_REFS.json'))
    for reference in actual.values():add(reference)
    C.need(add(owner_ref)==actual['RESULT.json']and add(HE_owned_ref)==actual['he-controls/OWNED.json']
        and add(HE_release_ref)==actual['he-controls/cleanup.json'],'exact supplied actual CPU12 owner/HE identity/retirement primary refs')
    e=obj(C.ref(P/'PREVIOUS_CPU_EXPECTED.json'));r=add(owner_ref)
    C.need((r['bytes'],r['sha256'])==(e['owner']['bytes'],e['owner']['sha256']),'exact actual CPU12 failed complete owner, never a prerequisite pass')
    v=obj(owner_ref);x=obj(v['inputs_ref']);s=v['summary']
    C.need(v['schema']=='bole.actual-finite-task-CPU-owner/v4'and v['primary']['phase']=='he-controls'
        and v['secondary']==[]and v['source_input_before']and v['source_input_before']==v['source_input_after']
        and v['private_namespace_restored_by_identity']is True and v['source_image_CPU_owner_software_controls_verified']is False
        and x['image_id']==C.IMAGE and x['qualification_profile']=='full-v012-public-backend-network-isolation/v3',
        'actual source-equal retired failed full qualification; no successful HE or independent phase asserted')
    C.need(set(x['files'])==set(e['CPU_source']),'complete actual CPU12 executable source inventory')
    for name,reference in x['files'].items():
        a=add(reference);want=e['CPU_source'][name]
        C.need((a['bytes'],a['sha256'])==(want['bytes'],want['sha256'])
            and v['source_input_before'].get(a['path'])==a['sha256'],'actual byteexact CPU12 source '+name)
    child=obj(s['CPU']['report']);p=child['payload'];release=obj(s['CPU_release']);decoder=obj(p['decoder_ref'])
    controls=obj(actual['cpu-preflight/SOFTWARE-CONTROLS.json']);network=obj(actual['cpu-preflight/NETWORK-GUARD-CONTROLS.json'])
    C.need(controls['pure_tests']==43 and controls['returncode']==0 and controls['generated_code_executed']is False
        and controls['task_score_produced']is False and network['pure_tests']==20 and network['returncode']==0
        and network['network_or_evaluator_executed']is False,'actual original43 and20 network software controls passed, not HE evaluation')
    C.need(child['inputs_ref']==v['inputs_ref']and child['mode']=='prepare-decode'and child['readset_before']==child['readset_after']
        and p['pure_controls_pass']is True and p['network_guard_controls_pass']is True and p['all_input_source_gold_template_verified']is True
        and p['counts']=={'GSM8K':1319,'HumanEval':164,'MMLU':14042}and p['forbidden_import_attempts']==[]
        and decoder['coverage']['complete_official_source_gold_and_template_coverage']is True
        and decoder['coverage']['counts']==p['counts']and release['stopped']is True and release['retained']is True
        and release['errors']==[],'actual successful complete firstCPU phase and retained cleanup, without repeating15525')
    stage=obj(p['HE_stage_ref']);cap=obj(stage['capsule_ref']);root=obj(p['bound_task_source_ref'])
    C.need(stage['schema']=='bole.he-sandbox-stage/v1'and stage['kind']=='controls'and stage['image_id']==C.IMAGE
        and stage['source_ref']==p['bound_task_source_ref']and cap['root_source_sha256']==p['bound_task_source_ref']['sha256'],
        'actual immutable original control capsule/source, no task outputs used')
    for name in PUBLIC:
        a=add(dict(path=str(Path(stage['source_root'])/name),**e['task_files'][name]))
        C.need(root['files'][name]['sha256']==a['sha256'],'exact original staged public worker/guard/UAPI')
    for directory,entries in((stage['source_root'],cap['files']),(stage['suite_root'],cap['official_package_files'])):
        for row in entries:
            q=Path(row['relative']);C.need(not q.is_absolute()and'..'not in q.parts,'ordinary bounded public staged path')
            add(dict(path=str(Path(directory)/q),bytes=row['bytes'],sha256=row['sha256']))
    index=obj(stage['inputs_ref']);C.need(index['kind']=='controls'and index['case_labels']==['correct','wrong','timeout'],
        'original known controls data only, never task samples')
    for row in index['files']:add(dict(path=str(Path(stage['input_root'])/row['relative']),bytes=row['bytes'],sha256=row['sha256']))
    h=obj(HE_owned_ref);hr=obj(HE_release_ref);binding=obj(s['HE_binding']);admission=obj(s['HE_network_admission'])
    C.need(h['cid']==binding['container_id']==hr['container']and h['image']==C.IMAGE and h['guest_cpus']==[145]
        and h['source']==p['bound_task_source_ref']and binding['uid']==65534 and binding['Devices']==[]
        and hr['stopped']is True and hr['retained']is True and hr['errors']==[]and hr['deleted']is False,
        'failed HE exact owned identity and actual stopped retained cleanup')
    for key in('binding_ref','namespace_ref','ready_ref','ack_ref','publication_ref'):add(admission[key])
    C.need(admission['binding_ref']==s['HE_binding']and admission['before_executor_ack_issued']is True,
        'actual CPU12 before-executor network ACK existed; no claim official imports succeeded')
    create=obj(h['create_receipt']);C.need(create['exit_code']==0 and create['stdout'].strip()==h['cid']
        and create['requested_argv']==h['create_argv'],'actual prior HE fullCID/create identity')
    for key in('before_inspect','after_inspect','stop_receipt'):
        if hr.get(key):add(hr[key])
    after=obj(hr['after_inspect']);actual=json.loads(after['stdout'])
    C.need(len(actual)==1 and actual[0]['Id']==h['cid']and actual[0]['Name']=='/'+h['name']
        and actual[0]['Image']==C.IMAGE and not actual[0]['State']['Running']and actual[0]['State']['Pid']==0
        and not actual[0].get('ExecIDs'),'actual retired prior HE process; no guessed future retirement')
    return dict(refs=list(refs.values()),stage=stage,stage_ref=p['HE_stage_ref'],root_source_ref=p['bound_task_source_ref'])


def inputs(reference,*,clock=True):
    x=C.obj(reference)
    C.need(x['schema']=='bole.HE-dependency-preflight-inputs/v1'and x['default_enabled']is False and x['diagnostic_only']is True
        and x['image_id']==C.IMAGE and x['phase_seconds']==3600 and x['cleanup_seconds']==180
        and x['HE_seconds']==90 and x['CPU']==145 and x['host_CPU']==166 and x['HE_memory_bytes']==2*C.GIB
        and x['summed_ancestor_CPU_budget']==7 and x['reserve_CPU_budget']==2
        and x['generated_code_executed']is False and x['full_software_qualification_accepted']is False,
        'exact finite import-only same-image nonprivileged HE profile')
    C.need(set(x['files'])==set(FILES)and set(x['data_files'])==set(DATA),'whole exact preflight closure')
    for name,r in {**x['files'],**x['data_files']}.items():C.need(C.checked(r)==P/name,'actual source-bound preflight executable/data')
    Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref'])
    if clock:C.authority(x['authority_ref'])
    return x


def stage_readset(stage_ref):
    s=C.obj(stage_ref);cap=C.obj(s['capsule_ref']);idx=C.obj(s['inputs_ref']);refs=[stage_ref,s['capsule_ref'],s['inputs_ref']]
    C.need(s['schema']=='bole.HE-dependency-preflight-stage/v1'and s['mode']=='preflight'and s['image_id']==C.IMAGE
        and cap['root_source_sha256']==s['original_task_source_ref']['sha256']and idx['root_source_sha256']==cap['root_source_sha256']
        and idx['capsule_sha256']==s['capsule_ref']['sha256'],'explicit new public-only stage with original fixed-input provenance')
    for directory,entries in((s['source_root'],cap['files']),(s['suite_root'],cap['official_package_files']),(s['input_root'],idx['files'])):
        seen=set()
        for row in entries:
            q=Path(row['relative']);C.need(not q.is_absolute()and'..'not in q.parts and str(q)not in seen,'bounded unique public staged paths');seen.add(str(q))
            r=dict(path=str(Path(directory)/q),bytes=row['bytes'],sha256=row['sha256']);C.checked(r);refs.append(r)
    for name in PUBLIC:
        a=C.ref(Path(s['source_root'])/name);b=C.ref(P/name)
        C.need((a['bytes'],a['sha256'])==(b['bytes'],b['sha256']),'original public executor/runtime byteexact')
    C.need({str(p.relative_to(s['source_root']))for p in Path(s['source_root']).rglob('*')if p.is_file()}=={*PUBLIC,'AUTHORITY.json','HE_CAPSULE.json'},
        'only explicitly declared public source files mounted')
    C.need(not any(p.is_symlink()for base in('source_root','suite_root','input_root')for p in Path(s[base]).rglob('*')),'no public stage symlinks')
    return refs
