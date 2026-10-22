"""Pure complete-source short8 FAST qualification renderer. Never freezes/launches."""
import copy
import json
import ast
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
WORK=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PERF=WORK/'performance_followup_prepare_20261022T203100Z'
SHORT=WORK/'bound-reduction-ON-v6-common_20261022T210000Z'
SHORT_REF=dict(path=str(SHORT/'SOURCE_BOUND.json'),bytes=1642902,
    sha256='74b2f3f82c97e91ff1c0d77e439631a7e7aa62345c46b3ea4428ca80dd16426d')
sys.path.insert(0,str(HERE))
import qualification_parent_renderer as R
import qualification_tap_delta as TAP

HELPERS=('fastpath_numeric_observer.py','fastpath_numeric_consumer.py','fastpath_numeric_sink.py',
         'qualification_tap_delta.py','qualification_state_probe.py','qualification_smoke_join.py',
         'qualification_short_prepare.py','qualification_source_validate.py','qualification_source_producer.py',
         'qualification_parent_renderer.py',
         'test_qualification_entry.py')
QUAL=dict(schema='bole.fastpath-numeric-qualification-profile/v1',enabled=True,input_tokens=131,
          output_tokens=8,generations=2,logical_frame_cap=384*2**20,
          independent_reference=True,formal_performance=False)

def need(v,s):
    if not v:raise ValueError(s)

def exact_short_sources(reference=None):
    reference=SHORT_REF if reference is None else reference
    source=json.loads(R.checked(reference))
    names=('short_state_digest.py','compare_state_digest.py','performance_client_consumer.py',
           'bole_performance_profile.py','prepare_short_gate.py')
    return {n:R.checked(source['files'][n])for n in names},reference

def short_policy(text):
    # Qualification is a distinct, default-OFF mode. Formal1024 policy and
    # original math/write elisions remain identical, never admitted by short8.
    a='''    need(scope['input_tokens']==131 and scope['output_tokens']==1024 and scope['concurrency']==1,
         'fixed original131/1024/C1 screening domain')
    need(all(environ.get(k) in(None,'','0') for k in (
        'BOLE_NATIVE_BOUNDARY_PROBE_ENABLE','BOLE_NATIVE_PROJECTION_PROBE_ENABLE',
        'BOLE_SHORT_STATE_DIGEST_ENABLE','BOLE_G3_STREAM_ENABLE')),
         'no diagnostic raw/state/stream modes in performance candidate')'''
    b='''    qualifier=environ.get('BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE')=='1'
    if qualifier:
        need(scope['input_tokens']==131 and scope['output_tokens']==8 and scope['concurrency']==1
             and manifest.get('fastpath_numeric_qualification')is not None
             and environ.get('BOLE_SHORT_STATE_DIGEST_ENABLE')=='1',
             'explicit short8 FAST numerical qualifier, never timed screening')
    else:
        need(scope['input_tokens']==131 and scope['output_tokens']==1024 and scope['concurrency']==1,
             'fixed original131/1024/C1 screening domain')
    need(all(environ.get(k) in(None,'','0') for k in (
        'BOLE_NATIVE_BOUNDARY_PROBE_ENABLE','BOLE_NATIVE_PROJECTION_PROBE_ENABLE',
        'BOLE_G3_STREAM_ENABLE')) and
         (qualifier or environ.get('BOLE_SHORT_STATE_DIGEST_ENABLE') in(None,'','0')),
         'no unrelated raw/boundary/stream modes')'''
    return R.once(text,a,b)

def render(*,base_root=None,permit_materialized=False,parent_pair_preparation_root=None,
           historical_short_source_ref=None,authority_ref=None,parent_preparation_readset=None):
    parent_root=PERF if parent_pair_preparation_root is None else Path(parent_pair_preparation_root)
    refs=R.readset(parent_root) if parent_preparation_readset is None else parent_preparation_readset
    with R.modules(refs,parent_root)as loaded:
        return _render(base_root=base_root,permit_materialized=permit_materialized,
            parent_pair_preparation_root=parent_root,historical_short_source_ref=historical_short_source_ref,
            authority_ref=authority_ref,parent_modules=loaded,parent_refs=refs)


