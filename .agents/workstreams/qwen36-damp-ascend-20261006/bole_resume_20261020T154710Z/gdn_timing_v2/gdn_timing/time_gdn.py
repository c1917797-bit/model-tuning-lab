"""Default-OFF warmed component timing; requires a successful independent replay.

MAIN alone admits the owned same-image singleton. This program contains no
Docker, physical device selection, Git, service or live-cache publication code.
"""
import argparse
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import statistics
import sys
import time
import traceback


KEYS = ('O', 'P', 'U', 'S')
CONFIG = dict(warmup_pairs=4, sample_pairs=20, batch_iterations=4, cpu_threads=1,
              order='alternate-AB-BA-by-global-frame-and-pair-parity',
              clock='perf_counter_ns-with-symmetric-NPU-synchronize',
              terminal_policy='actual-r23-selected', frames='all192',
              layouts=['contiguous', 'column_strided'])


def need(value, message):
    if not value:
        raise ValueError(message)


def checked_bootstrap(reference):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    path = Path(reference['path'])
    need(path.is_absolute() and path.is_file() and
         not any(x.is_symlink() for x in (path, *path.parents)), 'ordinary absolute Ref3')
    data = path.read_bytes()
    need(len(data) == reference['bytes'] and hashlib.sha256(data).hexdigest() == reference['sha256'],
         'exact source bytes before helper import')
    return path, data


def bootstrap(reference):
    _, data = checked_bootstrap(reference); m = json.loads(data)
    need(m['schema'] == 'bole.gdn3-warmed-timing-manifest/v1' and m['configuration'] == CONFIG,
         'one exact preregistered correctness-gated timing variant')
    need(set(m['files']) == {'time_gdn.py', 'timing_paths.py'}, 'two complete timing sources')
    for r in m['files'].values():
        checked_bootstrap(r)
    own = Path(__file__).resolve()
    need(checked_bootstrap(m['files']['time_gdn.py'])[0] == own and
         Path(m['files']['timing_paths.py']['path']).parent == own.parent,
         'exact private timing source pair')
    _, replay_data = checked_bootstrap(m['replay_manifest'])
    replay = json.loads(replay_data)
    helper_ref = replay['files']['replay_common.py']
    helper_path, _ = checked_bootstrap(helper_ref)
    name = '_bole_timing_replay_common'
    need(name not in sys.modules, 'fresh timing source helper namespace')
    spec = importlib.util.spec_from_file_location(name, str(helper_path))
    H = importlib.util.module_from_spec(spec); sys.modules[name] = H
    spec.loader.exec_module(H)
    H.need(H.ref(helper_path) == helper_ref, 'helper stable across import')
    return H, m


def successful_replay(H, m):
    replay, receipts, prior_admission = H.manifest(m['replay_manifest'], H.__file__)
    consumer = H.load_module(replay['files']['consume_gdn.py'], '_bole_timing_replay_consumer')
    consumer.release(H, replay, m['replay_result'], m['replay_release'])
    result = H.obj(m['replay_result']); report = H.obj(m['replay_independent'])
    H.need(result['schema'] == 'bole.gdn3-actual-replay-result/v1' and
           result['manifest'] == m['replay_manifest'] and result['admission'] == replay['admission'] and
           result['source'] == replay['actual_source'] and result['frames'] == 192 and
           result['frame_layouts'] == 384 and result['all_actual_results_exported'] is True and
           result['local_component_checks_pass'] is True and
           [r['rank'] for r in result['summary']] == [0, 1, 2, 3] and
           all(r['passed'] is True for r in result['summary']) and
           result['model_ready'] is False and result['formal_success'] is False,
           'complete independently consumable successful actual replay')
    H.need(report['schema'] == 'bole.gdn3-independent-actual-replay/v1' and
           report['manifest'] == m['replay_manifest'] and report['replay_result'] == m['replay_result'] and
           report['owner_release'] == m['replay_release'] and report['frames'] == 192 and
           report['frame_layouts'] == 384 and report['component_replay_independent_pass'] is True and
           report['exact_original112_bounds'] is True and report['literal_sequential_FP64_oracle'] is True and
           report['actual_original_device_results_included'] is True and
           report['P_bitwise_original_checked'] is True and report['actual_inputs_bitwise_unchanged'] is True and
           report['lossless_actual_byte_exports'] is True and report['NPU'] is False and
           report['model_ready'] is False and report['formal_success'] is False and
           [r['rank'] for r in report['ranks']] == [0, 1, 2, 3],
           'successful exact independent Devices[] replay chain required before execution')
    H.need(len(result['ranks']) == len(report['ranks']) == 4, 'four actual replay rank indexes')
    for rank, r in enumerate(report['ranks']):
        H.need(r['index'] == result['ranks'][rank] and r['original_raw'] == receipts[rank]['raw'] and
               r['passed'] is True and [x['layer'] for x in r['rows']] == list(H.LAYERS),
               'all192 independent actual frame joins, no winning-frame filter')
        index = H.obj(r['index'])
        H.need(index['original_raw'] == receipts[rank]['raw'] and index['rank'] == rank and
               index['manifest'] == m['replay_manifest'], 'actual result/index/input chain')
        H.checked(index['blob'])
        for row in r['rows']:
            H.need([x['layout'] for x in row['layouts']] == list(H.LAYOUTS) and
                   all(x['passed'] is True and x['metrics']['passed'] is True and
                       x['actual_inputs_bitwise_unchanged'] is True and
                       x['actual_original_and_candidate_bytes_verified'] is True for x in row['layouts']),
                   'both independent layouts passed every original gate')
    return replay, receipts, prior_admission


