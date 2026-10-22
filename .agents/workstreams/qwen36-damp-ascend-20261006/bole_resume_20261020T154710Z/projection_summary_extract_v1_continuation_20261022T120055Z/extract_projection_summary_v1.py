"""Project one saved, exact continuation diagnostic; never run its reader/model.

Only a new --output file is written. This is a bounded presentation extractor,
not a second evidence-closure validator or a numerical/causal admission gate.
Missing fields are represented by value=null plus present=false, never false.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import stat
import time


WS = '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
BATCH = 'continuation_20261022T120055Z'
EXPECTED_DIAGNOSTIC_PATH = '/opt/host/vnf/austinov/run-bole-projection-reader-v2-' + BATCH + '/PROJECTION_DIAGNOSTIC.json'
EXPECTED_SOURCE = dict(path=WS + '/bound-boundary-ON-v3-' + BATCH + '/SOURCE_BOUND.json', bytes=1638841,
    sha256='d28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df')
EXPECTED_AUDIT = dict(path='/opt/host/vnf/austinov/run-bole-boundary-source-audit-v4-' + BATCH + '/SOURCE_AUDIT.json',
    bytes=1424700, sha256='08c783e7989397f25a6db83fa9d1f1d86807e9154a8691058f6ee5d510a62cc6')
EXPECTED_READER = dict(path=WS + '/projection_result_reader_v2_' + BATCH + '/read_projection_result_v2.py',
    bytes=99832, sha256='19bfdd2005ea0881fcd61415bc51d10af1d7e1d244425642224df75255a8a38e')
EXPECTED_HOST_RESULT_PATH = '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-' + BATCH + '/RESULT.json'
HISTORICAL_PAIR_EXECUTION = dict(path='/opt/host/vnf/austinov/run-bole-short-pair-reader-v4-20261022T070247Z/EXECUTION.json',
    bytes=3721, sha256='41202d391c8165138555b22e6b07c12d98e88cee456be8a757e35027bac163d1')
INPUT_SCHEMA = 'bole.completed-projection-within-arm-diagnostic/v1'
OUTPUT_SCHEMA = 'bole.saved-projection-diagnostic-summary/v1'
INPUT_CAP, SOURCE_CAP, OUTPUT_CAP = 32 * 2**20, 128 * 1024, 256 * 1024
STAGES = ('projection_input', 'quant_return', 'pre_reduce', 'post_reduce', 'projection_return')
STAGE_FIELDS = ('observed', 'reason', 'sha256', 'bytes', 'dtype', 'shape', 'geometry',
    'finite', 'full_actual_tensor', 'read_ordinal', 'source_role', 'line', 'numerical_qualified')
TRUE_FLAGS = ('diagnostic_only', 'source_validation_reopened', 'original_host_and_single_arm_gates_revalidated',
    'boundary_record_integrity_validated', 'projection_internal_integrity_validated',
    'original_inputs_unchanged', 'complete_whole_sha_readset_unchanged', 'file_identity_unchanged')
FALSE_FLAGS = ('source_only', 'model_ready', 'paired_gate_pass', 'numerical_admitted',
    'independent_algorithm_numerical_qualification', 'performance_admitted', 'formal_performance',
    'task_accuracy', 'NPU_executed_by_reader', 'cause_determined', 'original_pair_gate_replaced',
    'original_pair_gate_rerun')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False) + '\n').encode()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant ' + value)
    def finite_float(value):
        parsed = float(value)
        need(math.isfinite(parsed), 'nonfinite JSON number')
        return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)


def ref_path(reference, cap):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    need(type(reference['path']) is str and '\x00' not in reference['path'] and
         type(reference['bytes']) is int and 0 < reference['bytes'] <= cap and sha(reference['sha256']),
         'typed bounded Ref3')
    path = Path(reference['path'])
    need(path.is_absolute() and str(path) == reference['path'] and '..' not in path.parts, 'canonical absolute path')
    return path


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink, value.st_uid,
            value.st_gid, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def parents(path):
    result = []
    for parent in path.parents:
        value = parent.lstat()
        need(stat.S_ISDIR(value.st_mode), 'ordinary ancestors, no symlinks')
        result.append((str(parent), value.st_dev, value.st_ino, value.st_mode))
    return result


def whole(path, cap, deadline, expected=None, keep=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute whole-file input')
    ancestry, before = parents(path), path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= cap, 'bounded ordinary whole file')
    if expected is not None:
        need(before.st_size == expected['bytes'], 'expected size before read')
    digest, size, blocks = hashlib.sha256(), 0, []
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        need(identity(os.fstat(stream.fileno())) == identity(before), 'stable opened file')
        while True:
            need(time.monotonic() < deadline, 'bounded extraction wall time')
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            need(size <= cap, 'bounded full read')
            digest.update(block)
            if keep:
                blocks.append(block)
        need(identity(os.fstat(stream.fileno())) == identity(before), 'stable file through read')
    need(identity(path.lstat()) == identity(before) and parents(path) == ancestry and size == before.st_size,
         'stable exact complete input and ancestors')
    reference = dict(path=str(path), bytes=size, sha256=digest.hexdigest())
    if expected is not None:
        need(reference == expected, 'complete input bytes and SHA256 match Ref3')
    return reference, b''.join(blocks) if keep else None, (identity(before), ancestry)


def fields(value, names):
    """No absent value is synthesized as false; explicit null stays present."""
    need(type(value) is dict, 'field source object')
    return {name: dict(present=name in value, value=value[name] if name in value else None) for name in names}


def exact_rows(rows, key, values):
    need(type(rows) is list and [row[key] for row in rows] == list(values), 'complete ordered ' + key + ' rows')
    return rows


def stage(value):
    need(type(value) is dict and type(value.get('observed')) is bool, 'explicit stage availability')
    if value['observed']:
        need(sha(value['sha256']) and type(value['bytes']) is int and value['bytes'] > 0 and
             value['full_actual_tensor'] is True and value['numerical_qualified'] is False,
             'full logical stage witness, no numerical qualification')
    else:
        need(set(value) == {'observed', 'reason'} and value['reason'] in
             ('fused_no_python_local_result', 'no_reduce_callsite_executed'), 'explicit unavailable stage reason')
    return fields(value, STAGE_FIELDS)


def project(value):
    need(type(value) is dict and value['schema'] == INPUT_SCHEMA, 'exact final reader diagnostic schema')
    need(value['source'] == EXPECTED_SOURCE and value['source_audit'] == EXPECTED_AUDIT and
         value['comparison_source'] == EXPECTED_READER, 'exact frozen source/audit/final-reader identities')
    need(str(ref_path(value['actual_host_result'], INPUT_CAP)) == EXPECTED_HOST_RESULT_PATH, 'exact actual host result path')
    for name in TRUE_FLAGS:
        need(value[name] is True, 'required saved integrity flag ' + name)
    for name in FALSE_FLAGS:
        need(value[name] is False, 'unchanged false qualification/interpretation flag ' + name)
    need(value['actual_physical_devices'] == [4, 5, 6, 7] and value['complete_boundary_files_per_rank'] == 150 and
         value['complete_boundary_files_all_ranks'] == 600, 'exact TP4 saved boundary scope')
    need(type(value['inputs_before']) is list and value['inputs_before'] == value['inputs_after'] and
         type(value['readset_count']) is int and value['readset_count'] == len(value['inputs_before']),
         'saved complete reader before/after readset agreement')
    ranks = exact_rows(value['ranks'], 'rank', range(4))
    internal = exact_rows(value['projection_internal'], 'rank', range(4))
    projected = []
    for boundary, projection in zip(ranks, internal):
        need(boundary['initial_state_equivalence_assumed'] is False and boundary['cause_determined'] is False,
             'no assumed initial state or causal result')
        need(projection['caller_source_validated'] is True, 'saved source-bound caller validation')
        for name in ('collective_implementation_pinned', 'weight_content_equality_proven', 'same_initial_state_assumed',
                     'cause_determined', 'paired_gate_pass', 'numerical_admitted', 'performance_admitted'):
            need(projection[name] is False, 'saved projection interpretation boundary ' + name)
        stage_rows = []
        for row in exact_rows(projection['stages'], 'stage', STAGES):
            stage_rows.append(dict(stage=row['stage'], generation_1=stage(row['generation_1']),
                generation_2=stage(row['generation_2']), comparison=fields(row,
                    ('both_observed', 'availability_equal', 'full_logical_sha256_equal', 'same_logical_metadata',
                     'geometry_differences', 'producer_hash_witness', 'raw_values_preserved', 'numerical_qualification'))))
        generations = []
        for generation in exact_rows(projection['generations'], 'generation', (1, 2)):
            need(generation['weight_bytes_hashed'] is False and generation['backend_format_observed'] is False,
                 'weight bytes/backend format remain unobserved')
            need(type(generation['joins']) is list and len(generation['joins']) == 4, 'four existing within-generation joins')
            generations.append(dict(generation=generation['generation'], actual_dispatch=fields(generation,
                ('active', 'roles', 'calls', 'exceptions', 'reductions', 'trace_restored')),
                joins=[fields(join, ('before', 'after', 'both_observed', 'before_value', 'after_value',
                    'generation_values', 'logical_hash_equal', 'same_logical_metadata', 'byte_count_equal',
                    'geometry_differences', 'equality_required', 'magnitude_threshold_applied')) for join in generation['joins']],
                limitations=fields(generation, ('weight_bytes_hashed', 'backend_format_observed'))))
        native_inputs = exact_rows(boundary['native0_full131_input_hashes'], 'name', ('mixed_qkv', 'b', 'a'))
        selected_raw = [row for row in boundary['raw9_stages'] if row['name'] in
                        ('layer0_core_output', 'layer0_gated_norm', 'layer0_out_projection')]
        need([row['name'] for row in selected_raw] ==
             ['layer0_core_output', 'layer0_gated_norm', 'layer0_out_projection'], 'three existing native boundary rows')
        transitions = boundary['within_generation_observed_transitions']
        need(type(transitions) is list and len(transitions) == 12, 'twelve saved state endpoint transitions')
        transition_summaries = []
        for row in transitions:
            changes = row['changed_hashes']
            need(type(changes) is list, 'saved complete transition change list')
            item = fields(row, ('generation', 'before', 'after', 'all_observed_hashes_equal',
                                'interval_contains_unobserved_work'))
            item['changed_hashes_summary'] = dict(present=True, value=dict(count=len(changes),
                first_change=changes[0] if changes else None,
                complete_list_canonical_sha256=hashlib.sha256(canonical(changes)).hexdigest(),
                encoding='UTF-8 compact sorted-key ASCII JSON plus one newline',
                remaining_changes_not_expanded=True, complete_values_remain_in_diagnostic=True))
            transition_summaries.append(item)
        projected.append(dict(rank=boundary['rank'], complete_ref=boundary['complete_ref'],
            first_boundary_difference=fields(boundary, ('first_observed_difference', 'no_difference_observed_at_retained_boundaries')),
            first_projection_difference=fields(projection, ('first_observed_projection_hash_difference',
                'first_projection_stage_coverage_difference', 'active_metadata_differences', 'calls_equal', 'reductions_equal')),
            native0_full131_input_hashes=native_inputs,
            native_core_norm_outer=selected_raw, stages=stage_rows, generations=generations,
            state_endpoint_transitions=transition_summaries,
            no_causal_or_qualification_inference=True))
    cross_rank = value['projection_cross_rank']
    need(type(cross_rank) is list and [(row['generation'], row['stage']) for row in cross_rank] ==
         [(generation, name) for generation in (1, 2) for name in STAGES], 'ten complete same-generation cross-rank rows')
    cross = []
    for row in cross_rank:
        need(row['equality_required'] is False and row['numerical_qualification'] is False, 'TP shard equality is observational')
        cross.append(dict(generation=row['generation'], stage=row['stage'],
            ranks=[dict(rank=rank['rank'], observation=stage(rank['observation']))
                   for rank in exact_rows(row['ranks'], 'rank', range(4))],
            comparison=fields(row, ('all_four_observed', 'full_logical_hashes_equal', 'same_logical_metadata',
                                   'equality_required', 'numerical_qualification', 'comparison_scope'))))
    need(type(value['limitations']) is list and all(type(item) is str for item in value['limitations']),
         'all original interpretation limitations retained')
    need(type(value['projection_runtime_sources']) is list and len(value['projection_runtime_sources']) == 5,
         'five saved source-index mappings for actual dispatch roles')
    return dict(schema=OUTPUT_SCHEMA, status='SAVED_DIAGNOSTIC_SUMMARY_NOT_GATE',
        source=value['source'], actual_host_result=value['actual_host_result'], source_audit=value['source_audit'],
        comparison_source=value['comparison_source'], original_diagnostic_schema=value['schema'],
        projection_runtime_sources=value['projection_runtime_sources'],
        saved_reader_flags={name: value[name] for name in TRUE_FLAGS + FALSE_FLAGS},
        actual_physical_devices=value['actual_physical_devices'],
        saved_reader_scope=fields(value, ('complete_boundary_files_per_rank', 'complete_boundary_files_all_ranks',
            'readset_count', 'total_input_bytes', 'source_audit_readset_count')),
        HTTP=fields(value['HTTP'], ('reference', 'request_payload_equal', 'prompt_equal', 'both_explicit_seeds_present',
            'same_explicit_seed', 'output_tokens_generation_1', 'output_tokens_generation_2', 'output_token_differences',
            'distinct_request_ids', 'identical_initial_state_assumed')),
        ranks=projected, same_generation_cross_rank=cross, limitations=value['limitations'],
        historical_full_pair=dict(recorded_status='FAIL', execution_ref=HISTORICAL_PAIR_EXECUTION,
            reopened_by_extractor=False, status_provenance='Previously saved historical evidence; not a fresh pair evaluation.',
            original_pair_gate_replaced=value['original_pair_gate_replaced'], original_pair_gate_rerun=value['original_pair_gate_rerun']),
        extractor_scope=dict(evidence_input_is_original_diagnostic_only=True, reopens_nested_evidence=False,
            reruns_independent_reader=False, executes_NPU=False, changes_thresholds=False,
            numerical_qualification=False, performance_admission=False, task_accuracy=False,
            source_or_worker_dispatch_is_not_reexecuted=True))


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__)
    parser.add_argument('--diagnostic-ref', required=True, type=strict_json)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    path = ref_path(args.diagnostic_ref, INPUT_CAP)
    need(str(path) == EXPECTED_DIAGNOSTIC_PATH, 'only actual continuation reader output is accepted')
    output = args.output
    need(output.is_absolute() and '..' not in output.parts and output != path and
         not output.exists() and not output.is_symlink(), 'new exclusive absolute summary output')
    output_parents = parents(output)
    for kind, cap in ((resource.RLIMIT_AS, 512 * 2**20), (resource.RLIMIT_CPU, 30),
                      (resource.RLIMIT_FSIZE, OUTPUT_CAP), (resource.RLIMIT_CORE, 0)):
        soft, hard = resource.getrlimit(kind)
        target = min(cap, hard) if hard != resource.RLIM_INFINITY else cap
        if soft != resource.RLIM_INFINITY:
            target = min(target, soft)
        resource.setrlimit(kind, (target, target))
    deadline = started + 60
    own = Path(__file__).absolute()
    own_ref, _, own_identity = whole(own, SOURCE_CAP, deadline, keep=False)
    reference, raw, before = whole(path, INPUT_CAP, deadline, expected=args.diagnostic_ref)
    value = strict_json(raw)
    summary = project(value)
    after_ref, _, after = whole(path, INPUT_CAP, deadline, expected=reference, keep=False)
    _, _, own_after = whole(own, SOURCE_CAP, deadline, expected=own_ref, keep=False)
    need(before == after and own_identity == own_after, 'diagnostic and extractor unchanged before/after extraction')
    summary.update(diagnostic_ref=reference, extractor_ref=own_ref,
        complete_diagnostic_sha256_verified=True, complete_diagnostic_before_after_equal=reference == after_ref,
        diagnostic_file_identity_unchanged=True, extractor_file_identity_unchanged=True,
        output_cap_bytes=OUTPUT_CAP)
    data = canonical(summary)
    need(len(data) <= OUTPUT_CAP and time.monotonic() < deadline, 'bounded complete summary')
    need(parents(output) == output_parents, 'stable ordinary output ancestors')
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(data) == len(data), 'complete summary write')
        stream.flush()
        os.fsync(stream.fileno())
    output_ref, _, _ = whole(output, OUTPUT_CAP, deadline, keep=False)
    print(json.dumps(dict(summary=output_ref, diagnostic=reference, diagnostic_only=True,
        paired_gate_pass=False, numerical_admitted=False, performance_admitted=False,
        nested_evidence_reopened=False, NPU_executed=False), sort_keys=True))


if __name__ == '__main__':
    main()