def _render(*,base_root=None,permit_materialized=False,parent_pair_preparation_root=None,
            historical_short_source_ref=None,authority_ref=None,parent_modules=None,parent_refs=None):
    P=parent_modules['paired_prepare.py'];D=parent_modules['performance_followup_delta.py']
    # Existing complete FAST source renderer/inverse remains the parent.
    # No current V6 live file is ever changed.
    base=HERE if base_root is None else Path(base_root)
    parent_root=PERF if parent_pair_preparation_root is None else Path(parent_pair_preparation_root)
    need(type(permit_materialized)is bool,'explicit read-only materialized validation mode')
    parent=P.render_pair(base_root=parent_root,permit_materialized=permit_materialized)['arms']['bole']
    files=dict(parent['files']);m=copy.deepcopy(parent['manifest'])
    short,shortref=exact_short_sources(historical_short_source_ref)
    donor=json.loads(P.checked(shortref))
    for name in ('prepare_short_gate.py','test_short_state_digest.py','test_digest_reader.py',
                 'test_short_dependency_contract.py','fixtures/service_runner.py','fixtures/live_owner.py',
                 'fixtures/bole_performance_profile.py','fixtures/performance_service_client.py'):
        files[name]=P.checked(donor['files'][name])
    files['test_short_dependency_contract.py']=D.once(files['test_short_dependency_contract.py'].decode(),
        'import performance_validate as V','import followup_source_validate as V').encode()
    ns={'__file__':str(SHORT/'prepare_short_gate.py'),'__name__':'qualification_original_short_overlay'}
    exec(compile(short['prepare_short_gate.py'],'original-short-overlay','exec'),ns)
    _,originals,_=P.read_parent()
    overlay=ns['overlays']({n:originals[n].decode()for n in
         ('service_runner.py','live_owner.py','bole_performance_profile.py','performance_service_client.py')})
    for n in ('live_owner.py','performance_service_client.py'):files[n]=overlay[n].encode()
    for n in ('short_state_digest.py','compare_state_digest.py','performance_client_consumer.py',
              'bole_performance_profile.py'):files[n]=short[n]
    s=files['service_runner.py'].decode()
    s=D.once(s,'import validated_performance_policy as FAST',
         'import validated_performance_policy as FAST\nimport short_state_digest as DSP\nimport snapshot_publication as SP\nimport qualification_state_probe as FSP')
    s=D.once(s,"    fast_performance = FAST.select(C,m,os.environ)",
         "    fast_performance = FAST.select(C,m,os.environ)\n"
         "    probe=FSP.Probe(torch,C,source_ref,m,os.environ,native_get_tp_group().rank_in_group,_verify_published,SP.publish)")
    for a,b in [
      ('max_tokens=G2.MAX_OUTPUT, min_tokens=0','max_tokens=performance.output_tokens, min_tokens=0'),
      ('max_steps=G2.MAX_OUTPUT-1, output_budget=G2.MAX_OUTPUT','max_steps=performance.output_tokens-1, output_budget=performance.output_tokens'),
      ('f.remaining_output = G2.MAX_OUTPUT-len(f.request_output_tokens_before)','f.remaining_output = performance.output_tokens-len(f.request_output_tokens_before)'),
      ("1 <= f.remaining_output < G2.MAX_OUTPUT, 'actual bounded remaining output includes prefill root'",
       "1 <= f.remaining_output < performance.output_tokens, 'actual bounded remaining output includes prefill root'")]:
        s=D.once(s,a,b)
    s=D.once(s,"        SB.install_methods(bridge, state.live, C, m)\n        neutral_policy(state.live.request)",
       "        SB.install_methods(bridge, state.live, C, m)\n        neutral_policy(state.live.request)\n        probe.begin(owner,state.prefill['input_ids'],state.calibration_acquire)")
    s=D.once(s,"            f.commit_metadata = FAST.commit_metadata(f.proposal,f.publication)",
       "            f.commit_metadata = FAST.commit_metadata(f.proposal,f.publication)\n        probe.capture(state.bridge,f,record)")
    s=D.once(s,"                    emit_retirement=lambda row: performance_metadata('RETIRE', row))",
       "                    emit_retirement=lambda row:(probe.retire(row),performance_metadata('RETIRE',row)))")
    files['service_runner.py']=s.encode()
    files.update({n:s.encode()for n,s in TAP.render({n:files[n].decode()for n in D.RUNTIME}).items()})
    files['validated_performance_policy.py']=short_policy(files['validated_performance_policy.py'].decode()).encode()
    s=files['host_service.py'].decode()
    s=D.once(s,"  if performance:argv[2:2]=['--env',PERF.FLAG+'=1']",
       "  if performance:argv[2:2]=['--env',PERF.FLAG+'=1','--env','BOLE_SHORT_STATE_DIGEST_ENABLE=1','--env','BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE=1','--env','BOLE_OBSERVATION_ONLY_OFF=1']")
    files['host_service.py']=s.encode()
    for n in HELPERS:files[n]=(HERE/n).read_bytes()
    validator=files['qualification_source_validate.py'].decode()
    oldnode=next(n for n in ast.parse(validator).body if isinstance(n,ast.FunctionDef)and n.name=='dependency_contract')
    donor_validator=P.checked(donor['files']['performance_validate.py']).decode()
    node=next(n for n in ast.parse(donor_validator).body if isinstance(n,ast.FunctionDef)and n.name=='dependency_contract')
    body=ast.get_source_segment(donor_validator,node)
    first,rest=body.split('\n',1)
    indent=rest[:len(rest)-len(rest.lstrip())]
    validator=D.once(validator,ast.get_source_segment(validator,oldnode),first+'\n'+indent+'import sourceio as C\n'+rest)
    files['qualification_source_validate.py']=validator.encode()
    root=base/'prepared-source-short8-qualifier';output=base/'reserved-output-short8-qualifier'
    need(permit_materialized or(not root.exists()and not output.exists()),
         'future-only independent qualification source/output; materialized mode is read-only validation')
    files['contract090.py']=P.output_contract(files['contract090.py'].decode(),str(output)).encode()
    files['performance_host.py']=D.once(files['performance_host.py'].decode(),
        "'input_tokens': 131, 'output_tokens': 1024, 'concurrency': 1,",
        "'input_tokens': 131, 'output_tokens': 8, 'concurrency': 1,").encode()
    files['command_contract.py']=D.once(files['command_contract.py'].decode(),
        "'BOLE_PAIRED_PERFORMANCE_ENABLE=1',",
        "'BOLE_PAIRED_PERFORMANCE_ENABLE=1','BOLE_SHORT_STATE_DIGEST_ENABLE=1','BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE=1',").encode()
    files['command_contract.py']=D.once(files['command_contract.py'].decode(),
        "        '/usr/bin/python3','-I','-B',str(root/'bind_model.py'),'--execute',\n        '--reviewed-template-ref',json.dumps(template),\n        '--component-refs-json',json.dumps(components)])",
        "        '/usr/bin/python3','-I','-B',str(root/'qualification_source_producer.py'),'--bind',\n        '--template-ref',json.dumps(template)],consume=[\n        '/usr/bin/python3','-I','-B',str(root/'qualification_smoke_join.py'),'--consume',\n        '--source',str(root/'SOURCE_BOUND.json'),'--host-result',output+'/RESULT.json',\n        '--output',output+'/FASTPATH_NUMERIC_SCOPE_RESULT.json'])").encode()
    files['followup_source_validate.py']=(
        '"""Short8 qualification-only gate alias. Formal1024 gate is unchanged elsewhere."""\n'
        'from qualification_source_validate import (validate,execution_window,active_cutoff,\n'
        '    require_fastpath_admission,enumerate_tests,dependency_contract,TEST_FILES,SCHEMA)\n').encode()
    # Only the exact current short20 + qualifier5 software lane is claimed.
    # Original46 sources remain in the archive/readset, not counted as fresh.
    for name in ('performance_software_stages.py','performance_exact_controls.py'):
        text=files[name].decode()
        need(text.count('46')==(4 if name=='performance_software_stages.py'else 2),
             'exact original software count operands before short adaptation')
        files[name]=text.replace('46','25').encode()
    m.update(root=str(root),output_root=str(output),model_receipt_root=str(output/'dense/receipts'),
        fastpath_numeric_qualification=dict(QUAL),default_enabled=False,prepared_only=True,
        performance_ready=False,numerical_qualified=False,
        qualification_source_binding_pending=True,qualification_execution_authority_pending=True,
        short_state_digest_profile=dict(schema='bole.two-generation-short-state-digest/v1',enabled=True,
            input_tokens=131,output_tokens=8,generations=2,ordinals=list(range(7)),observation='OFF',
            formal_performance=False))
    m['performance_profile']['schema']='bole.prepared-c1-short-state-profile/v1'
    m['performance_profile']['scope']['output_tokens']=8
    for key in ('service_experiment','profile','performance_client_contract'):
        m[key]=copy.deepcopy(donor[key])
    m['qualification_preparation_root']=str(base)
    m['qualification_parent_pair_preparation_root']=str(parent_root)
    m['qualification_historical_short_source']=shortref
    m['qualification_authority_ref']=authority_ref
    m['qualification_parent_preparation_readset']=copy.deepcopy(parent_refs)
    m['qualification_source_schema']='bole.fastpath-short8-qualification-whole-source/v1'
    m['service_required_sameimage_software_cases']=25
    m['qualification_source_binding_pending']=True
    m['qualification_execution_authority_pending']=authority_ref is None
    m['files']={n:R.refbytes(root/n,b)for n,b in sorted(files.items())}
    old_refs={r['path']:(n,r)for n,r in parent['manifest']['files'].items()}
    def rebase(value):
        if type(value)is dict:
            if set(value)=={'path','bytes','sha256'}and value['path']in old_refs:
                n,old=old_refs[value['path']]
                need(value==old,'unambiguous complete copied source reference')
                return dict(m['files'][n])
            return {k:rebase(v)for k,v in value.items()}
        if type(value)is list:return [rebase(v)for v in value]
        return value
    for key in ('dependencies','service_runtime_source_snapshots','performance_timing_donor','performance_streaming_client'):
        m[key]=rebase(m[key])
    m['stream_channel_root']=str(output/'dense/receipts/STREAM')
    m['stream_channel_contract_path']=str(output/'dense/receipts/STREAM/CHANNEL.json')
    changed={n:dict(before=parent['manifest']['files'].get(n),after=m['files'][n])
             for n,b in files.items()if n not in parent['files']or b!=parent['files'][n]}
    for n,b in files.items():
        if n.endswith('.py'):compile(b,n,'exec')
    return dict(schema='bole.in-memory-short8-FAST-numeric-qualification-preparation/v1',
        manifest=m,files=files,parent_bundle=parent,short_source=shortref,
        inverse_delta=changed,prepared_only=True,NPU=False,launch_ready=False,
        pending=['new qualification-only MAIN authority/source binding/whole-source command validator',
            'same-image worker import and complete source load',
            'actual short8 full numeric+STATE/HTTP/retirement consumer execution',
            'same-input diagnostic-control paired NPU and TP/untouched-arena qualification',
            'long160/1024 bounded streaming and page/slot transitions',
            'actual observer-OFF same-compute integration before any formal performance'])

def inverse(bundle):
    actual=bundle['files'];parent=bundle['parent_bundle']['files']
    changed={n for n,b in actual.items()if n not in parent or b!=parent[n]}
    need(set(bundle['inverse_delta'])==changed,'complete exact short qualifier inverse ledger')
    restored=dict(actual)
    for n in changed:
        need(bundle['inverse_delta'][n]['after']==bundle['manifest']['files'][n]and
             bundle['inverse_delta'][n]['after']==R.refbytes(Path(bundle['manifest']['files'][n]['path']),actual[n]),
             'actual complete short source delta')
        if n in parent:restored[n]=parent[n]
        else:restored.pop(n)
    need(restored==parent,'full inverse restores every FAST source byte')
    return restored

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--review',action='store_true');a=p.parse_args()
    if not a.review:print(json.dumps(dict(enabled=False,NPU=False,launch_ready=False)))
    else:
        x=render();inverse(x)
        print(json.dumps(dict(source_files=len(x['files']),changed=list(x['inverse_delta']),
            pending=x['pending'],NPU=False,launch_ready=False)))
