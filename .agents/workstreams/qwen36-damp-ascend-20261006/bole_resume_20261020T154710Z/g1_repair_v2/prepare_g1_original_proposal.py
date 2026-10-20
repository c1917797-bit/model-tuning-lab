"""Freeze a NEW G1 packet from the exact passed V6 packet; default OFF.

Only the requested new source leaf is written. No model, container, scheduler,
Git operation or device work is performed. Root reviews and invokes this on
the host after integrating the independent reader proposal.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path)
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def obj(reference):
    need(ref(reference['path']) == reference, 'exact input Ref3')
    return json.loads(Path(reference['path']).read_bytes())


def write(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')


def tests(path):
    if not path.exists():
        return 0
    return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and
               n.name.startswith('test_') for n in ast.walk(ast.parse(path.read_bytes())))


def validate_parent_qualification(parent_ref, parent, owner_ref, qualification_ref):
    owner, qualification = obj(owner_ref), obj(qualification_ref)
    need(owner['schema']=='bole.actual-three-node-model-owned/v131' and
         owner['source']==parent_ref and owner['primary'] is None and owner['secondary']==[] and
         owner['cpu_only'] is False and owner['source_before'] and
         owner['source_before']==owner['source_after'] and
         owner['summary']['independent']==qualification_ref,
         'actual successful same-source V6 owner lifecycle with exact independent report link')
    for reference in parent['files'].values():
        need(owner['source_before'].get(reference['path'])==reference['sha256'],
             'V6 owner before/after ledger covers every exact parent source file')
    need(qualification['schema']=='bole.actual-c1-continuous-service-independent/v1' and
         qualification['source']==parent_ref and
         all(qualification[k] is True for k in ('service_complete','service_experiment_pass',
             'component_checks_pass','scheduler_committed_independently','actual_all4_retirement',
             'actual_HTTP_output_token_ID_join','actual_scheduler_flow_observed')),
         'actual independently qualified V6 bounded lifecycle/component/HTTP/all4 retirement evidence')
    need(all(qualification[k] is False for k in ('model_ready','task_ready','performance_ready',
             'formal_success','whole_numerical_qualified','native_AR_greedy_comparison_performed')) and
         all(owner[k] is False for k in ('model_ready','candidate_qualification',
             'performance_gain_measured','formal_performance','task_accuracy')),
         'V6 bounded pass makes no model/task/nativeAR/formal/performance claim')


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--parent-source-ref')
    parser.add_argument('--parent-owner-result-ref')
    parser.add_argument('--parent-qualification-ref')
    parser.add_argument('--inverse-original-template-ref')
    parser.add_argument('--proposal', type=Path)
    parser.add_argument('--new-root', type=Path)
    parser.add_argument('--output-root', type=Path)
    a = parser.parse_args()
    if not a.execute:
        print('{"enabled":false,"NPU":false}')
        return 0
    need(all((a.parent_source_ref, a.parent_owner_result_ref, a.parent_qualification_ref,
              a.inverse_original_template_ref, a.proposal,
              a.new_root, a.output_root)), 'all exact freeze operands required')
    parent_ref = json.loads(a.parent_source_ref)
    parent = obj(parent_ref)
    owner_ref, qualification_ref = json.loads(a.parent_owner_result_ref), json.loads(a.parent_qualification_ref)
    validate_parent_qualification(parent_ref, parent, owner_ref, qualification_ref)
    old = Path(parent['root'])
    new, output, proposal = a.new_root, a.output_root, a.proposal.resolve()
    need(old / 'SOURCE_BOUND.json' == Path(parent_ref['path']) and
         parent['prepared_only'] is False and
         parent['service_experiment'] == dict(schema='bole.c1-service-prefix-experiment/v1',
             prefix=131, max_steps=3, max_output_tokens=4), 'exact immutable passed V6 parent scope')
    need(new.is_absolute() and output.is_absolute() and
         new.parent == output.parent == Path('/opt/host/vnf/austinov') and
         new.name.startswith('bole-g1-two-request-') and
         output.name == 'run-' + new.name and not new.exists() and
         not output.exists() and not Path(str(output)+'-CPU').exists(),
         'fresh explicit G1 source/model/CPU leaves')
    for reference in parent['files'].values():
        need(ref(reference['path']) == reference, 'exact V6 file before copy')
    original_ref = json.loads(a.inverse_original_template_ref)
    original = obj(original_ref)
    original_root = Path(original['root'])
    reader = proposal / 'consumer_proposal' / 'consume_service.py'
    need(reader.is_file(), 'complete independently owned G1 consumer proposal required')
    overlays = {p.name: p for p in proposal.glob('*.py')
                if p.name != 'consume_service.py'}
    overlays['consume_service.py'] = reader
    for path in sorted(reader.parent.glob('test*.py')):
        need(path.name not in overlays, 'distinct consumer test file name')
        overlays[path.name] = path
    required = {'service_runner.py', 'consume_service.py', 'service_client.py',
        'worker_bootstrap.py', 'worker_entry.py', 'cache_registry.py', 'layer_slots131r10.py',
        'model_entry.py', 'model_process_calibration.py', 'g1_contract.py', 'service_bridge.py',
        'service_entry.py', 'host_service.py', 'contract090.py', 'server090.py',
        'cache_observation.py', 'fa_prefill131r10.py', 'registration_audit131r11.py',
        'test_g1_lifecycle.py', 'test_service_client.py'}
    need(required <= overlays.keys(), 'complete G1 proposal before any source write')
    # Original numerical implementations and their literal tolerances stay exact.
    mathematical = ('core112.py', 'oracle112.py', 'adapter.py', 'treeconv118.py',
                    'native_seams.py', 'independent_model.py', 'model_calibration131r12.py')
    for name in mathematical:
        if name in overlays:
            need(overlays[name].read_bytes() == (old/name).read_bytes(),
                 'byteexact original numerical/reference module '+name)
    old_model = ast.parse((old/'model_entry.py').read_bytes())
    new_model = ast.parse(overlays['model_entry.py'].read_bytes())
    def methods(tree):
        bridge = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Bridge')
        return {n.name: ast.dump(n, include_attributes=False) for n in bridge.body
                if isinstance(n, ast.FunctionDef)}
    before_math, after_math = methods(old_model), methods(new_model)
    for name in ('_gdn', '_fa', '_anchors', '_unchanged', '_native_gdn_ar',
                 '_native_fa_ar', 'sequential_native_paths', 'stage_selected_path', 'greedy_proposal'):
        need(before_math[name] == after_math[name], 'unchanged actual model mathematical method '+name)
    for path in overlays.values():
        compile(path.read_bytes(), str(path), 'exec')
    shutil.copytree(old, new, ignore=shutil.ignore_patterns('__pycache__'))
    (new/'SOURCE_BOUND.json').rename(new/'PARENT_V6_SOURCE_BOUND.json')
    for name, path in overlays.items():
        shutil.copyfile(path, new/name)
    # Contract source is already G1-specific, but its output operands are bound here.
    contract = new/'contract090.py'
    text = contract.read_text()
    need(text.count(parent['output_root']) == 2, 'exact V6 output operands before new binding')
    contract.write_text(text.replace(parent['output_root'], str(output)))
    m = json.loads(json.dumps(parent))
    m.update(root=str(new), output_root=str(output), model_receipt_root=str(output/'dense/receipts'),
             prepared_only=True, default_enabled=False)
    m.pop('prepared_template', None)
    scope = dict(schema='bole.c1-two-request-service/v1', prefix=131, request_count=2,
                 max_steps_per_request=1, max_output_tokens=2)
    m['profile']['HTTP_output_tokens'] = 2
    m['profile']['HTTP_tree_request_count'] = 2
    m['service_experiment'] = scope
    m['service_activation'] = dict(callback='service_runner.install',
        enable_environment='BOLE_G1_MULTI_REQUEST_ENABLE', first_request_only=False,
        request_count=2, monotonic_generations=[1, 2], subsequent_retirement_barrier_native=True,
        calibration='one original MC.run; strong process-local reuse revalidated on request2',
        slot_reuse_must_be_observed=False, reuse_observation_required=True, formal_performance=False,
        formal_task_accuracy=False, model_ready=False, actual_scheduler_executed=False)
    # Extend the original inverse ledger to all changed legacy files. The old
    # source and each complete before/after text remain independently reopenable.
    ledger = {}
    for name, reference in original['files'].items():
        if Path(reference['path']).is_relative_to(original_root) and (new/name).is_file():
            need(ref(reference['path']) == reference, 'exact original inverse source '+name)
            before, after = Path(reference['path']).read_text(), (new/name).read_text()
            if before != after:
                ledger[name] = dict(before=reference, after=ref(new/name),
                    edits=[dict(before=before, after=after)])
    ledger_path = new/'FA_BOUNDARY_EDITS_R14.json'
    ledger_path.unlink()
    write(ledger_path, ledger)
    for name, reference in list(m['files'].items()):
        if Path(reference['path']).is_relative_to(old):
            m['files'][name] = ref(new/Path(reference['path']).relative_to(old))
    for name in overlays:
        m['files'][name] = ref(new/name)
    for key, reference in list(m.get('service_runtime_source_snapshots', {}).items()):
        if Path(reference['path']).is_relative_to(old):
            m['service_runtime_source_snapshots'][key] = ref(new/Path(reference['path']).relative_to(old))
    m['dependencies'] = [ref(new/Path(r['path']).relative_to(old))
                         if Path(r['path']).is_relative_to(old) else r for r in m['dependencies']]
    m['dependencies'].append(parent_ref)
    m['dependencies'].extend([owner_ref, qualification_ref])
    m['dependencies'].append(ref(__file__))
    m['g1_predecessor'] = dict(source=parent_ref, owner_result=owner_ref,
        independent_qualification=qualification_ref, inverse_original=original_ref,
        numerical_reference_modules_byteexact=True, model_mathematical_methods_AST_exact=True,
        actual_V6_pass_is_prerequisite=True, no_G1_actual_execution_claimed=True)
    delta = sum(tests(new/name)-tests(old/name) for name in overlays if name.startswith('test'))
    m['service_required_sameimage_software_cases'] = parent['service_required_sameimage_software_cases']+delta
    m['g1_overlay'] = {name: ref(new/name) for name in sorted(overlays)}
    for path in new.rglob('*.py'):
        compile(path.read_bytes(), str(path), 'exec')
    for name in ('SOURCE_TEMPLATE.json', 'SOURCE.json'):
        path = new/name
        path.unlink()
        write(path, m)
    source_template = ref(new/'SOURCE_TEMPLATE.json')
    result = subprocess.run([sys.executable, '-I', '-B', str(new/'bind_model.py'), '--execute',
        '--reviewed-template-ref', json.dumps(source_template),
        '--component-refs-json', json.dumps(parent['component_refs'])],
        cwd=new, capture_output=True, text=True, timeout=25)
    need(result.returncode == 0, 'actual source binding '+result.stdout+result.stderr)
    bound = ref(new/'SOURCE_BOUND.json')
    commands = dict(schema='bole.g1-frozen-commands/v1', source=bound, template=source_template,
        source_audit=[sys.executable, '-I', '-B', str(new/'host_service.py'), '--source-audit',
            '--source-ref', json.dumps(bound)],
        model=[sys.executable, '-I', '-B', str(new/'host_service.py'), '--execute',
            '--source-ref', json.dumps(bound), '--output', str(output)],
        CPU=[sys.executable, '-I', '-B', str(new/'host_service.py'), '--execute', '--cpu-only',
            '--source-ref', json.dumps(bound), '--output', str(output)+'-CPU'],
        required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
        actual_scheduler_executed=False, model_ready=False)
    command_path = new/'COMMANDS_G1.json'
    write(command_path, commands)
    print(json.dumps(dict(source=bound, commands=ref(command_path), prepared=True,
        NPU=False, actual_scheduler_executed=False, model_ready=False)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
