"""Exact actual namespace-compile proof and immutable failed-v1 source closure."""
import json

REPORT='NATIVE_AR_FIA_V2_NAMESPACE_PROBE.json'
EXECUTION='NATIVE_AR_FIA_V2_NAMESPACE_PROBE_EXECUTION.json'

def verify(C,y):
    C.need(y.get('namespace_profile_repair_v2')is True and C.ref(__file__)==y['files']['namespace_repair_gate.py'],
        'exact source-bound namespace-only repair gate')
    vr=C.obj(y['files']['ACTUAL_FIA_V1_REFS.json']);pr=C.obj(y['files']['ACTUAL_NAMESPACE_PROBE_REFS.json'])
    C.need(len(vr)==11 and set(pr)=={REPORT,EXECUTION},'complete exact failed-v1 and actual source-only probe primary maps')
    for r in (*vr.values(),*pr.values()):C.checked(r)
    C.need((vr['RESULT.json']['bytes'],vr['RESULT.json']['sha256'])==(344663,'a2a728f558c812d18059886be334353445b14c9699a56888bba602315a8312a6')and
        (vr['INPUTS.json']['bytes'],vr['INPUTS.json']['sha256'])==(9615,'4ec84d8afc471fdd5bc5fdc26d61f7a1cfbd1a9da46ae654d8e758871c6c600f')and
        (pr[REPORT]['bytes'],pr[REPORT]['sha256'])==(7020,'2f93b69fb6605444d1b708bc51ff288610a9952c3b2ae573c98c156c90afbef2')and
        (pr[EXECUTION]['bytes'],pr[EXECUTION]['sha256'])==(1750,'3eeb1fdafa49d8ffe7702f827c260f5d00126ff376d35a2812a7aa810246a5fb'),
        'actual immutable v1 failure and MAIN successful namespace proof identities')
    old=C.obj(vr['INPUTS.json']);failed=C.obj(vr['RESULT.json']);proof=C.obj(pr[REPORT]);execution=C.obj(pr[EXECUTION])
    C.need(failed['schema']=='bole.native-AR-FIA-finite-diagnostic-owner/v1'and failed['inputs']==vr['INPUTS.json']and
        failed['primary']['error']=="ValueError('actual exact installed readonly function before singleton change device_map')"and
        failed['secondary']==[]and failed['summary']=={}and failed['cleanup_spent']==0 and
        failed['source_before']==failed['source_after']and len(failed['source_before'])==1010 and
        old['AR_source']==y['AR_source']and old['authority']==y['authority'],
        'retained source-equal precreate v1 failure, no native mathematical pass')
    C.need(proof['schema']=='bole.native-AR-FIA-actual-source-only-namespace-compile-probe/v2'and
        proof['v1_inputs']==vr['INPUTS.json']and proof['primary']is None and proof['source_only_probe_pass']is True and
        proof['v1_actual_guard_failure']==failed['primary']['error']and
        all(proof[k]is True for k in('v2_actual_profile_entered','unique_exception_exercised',
            'singleton_finally_restored_original_objects','namespace_finally_restored_original_objects','unused_output_root_absent'))and
        all(proof[k]is False for k in('controller_constructed','container_created','resources_admitted','NPU',
            'whole_host_readset_recomputed','mathematical_qualification','formal_success')),
        'actual no-resource original namespace/whole-code and exception-finally object inverses, no qualification substitution')
    C.need(set(proof['functions'])=={'device_map','create_argv','validate_inspect'}and
        all(v['v2']['actual_globals_is_S']is True and v['v2']['whole_marshal_equal']is True and
            v['v2']['actual_flags']==v['v2']['expected_flags']and v['v2']['actual_filename']==v['v2']['expected_filename']and
            v['v2']['actual_marshal_sha256']==v['v2']['expected_marshal_sha256']and v['v2']['code_fields_different']==[]
            for v in proof['functions'].values()),'all3 actual full-code identities, no AST/qualname-only replacement')
    C.need(proof['functions']['device_map']['v1']['whole_marshal_equal']is False and
        proof['functions']['device_map']['v1']['actual_flags']!=proof['functions']['device_map']['v1']['expected_flags'],
        'actual original future-flag counterexample reproduced')
    for field,name,expected in (
        ('new_profile','singleton_profile.py',(6682,'b4843a436f79337bd5fb55817b2445c7a15202e1fa19887683be0ee8418c3101')),
        ('probe_source','namespace_compile_probe.py',(7297,'c9b54024922abe7f5e5064031b277868184938ed930fe5dada7bb9262fcf9e96'))):
        r=proof[field];C.checked(r);now=y['files'][name];C.checked(now)
        C.need((r['bytes'],r['sha256'])==(now['bytes'],now['sha256'])==expected,
            'actual proof keeps its original full path and exact prepared-copy content '+name)
    prefix=['/usr/bin/flock','--nonblock','--no-fork',y['MAIN_lock'],'/usr/bin/env',
        'DENSE090_EXTERNAL_OUTPUT_ENABLE=1','BOLE_NATIVE_FIA_NAMESPACE_PROBE_ENABLE=1','/usr/bin/python3','-I','-B']
    C.need(execution['exit_code']==0 and execution['stderr']==''and execution['argv']==prefix+proof['actual_host_argv']and
        proof['MAIN_lock']['inherited_MAIN_lock_verified']is True and proof['MAIN_lock']['path']==y['MAIN_lock'],
        'actual MAIN-inherited source-only probe invocation exited0')
    output=json.loads(execution['stdout'])
    C.need(output==dict(output=pr[REPORT],source_only_probe_pass=True,NPU=False),'exact sole probe output provenance')
    return dict(objects=[vr,pr,old,failed,proof,execution],source_before=failed['source_before'],
        actual_namespace_probe=pr[REPORT],actual_v1_failure=vr['RESULT.json'],
        original_native_numerical_pass=False,resources_admitted=False,NPU=False)
