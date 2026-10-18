"""Exact released Devices[] proof for the separate fixed-frame FIA component.

The original ticket116 join is retained. The original alias116r5 join is copied
explicitly with this successor's actual owner label and cpu_guest.py identity,
and extended to the two new CPU metadata files. No old report is rewritten.
Image-internal ABI module/header Refs are not turned into host mounts.
"""
import argparse
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C

SCHEMA = 'bole.fia-replay-NPU-ticket/v1'
OWNER_LABEL = 'bole-fia-fixed-frame-CPU-MAIN-RENEW24H-001'
CPU_SCHEMA = 'bole.fia-replay-owned-CPU/v1'
STAGE_SCHEMA = 'bole.fia-replay-CPU-stage/v1'
OUTPUTS = {'actual_abi_ref': 'ACTUAL_FIA_ABI.json',
           'input_binding_ref': 'INPUT_BINDING.json',
           'software_controls': 'SOFTWARE_CONTROLS.json'}


def resolve_outputs(source_ref, manifest, owner_ref, owner, stage):
    """Original per-item alias proof with exact new identities; no prefix map."""
    root = Path(owner_ref['path']).parent
    C.need(Path(owner_ref['path']).name == 'RESULT.json'
           and root == Path(manifest['output_root']) / 'cpu', 'actual source CPU owner path')
    C.need(owner['source'] == source_ref and type(owner['cid']) is str
           and re.fullmatch('[0-9a-f]{64}', owner['cid'])
           and owner['stage_result']['path'] == str(root / 'preflight/STAGE_RESULT.json'),
           'CPU owner/stage path and exact created CID join')
    inspect_ref = C.ref(root / 'FINAL_INSPECT.json')
    inspect = C.obj(inspect_ref)
    host, config, state = inspect['HostConfig'], inspect['Config'], inspect['State']
    C.need(inspect['Id'] == owner['cid'] and inspect['Image'] == manifest['image']
           and state['Running'] is False and state['Pid'] == 0 and state['ExitCode'] == 0
           and state['OOMKilled'] is False and not inspect.get('ExecIDs'),
           'actual same CID natural stopped CPU success')
    C.need(config['Labels'].get('qwen36.owner') == OWNER_LABEL, 'actual new CPU owner label')
    C.need(not host.get('Devices') and not host.get('DeviceRequests')
           and not host.get('DeviceCgroupRules') and host['ReadonlyRootfs'] is True
           and host['Privileged'] is False, 'actual Devices[] restricted CPU')
    mounts = inspect['Mounts']
    writable = [mount for mount in mounts if mount['RW']]
    C.need(len(writable) == 1 and writable[0]['Source'] == str(root)
           and writable[0]['Destination'] == '/adakv-results'
           and writable[0]['Type'] == 'bind', 'sole exact CPU output RW binding')
    protected = {'/adakv-results/preflight',
                 *('/adakv-results/preflight/' + name for name in OUTPUTS.values())}
    C.need(not any(mount['Destination'] in protected for mount in mounts),
           'no nested shadow mount for any exact CPU proof file')
    command = config['Cmd']
    C.need(type(command) is list and command.count('--source-ref') == 1,
           'one actual source-bound CPU argument')
    source_pos = command.index('--source-ref')
    C.need(json.loads(command[source_pos + 1]) == source_ref
           and command[-2:] == ['--output', '/adakv-results/preflight']
           and command.count(manifest['files']['cpu_guest.py']['path']) == 1,
           'actual source-bound new CPU child argv')
    mapped = {}
    for field, filename in OUTPUTS.items():
        original = stage[field]
        C.need(type(original) is dict and set(original) == {'path', 'bytes', 'sha256'},
               'original exact metadata Ref3')
        guest = '/adakv-results/preflight/' + filename
        target = str(root / 'preflight' / filename)
        C.need(original['path'] in (guest, target), 'only exact named CPU proof file/location')
        value = dict(original, path=target)
        C.checked(value)
        mapped[field] = value
    return mapped, inspect_ref


def abi_required(manifest):
    # abi116 imports the complete original probe115, which itself imports the
    # complete original tree_fa115. All six original support files are pinned.
    helper = C.load(manifest['files']['cpu_guest.py'], '_fia_ticket_CPU_support')
    return helper.support_modules(manifest).REQUIRED


