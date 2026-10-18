"""Retained-input CPU probability-quantization probe; never an acceptance gate.

The two predictions share QK, softmax, the PV summation and final BF16 rounding.
Their only difference is rounding P64 to BF16, then widening it to Python FP64.
Probability rounding is not followed by renormalization.
"""
import gc
import hashlib
import json
import math
import struct

SCALE = 0.0625
ATOL = 0.001
RTOL = 0.01


def need(condition, message):
    if not condition:
        raise ValueError(message)


def nearest_bf16(value):
    """Return (bits, exact value), with nearest-even FP64-to-BF16 rounding.

Inspect neighbors of the FP32 seed so a midpoint is not decided by double
rounding through FP32. Inputs here are finite probabilities or BF16-bounded
attention outputs; infinities and out-of-range inputs are rejected.
"""
    need(math.isfinite(value), "finite BF16-rounding input")
    need(abs(value) <= struct.unpack('>f', struct.pack('>I', 0x7f7f0000))[0],
         "BF16-rounding input exceeds finite BF16 range")
    if value == 0.0:
        word = 0x8000 if math.copysign(1.0, value) < 0 else 0
        return word, math.copysign(0.0, value)
    try:
        seed = struct.unpack(">I", struct.pack(">f", value))[0] >> 16
    except OverflowError as error:
        raise ValueError("BF16-rounding input exceeds finite FP32 range") from error
    candidates = []
    for word in range(max(0, seed - 2), min(65535, seed + 2) + 1):
        represented = struct.unpack(">f", struct.pack(">I", word << 16))[0]
        if math.isfinite(represented):
            candidates.append((abs(represented - value), word & 1,
                               word, represented))
    need(bool(candidates), "finite BF16 neighbor exists")
    _, _, word, represented = min(candidates)
    return word, represented


def probabilities64(query, keys):
    need(bool(query) and bool(keys), "nonempty query and keys")
    need(all(len(row) == len(query) for row in keys), "QK dimensions")
    need(all(math.isfinite(x) for row in [query, *keys] for x in row),
         "finite QK values")
    scores = [math.fsum(a * b for a, b in zip(query, row)) * SCALE
              for row in keys]
    need(all(math.isfinite(x) for x in scores), "finite FP64 scores")
    peak = max(scores)
    exponentials = [math.exp(x - peak) for x in scores]
    denominator = math.fsum(exponentials)
    need(denominator > 0 and math.isfinite(denominator), "finite softmax denominator")
    return [x / denominator for x in exponentials]


def pv64(probabilities, values):
    need(bool(values) and len(probabilities) == len(values), "PV token join")
    width = len(values[0])
    need(width > 0 and all(len(row) == width for row in values), "PV dimensions")
    need(all(math.isfinite(x) for row in values for x in row), "finite V values")
    return [math.fsum(p * row[channel] for p, row in zip(probabilities, values))
            for channel in range(width)]


def digest64(values):
    digest = hashlib.sha256()
    for value in values:
        digest.update(struct.pack(">d", value))
    return digest.hexdigest()


def flatten(rows):
    return [value for row in rows for value in row]


def reference_comparison(values, truth):
    need(len(values) == len(truth) and bool(values), "reference dimensions")
    errors = [abs(value - ref) for value, ref in zip(values, truth)]
    bounds = [ATOL + RTOL * abs(ref) for ref in truth]
    failed = [index for index, (error, bound) in enumerate(zip(errors, bounds))
              if error > bound]
    norm = math.sqrt(math.fsum(ref * ref for ref in truth))
    return dict(elements=len(values), failed_elements=len(failed),
                failed_flat_indices=failed, max_absolute_error=max(errors),
                relative_l2=math.sqrt(math.fsum(x * x for x in errors)) / max(norm, 1e-30))


def actual_comparison(values, actual):
    differences = [left - right for left, right in zip(values, actual)]
    need(len(values) == len(actual) and bool(values), "actual-output dimensions")
    return dict(elements=len(values),
                bitwise_equal_elements=sum(nearest_bf16(left)[0] == nearest_bf16(right)[0]
                                           for left, right in zip(values, actual)),
                max_absolute_error=max(abs(x) for x in differences),
                l2_error=math.sqrt(math.fsum(x * x for x in differences)))


