"""Independent CPU path oracle: does not consume candidate scratch or mask."""


def sequential(t, q, k, v, committed_k, committed_v, block_table, prefix_length, *, dtype):
    assert q.device.type == k.device.type == v.device.type == committed_k.device.type == committed_v.device.type == 'cpu'
    assert q.shape == (3, 6, 256) and k.shape == v.shape == (3, 1, 256)
    result = t.empty_like(q, dtype=dtype)
    # Independently walk original physical prefix pages, then only each path.
    prefix_k = t.stack([committed_k[block_table[p // 128], p % 128, 0] for p in range(prefix_length)]) if prefix_length else t.empty((0, 256))
    prefix_v = t.stack([committed_v[block_table[p // 128], p % 128, 0] for p in range(prefix_length)]) if prefix_length else t.empty((0, 256))
    for node, path in enumerate(((0,), (0, 1), (0, 2))):
        keys = t.cat((prefix_k, t.stack([k[x, 0] for x in path]))).to(dtype)
        values = t.cat((prefix_v, t.stack([v[x, 0] for x in path]))).to(dtype)
        for head in range(6):
            logits = keys.mv(q[node, head].to(dtype)) * (256 ** -.5)
            probability = (logits - logits.max()).exp()
            probability /= probability.sum()
            result[node, head] = values.t().mv(probability)
    return result


def assess(t, output, reference64, reference32):
    if output.shape != (3, 6, 256) or output.dtype != t.bfloat16:
        raise ValueError('actual BF16 TND ABI')
    rows = []
    for node in range(3):
        observed = output[node].double()
        rows.append(dict(node=node, finite=bool(t.isfinite(observed).all()),
                         double_allclose=bool(t.all((observed-reference64[node]).abs() <= .001+.01*reference64[node].abs())),
                         float_allclose=bool(t.all((observed-reference32[node].double()).abs() <= .001+.01*reference32[node].double().abs())),
                         peak_abs=float((observed-reference64[node]).abs().max())))
    return dict(schema='bole.paged-tree-independent/v1', rows=rows,
                component_pass=all(r['finite'] and r['double_allclose'] and r['float_allclose'] for r in rows),
                model_ready=False, qualified=False)
