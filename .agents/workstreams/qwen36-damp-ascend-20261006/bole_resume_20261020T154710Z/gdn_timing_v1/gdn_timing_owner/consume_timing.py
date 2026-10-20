"""Default-OFF Devices[] independent arithmetic reader for ALL component samples.

This reader imports no Torch/Triton. It reopens actual prior/source/owner/release,
all four timing indexes and all binary bytes. It recomputes statistics from every
raw AB/BA pair, without a speed threshold, frame filter or E2E conclusion.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import statistics

ROLES = ('original', 'candidate')
KEYS = ('O', 'P', 'U', 'S')
LAYERS = tuple(i for i in range(64) if i % 4 != 3)


def bootstrap(r):
    def checked(q):
        p = Path(q['path']); b = p.read_bytes()
        if (not p.is_absolute() or any(z.is_symlink() for z in (p, *p.parents)) or
                len(b) != q['bytes'] or hashlib.sha256(b).hexdigest() != q['sha256']):
            raise ValueError('exact independent entry source before imports')
        return p, b
    _, b = checked(r); x = json.loads(b); p, _ = checked(x['files']['timing_owner_common.py'])
    s = importlib.util.spec_from_file_location('_bole_timing_reader_common', str(p))
    C = importlib.util.module_from_spec(s); s.loader.exec_module(C)
    return C, C.package(r, __file__)


def stats(values, iterations):
    units = [v/iterations for v in values]
    return dict(count=len(units), batch_iterations=iterations, mean_ns=statistics.mean(units),
        median_ns=statistics.median(units), minimum_ns=min(units), maximum_ns=max(units), outliers_removed=0)


def scalar_stats(values):
    return dict(count=len(values), mean=statistics.mean(values), median=statistics.median(values),
                minimum=min(values), maximum=max(values), outliers_removed=0)


def samples(C, sample, number, cfg):
    """Pure independent arithmetic; deliberately does not call producer stats()."""
    C.need(len(sample['samples']) == cfg['sample_pairs'] and cfg['sample_pairs'] == 20 and
           cfg['batch_iterations'] == 4, 'exact finite preregistered pair count/batch')
    by_role = {r: [] for r in ROLES}; orders = {'AB': [], 'BA': []}; ratios = []; differences = []
    for pair, row in enumerate(sample['samples']):
        sequence = list(ROLES) if (number+pair) % 2 == 0 else list(reversed(ROLES))
        C.need(row['pair'] == pair and row['order'] == sequence and
               set(row['batch_elapsed_ns']) == set(ROLES), 'all raw pairs and exact alternate AB/BA schedule')
        for role in ROLES:
            v = row['batch_elapsed_ns'][role]
            C.need(type(v) is int and v > 0, 'positive integer actual host-device duration')
            by_role[role].append(v)
        orders['AB' if sequence == list(ROLES) else 'BA'].append(row)
        a, b = (row['batch_elapsed_ns'][r] for r in ROLES)
        ratios.append(a/b); differences.append((a-b)/cfg['batch_iterations'])
    summary = {r: stats(by_role[r], cfg['batch_iterations']) for r in ROLES}
    C.need(sample['summary'] == summary, 'all-sample independent mean/median/min/max arithmetic')
    warm = [list(ROLES) if (number+p) % 2 == 0 else list(reversed(ROLES)) for p in range(cfg['warmup_pairs'])]
    C.need(sample['warmup_order'] == warm and len(warm) == 4, 'exact symmetric warmup order')
    groups = {}
    for label, rows in orders.items():
        C.need(len(rows) == 10, 'ten AB and ten BA pairs in every frame/layout')
        groups[label] = dict(pair_numbers=[r['pair'] for r in rows],
            summary={role: stats([r['batch_elapsed_ns'][role] for r in rows], cfg['batch_iterations']) for role in ROLES},
            paired_original_over_candidate=scalar_stats([r['batch_elapsed_ns']['original']/
                r['batch_elapsed_ns']['candidate'] for r in rows]))
    return dict(summary=summary, order_groups=groups, paired_original_over_candidate=scalar_stats(ratios),
                paired_original_minus_candidate_unit_ns=scalar_stats(differences), raw_samples=sample['samples'])


def calibration(C, sample):
    c = sample['calibration']
    for key in ('original', 'guarded_candidate', 'compiled_candidate'):
        row = c[key]
        C.need(row['passed'] is True and set(row['hashes']) == set(KEYS), 'actual untimed output calibration')
        for label in ('literal', 'original_device'):
            C.need(set(row[label]) == set(KEYS), 'all O/P/U plus selected state calibration metrics')
            for metric in row[label].values():
                C.need(metric['passed'] is True and all(type(metric[k]) in (int, float) and
                    math.isfinite(metric[k]) and metric[k] >= 0 for k in ('peak_abs', 'relative_l2', 'reference_l2'))
                    and metric['relative_l2'] <= 2e-4, 'finite original112 metric evidence')
        C.need(all(type(h) is str and re.fullmatch('[0-9a-f]{64}', h) for h in row['hashes'].values()),
               'complete actual calibration output hashes')
    C.need(c['original']['hashes']['P'] == c['guarded_candidate']['hashes']['P'] and
           c['guarded_candidate']['hashes'] == c['compiled_candidate']['hashes'],
           'guarded P bitwise original; direct compiled all outputs equal guarded calibration')
    for role, ref_key in (('original', 'original'), ('candidate', 'guarded_candidate')):
        post = c['post_timing'][role]
        C.need(post['passed'] is True and post['bitwise_preflight'] is True and
               post['hashes'] == c[ref_key]['hashes'], 'post-timing final output bitwise preflight evidence')
        for label in ('literal', 'original_device'):
            C.need(set(post[label]) == set(KEYS) and all(q['passed'] is True and
                all(type(q[k]) in (int, float) and math.isfinite(q[k]) and q[k] >= 0
                    for k in ('peak_abs', 'relative_l2', 'reference_l2')) and q['relative_l2'] <= 2e-4
                for q in post[label].values()), 'post-timing finite original112 metric evidence')
    guard = sample['input_guard']
    C.need(guard['unchanged'] is True and set(guard['hashes']) == set(guard['identities']) ==
           {'q', 'k', 'v', 'beta', 'gamma', 'state'} and
           all(type(h) is str and re.fullmatch('[0-9a-f]{64}', h) for h in guard['hashes'].values()),
           'complete actual unchanged input storage/hash evidence')
    state = guard['identities']['state']
    C.need(len(state) == 7 and state[3] == [1, 12, 128, 128] and state[5:] == ['torch.float32', 'npu:0'] and
           state[4][-2:] == ([128, 1] if sample['layout'] == 'contiguous' else [1, 128]),
           'canonical actual state shape/dtype/logical device and both declared strides')
    first = sample['compile_or_first_use']
    C.need(first['all_first_compile_or_cache_loading_outside_samples'] is True and
           first['includes_wrapper_source_finite_topology_validation'] is True and
           first['isolated_compiler_time_ns'] is None and first['disk_compile_vs_cache_hit_known'] is False and
           all(type(first[k]) is int and first[k] > 0 for k in ('original_untimed_host_ns',
               'candidate_guarded_compile_or_cache_load_host_ns')) and
           len(first['new_runtime_cache_entries']) == 2 and all(type(v) is int and v >= 0
               for v in first['new_runtime_cache_entries']), 'untimed first-use boundary and honest compile accounting')


def release(C, x, m, result_ref, release_ref, npu_owner_ref, inputs_ref):
    a = C.admission(x, m, current=False); rel = C.obj(release_ref)
    C.need(rel['schema'] == 'bole.gdn3-timing-owner-released/v1' and rel['authority'] == 'MAIN' and
           rel['timing_result'] == result_ref and rel['admission'] == m['admission'] and
           rel['owner_stop_completed'] is True, 'actual owner release joins exact timing result and admission')
    stopped = C.inspection(rel['controller_inspection'])
    C.device_inspection(stopped, cid=a['owned_container_id'], running=False, name=x['name'])
    C.need(stopped['State']['ExitCode'] == 0, 'actual stopped timing process exited zero')
    own = C.obj(npu_owner_ref)
    C.need(own['schema'] == 'bole.gdn3-finite-timing-npu-owner/v1' and own['authority'] == 'MAIN' and
           own['inputs'] == inputs_ref and own['owner_source'] == x['files']['timing_owner.py'] and
           own['cid'] == a['owned_container_id'] and own['manifest'] == C.ref(Path(m['admission']['path']).parent/'MANIFEST.json') and
           own['admission'] == m['admission'] and own['timing_result'] == result_ref and
           own['release'] == release_ref and own['primary'] is None and own['secondary'] == [] and
           own['source_before'] == own['source_after'] and own['physical'] == [4] and
           own['protected'] == [0, 1, 2, 3] and own['E2E_measured'] is False and own['formal_success'] is False,
           'source-bound actual finite stopped NPU owner receipt')
    child = C.obj(own['child']); C.need(child['exit_code'] == 0, 'actual owned timing child exited zero')
    C.checked(child['stdout']); C.checked(child['stderr'])
    for r in own['source_before'].values(): C.checked(r)
    C.need(own['source_before'] == C.snapshot(x, inputs_ref), 'complete independently reopened source/prior evidence inventory')
    return a, own


def reader_identity(C, x, inputs_ref, root):
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == '' and
           os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0' and
           os.environ.get('BOLE_GDN3_TIMING_CONSUME_ENABLE') == '1' and
           not list(Path('/dev').glob('davinci[0-9]*')), 'explicit Devices[] consumer with no numbered NPU nodes')
    a = C.obj(C.ref(root/'READER-ADMISSION.json'))
    C.need(a['schema'] == 'bole.gdn3-timing-reader-admission/v1' and a['authority'] == 'MAIN' and
           a['inputs'] == inputs_ref and a['image'] == C.IMAGE and a['cid'] in Path('/proc/self/cgroup').read_text(),
           'actual separate Devices[] reader identity/cgroup before consumption')
    inspected = C.device_inspection(C.inspection(a['controller_inspection']), cid=a['cid'], running=False,
                                    name=x['reader_name'], cpu=True)
    env = dict(v.split('=', 1) for v in inspected['Config']['Env'] if '=' in v)
    expected = dict(C.ENV, ASCEND_RT_VISIBLE_DEVICES='', BOLE_GDN3_TIMING_ENABLE='0',
                    BOLE_GDN3_TRITON_ENABLE='0', BOLE_GDN3_TIMING_CONSUME_ENABLE='1')
    C.need(all(env.get(k) == v and os.environ.get(k) == v for k, v in expected.items()),
           'actual Devices[] exact inspect/current bounded CPU environment')
    C.need(all(z['RW'] is False or (z['Type'] == 'bind' and z['Destination'] == str(root)) or
               (z['Type'] == 'tmpfs' and z['Destination'] == '/tmp') for z in inspected['Mounts']),
           'reader sources/evidence readonly with one dedicated output leaf')
    return a


def run(C, x, inputs_ref, manifest_ref, result_ref, release_ref, npu_owner_ref, output):
    C.prior_chain(x, installed=True)
    m = C.final_manifest(x, manifest_ref, current=False)
    root = Path(manifest_ref['path']).parent
    identity = reader_identity(C, x, inputs_ref, root)
    a, own = release(C, x, m, result_ref, release_ref, npu_owner_ref, inputs_ref)
    result = C.obj(result_ref); cfg = m['configuration']
    C.need(result['schema'] == 'bole.gdn3-warmed-host-device-result/v1' and
           result['manifest'] == manifest_ref and result['configuration'] == cfg and
           all(result[k] == m[k] for k in ('replay_independent', 'replay_result', 'replay_release', 'admission')) and
           result['frames'] == 192 and result['frame_layouts'] == 384 and len(result['ranks']) == 4 and
           result['all_samples_retained'] is True and result['timing_complete'] is True and
           result['every_timed_iteration_output_checked'] is False and
           all(result[k] is False for k in ('whole_model_qualified', 'model_ready', 'E2E_measured',
               'ten_percent_E2E_claim', 'formal_success', 'scheduler_committed', 'persistent_cache_written')),
           'complete component-only timing result with honest output-check scope')
    C.need(result['clock'] == 'host perf_counter_ns; pre-sync outside/start; final NPU sync inside interval' and
           result['includes'] == 'Python dispatch, allocations, Torch P/ratio, actual compute and completion wait' and
           result['excludes'] == 'guards, H2D/D2H, source/binary checks, oracle, codec, first compile/cache load',
           'symmetric declared host-plus-device clock and measured computation boundaries')
    output = Path(output)
    C.need(output.is_dir() and output.is_absolute() and not any(output.iterdir()) and
           output == root/'consumer' and not any(z.is_symlink() for z in (output, *output.parents)),
           'fresh ordinary independent output at exact new leaf')
    binary_inventory = {r['sha256']: r for r in result['binaries']}
    C.need(len(binary_inventory) == len(result['binaries']) > 0, 'unique exhaustive actual binary inventory')
    for r in binary_inventory.values():
        C.checked(r)
        C.need(Path(r['path']).parent == root/'data' and Path(r['path']).name == 'KERNEL-'+r['sha256']+'.npubin'
               and 0 < r['bytes'] <= 63*2**20, 'new-leaf bounded actual saved npubin bytes')
    replay = C.obj(m['replay_manifest']); refs = []; seen = set(); number = 0; selection = owner = None
    sums = {layout: [0.0, 0.0] for layout in cfg['layouts']}
    order_sums = {layout: {order: [0.0, 0.0] for order in ('AB', 'BA')} for layout in cfg['layouts']}
    for rank, rr in enumerate(result['ranks']):
        C.need(Path(rr['path']) == root/'data'/('TIMING-RANK-%d.json' % rank), 'all4 exact new timing indexes')
        row = C.obj(rr); original = C.obj(replay['receipts'][rank]['receipt'])
        C.need(row['schema'] == 'bole.gdn3-warmed-host-device-rank/v1' and row['rank'] == rank and
               row['manifest'] == manifest_ref and row['original_receipt'] == replay['receipts'][rank]['receipt'] and
               row['original_raw'] == original['raw'] and [r['layer'] for r in row['rows']] == list(LAYERS) and
               all(row[k] is False for k in ('model_ready', 'E2E_measured', 'formal_success')),
               'every actual source-bound GDN rank/frame once')
        C.checked(original['raw'])
        if selection is None: selection, owner = row['selection'], row['owner']
        C.need(row['selection'] == selection and row['owner'] == owner and selection['policy'] == 'actual-r23-selected',
               'all4 original actual owner/selected terminal joined')
        tokens = selection['tokens']; choice = selection['target_root_argmax']
        terminal = 1 if choice == tokens[1] else 2 if choice == tokens[2] else 0
        C.need(len(tokens) == 3 and selection['terminal'] == terminal and
               selection['processed_nodes'] == ([0] if terminal == 0 else [0, terminal]),
               'actual saved selected-terminal derivation internally consistent')
        rows = []
        for layer in row['rows']:
            C.need([f['layout'] for f in layer['layouts']] == cfg['layouts'], 'both layouts of every actual frame')
            for sample in layer['layouts']:
                C.need(sample['frame_number'] == number and sample['terminal'] == terminal and
                       sample['timing_complete'] is True and sample['candidate_dispatch'] ==
                       'validated cached CompiledKernel runners' and sample['computation'] ==
                       'all-node O/P/U plus ONE actual selected state; Torch P/ratio/allocations per call' and
                       sample['every_timed_iteration_output_checked'] is False and
                       sample['output_check_scope'] == 'preflight/JIT/compiled/warmup and final timed output per role' and
                       all(sample[k] is False for k in ('model_ready', 'E2E_measured', 'formal_success')),
                       'all384 exact frames, equal per-call work, and honest untimed correctness scope')
                calibration(C, sample)
                C.need(len(sample['binaries']) == 2, 'actual forward plus selected-state binary proofs')
                for proof in sample['binaries']:
                    b = proof['binary']; C.need(binary_inventory.get(b['sha256']) == b and
                        proof['loaded'] is True and proof['source_bound'] is True and proof['compiled_runner'] is True and
                        proof['target']['backend'] == 'npu' and type(proof['signature']) is dict and
                        type(proof['constants']) is dict and type(proof['compiled_hash']) is str and proof['compiled_hash'],
                        'all actual loaded source-bound compiled binary inventories joined')
                    C.checked(b); seen.add(b['sha256'])
                computed = samples(C, sample, number, cfg)
                for i, role in enumerate(ROLES):
                    sums[sample['layout']][i] += computed['summary'][role]['mean_ns']
                    for label in ('AB', 'BA'):
                        order_sums[sample['layout']][label][i] += computed['order_groups'][label]['summary'][role]['mean_ns']
                rows.append(dict(layer=layer['layer'], layout=sample['layout'], frame_number=number,
                                 terminal=terminal, statistics=computed))
                number += 1
        refs.append(C.write(output/('STATISTICS-RANK-%d.json' % rank), dict(
            schema='bole.gdn3-independent-statistics-rank/v1', rank=rank, timing_rank=rr, rows=rows,
            all_samples_retained=True, outliers_removed=0, NPU=False, E2E_measured=False, formal_success=False)))
    C.need(number == 384 and seen == set(binary_inventory), 'all frames/samples/binary bytes consumed without extras or filtering')
    aggregates = {}; by_order = {}
    for layout, (orig, cand) in sums.items():
        expected = dict(frames=192, original_sum_mean_unit_ns=orig, candidate_sum_mean_unit_ns=cand,
            ratio_original_over_candidate=orig/cand, excluded_frames=0, excluded_samples=0, component_scope_only=True)
        C.need(result['aggregate'][layout] == expected, 'independently recomputed complete aggregate matches producer')
        aggregates[layout] = expected
        by_order[layout] = {label: dict(frames=192, sample_pairs_per_frame=10,
            original_sum_mean_unit_ns=values[0], candidate_sum_mean_unit_ns=values[1],
            ratio_original_over_candidate=values[0]/values[1], component_scope_only=True)
            for label, values in order_sums[layout].items()}
    C.need(set(result['aggregate']) == set(cfg['layouts']), 'no extra aggregate winning-frame groups')
    C.need(C.unchanged(own['source_before']), 'source and original evidence stable after independent reopens')
    report = dict(schema='bole.gdn3-independent-warmed-statistics/v1', inputs=inputs_ref, manifest=manifest_ref,
        timing_result=result_ref, owner_release=release_ref, npu_owner=npu_owner_ref, reader_identity=identity,
        runtime_container_refs=C.runtime_refs(), runtime_host_evidence=x['runtime_host_evidence'],
        replay_independent=m['replay_independent'], ranks=refs, actual_frames=192, actual_frame_layouts=384,
        raw_sample_pairs=384*20, raw_batch_durations=384*20*2, iterations_per_batch=4,
        warmup_pairs_per_frame=4, order_pairs_per_frame=dict(AB=10, BA=10), aggregate=aggregates,
        aggregate_by_order=by_order, all_samples_retained=True, excluded_frames=0, excluded_samples=0,
        outliers_removed=0, independent_statistics_pass=True, tensor_runtime_imported=False, NPU=False,
        numerical_replay_recomputed=False, calibration_scope='saved untimed metric/hash evidence checked; no new tensor math',
        speed_threshold_asserted=False, component_scope_only=True, model_ready=False, performance_ready=False,
        whole_model_qualified=False, E2E_measured=False, ten_percent_E2E_claim=False, formal_success=False)
    total = sum(p.stat().st_size for p in output.iterdir())
    C.need(total + len(json.dumps(report)) <= 8*2**20, 'bounded independent reader output8MiB')
    return C.write(output/'TIMING-INDEPENDENT.json', report)


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--execute', action='store_true')
    for name in ('inputs-ref', 'manifest-ref', 'result-ref', 'owner-release-ref', 'npu-owner-ref'):
        p.add_argument('--'+name)
    p.add_argument('--output', type=Path); a = p.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False, NPU=False, tensor_runtime_imported=False,
                              independent_statistics_pass=False, prepared_only=True, formal_success=False))); return 0
    if not all((a.inputs_ref, a.manifest_ref, a.result_ref, a.owner_release_ref, a.npu_owner_ref, a.output)):
        p.error('all exact inputs/manifest/result/release/owner refs and fresh output required')
    ir, mr, rr, rel, own = [json.loads(v) for v in (a.inputs_ref, a.manifest_ref, a.result_ref, a.owner_release_ref, a.npu_owner_ref)]
    C, x = bootstrap(ir)
    result = run(C, x, ir, mr, rr, rel, own, a.output)
    print(json.dumps(dict(result=result, NPU=False, E2E_measured=False, formal_success=False))); return 0


if __name__ == '__main__':
    raise SystemExit(main())
