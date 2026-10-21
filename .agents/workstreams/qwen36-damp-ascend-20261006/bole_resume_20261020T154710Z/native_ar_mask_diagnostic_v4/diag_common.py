"""Actual failed-v3/complete saved readset gates, no numerical replay or device."""
import importlib.util
import json
from pathlib import Path
import re
import os
import stat

LOCK='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock'
FILES=('ar_owner_common.py','ar_saved_namespace.py','diag_common.py','prepare_mask_owner.py','mask_cpu_owner.py',
       'mask_diagnostic.py','ACTUAL_V3_FAILURE_REFS.json','MASK_SOURCE_EVIDENCE.json','MASK_SOURCE_COPY_RECORD.json',
       'ACTUAL_CPU_PROFILE_REFS.json')


def common():
    p=Path(__file__).parent/'ar_owner_common.py';import hashlib
    raw=p.read_bytes()
    if(len(raw),hashlib.sha256(raw).hexdigest())!=(19055,'5d0b9034706b9a942a4d7dd10870139959b22dfaab2cebbdddf25ba962e456a4'):
        raise ValueError('exact frozen original AR/025 helper')
    s=importlib.util.spec_from_file_location('_mask_original_common',p);C=importlib.util.module_from_spec(s);s.loader.exec_module(C);return C


def held_main_lock(C):
    path=Path(LOCK);C.need(path.is_file()and not any(p.is_symlink()for p in(path,*path.parents))and
        stat.S_IMODE(path.stat().st_mode)==0o600,'ordinary actual0600 MAIN lock')
    value=path.stat();fds=[];lines=[]
    for p in Path('/proc/self/fd').iterdir():
        try:
            s=p.stat()
            if(s.st_dev,s.st_ino)==(value.st_dev,value.st_ino)and os.readlink(p)==LOCK:fds.append(int(p.name))
        except FileNotFoundError:continue
    for line in Path('/proc/locks').read_text().splitlines():
        v=line.split()
        if len(v)>=8 and v[1:4]==['FLOCK','ADVISORY','WRITE']and v[4]==str(os.getpid()):
            q=v[5].split(':')
            if len(q)==3 and int(q[0],16)==os.major(value.st_dev)and int(q[1],16)==os.minor(value.st_dev)and int(q[2])==value.st_ino:lines.append(line)
    C.need(fds and len(lines)==1,'inherited actual outer MAIN --no-fork flock; never acquire/create')
    return dict(path=LOCK,host_pid=os.getpid(),inherited_FDs=sorted(fds),actual_proc_locks=lines,
        inherited_MAIN_lock_verified=True,lock_acquired_by_this_helper=False)


def source(C,ir):
    y=C.obj(ir)
    C.need(y['schema']=='bole.native-ar-mask-diagnostic-inputs/v1'and y['default_enabled']is False and
        y['prepared_only']is True and y['files']['diag_common.py']==C.ref(__file__)and y['MAIN_lock']==LOCK,
        'new defaultOFF exact diagnostic source')
    for r in y['files'].values():C.checked(r)
    C.need(Path(y['output_root']).parent==Path('/opt/host/vnf/austinov')and
        re.fullmatch('run-bole-native-ar-mask-[a-z0-9-]{1,22}',Path(y['output_root']).name)is not None and
        len(Path(y['output_root']).name)<=50 and y['consumer_output_root']==str(Path(y['output_root'])/'cpu-consumer'),
        'new bounded lowercase independent diagnostic leaf')
    return y


def prior(C,y):
    expected=C.obj(C.ref(Path(__file__).parent/'ACTUAL_V3_FAILURE_REFS.json'))
    C.need(y['actual_v3_failure_refs']==expected,'exact actual third CPU failure and passed original G1 gate')
    refs=expected;values={n:C.obj(r)for n,r in refs.items()if n.endswith('.json')}
    for r in refs.values():C.checked(r)
    owner=values['RESULT.json'];release=values['cpu-consumer/cleanup.json'];child=values['cpu-consumer/SAVED-PAIR-INDEPENDENT-CHILD.json']
    C.need(owner['schema']=='bole.native-ar-saved-evidence-owner/v3'and owner['primary']is not None and
        owner['secondary']==[]and owner['source_before']==owner['source_after']and owner['source_before']and
        owner['independent_numeric_requalification_pass']is False and 'independent'not in owner['summary']and
        release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[]and
        child['exit_code']!=0 and child['child_termination_observed']is True,'actual clean failed numerical-v3 preserved')
    stderr=C.checked(refs['cpu-consumer/SAVED-PAIR-INDEPENDENT.stderr']).read_text()
    C.need('actual_native_fa'in stderr and 'line 190'in stderr and 'mask.dtype==t.bool'in stderr and
        'actual native causal-mask bytes; unknown mask rejected'in stderr,'exact actual mask-guard failure, no native FA verdict')
    oldy=C.obj(owner['inputs']);r=oldy['files']['saved_common.py']
    C.need((r['bytes'],r['sha256'])==(17640,'2f67a4a00ea527a6e18213d11a6e1bacc7d7c7a0ea521da52493de68e8ad50f8'),
        'exact frozen complete385-path saved-v3 source helper before import')
    B=C.load(r,'_mask_exact_saved_v3')
    original,x,m=B.prior(C,oldy['actual_saved_refs'])
    pair=C.obj(oldy['actual_saved_refs']['PAIR-INPUTS.json'])
    gate=values['cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json']
    C.need(gate['schema']=='bole.actual-c1-two-request-service-independent/v1'and gate['source']==m['BOLE_source_ref']and
        gate['inputs']==pair['BOLE']and gate['completed_request_count']==2 and
        all(gate[k]is True for k in('G1_experiment_pass','service_complete','component_checks_pass',
            'independent_actual_target_TP4_vocabulary_join','independent_actual_MTP_TP4_vocabulary_join',
            'actual_HTTP_output_token_ID_join','actual_all4_retirement','scheduler_committed_independently'))and
        gate['native_AR_greedy_comparison_performed']is False and gate['greedy_identity_pass']is None and
        gate['model_ready']is False and gate['formal_success']is False,
        'actual completed full original G1 child report required; never replay its mathematics in this diagnostic')
    return owner,oldy,B,x,m,original


