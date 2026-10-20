"""Default-OFF actual GDN replay. MAIN alone admits/creates its owned container.

--execute may initialize ONLY logical npu:0 after the exact MAIN admission is
verified. This program has no Docker, physical selection, service or Git code.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback


def _common(manifest_ref):
    # Bootstrap the helper by its explicit manifest Ref3 before importing it.
    reference = json.loads(manifest_ref)
    path = Path(reference['path'])
    if (not path.is_absolute() or any(x.is_symlink() for x in (path, *path.parents)) or not path.is_file() or
        path.stat().st_size != reference['bytes'] or
        hashlib.sha256(path.read_bytes()).hexdigest() != reference['sha256']):
        raise ValueError('exact manifest Ref3 before helper import')
    manifest = json.loads(path.read_bytes())
    r = manifest['files']['replay_common.py']; p = Path(r['path'])
    if (p != Path(__file__).resolve().with_name('replay_common.py') or
        any(x.is_symlink() for x in (p, *p.parents)) or
        p.stat().st_size != r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != r['sha256']):
        raise ValueError('exact ordinary private helper before import')
    name = '_bole_gdn_replay_common'
    if name in sys.modules:
        raise ValueError('fresh standalone replay helper namespace')
    spec = importlib.util.spec_from_file_location(name, str(p))
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    module.need(module.ref(path) == reference and module.ref(p) == r,
                'stable manifest/helper bootstrap')
    return module, reference


def owned_runtime(t, H, admission):
    H.need(os.environ.get('BOLE_GDN3_REPLAY_ENABLE') == '1' and
           os.environ.get('BOLE_GDN3_TRITON_ENABLE') == '1', 'two explicit execution opt-ins')
    H.owned_environment(admission)
    H.need(hasattr(t, 'npu') and t.npu.device_count() == 1,
           'MAIN supplied singleton logical device mapping')
    # The physical4 -> /dev/davinci0 mapping belongs to MAIN's controller proof.
    # This call never uses or chooses a physical identifier.
    t.npu.set_device(0)
    t.npu.matmul.allow_hf32 = False
    H.need(t.npu.is_initialized() and t.npu.current_device() == 0 and
           t.npu.matmul.allow_hf32 is False, 'existing owned logical0/common HF32-OFF')


def identity(tensor):
    return [tensor.untyped_storage().data_ptr(), tensor.data_ptr(),
            tensor.storage_offset(), list(tensor.shape), list(tensor.stride()),
            str(tensor.dtype), str(tensor.device)]


def cpu(tensor):
    return tensor.detach().cpu().contiguous()


def observe(t, H, inputs, expected, before):
    result = dict(storage={k: identity(x) for k, x in inputs.items()},
                  hashes={k: H.tensor_hash(t, cpu(x)) for k, x in inputs.items()})
    result['unchanged'] = result['storage'] == before and all(
        H.bits(t, cpu(inputs[k]), expected[k]) for k in H.INPUT_KEYS)
    return result


def one_layout(t, H, C, I, K, O, candidate, m, row, layout, stream, budget):
    captured = H.bases(row); expected = H.frame_inputs(t, row)
    inputs = {name: x.to(device='npu:0').contiguous() for name, x in expected.items()}
    if layout == 'column_strided':
        inputs['state'] = inputs['state'].transpose(-1, -2).contiguous().transpose(-1, -2)
    H.need(tuple(inputs['state'].stride()[-2:]) ==
           ((128, 1) if layout == 'contiguous' else (1, 128)), 'actual requested canonical stride')
    before = {k: identity(x) for k, x in inputs.items()}
    H.need(all(H.bits(t, cpu(inputs[k]), expected[k]) for k in H.INPUT_KEYS),
           'exact actual FP32 H2D input roundtrip, no synthesis or dtype conversion')
    ancestor = t.tensor([[False, False, False], [True, False, False],
                         [True, False, False]], dtype=t.bool, device='npu:0')
    inclusive = ancestor.float() + t.eye(3, dtype=t.float32, device='npu:0')
    q, k, v, beta, gamma, state = (inputs[n] for n in H.INPUT_KEYS)
    output, factors = K.verify(t, q, k, v, beta, gamma, state, ancestor, 1)
    original_device = dict(O=output, P=factors[0], U=factors[1])
    for terminal in range(3):
        original_device['S%d' % terminal] = K.commit(t, state, k, factors, inclusive, terminal)
    original_after = observe(t, H, inputs, expected, before)
    source_refs = dict(implementation=m['candidate']['wrapper'],
                       kernels=m['candidate']['kernels'], reference=m['references']['core112.py'])
    result = candidate.execute_verify(t, q, k, v, beta, gamma, state, ancestor, 1,
                                     enabled=True, arm_verified=True, C=C,
                                     source_refs=source_refs, tile_v=32)
    H.need(result['enabled'] is True, 'actual candidate execution, never disabled placeholder')
    candidate_device = dict(O=result['output'], P=result['factors'][0], U=result['factors'][1])
    commit_receipts = []
    for terminal in range(3):
        selected = candidate.execute_commit(t, state, k, result['factors'], terminal,
                                           enabled=True, arm_verified=True, C=C,
                                           source_refs=source_refs, tile_k=32, tile_v=32)
        candidate_device['S%d' % terminal] = selected['selected_state']
        commit_receipts.append(selected['receipt'])
    candidate_after = observe(t, H, inputs, expected, before)
    input_storages = {x.untyped_storage().data_ptr() for x in inputs.values()}
    private = all(x.untyped_storage().data_ptr() not in input_storages
                  for values in (original_device, candidate_device) for x in values.values())
    original = {key: cpu(value) for key, value in original_device.items()}
    actual = {key: cpu(value) for key, value in candidate_device.items()}
    truth = H.oracle_values(t, O, expected)
    numerical = H.metrics(t, I, original, actual, truth, captured)
    # All actual results are exported, including failures; no best-frame filter.
    encoded = {}
    for name, values in (('original', original), ('candidate', actual)):
        encoded[name] = {key: H.encode(t, stream, budget, values[key], captured[key])
                         for key in H.RESULT_KEYS}
    encoded['inputs_after'] = {key: H.encode(t, stream, budget, cpu(inputs[key]), expected[key])
                               for key in H.INPUT_KEYS}
    passed = bool(numerical['passed'] and original_after['unchanged'] and
                  candidate_after['unchanged'] and private)
    return dict(layout=layout, encoded=encoded, metrics=numerical,
                original_after=original_after, candidate_after=candidate_after,
                input_storage_before=before, private_storage_disjoint_from_inputs=private,
                candidate_receipt=result['receipt'], commit_receipts=commit_receipts,
                passed=passed, source_inputs_written=False, persistent_cache_written=False,
                scheduler_committed=False, model_ready=False, formal_success=False)


def run(t, H, manifest_ref, output, *, initialize_logical0=True):
    m, receipts, admission = H.manifest(manifest_ref, __file__)
    budget = H.Budget(output)
    try:
        H.need(os.environ.get('BOLE_GDN3_REPLAY_ENABLE') == '1' and
               os.environ.get('BOLE_GDN3_TRITON_ENABLE') == '1', 'execution opt-ins')
        H.owned_environment(admission)
        if initialize_logical0:
            owned_runtime(t, H, admission)
        else:
            H.need(admission['owned_container_id'] in Path('/proc/self/cgroup').read_text() and
                   t.npu.is_initialized() and t.npu.current_device() == 0 and
                   t.npu.matmul.allow_hf32 is False and t.npu.device_count() == 1,
                   'preinitialized existing MAIN-owned singleton logical0')
        t.set_num_threads(1)
        C, I, K, O, candidate = H.sources(m, with_candidate=True)
        indexes = []; summary = []; common_owner = None; common_tokens = None
        for rank, receipt in enumerate(receipts):
            exported, raw = H.load_raw(t, receipt, m)
            owner = raw['request']; tokens = raw['tree_context']['tokens']
            if common_owner is None:
                common_owner, common_tokens = owner, tokens
            H.need(owner == common_owner and tokens == common_tokens,
                   'all4 actual ranks share exact request/tree ownership')
            blob_path = budget.output / ('ACTUAL-RANK-%d.bin' % rank)
            rows = []
            with blob_path.open('xb') as stream:
                for layer in H.LAYERS:
                    row = raw['tree_context']['captures'][layer]
                    rows.append(dict(layer=layer, layouts=[
                        one_layout(t, H, C, I, K, O, candidate, m, row, layout, stream, budget)
                        for layout in H.LAYOUTS]))
            index = dict(schema='bole.gdn3-actual-replay-rank/v1', manifest=manifest_ref,
                         rank=rank, source=m['actual_source'], receipt=m['receipts'][rank]['receipt'],
                         original_raw=receipt['raw'], admission=m['admission'],
                         owner=owner, tokens=tokens, blob=H.ref(blob_path), rows=rows,
                         frames=48, layouts_per_frame=2, actual_tensors_per_layout=18,
                         codec='lossless FP32 bytewise XOR against exact captured originals + zlib',
                         mathematically_qualified=False, model_ready=False, formal_success=False)
            indexes.append(budget.json('ACTUAL-RANK-%d.json' % rank, index))
            summary.append(dict(rank=rank, frames=48, passed=all(
                layout['passed'] for row in rows for layout in row['layouts'])))
            del exported, raw, rows, index
        passed = all(row['passed'] for row in summary)
        result = dict(schema='bole.gdn3-actual-replay-result/v1', manifest=manifest_ref,
                      admission=m['admission'], source=m['actual_source'], ranks=indexes,
                      summary=summary, frames=192, frame_layouts=384,
                      all_actual_results_exported=True, local_component_checks_pass=passed,
                      output_bytes_before_result=budget.used, output_cap_bytes=H.CAP,
                      microtiming=None, E2E_measured=False, independent_consumer_required=True,
                      mathematically_qualified=False, model_ready=False, formal_success=False,
                      scheduler_committed=False, persistent_cache_written=False)
        result_ref = budget.json('REPLAY-RESULT.json', result)
        H.need(passed, 'actual replay component gates failed; all192 frame results/metrics retained')
        return result_ref
    except BaseException as error:
        try:
            budget.json('FAILURE.json', dict(schema='bole.gdn3-replay-failure/v1',
                        manifest=manifest_ref, primary=repr(error)[:8192], traceback=traceback.format_exc()[-65536:],
                        output_bytes_before_failure=budget.used, model_ready=False,
                        mathematically_qualified=False, formal_success=False), failure=True)
        except BaseException as secondary:
            print(json.dumps(dict(primary=repr(error), failure_receipt_error=repr(secondary))), file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-ref', help='JSON Ref3 of the exact MAIN-filled manifest')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, NPU=False, tensor_runtime_imported=False,
                              mathematically_qualified=False, model_ready=False, formal_success=False)))
        return 0
    if not args.manifest_ref or args.output is None:
        parser.error('--execute requires --manifest-ref and --output')
    if (os.environ.get('BOLE_GDN3_REPLAY_ENABLE') != '1' or
        os.environ.get('BOLE_GDN3_TRITON_ENABLE') != '1'):
        parser.error('--execute requires BOLE_GDN3_REPLAY_ENABLE=1 and BOLE_GDN3_TRITON_ENABLE=1')
    H, manifest_ref = _common(args.manifest_ref)
    # Complete all source/raw/admission checks before importing tensor runtimes.
    _, _, admission = H.manifest(manifest_ref, __file__)
    H.owned_environment(admission)
    import torch
    import torch_npu  # exact admitted image; registration only after execute/opt-in
    del torch_npu
    result = run(torch, H, manifest_ref, args.output)
    print(json.dumps(dict(result=result, mathematically_qualified=False,
                          model_ready=False, formal_success=False), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
