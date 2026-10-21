"""Independent actual bytes/identity/ACK reader. Never runs HE or imports NumPy."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import preflight_contract as T
import main_quiescence as Q
import lock_evidence as L
import he_policy as H
import he_network_guard as G

MARKER='BOLE_HE_OFFICIAL_V2 '
EVAL_SHA='e926d5e9b8f1ec040096cd5952e8cf79f8dc0b7fb80ba6667ce604ffea0397bc'
EXEC_SHA='79901c6f5b59701c465b164aed290fa53abc35abc80a5378fc10f4dac1f9a84c'


def readset(ir,x,prior):
    refs={}
    def add(r):
        a=C.ref(C.checked(r));refs[a['path']]=a
    stage=C.obj(x['stage_ref']);old=prior['stage']
    C.need(stage['original_stage_ref']==prior['stage_ref']and stage['original_task_source_ref']==prior['root_source_ref']
        and stage['suite_root']==old['suite_root']and stage['source_root']==str(P/'public/source')and stage['input_root']==str(P/'public/inputs')
        and C.obj(stage['capsule_ref'])==C.obj(old['capsule_ref'])and C.obj(stage['inputs_ref'])==C.obj(old['inputs_ref'])
        and C.obj(stage['capsule_ref'])['authority_sha256']==x['authority_ref']['sha256'],
        'actual exact unchanged prior public capsule/input provenance under new explicit source leaf')
    for r in(ir,*x['files'].values(),*x['data_files'].values(),*x['helper_refs'],*prior['refs'],x['authority_ref'],
             x['G1_source_ref'],x['G1_owner_ref'],x['G1_bundle_ref'],x['G1_independent_ref'],x['dependency_copy_ref'],
             *T.stage_readset(x['stage_ref']),*Q.readset(x['main_quiescence_ref'],authority_ref=x['authority_ref'])):add(r)
    for name in T.PUBLIC:add(C.ref(P/name))
    for row in C.obj(x['dependency_copy_ref'])['files'].values():add(row['copied_ref'])
    return list(refs.values())


def parse(text,stage):
    C.need(type(text)is str and len(text.encode())<=2**20,'bounded actual import-only stdout')
    rows=[line[len(MARKER):]for line in text.splitlines()if line.startswith(MARKER)]
    C.need(len(rows)==1,'exactly one original worker preflight result')
    v=json.loads(rows[0]);cap=C.obj(stage['capsule_ref'])
    C.need(v['schema']=='bole.actual-HE-official-sandbox-result/v2'and v['mode']=='preflight'
        and v['root_source_sha256']==stage['original_task_source_ref']['sha256']and v['capsule_sha256']==stage['capsule_ref']['sha256']
        and v['input_sha256']==stage['inputs_ref']['sha256']and v['authority_sha256']==cap['authority_sha256']
        and v['official_evaluation_sha256']==EVAL_SHA and v['official_execution_sha256']==EXEC_SHA
        and all(v[k]is False for k in('generated_code_executed','task_score_produced','task_accuracy_accepted','model_ready','NPU'))
        and not({'rows','component_score','component_scores','control_discrimination_pass','elapsed_seconds'}&set(v)),
        'same exact original evaluator imports with no evaluate call, code snippets or score')
    py=v['runtime_identity'];e=C.obj(C.ref(P/'DEPENDENCY_EXPECTED.json'))
    C.need(py['python_executable']in('/usr/local/python3.12.13/bin/python3','/usr/local/python3.12.13/bin/python3.12')
        and type(py['python_version'])is str and 0<len(py['python_version'])<=2048
        and py['python_version'].split()[0]=='3.12.13'
        and type(py['numpy_version'])is str and py['numpy_version']=='1.26.4'
        and type(py['tqdm_version'])is str and 0<len(py['tqdm_version'])<=128 and py['tqdm_version']!='UNKNOWN',
        'actual bounded Python/NumPy/tqdm identities; no derived successful import from filesystem existence')
    for key,name in(('numpy_source','numpy_init.py'),('tqdm_source','tqdm_init.py')):
        want=e['files'][name];r=py[key]
        C.need(r==dict(path=want['installed_path'],bytes=want['copied_ref']['bytes'],sha256=want['copied_ref']['sha256']),
            'actual imported real library source matches whole same-image copy '+key)
    return v


def admission(v,binding,proof,guard=G):
    a=v['network_admission'];r=a['ready'];facts=r['facts'];predicate=guard.validate(facts)
    guard.validate(a['after_ack_facts']);guard.validate_ack(a['ack'],r)
    C.need(a['before_executor_host_ack_verified']is True and r['predicate']==predicate
        and all(a['after_ack_facts'][k]==facts[k]for k in('guest','net_namespace')),'actual original pre-import READY/ACK and stable private guest')
    sha=hashlib.sha256(guard.canonical(a['ack'])+b'\n').hexdigest();ack=C.obj(proof['ack_ref']);ns=C.obj(proof['namespace_ref']);pub=C.obj(proof['publication_ref'])
    C.need(proof['schema']=='bole.actual-HE-host-pre-executor-network-admission/v1'and proof['before_executor_ack_issued']is True
        and C.obj(proof['binding_ref'])==binding and C.obj(proof['ready_ref'])==r and ack==a['ack']
        and C.ref(C.checked(proof['ack_ref']))['sha256']==a['ack_sha256']==sha,'independently reopened complete actual ACK/READY bytes')
    guest=ns['namespaces']['guest'];host=ns['namespaces']['owner'];init=ns['namespaces']['host_init']
    C.need(binding['container_id']==ack['container_id']==ns['container_id']and binding['uid']==65534 and binding['Devices']==[]
        and binding['host_pid']==ack['owned_host_pid']==ns['bound_guest_host_pid']==guest['pid']
        and binding['start_ticks']==ack['owned_start_ticks']==ns['bound_guest_start_ticks']==guest['start_ticks']
        and facts['guest']==dict(pid=binding['guest_pid'],start_ticks=binding['start_ticks'])
        and facts['net_namespace']==dict(link=guest['link'],**guest['file_identity'])
        and ack['host_namespaces']==dict(owner=host,host_init=init)and init['pid']==1
        and host['file_identity']==init['file_identity']and guest['file_identity']!=host['file_identity']
        and ns['comparisons']==dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False),
        'actual bound owned guest lifetime and distinct private network namespace before real imports')
    C.need(pub['container_id']==binding['container_id']and pub['owned_host_pid']==binding['host_pid']and pub['owned_start_ticks']==binding['start_ticks']
        and pub['namespace_before']==binding['program']['namespaces']and pub['ack_uid']==0 and pub['ack_mode']==0o444
        and pub['ack_sha256']==sha and pub['ack_bytes']==C.ref(C.checked(proof['ack_ref']))['bytes']
        and all(pub[k]is True for k in('directory_nofollow','new_file_exclusive','complete_data_before_atomic_link','no_added_mounts','no_sockets_or_ioctls_or_setns')),
        'source-owned root-only atomic ACK in same pinned private tmpfs')
    fields=pub['tmp_mountinfo'].split();i=fields.index('-');major,minor=map(int,fields[2].split(':'))
    C.need(fields[3:5]==['/','/tmp']and fields[i+1]=='tmpfs'and{'rw','nosuid','nodev','noexec'}<=set(fields[5].split(','))
        and(major,minor)==(G.os.major(pub['tmp_identity']['device']),G.os.minor(pub['tmp_identity']['device']))
        and pub['ack_file_identity']['device']==pub['tmp_identity']['device']and pub['ack_file_identity']['inode']>0,
        'actual ACK inode and private tmpfs mount identity')
    return True


def consume(owner_ref):
    owner=C.obj(owner_ref);x=T.inputs(owner['inputs_ref'],clock=False);s=owner['summary'];stage=C.obj(x['stage_ref'])
    C.need(Path(owner_ref['path'])==Path(x['output_root'])/'RESULT.json'and owner['schema']=='bole.actual-HE-dependency-preflight-owner/v1'
        and owner['primary']is None and owner['secondary']==[]and owner['dependency_preflight_complete']is True
        and owner['source_input_before']and owner['source_input_before']==owner['source_input_after']
        and owner['private_namespace_restored_by_identity']is True
        and all(owner[k]is False for k in('evaluator_called','generated_code_executed','task_score_produced','full_software_qualification_accepted','model_ready','NPU')),
        'complete source-equal retired import-only preflight; never full CPU qualification')
    prior=T.predecessor(x['previous_CPU_owner_ref'],x['previous_HE_owned_ref'],x['previous_HE_release_ref'])
    refs=readset(owner['inputs_ref'],x,prior)
    C.need(owner['source_input_before']=={r['path']:r['sha256']for r in refs},'all exact current code/input/evidence bytes independently reopened')
    policy=Q.policy(x['main_quiescence_ref'],authority_ref=x['authority_ref']);lock=L.validate(C.obj(s['inherited_lock_ref']),x['main_quiescence_ref'],policy['serial_schedule']['external_lock_path'])
    C.need(lock['owner_pid']==owner['actual_host_pid']and lock['owner_start_ticks']==owner['actual_host_start_ticks'],'whole inherited lock matches actual owner lifetime')
    v=parse(C.checked(s['logs_ref']).read_text(),stage);C.need(v==C.obj(s['preflight_ref']),'raw original worker preflight and saved value agree')
    b=C.obj(s['binding_ref']);o=C.obj(s['owned_ref']);cmd=H.argv(o['name'],C.IMAGE,stage['source_root'],stage['suite_root'],stage['input_root'],stage['capsule_ref']['sha256'],'preflight')
    C.need(o['cid']==b['container_id']and o['source']==owner['inputs_ref']and o['guest_cpus']==[145]
        and o['create_argv']==cmd==C.obj(s['create_argv_ref'])and b['argv']==['python3','-I','-B','/source/he_worker.py','--preflight','--capsule-sha256',stage['capsule_ref']['sha256']],
        'actual source/fullCID/CPU145/exact env-i preflight entry identity')
    create=C.obj(o['create_receipt']);C.need(create['requested_argv']==cmd and create['exit_code']==0 and create['stdout'].strip()==o['cid'],'actual original create receipt')
    py=b['program'];want=C.obj(C.ref(P/'DEPENDENCY_EXPECTED.json'))['prior_binding']['executable']
    C.need(py['expected_namespace_executable']==py['actual_namespace_executable']=='/usr/local/python3.12.13/bin/python3.12'
        and py['executable']['bytes']==want['bytes']and py['executable']['sha256']==want['sha256']
        and b['cpu']['effective_cpus']==[145]and b['cpu']['effective_capacity']==1 and b['memory']['effective_bytes']==2*C.GIB,
        'actual loaded whole Python312 binary and actual oneCPU/twoGiB ancestry')
    inspect=C.obj(s['inspect_ref']);C.need(inspect[0]['Name']=='/'+o['name'],'same actual exact owned name')
    H.inspect_actual(inspect,expected_id=o['cid'],expected_image=C.IMAGE,expected_argv=cmd,
        source_root=stage['source_root'],suite_root=stage['suite_root'],input_root=stage['input_root'])
    wait=C.obj(s['wait_receipt']);C.need(wait['exit_code']==0 and wait['stdout'].strip()=='0'
        and wait['requested_argv']==['/usr/bin/docker','wait',o['cid']],'actual complete preflight wait0 receipt')
    logs=C.obj(s['logs_receipt']);C.need(logs['requested_argv']==['/usr/bin/docker','logs',o['cid']]and logs['exit_code']==0
        and logs['stdout']+logs['stderr']==C.checked(s['logs_ref']).read_text(),'actual complete raw docker logs source')
    admission(v,b,C.obj(s['network_admission_ref']))
    release=C.obj(s['release_ref']);C.need(release['container']==o['cid']and release['stopped']is True and release['retained']is True
        and release['deleted']is False and release['errors']==[],'actual exact import-only sandbox stopped retained')
    after=C.obj(release['after_inspect']);rows=json.loads(after['stdout']);C.need(after['exit_code']==0 and len(rows)==1
        and rows[0]['Id']==o['cid']and rows[0]['Image']==C.IMAGE and not rows[0]['State']['Running']and rows[0]['State']['Pid']==0
        and not rows[0].get('ExecIDs'),'actual stopped lifecycle readback')
    return dict(schema='bole.independent-HE-dependency-preflight/v1',owner_ref=owner_ref,inputs_ref=owner['inputs_ref'],
        actual_dependency_and_official_module_imports_verified=True,actual_before_import_network_ACK_verified=True,
        inherited_owner_lock_evidence_joined=True,actual_stopped_retained=True,runtime_identity=v['runtime_identity'],
        evaluator_called=False,generated_code_executed=False,task_score_produced=False,
        full_software_qualification_accepted=False,model_ready=False,NPU=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--consume',action='store_true');p.add_argument('--owner-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.consume:print('{"enabled":false,"qualified":false,"NPU":false}');return 0
    C.need(a.owner_ref and a.output,'actual owner and new independent output required')
    print(json.dumps(dict(independent_ref=C.write(a.output,consume(json.loads(a.owner_ref))),qualified=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
