"""Stdlib provenance/readset contract for one new bounded G1 GDN probe."""
import importlib.util
import json
from pathlib import Path
import sys

SCOPE=dict(schema='bole.c1-two-request-service/v1',prefix=131,request_count=2,
           max_steps_per_request=1,max_output_tokens=2)
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PRIOR_SOURCE=(109479,'010914ebe1bf5d3e6b516103e1a376e24e0a0d965ac0a3a42d7aeb19fca57677')
PRIOR_OWNER=(131517,'52030a932da1f3cd2392389a2d9246925e40c2d93186b5f67d41fba8cfa1e4fc')
PRIOR_REPORT=(12221,'8caf55b28f4a3c4108b8b932e9c664e08b3c28ea18f0bf4fc3bdf62de3538d53')


def load(C,r,name):
    C.checked(r)
    if name in sys.modules:
        value=sys.modules[name];C.need(C.ref(value.__file__)==r,'exact private probe helper');return value
    s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);sys.modules[name]=v
    try:s.loader.exec_module(v);C.need(C.ref(v.__file__)==r,'helper bytes unchanged across import')
    except BaseException:sys.modules.pop(name,None);raise
    return v


def fullref(C,r):
    C.need(type(r)is dict and set(r)in({'path','bytes','sha256'},{'path','sha256'}),'exact Ref2/Ref3 input')
    actual=C.ref(r['path']);C.need(actual['sha256']==r['sha256']and('bytes'not in r or actual['bytes']==r['bytes']),
                                'actual complete legacy Ref upgraded without changing digest')
    C.checked(actual);return actual


def prior(C,refs):
    C.need(set(refs)=={'source','owner','bundle','independent'},'exact successful G1 prior chain')
    on,own,b,v=[C.obj(refs[k])for k in('source','owner','bundle','independent')]
    for key,pin in(('source',PRIOR_SOURCE),('owner',PRIOR_OWNER),('independent',PRIOR_REPORT)):
        C.need((refs[key]['bytes'],refs[key]['sha256'])==pin,'actual exact successful G1-v2 '+key)
    C.need(on['service_experiment']==SCOPE and on['prepared_only']is False and
        own['source']==refs['source']and own['primary']is None and own['secondary']==[]and own['cpu_only']is False and
        own['source_before']and own['source_before']==own['source_after']and own['summary']['independent']==refs['independent']and
        b['source']==refs['source']and b['schema']=='bole.actual-four-rank-two-request-inputs/v1'and
        v['source']==refs['source']and v['inputs']==refs['bundle']and v['schema']=='bole.actual-c1-two-request-service-independent/v1'and
        v['completed_request_count']==2 and all(v[k]is True for k in('service_complete','component_checks_pass',
        'scheduler_committed_independently','actual_all4_retirement','actual_HTTP_output_token_ID_join'))and
        all(v[k]is False for k in('model_ready','task_ready','performance_ready','formal_success')),
        'real independently successful bounded G1 owner/component/HTTP/retirement prerequisite')
    for r in on['files'].values():
        C.checked(r);C.need(own['source_before'].get(r['path'])==r['sha256'],'prior owner covers every unchanged actual source')
    for k in('CPU_release','model_release','independent_release'):
        released=C.obj(fullref(C,own['summary'][k]));C.need(released['stopped']is True and released['retained']is True and
            released['errors']==[],'all actual G1 owners stopped retained before new probe')
    return on,own,b,v


def json_report(C,text,source,count):
    """Ignore non-JSON log lines, require ONE exact schema, then exact source.

    Never assume the report is the last stdout line. Duplicate/stale schema
    reports fail, even if another report would match. Preserve full stdout.
    """
    C.need(type(text)is str and len(text.encode())<=8*2**20,'bounded full original software stdout')
    matches=[]
    for line in text.splitlines():
        try:value=json.loads(line)
        except json.JSONDecodeError:continue
        if type(value)is dict and value.get('schema')=='bole.g1-cold-aggregate-software/v1':matches.append(value)
    C.need(len(matches)==1,'one unique actual G1 software report schema in full stdout')
    value=matches[0]
    C.need(value['source']==source and value['tests']==count and count>=214 and
        value['all_tests_passed']is True and value['complete_readset_audited']is True and
        value['NPU']is False and value['actual_scheduler_executed']is False and
        len(value['actual_cold_cli'])==10 and all(r['exit_code']==0 for r in value['actual_cold_cli']),
        'actual same-source complete original214 plus declared added tests and ten cold CLIs')
    return value


def software(C,reference,sr,m):
    gate=C.obj(reference)
    C.need(gate['schema']=='bole.gdn-g1-actual-software-handoff/v1'and gate['source']==sr and
        gate['owner']=='MAIN'and gate['actual_report']==json_report(C,C.checked(gate['stdout']).read_text(),sr,
        m['service_required_sameimage_software_cases']),'actual structured report matches original whole stdout')
    child=C.obj(gate['child']);release=C.obj(gate['release']);C.checked(gate['stderr'])
    C.need(child['exit_code']==0 and child['child_termination_observed']is True and
        fullref(C,child['stdout_ref'])==gate['stdout']and fullref(C,child['stderr_ref'])==gate['stderr']and
        child['requested_argv'][-2:]==[m['files']['service_entry.py']['path'],'--software']and
        release['stopped']is True and release['retained']is True and release['errors']==[]and
        release['container']==child['requested_argv'][child['requested_argv'].index('exec')+1],
        'actual software child exit/argv/stdout/stderr and same completed CPU owner release')
    inspect=C.obj(fullref(C,release['after_inspect']));rows=json.loads(inspect['stdout'])
    C.need(len(rows)==1 and rows[0]['Id']==release['container']and rows[0]['Image']==IMAGE and
        rows[0]['State']['Running']is False and not rows[0]['HostConfig'].get('Devices'),
        'actual stopped same-image Devices[] software owner, not asserted admission')
    return gate['actual_report']


def materialize_software(C,root,child_ref,release_ref,sr,m):
    root=Path(root);child_ref=fullref(C,child_ref);release_ref=fullref(C,release_ref);child=C.obj(child_ref)
    stdout=fullref(C,child['stdout_ref']);stderr=fullref(C,child['stderr_ref'])
    C.need(Path(stdout['path'])==root/'SOFTWARE.stdout'and Path(stderr['path'])==root/'SOFTWARE.stderr',
           'actual fixed CPU phase software outputs only')
    report=json_report(C,C.checked(stdout).read_text(),sr,m['service_required_sameimage_software_cases'])
    value=dict(schema='bole.gdn-g1-actual-software-handoff/v1',source=sr,owner='MAIN',child=child_ref,
        stdout=stdout,stderr=stderr,release=release_ref,actual_report=report,
        source_preflight_only=True,actual_NPU_admission_granted=False,model_ready=False,formal_success=False)
    result=C.write(root/'GDN-SOFTWARE-HANDOFF.json',value);software(C,result,sr,m);return result