def validate_controls(source_ref, manifest, controls):
    counts = manifest['software_control_counts']
    C.need(controls['schema'] == 'bole.fia-replay-software-controls/v1'
           and controls['source'] == source_ref and controls['expected_counts'] == counts
           and controls['primary'] is None and controls['pass_gate'] is True
           and controls['NPU'] is False and controls['qualified'] is False,
           'actual complete same-source CPU controls')
    C.need(type(controls['rows']) is list and len(controls['rows']) == len(counts) == 2,
           'both complete original control processes')
    helper = C.load(manifest['files']['cpu_guest.py'], '_fia_ticket_actual_control_parser')
    executed = 0
    for row, name in zip(controls['rows'], sorted(counts)):
        C.need(row['script'] == manifest['files'][name] and row['expected'] == counts[name]
               and type(row['executed']) is int and row['executed'] == counts[name]
               and type(row['exit_code']) is int and row['exit_code'] == 0
               and row['no_skip'] is True and type(row['stdout']) is str
               and type(row['stderr']) is str, 'exact successful noSkip control process')
        C.need(helper.control_count(row['stderr']) == row['executed'],
               'actual emitted unittest summary matches frozen case count')
        executed += row['executed']
    C.need(type(controls['executed']) is int and controls['executed'] == executed
           and type(controls['expected']) is int and controls['expected'] == sum(counts.values())
           and executed == sum(counts.values()), 'complete same-source software count')


def validate_inputs(source_ref, manifest, binding):
    plan = C.load(manifest['files']['plan.py'], '_fia_ticket_fixed_input_plan')
    C.need(binding['schema'] == 'bole.fia-fixed-frame-input-binding/v1'
           and binding['source'] == source_ref and binding['probe_plan_ref'] == manifest['probe_plan_ref']
           and binding['original_raw'] == plan.RAW and binding['original_source'] == plan.SOURCE
           and binding['original_rank_report'] == plan.RANK_REPORT
           and binding['previous_rounding'] == plan.PREVIOUS
           and binding['original_producers'] == plan.PRODUCERS
           and binding['fixed_cases'] == plan.CASES,
           'actual saved input binding joins every fixed original identity')
    C.need(binding['actual_saved_inputs_checked'] is True
           and binding['original_failure_sets_reproduced'] is True
           and binding['original_numeric_failures_unchanged'] is True
           and binding['qualified'] is False and binding['NPU'] is False,
           'CPU only original fixed frames; original failures remain unchanged')
    C.need(type(binding['branches']) is dict and set(binding['branches']) == {'tree', 'native'},
           'both complete original call bindings')
    for branch in ('tree', 'native'):
        item = binding['branches'][branch]
        C.need(set(item) == {'inputs', 'expected_output', 'original_CPU64_reference',
                            'original_parameters', 'original_metrics'}
               and item['original_parameters'] == plan.call_parameters(branch),
               'unchanged complete original FIA call parameters')
        expected_inputs = {'query', 'key', 'value'} | (
            {'atten_mask', 'block_table'} if branch == 'tree' else set())
        C.need(type(item['inputs']) is dict and set(item['inputs']) == expected_inputs,
               'complete original tensor input metadata')
        for tensor in [*item['inputs'].values(), item['expected_output']]:
            C.need(type(tensor) is dict and set(tensor) == {'shape', 'stride', 'dtype', 'bytes', 'sha256'}
                   and type(tensor['shape']) is list and type(tensor['stride']) is list
                   and len(tensor['shape']) == len(tensor['stride']) > 0
                   and all(type(v) is int and v > 0 for v in tensor['shape'])
                   and all(type(v) is int and v >= 0 for v in tensor['stride'])
                   and type(tensor['bytes']) is int and tensor['bytes'] > 0
                   and tensor['dtype'] in ('torch.bfloat16', 'torch.bool', 'torch.int32')
                   and type(tensor['sha256']) is str
                   and re.fullmatch('[0-9a-f]{64}', tensor['sha256']),
                   'complete typed original tensor byte binding')
        reference = item['original_CPU64_reference']
        reference_shape = [3, 6, 256] if branch == 'tree' else [1, 6, 256]
        reference_bytes = 36864 if branch == 'tree' else 12288
        C.need(type(reference) is dict
               and set(reference) == {'shape', 'stride', 'dtype', 'bytes', 'sha256'}
               and type(reference['shape']) is list
               and all(type(v) is int for v in reference['shape'])
               and reference['shape'] == reference_shape
               and type(reference['stride']) is list
               and all(type(v) is int for v in reference['stride'])
               and reference['stride'] == [1536, 256, 1]
               and reference['dtype'] == 'torch.float64'
               and type(reference['bytes']) is int and reference['bytes'] == reference_bytes
               and type(reference['sha256']) is str
               and re.fullmatch('[0-9a-f]{64}', reference['sha256']),
               'complete exact original CPU64 vector shape/stride/float64/bytes/SHA binding')
        rows = item['original_metrics']['nodes']
        wanted = [[], [], [573]] if branch == 'tree' else [[573]]
        C.need(type(rows) is list and [row['failed_flat_indices'] for row in rows] == wanted,
               'full original CPU failure sets retained in input binding')
    # Host keeps its original512MiB resource gate. The successful source-bound
    # CPU child performed torch.load; the NPU guest independently reloads and
    # verifies the complete fixed raw and inputs before any operator call.


