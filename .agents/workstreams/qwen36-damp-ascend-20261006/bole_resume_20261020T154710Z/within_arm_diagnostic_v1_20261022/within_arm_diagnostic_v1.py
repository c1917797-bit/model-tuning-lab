"""One-shot stdlib diagnostic of G1/O0 versus G2/O0 within each retained arm.

Both complete arms are revalidated by the fixed v4 host/original load_arm.
Two request generations are not assumed to have identical initial state.
This comparison cannot repair or replace the failed original ON/OFF gate.
The sole write is a new, exclusively created --output JSON.
"""
import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

sys.dont_write_bytecode = True
READER_ROOT = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/short_pair_reader_v4_20261022')
PRIOR_ROOT = Path('/opt/host/vnf/austinov/run-bole-short-pair-reader-v4-20261022T070247Z')
ARM_ROOTS = (
    Path('/opt/host/vnf/austinov/run-bole-short-state-20261021T123841Z-ON-v2'),
    Path('/opt/host/vnf/austinov/run-bole-short-state-20261021T123841Z-OFF-v2'),
)
PRIOR_REFS = [
    dict(path=str(PRIOR_ROOT/'EXECUTION.json'), bytes=3721,
         sha256='41202d391c8165138555b22e6b07c12d98e88cee456be8a757e35027bac163d1'),
    dict(path=str(PRIOR_ROOT/'INPUTS_BEFORE.json'), bytes=32191,
         sha256='ca10048adbf179d2e904e7a05965f857c22ba4ffa929d470c01564c5b30a2e65'),
    dict(path=str(PRIOR_ROOT/'INPUTS_AFTER.json'), bytes=32191,
         sha256='ca10048adbf179d2e904e7a05965f857c22ba4ffa929d470c01564c5b30a2e65'),
]
EXPECTED_READER = dict(path=str(READER_ROOT/'compare_completed_short.py'), bytes=3300,
    sha256='dd653ae8be7d83f3b83c0f1d069b64af4d4be2a72ec5d60dff49f0024a21d8df')
EXPECTED_HELPER = dict(path=str(READER_ROOT/'cleanup_summary.py'), bytes=3957,
    sha256='1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687')
CAP = 8 * 2**20
OUTPUT_CAP = 16 * 2**20
SEMANTIC_FIELDS = ('prompt', 'length', 'version', 'tokens', 'processed_nodes', 'emitted_tokens')
CANONICAL_ENCODING = 'UTF-8 json.dumps(sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False), no trailing newline'


def need(value, message):
    if not value:
        raise ValueError(message)


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_uid, value.st_gid, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def checked_bytes(reference):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'},
         'exact complete diagnostic input Ref')
    need(type(reference['path']) is str and type(reference['bytes']) is int
         and 0 <= reference['bytes'] <= CAP and type(reference['sha256']) is str
         and len(reference['sha256']) == 64
         and all(c in '0123456789abcdef' for c in reference['sha256']),
         'typed bounded diagnostic input Ref')
    path = Path(reference['path'])
    need(path.is_absolute() and str(path) == reference['path'] and '..' not in path.parts,
         'ordinary absolute diagnostic input path')
    parents = tuple((str(p), p.lstat().st_dev, p.lstat().st_ino, p.lstat().st_mode)
                    for p in path.parents)
    need(all(stat.S_ISDIR(row[3]) for row in parents), 'no symlink input ancestors')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size == reference['bytes'],
         'regular exact-size diagnostic input')
    descriptor = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        need(identity(os.fstat(stream.fileno())) == identity(before), 'input changed before read')
        data = stream.read(reference['bytes'] + 1)
        need(identity(os.fstat(stream.fileno())) == identity(before), 'input changed during read')
    after_parents = tuple((str(p), p.lstat().st_dev, p.lstat().st_ino, p.lstat().st_mode)
                          for p in path.parents)
    need(identity(path.lstat()) == identity(before) and after_parents == parents,
         'input path changed during read')
    need(len(data) == reference['bytes']
         and hashlib.sha256(data).hexdigest() == reference['sha256'],
         'exact whole diagnostic input SHA and bytes')
    return data


def obj(reference):
    return json.loads(checked_bytes(reference))