def gate(H, m):
    replay, receipts, prior = successful_replay(H, m)
    H.need(set(m['runtime_sources']) == {'triton_jit', 'triton_compiled', 'ascend_compiler'},
           'exact installed source evidence for JIT/cache/binary APIs')
    for r in m['runtime_sources'].values():
        H.checked(r)
    expected_hashes = dict(triton_jit='8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad',
        triton_compiled='4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b',
        ascend_compiler='253bdb0d9bf2d092c8c1ae40cc610b2d00c534b127f9d258e9e8e1a221934002')
    H.need(all(m['runtime_sources'][k]['sha256'] == v for k, v in expected_hashes.items()),
           'exact inspected installed source versions, no assumed runtime API')
    admission = H.obj(m['admission'])
    H.need(admission['schema'] == 'bole.gdn3-timing-owned-admission/v1' and
           admission['authority'] == 'MAIN' and admission['actual_source'] == replay['actual_source'] and
           admission['replay_result'] == m['replay_result'] and
           admission['independent_replay'] == m['replay_independent'] and
           admission['physical_devices'] == [4] and admission['logical_devices'] == [0] and
           admission['guest_device_path'] == '/dev/davinci0' and admission['allow_hf32'] is False and
           admission['image_digest'] == prior['image_digest'], 'new MAIN-owned same-image singleton timing admission')
    inspection = H.inspection(admission['controller_inspection'])
    H.need(inspection['Id'] == admission['owned_container_id'] and
           inspection['Image'] == admission['image_digest'] and inspection['State']['Running'] is True,
           'actual new timing container identity and running observation')
    devices = [d for d in inspection['HostConfig']['Devices']
               if Path(d['PathInContainer']).name.startswith('davinci') and
               Path(d['PathInContainer']).name[7:].isdigit()]
    H.need(len(devices) == 1 and devices[0]['PathOnHost'] == '/dev/davinci4' and
           devices[0]['PathInContainer'] == '/dev/davinci0', 'actual singleton physical4-to-guest0 mapping')
    H.owned_environment(admission)
    return replay, receipts, admission


class Output:
    def __init__(self, H, path):
        self.H = H; self.path = Path(path); self.used = 0; self.binaries = {}
        H.need(self.path.is_dir() and not any(self.path.iterdir()) and
               not any(p.is_symlink() for p in (self.path, *self.path.parents)),
               'fresh ordinary empty MAIN-owned timing output')

    def write(self, name, data):
        limit = (64 if name == 'FAILURE.json' else 63) * 2**20
        self.H.need(self.used + len(data) <= limit and
                    (name != 'FAILURE.json' or len(data) <= 2**20),
                    'aggregate timing artifacts cap64MiB including primary failure reserve')
        path = self.path / name
        with path.open('xb') as stream:
            stream.write(data)
        self.used += len(data)
        return self.H.ref(path)

    def json(self, name, value):
        return self.write(name, self.H.json_bytes(value))

    def binary(self, data):
        digest = hashlib.sha256(data).hexdigest()
        if digest not in self.binaries:
            self.binaries[digest] = self.write('KERNEL-' + digest + '.npubin', data)
        return self.binaries[digest]


