"""Five exact-source software stages in the original finite diagnostic lane."""
import json,os,sys,time
from pathlib import Path
import sourceio as C
from g2_software_stages import Budget,process,finite,metadata_gate,one,CAPS,LANE_CAP,PHASE,CLEANUP
SOURCE13=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json',bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
SCHEMA='bole.G3-five-source-staged-software-scope/v1'
RESULT_SCHEMA='bole.actual-G3-five-source-staged-software-gate/v1'

def scope(m,sr):
    old=C.obj(SOURCE13);prior=old['service_software_scope'];s=m['service_software_scope']
    expected=dict(schema=SCHEMA,parent_source=prior['parent_source'],parent_exact_cases=279,
        controls_source=prior['controls_source'],controls_source_cases=25,
        historical_stage_source=prior['historical_stage_source'],historical_stage_cases=18,
        historical_ACK_source=SOURCE13,historical_ACK_cases=27,
        historical_runner_ref=old['files']['g2_exact_controls.py'],
        parent_suite_runs_in_separate_exact_source_process=True,
        controls_run_only_tests_in_exact_source_process=True,
        current_pattern='test_g3_*.py',new_current_cases=32,
        allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP)
    C.need(s==expected and old['service_required_sameimage_software_cases']==349
        and prior['new_current_cases']==27 and m['service_required_sameimage_software_cases']==381
        and CAPS==dict(parent279=120.,controls=60.,metadata=120.)
        and LANE_CAP==300. and PHASE==3600. and CLEANUP==180.,
        '279+25+18+27+32 explicit exact-source contexts in original300/3600/180')
    C.need(C.checked(m['files']['g2_software_stages.py']).read_bytes()==
        C.checked(old['files']['g2_software_stages.py']).read_bytes(),
        'current immutable Budget/process/metadata/one source equals whole actual13 original')
    C.checked(s['historical_runner_ref'])
    return s

def run(sr,*,phase_entry,lane_start,lane_deadline,guest_entry):
    b=Budget(phase_entry,lane_start,lane_deadline,1792597630,guest_entry)
    m=C.obj(sr);s=scope(m,sr);P=Path(m['root'])
    C.need(C.ref(__file__)==m['files']['g3_software_stages.py'],'source-bound G3 coordinator')
    import g3_validate as V
    C.need(C.ref(V.__file__)==m['files']['g3_validate.py'],'actual current full G3 validation module')
    proof=V.validate(sr)
    C.need(type(proof)is dict and proof.get('source_validated')is True
        and proof.get('source')==sr
        and proof.get('schema')=='bole.G3-fixed131-long1024-source-validation/v1',
        'actual complete G3 source/parent/profile validation result, never caller PASS stub')
    b.check()
    options=[Path(m['output_root'])/'cpu-preflight',Path(m['output_root']+'-CPU')/'cpu-preflight']
    matches=[p for p in options if p.is_dir()and p.samefile('/adakv-results')]
    C.need(len(matches)==1,'one actual preexisting owned RW output, no source writes')
    actual=matches[0];root=actual/'G3-SOFTWARE';root.mkdir()
    admission=C.write(root/'ADMISSION.json',dict(
        schema='bole.actual-G3-five-source-software-admission/v1',source=sr,
        phase_entry=phase_entry,lane_start=lane_start,lane_deadline=lane_deadline,
        guest_entry=guest_entry,allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP,
        validation_elapsed_before_parent=time.monotonic()-lane_start,
        original_phase_seconds=PHASE,original_cleanup_seconds=CLEANUP,fixed_cutoff=1792597630))
    parent=C.obj(s['parent_source']);entry=C.checked(parent['files']['service_entry.py'])
    C.need(entry==Path(parent['root'])/'service_entry.py','exact original source8 whole279 entry')
    env={k:v for k,v in os.environ.items()if not k.startswith('BOLE_')}
    ev,elapsed=process(root/'PARENT279','parent279',
        [sys.executable,'-I','-B',str(entry),'--software'],b.remaining('parent279'),source=sr,env=env)
    b.exclude(elapsed)
    from g2_cold_parent_output import extract,alias_exports
    prior=extract(C.checked(ev['stdout']).read_bytes(),s['parent_source'],parent)
    exports=alias_exports(prior['parent_software_evidence'],Path(parent['output_root'])/'cpu-preflight',actual)
    extraction=C.write(root/'PARENT279/EXTRACTION.json',dict(
        schema='bole.actual-three-source-parent-extraction/v11',source=sr,
        parent_source=s['parent_source'],stage=ev,original_summary=prior,
        original_guest_evidence_to_actual_host_refs=exports,
        original_source_owned_extract_used=True,original_G1_and_G2_controls_really_rerun=True,NPU=False))
    b.check();controls={}
    historical=(('source10',25,s['controls_source'],'source10','test_g2_cold*.py'),
                ('source11',18,s['historical_stage_source'],'source11','test_g2_stage*.py'),
                ('source13',27,SOURCE13,'current12','test_g2_ack*.py'))
    for role,count,test_source,inner_role,pattern in historical:
        argv=[sys.executable,'-I','-B',str(C.checked(s['historical_runner_ref'])),
            '--execute','--source-ref',json.dumps(SOURCE13),'--role',inner_role]
        row,cost=process(root/role,role,argv,b.remaining('controls'),source=sr)
        value=one(C.checked(row['stdout']).read_bytes(),'bole.actual-exact-source-only-unittest/v12')
        wanted=dict(schema='bole.actual-exact-source-only-unittest/v12',source=SOURCE13,
            test_source=test_source,role=inner_role,pattern=pattern,tests=count,
            all_tests_passed=True,skipped=0,cached_PASS_reused=False,
            original_software_entry_invoked=False,NPU=False)
        C.need(value==wanted,'unchanged historical inner source/role/schema and exact count; not G3 namespace')
        controls[role]=dict(stage=row,result=value,logical_role=role);b.check()
    argv=[sys.executable,'-I','-B',str(C.checked(m['files']['g3_exact_controls.py'])),
        '--execute','--source-ref',json.dumps(sr)]
    row,cost=process(root/'currentG3','currentG3',argv,b.remaining('controls'),source=sr)
    value=one(C.checked(row['stdout']).read_bytes(),'bole.actual-G3-current-only-unittest/v1')
    C.need(value==dict(schema='bole.actual-G3-current-only-unittest/v1',source=sr,
        test_source=sr,role='currentG3',pattern='test_g3_*.py',tests=32,
        all_tests_passed=True,skipped=0,cached_PASS_reused=False,
        original_software_entry_invoked=False,NPU=False),
        'actual current G3 all32 including tensor4, no historical shadowing or skipped case')
    controls['currentG3']=dict(stage=row,result=value,logical_role='currentG3');b.check()
    metadata_path=root/'METADATA.json'
    meta,cost=process(root/'METADATA','metadata',[
        sys.executable,'-B',str(C.checked(m['files']['service_metadata.py'])),
        '--execute','--source-ref',json.dumps(sr),'--output',str(metadata_path)],
        b.remaining('metadata'),source=sr)
    b.exclude(cost);installed=C.obj(C.ref(metadata_path));metadata_gate(installed,sr)
    C.need(one(C.checked(meta['stdout']).read_bytes(),installed['schema'])==installed,
        'original full current metadata CLI stdout/file agree')
    b.check()
    value=dict(schema=RESULT_SCHEMA,source=sr,tests=381,source8_fresh_cases=279,
        source10_fresh_cases=25,source11_fresh_cases=18,source13_fresh_cases=27,
        currentG3_fresh_cases=32,all_tests_passed=True,admission=admission,
        parent_source=s['parent_source'],parent_software_result=prior,
        parent_software_evidence=dict(stage=ev,extraction=extraction),controls=controls,
        actual_installed_metadata=installed,actual_installed_metadata_ref=C.ref(metadata_path),
        metadata_stage=meta,source_validated=proof,phase_entry=phase_entry,lane_start=lane_start,
        lane_deadline=lane_deadline,elapsed_seconds=time.monotonic()-lane_start,
        controls_total_elapsed_seconds=time.monotonic()-lane_start-b.excluded,
        allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP,NPU=False,
        actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)
    C.write(root/'RESULT.json',value);b.check()
    C.need(time.monotonic()<=lane_deadline,'same finite lane includes final software export')
    return value

