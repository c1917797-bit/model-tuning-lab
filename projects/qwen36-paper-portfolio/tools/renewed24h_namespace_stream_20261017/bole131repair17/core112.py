"""Paper-derived all-node GDN; depth loops only, never node recurrence."""
def verify(t, q, k, v, beta, gamma, state, ancestors, depth):
    # [B,H,T,D], [B,H,D,Dv]. GQA expansion occurs before this API.
    b, h, n, dk = q.shape
    mask = ancestors.to(dtype=t.float32, device=q.device)
    inclusive = mask+t.eye(n, device=q.device, dtype=t.float32)
    # Product on each root-to-node path, excluding other requests/siblings.
    logg = gamma.log()
    p = t.exp(t.matmul(logg, inclusive.transpose(-1,-2)))
    ratio = p.unsqueeze(-1)/p.unsqueeze(-2)
    g = beta.unsqueeze(-1)*ratio*t.matmul(k,k.transpose(-1,-2))*mask
    c = ratio*t.matmul(q,k.transpose(-1,-2))*inclusive
    outputs, updates = [], []
    for start in range(0, state.shape[-1], 64):
        s = state[...,start:start+64]
        base = p.unsqueeze(-1)*t.matmul(q,s)
        r = beta.unsqueeze(-1)*(v[...,start:start+64]-p.unsqueeze(-1)*t.matmul(k,s))
        z, u = r, r
        for _ in range(depth):
            z = -t.matmul(g,z)
            u = u+z
        outputs.append(base+t.matmul(c,u));updates.append(u)
    return t.cat(outputs,dim=-1), (p,t.cat(updates,dim=-1))


def commit(t, state, k, factors, inclusive, terminal):
    if terminal is None: return state.clone()
    p,u = factors
    weights = (p[...,terminal:terminal+1]/p)*inclusive[terminal].to(p.device)
    return p[...,terminal,None,None]*state+t.matmul((k*weights.unsqueeze(-1)).transpose(-1,-2),u)
