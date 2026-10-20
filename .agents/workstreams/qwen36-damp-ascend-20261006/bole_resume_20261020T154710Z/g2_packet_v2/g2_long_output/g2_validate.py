"""Pure source/qualification closure; no device or controller admission."""
import ast
import hashlib
from pathlib import Path
import sourceio as C
import g2_contract as G2

MATH_UNCHANGED=('core112.py','adapter.py','oracle112.py','native_seams.py','treeconv118.py',
    'independent_model.py','model_entry.py','service_bridge.py','service_fia.py',
    'model_process_calibration.py','model_calibration131r12.py','calibrate_conv118.py')


def parent_qualified(sr,m,owner_ref,report_ref):
    owner=C.obj(owner_ref);report=C.obj(report_ref)
    C.need(m['service_experiment']==dict(schema='bole.c1-two-request-service/v1',prefix=131,
        request_count=2,max_steps_per_request=1,max_output_tokens=2)and
        m['prepared_only']is False and m['default_enabled']is False and 'g1_repair_v2'in m,
        'exact actual G1-v2 parent source, never failed-v1/source-only readiness')
    C.need(owner['source']==sr and owner['primary']is None and owner['secondary']==[]and
        owner['source_before']==owner['source_after']and owner['cpu_only']is False,
        'actual successful clean finite G1-v2 TP4 model owner, not CPU211/214 alone')
    C.need(owner['summary']['independent']==report_ref and report['source']==sr and
        report['service_complete']is True and report['completed_request_count']==2 and
        report['component_checks_pass']is True and report['scheduler_committed_independently']is True and
        report['model_ready']is False and type(report['slot_reuse_observed'])is bool,
        'actual independent two-request all4 component/retirement attribution')
    C.need(report['actual_all4_retirement']is True and len(report['ranks'])==4 and
        all(len(C.obj(r)['requests'])==2 and all(v['actual_final_retirement_observed']is True for v in C.obj(r)['requests'])for r in report['ranks']),
        'actual all4 retirement joined in parent independent report')
    for r in m['files'].values():C.checked(r)
    return True


def validate(sr):
    m=C.obj(sr);root=Path(m['root']);prior=m['g2_predecessor'];parent=C.obj(prior['source'])
    C.need(root==Path(__file__).resolve().parent and m['service_experiment']==G2.SCOPE and
        G2.SCOPE['profile']=='smoke4'and m['default_enabled']is False,
        'explicit new defaultOFF output4 stream scope;1024 successor not silently enabled')
    parent_qualified(prior['source'],parent,prior['owner_result'],prior['qualification'])
    for r in(*m['files'].values(),*m['runtime_sources'].values(),*m['dependencies']):C.checked(r)
    C.need(m['stream_consumer_source']==m['files']['g2_consumer.py']and
        m['stream_consumer_source']['sha256']==m['reviewed_stream_consumer']['sha256'],
        'explicit separate exact independently reviewed streaming consumer Ref')
    for name in MATH_UNCHANGED:
        C.need(Path(m['files'][name]['path']).read_bytes()==C.checked(parent['files'][name]).read_bytes(),
            'byteexact qualified parent numerical/calibration reference '+name)
    proof=C.obj(m['files']['G2_STREAM_EDITS_V1.json'])
    C.need(proof['baseline']==prior['source']and proof['schema']=='bole.exact-G2-stream-inverse-to-G1v2/v1',
        'exact current lifecycle/capture delta source ledger')
    for name,row in proof['files'].items():
        C.need(row['before']==parent['files'][name]and row['after']==m['files'][name]and
            row['edits']==[dict(before=C.checked(row['before']).read_text(),after=C.checked(row['after']).read_text())],
            'complete whole-file exact G2 inverse, no unknown lifecycle change '+name)
    import g2_executor_proof as EP
    C.need(EP.consume(m['stream_executor_sources'])==m['stream_executor_proof']and
        EP.installed(m['stream_executor_sources'])==m['stream_runtime_sources'],
        'exact complete launcher proof and installed source pins')
    for r in m['stream_executor_sources'].values():
        data=C.checked(r).read_bytes();compile(data,r['path'],'exec')
    import command_contract
    commands=command_contract.validate(C,sr,m)
    return dict(source_validated=True,NPU=False,actual_scheduler_executed=False,
        model_ready=False,commands=commands,parent_source=prior['source'],scope=G2.SCOPE)