def host_run(C,c,H,ctl,sr,entry_start):
    m=C.obj(sr);s=scope(m,sr)
    C.need(C.ref(__file__)==m['files']['g3_software_stages.py']
        and ctl.deadline==entry_start+PHASE and ctl.created_monotonic==entry_start,
        'original host firstentry/controller with source-bound five-source G3 coordinator')
    now=time.monotonic();available=min(LANE_CAP,ctl.remaining(cap=LANE_CAP))
    C.need(finite(available)and available>0,'remaining original phase admits one finite software lane')
    deadline=now+available
    C.need(deadline<=entry_start+PHASE-CLEANUP+0.01,'no renewed G3 software/phase deadline')
    args=[str(Path(__file__).with_name('service_entry.py')),'--software',
        '--phase-entry',repr(entry_start),'--lane-start',repr(now),'--lane-deadline',repr(deadline)]
    C.write(ctl.out/'SOFTWARE-ADMISSION.json',dict(
        schema='bole.actual-host-software-allocation/v11',source=sr,
        phase_entry=entry_start,lane_start=now,lane_deadline=deadline,allocated_seconds=available,
        allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP,requested_args=args,
        original_phase_seconds=PHASE,original_cleanup_seconds=CLEANUP))
    result=H.child(ctl,'SOFTWARE',args,
        min(deadline-time.monotonic(),ctl.remaining(cap=LANE_CAP)),observe=False)
    raw=C.checked(C.ref(ctl.out/'SOFTWARE.stdout')).read_bytes();value=one(raw,RESULT_SCHEMA)
    C.need(value['source']==sr and value['phase_entry']==entry_start
        and value['lane_start']==now and value['lane_deadline']==deadline
        and value['all_tests_passed']is True and value['tests']==381
        and value['source8_fresh_cases']==279 and value['source10_fresh_cases']==25
        and value['source11_fresh_cases']==18 and value['source13_fresh_cases']==27
        and value['currentG3_fresh_cases']==32
        and set(value['controls'])=={'source10','source11','source13','currentG3'}
        and value['allocation_seconds']==CAPS and value['aggregate_cap_seconds']==LANE_CAP
        and 0<=value['controls_total_elapsed_seconds']<=CAPS['controls']
        and 0<=value['elapsed_seconds']<=deadline-now,
        'complete actual five-source381 metadata and clocks, never child exit alone')
    return result
