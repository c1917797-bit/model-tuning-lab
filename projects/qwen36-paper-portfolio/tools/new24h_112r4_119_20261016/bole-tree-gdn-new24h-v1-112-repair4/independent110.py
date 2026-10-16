"""Paper-derived CPU checks, not an official Bole implementation or NPU kernel."""
import math


def topology(parents):
    if not parents or len(parents) > 256:
        raise ValueError('bounded nonempty tree')
    paths = []
    for i, p in enumerate(parents):
        if type(p) is not int or not -1 <= p < i:
            raise ValueError('parent-before-child; -1 denotes committed prefix')
        paths.append(([] if p == -1 else paths[p]) + [i])
    return paths


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b))


def validate(parents, q, k, v, beta, gamma, state):
    paths = topology(parents)
    n, dk, dv = len(parents), len(state), len(state[0])
    if not dk or not dv or any(len(row) != dv for row in state):
        raise ValueError('state shape')
    if any(len(x) != n for x in (q, k, v, beta, gamma)):
        raise ValueError('node shape')
    if any(len(row) != dk for rows in (q, k) for row in rows) or any(len(row) != dv for row in v):
        raise ValueError('operand shape')
    scalars = [x for rows in (q, k, v, state) for row in rows for x in row] + list(beta) + list(gamma)
    if not all(math.isfinite(x) for x in scalars) or any(x <= 0 for x in gamma):
        raise ValueError('finite operands and positive decay')
    return paths, dk, dv


def sequential(parents, q, k, v, beta, gamma, state):
    paths, dk, dv = validate(parents, q, k, v, beta, gamma, state)
    states, outputs = [], []
    for i, p in enumerate(parents):
        before = state if p == -1 else states[p]
        decayed = [[gamma[i]*x for x in row] for row in before]
        u = [beta[i]*(v[i][c]-dot(k[i], [decayed[r][c] for r in range(dk)])) for c in range(dv)]
        after = [[decayed[r][c]+k[i][r]*u[c] for c in range(dv)] for r in range(dk)]
        states.append(after)
        outputs.append([dot(q[i], [after[r][c] for r in range(dk)]) for c in range(dv)])
    return outputs, states


def closed_form(parents, q, k, v, beta, gamma, state):
    paths, dk, dv = validate(parents, q, k, v, beta, gamma, state)
    n = len(parents)
    products = [math.prod(gamma[j] for j in path) for path in paths]
    if any(p == 0 or not math.isfinite(p) for p in products):
        raise ValueError('decay product numeric range; no silent division underflow')
    g = [[beta[i]*products[i]/products[j]*dot(k[i], k[j]) if j in paths[i][:-1] else 0.0 for j in range(n)] for i in range(n)]
    cmat = [[products[i]/products[j]*dot(q[i], k[j]) if j in paths[i] else 0.0 for j in range(n)] for i in range(n)]
    residual = [[beta[i]*(v[i][c]-products[i]*dot(k[i], [state[r][c] for r in range(dk)])) for c in range(dv)] for i in range(n)]
    # Depth rounds of all-node matrix propagation, NOT a parent recurrence.
    z = [row[:] for row in residual]
    u = [row[:] for row in residual]
    for _ in range(max(map(len, paths))-1):
        z = [[-math.fsum(g[i][j]*z[j][c] for j in range(n)) for c in range(dv)] for i in range(n)]
        u = [[u[i][c]+z[i][c] for c in range(dv)] for i in range(n)]
    outputs = [[products[i]*dot(q[i], [state[r][c] for r in range(dk)]) + math.fsum(cmat[i][j]*u[j][c] for j in range(n)) for c in range(dv)] for i in range(n)]
    return outputs, {'parents': list(parents), 'paths': paths, 'P': products, 'K': k, 'U': u}


def commit(state, factors, accepted_terminal):
    if accepted_terminal is None:
        return [row[:] for row in state]
    paths = topology(factors['parents'])
    if type(accepted_terminal) is not int or not 0 <= accepted_terminal < len(paths):
        raise ValueError('accepted terminal')
    a = accepted_terminal
    p, k, u = factors['P'], factors['K'], factors['U']
    return [[p[a]*state[r][c] + math.fsum((p[a]/p[j])*k[j][r]*u[j][c] for j in paths[a]) for c in range(len(state[0]))] for r in range(len(state))]


def tree_conv(tokens, parents, history, weights, bias):
    """Independent path gather: weights oldest-to-current; no flattened siblings."""
    paths = topology(parents)
    width = len(weights)
    if not width or len(history) < width-1:
        raise ValueError('convolution history')
    return [dot((history+[tokens[j] for j in path])[-width:], weights)+bias for path in paths]
