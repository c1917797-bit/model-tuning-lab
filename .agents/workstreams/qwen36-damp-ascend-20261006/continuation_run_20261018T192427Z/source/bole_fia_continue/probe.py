"""Exact retained FIA calls before a single numeric-parameter intervention.

This module creates no device, owner, container or ARM. A source-bound singleton
guest may call run only after its original actual owner/MAIN_ARM checks. Complete
tree and dense baselines must both match the frozen BF16 outputs before either
parameter intervention. A failed replay remains useful evidence, never a pass.
"""
import argparse
import gc
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

import plan as P

SCHEMA = 'bole.fia-original-replay-and-parameter-probe/v1'
ATOL, RTOL = 0.001, 0.01
need = P.need


def words_comparison(actual, expected):
    need(len(actual) == len(expected) and len(actual) > 0, 'complete BF16 word vectors')
    need(all(type(x) is int and 0 <= x <= 65535 for x in (*actual, *expected)),
         'unsigned BF16 words')
    changed = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
    return dict(elements=len(actual), bitwise_equal_elements=len(actual)-len(changed),
                bitwise_equal=not changed, different_flat_indices=changed)


def pointwise(actual, truth):
    need(len(actual) == len(truth) and len(actual) > 0 and
         all(math.isfinite(x) for x in (*actual, *truth)), 'finite complete numerical vectors')
    errors = [abs(a-b) for a, b in zip(actual, truth)]
    failed = [i for i, (error, value) in enumerate(zip(errors, truth))
              if error > ATOL+RTOL*abs(value)]
    norm = math.sqrt(math.fsum(x*x for x in truth))
    return dict(elements=len(actual), pointwise_pass=not failed,
                failed_elements=len(failed), failed_flat_indices=failed,
                max_absolute_error=max(errors),
                relative_l2=math.sqrt(math.fsum(x*x for x in errors))/max(norm, 1e-30))


def parameter_delta(original, changed):
    need(set(original) == set(changed), 'no added or omitted call arguments')
    differences = [key for key in original if original[key] != changed[key]]
    need(differences == ['inner_precise'] and
         type(original['inner_precise']) is type(changed['inner_precise']) is int and
         {original['inner_precise'], changed['inner_precise']} == {0, 2},
         'sole intervention is original0-to2 or original2-to0')
    return dict(parameter='inner_precise', original=original['inner_precise'],
                changed=changed['inner_precise'], numeric_semantics=None)


def baseline_gate(rows):
    if len(rows) != 2 or [row.get('branch') for row in rows] != ['tree', 'native']:
        return False
    return all(row.get('role') == 'baseline' and row.get('primary') is None and
               row.get('operator_completed') is True and
               row.get('transfer_and_inputs_unchanged') is True and
               row.get('whole_output', {}).get('bitwise_equal') is True and
               row.get('whole_output', {}).get('elements') ==
                   (4608 if row['branch'] == 'tree' else 1536) and
               row.get('original_failure_sets_reproduced') is True for row in rows)


def deadline(value):
    need(type(value) in (int, float) and math.isfinite(value) and
         time.time() < value <= P.CUTOFF, 'remaining reviewed guest work window')


def bits(t, left, right):
    return (left.shape == right.shape and left.dtype == right.dtype and
            t.equal(left.contiguous().view(t.uint8), right.contiguous().view(t.uint8)))


def tensor_words(t, value):
    need(value.device.type == 'cpu' and value.dtype == t.bfloat16, 'CPU BF16 output words')
    return [int(word) & 65535 for word in value.contiguous().view(t.int16).reshape(-1).tolist()]


