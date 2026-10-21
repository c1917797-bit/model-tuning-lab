"""Independent CPU reader reopens source/raw data, repeats decode and checks HE owner evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import he_policy as H
import he_worker as W
import he_network_guard as G
import stage_he as T


def staged(source_ref,stage_ref,grade=None):
    m=C.source(source_ref);s=C.obj(stage_ref)
    C.need(s['schema']=='bole.he-sandbox-stage/v1'and s['source_ref']==source_ref
           and s['effective_inputs_ref']==m['effective_inputs_ref']and s['image_id']==m['image_id'],
           'same independently reopened HE stage/root/inputs/image')
    source=Path(s['source_root']);inputs=Path(s['input_root']);suite=Path(s['suite_root'])
    C.need({str(p.relative_to(source))for p in source.rglob('*')if p.is_file()}=={'he_worker.py','task_contract.py','he_network_guard.py','HE_NETWORK_PROTOCOL.json','AUTHORITY.json','HE_CAPSULE.json',*[str(p.relative_to(P))for p in sorted((P/'network_uapi').glob('*.h'))]}
           and set(p.name for p in inputs.iterdir())=={'samples.jsonl','problems.jsonl','INPUTS.json'},'only exact public capsule/input files mounted')
    C.need(all(not p.is_symlink()for p in source.rglob('*'))
        and {str(p.relative_to(source))for p in source.rglob('*')if p.is_dir()}=={'network_uapi'},
        'only explicitly declared public source directory; no hidden directory/symlink exposure')
    cap=C.obj(s['capsule_ref']);index=C.obj(s['inputs_ref'])
    C.need(Path(s['capsule_ref']['path'])==source/'HE_CAPSULE.json'
           and Path(s['inputs_ref']['path'])==inputs/'INPUTS.json','current exact stage locations')
    files=[]
    for name in('he_worker.py','task_contract.py','he_network_guard.py','HE_NETWORK_PROTOCOL.json',*[str(p.relative_to(P))for p in sorted((P/'network_uapi').glob('*.h'))],'AUTHORITY.json'):
        actual=C.ref(source/name);expected=m['authority_ref']if name=='AUTHORITY.json'else m['files'][name]
        C.need((actual['bytes'],actual['sha256'])==(expected['bytes'],expected['sha256']),'unchanged capsule source/authority')
        files.append(T.slim(actual,name))
    package=C.obj(m['human_eval_package_ref']);original_suite=Path(package['dataset_ref']['path']).parent.parent
    C.need(s['original_suite_root']==str(original_suite)and suite==source.parent/'suite'
           and inputs==source.parent/'inputs'and source==source.parent/'source'
           and Path(stage_ref['path'])==source.parent/'STAGE.json','one new dedicated minimal public stage')
    official_files=[]
    for reference in package['files']+[package['dataset_ref']]:
        relative=str(C.checked(reference).relative_to(original_suite));actual=C.ref(suite/relative)
        C.need((actual['bytes'],actual['sha256'])==(reference['bytes'],reference['sha256']),'whole unchanged relocated public official package')
        official_files.append(T.slim(actual,relative))
    C.need(all(not p.is_symlink()for p in suite.rglob('*'))
           and {str(p.relative_to(suite))for p in suite.rglob('*')if p.is_file()}=={r['relative']for r in official_files},
           'only original public package files, no hidden host/secret file exposure')
    C.need(cap==dict(schema='bole.he-public-source-capsule/v1',root_source_sha256=source_ref['sha256'],
        authority_sha256=m['authority_ref']['sha256'],files=files,official_package_files=official_files,
        official_repository=package['repository'],official_commit=package['commit']),'whole exact independent public source capsule replay')
    samples=W.rows(inputs/'samples.jsonl');problems=W.rows(inputs/'problems.jsonl')
    if s['kind']=='controls':
        C.need(grade is None and s['grades_ref']is None,'controls independent of task outputs')
        with gzip.open(C.checked(package['dataset_ref']),'rt',encoding='utf8')as stream:problem=json.loads(next(stream))
        expected_samples=[dict(task_id=problem['task_id'],completion=value)for value in(
            problem['canonical_solution'],"    raise AssertionError('deliberately wrong software control')\n",
            '    while True:\n        pass\n')]
        C.need(samples==expected_samples and problems==[problem]and s['phase']=='software-controls','exact correct/wrong/timeout official-problem controls')
    else:
        C.need(s['kind']=='tasks'and grade is not None and samples==grade['human_eval_samples']
               and problems==grade['human_eval_problems']and s['phase']==grade['phase'],'exact independently transformed actual generated HE samples')
    expected_files=[T.slim(C.ref(inputs/name),name)for name in('samples.jsonl','problems.jsonl')]
    C.need(index==dict(schema='bole.he-official-staged-inputs/v1',kind=s['kind'],phase=s['phase'],
        root_source_sha256=source_ref['sha256'],capsule_sha256=s['capsule_ref']['sha256'],
        authority_sha256=m['authority_ref']['sha256'],files=expected_files,
        case_labels=['correct','wrong','timeout']if s['kind']=='controls'else None),'whole exact staged input manifest replay')
    return m,s,index,samples


def he_result(source_ref,stage_ref,owner_ref,grade=None):
    m,s,index,samples=staged(source_ref,stage_ref,grade);owner=C.obj(owner_ref)
    C.need(owner['schema']=='bole.actual-HE-sandbox-owner-evidence/v2'and owner['stage_ref']==stage_ref,
           'actual exact sandbox owner evidence, never caller boolean approval')
    command=H.argv(owner['name'],m['image_id'],s['source_root'],s['suite_root'],s['input_root'],s['capsule_ref']['sha256'],s['kind'])
    C.need(C.obj(owner['create_argv_ref'])==command and C.checked(owner['created_id_ref']).read_text().strip()==owner['container_id'],
           'actual create argv/CID bytes')
    inspect=C.obj(owner['inspect_ref'])
    C.need(inspect[0]['Name']=='/'+owner['name'],'same owned unique actual sandbox name')
    isolated=H.inspect_actual(inspect,expected_id=owner['container_id'],expected_image=m['image_id'],
        expected_argv=command,source_root=s['source_root'],suite_root=s['suite_root'],input_root=s['input_root'])
    C.need(C.checked(owner['wait_ref']).read_text().strip()=='0','actual completed docker wait exit status')
    lines=C.checked(owner['stdout_ref']).read_text().splitlines();markers=[line for line in lines if line.startswith(W.MARKER)]
    C.need(len(markers)==1,'one exact actual official HE result marker')
    value=json.loads(markers[0][len(W.MARKER):])
    C.need(value['schema']=='bole.actual-HE-official-sandbox-result/v2'and value['mode']==s['kind']
           and value['root_source_sha256']==source_ref['sha256']and value['capsule_sha256']==s['capsule_ref']['sha256']
           and value['input_sha256']==s['inputs_ref']['sha256']and value['authority_sha256']==m['authority_ref']['sha256']
           and value['official_evaluation_sha256']==W.EVAL_SHA and value['official_execution_sha256']==W.EXEC_SHA
           and value['generated_code_executed']is True and value['task_accuracy_accepted']is False
           and value['model_ready']is False and value['NPU']is False,'same original official executor/source/input result identity')
    admission=value['network_admission'];ready=admission['ready'];G.validate(ready['facts']);G.validate(admission['after_ack_facts']);G.validate(value['network_after'])
    C.need(admission['before_executor_host_ack_verified']is True and ready['predicate']==G.validate(ready['facts'])
        and ready['capsule_sha256']==s['capsule_ref']['sha256']and ready['root_source_sha256']==source_ref['sha256'],'actual pre-executor network facts and host ACK source join')
    G.validate_ack(admission['ack'],ready)
    C.need(hashlib.sha256(G.canonical(admission['ack'])+b'\n').hexdigest()==admission['ack_sha256'],'exact canonical host ACK bytes')
    proof=C.obj(owner['network_admission_ref']);binding=C.obj(proof['binding_ref']);namespace=C.obj(proof['namespace_ref'])
    publication=C.obj(proof['publication_ref']);ack=C.obj(proof['ack_ref'])
    interpreter=C.obj(m['files']['HE_PYTHON_PROTOCOL.json']);runtime=value['runtime_identity'];program=binding['program']
    C.need(runtime['python_executable']in('/usr/local/python3.12.13/bin/python3','/usr/local/python3.12.13/bin/python3.12')
        and runtime['python_version'].split()[0]==interpreter['python_version']
        and runtime['numpy_version']==interpreter['numpy_version']and runtime['tqdm_version']==interpreter['tqdm_version']
        and {k:runtime[k]for k in('numpy_source','tqdm_source')}==interpreter['imported_sources']
        and program['expected_namespace_executable']==program['actual_namespace_executable']==interpreter['namespace_interpreter']
        and program['executable']['bytes']==interpreter['python_executable_bytes']
        and program['executable']['sha256']==interpreter['python_executable_sha256'],
        'actual whole Python312 executable and actual real NumPy/tqdm sources match isolated import preflight profile')
    C.need(proof['schema']=='bole.actual-HE-host-pre-executor-network-admission/v1'and proof['before_executor_ack_issued']is True
        and C.obj(proof['ready_ref'])==ready and ack==admission['ack']
        and C.ref(C.checked(proof['ack_ref']))['sha256']==admission['ack_sha256'],
        'independently reopened actual READY and atomically published exact ACK bytes')
    facts=ready['facts'];guest=namespace['namespaces']['guest'];host=namespace['namespaces']['owner'];init=namespace['namespaces']['host_init']
    C.need(binding['container_id']==namespace['container_id']==ack['container_id']==owner['container_id']
        and binding['host_pid']==namespace['bound_guest_host_pid']==guest['pid']==ack['owned_host_pid']
        and binding['start_ticks']==namespace['bound_guest_start_ticks']==guest['start_ticks']==ack['owned_start_ticks']
        and binding['uid']==65534 and binding['Devices']==[]
        and facts['guest']==dict(pid=binding['guest_pid'],start_ticks=binding['start_ticks'])
        and facts['net_namespace']==dict(link=guest['link'],**guest['file_identity'])
        and ack['host_namespaces']==dict(owner=host,host_init=init)
        and host['file_identity']==init['file_identity']and guest['file_identity']!=host['file_identity']
        and init['pid']==1 and namespace['comparisons']==dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False),
        'actual strong UID/fullCID/process lifetime and private guest-vs-host namespace join before executor')
    C.need(publication['container_id']==owner['container_id']and publication['owned_host_pid']==binding['host_pid']
        and publication['owned_start_ticks']==binding['start_ticks']and publication['namespace_before']==binding['program']['namespaces']
        and publication['ack_uid']==0 and publication['ack_mode']==0o444
        and publication['ack_sha256']==admission['ack_sha256']
        and publication['ack_bytes']==C.ref(C.checked(proof['ack_ref']))['bytes']
        and all(publication[k]is True for k in('directory_nofollow','new_file_exclusive','complete_data_before_atomic_link',
            'no_added_mounts','no_sockets_or_ioctls_or_setns')),
        'actual source-owned root-only ACK in pinned private tmpfs; no mount/resource/capability change')
    mount=publication['tmp_mountinfo'].split();separator=mount.index('-');major,minor=map(int,mount[2].split(':'))
    C.need(mount[3:5]==['/','/tmp']and mount[separator+1]=='tmpfs'
        and{'rw','nosuid','nodev','noexec'}<=set(mount[5].split(','))
        and(major,minor)==(G.os.major(publication['tmp_identity']['device']),G.os.minor(publication['tmp_identity']['device']))
        and publication['ack_file_identity']['device']==publication['tmp_identity']['device']
        and publication['ack_file_identity']['inode']>0,'actual ACK file and pinned private tmpfs mount device identity')
    C.need(all(v['guest']==facts['guest']and v['net_namespace']==facts['net_namespace']
        for v in(admission['after_ack_facts'],value['network_after'])),'same isolated guest before and after official evaluation')
    rows=value['rows']
    C.need(len(rows)==len(samples)and all(r['task_id']==sample['task_id']and r['completion']==sample['completion']
           and type(r['passed'])is bool and type(r['result'])is str for r,sample in zip(rows,samples)),
           'all actual official result rows and exact unmodified completion bytes')
    C.need(type(value['elapsed_seconds'])in(int,float)and value['elapsed_seconds']>=0,'actual bounded evaluator duration')
    if s['kind']=='controls':
        C.need([r['passed']for r in rows]==[True,False,False]and rows[2]['result']=='timed out'
               and value['case_labels']==['correct','wrong','timeout']and value['control_discrimination_pass']is True
               and value['task_score_produced']is False and 'component_score'not in value,'software-control discrimination, never task score')
        return dict(kind='controls',official_executor_controls_pass=True,owner=isolated,task_score_produced=False)
    score=sum(r['passed']for r in rows)/len(rows)
    C.need(value['count']==len(rows)and value['component_score']==score and value['task_score_produced']is True,
           'independent complete-count official HE pass@1')
    return dict(kind='tasks',component_score=score,correct=sum(r['passed']for r in rows),count=len(rows),owner=isolated,
                task_score_produced=True,actual_official_executor_rows_verified=True)


def decoder_smoke(source_ref,reference):
    import decoder as D
    import provenance as V
    m=C.source(source_ref,seconds=300);value=C.obj(reference);effective=C.verify_inputs(m)
    tok,identity=D.create(m,effective)
    expected=dict(source=source_ref,rendered_inputs_ref=m['rendered_inputs_ref'],effective_inputs_ref=m['effective_inputs_ref'],
        decoder=identity,result=D.controls(tok),coverage=V.run(m,effective,tok),
        actual_frozen_tokenizer_executed=True,same_image_owner_verified=False,model_ready=False,task_ready=False,performance_ready=False)
    C.need(value==expected,'independently rerun complete actual tokenizer-only source/gold/template/controls')
    return dict(actual_frozen_decoder_controls_pass=True,complete_input_provenance_pass=True,
                counts=value['coverage']['counts'],task_score_produced=False)


def run(source_ref,stage_ref,owner_ref,decoder_ref,grades_ref=None):
    m=C.source(source_ref,seconds=300);C.cpu_runtime();grade=None
    decoder_result=decoder_smoke(source_ref,decoder_ref)
    if grades_ref is not None:
        import score_tokens as S
        grade=C.obj(grades_ref);C.need(grade==S.replay(source_ref,grade['raw_ref']),
            'independent original raw ID decoding/gold/extraction replay matches producer grades exactly')
    he=he_result(source_ref,stage_ref,owner_ref,grade)
    if grade is not None:
        C.need(C.obj(stage_ref)['grades_ref']==grades_ref and he['kind']=='tasks','same actual task grade and HE stage')
    C.current_authority(m['authority_ref']);C.cpu_runtime()
    result=dict(schema='bole.independent-three-task-component-result/v1',source_ref=source_ref,decoder_smoke_ref=decoder_ref,
        grades_ref=grades_ref,HE_stage_ref=stage_ref,HE_owner_ref=owner_ref,decoder=decoder_result,HumanEval=he,
        independent_component_checks_pass=True,software_controls_only=grade is None,
        CPU_same_image_owner_join_accepted=False,worker_lifecycle_accepted=False,normal_EOS_native_worker_proof_accepted=False,
        BOLE_activation_accepted=False,formal_task_accuracy_accepted=False,model_ready=False,
        performance_ready=False,NPU=False)
    if grade is not None:result.update(phase=grade['phase'],arm=grade['arm'],counts=grade['counts'],
        component_scores=dict(grade['component_scores'],HumanEval=he['component_score']),
        component_correct=dict(grade['correct'],HumanEval=he['correct']),
        finish_reason_counts=grade['finish_reason_counts'])
    return result


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for name in('source-ref','he-stage-ref','he-owner-ref','decoder-smoke-ref','grades-ref'):p.add_argument('--'+name)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"formal_task_accuracy_accepted":false}');return 0
    C.need(a.source_ref and a.he_stage_ref and a.he_owner_ref and a.decoder_smoke_ref and a.output,'explicit actual independent evidence set/output')
    values=[json.loads(x)for x in(a.source_ref,a.he_stage_ref,a.he_owner_ref,a.decoder_smoke_ref)]
    result=run(*values,None if a.grades_ref is None else json.loads(a.grades_ref))
    print(json.dumps(C.write(a.output,result)));return 0


if __name__=='__main__':raise SystemExit(main())