def identity(x):
    return [x.untyped_storage().data_ptr(), x.data_ptr(), x.storage_offset(),
            list(x.shape), list(x.stride()), str(x.dtype), str(x.device)]


def cpu(x):
    return x.detach().cpu().contiguous()


def copied(values):
    return {k: cpu(v) for k, v in values.items()}


def input_guard(t, H, inputs, expected, before):
    H.need({k: identity(x) for k, x in inputs.items()} == before and
           all(H.bits(t, cpu(inputs[k]), expected[k]) for k in H.INPUT_KEYS),
           'actual input storage/bytes unchanged outside measured regions')
    return dict(unchanged=True, identities=before,
                hashes={k: H.tensor_hash(t, expected[k]) for k in H.INPUT_KEYS})


def check_outputs(t, H, I, values, truth, reference, input_storages):
    H.need(set(values) == set(KEYS) and all(x.dtype == t.float32 and
           x.device.type == 'npu' and x.untyped_storage().data_ptr() not in input_storages
           for x in values.values()), 'private actual FP32 output/factors/one selected state')
    actual = copied(values)
    metrics = {k: I.old112(t, actual[k], truth[k]) for k in KEYS}
    comparison = {k: I.old112(t, actual[k], reference[k]) for k in KEYS}
    return actual, dict(literal=metrics, original_device=comparison,
                        passed=all(x['passed'] for x in (*metrics.values(), *comparison.values())),
                        hashes={k: H.tensor_hash(t, actual[k]) for k in KEYS})


def cache_values(jit):
    return tuple(jit.cache.get(0, {}).values())


def backend_source(H, C, m, backend):
    # Triton loads this Python module under a dynamic name without registering
    # that name in sys.modules. inspect.getsourcefile(class) then calls it a
    # built-in class. Python functions retain their actual code filenames.
    cls = type(backend)
    H.need(cls.__name__ == 'AscendBackend', 'actual Ascend backend class')
    for name in ('__init__', 'parse_options', 'pack_metadata', 'add_stages'):
        method = vars(cls).get(name)
        H.need(inspect.isfunction(method) and
               method.__qualname__ == 'AscendBackend.' + name and
               method.__module__ == cls.__module__ and
               C.ref(inspect.getsourcefile(method)) == m['runtime_sources']['ascend_compiler'],
               'actual installed Ascend compiler method source ' + name)


def binary_proof(H, C, m, jit, handle, output):
    H.need(C.ref(inspect.getsourcefile(type(jit))) == m['runtime_sources']['triton_jit'] and
           C.ref(inspect.getsourcefile(type(handle))) == m['runtime_sources']['triton_compiled'],
           'actual installed classes match copied primary JIT/CompiledKernel sources')
    H.need(handle.src.fn is jit and C.ref(inspect.getsourcefile(jit.fn)) ==
           m['_replay']['candidate']['kernels'] and jit.pre_run_hooks == [] and
           jit.launch_metadata is None and type(handle).launch_enter_hook is None and
           type(handle).launch_exit_hook is None and handle.metadata.target.backend == 'npu',
           'same actual private JIT source, target and uninstrumented compiled launch')
    backend = jit.make_backend(handle.metadata.target)
    backend_source(H, C, m, backend)
    data = handle.asm['npubin']
    H.need(type(data) is bytes and data == handle.kernel and len(data) > 0 and
           handle.module is not None and handle.function is not None,
           'actual loaded npubin bytes from the validated wrapper launch')
    H.need(all(type(v) in (str, int, float, bool, type(None)) for v in handle.src.constants.values()),
           'primitive actual compile constants')
    return dict(compiled_hash=handle.hash, name=handle.name, binary=output.binary(data),
                target=dict(backend=handle.metadata.target.backend,
                            arch=str(handle.metadata.target.arch), warp_size=handle.metadata.target.warp_size),
                signature=dict(handle.src.signature), constants=dict(handle.src.constants),
                loaded=True, source_bound=True, compiled_runner=True)


