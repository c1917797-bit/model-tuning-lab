#!/usr/bin/env python3
"""Restricted native-FP32 compressed NPU gate; not serving/performance/quality.

Parent owns execution. Two independent state trajectories, no resynchronizing.
--audit-only checks frozen CPU fixtures, never loads libraries or touches NPU.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
import torch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from independent_oracle import (OracleLayout, ValueMajorPacked, errors,
    pack_value_major, restore_state, transform_state, unpack_value_major)
from native_compressed_golden import step as native_step
from native_call_contract import cpu_signature_checks, validate_native_schema

SEED, STEPS = 260827513, 160
LIMITS = {'state_selected_max_head_relative_l2': 1e-5,
          'output_max_head_relative_l2': 0.00303}
GDN_SHA = 'd6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact(a, b):
    a, b = a.detach().cpu().contiguous(), b.detach().cpu().contiguous()
    return a.shape == b.shape and a.dtype == b.dtype and torch.equal(
        a.view(torch.uint8), b.view(torch.uint8))


def safe(value):
    if isinstance(value, dict): return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value): return {'nonfinite': repr(value)}
    return value


def pd(p):
    return {n: getattr(p, n) for n in ('high', 'low', 'scales')}


def ld(layout):
    return {n: getattr(layout, n) for n in ('c', 'pv', 'pk', 'khi', 'group')}


def layouts(batch, variant):
    generator = torch.Generator().manual_seed(SEED+10000*variant+batch)
    c = torch.ones(12, 128, dtype=torch.float32)
    if variant:
        c = torch.pow(2.0, torch.randint(-2, 3, (12, 128), generator=generator).float())
    pv = torch.stack([torch.randperm(128, generator=generator) for _ in range(12)]).int()
    pk = torch.stack([torch.randperm(128, generator=generator) for _ in range(12)]).int()
    layout = OracleLayout(c, pv, pk)
    original = torch.randn(batch+3, 12, 128, 128, generator=generator)*0.005
    return layout, pack_value_major(transform_state(original, layout), layout), generator


def turn(batch, slot_count, index, generator):
    q = torch.nn.functional.normalize(torch.randn(batch, 4, 128, generator=generator), dim=-1).bfloat16()
    k = torch.nn.functional.normalize(torch.randn(batch, 4, 128, generator=generator), dim=-1).bfloat16()
    # All integers in [-256,256] are exactly BF16, then scale by 2^-10.
    # This freezes a realistic bounded V fixture while avoiding unproved cast
    # underflow in power2-SR native input; not a general calibration distribution.
    v = (torch.randint(-256, 257, (batch, 12, 128), generator=generator).float()/1024).bfloat16()
    g = -(0.002+0.18*torch.rand(batch, 12, generator=generator))
    beta = torch.sigmoid(torch.randn(batch, 12, generator=generator)).bfloat16()
    ids = (torch.arange(batch, dtype=torch.int32)+index) % slot_count
    return q, k, v, g, beta, ids


def cast_audit(layout, values):
    vt = values.float()/layout.c[None]
    b = vt.bfloat16()
    return bool(torch.isfinite(b).all()) and exact(vt, b.float())


def loaded_libraries(operator_path):
    names = {str(operator_path.resolve())}
    for line in Path('/proc/self/maps').read_text().splitlines():
        parts = line.split()
        if not parts: continue
        name = parts[-1]
        if name.startswith('/') and any(x in name for x in (
                'libcust_opapi', 'libopapi', 'vllm_ascend', 'libtorch_npu', 'qwen36_damp')):
            names.add(name)
    return [{'path': n, 'sha256': sha(n)} for n in sorted(names) if Path(n).is_file()]


def device_manifest(path):
    proof = json.loads(path.read_text())
    if not isinstance(proof, dict): raise ValueError('device-proof must be a JSON object')
    physical = proof.get('physical_npu_ids', [])
    mapping = proof.get('logical_to_physical', {})
    observed = proof.get('observed_at_unix_ns', 0)
    if (not physical or any(x not in (4, 5, 6, 7) for x in physical) or
        mapping.get('0') != 4 or any(x not in physical for x in mapping.values()) or
        proof.get('privileged') is not False or
        proof.get('exclusive_resource_check_passed') is not True or
        not 0 <= time.time_ns()-observed <= 1800*10**9):
        raise ValueError('fresh nonprivileged physical4->logical0/exclusive-resource proof required')
    return {'path': str(path.resolve()), 'sha256': sha(path), 'manifest': proof,
            'authority': 'external parent observations; script validates fields, not host truth'}


def schema_check():
    decode = torch.ops.qwen36_damp.decode.default._schema
    prepare = torch.ops.qwen36_damp.prepare.default._schema
    writes = [i for i, a in enumerate(decode.arguments) if a.alias_info and a.alias_info.is_write]
    if len(decode.arguments) != 14 or writes != [5, 6, 7] or any(x.alias_info for x in decode.returns):
        raise RuntimeError('production decode schema/aliases differ')
    if len(prepare.arguments) != 6 or len(prepare.returns) != 0:
        raise RuntimeError('production prepare schema differs')
    return {'decode': str(decode), 'prepare': str(prepare)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--audit-only', action='store_true')
    parser.add_argument('--steps', type=int, default=STEPS)
    parser.add_argument('--operator-library', type=Path)
    parser.add_argument('--operator-sha256')
    parser.add_argument('--device-proof', type=Path)
    parser.add_argument('--native-gdn-source', type=Path,
                        default=Path('/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py'))
    parser.add_argument('--native-gdn-source-sha256', default=GDN_SHA)
    parser.add_argument('--native-source-manifest', type=Path,
                        help='external parent reference/build/runtime provenance JSON')
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() or out == REPO or REPO in out.parents:
        parser.error('require a NEW output root outside repository')
    if not 1 <= args.steps <= STEPS: parser.error('steps must be [1,160]; shorter = smoke only')
    if not args.audit_only:
        if os.environ.get('ASCEND_RT_VISIBLE_DEVICES') != '0': parser.error('requires logical0 only')
        for n in ('operator_library', 'device_proof', 'native_source_manifest'):
            p = getattr(args, n)
            if p is None or not p.is_file(): parser.error('requires existing --'+n.replace('_', '-'))
        if not args.operator_sha256: parser.error('requires frozen --operator-sha256')
    out.mkdir(parents=True)
    report = {'schema': 'damp-restricted-native-compressed-golden/v1', 'status': 'running',
              'artifact_root': str(out), 'created_ns': time.time_ns(), 'seed': SEED,
              'steps': args.steps, 'matrix_class': 'full-160' if args.steps == STEPS else 'smoke-only',
              'mode': 'cpu-fixture-audit-only' if args.audit_only else 'npu-restricted-native-golden',
              'limits': LIMITS, 'checks': [], 'cases': [],
              'source_hashes': {n: sha(HERE/n) for n in (
                  'restricted_native_golden_gate.py', 'native_compressed_golden.py', 'independent_oracle.py',
                  'native_call_contract.py', 'test_native_call_contract.py')},
              'versions': {'torch': torch.__version__},
              'scope': 'identity/power2-SR only, eager B1/B16 single-token native NK12 golden; '
                       'NOT arbitrary SR, graph, batchmix, calibrated model, serving, performance or task accuracy',
              'precision_boundaries': ['native FP32 update -> BF16 reordered readout',
                                       'inverse-Pv/power2 SR restore -> BF16 original readout'],
              'required_npu_format_id': 2,
              'feedback': 'independent golden and candidate arenas, no step resynchronization'}
    def save():
        (out/'report.json').write_text(json.dumps(safe(report), indent=2, allow_nan=False)+'\n')
    def retain(fixture):
        path = out/'first_failure.pt'
        if path.exists(): return
        def cpu(v):
            if isinstance(v, torch.Tensor): return v.detach().cpu().clone()
            if isinstance(v, dict): return {k: cpu(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)): return [cpu(x) for x in v]
            return v
        try:
            torch.save(cpu(fixture), path)
            report['first_failure_fixture'] = {'path': str(path), 'sha256': sha(path)}
        except BaseException as error: report['fixture_save_error'] = repr(error)
    def check(name, passed, data=None):
        report['checks'].append({'name': name, 'passed': bool(passed), **(data or {})}); save()
        if not passed: raise AssertionError(name)
    fixture = {'stage': 'preflight'}
    save()
    try:
        torch.set_num_threads(1)
        report['cpu_signature_guard'] = cpu_signature_checks(HERE)
        check('cpu_native_call_signature_guard', True)
        # Fixed fixture audit is valid without any NPU/runtime/library imports.
        audited = 0
        for b in (1, 16):
            for variant in (0, 1):
                layout, initial, generator = layouts(b, variant)
                for index in range(args.steps):
                    values = turn(b, b+3, index, generator)[2]
                    fixture = {'stage': 'fixture_cast_audit', 'batch': b, 'variant': variant,
                               'step': index+1, 'layout': ld(layout), 'v': values}
                    check('fixture_cast_b%d_sr%d_step%d' % (b, variant, index+1),
                          cast_audit(layout, values)); audited += 1
        report['fixture_audit'] = {'turns': audited, 'V/SR_BF16_cast_exact': True,
                                   'V_source': 'frozen integer[-256,256]*2^-10',
                                   'SR_exponents': [-2, 2]}
        if args.audit_only:
            report.update(status='cpu_fixture_audit_pass', completed_ns=time.time_ns()); save()
            print(json.dumps({'status': report['status'], 'report': str(out/'report.json')})); return
        fixture = {'stage': 'runtime_loader_preflight', 'operator_library': str(args.operator_library),
                   'expected_operator_sha256': args.operator_sha256,
                   'native_source_manifest': str(args.native_source_manifest)}
        report['device_proof'] = device_manifest(args.device_proof)
        if sha(args.operator_library) != args.operator_sha256:
            raise RuntimeError('candidate library identity differs from preregistered hash')
        if sha(args.native_gdn_source) != args.native_gdn_source_sha256:
            raise RuntimeError('deployed GDN source identity differs')
        report['native_gdn_source'] = {'path': str(args.native_gdn_source),
                                     'sha256': sha(args.native_gdn_source)}
        report['native_source_manifest'] = {'path': str(args.native_source_manifest),
            'sha256': sha(args.native_source_manifest),
            'content': json.loads(args.native_source_manifest.read_text()),
            'authority': 'external parent source/build identity, not loaded-library proof'}
        report['operator_library'] = {'path': str(args.operator_library.resolve()),
                                      'sha256': sha(args.operator_library)}
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op(): raise RuntimeError('native operator bootstrap unavailable')
        torch.npu.set_device(0)
        torch.ops.load_library(str(args.operator_library.resolve()))
        report['schemas'] = schema_check()
        native = torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        report['native_schema'] = str(native.default._schema)
        report['native_call_contract'] = validate_native_schema(native.default._schema)
        check('actual_native_schema_names_and_keyword_only', True, report['native_call_contract'])
        report['versions']['torch_npu'] = torch_npu.__version__
        report['cann_version_files'] = []
        for path in (Path('/usr/local/Ascend/ascend-toolkit/latest/version.cfg'),
                     Path('/usr/local/Ascend/ascend-toolkit/latest/opp/version.info')):
            if path.is_file():
                report['cann_version_files'].append({'path': str(path), 'sha256': sha(path),
                    'content': path.read_text(errors='replace')[:4096]})
        report['loaded_libraries_before'] = loaded_libraries(args.operator_library); save()
        device = 'npu:0'
        def nd(x):
            t = torch_npu.npu_format_cast(x.to(device).contiguous(), 2)
            if torch_npu.get_npu_format(t) != 2: raise RuntimeError('format must be ND(2)')
            return t
        def candidate_setup(initial, layout, b):
            arena = [nd(x) for x in (initial.high, initial.low, initial.scales)]
            plans = [nd(x.int()) for x in (layout.pk, layout.pv, layout.pv.argsort(1))]
            sr, lengths = nd(layout.c), nd(torch.tensor([0]+[1]*b, dtype=torch.int32))
            q0 = nd(torch.zeros(b, 4, 128, dtype=torch.bfloat16))
            torch.ops.qwen36_damp.prepare(q0, arena[0], *plans, sr)
            torch.npu.synchronize()
            return arena, plans, sr, lengths
        # Explicit HQ12 smoke first: no low-region quantization ambiguity.
        for b in (1, 16):
            layout = OracleLayout(torch.ones(12, 128), torch.arange(128).repeat(12, 1).int(),
                                  torch.arange(128).repeat(12, 1).int())
            initial = pack_value_major(torch.zeros(b+3, 12, 128, 128), layout)
            q = torch.zeros(b, 4, 128, dtype=torch.bfloat16); q[..., 3] = 1
            k = q.clone()
            v = ((torch.arange(b*12*128).reshape(b, 12, 128) % 16)-8).float().div(64).bfloat16()
            g, beta = torch.zeros(b, 12), torch.full((b, 12), 0.5, dtype=torch.bfloat16)
            ids = torch.arange(b, dtype=torch.int32)
            fixture = {'stage': 'native_hq12_dyadic', 'batch': b, 'layout': ld(layout),
                       'initial': pd(initial), 'q': q, 'k': k, 'v': v, 'g': g, 'beta': beta, 'indices': ids}
            evidence = native_step(initial, layout, q, k, v, g, beta, ids, native, device)
            expected_fp32 = torch.zeros(b, 12, 128, 128); expected_fp32[..., 3] = v.float()*0.5
            expected_output = (v.float()*0.5*torch.tensor(128**-0.5, dtype=torch.float32)).bfloat16()
            fixture['native_evidence'] = {n: x for n, x in evidence.items() if n != 'packed'}
            check('native_hq12_dyadic_exact_b%d' % b,
                  exact(evidence['native_updated_selected_fp32'], expected_fp32) and
                  exact(evidence['original_output_bf16'], expected_output),
                  {'native_query_shape': [b, 12, 128], 'native_state_dtype': 'FP32'})
            arena, plans, sr, lengths = candidate_setup(initial, layout, b)
            actual = torch.ops.qwen36_damp.decode(*[nd(x) for x in (q, k, v, g, beta)],
                                                 *arena, *plans, sr, lengths, nd(ids))
            torch.npu.synchronize()
            fixture['actual_output'] = actual; fixture['actual_after'] = dict(zip(('high', 'low', 'scales'), arena))
            check('production_dyadic_exact_b%d' % b, exact(actual, expected_output) and
                  all(exact(a, getattr(evidence['packed'], n)) for a, n in
                      zip(arena, ('high', 'low', 'scales'))))
        report['loaded_libraries_after_hq12_smoke'] = loaded_libraries(args.operator_library); save()
        # Separate OWN feedback arenas, identical initial packed state only.
        for b in (1, 16):
            for variant in (0, 1):
                layout, golden, generator = layouts(b, variant)
                arena, plans, sr, lengths = candidate_setup(golden, layout, b)
                pointers = [x.data_ptr() for x in arena]
                static = plans+[sr, lengths]; static_before = [x.cpu().clone() for x in static]
                case = {'batch': b, 'slots': b+3, 'SR': 'power2' if variant else 'identity',
                        'permutations': 'random independent per-Hv', 'status': 'running', 'steps': []}
                report['cases'].append(case); save()
                for index in range(args.steps):
                    q, k, v, g, beta, ids = turn(b, b+3, index, generator)
                    actual_before = ValueMajorPacked(*[x.cpu().clone() for x in arena])
                    golden_before = golden.clone()
                    fixture = {'stage': 'closed_loop', 'batch': b, 'variant': variant, 'step': index+1,
                        'layout': ld(layout), 'q': q, 'k': k, 'v': v, 'g': g, 'beta': beta,
                        'indices': ids, 'golden_before': pd(golden_before), 'actual_before': pd(actual_before)}
                    evidence = native_step(golden, layout, q, k, v, g, beta, ids, native, device)
                    golden = evidence['packed']
                    inputs = [nd(x) for x in (q, k, v, g, beta)]; input_before = [x.cpu().clone() for x in inputs]
                    indices = nd(ids)
                    output = torch.ops.qwen36_damp.decode(*inputs, *arena, *plans, sr, lengths, indices)
                    torch.npu.synchronize()
                    if output.shape != (b, 12, 128) or output.dtype != torch.bfloat16:
                        raise RuntimeError('production output ABI mismatch')
                    actual = ValueMajorPacked(*[x.cpu().clone() for x in arena])
                    fixture.update(golden_after=pd(golden), actual_after=pd(actual), actual_output=output,
                                   native_evidence={n: x for n, x in evidence.items() if n != 'packed'})
                    untouched = [s for s in range(b+3) if s not in ids.tolist()]
                    state_metric = errors(restore_state(unpack_value_major(actual, layout), layout).index_select(0, ids.long()),
                        restore_state(unpack_value_major(golden, layout), layout).index_select(0, ids.long()))
                    output_metric = errors(output, evidence['original_output_bf16'])
                    guards = {'candidate_untouched_exact': all(exact(getattr(actual, n)[untouched],
                         getattr(actual_before, n)[untouched]) for n in ('high', 'low', 'scales')),
                        'golden_untouched_exact': all(exact(getattr(golden, n)[untouched],
                         getattr(golden_before, n)[untouched]) for n in ('high', 'low', 'scales')),
                        'candidate_storage_stable': pointers == [x.data_ptr() for x in arena],
                        'static_inputs_exact': all(exact(a, z) for a, z in zip(static, static_before)),
                        'turn_inputs_exact': all(exact(a, z) for a, z in zip(inputs, input_before)),
                        'output_nonalias': all(output.data_ptr() != x.data_ptr() for x in arena+inputs+static+[indices]),
                        'output_format_ND': torch_npu.get_npu_format(output) == 2,
                        'indices_exact': exact(indices, ids), 'native_V_cast_exact': evidence['value_cast_exact'],
                        'native_restore_cast_exact': evidence['restored_cast_exact']}
                    passed = all(guards.values()) and state_metric['finite'] and output_metric['finite'] and (
                        state_metric['max_head_relative_l2'] <= LIMITS['state_selected_max_head_relative_l2'] and
                        output_metric['max_head_relative_l2'] <= LIMITS['output_max_head_relative_l2'])
                    case['steps'].append({'step': index+1, 'indices': ids.tolist(), 'passed': passed,
                        'state': state_metric, 'output': output_metric, 'guards': guards,
                        'packed_bitwise_diagnostic': {n: exact(getattr(actual, n), getattr(golden, n))
                                                     for n in ('high', 'low', 'scales')}}); save()
                    if not passed:
                        case.update(status='failed', failed_step=index+1)
                        raise AssertionError('restricted native closed-loop parity/guard failed')
                case['status'] = 'passed'; save()
        report['status'] = 'restricted_native_numerical_pass' if args.steps == STEPS else 'restricted_native_smoke_pass'
    except BaseException as error:
        if 'case' in locals() and case.get('status') == 'running':
            case.update(status='failed', failed_step=index+1, error=repr(error))
        report.update(status='failed', error=repr(error), error_type=type(error).__name__, traceback=traceback.format_exc())
        retain(fixture)
        raise
    finally:
        report['completed_ns'] = time.time_ns()
        if not args.audit_only and args.operator_library is not None:
            try: report['loaded_libraries_final'] = loaded_libraries(args.operator_library)
            except BaseException as error: report['library_snapshot_error'] = repr(error)
        try: save()
        except BaseException as error: print('secondary report-save error: '+repr(error), file=sys.stderr)
    print(json.dumps({'status': report['status'], 'report': str(out/'report.json')}))


if __name__ == '__main__':
    main()
