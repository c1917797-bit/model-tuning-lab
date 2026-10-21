"""Exact successful NUMdiag prerequisite and original025 readset; no tensor imports."""
import importlib.util
from pathlib import Path
import re

LOCK='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock'
FILES=('ar_owner_common.py','ar_saved_namespace.py','fsum_common.py','prepare_fsum_owner.py',
    'fsum_cpu_owner.py','fsum_oracle.py','ACTUAL_NUMDIAG_REFS.json','ACTUAL_NUMDIAG_UNIT_REF.json')


def common():
    import hashlib
    p=Path(__file__).parent/'ar_owner_common.py';b=p.read_bytes()
    if(len(b),hashlib.sha256(b).hexdigest())!=(19055,'5d0b9034706b9a942a4d7dd10870139959b22dfaab2cebbdddf25ba962e456a4'):
        raise ValueError('exact original AR025 source')
    s=importlib.util.spec_from_file_location('_fsum_original_common',p);C=importlib.util.module_from_spec(s);s.loader.exec_module(C);return C


def successful_numeric(C):
    refs=C.obj(C.ref(Path(__file__).parent/'ACTUAL_NUMDIAG_REFS.json'))
    values={n:C.obj(r)for n,r in refs.items()if n.endswith('.json')}
    for r in refs.values():C.checked(r)
    ur=C.obj(C.ref(Path(__file__).parent/'ACTUAL_NUMDIAG_UNIT_REF.json'));unit=C.obj(ur)
    C.need((ur['bytes'],ur['sha256'])==(582,'ca9ba17fdcc96ce678c121be0cc7b447e7fbe80372b86df66020650a4b023adc')and
        unit['schema']=='bole.actual-MAIN-finite-unit-terminal/v1'and unit['exit_code']==0 and
        unit['unit']=='bole-native-ar-numdiag-20261020t154710z-v1.service'and
        unit['argv']==['systemctl','show',unit['unit'],'--property=Id,MainPID,ControlPID,ActiveState,SubState,ExecMainStatus,Result,Restart,Type,RemainAfterExit,TasksCurrent,Job'],
        'exact actual whole owner unit terminal after namespace finally')
    fields=[row.split('=',1)for row in unit['stdout'].splitlines()]
    C.need(all(len(row)==2 for row in fields)and len({k for k,_ in fields})==len(fields),'unique actual systemd terminal properties')
    properties=dict(fields)
    C.need(all(properties.get(k)==v for k,v in dict(Id=unit['unit'],Type='exec',Restart='no',RemainAfterExit='yes',MainPID='0',
        ControlPID='0',Result='success',ExecMainStatus='0',ActiveState='active',SubState='exited',Job='').items()),
        'actual exact owner and its source-owned inverse finally returned0; no live unit process')
    values['UNIT_TERMINAL.json']=unit
    old=values['INPUTS.json'];owner=values['RESULT.json'];report=values['NUMERIC-DIAGNOSTIC.json']
    release=values['cpu-consumer/cleanup.json'];owned=values['cpu-consumer/OWNED.json']
    child=values['cpu-consumer/NUMERIC-DIAGNOSTIC-CHILD.json']
    C.need(owner['schema']=='bole.native-ar-numeric-diagnostic-finite-owner/v1'and
        owner['inputs']==report['inputs']==refs['INPUTS.json']and owner['primary']is None and owner['secondary']==[]and
        owner['source_before']==owner['source_after']and len(owner['source_before'])==874 and owner['diagnostic_completed']is True and
        owner['entry_clock_before_source_replay']is True and owner['mathematics_recomputed']is True and
        owner['guest_CPU']==0 and owner['Devices']==[]and owner['NPU']is False,'actual complete unchanged-source finite NUMdiag, no inferred pass')
    C.need(release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[]and
        release['container']==owned['cid']and owned['arm']=='cpu-preflight'and owned['guest_cpus']==[0]and owned['image']==C.IMAGE and
        all(owner['summary']['release'][k]==refs['cpu-consumer/cleanup.json'][k]for k in('path','sha256'))and
        child['exit_code']==0 and child['child_termination_observed']is True and
        child['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']],'exact real CPU-only child and stopped-retained owner')
    C.need(report['rank_count']==4 and report['frame_count']==128 and report['current_failure_frame_count']==16 and
        report['mathematics_recomputed']is True and report['weights_only_load']is True and report['original_pointwise_bound_preserved']is True and
        report['original_G1_math_rerun']is False and report['stage_models_are_qualified_oracles']is False and
        all(report[k]is False and owner[k]is False for k in('NPU','mask_semantics_qualified','native_FA_math_qualified',
            'native_AR_numeric_pass','common_effects_pass','model_ready','performance_ready','formal_success')),
        'actual all128 diagnostic result, every qualification still false')
    C.need(old['files']['numeric_common.py']['bytes']==6416 and
        old['files']['numeric_common.py']['sha256']=='09d821ffc3f017c12487d88b930be392bd2f8064ff4fb9eaa60b023ab54f345e',
        'exact already-successful NUMdiag complete source before import')
    D=C.load(old['files']['numeric_common.py'],'_fsum_successful_numeric_common');D.source(C,refs['INPUTS.json'])
    return refs,values,owner,old,D