def measure(t, call, iterations):
    # Identical clock/synchronization/loop/result lifetime for both paths.
    # No oracle, finite, source, byte codec, equality or copy work is in here.
    t.npu.synchronize()
    start = time.perf_counter_ns()
    result = None
    for _ in range(iterations):
        result = call()
    t.npu.synchronize()
    elapsed = time.perf_counter_ns() - start
    return elapsed, result


def order(frame, pair):
    return ('original', 'candidate') if (frame + pair) % 2 == 0 else ('candidate', 'original')


def stats(samples, iterations):
    unit = [v / iterations for v in samples]
    return dict(count=len(samples), batch_iterations=iterations, mean_ns=statistics.mean(unit),
                median_ns=statistics.median(unit), minimum_ns=min(unit), maximum_ns=max(unit),
                outliers_removed=0)


def selected_terminal(t, H, raw):
    logits = raw['staged']['actual_target_logits']; tokens = raw['tree_context']['tokens']
    H.need(logits.dtype == t.float32 and logits.ndim == 2 and logits.shape[0] == 3 and
           bool(t.isfinite(logits).all()), 'actual finite r23 target logits before selection')
    choice = int(logits[0].argmax())
    terminal = 1 if choice == tokens[1] else 2 if choice == tokens[2] else 0
    path = [0] if terminal == 0 else [0, terminal]
    H.need(raw['staged']['decision']['terminal'] == terminal and
           raw['staged']['processed_nodes'] == path and
           raw['staged']['decision']['processed_nodes'] == path and
           raw['staged']['decision']['cancelled'] is False, 'actual selected terminal/path independently derived')
    return terminal, dict(policy='actual-r23-selected', target_root_argmax=choice,
                          tokens=tokens, terminal=terminal, processed_nodes=path)


