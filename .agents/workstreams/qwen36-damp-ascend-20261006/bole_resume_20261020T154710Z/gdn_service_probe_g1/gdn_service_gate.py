"""Stdlib-only gate for a FUTURE opt-in service experiment, never admission."""
import importlib.util
from pathlib import Path
import sys


FILES = ('gdn_service_gate.py', 'gdn_service_seam.py', 'consume_gdn_service.py',
         'gdn_probe_contract.py','gdn_probe_runtime.py')
SERVICE_FILES = ('model_entry.py', 'core112.py', 'oracle112.py', 'independent_model.py',
                 'sourceio.py', 'native_seams.py', 'service_runner.py', 'service_bridge.py',
                 'live_owner.py', 'transaction.py', 'consume_service.py')


def load(C, reference, name):
    path = C.checked(reference)
    if name in sys.modules:
        module = sys.modules[name]
        C.need(C.ref(module.__file__) == reference, 'no ambient extension helper')
        return module
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        C.need(C.ref(module.__file__) == reference, 'extension helper stable across import')
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def content(a, b):
    return (a['bytes'], a['sha256']) == (b['bytes'], b['sha256'])


def replay_contract(C, x):
    source = C.obj(x['replay_manifest'])
    H = load(C, source['files']['replay_common.py'], '_bole_service_replay_common')
    replay, receipts, prior = H.manifest(x['replay_manifest'], H.__file__)
    consumer = load(C, replay['files']['consume_gdn.py'], '_bole_service_replay_reader')
    consumer.release(H, replay, x['replay_result'], x['replay_release'])
    result = C.obj(x['replay_result']); report = C.obj(x['replay_independent'])
    C.need(result['schema'] == 'bole.gdn3-actual-replay-result/v1' and
           result['manifest'] == x['replay_manifest'] and result['frames'] == 192 and
           result['frame_layouts'] == 384 and result['all_actual_results_exported'] is True and
           result['local_component_checks_pass'] is True and len(result['ranks']) == 4,
           'actual complete component replay producer chain')
    C.need(report['schema'] == 'bole.gdn3-independent-actual-replay/v1' and
           report['manifest'] == x['replay_manifest'] and report['replay_result'] == x['replay_result'] and
           report['owner_release'] == x['replay_release'] and report['frames'] == 192 and
           report['frame_layouts'] == 384 and report['component_replay_independent_pass'] is True and
           report['exact_original112_bounds'] is True and report['literal_sequential_FP64_oracle'] is True and
           report['actual_original_device_results_included'] is True and report['P_bitwise_original_checked'] is True and
           report['actual_inputs_bitwise_unchanged'] is True and report['lossless_actual_byte_exports'] is True and
           report['NPU'] is False and report['model_ready'] is False and report['formal_success'] is False and
           [r['rank'] for r in report['ranks']] == [0, 1, 2, 3], 'actual successful independent component replay')
    for rank, row in enumerate(report['ranks']):
        C.need(row['index'] == result['ranks'][rank] and row['original_raw'] == receipts[rank]['raw'] and
               row['passed'] is True and [r['layer'] for r in row['rows']] == list(H.LAYERS),
               'all192 independent actual frame joins')
        index = C.obj(row['index']); C.checked(index['blob'])
        for frame in row['rows']:
            C.need([r['layout'] for r in frame['layouts']] == list(H.LAYOUTS) and
                   all(r['passed'] is True and r['metrics']['passed'] is True and
                       r['actual_inputs_bitwise_unchanged'] is True and
                       r['actual_original_and_candidate_bytes_verified'] is True for r in frame['layouts']),
                   'every actual independent original112 frame/layout gate passed')
    return H, replay


def qualify(C, m, extension_ref, service_source_ref, software_gate_ref):
    x = C.obj(extension_ref)
    C.need(x['schema'] == 'bole.gdn3-service-extension/v1' and
           set(x['files']) == set(FILES) and set(x['service_files']) == set(SERVICE_FILES),
           'complete exact optional service extension closure')
    for name, r in x['files'].items():
        C.checked(r); C.need(m['files'][name] == r, 'extension source joins new service ticket')
    C.need(C.ref(__file__) == x['files']['gdn_service_gate.py'], 'exact loaded extension gate')
    for name, r in x['service_files'].items():
        C.checked(r); C.need(m['files'][name] == r, 'exact current service seam source ' + name)
    declared = m['gdn_service_extension']
    C.need(declared['source'] == extension_ref and declared['mode'] in ('matched_original', 'candidate') and
           declared['purpose'] == 'service_numerical_only' and
           declared['formal_performance'] is False and declared['model_ready'] is False,
           'source-declared nonformal matched control or candidate mode')
    C.need(C.obj(service_source_ref) == m and
           m['schema'] == 'bole.actual-model-three-node-entry/source-prep-v1' and
           m['prepared_only'] is False and m['default_enabled'] is False and
           m['whole_numerical_qualification'] is False and
           m['service_experiment'] == dict(schema='bole.c1-two-request-service/v1',
               prefix=131,request_count=2,max_steps_per_request=1,max_output_tokens=2),
           'exact new G1 numerical probe source ticket')
    P=load(C,m['files']['gdn_probe_contract.py'],'_gdn_service_probe_contract')
    parent,_,_,_=P.prior(C,x['prior_G1'])
    C.need(content(m['files']['model_entry.py'],parent['files']['model_entry.py']),
           'unchanged independently passed G1 Bridge implementation; no r23 file-identity shortcut')
    software = P.software(C,software_gate_ref,service_source_ref,m)
    C.need(software['schema'] == 'bole.g1-cold-aggregate-software/v1' and
           software['source'] == service_source_ref and software['all_tests_passed'] is True and
           software['tests'] == m['service_required_sameimage_software_cases'] and
           software['complete_readset_audited'] is True and software['NPU'] is False and
           software['actual_scheduler_executed'] is False and len(software['actual_cold_cli']) == 10 and
           all(r['exit_code'] == 0 for r in software['actual_cold_cli']),
           'actual same-image complete software aggregate for this exact new service source')
    H, replay = replay_contract(C, x)
    for name in ('core112.py', 'oracle112.py', 'independent_model.py', 'sourceio.py'):
        C.need(content(m['files'][name], replay['references'][name]), 'unchanged qualified mathematical bytes ' + name)
    timing_receipt = None
    return x, H, replay, dict(schema='bole.gdn3-service-component-prerequisites/v1',
        extension=extension_ref, service_source=service_source_ref, actual_software=software_gate_ref,
        purpose=declared['purpose'], replay_manifest=x['replay_manifest'],
        independent_replay=x['replay_independent'], timing=timing_receipt,
        timing_required_for_numerical_only=False,
        component_prerequisites_checked=True, new_service_prefixes_qualified=False,
        model_ready=False, formal_success=False)
