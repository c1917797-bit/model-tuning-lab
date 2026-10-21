"""Exact failed numerical-v4/source prerequisites; no tensor imports."""
import importlib.util
import json
from pathlib import Path
import re

LOCK='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock'
FILES=('ar_owner_common.py','ar_saved_namespace.py','numeric_common.py','prepare_numeric_owner.py',
    'numeric_cpu_owner.py','numeric_diagnostic.py','ACTUAL_NUMERIC_V4_REFS.json')


def common():
    import hashlib
    p=Path(__file__).parent/'ar_owner_common.py';b=p.read_bytes()
    if(len(b),hashlib.sha256(b).hexdigest())!=(19055,'5d0b9034706b9a942a4d7dd10870139959b22dfaab2cebbdddf25ba962e456a4'):
        raise ValueError('exact original AR025 source')
    s=importlib.util.spec_from_file_location('_numeric_original_common',p);C=importlib.util.module_from_spec(s);s.loader.exec_module(C);return C


def held_main_lock(C):
    # Reuse the exact already-reviewed original lock observer, not a new lock.
    refs=C.obj(C.ref(Path(__file__).parent/'ACTUAL_NUMERIC_V4_REFS.json'))
    old=C.obj(refs['INPUTS.json']);r=old['files']['saved_common.py']
    C.need((r['bytes'],r['sha256'])==(18903,'9e79c49a440317456dd9cea6da03c12d9473bceb3c3d9f9ee6244b3d9aa7eb08'),'exact frozen numeric-v4 helper')
    B=C.load(r,'_numeric_original_saved_v4');return B.held_main_lock(C)


def source(C,ir):
    y=C.obj(ir)
    C.need(y['schema']=='bole.native-ar-numeric-diagnostic-inputs/v1'and y['files']['numeric_common.py']==C.ref(__file__)and
        y['MAIN_lock']==LOCK and y['default_enabled']is False and y['prepared_only']is True,'new exact defaultOFF diagnostic source')
    for r in y['files'].values():C.checked(r)
    p=Path(y['output_root'])
    C.need(p.parent==Path('/opt/host/vnf/austinov')and re.fullmatch('run-bole-native-ar-numdiag-[a-z0-9-]{1,15}',p.name)is not None and
        y['consumer_output_root']==str(p/'cpu-consumer'),'new bounded independent diagnostic output leaf')
    return y


def prior(C,y):
    refs=C.obj(C.ref(Path(__file__).parent/'ACTUAL_NUMERIC_V4_REFS.json'))
    C.need(y['actual_numeric_v4_refs']==refs,'exact actual numerical-v4 failure chain')
    values={n:C.obj(r)for n,r in refs.items()if n.endswith('.json')}
    for r in refs.values():C.checked(r)
    owner=values['RESULT.json'];old=values['INPUTS.json'];release=values['cpu-consumer/cleanup.json']
    report=values['cpu-consumer/ATTRIBUTION.json'];child=values['cpu-consumer/SAVED-PAIR-INDEPENDENT-CHILD.json']
    owned=values['cpu-consumer/OWNED.json']
    C.need(owner['schema']=='bole.native-ar-saved-evidence-owner/v4'and owner['inputs']==refs['INPUTS.json']and
        owner['primary']is not None and owner['secondary']==[]and owner['source_before']==owner['source_after']and
        len(owner['source_before'])==834 and owner['independent_numeric_requalification_pass']is False and
        release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[]and
        child['exit_code']!=0 and child['child_termination_observed']is True,'actual clean source-equal numerical failure, never pass')
    C.need(release['container']==owned['cid']and owned['image']==C.IMAGE and owned['arm']=='cpu-preflight'and
        child['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']]and
        all(owner['summary']['failure_release'][k]==refs['cpu-consumer/cleanup.json'][k]for k in('path','sha256')),
        'same exact failed numerical CPU owner/child and stopped-retained release')
    C.need(report['native_AR_full_TP_greedy_verified']is True and report['all_actual_worker_retirements_verified']is True and
        report['native_AR_actual_PA_FIA_pointwise_pass']is False and report['native_AR_reference_smoke_pass']is False and
        report['token_identity_pass']is True and report['bounded_pair_pass']is False,'actual numeric failure despite complete greedy identity')
    C.need('actual original native paged FA frame exceeds original pointwise bound'in
        C.checked(refs['cpu-consumer/SAVED-PAIR-INDEPENDENT.stderr']).read_text(),'actual original pointwise rejection')
    control=values['cpu-consumer/NATIVE-MASK-CONTROLS.json'];g1=values['cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json']
    C.need(control['positive_control_pass']is True and control['negative_count']==11 and all(r['rejected']is True for r in control['negative_controls'])and
        g1['G1_experiment_pass']is True and g1['component_checks_pass']is True and g1['service_complete']is True,
        'actual all mask controls and original full G1 already passed; no rerun here')
    r=old['files']['saved_common.py']
    C.need((r['bytes'],r['sha256'])==(18903,'9e79c49a440317456dd9cea6da03c12d9473bceb3c3d9f9ee6244b3d9aa7eb08'),'exact frozen numerical-v4 source helper before import')
    B=C.load(r,'_numeric_original_saved_v4');B.source(C,refs['INPUTS.json'])
    return refs,values,owner,old,B


def readset(C,y,*,installed=False):
    refs,values,owner,old,B=prior(C,y)
    C.need(y['original_numeric_inputs']==refs['INPUTS.json'],'unchanged original numerical source ticket')
    x,m,on,base,mapping=B.readset(C,old,installed=installed)
    C.need(y['AR_source']==x['AR_source']and y['authority']==x['authority'],'same actual AR/authority chain')
    current={r['path']:r['sha256']for r in(*base,refs['INPUTS.json'])}
    C.need(all(current.get(p)==sha for p,sha in owner['source_before'].items()),'all834 original numerical-v4 immutable sources reopened')
    extra,_=B.collect(C,[values,refs,y['files']],{row['installed']['path']:row for row in mapping['mapping']},installed=installed)
    unique={}
    for r in(*base,*extra,refs['INPUTS.json']):
        C.need(r['path']not in unique or unique[r['path']]==r,'one exact immutable numerical diagnostic readset');unique[r['path']]=r
    owned=values['cpu-consumer/OWNED.json'];guest=values['cpu-consumer/GUEST_CPU.json']
    C.need(owned['guest_cpus']==[0]and guest['affinity']==guest['effective_cpus']==guest['ancestor_cpuset']==[0]and
        guest['effective_capacity']==1,'actual original CPU0 no-model profile')
    return x,m,on,list(unique.values()),dict(original_numeric_mapping=mapping,
        actual_CPU_profile=dict(owned=refs['cpu-consumer/OWNED.json'],guest=refs['cpu-consumer/GUEST_CPU.json'],guest_cpus=[0]),
        original834_sources_reopened=True,full_G1_math_rerun=False,mathematical_qualification=False,NPU=False)