def checked_ref(reference):
    data = checked_bytes(reference)
    return dict(path=reference['path'], bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def own_ref():
    path = Path(__file__).resolve()
    need(path.stat().st_size <= CAP, 'bounded diagnostic source')
    with path.open('rb') as stream:
        data = stream.read(CAP + 1)
    need(len(data) <= CAP, 'bounded whole diagnostic source')
    result = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    checked_bytes(result)
    return result


def unique_refs(references):
    result = {}
    for reference in references:
        path = reference['path']
        need(path not in result or result[path] == reference, 'no conflicting input Ref')
        result[path] = reference
    return [result[path] for path in sorted(result)]


def canonical(value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')
    return dict(encoding=CANONICAL_ENCODING, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def token_diff(g1, g2):
    return [dict(index=i, generation_1=g1[i] if i < len(g1) else None,
                 generation_2=g2[i] if i < len(g2) else None)
            for i in range(max(len(g1), len(g2)))
            if i >= len(g1) or i >= len(g2) or g1[i] != g2[i]]


def field_diff(g1, g2):
    return {field: dict(generation_1_present=field in g1,
                        generation_2_present=field in g2,
                        generation_1=g1.get(field), generation_2=g2.get(field))
            for field in sorted(set(g1) | set(g2))
            if field not in g1 or field not in g2 or canonical(g1[field]) != canonical(g2[field])}


def digest_comparison(g1, g2):
    changes = field_diff(g1, g2)
    return dict(generation_1=g1, generation_2=g2, digest_equal=not changes,
                sha256_equal=g1['sha256'] == g2['sha256'],
                metadata_equal=all(field == 'sha256' for field in changes),
                differing_fields=list(changes), differences=changes)


def http_comparison(http, http_ref):
    rows = http['rows'][:2]
    need([row['label'] for row in rows] == ['warmup', 'measured'],
         'exact validated G1 and G2 HTTP ordering')
    first, second = [row['request'] for row in rows]
    need(type(first) is dict and type(second) is dict, 'complete HTTP request payloads')
    summaries = []
    for generation, row in enumerate(rows, 1):
        request = row['request']
        summaries.append(dict(generation=generation, label=row['label'], request_id=row['id'],
            header=row['header'], request=request, request_canonical_json=canonical(request),
            prompt=request['prompt'], prompt_canonical_json=canonical(request['prompt']),
            explicit_seed_present='seed' in request, explicit_seed=request.get('seed'),
            output_tokens=row['token_ids'], status=row['status'], done=row['done'], usage=row['usage']))
    seed_present = 'seed' in first and 'seed' in second
    return dict(http_result_ref=http_ref,
        request_hash_scope='Canonical JSON of the parsed request object retained in HTTP_RESULT; not a hash of original HTTP wire bytes.',
        generation_1=summaries[0], generation_2=summaries[1],
        request_payload_equal=canonical(first) == canonical(second),
        request_payload_differences=field_diff(first, second),
        prompt_equal=canonical(first['prompt']) == canonical(second['prompt']),
        both_explicit_seeds_present=seed_present,
        same_explicit_seed=seed_present and canonical(first['seed']) == canonical(second['seed']),
        output_tokens_equal=rows[0]['token_ids'] == rows[1]['token_ids'],
        output_token_differences=token_diff(rows[0]['token_ids'], rows[1]['token_ids']))


def rank_comparison(rank, evidence, http, receipts_root, by_path):
    g1, g2 = evidence[rank, 1, 0], evidence[rank, 2, 0]
    need(g1['length'] == g2['length'] == 131 and g1['version'] == g2['version'] == 0,
         'original first frame of each validated request')
    first = {field: g1[field] for field in SEMANTIC_FIELDS}
    second = {field: g2[field] for field in SEMANTIC_FIELDS}
    rows1 = {(row['layer'], row['kind']): row for row in g1['rows'] if row['kind'] in ('state', 'conv')}
    rows2 = {(row['layer'], row['kind']): row for row in g2['rows'] if row['kind'] in ('state', 'conv')}
    need(set(rows1) == set(rows2) and len(rows1) == len(rows2) == 96,
         'all48 state and all48 conv entering destinations')
    records = [dict(layer=layer, kind=kind,
                    before=digest_comparison(rows1[layer, kind]['before'], rows2[layer, kind]['before']))
               for layer, kind in sorted(rows1)]
    counts = {}
    for kind in ('state', 'conv'):
        selected = [row for row in records if row['kind'] == kind]
        need(len(selected) == 48, 'full same-kind entering coverage')
        counts[kind] = dict(total=48,
            digest_equal=sum(row['before']['digest_equal'] for row in selected),
            sha256_equal=sum(row['before']['sha256_equal'] for row in selected),
            metadata_equal=sum(row['before']['metadata_equal'] for row in selected),
            different_sha256_layers=[row['layer'] for row in selected if not row['before']['sha256_equal']],
            different_metadata_layers=[row['layer'] for row in selected if not row['before']['metadata_equal']])
    lifecycle = []
    for generation in (1, 2):
        begin_ref = by_path[str(receipts_root/('STATE-BEGIN-G%d-O-1-R%d.json' % (generation, rank)))]
        step_ref = by_path[str(receipts_root/('STATE-STEP-G%d-O0-R%d.json' % (generation, rank)))]
        begin = obj(begin_ref)['record']
        lifecycle.append(dict(generation=generation, begin_ref=begin_ref, step_ref=step_ref,
                              request=begin['request'], calibration=begin['calibration']))
    first_http, second_http = http['rows'][:2]
    g1_count, g2_count = g1['length']-len(g1['prompt']), g2['length']-len(g2['prompt'])
    need(g1_count == g2_count == 0, 'first frame cache prefix contains prompt only')
    return dict(rank=rank, generation_1_key=[rank, 1, 0], generation_2_key=[rank, 2, 0],
        generation_1_semantic=first, generation_2_semantic=second,
        semantic_equal=not field_diff(first, second), semantic_differences=field_diff(first, second),
        frame_token_differences=token_diff(g1['tokens'], g2['tokens']),
        emitted_token_differences=token_diff(g1['emitted_tokens'], g2['emitted_tokens']),
        same_committed_token_prefix=g1['prompt'] == g2['prompt']
            and first_http['token_ids'][:g1_count] == second_http['token_ids'][:g2_count],
        same_root_token=g1['tokens'][0] == g2['tokens'][0],
        same_frame_tokens=g1['tokens'] == g2['tokens'],
        identical_initial_state_assumed=False, before_row_count=len(records),
        all_entering_digests_equal=all(row['before']['digest_equal'] for row in records),
        all_entering_sha256_equal=all(row['before']['sha256_equal'] for row in records),
        all_entering_metadata_equal=all(row['before']['metadata_equal'] for row in records),
        by_kind=counts, entering_state_conv_rows=records, lifecycle=lifecycle)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    need(args.output.is_absolute() and str(args.output) == str(Path(str(args.output)))
         and '..' not in args.output.parts and args.output.parent.is_dir()
         and not args.output.exists() and not args.output.is_symlink()
         and not any(p.is_symlink() for p in args.output.parents),
         'fresh exclusive absolute diagnostic output')
    execution, frozen_before, frozen_after = [obj(reference) for reference in PRIOR_REFS]
    need(execution['schema'] == 'bole.retained-short-pair-reader-execution/v4'
         and execution['reader_and_pair_passed'] is False
         and execution['original_inputs_unchanged'] is True
         and execution['performance_admitted'] is False and execution['NPU_executed'] is False,
         'exact retained v4 failed read-only execution')
    need(set(frozen_before) == {'source', 'retained_inputs'} and frozen_before == frozen_after
         and len(frozen_before['source']) == 4 and len(frozen_before['retained_inputs']) == 124
         and frozen_before['source'] == execution['source'], 'exact prior complete input snapshots')
    need(EXPECTED_READER in frozen_before['source'] and EXPECTED_HELPER in frozen_before['source'],
         'exact deployed v4 reader and cleanup helper')
    commands = {command['label']: command for command in execution['commands']}
    need(set(commands) == {'regression', 'pair'} and commands['regression']['exit_code'] == 0
         and commands['pair']['exit_code'] == 1 and commands['pair']['timed_out'] is False,
         'original completed regression and failed pair preserved')
    original_failure = checked_bytes(commands['pair']['stderr']).decode('utf-8')
    need('ValueError: all four ranks/two generations/two frames' in original_failure,
         'original failed pair coverage predicate')
    references = unique_refs(PRIOR_REFS + frozen_before['source'] + frozen_before['retained_inputs']
        + [command[stream] for command in commands.values() for stream in ('stdout', 'stderr')]
        + [own_ref()])
    by_path = {reference['path']: reference for reference in references}
    need(str(args.output) not in by_path
         and not any(root == args.output or root in args.output.parents
                     for root in (READER_ROOT, PRIOR_ROOT, *ARM_ROOTS))
         and not any(Path(reference['path']).parent == args.output.parent
                     for reference in frozen_before['retained_inputs']),
         'diagnostic output is outside retained source and evidence directories')
    input_before = [checked_ref(reference) for reference in references]

    sys.path.insert(0, str(READER_ROOT))
    import compare_completed_short as V4
    R = V4.R
    imported_sources = []
    for name in ('compare_completed_short', 'cleanup_summary', 'compare_state_digest',
                 'short_state_digest', 'bole_performance_profile'):
        module_path = str(Path(sys.modules[name].__file__))
        need(module_path in by_path and R.ref(module_path) == by_path[module_path],
             'exact frozen actually imported module ' + name)
        imported_sources.append(dict(module=name, source=by_path[module_path]))
    need(not any(name == 'torch' or name.startswith(('torch.', 'torch_npu'))
                 for name in sys.modules), 'stdlib diagnostic without Torch or NPU imports')
    on_manifest, on_out, on_host_refs = V4.host(V4.ON)
    off_manifest, off_out, off_host_refs = V4.host(V4.OFF)
    need((on_out, off_out) == ARM_ROOTS and R.ref(R.__file__) == on_manifest['files']['compare_state_digest.py'],
         'fixed original arm roots and original independent reader')
    on_http_ref = by_path[str(on_out/'dense/performance-client/HTTP_RESULT.json')]
    off_http_ref = by_path[str(off_out/'dense/performance-client/HTTP_RESULT.json')]
    on, a, a_refs = R.load_arm(V4.ON, on_out/'dense/receipts', on_http_ref, 'ON')
    off, b, b_refs = R.load_arm(V4.OFF, off_out/'dense/receipts', off_http_ref, 'OFF')
    used_refs = unique_refs(on_host_refs + off_host_refs + a_refs + b_refs)
    need(all(reference['path'] in by_path and by_path[reference['path']] == reference
             for reference in used_refs), 'every validated arm operand in original frozen readset')
    settings = {field: dict(equal=on[field] == off[field], on=on[field], off=off[field])
                for field in ('checkpoint_config_ref', 'checkpoint_index_ref', 'common', 'native_speculative_config')}
    need(all(value['equal'] for value in settings.values()), 'unchanged original paired common settings')
    need(set(a) != set(b), 'original failed complete pair key-set predicate still fails')
    arms = []
    for mode, source, evidence, out, http_ref in (
            ('ON', V4.ON, a, on_out, on_http_ref), ('OFF', V4.OFF, b, off_out, off_http_ref)):
        http = obj(http_ref)
        comparisons = [rank_comparison(rank, evidence, http, out/'dense/receipts', by_path) for rank in range(4)]
        arms.append(dict(arm=mode, source=source, http=http_comparison(http, http_ref),
            complete_validated_frame_count=len(evidence),
            all_ranks_entering_digests_equal=all(row['all_entering_digests_equal'] for row in comparisons),
            all_ranks_entering_sha256_equal=all(row['all_entering_sha256_equal'] for row in comparisons),
            all_ranks_entering_metadata_equal=all(row['all_entering_metadata_equal'] for row in comparisons),
            ranks=comparisons))
    result = dict(schema='bole.retained-within-arm-initial-state-diagnostic/v1',
        diagnostic_only=True, paired_gate_pass=False, performance_admitted=False,
        NPU_executed=False, formal_performance=False, task_accuracy=False,
        independent_algorithm_numerical_qualification=False, cause_determined=False,
        distinct_request_generations=True, identical_initial_state_assumed=False,
        interpretation='G1/O0 versus G2/O0 within each observation arm, after full original arm validation. '
            'Matching HTTP prompt, explicit seed, or canonical request payload does not establish equal initial state. '
            'Before digests are selected-path staging snapshots before publication, not BEGIN-time tensor snapshots. '
            'Any observed repeatability or difference here cannot replace the failed original ON/OFF pair gate '
            'and does not establish causal attribution, error magnitude, numerical qualification, or performance admission.',
        original_failed_key_set_predicate_reconfirmed=True,
        prior_execution_ref=PRIOR_REFS[0], prior_pair_exit_code=1, prior_pair_failure=original_failure,
        actual_hosts_and_individual_arm_predicates_revalidated=True,
        imported_sources=imported_sources, paired_common_settings=settings,
        frame_counts=dict(on=len(a), off=len(b)), arms=arms, validated_arm_readset=used_refs)
    input_after = [checked_ref(reference) for reference in references]
    need(input_before == input_after, 'complete diagnostic input readset unchanged')
    result.update(input_readset_before=input_before, input_readset_after=input_after,
                  complete_input_readset_unchanged=True, input_count=len(references),
                  original_retained_input_count=124, v4_source_count=4)
    data = (json.dumps(result, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    need(len(data) <= OUTPUT_CAP, 'bounded complete diagnostic output')
    with args.output.open('xb') as stream:
        stream.write(data)
    print(json.dumps(dict(output=dict(path=str(args.output), bytes=len(data),
                          sha256=hashlib.sha256(data).hexdigest()),
        diagnostic_only=True, paired_gate_pass=False, performance_admitted=False,
        input_count=len(references), complete_input_readset_unchanged=True,
        arm_summary=[dict(arm=arm['arm'],
                          request_payload_equal=arm['http']['request_payload_equal'],
                          same_explicit_seed=arm['http']['same_explicit_seed'],
                          all_ranks_entering_sha256_equal=arm['all_ranks_entering_sha256_equal'],
                          all_ranks_entering_metadata_equal=arm['all_ranks_entering_metadata_equal'])
                     for arm in arms]), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