def frame(t, H, C, I, K, O, candidate, paths, m, row, terminal, layout, number, output):
    expected = H.frame_inputs(t, row)
    inputs = {k: x.to(device='npu:0').contiguous() for k, x in expected.items()}
    if layout == 'column_strided':
        inputs['state'] = inputs['state'].transpose(-1, -2).contiguous().transpose(-1, -2)
    H.need(inputs['state'].stride()[-2:] == ((128, 1) if layout == 'contiguous' else (1, 128)),
           'actual qualified state layout')
    before = {k: identity(x) for k, x in inputs.items()}
    input_guard(t, H, inputs, expected, before)
    input_storages = {x.untyped_storage().data_ptr() for x in inputs.values()}
    ancestor = t.tensor([[False, False, False], [True, False, False], [True, False, False]],
                        dtype=t.bool, device='npu:0')
    inclusive = ancestor.float() + t.eye(3, dtype=t.float32, device='npu:0')
    full_truth = H.oracle_values(t, O, expected)
    truth = dict(O=full_truth['O'], P=full_truth['P'], U=full_truth['U'], S=full_truth['S%d' % terminal])
    original = paths.original_unit(t, K, inputs, ancestor, inclusive, terminal)
    t.npu.synchronize(); first_start = time.perf_counter_ns()
    original_values = original(); t.npu.synchronize()
    original_first_use_ns = time.perf_counter_ns() - first_start
    original_cpu = copied(original_values)
    _, original_checks = check_outputs(t, H, I, original_values, truth, original_cpu, input_storages)
    refs = dict(implementation=m['_replay']['candidate']['wrapper'],
                kernels=m['_replay']['candidate']['kernels'], reference=m['_replay']['references']['core112.py'])
    kernels = candidate._backend(C, refs)
    cached_before = [len(cache_values(kernels.forward_ou)), len(cache_values(kernels.selected_state))]
    t.npu.synchronize(); first_start = time.perf_counter_ns()
    q, k, v, beta, gamma, state = (inputs[n] for n in H.INPUT_KEYS)
    verified = candidate.execute_verify(t, q, k, v, beta, gamma, state, ancestor, 1,
                                        enabled=True, arm_verified=True, C=C, source_refs=refs, tile_v=32)
    selected = candidate.execute_commit(t, state, k, verified['factors'], terminal,
                                        enabled=True, arm_verified=True, C=C, source_refs=refs,
                                        tile_k=32, tile_v=32)
    t.npu.synchronize(); guarded_first_use_ns = time.perf_counter_ns() - first_start
    guarded = dict(O=verified['output'], P=verified['factors'][0], U=verified['factors'][1],
                   S=selected['selected_state'])
    guarded_cpu, guarded_checks = check_outputs(t, H, I, guarded, truth, original_cpu, input_storages)
    H.need(H.bits(t, guarded_cpu['P'], original_cpu['P']), 'guarded candidate P bitwise original device')
    H.need(original_checks['passed'] and guarded_checks['passed'],
           'standalone wrapper/original validation must pass before any bypass')
    wrapper_caches = (cache_values(kernels.forward_ou), cache_values(kernels.selected_state))
    cached_after = [len(v) for v in wrapper_caches]
    # Reproduce the exact installed JITFunction.run cache key before any probe
    # launch. A missing specialization FAILS instead of compiling a bypass.
    expected_handles = []
    def admit(jit, args, kwargs):
        options = dict(kwargs)
        options['debug'] = options.get('debug', False) or os.environ.get('TRITON_DEBUG', '0') == '1'
        _, signature, constants, _, excess = jit.binder(*args, **options)
        key = ''.join(signature) + str((constants, excess))
        handle = jit.cache.get(0, {}).get(key)
        prior = wrapper_caches[0] if jit is kernels.forward_ou else wrapper_caches[1]
        H.need(handle is not None and any(handle is v for v in prior),
               'exact probe specialization already compiled/validated by standalone wrapper')
        binary_proof(H, C, m, jit, handle, output)
        expected_handles.append(handle)
    # This normal JIT launch is UNTIMED and cannot take a compile path.
    probe, handles = paths.jit_probe(t, kernels, inputs, ancestor, terminal, admit)
    t.npu.synchronize()
    H.need(all(any(handle is v for v in prior) for handle, prior in zip(handles, wrapper_caches)),
           'untimed exact-operand probe reuses same compiled handles as standalone wrapper')
    H.need(all(a is b for a, b in zip(handles, expected_handles)), 'actual probe returned the admitted compiled handles')
    H.need(all(H.bits(t, cpu(probe[k]), guarded_cpu[k]) for k in KEYS),
           'actual untimed JIT probe bitwise matches standalone wrapper')
    proofs = [binary_proof(H, C, m, jit, handle, output) for jit, handle in
              zip((kernels.forward_ou, kernels.selected_state), handles)]
    compiled = paths.compiled_unit(t, handles[0][(12, 4)], handles[1][(12, 4, 4)],
                                   inputs, ancestor, terminal)
    compiled_values = compiled(); t.npu.synchronize()
    compiled_cpu, compiled_checks = check_outputs(t, H, I, compiled_values, truth, original_cpu, input_storages)
    H.need(all(H.bits(t, compiled_cpu[k], guarded_cpu[k]) for k in KEYS),
           'same loaded compiled binaries bitwise match guarded wrapper on these exact operands')
    H.need(original_checks['passed'] and guarded_checks['passed'] and compiled_checks['passed'],
           'unchanged original112 calibration gates before timing')
    input_guard(t, H, inputs, expected, before)
    calls = dict(original=original, candidate=compiled)
    iterations = CONFIG['batch_iterations']
    warmup_schedule = []
    for pair in range(CONFIG['warmup_pairs']):
        sequence = order(number, pair); warmup_schedule.append(list(sequence))
        for role in sequence:
            last = None
            for _ in range(iterations):
                last = calls[role]()
            t.npu.synchronize()
        del last
    # All correctness and copies are outside the measured phase.
    warm_original = original(); warm_candidate = compiled(); t.npu.synchronize()
    H.need(all(H.bits(t, cpu(warm_original[k]), original_cpu[k]) and
               H.bits(t, cpu(warm_candidate[k]), guarded_cpu[k]) for k in KEYS),
           'post-warmup identical actual outputs for both paths')
    input_guard(t, H, inputs, expected, before)
    samples = []; by_role = dict(original=[], candidate=[]); last_values = {}
    for pair in range(CONFIG['sample_pairs']):
        sequence = order(number, pair); durations = {}
        for role in sequence:
            durations[role], last_values[role] = measure(t, calls[role], iterations)
            by_role[role].append(durations[role])
        samples.append(dict(pair=pair, order=list(sequence), batch_elapsed_ns=durations))
    # Timing has ended. Prove fixed inputs/output/binary identity afterward.
    unchanged = input_guard(t, H, inputs, expected, before)
    post = {}
    for role, reference in (('original', original_cpu), ('candidate', guarded_cpu)):
        actual_cpu, checks = check_outputs(t, H, I, last_values[role], truth, original_cpu, input_storages)
        checks['bitwise_preflight'] = all(H.bits(t, actual_cpu[k], reference[k]) for k in KEYS)
        H.need(checks['passed'] and checks['bitwise_preflight'], 'post-timing actual output/source calibration')
        post[role] = checks
    for proof, jit, handle in zip(proofs, (kernels.forward_ou, kernels.selected_state), handles):
        H.need(binary_proof(H, C, m, jit, handle, output) == proof, 'same actual source/binary after timing')
    return dict(layout=layout, frame_number=number, terminal=terminal, input_guard=unchanged,
                calibration=dict(original=original_checks, guarded_candidate=guarded_checks,
                                 compiled_candidate=compiled_checks, post_timing=post),
                compile_or_first_use=dict(original_untimed_host_ns=original_first_use_ns,
                    candidate_guarded_compile_or_cache_load_host_ns=guarded_first_use_ns,
                    includes_wrapper_source_finite_topology_validation=True,
                    new_runtime_cache_entries=[b-a for a, b in zip(cached_before, cached_after)],
                    isolated_compiler_time_ns=None, disk_compile_vs_cache_hit_known=False,
                    all_first_compile_or_cache_loading_outside_samples=True),
                binaries=proofs, candidate_dispatch='validated cached CompiledKernel runners',
                computation='all-node O/P/U plus ONE actual selected state; Torch P/ratio/allocations per call',
                warmup_order=warmup_schedule, samples=samples,
                summary={role: stats(values, iterations) for role, values in by_role.items()},
                every_timed_iteration_output_checked=False,
                output_check_scope='preflight/JIT/compiled/warmup and final timed output per role',
                timing_complete=True, model_ready=False, E2E_measured=False, formal_success=False)