def original_CPU_profile(C,y,owner):
    refs=C.obj(C.ref(Path(__file__).parent/'ACTUAL_CPU_PROFILE_REFS.json'))
    C.need(y['actual_original_CPU_profile_refs']==refs,'exact actual saved-v3 CPU proof refs')
    owned=C.obj(refs['OWNED.json']);guest=C.obj(refs['GUEST_CPU.json'])
    release=C.obj(y['actual_v3_failure_refs']['cpu-consumer/cleanup.json'])
    child=C.obj(y['actual_v3_failure_refs']['cpu-consumer/SAVED-PAIR-INDEPENDENT-CHILD.json'])
    C.need(owned['arm']=='cpu-preflight'and owned['guest_cpus']==[0]and owned['source']==owner['source']and
        owned['image']==C.IMAGE and owned['cid']==release['container']and
        child['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']]and
        guest['affinity']==guest['effective_cpus']==guest['ancestor_cpuset']==[0]and
        guest['effective_capacity']==1 and guest['cgroup']=='/docker/'+owned['cid']and
        owned['cid']in guest['process']['cgroup'],
        'actual original025 no-model helper selected CPU0 with one effective ancestor capacity')
    return dict(schema='bole.actual-original025-no-model-CPU-profile/v1',refs=refs,
        original_owned_cid=owned['cid'],original_guest_cpus=owned['guest_cpus'],affinity=guest['affinity'],
        effective_cpus=guest['effective_cpus'],ancestor_cpuset=guest['ancestor_cpuset'],
        effective_capacity=guest['effective_capacity'],original_admission_function_unchanged=True,
        task_CPU145_profile_substituted=False)


def readset(C,y,*,installed=False):
    owner,oldy,B,x,m,objects=prior(C,y)
    C.need(y['original_saved_inputs']==owner['inputs']and y['AR_source']==x['AR_source']and
        y['authority']==x['authority'],'one unchanged actual saved input/source/authority chain')
    _,_,on,refs,mapping=B.readset(C,oldy,installed=installed)
    cpu_profile=original_CPU_profile(C,y,owner)
    extras=C.obj(y['mask_source_evidence_ref'])
    C.need(type(extras)is dict and 'attention_mask'in extras and len(extras)<=8,'explicit complete bounded mask/helper primary source map')
    extra=[]
    for key,row in extras.items():
        C.need(type(row)is dict and set(row)=={'runtime_ref','host_ref'},'distinct installed/host Ref3 pair')
        a,b=row['runtime_ref'],row['host_ref']
        C.need(set(a)==set(b)=={'path','bytes','sha256'}and a['path']!=b['path']and
            (a['bytes'],a['sha256'])==(b['bytes'],b['sha256']),'same actual complete source bytes/SHA at distinct paths')
        if key=='attention_mask':C.need(a['path']=='/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_mask.py'and
            (a['bytes'],a['sha256'])==(3783,'fb138c36ce381fb6ad65a620f30c6d85bd4d771ae2dfff5da947a67b2c2ba2a5'),
            'exact actual mask-builder primary source; no inferred ABI source version')
        C.checked(b);extra.append(b)
        if installed:C.checked(a)
    for r in [*y['files'].values(),*y['actual_v3_failure_refs'].values(),*cpu_profile['refs'].values(),owner['inputs'],y['mask_source_evidence_ref']]:
        C.checked(r);extra.append(C.ref(r['path']))
    # Reopen only actual Ref objects from failed receipts; never treat arbitrary
    # strings/prefixes as mount exemptions. Existing saved map stays exact.
    collected,_=B.collect(C,[owner,objects,y['actual_v3_failure_refs']],{v['installed']['path']:v for v in mapping['mapping']},installed=installed)
    unique={}
    for r in(*refs,*extra,*collected):
        C.need(r['path']not in unique or unique[r['path']]==r,'one exact immutable diagnostic readset');unique[r['path']]=r
    return x,m,on,list(unique.values()),dict(original_saved_mapping=mapping,mask_primary_sources=extras,
        actual_original_CPU_profile=cpu_profile,installed_sources_reopened=installed,
        numerical_replayed=False,mask_semantics_qualified=False)
