"""CPU-only extension of immutable120R2. Diagnosis, never qualification."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

P = Path(__file__).resolve().parent


def need(ok, why):
    if not ok:
        raise ValueError(why)


def ref(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def checked(item):
    need(type(item) is dict and set(item) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    path = Path(item['path'])
    need(path.is_absolute() and path.is_file() and not any(q.is_symlink() for q in (path, *path.parents)), 'ordinary absolute evidence/source')
    need(ref(path) == item, 'exact evidence/source bytes')
    return path


def obj(item):
    return json.loads(checked(item).read_bytes())


def load(item, name):
    spec = importlib.util.spec_from_file_location(name, checked(item))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@contextlib.contextmanager
def original_consumer(manifest):
    """Pin the public import used by original consume.py; restore caller state."""
    prior = sys.modules.get('guest_core')
    guest = load(manifest['files']['guest_core.py'], '_analysis120_exact_guest')
    oldpath = list(sys.path)
    try:
        sys.modules['guest_core'] = guest
        consumer = load(manifest['files']['consume.py'], '_analysis120_exact_consumer')
        need(consumer.G is guest, 'source-bound original consumer import')
        yield guest, consumer
    finally:
        sys.path[:] = oldpath
        if prior is None:
            sys.modules.pop('guest_core', None)
        else:
            sys.modules['guest_core'] = prior


def norm_metric(torch, actual, expected):
    need(actual.shape == expected.shape and bool(torch.isfinite(actual).all() and torch.isfinite(expected).all()), 'finite equal-shape diagnostic')
    delta = actual.double() - expected.double()
    return dict(relative_l2=float(delta.norm()) / max(float(expected.double().norm()), 1e-30), max_abs=float(delta.abs().max()), changed_values=int((actual.double() != expected.double()).sum()))


def round_cells(torch, actual, inverse, direct):
    """Reference is CPU64 inverse, not an exact-real inverse theorem."""
    need(actual.dtype == torch.bfloat16 and inverse.dtype == torch.float64 and actual.shape == inverse.shape, 'actual BF16 versus independent CPU64 inverse')
    nearest = direct.round_bf16(torch, inverse)
    need(bool(torch.isfinite(nearest).all()), 'finite direct BF16 reference')
    bits = nearest.contiguous().view(torch.int16).to(torch.int32) & 65535
    abits = actual.contiguous().view(torch.int16).to(torch.int32) & 65535
    values = nearest.double()
    lower = torch.where(values < 0, bits + 1, bits - 1)
    upper = torch.where(values < 0, bits - 1, bits + 1)
    lower = torch.where(values == 0, torch.full_like(lower, 0x8001), lower)
    upper = torch.where(values == 0, torch.full_like(upper, 1), upper)
    lo = (lower.to(torch.int16).view(torch.bfloat16).double() + values) * .5
    hi = (upper.to(torch.int16).view(torch.bfloat16).double() + values) * .5
    finite_bounds = torch.isfinite(lo) & torch.isfinite(hi)
    margin = torch.minimum((inverse - lo).abs(), (hi - inverse).abs())
    ordered = lambda x: torch.where((x & 32768) != 0, 32768 - (x & 32767), 32768 + x)
    ulp = (ordered(abits) - ordered(bits)).abs()
    different = abits != bits
    scores = torch.where(different, ulp, torch.full_like(ulp, -1)).flatten()
    selected = scores.argsort(descending=True)[:min(4, int(different.sum()))].tolist()
    examples = []
    for flat in selected:
        row, col = divmod(flat, actual.shape[-1])
        item = dict(row=row, col=col, actual_bits=int(abits[row, col]), direct_RNE_bits=int(bits[row, col]), ULP_distance=int(ulp[row, col]), inverse_CPU64=float(inverse[row, col]), actual=float(actual[row, col]), reference=float(values[row, col]))
        if bool(finite_bounds[row, col]):
            item.update(lower_midpoint=float(lo[row, col]), upper_midpoint=float(hi[row, col]), margin=float(margin[row, col]))
        else:
            item['cell_boundary_unbounded'] = True
        examples.append(item)
    nonzero = finite_bounds & (inverse != 0)
    return dict(changed_bitpatterns=int(different.sum()), signed_zero_only=int((different & (actual == 0) & (nearest == 0)).sum()), max_ULP_distance=int(ulp.max()), exact_midpoints=int(((margin == 0) & finite_bounds).sum()), nonzero_minimum_midpoint_margin=float(margin[nonzero].min()) if bool(nonzero.any()) else None, operational_torch_cast_vs_direct_changed=int((inverse.to(torch.bfloat16).view(torch.int16) != nearest.view(torch.int16)).sum()), examples=examples, reference_is_CPU64_not_exact_real=True)


def residual(torch, A, B):
    eye = torch.eye(A.shape[-1], dtype=torch.float64)
    M = eye + A.double()
    delta = M @ B.double() - eye
    return dict(max_abs=float(delta.abs().max()), frobenius=float(delta.norm()), backward_scaled=float(delta.norm()) / max(float(M.norm() * B.double().norm() + eye.norm()), 1e-30))


def vector_decomposition(torch, rows, working):
    C, N, I, W = (rows['saved_candidate']['state'].double(), rows['native']['state'].double(), rows['cpu64_cast']['state'].double(), working['state'].double())
    parts = [C - N, N - I, I - W]
    den = max(float(W.norm()), 1e-30)
    total = C - W
    return dict(identity='C-W=(C-N)+(N-I)+(I-W); norms do not add', common_denominator='norm(unchanged working state)', total_relative_l2=float(total.norm()) / den, component_relative_l2=dict(zip(('C-N', 'N-I', 'I-W'), (float(p.norm()) / den for p in parts))), pairwise_inner_products=[[float((a * b).sum()) for b in parts] for a in parts], squared_norm_identity_residual=float(total.square().sum() - sum((a * b).sum() for a in parts for b in parts)), vector_closure_max_abs=float((sum(parts) - total).abs().max()), native_truth_assumed=False)


def classify(registered):
    state = {name: values['state']['pass'] for name, values in registered.items()}
    if state == dict(saved_candidate=False, native=False, cpu64_cast=True):
        return 'ONLY_CPU64CAST_RECOVERS_WORKING_STATE'
    if not state['native'] and not state['cpu64_cast']:
        return 'NATIVE_AND_CPU64CAST_ALSO_FAIL_WORKING_STATE_REFERENCE_UNRESOLVED'
    if not state['saved_candidate'] and state['native'] and state['cpu64_cast']:
        return 'CANDIDATE_SPECIFIC_STATE_DIFFERENCE'
    return 'OTHER_MIXED_STATE_RESULT_READ_ALL_OUTPUT_AND_STATE_METRICS'


def analyze_case(torch, G, m, case, item, raw, base, direct):
    G.RAW = case['raw']; G.CASE = case
    x = G.validate_frame(torch, raw)
    boundary = G.load(m['original_working_oracle'], '_analysis120_working')
    working = boundary.evaluate(torch, x)
    O = G.load(m['original_metrics'], '_analysis120_metrics')
    inverse, inverse_checks = O.fp64_reference(torch, raw['solve']['A'], x['cu_seqlens'].tolist())
    rows = {r['arm']: torch.load(G.checked(r['raw']), map_location='cpu', weights_only=True) for r in item['result']['rows']}
    tiles = []
    for chunk, work in enumerate(working['trace']):
        need(work['start'] == chunk * 64 and work['stop'] == (chunk + 1) * 64 and work['segment'] == 0, 'complete actual2K chunk coverage')
        z = slice(chunk * 64, (chunk + 1) * 64)
        aa = rows['saved_candidate']['A'][0, z].permute(1, 0, 2).double()
        inv = inverse[0, z].permute(1, 0, 2)
        for head in range(12):
            byarm = {}
            for name, row in rows.items():
                B = row['B'][0, z, head]
                byarm[name] = dict(actual_A_inverse_residual=residual(torch, aa[head], B), versus_actual_A_inverse=norm_metric(torch, B, inv[head]), versus_working_B=norm_metric(torch, B, work['B'][head]), cast_cell=round_cells(torch, B, inv[head], direct))
            tiles.append(dict(chunk=chunk, head=head, actual_A_vs_working_A=norm_metric(torch, aa[head], work['A32'][head]), actual_G_vs_working_cumsum=norm_metric(torch, rows['saved_candidate']['G'][0, z, head], work['g_cumsum'][head]), actual_inverse_vs_working_inverse=norm_metric(torch, inv[head], work['inverse_FP64'][head]), arms=byarm))
    checkpoints = {}
    for name, row in rows.items():
        chain = []
        for chunk, work in enumerate(working['trace']):
            z = slice(chunk * 64, (chunk + 1) * 64)
            chain.append(dict(chunk=chunk, W=norm_metric(torch, row['W'][0, z].transpose(0, 1), work['W']), U=norm_metric(torch, row['U'][0, z].transpose(0, 1), work['U']), Hentry=norm_metric(torch, row['Hentry'].reshape(1, 12, 32, 128, 128)[0, :, chunk], work['Hstart']), Vnew=norm_metric(torch, row['Vnew'].reshape(1, 12, 2048, 128)[0, :, z], work['vnew'])))
        checkpoints[name] = chain
    return dict(case=case, classification=classify(base['registered_working']), registered_working=base['registered_working'], actual_pair_first_difference={k: v['first_differing_chunk'] for k, v in base['pairs'].items()}, actual_pair_final_state={k: v['final_state'] for k, v in base['pairs'].items()}, actual_A_independent_CPU64_inverse_checks=inverse_checks, tiles=tiles, actual_vs_working_checkpoints=checkpoints, state_vector_decomposition=vector_decomposition(torch, rows, working), intermediate_FP32_Hend_available=False, qualification=False)


def repeat_comparison(torch, G, stage, repeat):
    need(repeat['source'] == stage['source'] and repeat['primary'] is None and repeat['NPU'] is True, 'actual same-source complete repeat stage')
    values = []
    for left, right in zip(stage['result']['cases'], repeat['result']['cases']):
        need(left['case_id'] == right['case_id'] and left['raw'] == right['raw'], 'repeat exact original case/input')
        arms = {}
        for a, b in zip(left['result']['rows'], right['result']['rows']):
            need(a['arm'] == b['arm'], 'same repeat arm order')
            A = torch.load(G.checked(a['raw']), map_location='cpu', weights_only=True)
            B = torch.load(G.checked(b['raw']), map_location='cpu', weights_only=True)
            arms[a['arm']] = {k: dict(bitwise=G.equal(torch, A[k], B[k]), error=norm_metric(torch, A[k], B[k])) for k in ('A', 'G', 'B', 'W', 'U', 'Hentry', 'Vnew', 'output', 'state')}
        values.append(dict(case_id=left['case_id'], arms=arms))
    return dict(actual_repeat_available=True, cases=values, repeat_does_not_prove_oracle_validity=True)


def consume(torch, G, C, m, stage, direct, repeat=None):
    # Execute original full source/case/anchor consumer first; no partial repair.
    original = C.consume(torch, m, stage)
    model, _, _, _ = G.readset(m)
    reports = []
    for case, item, old in zip(m['cases'], stage['result']['cases'], original['cases']):
        reports.append(analyze_case(torch, G, m, case, item, G.frame(torch, model, case), old['attribution'], direct))
    repetition = dict(actual_repeat_available=False, reference_validity_unresolved=True)
    if repeat is not None:
        C.consume(torch, m, repeat)
        repetition = repeat_comparison(torch, G, stage, repeat)
    return dict(schema='mxr.prefill-source-and-round-cell-analysis/v120-analysis1', cases=reports, original_consumer=original, repeat=repetition, NPU=False, qualification=False, performance=False, task=False, reference_validity_resolved=False, required_before_reference_contract_change=['same-source actual native repeats with identical original inputs and common precision', 'independent source-derived per-stage rounding/exp/reduction boundary verification', 'separate actualA versus reconstructedA and downstream accumulated state error vectors', 'new preregistered holdout gate; old R5 failures preserved'], no_X3_selected=True)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--source-audit', action='store_true')
    parser.add_argument('--source-ref')
    parser.add_argument('--stage-ref')
    parser.add_argument('--repeat-stage-ref')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not (args.execute or args.source_audit):
        print('{"enabled":false,"NPU":false,"qualification":false}')
        return 0
    source = json.loads(args.source_ref); own = obj(source)
    need(own['schema'] == 'mxr.prefill-cpu-analysis-source/v120-analysis1' and own['files']['analyze.py'] == ref(__file__), 'exact source-only CPU extension')
    [checked(r) for r in own['files'].values()]
    m = obj(own['original_source_ref'])
    need(m['schema'] == 'mxr.r5-prefill-counterfactual-source/v120' and m['root'] == own['original_root'], 'exact frozen120R2 source')
    with original_consumer(m) as (G, C):
        _, _, _, refs = G.readset(m)
        readset = [source, own['original_source_ref'], *own['files'].values(), *m['files'].values(), *refs]
        [checked(r) for r in readset]
        if args.source_audit:
            print(json.dumps(dict(source=source, readset=readset, NPU=False, future_stage_data_pending=True)))
            return 0
        need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0' and os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == '' and not any(Path('/dev/davinci' + str(i)).exists() for i in range(8)), 'Devices[] original CPU contract')
        stage_ref = json.loads(args.stage_ref); stage = obj(stage_ref)
        need(stage['source'] == own['original_source_ref'], 'actual complete stage from frozen120R2')
        repeat_ref = json.loads(args.repeat_stage_ref) if args.repeat_stage_ref else None
        repeat = obj(repeat_ref) if repeat_ref else None
        need(args.output.is_absolute() and args.output.parent.is_dir() and not args.output.exists(), 'exclusive new report')
        import torch
        torch.set_num_threads(1)
        direct = load(own['files']['direct_round.py'], '_analysis120_exact_direct_RNE')
        result = consume(torch, G, C, m, stage, direct, repeat)
        result.update(source=source, stage_ref=stage_ref, repeat_stage_ref=repeat_ref, budgets=own['budgets'])
        payload = (json.dumps(result, sort_keys=True, allow_nan=False) + '\n').encode('utf8')
        need(len(payload) <= own['budgets']['output_bytes'], 'complete report cap; abort rather than truncate')
        with args.output.open('xb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