def tensor_binding(t, value):
    need(value.device.type == 'cpu', 'readback before digest')
    data = bytes(value.contiguous().view(t.uint8).reshape(-1).tolist())
    return dict(shape=list(value.shape), stride=list(value.stride()), dtype=str(value.dtype),
                bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def require_tensor(t, value, shape, dtype, *, contiguous=True):
    need(isinstance(value, t.Tensor) and value.device.type == 'cpu' and
         tuple(value.shape) == tuple(shape) and value.dtype == dtype and
         (not contiguous or value.is_contiguous()), 'original tensor shape/dtype/layout')
    need(bool(t.isfinite(value).all()), 'original finite tensor')


def cpu_reference(t, query, keys, values, dtype):
    """Exact per-head formula used by frozen independent_model.attention.

The tree's authoritative pass result is also obtained by calling that unchanged
original function. These vectors expose the complete pointwise failure set.
"""
    keys = keys.to(dtype)
    values = values.to(dtype)
    heads = []
    for head in range(6):
        logits = keys.mv(query[head].to(dtype))*(256**-.5)
        probability = (logits-logits.max()).exp()
        probability /= probability.sum()
        heads.append(values.T.mv(probability))
    return t.stack(heads)


def original_oracle():
    """Import both complete, byte-checked original files; no AST subset or shim."""
    modules = [('model_entry', P.PRODUCERS['model_entry.py']),
               ('_bole_replay_original_independent_model', P.PRODUCERS['independent_model.py'])]
    loaded = []
    for name, reference in modules:
        path = P.checked(reference)
        if name in sys.modules:
            module = sys.modules[name]
            need(P.ref(module.__file__) == reference, 'no ambient oracle/producer module')
        else:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            try:
                spec.loader.exec_module(module)
            except BaseException:
                sys.modules.pop(name, None)
                raise
        loaded.append(module)
    need(loaded[1].need is loaded[0].need, 'original independent oracle imports original guard')
    return loaded[1]


def select_frames(t, raw):
    need(raw['schema'] == 'bole.actual-three-node-model-capture/v1' and
         raw['rank'] == 1 and raw['source'] == P.SOURCE and
         raw['scheduler_committed'] is False and raw['request']['length'] == 131 and
         raw['tree_context']['owner'] == raw['request'], 'exact original source/rank/request')
    row = raw['tree_context']['captures'][43]
    need(row['kind'] == 'fa', 'original selected FA layer')
    saved = row['trial']['native_before']
    layouts = row['trial']['native_layout']
    shapes = dict(query=(1, 6, 3, 256), key=(2, 1, 128, 256),
                  value=(2, 1, 128, 256), atten_mask=(1, 1, 3, 256), block_table=(1, 2))
    for name, shape in shapes.items():
        dtype = t.bool if name == 'atten_mask' else t.int32 if name == 'block_table' else t.bfloat16
        require_tensor(t, saved[name], shape, dtype)
        need(layouts[name] == dict(shape=list(shape), stride=list(saved[name].stride()),
                                   dtype=str(dtype)), 'recorded original native layout')
    need(saved['block_table'].tolist() == [[0, 1]], 'unchanged original paged block table')
    anchors = [value for value in raw['initial_FA_pages'] if value['layer'] == 43]
    need(len(anchors) == 1, 'unique original FA prefix')
    anchor = anchors[0]
    need(len(anchor['physical_pages']) == 2 and len(set(anchor['physical_pages'])) == 2 and
         tuple(anchor['physical_pages']) == tuple(row['actual_physical_pages']),
         'original physical prefix page order')
    require_tensor(t, anchor['key'], (2, 128, 1, 256), t.bfloat16)
    require_tensor(t, anchor['value'], (2, 128, 1, 256), t.bfloat16)
    prefix_k = t.stack([anchor['key'][n//128, n%128, 0] for n in range(131)])
    prefix_v = t.stack([anchor['value'][n//128, n%128, 0] for n in range(131)])
    full_mask = t.ones((1, 1, 3, 256), dtype=t.bool)
    full_mask[:, :, :, :132] = False
    full_mask[0, 0, 1, 132] = False
    full_mask[0, 0, 2, 133] = False
    keys = saved['key'].permute(0, 2, 1, 3).reshape(256, 256)
    values = saved['value'].permute(0, 2, 1, 3).reshape(256, 256)
    query = saved['query'].squeeze(0).permute(1, 0, 2)
    require_tensor(t, row['query'], (3, 1536), t.bfloat16, contiguous=False)
    require_tensor(t, row['key'], (3, 256), t.bfloat16, contiguous=False)
    require_tensor(t, row['value'], (3, 256), t.bfloat16, contiguous=False)
    require_tensor(t, row['output'], (3, 6, 256), t.bfloat16)
    need(bits(t, saved['atten_mask'], full_mask) and
         bits(t, query, row['query'].reshape(3, 6, 256)) and
         bits(t, keys[:134], t.cat((prefix_k, row['key']))) and
         bits(t, values[:134], t.cat((prefix_v, row['value']))) and
         bits(t, keys[134:], t.zeros_like(keys[134:])) and
         bits(t, values[134:], t.zeros_like(values[134:])),
         'original full mask, post-RoPE query, prefix/nodes and zero padding')
    need([path['child'] for path in raw['native']] == [1, 2], 'original native paths')
    path = raw['native'][1]
    need([step['node'] for step in path['steps']] == [0, 2], 'original native root/right order')
    root = path['steps'][0]['context']['captures'][43]
    native = path['steps'][1]['context']['captures'][43]
    need(root['kind'] == native['kind'] == 'fa-native-AR' and
         root['phase'] == native['phase'] == 'NATIVE_FA_COMPLETE', 'original completed native calls')
    for capture, length in ((root, 132), (native, 133)):
        require_tensor(t, capture['query'], (1, 1536), t.bfloat16, contiguous=False)
        require_tensor(t, capture['key'], (1, 256), t.bfloat16, contiguous=False)
        require_tensor(t, capture['value'], (1, 256), t.bfloat16, contiguous=False)
        require_tensor(t, capture['after_key'], (length, 1, 256), t.bfloat16)
        require_tensor(t, capture['after_value'], (length, 1, 256), t.bfloat16)
    for name, prefix in (('key', prefix_k), ('value', prefix_v)):
        need(bits(t, root['after_'+name].reshape(132, 256), t.cat((prefix, root[name]))) and
             bits(t, native['after_'+name].reshape(133, 256),
                  t.cat((root['after_'+name].reshape(132, 256), native[name]))),
             'independent original native prefix/root/current token join')
    require_tensor(t, native['output'], (1, 6, 1, 256), t.bfloat16, contiguous=False)
    # Exactly the original native reshapes/permutation/contiguous calls. No mask,
    # table or block_size argument is introduced into this dense branch.
    native_inputs = dict(query=native['query'].reshape(1, 1, 6, 256).permute(0, 2, 1, 3).contiguous(),
                         key=native['after_key'].permute(1, 0, 2).unsqueeze(0).contiguous(),
                         value=native['after_value'].permute(1, 0, 2).unsqueeze(0).contiguous())
    frame_row = {name: row[name].clone() for name in ('query', 'key', 'value', 'output')}
    frame_anchor = dict(physical_pages=list(anchor['physical_pages']),
                        key=anchor['key'].clone(), value=anchor['value'].clone())
    tree_refs = []
    for node in range(3):
        allowed = ~full_mask[0, 0, node]
        tree_refs.append(cpu_reference(t, query[node], keys[allowed], values[allowed], t.float64))
    native_ref = cpu_reference(t, native_inputs['query'].reshape(6, 256),
                               native['after_key'].reshape(133, 256),
                               native['after_value'].reshape(133, 256), t.float64)
    return dict(tree=dict(inputs={name: saved[name].clone() for name in shapes},
                          expected=row['output'].permute(1, 0, 2).unsqueeze(0).contiguous(),
                          reference=t.stack(tree_refs), oracle_row=frame_row, oracle_anchor=frame_anchor),
                native=dict(inputs=native_inputs,
                            expected=native['output'].clone(), reference=native_ref.unsqueeze(0)))


def canonical_output(output, branch):
    return output.squeeze(0).permute(1, 0, 2) if branch == 'tree' else output.reshape(1, 6, 256)


def output_metrics(t, output, branch, frame, oracle):
    canonical = canonical_output(output, branch)
    rows = []
    for index in range(len(canonical)):
        actual = canonical[index].double().reshape(-1).tolist()
        truth = frame['reference'][index].double().reshape(-1).tolist()
        result = pointwise(actual, truth)
        result['node'] = index if branch == 'tree' else 2
        result['label'] = 'tree-node%d'%index if branch == 'tree' else 'native-path2-node2'
        result['failed_points'] = [dict(flat_index=i, head=i//256, channel=i%256,
                                        actual=actual[i], original_CPU64=truth[i],
                                        bound=ATOL+RTOL*abs(truth[i]))
                                   for i in result['failed_flat_indices']]
        witness = [573] if (branch == 'native' or index == 2) else []
        result['original_failure_witnesses'] = [
            dict(flat_index=i, head=i//256, channel=i%256, actual=actual[i],
                 original_CPU64=truth[i], absolute_error=abs(actual[i]-truth[i]),
                 bound=ATOL+RTOL*abs(truth[i]),
                 passes_unchanged_bound=abs(actual[i]-truth[i]) <= ATOL+RTOL*abs(truth[i]))
            for i in witness]
        rows.append(result)
    original_gate = None
    if branch == 'tree':
        row = dict(frame['oracle_row'], output=canonical.contiguous())
        original_gate = oracle.attention(t, row, frame['oracle_anchor'])
        need(original_gate['double']['pointwise_pass'] == all(x['pointwise_pass'] for x in rows),
             'full vectors agree with unchanged original CPU64 gate')
    return dict(nodes=rows, original_tree_component_gate=original_gate,
                native_CPU64_is_diagnostic_only=(branch == 'native'))


def original_sets(metrics, branch):
    wanted = [[], [], [573]] if branch == 'tree' else [[573]]
    return [row['failed_flat_indices'] for row in metrics['nodes']] == wanted


def validate_saved_failure(t, frames, proof, oracle):
    metrics = {branch: output_metrics(t, frame['expected'], branch, frame, oracle)
               for branch, frame in frames.items()}
    need(all(original_sets(metrics[b], b) for b in ('tree', 'native')),
         'original complete tree0/1 pass and tree2/native2 failure identities')
    old_layer = proof['previous_layer']
    for branch in ('tree', 'native'):
        group = 'tree' if branch == 'tree' else 'native_own_inputs'
        for row in metrics[branch]['nodes']:
            old = [value for value in old_layer[group] if value['label'] == row['label']]
            need(len(old) == 1 and old[0]['failed'] == row['failed_elements'],
                 'prior actual rounding case join')
            old_points = {(x['head'], x['channel']): x for x in old[0]['failed_values']}
            for point in row['failed_points']:
                saved = old_points[(point['head'], point['channel'])]
                need(point['actual'] == saved['actual'] and
                     abs(point['original_CPU64']-saved['CPU64']) <= 1e-12,
                     'unchanged original actual/CPU64 failure witnesses')
    rank = P.obj(P.RANK_REPORT)
    old_gate = [row for row in rank['report']['rows'] if row['layer'] == 43][0]['attention']
    actual_gate = metrics['tree']['original_tree_component_gate']
    for precision in ('double', 'float'):
        need(actual_gate[precision]['pointwise_pass'] is old_gate[precision]['pointwise_pass'],
             'unchanged original full-tree float and CPU64 gates reproduce R6 report')
    need(abs(actual_gate['double']['peak_abs']-old_gate['double']['peak_abs']) <= 1e-12,
         'original CPU64 whole-tree peak reproduced')
    return metrics


def load_inputs(t, manifest):
    proof = P.consume(manifest['probe_plan_ref'])
    blob = t.load(P.checked(P.RAW), map_location='cpu', weights_only=False)
    need(blob['schema'] == 'bole.model-diagnostic-primitives/v1' and
         type(blob['logical_tensor_bytes']) is int and
         0 <= blob['logical_tensor_bytes'] <= blob['cap_bytes'] == 2**30,
         'fixed original primitive serialization and1GiB cap')
    frames = select_frames(t, blob['payload'])
    del blob
    gc.collect()
    oracle = original_oracle()
    original_metrics = validate_saved_failure(t, frames, proof, oracle)
    binding = {branch: dict(inputs={name: tensor_binding(t, value)
                                    for name, value in frame['inputs'].items()},
                            expected_output=tensor_binding(t, frame['expected']),
                            original_CPU64_reference=tensor_binding(t, frame['reference']),
                            original_parameters=P.call_parameters(branch),
                            original_metrics=original_metrics[branch])
               for branch, frame in frames.items()}
    return proof, frames, oracle, binding


def prepare_cpu(source_ref, output_dir):
    need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0' and
         os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == '' and
         not list(Path('/dev').glob('davinci*')), 'actual Devices[] CPU preflight only')
    manifest = P.source(source_ref)
    import torch as t
    t.set_num_threads(1)
    proof, frames, oracle, binding = load_inputs(t, manifest)
    result = dict(schema='bole.fia-fixed-frame-input-binding/v1', source=source_ref,
                  probe_plan_ref=manifest['probe_plan_ref'], original_raw=P.RAW,
                  original_source=P.SOURCE, original_rank_report=P.RANK_REPORT,
                  previous_rounding=P.PREVIOUS, original_producers=P.PRODUCERS,
                  actual_saved_inputs_checked=True, original_failure_sets_reproduced=True,
                  fixed_cases=P.CASES, branches=binding, qualified=False, NPU=False,
                  original_numeric_failures_unchanged=True)
    for reference in proof['readset']:
        P.checked(reference)
    result_ref = P.write(Path(output_dir)/'INPUT_BINDING.json', result)
    del frames, oracle
    gc.collect()
    return dict(input_binding_ref=result_ref, actual_saved_inputs_checked=True,
                original_failure_sets_reproduced=True, qualified=False, NPU=False)


def actual_abi(t, torch_npu, runtime, source_ref, proof):
    ticket = P.obj(runtime['abi_ticket_ref'])
    need(ticket['source'] == source_ref and ticket['cpu_stage'] == runtime['cpu_stage'],
         'same-source releasedCPU ticket/runtime plan join')
    abi_ref = ticket['actual_abi_ref']
    abi = P.obj(abi_ref)
    need(abi['schema'] == 'bole.actual-FIA-installed-ABI/v115' and abi['source'] == source_ref and
         abi['NPU'] is False and abi['Devices'] == [] and abi['no_device_fds'] is True and
         abi['operator_executed'] is False, 'actual same-source CPU ABI without operator')
    family = {name: str(schema) for name, schema in t.ops.npu.npu_fused_infer_attention_score._schemas.items()}
    need(family == abi['schema_family'] == proof['original_abi']['schema_family'],
         'actual dispatcher family equals same-image CPU ticket and original R6 ABI')
    for key, actual in (('torch_python_ref', P.ref(t.__file__)),
                        ('torch_npu_python_ref', P.ref(torch_npu.__file__))):
        need(abi[key] == proof['original_abi'][key] == actual, 'same original actual torch module bytes')
    need(abi['header_ref'] == proof['original_abi']['header_ref'], 'same original CANN header')
    P.checked(abi['header_ref'])
    return abi_ref


def write_raw(t, output_dir, name, value):
    path = output_dir/(name+'.pt')
    with path.open('xb') as handle:
        t.save(value, handle)
        handle.flush()
        os.fsync(handle.fileno())
    need(path.stat().st_size <= 16*2**20 and
         sum(p.stat().st_size for p in output_dir.iterdir() if p.is_file()) <= 64*2**20,
         'original component raw64MiB ceiling')
    return P.ref(path)


def one_call(t, torch_npu, source_ref, runtime_ref, output_dir, frame, oracle,
             branch, intervention, work_deadline):
    deadline(work_deadline)
    role = 'intervention' if intervention else 'baseline'
    name = branch+'-'+role
    parameters = P.call_parameters(branch, intervention)
    row = dict(branch=branch, role=role, parameters=parameters, primary=None,
               operator_completed=False, transfer_and_inputs_unchanged=False,
               original_failure_sets_reproduced=False)
    device = {}
    readback = {}
    output = None
    try:
        device = {key: value.to('npu:0') for key, value in frame['inputs'].items()}
        readback = {key: value.cpu() for key, value in device.items()}
        need(all(bits(t, readback[key], value) and
                 tuple(device[key].shape) == tuple(value.shape) and
                 tuple(device[key].stride()) == tuple(value.stride()) and
                 device[key].dtype == value.dtype for key, value in frame['inputs'].items()),
             'exact original whole input transfer/layout')
        deadline(work_deadline)
        pair = torch_npu.npu_fused_infer_attention_score(**device, **parameters)
        t.npu.synchronize()
        output = pair[0].cpu()
        expected_shape = (1, 6, 3, 256) if branch == 'tree' else (1, 6, 1, 256)
        require_tensor(t, output, expected_shape, t.bfloat16, contiguous=False)
        need(all(bits(t, device[key].cpu(), value) for key, value in frame['inputs'].items()),
             'FIA does not modify original input/mask/table')
        row['transfer_and_inputs_unchanged'] = True
        row['operator_completed'] = True
        row['whole_output'] = words_comparison(tensor_words(t, output),
                                                tensor_words(t, frame['expected']))
        row['output_binding'] = tensor_binding(t, output)
        row['metrics'] = output_metrics(t, output, branch, frame, oracle)
        row['original_failure_sets_reproduced'] = original_sets(row['metrics'], branch)
        if intervention:
            row['sole_change'] = parameter_delta(P.call_parameters(branch), parameters)
    except Exception as error:
        row['primary'] = dict(error=repr(error), traceback=traceback.format_exc())
    finally:
        raw = dict(schema='bole.fia-fixed-frame-call-raw/v1', source=source_ref,
                   runtime_plan=runtime_ref, original_raw=P.RAW, branch=branch, role=role,
                   parameters=parameters, inputs=readback, output=output, primary=row['primary'],
                   qualified=False)
        row['raw'] = write_raw(t, output_dir, name, raw)
        row['receipt'] = P.write(output_dir/(name+'.json'), row)
        del device, readback, output
        gc.collect()
    return row


def run(source_ref, plan_ref, output_dir, *, work_deadline, actual_arm_verified=False):
    need(actual_arm_verified is True, 'actual existing singleton owner MAIN_ARM required')
    deadline(work_deadline)
    manifest = P.source(source_ref)
    runtime = P.obj(plan_ref)
    need(runtime['schema'] == 'bole.fia-replay-plan/v1' and runtime['source'] == source_ref and
         runtime['physical'] == 4 and runtime['logical'] == 0 and
         runtime['qualification'] is False, 'exact source-bound independent microprobe plan')
    output_dir = Path(output_dir)
    need(output_dir.is_absolute() and output_dir.is_dir() and not any(output_dir.iterdir()) and
         not any(p.is_symlink() for p in (output_dir, *output_dir.parents)),
         'fresh empty owned probe result leaf')
    import torch as t
    import torch_npu
    t.set_num_threads(1)
    need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == '0' and
         os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0' and
         t.npu.current_device() == 0 and t.npu.matmul.allow_hf32 is False,
         'already-established original singleton visibility and HF32OFF')
    proof, frames, oracle, binding = load_inputs(t, manifest)
    abi_ref = actual_abi(t, torch_npu, runtime, source_ref, proof)
    baselines, interventions = [], []
    for branch in ('tree', 'native'):
        row = one_call(t, torch_npu, source_ref, plan_ref, output_dir, frames[branch],
                       oracle, branch, False, work_deadline)
        baselines.append(row)
        if row['primary'] is not None:
            break
    gate = baseline_gate(baselines)
    baselines_ref = P.write(output_dir/'BASELINES.json', dict(source=source_ref,
                         baseline_gate_pass=gate, rows=baselines,
                         intervention_executed=False, qualified=False))
    if gate:
        for branch in ('tree', 'native'):
            row = one_call(t, torch_npu, source_ref, plan_ref, output_dir, frames[branch],
                           oracle, branch, True, work_deadline)
            interventions.append(row)
            if row['primary'] is not None:
                break
    complete = (len(baselines) == 2 and all(row['primary'] is None for row in baselines) and
                (not gate or len(interventions) == 2 and
                 all(row['primary'] is None for row in interventions)))
    primary = next((row['primary'] for row in [*baselines, *interventions]
                    if row['primary'] is not None), None)
    result = dict(schema=SCHEMA, source=source_ref, runtime_plan=plan_ref,
                  probe_plan_ref=manifest['probe_plan_ref'], actual_abi_ref=abi_ref,
                  original_source=P.SOURCE, original_raw=P.RAW,
                  original_rank_report=P.RANK_REPORT, previous_rounding=P.PREVIOUS,
                  original_producers=P.PRODUCERS, input_binding=binding,
                  fixed_cases=P.CASES, baselines_ref=baselines_ref,
                  baselines=baselines, interventions=interventions,
                  baseline_gate_pass=gate, intervention_executed=bool(interventions),
                  diagnostic_complete=complete, primary=primary, replay_qualified=False,
                  qualified=False, NPU=True, original_numeric_failures_unchanged=True,
                  original_tree_gate_called_without_modification=True,
                  original_pointwise_bound='.001+.01*abs(original_CPU64)',
                  native_reference_is_diagnostic_only=True,
                  inner_precise_numeric_semantics=None, kernel_internal_precision_proven=False,
                  kernel_path_proven=False, whole_model_qualified=False,
                  model_ready=False, performance_ready=False, task_ready=False,
                  scheduler_committed=False,
                  scope='same retained rank1/layer43 full tree and native path2/node2 FIA calls only')
    for reference in proof['readset']:
        P.checked(reference)
    probe_ref = P.write(output_dir/'PROBE.json', result)
    del frames, oracle
    gc.collect()
    return dict(schema=SCHEMA, source=source_ref, plan=plan_ref, result=probe_ref,
                actual_abi_ref=abi_ref, baseline_gate_pass=gate,
                intervention_executed=bool(interventions), diagnostic_complete=complete,
                primary=primary, qualified=False, replay_qualified=False, NPU=True)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--source-ref')
    parser.add_argument('--plan-ref')
    parser.add_argument('--output')
    args = parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false,"qualified":false}')
        return 0
    raise ValueError('bare-device CLI forbidden; source-owned guest calls run only after actual MAIN_ARM')


if __name__ == '__main__':
    raise SystemExit(main())
