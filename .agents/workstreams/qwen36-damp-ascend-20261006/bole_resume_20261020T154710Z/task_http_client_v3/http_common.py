"""Bounded primitive-only IO. No accelerator, inference, tokenizer or model imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
P=Path(__file__).resolve().parent
NATIVE_EXPECTED_SHA='2bb01c9d2ecf4db1790bf7e4ad3bc9dd4ee325185ea3d277a03591202a783b47'
CPU_EXPECTED_SHA='1b992ab2d3121f4382058f3ff7843591c137dc96d87f4109e570a33fcdf26713'
TASK_PACKET_MANIFEST_SHA='248fe4f5ddd17cb9bad494d05e692ba0edee95fe4cb5c78bebcb58fc0a0a2129'
CPU_PROFILE='full-v012-public-backend-network-isolation-python312/v4'
CLIENT_OPTIN_PROTOCOL='actual-client-process-source-bound-runpy/v1'
SUPPORTED_CPU_OWNER_REF=dict(path='/opt/host/vnf/austinov/run-bole-task-cpu-20261020T154710Z-v14/RESULT.json',bytes=244257,sha256='8403c75bdcdb74df6801b06c2e552fe0eec70a9053ddb663432fe4323be92dc5')
SUPPORTED_CPU_INPUTS_REF=dict(path='/opt/host/vnf/austinov/bole-task-cpu-20261020T154710Z-v14/OWNER_INPUTS.json',bytes=63022,sha256='91d364a8729efde66b9c6fa062c10fdc5f17669ab3a49639af03dc21297be394')
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
SMOKE=[('GSM8K','gsm8k-test-0000'),('GSM8K','gsm8k-test-0001'),('HumanEval','HumanEval/0'),('HumanEval','HumanEval/1'),('MMLU','mmlu-abstract_algebra-0000'),('MMLU','mmlu-abstract_algebra-0001')]
FILES=('client_entry.py','http_common.py','prepare_http.py','http_client.py','native_finish_observer.py','consume_lifecycle.py','bind_processes.py','test_http_pure.py')


def need(v,m):
    if not v:raise ValueError(m)


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()


def parse(raw):
    def pairs(xs):
        d={}
        for k,v in xs:need(k not in d,'no duplicate JSON keys');d[k]=v
        return d
    def bad(v):raise ValueError('nonfinite JSON '+v)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)


def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary whole file Ref')
    a=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    b=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns)and size==b.st_size,'stable whole bytes')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())


def checked(r):
    need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'exact Ref2/3')
    a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or r['bytes']==a['bytes']),'complete exact Ref bytes');return Path(r['path'])


def obj(r):return parse(checked(r).read_bytes())


def write(path,v):
    p=Path(path);need(p.is_absolute()and p.parent.is_dir()and not p.exists(),'new ordinary output')
    with p.open('xb')as f:f.write(canonical(v)+b'\n');f.flush();__import__('os').fsync(f.fileno())
    return ref(p)


def load(r,name):
    need(name not in sys.modules,'fresh exact source namespace')
    s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);sys.modules[name]=m
    try:s.loader.exec_module(m);checked(r)
    except BaseException:sys.modules.pop(name,None);raise
    return m


def authority(r,seconds=0):
    v=obj(r);need(v['start_epoch']<=time.time()and time.time()+seconds<v['cutoff_epoch'],'current new authority including finite full budget');return v


def source(r,seconds=0,*,native_runtime=True):
    m=obj(r);need(m['schema']=='bole.three-task-normalEOS-smoke/source/v3'and m['default_enabled']is False
        and m['prepared_only']is True and m['image_id']==IMAGE and m['phase']=='smoke'and m['request_count']==6
        and m['max_tokens']==2048 and m['minimum_context_tokens']==5199 and m['concurrency']==1
        and m['CPU_owner_profile']==CPU_PROFILE and m['task_decoder_packet_manifest_sha256']==TASK_PACKET_MANIFEST_SHA
        and m['phase_seconds']==1800 and m['request_seconds']==300 and m['raw_limit_bytes']==64*2**20,'exact bounded smoke policy')
    need(set(m['files'])==set(FILES),'complete own executable source closure')
    need(m['client_process_optin_protocol']==CLIENT_OPTIN_PROTOCOL
        and m['client_entry_ref']==m['files']['client_entry.py'],'explicit actual client-process opt-in entry/source binding')
    for n,x in m['files'].items():need(checked(x)==P/n,'current exact local source')
    if native_runtime:
        for x in m['native_sources'].values():checked(x)
    else:
        snapshots=obj(m['native_source_snapshot_manifest_ref']);need(set(snapshots)==set(m['native_sources']),'whole exact actual stopped-image source snapshots')
        for k,r in snapshots.items():
            x=ref(checked(r['snapshot_ref']));expected=m['native_sources'][k]
            need(r['runtime_ref']==expected and(x['bytes'],x['sha256'])==(expected['bytes'],expected['sha256']),'same exact native snapshot on host '+k)
    need(m['native_expected_ref']['sha256']==NATIVE_EXPECTED_SHA and checked(m['native_expected_ref'])==P/'NATIVE_SOURCE_EXPECTED.json','frozen original native source expected Ref')
    expected=obj(m['native_expected_ref']);need(expected==m['native_sources'],'same exact stopped-image source declaration')
    gr=ref(checked(m['generation_config_ref']));need((gr['bytes'],gr['sha256'])==(202,'e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e'),'exact original checkpoint generation config only')
    authority(m['authority_ref'],seconds)
    return m


def plan(r):
    m=obj(r);need(m['schema']=='bole.three-task-prompt-only-request-plan/v1'and m['phase']=='smoke'and m['arm']in{'OFF','ON'}
       and m['count']==6 and m['minimum_model_context_tokens']==5199 and m['concurrency']==1 and m['HTTP_executed']is False,'exact frozen six-case plan')
    p=checked(m['requests_ref']);need(p.stat().st_size<=2**20,'bounded prompt-only plan');rows=[parse(line)for line in p.read_bytes().splitlines()]
    need([(v['task'],v['id'])for v in rows]==SMOKE,'all six frozen smoke IDs, no substitute/cohort change')
    for r in rows:
        b=r['body'];need(set(b)=={'model','prompt','max_tokens','ignore_eos','temperature','top_p','seed','n','stream','return_token_ids'}
            and b['model']==m['model']and b['max_tokens']==2048 and b['ignore_eos']is False and b['temperature']==0
            and b['top_p']==1 and b['seed']==0 and b['n']==1 and b['stream']is False and b['return_token_ids']is True,'exact normalEOS greedy wire policy')
        ids=b['prompt'];need(type(ids)is list and 0<len(ids)<=3151 and all(type(t)is int and 0<=t<248320 for t in ids),'full uncropped token-list prompt')
        need(type(r['frozen_row_sha256'])is str and len(r['frozen_row_sha256'])==64,'row freeze identity')
    return m,rows


def CPU_status(v):
    need(v['schema']=='bole.actual-finite-task-CPU-owner/v5'and v['primary']is None and v['secondary']==[]
        and v['diagnostic_only']is False and v['qualification_profile']==CPU_PROFILE
        and v['decoder_packet_manifest_sha256']==TASK_PACKET_MANIFEST_SHA
        and v['source_image_CPU_owner_software_controls_verified']is True and v['private_namespace_restored_by_identity']is True
        and v['source_input_before']and v['source_input_before']==v['source_input_after']
        and v['NPU']is False and v['model_executed']is False and v['HTTP_executed']is False
        and v['task_score_produced']is False,'actual complete v14 same-image CPU qualification; diagnostic or planned booleans rejected')


def CPU_audit(reference,source_ref):
    p=checked(reference);need(p.stat().st_size<=4*2**20,'bounded actual full CPU import audit')
    rows=[]
    with p.open('rb')as f:
        for line in f:
            need(len(rows)<256 and len(line)<=65536,'complete bounded CPU audit ordinals')
            v=parse(line);need(v['schema']=='bole.actual-tokenizer-import-audit-event/v1'and v['ordinal']==len(rows)
                and v['event']in{'entry','import-attempt','closed'},'no denied import event in qualified CPU child')
            if v['event']=='import-attempt':need(v['payload']['module'].split('.')[0]not in{'torch_npu','vllm','vllm_ascend','triton'},'zero forbidden accelerator/inference import attempt')
            rows.append(v)
    need(len(rows)>=2 and rows[0]['event']=='entry'and rows[0]['payload']['source_ref']==source_ref
        and rows[-1]['event']=='closed'and rows[-1]['payload']['forbidden_attempts']==[]
        and rows[-1]['payload']['software_qualification_accepted']is False,'closed source-bound audit; audit alone never qualification')


def CPU_lock(value,policy,owner):
    expected=policy['serial_schedule']['external_lock_path'];identity=value['file_identity'];pid=owner['actual_host_pid']
    need(value['schema']=='bole.actual-inherited-MAIN-lock-observation/v1'and value['lock_path']==expected
        and value['owner_pid']==pid and value['owner_start_ticks']==owner['actual_host_start_ticks']
        and value['capture_phase']=='before-sandbox-create'and value['acquired_or_released_lock']is False,
        'actual owner lifetime inherited whole-owner lock observation before any create')
    def match(line):
        p=line.split()
        if len(p)!=8 or p[1:4]!=['FLOCK','ADVISORY','WRITE']or p[4]!=str(pid)or p[6:]!=['0','EOF']:return False
        try:
            a,b,c=p[5].split(':');got=dict(device_major=int(a,16),device_minor=int(b,16),inode=int(c))
        except ValueError:return False
        return got==identity
    need(len(value['proc_locks_matching_lines'])==1 and match(value['proc_locks_matching_lines'][0])
        and 1<=len(value['inherited_fds'])<=64,'actual matching current-PID exclusive kernel FLOCK and inherited FD')
    for row in value['inherited_fds']:
        need(row['link']==expected and row['file_identity']==identity and row['regular_file']is True
            and any(match(line.split(':',1)[1].strip())for line in row['fdinfo'].splitlines()if line.startswith('lock:')),
            'same existing inherited FD path/device/inode and held exclusive lock')


def CPU_HE(summary,owner,inputs,plan_source,read,add):
    he=read(summary['HE_owner_ref']);proof=read(summary['HE_network_admission'])
    need(he['schema']=='bole.actual-HE-sandbox-owner-evidence/v2'and he['network_admission_ref']==summary['HE_network_admission']
        and proof['schema']=='bole.actual-HE-host-pre-executor-network-admission/v1'and proof['before_executor_ack_issued']is True,
        'actual HE official executor owner and pre-executor host admission receipts')
    binding=read(proof['binding_ref']);ns=read(proof['namespace_ref']);ready=read(proof['ready_ref'])
    ack=read(proof['ack_ref']);publication=read(proof['publication_ref']);stage=read(he['stage_ref'])
    need(proof['binding_ref']==summary['HE_binding']and stage['source_ref']==plan_source,
        'same actual HE source/stage/binding before real control execution')
    path=Path(inputs['task_packet_root'])/'he_network_guard.py';guard_ref=ref(path)
    G=load(guard_ref,'_HTTPv3_pure_HE_guard_'+str(len(sys.modules)))
    G.verify_protocol(Path(inputs['task_packet_root']));need(ready['predicate']==G.validate(ready['facts']),
        'independent source-bound pure replay of actual pre-executor network facts')
    G.validate_ack(ack,ready)
    need(ready['root_source_sha256']==plan_source['sha256']and ready['capsule_sha256']==stage['capsule_ref']['sha256']
        and ack['container_id']==he['container_id']==binding['container_id']==ns['container_id']
        and ack['owned_host_pid']==binding['host_pid']==ns['bound_guest_host_pid']
        and ack['owned_start_ticks']==binding['start_ticks']==ns['bound_guest_start_ticks']
        and ready['facts']['guest']==dict(pid=binding['guest_pid'],start_ticks=binding['start_ticks'])
        and binding['uid']==65534 and binding['Devices']==[],
        'same actual nonce/source/capsule/fullCID/PID/start/UID/Devices namespace admission')
    rows=ns['namespaces'];host=rows['owner'];init=rows['host_init'];guest=rows['guest']
    need(host['pid']==owner['actual_host_pid']and host['start_ticks']==owner['actual_host_start_ticks']and init['pid']==1
        and host['file_identity']==init['file_identity']and guest['file_identity']!=host['file_identity']
        and guest['pid']==binding['host_pid']and guest['start_ticks']==binding['start_ticks']
        and ready['facts']['net_namespace']==dict(link=guest['link'],**guest['file_identity'])
        and ack['host_namespaces']==dict(owner=host,host_init=init)
        and ns['comparisons']==dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False),
        'actual owner/init network identity and independently distinct bound guest before executor')
    ack_bytes=canonical(ack)+b'\n';ack_sha=hashlib.sha256(ack_bytes).hexdigest()
    need(ref(checked(proof['ack_ref']))['sha256']==ack_sha and publication['ack_sha256']==ack_sha
        and publication['container_id']==he['container_id']and publication['owned_host_pid']==binding['host_pid']
        and publication['owned_start_ticks']==binding['start_ticks']and publication['namespace_before']==binding['program']['namespaces']
        and publication['ack_uid']==0 and publication['ack_mode']==0o444 and publication['ack_bytes']==len(ack_bytes)
        and all(publication[k]is True for k in('directory_nofollow','new_file_exclusive','complete_data_before_atomic_link',
            'no_added_mounts','no_sockets_or_ioctls_or_setns')),
        'actual complete source-owned root ACK atomically issued in pinned private tmpfs')
    capsule=read(stage['capsule_ref']);staged_inputs=read(stage['inputs_ref'])
    for key in('official_package_ref','effective_inputs_ref'):read(stage[key])
    for directory,entries in((stage['source_root'],capsule['files']),
            (stage['suite_root'],capsule['official_package_files']),(stage['input_root'],staged_inputs['files'])):
        for row in entries:
            relative=Path(row['relative']);need(not relative.is_absolute()and'..'not in relative.parts,'only exact staged public files')
            add(dict(path=str(Path(directory)/relative),bytes=row['bytes'],sha256=row['sha256']))
    raw=checked(he['stdout_ref']).read_text();lines=[s[len('BOLE_HE_OFFICIAL_V2 '):]for s in raw.splitlines()if s.startswith('BOLE_HE_OFFICIAL_V2 ')]
    need(len(lines)==1,'one actual source-bound official HE control result')
    result=parse(lines[0]);admission=result['network_admission']
    interpreter=read(dict(path=str(Path(inputs['task_packet_root'])/'HE_PYTHON_PROTOCOL.json'),
        bytes=ref(Path(inputs['task_packet_root'])/'HE_PYTHON_PROTOCOL.json')['bytes'],
        sha256='b3659515cd0546f72e5b3166ccae285080dc71b09815663570d5ab8bd515dc00'))
    runtime=result['runtime_identity'];program=binding['program']
    need(runtime['python_executable']in('/usr/local/python3.12.13/bin/python3','/usr/local/python3.12.13/bin/python3.12')
        and runtime['python_version'].split()[0]==interpreter['python_version']=='3.12.13'
        and runtime['numpy_version']==interpreter['numpy_version']=='1.26.4'
        and runtime['tqdm_version']==interpreter['tqdm_version']=='4.70.0'
        and{k:runtime[k]for k in('numpy_source','tqdm_source')}==interpreter['imported_sources']
        and program['expected_namespace_executable']==program['actual_namespace_executable']==interpreter['namespace_interpreter']
        and program['executable']['bytes']==interpreter['python_executable_bytes']
        and program['executable']['sha256']==interpreter['python_executable_sha256'],
        'actual loaded whole Python312 interpreter and actual real libraries match successful isolated dependency preflight')
    need(result['schema']=='bole.actual-HE-official-sandbox-result/v2'and result['mode']=='controls'
        and result['control_discrimination_pass']is True and result['task_score_produced']is False
        and result['root_source_sha256']==plan_source['sha256']and result['capsule_sha256']==stage['capsule_ref']['sha256']
        and result['input_sha256']==stage['inputs_ref']['sha256']
        and result['official_evaluation_sha256']=='e926d5e9b8f1ec040096cd5952e8cf79f8dc0b7fb80ba6667ce604ffea0397bc'
        and result['official_execution_sha256']=='79901c6f5b59701c465b164aed290fa53abc35abc80a5378fc10f4dac1f9a84c'
        and result['generated_code_executed']is True and result['case_labels']==['correct','wrong','timeout']
        and [row['passed']for row in result['rows']]==[True,False,False]and result['rows'][2]['result']=='timed out'
        and admission['ready']==ready and admission['ack']==ack and admission['ack_sha256']==ack_sha
        and admission['before_executor_host_ack_verified']is True,'actual unchanged official controls only after exact host ACK')
    for facts in(admission['after_ack_facts'],result['network_after']):
        G.validate(facts);need(facts['guest']==ready['facts']['guest']and facts['net_namespace']==ready['facts']['net_namespace'],
            'actual same isolated guest throughout evaluation')


def CPU_proof(r,plan_source,*,evidence_refs=None):
    refs={}
    def add(reference):
        a=ref(checked(reference));refs[a['path']]=a;return a
    def read(reference):add(reference);return obj(reference)
    need(add(r)==SUPPORTED_CPU_OWNER_REF,'exact actual successful fullCPU14 owner; old failed CPU10/13 and diagnostic/planned refs rejected')
    v=read(r);CPU_status(v)
    need(add(v['inputs_ref'])==SUPPORTED_CPU_INPUTS_REF,'exact actual fullCPU14 input/source binding')
    ce=add(ref(P/'CPU_OWNER_EXPECTED.json'));need(ce['sha256']==CPU_EXPECTED_SHA,'same frozen CPU v14 expected code')
    expected=read(ce);inputs=read(v['inputs_ref'])
    need(inputs['schema']=='bole.task-finite-CPU-owner-inputs/v5'and inputs['image_id']==IMAGE
        and inputs['diagnostic_only']is False and inputs['qualification_profile']==CPU_PROFILE
        and inputs['phase_order']==['cpu-preflight','he-controls','cpu-consumer']
        and inputs['public_probe_owner_ref']==v['public_probe_owner_ref']and set(inputs['files'])==set(expected),
        'actual supported complete v14 CPU owner input source and public prerequisite')
    for n,r in inputs['files'].items():
        a=add(r);need((a['bytes'],a['sha256'])==(expected[n]['bytes'],expected[n]['sha256'])
            and v['source_input_before'].get(a['path'])==a['sha256'],'exact supported actual CPU owner code before/after '+n)
    manifest=read(inputs['frozen_packet_manifest_ref'])
    need(inputs['frozen_packet_manifest_ref']['sha256']==TASK_PACKET_MANIFEST_SHA,'exact prospective public decoder v4 and HE admission packet')
    root=Path(inputs['task_packet_root'])
    for n,row in manifest['files'].items():add(dict(row,path=str(root/n)))
    tm=read(plan_source)
    need(tm['schema']=='bole.three-task-decoder-scorer/source/v4'and tm['root']==str(root)
        and tm['decoder_constructor_protocol']=='transformers-public-TokenizersBackend.from_pretrained/v2'
        and tm['network_isolation_protocol']=='bole.HE-isolated-down-virtual-networks/v1'
        and tm['input_preparation_source_ref']==inputs['task_source_unbound_ref']and tm['effective_inputs_ref']is not None,
        'same actual v012 bound input/constructor source used to create the plan')
    add(inputs['task_source_unbound_ref']);add(inputs['public_probe_owner_ref'])
    for n,r in tm['files'].items():
        a=add(r);w=manifest['files'][n]
        need(a==dict(w,path=str(root/n)),'whole source-bound unchanged public decoder/scorer/input closure '+n)
    summary=v['summary'];first=read(summary['CPU']['report']);independent=read(summary['independent']['report'])
    need(first['inputs_ref']==independent['inputs_ref']==v['inputs_ref']
        and first['mode']=='prepare-decode'and independent['mode']=='independent-reader'
        and first['payload']['bound_task_source_ref']==plan_source
        and first['payload']['effective_inputs_ref']==tm['effective_inputs_ref']
        and first['payload']['pure_controls_pass']is True and first['payload']['network_guard_controls_pass']is True
        and first['payload']['all_input_source_gold_template_verified']is True,
        'actual producer and independent child source/effective input joins')
    for child in(first,independent):
        need(child['readset_before']==child['readset_after']and child['payload']['forbidden_import_attempts']==[],
            'actual full CPU child source equality and zero forbidden attempts')
        a=child['payload']['import_audit_ref'];add(a);CPU_audit(a,inputs['task_source_unbound_ref'])
    for phase in('CPU','independent'):
        row=summary[phase]
        for key in('terminal','binding','inspect_ref'):add(row[key])
        terminal=read(row['terminal']);need(terminal['exit_code']==0 and terminal['process_binding']==row['binding'],'actual finite qualified CPU child exit/live binding')
        add(terminal['stdout']);add(terminal['stderr'])
    inner=read(summary['independent_component_ref'])
    need(independent['payload']['independent_ref']==summary['independent_component_ref']and inner['source_ref']==plan_source
        and inner['independent_component_checks_pass']is True and inner['software_controls_only']is True
        and inner['decoder']['counts']=={'GSM8K':1319,'HumanEval':164,'MMLU':14042}
        and inner['HumanEval']['official_executor_controls_pass']is True
        and inner['HumanEval']['task_score_produced']is False and inner['formal_task_accuracy_accepted']is False,
        'same full15525 input/decoder and real official sandbox controls; no task score')
    retired_cids=dict(CPU_release=read(summary['CPU']['binding'])['container_id'],
        HE_release=read(summary['HE_owner_ref'])['container_id'],
        independent_release=read(summary['independent']['binding'])['container_id'])
    for key in('CPU_release','HE_release','independent_release'):
        x=read(summary[key]);need(x['stopped']is True and x['retained']is True and x['errors']==[],'all CPU prior owned stages stopped retained')
        need(x['container']==retired_cids[key]and x['deleted']is False,'actual same phase fullCID cleanup identity, stopped retained')
        after=read(x['after_inspect']);rows=parse(after['stdout'])
        need(after['exit_code']==0 and after['requested_argv']==['/usr/bin/docker','inspect',x['container']]
            and len(rows)==1 and rows[0]['Id']==x['container']and rows[0]['Image']==IMAGE
            and rows[0]['State']['Running']is False and rows[0]['State']['Pid']==0 and not rows[0].get('ExecIDs'),
            'all actual fullCPU14 post-cleanup whole inspect refs explicitly reopened and mounted')
    for key in('HE_owner_ref','HE_binding','HE_CPU145_prestart_update'):add(summary[key])
    he=read(summary['HE_owner_ref'])
    for k in('stage_ref','create_argv_ref','created_id_ref','inspect_ref','wait_ref','stdout_ref'):add(he[k])
    policy=read(inputs['main_quiescence_ref']);lock=read(summary['inherited_lock_ref'])
    need(lock['policy_ref']==inputs['main_quiescence_ref'],'actual same policy inherited owner lock')
    CPU_lock(lock,policy,v);CPU_HE(summary,v,inputs,plan_source,read,add)
    # This exact owner readset includes all new HE diagnostic prerequisites,
    # copied public headers, frozen input files and explicit controller refs.
    for path,sha in v['source_input_before'].items():
        need(Path(path).suffix not in{'.safetensors','.bin','.pth'}and Path(path).stat().st_size<=256*2**20,
            'bounded source/input/tokenizer closure; never hash checkpoint weights')
        add(dict(path=path,sha256=sha))
    if evidence_refs is not None:
        need(type(evidence_refs)is list,'explicit optional CPU evidence Ref list')
        evidence_refs.extend(refs.values())
    return v


def owned_inspect(owned_ref,inspect_ref):
    e=obj(owned_ref);creation=obj(e['create_receipt']);argv=creation['requested_argv'];labels={};names=[]
    need(creation['exit_code']==0 and creation['stdout'].strip()==e['cid']and argv[:2]==['/usr/bin/docker','create'],'same original full-CID successful create receipt')
    for n,t in enumerate(argv):
        if t=='--name':need(n+1<len(argv),'create name value');names.append(argv[n+1])
        if t=='--label':
            need(n+1<len(argv)and '='in argv[n+1],'original complete create label');k,v=argv[n+1].split('=',1)
            need(k not in labels and k and v,'unique original create labels');labels[k]=v
        need(not t.startswith('--label=')and not t.startswith('--name='),'original separate name/label tokens')
    expected={'model-tuning-lab.run':e['name'],'model-tuning-lab.arm':e['arm'],
        'model-tuning-lab.source-manifest-sha256':e['source']['sha256'],'model-tuning-lab.controller-sha256':e['host_sha256']}
    need(names==[e['name']]and argv.count(IMAGE)==1 and e['image']==IMAGE and len(e['cid'])==64
         and all(labels.get(k)==v for k,v in expected.items())and labels.get('model-tuning-lab.owner'),'same original model name/image/source/controller/owner')
    raw=obj(inspect_ref);need(raw['exit_code']==0 and raw['requested_argv']==['/usr/bin/docker','inspect',e['cid']],'actual complete exact-owned inspect receipt')
    rows=parse(raw['stdout']);need(len(rows)==1,'one explicit owned inspect');x=rows[0]
    need(x['Id']==e['cid']and x['Name']=='/'+e['name']and x['Image']==x['Config']['Image']==IMAGE
        and all((x['Config'].get('Labels')or{}).get(k)==v for k,v in labels.items()),'actual same full CID/model source/image/owner labels')
    return e,x