def evaluate_paths(queries, keys, values, actual):
    """Pure-Python arithmetic; the production caller checks the tensor shapes."""
    need(bool(queries) and len(queries) == len(actual), "head count")
    need(bool(values) and bool(values[0]), "nonempty values")
    need(len(keys) == len(values), "original KV token join")
    need(all(len(row) == len(values[0]) for row in actual), "output width")
    need(all(math.isfinite(x) and nearest_bf16(x)[1] == x
             for row in [*queries, *keys, *values, *actual] for x in row),
         "retained inputs and output must be finite BF16 values")
    reference, rounded_probability_output, probability_rows = [], [], []
    for query in queries:
        p64 = probabilities64(query, keys)
        p_bf16 = [nearest_bf16(value)[1] for value in p64]
        reference.append(pv64(p64, values))
        rounded_probability_output.append(pv64(p_bf16, values))
        probability_rows.append(dict(
            probability64_sha256=digest64(p64),
            probability_bf16_widened_sha256=digest64(p_bf16),
            probability64_sum=math.fsum(p64),
            probability_bf16_sum=math.fsum(p_bf16),
            probability_max_abs_delta=max(abs(a - b) for a, b in zip(p64, p_bf16)),
            probability_l1_delta=math.fsum(abs(a - b) for a, b in zip(p64, p_bf16)),
            changed_probabilities=sum(a != b for a, b in zip(p64, p_bf16))))
    truth = flatten(reference)
    baseline = [nearest_bf16(x)[1] for x in truth]
    intervention = [nearest_bf16(x)[1] for x in flatten(rounded_probability_output)]
    observed = flatten(actual)
    original = reference_comparison(observed, truth)
    final_only = dict(reference=reference_comparison(baseline, truth),
                      actual=actual_comparison(baseline, observed))
    probability_rounded = dict(reference=reference_comparison(intervention, truth),
                               actual=actual_comparison(intervention, observed))
    width = len(values[0])
    failed_points = []
    for index in original['failed_flat_indices']:
        failed_points.append(dict(
            head=index // width, channel=index % width,
            original_actual=observed[index], reference_compensated64=truth[index],
            bound=ATOL + RTOL * abs(truth[index]),
            final_only_bf16=baseline[index], probability_bf16=intervention[index],
            final_only_actual_error=abs(baseline[index] - observed[index]),
            probability_bf16_actual_error=abs(intervention[index] - observed[index]),
            intervention_exact_actual_bits=(nearest_bf16(intervention[index])[0] ==
                                            nearest_bf16(observed[index])[0])))
    return dict(original_actual=original, final_only_bf16=final_only,
                probability_bf16=probability_rounded, probability_heads=probability_rows,
                intervention_changed_output_elements=sum(nearest_bf16(a)[0] != nearest_bf16(b)[0]
                                                         for a, b in zip(baseline, intervention)),
                failed_points=failed_points,
                reference64_sha256=digest64(truth), renormalized_after_probability_rounding=False)


def tensor_bits_equal(torch, left, right):
    return (left.shape == right.shape and left.dtype == right.dtype and
            torch.equal(left.contiguous().view(torch.uint8),
                        right.contiguous().view(torch.uint8)))


def tensor_digest(torch, value):
    data = bytes(value.contiguous().view(torch.uint8).reshape(-1).tolist())
    return dict(shape=list(value.shape), dtype=str(value.dtype), bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest())


