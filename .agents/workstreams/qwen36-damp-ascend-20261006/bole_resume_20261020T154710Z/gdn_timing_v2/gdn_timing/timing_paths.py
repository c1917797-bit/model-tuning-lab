"""Pure computation factories. No imports, guards, copies or clocks in units.

All operands, sources, exact compiled handles and output equivalence must be
validated by time_gdn.py before a unit is called in a measured region.
"""


def strides(value):
    return tuple(int(v) for v in value.stride())


def original_unit(t, core, inputs, ancestor, inclusive, terminal):
    q, k, v, beta, gamma, state = (inputs[n] for n in ('q', 'k', 'v', 'beta', 'gamma', 'state'))

    def call():
        output, factors = core.verify(t, q, k, v, beta, gamma, state, ancestor, 1)
        selected = core.commit(t, state, k, factors, inclusive, terminal)
        return dict(O=output, P=factors[0], U=factors[1], S=selected)
    return call


def source_factors(t, ancestor, gamma):
    # Exact wrapper/core expression; this is recomputed on EVERY invocation.
    mask = ancestor.to(dtype=t.float32, device=gamma.device)
    inclusive = mask + t.eye(3, device=gamma.device, dtype=t.float32)
    logg = gamma.log()
    p = t.exp(t.matmul(logg, inclusive.transpose(-1, -2)))
    ratio = p.unsqueeze(-1) / p.unsqueeze(-2)
    return p, ratio


def jit_probe(t, kernels, inputs, ancestor, terminal, admit):
    """Untimed only: exact wrapper launch arguments plus returned actual handles."""
    q, k, v, beta, gamma, state = (inputs[n] for n in ('q', 'k', 'v', 'beta', 'gamma', 'state'))
    p, ratio = source_factors(t, ancestor, gamma)
    output = t.empty((1, 12, 3, 128), dtype=t.float32, device=q.device)
    updates = t.empty_like(output)
    forward_args = (q, k, v, beta, p, ratio, state, output, updates,
                    *strides(q), *strides(k), *strides(v), *strides(beta),
                    *strides(p), *strides(ratio), *strides(state))
    forward_kwargs = dict(H=12, DV=128, TILE_V=32)
    admit(kernels.forward_ou, forward_args, forward_kwargs)
    forward = kernels.forward_ou[(12, 4)](*forward_args, **forward_kwargs)
    weights = p[..., terminal:terminal + 1] / p
    selected = t.empty((1, 12, 128, 128), dtype=t.float32, device=q.device)
    selected_args = (state, k, p, weights, updates, selected,
                     *strides(state), *strides(k), *strides(p), *strides(weights), *strides(updates))
    selected_kwargs = dict(H=12, DK=128, DV=128, TILE_K=32, TILE_V=32, TERMINAL=terminal)
    admit(kernels.selected_state, selected_args, selected_kwargs)
    commit = kernels.selected_state[(12, 4, 4)](*selected_args, **selected_kwargs)
    return dict(O=output, P=p, U=updates, S=selected), (forward, commit)


def compiled_unit(t, forward_runner, selected_runner, inputs, ancestor, terminal):
    """Same Torch factor/ratio/allocation work; two already validated binaries.

    The compiled runners come from the actual JIT handles used by the guarded
    wrapper, so this unit cannot compile a new specialization during timing.
    """
    q, k, v, beta, gamma, state = (inputs[n] for n in ('q', 'k', 'v', 'beta', 'gamma', 'state'))

    def call():
        p, ratio = source_factors(t, ancestor, gamma)
        output = t.empty((1, 12, 3, 128), dtype=t.float32, device=q.device)
        updates = t.empty_like(output)
        forward_runner(q, k, v, beta, p, ratio, state, output, updates)
        weights = p[..., terminal:terminal + 1] / p
        selected = t.empty((1, 12, 128, 128), dtype=t.float32, device=q.device)
        selected_runner(state, k, p, weights, updates, selected)
        return dict(O=output, P=p, U=updates, S=selected)
    return call
