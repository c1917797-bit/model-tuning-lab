"""One-shot, stdlib-only diagnosis of the retained failed BOLE short pair.

The original v4 host and original load_arm validators remain the authorities.
Shared-frame comparisons below are diagnostics only, never a paired gate pass.
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
    return dict(path=reference['path'], bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest())


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


def logical_order(key):
    rank, generation, ordinal = key
    return generation, ordinal, rank


def token_diff(a, b):
    return [dict(index=i, on=a[i] if i < len(a) else None,
                 off=b[i] if i < len(b) else None)
            for i in range(max(len(a), len(b)))
            if i >= len(a) or i >= len(b) or a[i] != b[i]]


def digest_diff(a, b):
    fields = sorted(set(a) | set(b))
    different = [field for field in fields if a.get(field) != b.get(field)]
    return dict(different=bool(different), differing_fields=different,
                on_sha256=a['sha256'], off_sha256=b['sha256'],
                metadata_equal=all(a.get(field) == b.get(field)
                                   for field in fields if field != 'sha256'),
                metadata_differences={field: dict(on=a.get(field), off=b.get(field))
                                      for field in different if field != 'sha256'})


def frame_diagnostic(key, a, b, on_tokens, off_tokens):
    # The original validator proves length=131+sum(previous processed_nodes).
    # The next root token is separate from that already committed cache prefix.
    on_count = a['length'] - len(a['prompt'])
    off_count = b['length'] - len(b['prompt'])
    need(0 <= on_count < len(on_tokens) and 0 <= off_count < len(off_tokens),
         'validated frame maps into actual emitted HTTP prefix')
    on_prefix, off_prefix = on_tokens[:on_count], off_tokens[:off_count]
    same_prompt = a['prompt'] == b['prompt']
    same_cache = same_prompt and a['length'] == b['length'] and on_prefix == off_prefix
    same_root = a['tokens'][0] == b['tokens'][0]
    semantic = {field: dict(on=a[field], off=b[field]) for field in SEMANTIC_FIELDS
                if a[field] != b[field]}
    left = {(row['layer'], row['kind']): row for row in a['rows']}
    right = {(row['layer'], row['kind']): row for row in b['rows']}
    need(set(left) == set(right), 'original all-destination row identity')
    rows = []
    entering = []
    differing_fields = list(semantic)
    for row_key in sorted(left):
        layer, kind = row_key
        x, y = left[row_key], right[row_key]
        after = digest_diff(x['after'], y['after'])
        before = digest_diff(x['before'], y['before']) if kind in ('state', 'conv') else None
        rows.append(dict(layer=layer, kind=kind, before=before, after=after))
        if before is not None and before['different']:
            entering.append(dict(layer=layer, kind=kind, **before))
            differing_fields.append('rows[%d,%s].before' % row_key)
        if after['different']:
            differing_fields.append('rows[%d,%s].after' % row_key)
    return dict(key=list(key), same_prompt=same_prompt,
                same_committed_cache_prefix=same_cache,
                same_cache_prefix_and_root=same_cache and same_root,
                same_cache_prefix_and_frame_tokens=same_cache and a['tokens'] == b['tokens'],
                on_committed_output_prefix=on_prefix, off_committed_output_prefix=off_prefix,
                on_root=a['tokens'][0], off_root=b['tokens'][0],
                semantic_differing_fields=list(semantic), semantic_differences=semantic,
                all_differing_fields=differing_fields,
                entering_state_conv_differences=entering,
                row_count=len(rows), rows=rows)


def first_records(frames, predicate):
    # Logical generation/ordinal order, not an assertion about wall-clock order.
    selected = [frame for frame in frames if predicate(frame)]
    per_rank_generation = []
    for rank in range(4):
        for generation in (1, 2):
            candidates = [f for f in selected if f['key'][:2] == [rank, generation]]
            frame = candidates[0] if candidates else None
            per_rank_generation.append(dict(rank=rank, generation=generation,
                first=None if frame is None else dict(
                    key=frame['key'], all_differing_fields=frame['all_differing_fields'],
                    semantic_differences=frame['semantic_differences'],
                    same_committed_cache_prefix=frame['same_committed_cache_prefix'],
                    same_cache_prefix_and_root=frame['same_cache_prefix_and_root'],
                    same_cache_prefix_and_frame_tokens=frame['same_cache_prefix_and_frame_tokens'],
                    entering_state_conv_differences=frame['entering_state_conv_differences'])))
    return dict(first_logical_key=selected[0]['key'] if selected else None,
                per_rank_generation=per_rank_generation)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False, description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    need(args.output.is_absolute() and args.output.parent.is_dir()
         and not args.output.exists() and not args.output.is_symlink()
         and not any(p.is_symlink() for p in args.output.parents),
         'fresh exclusive absolute diagnostic output')

    execution, frozen_before, frozen_after = [obj(reference) for reference in PRIOR_REFS]
    need(execution['schema'] == 'bole.retained-short-pair-reader-execution/v4'
         and execution['reader_and_pair_passed'] is False
         and execution['original_inputs_unchanged'] is True
         and execution['performance_admitted'] is False
         and execution['NPU_executed'] is False,
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
         and not any(root == args.output or root in args.output.parents for root in
                     (READER_ROOT, PRIOR_ROOT,
                      Path('/opt/host/vnf/austinov/run-bole-short-state-20261021T123841Z-ON-v2'),
                      Path('/opt/host/vnf/austinov/run-bole-short-state-20261021T123841Z-OFF-v2'))),
         'diagnostic output is outside retained source and evidence roots')
    input_before = [checked_ref(reference) for reference in references]

    sys.path.insert(0, str(READER_ROOT))
    import compare_completed_short as V4
    R = V4.R
    for name in ('compare_completed_short', 'cleanup_summary', 'compare_state_digest',
                 'short_state_digest', 'bole_performance_profile'):
        module_path = str(Path(sys.modules[name].__file__))
        need(module_path in by_path and R.ref(module_path) == by_path[module_path],
             'exact frozen actually imported module ' + name)
    need(not any(name == 'torch' or name.startswith(('torch.', 'torch_npu'))
                 for name in sys.modules), 'stdlib diagnostic without Torch or NPU imports')
    on_manifest, on_out, on_host_refs = V4.host(V4.ON)
    off_manifest, off_out, off_host_refs = V4.host(V4.OFF)
    need(R.ref(R.__file__) == on_manifest['files']['compare_state_digest.py'],
         'original exact independent reader')
    on_http_ref = by_path[str(on_out/'dense/performance-client/HTTP_RESULT.json')]
    off_http_ref = by_path[str(off_out/'dense/performance-client/HTTP_RESULT.json')]
    on, a, a_refs = R.load_arm(V4.ON, on_out/'dense/receipts', on_http_ref, 'ON')
    off, b, b_refs = R.load_arm(V4.OFF, off_out/'dense/receipts', off_http_ref, 'OFF')
    used_refs = unique_refs(on_host_refs + off_host_refs + a_refs + b_refs)
    need(all(reference['path'] in by_path and by_path[reference['path']] == reference
             for reference in used_refs), 'every validated arm operand in original frozen readset')
    settings = {field: dict(equal=on[field] == off[field], on=on[field], off=off[field])
                for field in ('checkpoint_config_ref', 'checkpoint_index_ref', 'common',
                              'native_speculative_config')}
    need(all(value['equal'] for value in settings.values()), 'unchanged original paired common settings')
    on_http, off_http = obj(on_http_ref), obj(off_http_ref)
    http_rows = []
    for left, right in zip(on_http['rows'], off_http['rows']):
        changes = token_diff(left['token_ids'], right['token_ids'])
        left_prompt = left['request'].get('prompt') if type(left.get('request')) is dict else None
        right_prompt = right['request'].get('prompt') if type(right.get('request')) is dict else None
        http_rows.append(dict(label=left['label'], on_id=left['id'], off_id=right['id'],
            same_prompt=left_prompt == right_prompt if left_prompt is not None and right_prompt is not None else None,
            on_tokens=left['token_ids'], off_tokens=right['token_ids'],
            differences=changes, first_difference_index=changes[0]['index'] if changes else None))
    keys_a, keys_b = set(a), set(b)
    per_rank_generation = []
    for rank in range(4):
        for generation in (1, 2):
            entry = dict(rank=rank, generation=generation)
            for label, evidence, out in [('on', a, on_out), ('off', b, off_out)]:
                keys = sorted([key for key in evidence if key[:2] == (rank, generation)])
                retire_path = out/'dense/receipts'/('STATE-RETIRE-G%d-O-1-R%d.json' % (generation, rank))
                begin_path = out/'dense/receipts'/('STATE-BEGIN-G%d-O-1-R%d.json' % (generation, rank))
                retired = obj(by_path[str(retire_path)])['record']['retirement']
                calibration = obj(by_path[str(begin_path)])['record']['calibration']
                need(retired['steps'] == len(keys), 'actual retired nr equals fully validated frame count')
                entry[label] = dict(nr=retired['steps'], keys=[list(key) for key in keys],
                    calibration_pid=calibration['pid'], calibration_ref=calibration['calibration_ref'],
                    calibration_created=calibration['created'], calibration_reused=calibration['reused'])
            per_rank_generation.append(entry)
    frames = [frame_diagnostic(key, a[key], b[key],
                 on_http['rows'][key[1]-1]['token_ids'], off_http['rows'][key[1]-1]['token_ids'])
              for key in sorted(keys_a & keys_b, key=logical_order)]
    result = dict(schema='bole.retained-short-pair-diagnostic/v1', diagnostic_only=True,
        paired_gate_pass=False, performance_admitted=False, NPU_executed=False,
        formal_performance=False, task_accuracy=False,
        independent_algorithm_numerical_qualification=False,
        cause_determined=False,
        interpretation='Logical shared-frame diagnostics cannot repair the failed complete key-set gate. '
            'Different emitted tokens or paths can make later state incomparable; no causal attribution '
            'to observation policy, numerics, or another mechanism is inferred here.',
        logical_order='generation, ordinal, rank; not wall-clock order',
        prefix_definition='Committed cache prefix is prompt plus HTTP output tokens[:length-len(prompt)]. '
            'The next root token is recorded separately; same-cache-prefix-and-frame-tokens additionally '
            'requires all proposed tokens equal. Neither label asserts equality of recurrent state.',
        prior_execution_ref=PRIOR_REFS[0], prior_pair_exit_code=1,
        prior_pair_failure=original_failure, sources=dict(on=V4.ON, off=V4.OFF),
        actual_hosts_and_individual_arm_predicates_revalidated=True,
        paired_common_settings=settings, http_rows=http_rows,
        frame_counts=dict(on=len(a), off=len(b), common=len(frames)),
        original_failed_key_set_predicate_reconfirmed=keys_a != keys_b,
        complete_key_sets=dict(on=[list(k) for k in sorted(keys_a, key=logical_order)],
                               off=[list(k) for k in sorted(keys_b, key=logical_order)],
                               on_only=[list(k) for k in sorted(keys_a-keys_b, key=logical_order)],
                               off_only=[list(k) for k in sorted(keys_b-keys_a, key=logical_order)]),
        per_rank_generation=per_rank_generation, shared_frame_diagnostics=frames,
        earliest_entering_state_conv_difference=first_records(frames, lambda f: bool(f['entering_state_conv_differences'])),
        earliest_difference_at_equal_committed_cache_prefix=first_records(frames,
            lambda f: f['same_committed_cache_prefix'] and bool(f['all_differing_fields'])),
        earliest_difference_at_equal_cache_prefix_and_root=first_records(frames,
            lambda f: f['same_cache_prefix_and_root'] and bool(f['all_differing_fields'])),
        earliest_difference_at_equal_cache_prefix_and_frame_tokens=first_records(frames,
            lambda f: f['same_cache_prefix_and_frame_tokens'] and bool(f['all_differing_fields'])),
        validated_arm_readset=used_refs)
    input_after = [checked_ref(reference) for reference in references]
    need(input_before == input_after, 'complete diagnostic input readset unchanged')
    result.update(input_readset_before=input_before, input_readset_after=input_after,
                  complete_input_readset_unchanged=True,
                  original_retained_input_count=124, v4_source_count=4)
    data = (json.dumps(result, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    need(len(data) <= OUTPUT_CAP, 'bounded complete diagnostic output')
    with args.output.open('xb') as stream:
        stream.write(data)
    print(json.dumps(dict(output=dict(path=str(args.output), bytes=len(data),
                          sha256=hashlib.sha256(data).hexdigest()),
        diagnostic_only=True, paired_gate_pass=False, performance_admitted=False,
        frame_counts=result['frame_counts'], input_count=len(references),
        complete_input_readset_unchanged=True), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