def retained_cases(torch, raw, plan):
    """Use original candidate-own-input and native-own-input frames, unchanged."""
    need(raw['schema'] == 'bole.actual-three-node-model-capture/v1' and
         raw['scheduler_committed'] is False and raw['rank'] == 1 and
         raw['source'] == plan['source'], 'original R6 raw identity')
    layer = 43
    row = raw['tree_context']['captures'][layer]
    saved = row['trial']['native_before']
    anchors = [value for value in raw['initial_FA_pages'] if value['layer'] == layer]
    need(len(anchors) == 1, 'one original FA prefix anchor')
    anchor = anchors[0]
    query = saved['query'].squeeze(0).permute(1, 0, 2)
    mask = saved['atten_mask'][0, 0]
    need(query.shape == (3, 6, 256) and mask.shape == (3, 256) and
         mask.dtype == torch.bool and saved['block_table'].tolist() == [[0, 1]] and
         saved['key'].shape == saved['value'].shape == (2, 1, 128, 256),
         'original page table, Q shape and boolean tree mask')
    keys = saved['key'].permute(0, 2, 1, 3).reshape(256, 256)
    values = saved['value'].permute(0, 2, 1, 3).reshape(256, 256)
    prefix_k = torch.stack([anchor['key'][n // 128, n % 128, 0] for n in range(131)])
    prefix_v = torch.stack([anchor['value'][n // 128, n % 128, 0] for n in range(131)])
    canonical = torch.ones_like(mask)
    canonical[:, :132] = False
    canonical[1, 132] = False
    canonical[2, 133] = False
    need(tensor_bits_equal(torch, mask, canonical) and
         tensor_bits_equal(torch, query, row['query'].reshape(3, 6, 256)) and
         tensor_bits_equal(torch, keys[:134], torch.cat((prefix_k, row['key'].reshape(3, 256)))) and
         tensor_bits_equal(torch, values[:134], torch.cat((prefix_v, row['value'].reshape(3, 256)))),
         'bitwise original query/prefix/ancestor joins; no input repair')
    selected = []
    for case in plan['cases']:
        if case['kind'] == 'tree':
            node = case['node']
            tensors = (query[node], keys[~mask[node]], values[~mask[node]], row['output'][node])
            selection = dict(kind='tree', node=node, full_mask=tensor_digest(torch, mask),
                             block_table=saved['block_table'].tolist(), original_prefix_tokens=131)
        else:
            paths = [path for path in raw['native'] if path['child'] == case['path']]
            need(len(paths) == 1, 'one fixed original native path')
            steps = [step for step in paths[0]['steps'] if step['node'] == case['node']]
            need(len(steps) == 1, 'one fixed original native step')
            capture = steps[0]['context']['captures'][layer]
            tensors = (capture['query'].reshape(6, 256),
                       capture['after_key'].reshape(-1, 256),
                       capture['after_value'].reshape(-1, 256),
                       capture['output'].reshape(6, 256))
            selection = dict(kind='native', path=case['path'], node=case['node'],
                             causal_prefix='all tokens in this exact native step after_key/after_value')
        q, k, v, output = tensors
        need(q.shape == output.shape == (6, 256) and
             k.shape == v.shape == (case['key_tokens'], 256), 'fixed selected case shapes')
        need(all(x.device.type == 'cpu' and x.dtype == torch.bfloat16 and
                 bool(torch.isfinite(x).all()) for x in tensors), 'finite original CPU BF16 tensors')
        selection['scale'] = SCALE
        selection['tensors'] = {name: tensor_digest(torch, value)
                                for name, value in zip(('q', 'k', 'v', 'actual'), tensors)}
        selected.append((case, tensors, selection))
    return selected


def run_retained(torch, raw, plan, previous):
    need((SCALE, ATOL, RTOL) == (plan['scale'], plan['atol'], plan['rtol']),
         'exact preregistered scale/atol/rtol')
    previous_rows = [row for row in previous['rows'] if row['layer'] == 43]
    need(len(previous_rows) == 1, 'one fixed previous diagnostic layer')
    previous_row = previous_rows[0]
    results = []
    for case, tensors, selection in retained_cases(torch, raw, plan):
        group = 'tree' if case['kind'] == 'tree' else 'native_own_inputs'
        old_rows = [row for row in previous_row[group] if row['label'] == case['label']]
        need(len(old_rows) == 1, 'one fixed previous diagnostic node')
        old = old_rows[0]
        q, k, v, output = tensors
        diagnostic = evaluate_paths(q.double().tolist(), k.double().tolist(),
                                    v.double().tolist(), output.double().tolist())
        need(diagnostic['original_actual']['elements'] == 1536 and
             diagnostic['original_actual']['failed_elements'] == case['original_failed_elements'] and
             old['failed'] == old['compensated_failed'] == case['original_failed_elements'] and
             old['failed_set_changed'] is False, 'exact retained original failure/pass counts')
        new_points = {(point['head'], point['channel']): point
                      for point in diagnostic['failed_points']}
        old_points = {(point['head'], point['channel']): point for point in old['failed_values']}
        need(set(new_points) == set(old_points), 'same original failing element identities')
        for key, point in new_points.items():
            old_point = old_points[key]
            need(point['original_actual'] == old_point['actual'] and
                 abs(point['reference_compensated64'] - old_point['compensated_CPU64']) <= 1e-12,
                 'same retained values and independent compensated reference')
        need(diagnostic['final_only_bf16']['reference']['failed_elements'] == 0,
             'final-only rounding control meets unchanged bound')
        results.append(dict(case=case, input_binding=selection, diagnostic=diagnostic))
    gc.collect()
    return dict(schema='bole.fa-probability-quantization-three-case/v1',
                cases=results, diagnostic_complete=True, cases_completed=3,
                diagnostic_pointwise_bound='.001+.01*abs(compensated_CPU64)',
                original_pointwise_bound='.001+.01*abs(original_CPU64)',
                original_CPU64_gate_unchanged=True, atol_rtol_unchanged=True,
                compensated_oracle_is_diagnostic_not_replacement=True,
                sole_intervention='P64 -> nearest-even BF16 -> FP64; no renormalization',
                QK_and_softmax='independent Python FP64 products/math.fsum/math.exp',
                PV_both_arms='Python FP64 products/math.fsum',
                final_rounding_both_arms='nearest-even BF16',
                original_numeric_failures_unchanged=True, qualified=False, NPU=False,
                kernel_path_proven=False, full_model_performance=False,
                diagnostic_match_is_not_kernel_causality=True)