def aggregate(rows, H):
    result = {}
    for layout in H.LAYOUTS:
        frames = [x for rank in rows for layer in rank['rows'] for x in layer['layouts'] if x['layout'] == layout]
        H.need(len(frames) == 192, 'all192 frames included once per layout')
        a = sum(x['summary']['original']['mean_ns'] for x in frames)
        b = sum(x['summary']['candidate']['mean_ns'] for x in frames)
        result[layout] = dict(frames=192, original_sum_mean_unit_ns=a,
                              candidate_sum_mean_unit_ns=b, ratio_original_over_candidate=a/b,
                              excluded_frames=0, excluded_samples=0, component_scope_only=True)
    return result


def run(t, H, manifest_ref, m, output_path):
    replay, receipts, admission = gate(H, m)
    m = dict(m, _replay=replay)
    output = Output(H, output_path)
    try:
        H.need(os.environ.get('BOLE_GDN3_TIMING_ENABLE') == '1' and
               os.environ.get('BOLE_GDN3_TRITON_ENABLE') == '1', 'two explicit timing/candidate opt-ins')
        # This timing entry requires an ALREADY initialized MAIN-owned context.
        H.need(t.npu.is_initialized() and t.npu.current_device() == 0 and t.npu.device_count() == 1 and
               t.npu.matmul.allow_hf32 is False, 'existing MAIN-admitted logical0/common HF32-OFF')
        t.set_num_threads(1)
        C, I, K, O, candidate = H.sources(replay, with_candidate=True)
        paths = H.load_module(m['files']['timing_paths.py'], '_bole_actual_timing_paths')
        ranks = []; rank_refs = []; number = 0; common_owner = None; common_terminal = None
        for rank, receipt in enumerate(receipts):
            exported, raw = H.load_raw(t, receipt, replay)
            terminal, selection = selected_terminal(t, H, raw)
            if common_owner is None:
                common_owner, common_terminal = raw['request'], terminal
            H.need(raw['request'] == common_owner and terminal == common_terminal,
                   'all4 same actual request and selected terminal')
            rows = []
            for layer in H.LAYERS:
                layouts = []
                for layout in H.LAYOUTS:
                    layouts.append(frame(t, H, C, I, K, O, candidate, paths, m,
                                         raw['tree_context']['captures'][layer], terminal, layout, number, output))
                    number += 1
                rows.append(dict(layer=layer, layouts=layouts))
            report = dict(schema='bole.gdn3-warmed-host-device-rank/v1', rank=rank,
                          manifest=manifest_ref, original_receipt=replay['receipts'][rank]['receipt'],
                          original_raw=receipt['raw'], owner=raw['request'], selection=selection, rows=rows,
                          model_ready=False, E2E_measured=False, formal_success=False)
            rank_refs.append(output.json('TIMING-RANK-%d.json' % rank, report)); ranks.append(report)
            del exported, raw
        H.need(number == 384, 'complete192 frames/both layouts')
        result = dict(schema='bole.gdn3-warmed-host-device-result/v1', manifest=manifest_ref,
                      replay_independent=m['replay_independent'], replay_result=m['replay_result'],
                      replay_release=m['replay_release'], admission=m['admission'], configuration=CONFIG,
                      ranks=rank_refs, frames=192, frame_layouts=384,
                      clock='host perf_counter_ns; pre-sync outside/start; final NPU sync inside interval',
                      includes='Python dispatch, allocations, Torch P/ratio, actual compute and completion wait',
                      excludes='guards, H2D/D2H, source/binary checks, oracle, codec, first compile/cache load',
                      aggregate=aggregate(ranks, H), binaries=list(output.binaries.values()),
                      all_samples_retained=True, timing_complete=True,
                      every_timed_iteration_output_checked=False,
                      whole_model_qualified=False, model_ready=False, E2E_measured=False,
                      ten_percent_E2E_claim=False, formal_success=False, scheduler_committed=False,
                      persistent_cache_written=False)
        return output.json('TIMING-RESULT.json', result)
    except BaseException as error:
        try:
            output.json('FAILURE.json', dict(primary=repr(error)[:8192], traceback=traceback.format_exc()[-65536:],
                        manifest=manifest_ref, timing_complete=False, model_ready=False, formal_success=False))
        except BaseException as secondary:
            print(json.dumps(dict(primary=repr(error), failure_receipt_error=repr(secondary))), file=sys.stderr)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--execute', action='store_true'); p.add_argument('--manifest-ref'); p.add_argument('--output', type=Path)
    args = p.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, tensor_runtime_imported=False, NPU=False,
                              prepared_only=True, timing_complete=False, model_ready=False, formal_success=False)))
        return 0
    if not args.manifest_ref or args.output is None:
        p.error('--execute requires --manifest-ref and --output')
    if os.environ.get('BOLE_GDN3_TIMING_ENABLE') != '1' or os.environ.get('BOLE_GDN3_TRITON_ENABLE') != '1':
        p.error('explicit BOLE_GDN3_TIMING_ENABLE=1 and BOLE_GDN3_TRITON_ENABLE=1 required')
    manifest_ref = json.loads(args.manifest_ref)
    H, m = bootstrap(manifest_ref)
    gate(H, m)  # Whole successful chain and actual identity BEFORE tensor import.
    import torch
    import torch_npu
    del torch_npu
    # MAIN has already admitted/created the owner. Only its mapped logical0
    # context may be initialized here; no physical identifier is selected.
    H.need(torch.npu.device_count() == 1, 'already admitted singleton logical mapping')
    if not torch.npu.is_initialized():
        torch.npu.set_device(0)
    torch.npu.matmul.allow_hf32 = False
    result = run(torch, H, manifest_ref, m, args.output)
    print(json.dumps(dict(result=result, model_ready=False, formal_success=False), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