def from_cpu(source_ref, cpu_owner_ref):
    manifest = C.source(source_ref)
    owner = C.obj(cpu_owner_ref)
    C.need(owner['schema'] == CPU_SCHEMA and owner['source'] == source_ref
           and owner['primary'] is None and owner['secondary'] == []
           and owner['resource_release_verified'] is True and owner['stopped_retained'] is True
           and owner['stage_ref'] is None and owner['numeric_owner'] is None
           and owner['Devices'] == [] and owner['NPU'] is False and owner['qualified'] is False,
           'actual released same-source Devices[] preflight CPU owner')
    stage = C.obj(owner['stage_result'])
    C.need(stage['schema'] == STAGE_SCHEMA and stage['source'] == source_ref
           and stage['authority'] == manifest['authority_ref'] and stage['NPU'] is False
           and stage['qualified'] is False and stage['primary'] is None
           and stage['actual_meta']['pass_gate'] is True
           and stage['actual_meta']['operator_executed'] is False
           and stage['actual_meta']['NPU'] is False,
           'actual complete same-source CPU ABI and fixed-input stage')
    mapped, inspect_ref = resolve_outputs(source_ref, manifest, cpu_owner_ref, owner, stage)
    abi_ref = mapped['actual_abi_ref']
    abi = C.obj(abi_ref)
    C.need(abi['schema'] == 'bole.actual-FIA-installed-ABI/v115' and abi['source'] == source_ref
           and abi['NPU'] is False and abi['Devices'] == [] and abi['no_device_fds'] is True
           and abi['operator_executed'] is False, 'actual installed ABI no-operator receipt')
    required = abi_required(manifest)
    C.need(abi['operator'] == 'npu::npu_fused_infer_attention_score'
           and set(required) <= set(abi['argument_names']) and abi['header_ref'] == manifest['header_ref']
           and isinstance(abi['overload'], str)
           and abi['schema_family'][abi['overload']] == abi['actual_schema'],
           'exact actual installed ABI/header and complete schema family')
    input_ref = mapped['input_binding_ref']
    controls_ref = mapped['software_controls']
    validate_inputs(source_ref, manifest, C.obj(input_ref))
    validate_controls(source_ref, manifest, C.obj(controls_ref))
    preflight = stage['input_preflight']
    C.need(preflight['input_binding_ref'] == stage['input_binding_ref']
           and preflight['actual_saved_inputs_checked'] is True
           and preflight['original_failure_sets_reproduced'] is True
           and preflight['qualified'] is False and preflight['NPU'] is False,
           'actual CPU saved-input return and published file join')
    runtime = C.dedup([cpu_owner_ref, owner['stage_result'], abi_ref,
                       input_ref, controls_ref, inspect_ref])
    for reference in runtime:
        C.checked(reference)
    return dict(schema=SCHEMA, source=source_ref, cpu_owner=cpu_owner_ref,
        cpu_stage=owner['stage_result'], actual_abi_ref=abi_ref,
        input_binding_ref=input_ref, software_controls_ref=controls_ref,
        cpu_final_inspect_ref=inspect_ref, runtime_readset=runtime,
        alias_predecessor_ref=manifest['support_files']['ticket_alias116r5.py'],
        image=manifest['image'], NPU=False, admitted_for_microprobe_only=True,
        actual_saved_inputs_checked=True, original_numeric_failures_unchanged=True,
        model_ready=False, performance_ready=False, qualified=False)


def consume(ticket_ref, source_ref, cpu_owner_ref):
    value = C.obj(ticket_ref)
    C.need(value == from_cpu(source_ref, cpu_owner_ref),
           'ticket exact releasedCPU/input proof recomputed; no future boolean')
    return value


def output_path(manifest, output):
    C.need(output == Path(manifest['output_root']) / 'ABI_TICKET.json',
           'exact ticket within the same metered profile output')
    return output


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--source-ref')
    parser.add_argument('--cpu-owner-ref')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false}')
        return 0
    source_ref = json.loads(args.source_ref)
    manifest = C.source(source_ref)
    C.window(manifest)
    output = output_path(manifest, args.output)
    value = from_cpu(source_ref, json.loads(args.cpu_owner_ref))
    # C.write requires an existing ordinary parent and an exclusive fresh file.
    C.write(output, value)
    print(json.dumps(C.ref(output), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