def held_main_lock(C):
    _,_,_,_,D=successful_numeric(C);return D.held_main_lock(C)


def source(C,ir):
    y=C.obj(ir)
    C.need(y['schema']=='bole.native-ar-fsum-oracle-inputs/v1'and y['files']['fsum_common.py']==C.ref(__file__)and
        y['MAIN_lock']==LOCK and y['default_enabled']is False and y['prepared_only']is True,'new exact defaultOFF fsum source')
    for r in y['files'].values():C.checked(r)
    p=Path(y['output_root'])
    C.need(p.parent==Path('/opt/host/vnf/austinov')and re.fullmatch('run-bole-native-ar-fsum-[a-z0-9-]{1,15}',p.name)is not None and
        y['consumer_output_root']==str(p/'cpu-consumer'),'new sole fsum CPU output leaf')
    return y


def readset(C,y,*,installed=False):
    refs,values,owner,old,D=successful_numeric(C)
    ur=C.obj(C.ref(Path(__file__).parent/'ACTUAL_NUMDIAG_UNIT_REF.json'))
    C.need(y['actual_NUMdiag_refs']==refs and y['actual_NUMdiag_unit_ref']==ur and y['original_NUMdiag_inputs']==refs['INPUTS.json'],
        'actual successful NUMdiag source and post-finally unit terminal tickets')
    x,m,on,base,mapping=D.readset(C,old,installed=installed)
    C.need(y['AR_source']==x['AR_source']and y['authority']==x['authority'],'same actual AR/authority chain')
    current={r['path']:r['sha256']for r in(*base,refs['INPUTS.json'])}
    C.need(all(current.get(p)==sha for p,sha in owner['source_before'].items()),'all874 actual NUMdiag immutable sources reopened')
    B=C.load(C.obj(old['original_numeric_inputs'])['files']['saved_common.py'],'_fsum_original_saved_common')
    mapping_rows=mapping['original_numeric_mapping']['mapping']
    extra,_=B.collect(C,[values,refs,ur,y['files']],{r['installed']['path']:r for r in mapping_rows},installed=installed)
    unique={}
    for r in(*base,*extra,refs['INPUTS.json']):
        C.need(r['path']not in unique or unique[r['path']]==r,'one exact fsum immutable readset');unique[r['path']]=r
    return x,m,on,list(unique.values()),dict(original_NUMdiag_mapping=mapping,
        actual_CPU_profile=mapping['actual_CPU_profile'],original874_sources_reopened=True,
        actual_owner_unit_terminal=ur,source_owned_namespace_finally_exited_cleanly=True,
        original_G1_math_rerun=False,mathematical_qualification=False,NPU=False)
