"""Current CPU replay boundary; historical generation and preparation are not current authority."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import time
from contextlib import contextmanager

IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
COUNTS={'GSM8K':1319,'HumanEval':164,'MMLU':14042}
AUTH_SCHEMA='bole.current-CPU-decode-replay-authority/v1'
REVIEW_SCHEMA='bole.MAIN-current-CPU-decode-replay-review/v1'
SCOPE=dict(action='token-decode-component-grade-only',image_id=IMAGE,Devices=[],
           network='none',generated_code_execution=False,HTTP=False,NPU=False)
_ACTIVE=None

def need(ok,message):
    if not ok:raise ValueError(message)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def ref(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact replay source')
    a=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as stream:
        for b in iter(lambda:stream.read(2**20),b''):h.update(b);size+=len(b)
    z=p.stat()
    need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==
         (z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)and size==z.st_size,'stable whole replay Ref')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())

def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and
         0<=r['bytes']<=128*2**20,'exact bounded replay Ref3')
    need(ref(r['path'])==r,'whole replay evidence bytes');return Path(r['path'])

def obj(r):return json.loads(checked(r).read_bytes())

def exact(a,b):
    if type(a)is not type(b):return False
    if type(b)is dict:return set(a)==set(b)and all(exact(a[k],v)for k,v in b.items())
    if type(b)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
    return a==b

def process_identity():
    p=Path('/proc/self');text=(p/'stat').read_text();fields=text[text.rfind(')')+2:].split()
    return dict(pid=os.getpid(),start_ticks=int(fields[19]),uid=os.getuid(),
        executable=os.readlink(p/'exe'),cgroup_sha256=hashlib.sha256((p/'cgroup').read_bytes()).hexdigest())

def ticket_policy(ticket,review,binding_ref,binding,executor,inspect_record,host_binding,now,seconds,process):
    need(type(now)in(int,float)and type(seconds)in(int,float)and seconds>=0,'real finite replay time')
    need(type(ticket)is dict and set(ticket)=={'schema','approved','start_epoch','cutoff_epoch','scope','binding_ref','MAIN_review_ref'}and
         ticket['schema']==AUTH_SCHEMA and ticket['approved']is True and exact(ticket['scope'],SCOPE)and
         ticket['binding_ref']==binding_ref,'distinct current CPU decoder ticket, never an HTTP/expired-generation ticket')
    need(type(ticket['start_epoch'])is int and type(ticket['cutoff_epoch'])is int and
         ticket['start_epoch']<=now and now+seconds<ticket['cutoff_epoch'],'current finite CPU replay window including budget')
    need(review.get('schema')==REVIEW_SCHEMA and review.get('approved')is True and exact(review.get('scope'),SCOPE)and
         review.get('binding_ref')==binding_ref and review.get('source_root')==binding['source_root']and
         review.get('files')==binding['files'],'actual MAIN review pins replay source and inputs')
    need(executor['schema']=='bole.actual-current-CPU-replay-execution/v1'and executor['role']=='cpu-consumer'and
         executor['image_id']==IMAGE and executor['process']==process and
         type(process['pid'])is int and process['pid']>0 and type(process['start_ticks'])is int and process['start_ticks']>0,
         'actual current CPU execution identity, not historical CPU14/planned success')
    need(inspect_record['exit_code']==0 and inspect_record['requested_argv']==
         ['/usr/bin/docker','inspect',executor['container_id']]and inspect_record.get('stderr','')=='',
         'actual host Docker inspect execution record, not guest-declared Devices JSON')
    inspect=json.loads(inspect_record['stdout'])
    need(type(inspect)is list and len(inspect)==1,'whole actual owned CPU inspect')
    x=inspect[0];h=x['HostConfig']
    need(x['Id']==executor['container_id']and x['Image']==IMAGE and x['State']['Running']is True and
         x['State']['Pid']>0 and h['Privileged']is False and h.get('Devices',[])==[]and
         h.get('DeviceRequests',[])in([],None)and h.get('DeviceCgroupRules',[])in([],None)and
         h['Runtime']=='runc'and h['NetworkMode']=='none'and h['ReadonlyRootfs']is True,
         'current owned same-image nonprivileged Devices[] no-network CPU execution')
    broad={'/','/dev','/proc','/sys','/run','/var/run','/etc','/root','/home','/opt','/cache'}
    for mount in x['Mounts']:
        source=PurePosixPath(mount['Source']);dest=PurePosixPath(mount['Destination'])
        need(source.is_absolute()and dest.is_absolute()and '..'not in source.parts and '..'not in dest.parts and
             str(source)not in broad and not any(str(source)==p or p+'/'in str(source)+'/'for p in('/dev','/proc','/sys'))and
             not any(str(dest)==p or str(dest).startswith(p+'/')for p in('/dev','/proc','/sys')),
             'no host broad root, device/driver nodes or kernel-tree bind into CPU replay')
    need(host_binding['schema']=='bole.actual-host-CPU-replay-process-binding/v1'and
         host_binding['container_id']==executor['container_id']and host_binding['process']==process and
         type(host_binding['host_pid'])is int and host_binding['host_pid']>0 and
         host_binding['NSpid'][0]==host_binding['host_pid']and host_binding['NSpid'][-1]==process['pid']and
         host_binding['host_start_ticks']==process['start_ticks']and
         executor['container_id']in host_binding['host_cgroup']and
         host_binding['UID']==[process['uid']]*4 and host_binding['executable']==process['executable'],
         'MAIN host-captured PID namespace/start/executable/cgroup identity for this current guest')
    required=binding['required_readonly_mounts']
    need(type(required)is list and required and binding['source_root']in required and
         all(any(z['Destination']==path and z['RW']is False for z in x['Mounts'])for path in required),
         'actual host inspect readonly source/input mounts match MAIN-bound readset')
    return ticket

def generation_policy(binding,plan,raw,generation,HTTP_source,authority,owner,client,release):
    need(binding['schema']=='bole.current-CPU-replay-binding/v1'and binding['phase']in('smoke','full')and
         binding['arm']in('OFF','ON'),'explicit replay binding/phase/arm')
    count=6 if binding['phase']=='smoke' else 15525
    need(plan['phase']==raw['phase']==binding['phase']and plan['arm']==raw['arm']==binding['arm']and
         plan['source_ref']==raw['source_ref']==binding['historical_task_source_ref']and
         plan['effective_inputs_ref']==raw['effective_inputs_ref']==binding['effective_inputs_ref']and
         len(raw['records'])==plan['count']==count and raw['model']==plan['model'],'exact original source/cohort/arm before CPU replay')
    need(generation['schema']=='bole.actual-task-generation-provenance/v1'and
         generation['producer_ref']==binding['generation_producer_ref']and
         generation['plan_ref']==binding['plan_ref']and generation['raw_ref']==binding['raw_ref']and
         generation['HTTP_source_ref']==client['source_ref']and generation['authority_ref']==HTTP_source['authority_ref']and
         HTTP_source['plan_ref']==binding['plan_ref']and HTTP_source['phase']==binding['phase']and
         HTTP_source['request_count']==count,'actual generation provenance, never current decoder identity')
    start=generation['started_epoch'];finish=generation['finished_epoch']
    need(type(start)in(int,float)and type(finish)in(int,float)and start<=finish and
         authority['start_epoch']<=start<=finish<authority['cutoff_epoch'],
         'generation really occurred inside its own unchanged historical authorization')
    need(owner['schema']=='bole.actual-task-runtime-owned/v1'and owner['primary']is None and owner['secondary']==[]and
         owner['source_input_before']==owner['source_input_after']and owner['private_namespace_restored_by_identity']is True and
         owner['summary']['client_ref']==generation['client_ref']and
         owner['summary']['model_release_ref']==generation['release_ref'],'actual complete generation owner, not copied PASS')
    need(client['schema']=='bole.actual-task-normalEOS-cohort-client/v2'and client['primary']is None and
         client['raw_ref']==binding['raw_ref']and client['completed_task_requests']==count and client['barrier']is not None and
         release['stopped']is True and release['retained']is True and release['errors']==[],
         'complete original generation and stop-retain before separate CPU replay')
    return True

def envelope(original,new_source_ref):
    # This is a DERIVED replay envelope, not an edit or relabel of generation evidence.
    need(original['schema']=='bole.actual-three-task-HTTP-completions/v1','original token-completion envelope')
    result=dict(original);result['source_ref']=new_source_ref
    need({k:v for k,v in result.items()if k!='source_ref'}==
         {k:v for k,v in original.items()if k!='source_ref'},'only explicit source identity remapping')
    return result

def inverse_envelope(derived,historical_source_ref):
    result=dict(derived);result['source_ref']=historical_source_ref;return result

def validate_current(m,binding_ref,*,seconds=0):
    binding=obj(binding_ref)
    need(m['decoder_replay_lineage_ref']==binding_ref and m['root']==binding['source_root']and
         m['files']==binding['files'],'current source, full actual replay tree and binding')
    for name,r in m['files'].items():
        need(checked(r)==Path(m['root'])/name,'same actual current source location')
    ticket=obj(m['authority_ref']);review=obj(ticket['MAIN_review_ref']);executor=obj(binding['executor_ref'])
    ticket_policy(ticket,review,binding_ref,binding,executor,obj(executor['host_inspect_record_ref']),
        obj(executor['host_process_binding_ref']),time.time(),seconds,process_identity())
    return binding

def verify_generation(binding,m):
    generation=obj(binding['generation_ref']);plan=obj(binding['plan_ref']);raw=obj(binding['raw_ref'])
    checked(binding['generation_producer_ref'])
    need(generation['producer_ref']==binding['generation_producer_ref']and
         generation['operator_epochs_accepted']is False,'actual reviewed generation-provenance producer, not arbitrary epoch fields')
    import generation_provenance as G
    need(ref(G.__file__)==binding['generation_producer_ref']==m['files']['generation_provenance.py'],
         'actual same source-owned producer/independent reconstruction, not a declared producer string')
    expected=G.provenance(generation['host_clock_before_ref'],generation['host_execution_ref'],
        generation['host_clock_after_ref'],generation['owner_ref'],generation['HTTP_source_ref'],generation['plan_ref'])
    need(generation==expected,'whole generation provenance independently reconstructed from actual host operations/owner/client/stop')
    HTTP_source=obj(generation['HTTP_source_ref'])
    generation_policy(binding,plan,raw,generation,HTTP_source,obj(generation['authority_ref']),
        obj(generation['owner_ref']),obj(generation['client_ref']),obj(generation['release_ref']))
    return plan,raw

@contextmanager
def execution(m,source_ref,binding_ref):
    global _ACTIVE
    need(_ACTIVE is None,'one explicit current replay, no nested or global fallback')
    binding=validate_current(m,binding_ref,seconds=300)
    plan,raw=verify_generation(binding,m)
    # Reuse the already-qualified CPU14 *historical* proof reader unchanged.
    import lineage_http_common as H
    H.CPU_proof(H.SUPPORTED_CPU_OWNER_REF,binding['historical_task_source_ref'])
    original=obj(binding['historical_task_source_ref'])
    need(original['authority_ref']==binding['historical_preparation_authority_ref']and
         original['effective_inputs_ref']==m['effective_inputs_ref']==binding['effective_inputs_ref'],
         'immutable original preparation identity and same official effective input source')
    _ACTIVE=dict(m=m,source_ref=source_ref,binding_ref=binding_ref,binding=binding,raw=raw)
    try:yield _ACTIVE
    finally:_ACTIVE=None

def assert_source(m,source_ref):
    need(_ACTIVE is not None and m==_ACTIVE['m']and source_ref==_ACTIVE['source_ref'],
         'only the explicit current CPU replay entry may use this derived source')
    validate_current(m,_ACTIVE['binding_ref'])

def verify_inputs(m,original_verify):
    need(_ACTIVE is not None and m==_ACTIVE['m'],'explicit current replay input lineage context')
    original=obj(_ACTIVE['binding']['historical_task_source_ref'])
    allowed={'root','files','authority_ref','decoder_replay_lineage_ref','decoder_replay_source_schema','historical_task_source_ref'}
    need(set(m)==set(original)|{'decoder_replay_lineage_ref','decoder_replay_source_schema','historical_task_source_ref'}and
         all(m[k]==v for k,v in original.items()if k not in allowed)and
         m['historical_task_source_ref']==_ACTIVE['binding']['historical_task_source_ref'],
         'derived source changes only explicit CPU execution/owning-layer identity, never effective input/preparation')
    additions={'decoder_replay_contract.py','replay_entry.py','generation_provenance.py','lineage_http_common.py','cohort_contract.py','CPU_OWNER_EXPECTED.json'}
    need(set(m['files'])==set(original['files'])|additions,'all original source files plus exact replay additions')
    for n,old in original['files'].items():
        if n!='task_contract.py':
            need((m['files'][n]['bytes'],m['files'][n]['sha256'])==(old['bytes'],old['sha256']),
                 'unchanged original input/scorer/decoder/HE source '+n)
    # The original complete function still executes, against the original
    # manifest/authority/preparation equality. Nothing is regenerated or skipped.
    import ast
    oldtree=ast.parse(checked(original['files']['task_contract.py']).read_bytes())
    newtree=ast.parse(checked(m['files']['task_contract.py']).read_bytes())
    for old_name,new_name in (('verify_inputs','_historical_verify_inputs'),('current_authority','_historical_current_authority')):
        a=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef)and n.name==old_name)
        b=next(n for n in newtree.body if isinstance(n,ast.FunctionDef)and n.name==new_name)
        b.name=old_name
        need(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'complete original verifier/clock body retained')
    need(original_verify.__name__=='_historical_verify_inputs'and
         Path(original_verify.__code__.co_filename)==checked(m['files']['task_contract.py']),
         'actual source-owned legacy input verifier, not an injected callback')
    return original_verify(original)

def current_authority(reference,seconds=0,now=None):
    need(_ACTIVE is not None and now is None and reference==_ACTIVE['m']['authority_ref'],
         'no old ticket, fake clock or HTTP ticket as CPU decoder authority')
    validate_current(_ACTIVE['m'],_ACTIVE['binding_ref'],seconds=seconds)
    return obj(reference)
