"""Read-only exact G2-v6 source closure after actual complete model qualification."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v6/SOURCE_BOUND.json',
            bytes=475051,sha256='41a3ffb818e9163515f4bc2e15ab46f2ffbd301ae8a28c7c14e2f209ef92cfd1')


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--model-owner-ref')
    p.add_argument('--frozen-auditor-ref')
    a=p.parse_args()
    if not a.execute:
        print('{"enabled":false,"NPU":false}')
        return 0
    if not a.model_owner_ref or not a.frozen_auditor_ref:
        raise ValueError('actual complete model owner and frozen read-only auditor required')
    ar=json.loads(a.frozen_auditor_ref)
    path=Path(ar['path']);b=path.read_bytes()
    if set(ar)!={'path','bytes','sha256'} or not path.is_absolute() or any(x.is_symlink() for x in(path,*path.parents)) or len(b)!=ar['bytes'] or hashlib.sha256(b).hexdigest()!=ar['sha256']:
        raise ValueError('exact complete ordinary prior auditor')
    spec=importlib.util.spec_from_file_location('_exact_frozen_g2_readset_audit',path)
    A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    A.checked(ar);sr=A.ref(SOURCE['path']);A.need(sr==SOURCE,'only actual immutable G2-v6')
    owner_ref=json.loads(a.model_owner_ref);owner=A.obj(owner_ref)
    A.need(owner_ref['path']=='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v6/RESULT.json' and
        owner['source']==sr and owner['primary'] is None and owner['secondary']==[] and owner['cpu_only'] is False and
        owner['source_before']==owner['source_after'] and owner['source_before'], 'actual clean finite model owner')
    def legacy_ref(r):
        value=A.ref(r['path']);A.need(value['sha256']==r['sha256'] and ('bytes' not in r or value['bytes']==r['bytes']), 'whole exact legacy evidence')
        return value
    child_ref=legacy_ref(owner['summary']['actual_software_child']);child=A.obj(child_ref)
    A.need(child['exit_code']==0 and child['child_termination_observed'] is True, 'actual software process succeeded')
    stdout_ref=legacy_ref(child['stdout_ref']);stderr_ref=legacy_ref(child['stderr_ref']);A.checked(stderr_ref)
    matches=[]
    for line in A.checked(stdout_ref).read_text().splitlines():
        try:value=json.loads(line)
        except ValueError:continue
        if type(value) is dict and value.get('schema')=='bole.G2-explicit-combined-software-gate/v1':
            matches.append(value)
    A.need(len(matches)==1, 'one unique actual complete software report')
    q=matches[0]
    A.need(q['source']==sr and q['tests']==258 and q['historical_cases']==214 and q['current_cases']==44 and
        q['all_tests_passed'] is True, 'actual258 same-image controls on this exact source')
    release_refs={}
    for key in ('CPU_release','model_release','independent_release'):
        r=legacy_ref(owner['summary'][key]);v=A.obj(r)
        A.need(v['stopped'] is True and v['retained'] is True and v['errors']==[], 'all actual owners stopped retained')
        release_refs[key]=r
    report_ref=legacy_ref(owner['summary']['independent']);report=A.obj(report_ref)
    A.need(report['source']==sr and report['service_complete'] is True and report['every_frame_independently_consumed'] is True and
        report['component_checks_pass'] is True and report['all4_worker_retirement_verified'] is True,
        'actual complete all-frame model consumer prerequisite')
    value=A.audit(sr)
    value.update(schema='bole.G2-readonly-source-preparation-audit-supplement/v6',audit_source=A.ref(Path(__file__).absolute()),
        frozen_readset_auditor=ar,actual_software_cases=258,model_owner=owner_ref,software_child=child_ref,
        software_stdout=stdout_ref,software_stderr=stderr_ref,independent=report_ref,releases=release_refs,
        source_preparation_supplement_only=True,CPU_or_NPU_execution_qualified=False)
    value.pop('CPU242_preflight_still_required',None);value.pop('original_v3_audit_preparer',None)
    value['retained_actual_builder']=A.obj(sr)['g2_parent_prerequisites_v3']['actual_preparer']
    value['correction']='Reopen exact v6/G1 closure using unchanged source-owned readset and literal COMMANDS checks.'
    print(json.dumps(value,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
