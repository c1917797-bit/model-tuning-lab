"""Default-OFF independent Devices[] consumer of all192 actual GDN frames."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback


def _common(manifest_ref):
    reference = json.loads(manifest_ref); path = Path(reference['path'])
    if (not path.is_absolute() or any(x.is_symlink() for x in (path, *path.parents)) or
        path.stat().st_size != reference['bytes'] or
        hashlib.sha256(path.read_bytes()).hexdigest() != reference['sha256']):
        raise ValueError('exact ordinary manifest Ref3 before helper import')
    manifest = json.loads(path.read_bytes())
    r = manifest['files']['replay_common.py']; p = Path(r['path'])
    if (p != Path(__file__).resolve().with_name('replay_common.py') or
        any(x.is_symlink() for x in (p, *p.parents)) or
        p.stat().st_size != r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != r['sha256']):
        raise ValueError('exact private helper before import')
    name = '_bole_gdn_consumer_common'
    if name in sys.modules:
        raise ValueError('fresh standalone independent helper namespace')
    spec = importlib.util.spec_from_file_location(name, str(p))
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    module.need(module.ref(path) == reference and module.ref(p) == r,
                'stable manifest/helper bootstrap')
    return module, reference


def release(H, m, result_ref, release_ref):
    value = H.obj(release_ref)
    H.need(value['schema'] == 'bole.gdn3-replay-owner-released/v1' and
           value['authority'] == 'MAIN' and value['replay_result'] == result_ref and
           value['admission'] == m['admission'] and value['owner_stop_completed'] is True,
           'MAIN release bound to this exact replay result and admission')
    inspection = H.inspection(value['controller_inspection'])
    admission = H.obj(m['admission'])
    H.need(inspection['Id'] == admission['owned_container_id'] and
           inspection['Image'] == admission['image_digest'] and
           inspection['State']['Running'] is False,
           'actual controller inspection of stopped same owned container')


def source_observations(H, t, record, inputs, layout, source_refs):
    expected_hashes = {key: H.tensor_hash(t, tensor) for key, tensor in inputs.items()}
    before = record['input_storage_before']
    H.need(set(before) == set(H.INPUT_KEYS) and
           before['state'][4][-2:] == ([128, 1] if layout == 'contiguous' else [1, 128]),
           'actual recorded canonical layout and complete input identities')
    H.need(all(before[k][0] > 0 and before[k][1] > 0 and before[k][2] >= 0 and
               before[k][3] == list(inputs[k].shape) and before[k][5:] == ['torch.float32', 'npu:0']
               for k in H.INPUT_KEYS), 'actual private FP32 logical0 input identities')
    for role in ('original_after', 'candidate_after'):
        observation = record[role]
        H.need(observation['storage'] == before and observation['hashes'] == expected_hashes and
               observation['unchanged'] is True, 'actual input bytes/identities unchanged after ' + role)
    H.need(record['private_storage_disjoint_from_inputs'] is True and
           record['source_inputs_written'] is False and record['persistent_cache_written'] is False and
           record['scheduler_committed'] is False and record['model_ready'] is False and
           record['formal_success'] is False, 'private component replay only')
    receipt = record['candidate_receipt']
    H.need(receipt['source_refs'] == source_refs and receipt['kernel_launched'] is True and
           receipt['input_strides']['state'][-2:] == before['state'][4][-2:] and
           receipt['FP32'] is True and receipt['HF32'] is False and receipt['tile_v'] == 32 and
           receipt['source_inputs_written'] is False and receipt['persistent_cache_written'] is False and
           receipt['mathematically_qualified'] is False and receipt['model_ready'] is False and
           receipt['formal_success'] is False, 'actual source-bound candidate O/P/U launch receipt')
    H.need([r['terminal'] for r in record['commit_receipts']] == [0, 1, 2],
           'three actual selected-state launches')
    for r in record['commit_receipts']:
        H.need(r['source_refs'] == source_refs and r['kernel_launched'] is True and
               r['FP32'] is True and r['HF32'] is False and
               r['source_inputs_written'] is False and r['persistent_cache_written'] is False and
               r['scheduler_committed'] is False and r['mathematically_qualified'] is False and
               r['model_ready'] is False and r['formal_success'] is False,
               'source-bound private selected-state launch receipt')


def run(t, H, manifest_ref, result_ref, release_ref, output):
    m, receipts, admission = H.manifest(manifest_ref, __file__)
    del admission
    release(H, m, result_ref, release_ref)
    result = H.obj(result_ref)
    H.need(result['schema'] == 'bole.gdn3-actual-replay-result/v1' and
           result['manifest'] == manifest_ref and result['admission'] == m['admission'] and
           result['source'] == m['actual_source'] and result['frames'] == 192 and
           result['frame_layouts'] == 384 and len(result['ranks']) == 4 and
           result['all_actual_results_exported'] is True and result['microtiming'] is None and
           result['E2E_measured'] is False and result['mathematically_qualified'] is False and
           result['model_ready'] is False and result['formal_success'] is False,
           'complete untimed component replay requiring independent consumption')
    replay_root = Path(result_ref['path']).parent
    expected_files = {'REPLAY-RESULT.json', *('ACTUAL-RANK-%d.%s' % (rank, ext)
                                           for rank in range(4) for ext in ('json', 'bin'))}
    files = list(replay_root.iterdir())
    H.need({p.name for p in files} in (expected_files, expected_files | {'FAILURE.json'}) and
           all(p.is_file() and not p.is_symlink() for p in files),
           'only declared bounded result/index/blob/failure files in replay leaf')
    total_bytes = sum(p.stat().st_size for p in files)
    H.need(total_bytes <= H.CAP, 'actual aggregate output <=1GiB including originals/both layouts')
    output = Path(output)
    H.need(output.is_dir() and not any(output.iterdir()) and
           not any(p.is_symlink() for p in (output, *output.parents)),
           'fresh ordinary empty independent consumer output directory')
    t.set_num_threads(1)
    C, I, K, O, candidate = H.sources(m, with_candidate=False)
    del C, K, candidate
    source_refs = dict(implementation=m['candidate']['wrapper'], kernels=m['candidate']['kernels'],
                       reference=m['references']['core112.py'])
    reports = []; common_owner = None; common_tokens = None
    for rank, index_ref in enumerate(result['ranks']):
        H.need(Path(index_ref['path']) == replay_root / ('ACTUAL-RANK-%d.json' % rank),
               'exact same-leaf rank index')
        index = H.obj(index_ref)
        H.need(index['schema'] == 'bole.gdn3-actual-replay-rank/v1' and
               index['manifest'] == manifest_ref and index['rank'] == rank and
               index['source'] == m['actual_source'] and index['admission'] == m['admission'] and
               index['receipt'] == m['receipts'][rank]['receipt'] and
               index['original_raw'] == receipts[rank]['raw'] and
               index['frames'] == 48 and index['layouts_per_frame'] == 2 and
               index['actual_tensors_per_layout'] == 18 and
               index['mathematically_qualified'] is False and index['model_ready'] is False and
               index['formal_success'] is False,
               'complete source-bound actual per-rank export')
        blob = H.checked(index['blob'])
        H.need(blob == replay_root / ('ACTUAL-RANK-%d.bin' % rank), 'exact owned rank blob')
        exported, raw = H.load_raw(t, receipts[rank], m)
        H.need(index['owner'] == raw['request'] and index['tokens'] == raw['tree_context']['tokens'],
               'actual original rank/request/tree join')
        if common_owner is None:
            common_owner, common_tokens = index['owner'], index['tokens']
        H.need(index['owner'] == common_owner and index['tokens'] == common_tokens and
               [r['layer'] for r in index['rows']] == list(H.LAYERS),
               'all4 same actual request and every48 GDN layer exactly once')
        offset = 0; rows = []
        with blob.open('rb') as stream:
            for item in index['rows']:
                layer = item['layer']; row = raw['tree_context']['captures'][layer]
                inputs = H.frame_inputs(t, row); captured = H.bases(row)
                truth = H.oracle_values(t, O, inputs)
                H.need([r['layout'] for r in item['layouts']] == list(H.LAYOUTS),
                       'both actual layouts exactly once')
                layouts = []
                for record in item['layouts']:
                    layout = record['layout']; decoded = {}
                    H.need(set(record['encoded']) == {'original', 'candidate', 'inputs_after'},
                           'no missing original/candidate/post-call actual values')
                    for role, keys, anchors in (('original', H.RESULT_KEYS, captured),
                                                 ('candidate', H.RESULT_KEYS, captured),
                                                 ('inputs_after', H.INPUT_KEYS, inputs)):
                        H.need(set(record['encoded'][role]) == set(keys), 'complete exact actual tensor set')
                        decoded[role] = {}
                        for key in keys:
                            decoded[role][key], offset = H.decode(
                                t, stream, record['encoded'][role][key], anchors[key], offset)
                    source_observations(H, t, record, inputs, layout, source_refs)
                    H.need(all(H.bits(t, decoded['inputs_after'][key], inputs[key]) for key in H.INPUT_KEYS),
                           'independent bitwise unchanged actual final inputs')
                    numerical = H.metrics(t, I, decoded['original'], decoded['candidate'], truth, captured)
                    H.need(numerical == record['metrics'] and record['passed'] == numerical['passed'],
                           'independently recomputed exact original112 metrics/decision, no relaxed gate')
                    layouts.append(dict(layout=layout, metrics=numerical, passed=numerical['passed'],
                                        actual_inputs_bitwise_unchanged=True,
                                        actual_original_and_candidate_bytes_verified=True))
                    del decoded
                rows.append(dict(layer=layer, layouts=layouts))
        H.need(offset == index['blob']['bytes'] and H.ref(blob) == index['blob'],
               'all blob bytes consumed once without gaps/trailing data; stable actual bytes')
        reports.append(dict(rank=rank, index=index_ref, original_raw=receipts[rank]['raw'], rows=rows,
                            passed=all(x['passed'] for r in rows for x in r['layouts'])))
        del exported, raw, index, rows
    passed = all(r['passed'] for r in reports)
    H.need(result['local_component_checks_pass'] == passed and
           [r['passed'] for r in result['summary']] == [r['passed'] for r in reports],
           'independent complete192-frame decision joins local result without trusting it')
    report = dict(schema='bole.gdn3-independent-actual-replay/v1', manifest=manifest_ref,
                  replay_result=result_ref, owner_release=release_ref, ranks=reports,
                  frames=192, frame_layouts=384, component_replay_independent_pass=passed,
                  exact_original112_bounds=True, literal_sequential_FP64_oracle=True,
                  actual_original_device_results_included=True, P_bitwise_original_checked=True,
                  actual_inputs_bitwise_unchanged=True, lossless_actual_byte_exports=True,
                  replay_export_bytes=total_bytes, output_cap_bytes=H.CAP, NPU=False,
                  microtiming=None, E2E_measured=False, model_ready=False,
                  whole_model_qualified=False, formal_success=False, scheduler_committed=False)
    data = H.json_bytes(report)
    H.need(len(data) <= 15 * 2**20 and total_bytes + len(data) <= H.CAP,
           'aggregate replay plus independent metrics remains <=1GiB')
    path = output / 'INDEPENDENT.json'
    with path.open('xb') as stream:
        stream.write(data)
    report_ref = H.ref(path)
    H.need(passed, 'independent original component bounds failed; all metrics retained')
    return report_ref


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-ref')
    parser.add_argument('--result-ref')
    parser.add_argument('--owner-release-ref')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, NPU=False, tensor_runtime_imported=False,
                              component_replay_independent_pass=False, model_ready=False, formal_success=False)))
        return 0
    if not all((args.manifest_ref, args.result_ref, args.owner_release_ref, args.output)):
        parser.error('--execute needs --manifest-ref --result-ref --owner-release-ref --output')
    if (os.environ.get('BOLE_GDN3_CONSUME_ENABLE') != '1' or
        os.environ.get('ASCEND_RT_VISIBLE_DEVICES') != '' or
        os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') != '0'):
        parser.error('explicit BOLE_GDN3_CONSUME_ENABLE=1 in Devices[] with empty ASCEND_RT_VISIBLE_DEVICES and TORCH_DEVICE_BACKEND_AUTOLOAD=0')
    if list(Path('/dev').glob('davinci[0-9]*')):
        parser.error('independent Devices[] consumer must have no NPU device nodes')
    H, manifest_ref = _common(args.manifest_ref)
    H.manifest(manifest_ref, __file__)
    result_ref = json.loads(args.result_ref); release_ref = json.loads(args.owner_release_ref)
    H.checked(result_ref); release(H, H.obj(manifest_ref), result_ref, release_ref)
    import torch
    try:
        result = run(torch, H, manifest_ref, result_ref, release_ref, args.output)
    except BaseException:
        # No device cleanup or new admission is attempted by this consumer.
        print(traceback.format_exc(), file=sys.stderr)
        raise
    print(json.dumps(dict(result=result, model_ready=False, formal_success=False), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
