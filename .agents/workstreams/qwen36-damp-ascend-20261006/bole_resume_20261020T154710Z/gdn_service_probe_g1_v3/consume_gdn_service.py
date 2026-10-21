"""Default-OFF Devices[] supplement to the unchanged full service consumer.

The full original reader/HTTP/TP4/retirement report remains mandatory. This
supplement verifies actual extension ownership and recomputes new-prefix GDN
math; it never certifies whole-model, task or performance readiness.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def disabled():
    return dict(enabled=False, NPU=False, prepared_only=True,
                new_service_prefixes_pass=False, model_ready=False, formal_success=False)


def bootstrap(reference):
    def checked(r):
        p = Path(r['path']); data = p.read_bytes()
        if (not p.is_absolute() or any(x.is_symlink() for x in (p, *p.parents)) or
            len(data) != r['bytes'] or hashlib.sha256(data).hexdigest() != r['sha256']):
            raise ValueError('exact ordinary service source bytes before imports')
        return p, data
    _, data = checked(reference); m = json.loads(data)
    p, _ = checked(m['files']['sourceio.py'])
    spec = importlib.util.spec_from_file_location('_gdn_service_sourceio', str(p))
    C = importlib.util.module_from_spec(spec); sys.modules[spec.name] = C
    spec.loader.exec_module(C)
    C.need(C.ref(p) == m['files']['sourceio.py'] and C.obj(reference) == m and
           C.ref(__file__) == m['files']['consume_gdn_service.py'], 'stable exact independent source entry')
    for r in (*m['files'].values(), *m['runtime_sources'].values()):
        C.checked(r)
    p = C.checked(m['files']['gdn_service_gate.py'])
    spec = importlib.util.spec_from_file_location('_gdn_service_consumer_gate', str(p))
    G = importlib.util.module_from_spec(spec); sys.modules[spec.name] = G
    spec.loader.exec_module(G)
    C.need(C.ref(G.__file__) == m['files']['gdn_service_gate.py'], 'exact independent extension gate')
    return C, G, m


def consume_rank(t, C, m, raw, base, qualification, extension_ref, replay):
    C.need(C.ref(base.__file__) == m['files']['consume_service.py'] and
           C.ref(base.I.__file__) == m['files']['independent_model.py'] and
           C.ref(base.oracle112.__file__) == m['files']['oracle112.py'], 'unchanged complete service/math readers')
    original_report = base.consume_rank(t, m, raw)
    rows = []; passed = bool(original_report['component_checks_pass'])
    expected_refs = dict(implementation=replay['candidate']['wrapper'], kernels=replay['candidate']['kernels'],
                         reference=m['files']['core112.py'])
    for ordinal, step in enumerate(raw['steps']):
        path = step['staged']['processed_nodes']; terminal = path[-1]
        writes = {(r['layer'], r['kind']): r for r in step['staged']['writes']}
        before = {r['layer']: r for r in step['before_GDN']}
        metrics = []
        for layer in (i for i in range(64) if i % 4 != 3):
            row = step['tree_context']['captures'][layer]; proof = row['gdn_extension']
            C.need(proof['schema'] == 'bole.service-private-gdn/v1' and proof['source'] == extension_ref and
                   proof['mode'] == m['gdn_service_extension']['mode'] and proof['owner'] == step['owner'] and
                   proof['layer'] == layer and proof['prerequisites'] == qualification and
                   proof['actual_node_states_omitted'] is True and 'actual_node_states' not in row and
                   proof['persistent_cache_written'] is False and proof['model_ready'] is False and
                   proof['formal_success'] is False, 'exact mode/source/owner/layer private O/P/U capture')
            selected = proof['selected']
            C.need(selected['terminal'] == terminal and selected['private'] is True and
                   selected['canonical_layout'] == 'B,H,Dk,Dv' and selected['native_after_layout'] == 'H,Dv,Dk' and
                   selected['source_inputs_written'] is False and selected['persistent_cache_written'] is False and
                   selected['scheduler_committed'] is False, 'one exact private selected state joined to actual path')
            if proof['mode'] == 'candidate':
                forward = proof['forward']; commit = selected['receipt']
                C.need(forward['source_refs'] == commit['source_refs'] == expected_refs and
                       forward['kernel_launched'] is True and commit['kernel_launched'] is True and
                       forward['FP32'] is True and commit['FP32'] is True and
                       forward['HF32'] is False and commit['HF32'] is False and
                       commit['terminal'] == terminal and forward['persistent_cache_written'] is False and
                       commit['persistent_cache_written'] is False and
                       commit['scheduler_committed'] is False, 'actual candidate O/P/U and selected kernel receipts')
            else:
                C.need(proof['forward'] == selected['receipt'] ==
                       dict(reference=m['files']['core112.py'], original_math=True),
                       'matched original math, no fabricated kernel result')
            q, k, v, beta, gamma = row['normalized_inputs']
            initial = before[layer]['native_state'].transpose(-1, -2).unsqueeze(0)
            C.need(base.I.bits(t, row['state'], initial), 'actual new-prefix canonical input/native preimage')
            truth, states, updates = base.oracle112.sequential(t, q.double(), k.double(), v.double(),
                beta.double(), gamma.double(), initial.double(), (-1, 0, 0), return_updates=True)
            gd = gamma.double(); product = t.stack((gd[..., 0], gd[..., 0]*gd[..., 1], gd[..., 0]*gd[..., 2]), dim=-1)
            after = writes[layer, 'state']['after'].transpose(-1, -2).unsqueeze(0)
            metric = dict(layer=layer, O=base.I.old112(t, row['precast_output'], truth),
                P=base.I.old112(t, row['factors'][0], product), U=base.I.old112(t, row['factors'][1], updates),
                selected=base.I.old112(t, after, states[terminal]))
            metric['passed'] = all(metric[key]['passed'] for key in ('O', 'P', 'U', 'selected'))
            passed = passed and metric['passed']; metrics.append(metric)
        rows.append(dict(ordinal=ordinal, owner=step['owner'], terminal=terminal, metrics=metrics))
    return dict(schema='bole.gdn3-service-independent-rank/v1', rank=raw['rank'], rows=rows,
                base_component_checks_pass=original_report['component_checks_pass'],
                base_output_token_ids=original_report['output_token_ids'],
                new_service_prefixes_pass=bool(passed), model_ready=False,
                native_AR_greedy_comparison_performed=False, E2E_measured=False, formal_success=False)


def run(t, C, G, m, *, source_ref, extension_ref, software_gate_ref, base_report_ref, output):
    x, H, replay, qualification = G.qualify(C, m, extension_ref, source_ref, software_gate_ref)
    del x
    prior = C.obj(base_report_ref)
    C.need(prior['schema'] == 'bole.actual-c1-two-request-service-independent/v1' and
           prior['source'] == source_ref and prior['service_complete'] is True and
           prior['component_checks_pass'] is True and prior['actual_all4_retirement'] is True and
           prior['actual_HTTP_output_token_ID_join'] is True and
           prior['scheduler_committed_independently'] is True and prior['model_ready'] is False and
           prior['formal_success'] is False, 'unchanged all4 full service/HTTP/retirement consumer pass required')
    bundle = C.obj(prior['inputs'])
    C.need(bundle['source'] == source_ref and len(bundle['ranks']) == len(prior['ranks']) == 4,
           'same exact four actual service raw inputs')
    output = Path(output)
    C.need(output.is_absolute() and output.is_dir() and not any(output.iterdir()) and
           not any(p.is_symlink() for p in (output, *output.parents)), 'fresh ordinary independent output')
    base = G.load(C, m['files']['consume_service.py'], '_gdn_service_original_consumer')
    base.load_helpers()
    C.need(base.validate_source(source_ref) == m, 'unchanged complete service reader source/root closure')
    t.set_num_threads(1)
    reports = []; refs = []
    for rank, pair in enumerate(bundle['ranks']):
        receipt = C.obj(pair['receipt']); base_rank = C.obj(prior['ranks'][rank])
        C.need(receipt['source'] == source_ref and receipt['rank'] == rank and receipt['primary'] is None and
               receipt['raw'] == pair['raw'] and base_rank['source'] == source_ref and
               base_rank['receipt'] == pair['receipt'] and base_rank['raw'] == pair['raw'] and
               [r['generation']for r in base_rank['requests']]==[1,2]and
               all(r['rank']==rank and r['component_checks_pass']is True for r in base_rank['requests']),
               'actual raw/receipt/base independent two-request result join')
        path = C.checked(pair['raw']); exported = t.load(path, map_location='cpu', weights_only=True)
        C.need(C.ref(path) == pair['raw'] and exported['schema'] == 'bole.model-diagnostic-primitives/v1' and
               exported['cap_bytes'] == 2**30 and
               H.primitive_bytes(t, exported['payload']) == exported['logical_tensor_bytes'] <= 2**30,
               'stable safe-loaded complete primitive service envelope')
        raw = exported['payload']
        C.need(raw['source'] == source_ref and raw['rank'] == rank and len(raw['requests'])==2 and
               raw['schema']=='bole.actual-c1-two-request-service/v1', 'same actual two-request service rank/source')
        rank_reports=[]
        for generation,item in enumerate(raw['requests'],1):
            C.need(item['source']==source_ref and item['rank']==rank and item['request']['generation']==generation,
                   'actual two distinct monotonic request captures')
            report=consume_rank(t,C,m,item,base,qualification,extension_ref,replay)
            C.need(report['base_output_token_ids']==base_rank['requests'][generation-1]['output_token_ids'],
                   'supplement reopens same full independent output-token result')
            report.update(request=item['request']['request'],generation=generation)
            reports.append(report);rank_reports.append(report)
        refs.append(C.write(output / ('GDN-RANK-%d.json' % rank), dict(source=source_ref,
            receipt=pair['receipt'], raw=pair['raw'], requests=rank_reports)))
        del exported, raw
    result = dict(schema='bole.gdn3-service-independent/v1', source=source_ref, extension=extension_ref,
                  base_service_report=base_report_ref, qualification=qualification, ranks=refs,
                  new_service_prefixes_pass=all(r['new_service_prefixes_pass'] for r in reports),
                  scope='bounded G1 two131/output2/root-only target each; all O/P/U and one actual selected state',
                  actual_GDN_frames=sum(len(row['metrics'])for report in reports for row in report['rows']),
                  completed_request_count=2,
                  NPU=False, model_ready=False, whole_model_qualified=False,
                  E2E_measured=False, performance_ready=False, formal_success=False)
    result_ref = C.write(output / 'GDN-INDEPENDENT.json', result)
    C.need(result['new_service_prefixes_pass']and result['actual_GDN_frames']==384,
           'complete new service GDN original bounds failed; all metrics retained')
    return result_ref


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--execute', action='store_true'); p.add_argument('--source-ref'); p.add_argument('--extension-ref')
    p.add_argument('--owned-probe-consumer',action='store_true')
    p.add_argument('--software-gate-ref'); p.add_argument('--base-report-ref'); p.add_argument('--output', type=Path)
    a = p.parse_args()
    if not a.execute:
        print(json.dumps(disabled())); return 0
    if not all((a.source_ref, a.extension_ref, a.software_gate_ref, a.base_report_ref, a.output)):
        p.error('all exact source/extension/software/base-report refs and output required')
    if (not(a.owned_probe_consumer or os.environ.get('BOLE_GDN_SERVICE_CONSUME_ENABLE') == '1') or
        os.environ.get('ASCEND_RT_VISIBLE_DEVICES') != '' or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') != '0'):
        p.error('explicit Devices[] consumer opt-in, empty visibility and backend autoload0 required')
    if list(Path('/dev').glob('davinci[0-9]*')):
        p.error('no numbered NPU nodes in independent Devices[] consumer')
    sr, xr, sw, br = (json.loads(v) for v in (a.source_ref, a.extension_ref, a.software_gate_ref, a.base_report_ref))
    C, G, m = bootstrap(sr)
    G.qualify(C, m, xr, sr, sw)  # All sources/replay/software checks before Torch.
    import torch
    print(json.dumps(dict(result=run(torch, C, G, m, source_ref=sr, extension_ref=xr,
        software_gate_ref=sw, base_report_ref=br, output=a.output), model_ready=False, formal_success=False)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
