"""Independent CPU tensor port of110 sequential recurrence, no closed form."""
def sequential(t, q, k, v, beta, gamma, state, parents, *, return_updates=False):
    states=[];outputs=[];updates=[]
    for i,parent in enumerate(parents):
        before=state if parent == -1 else states[parent]
        decayed=gamma[...,i,None,None]*before
        prediction=t.matmul(k[...,i,None,:],decayed).squeeze(-2)
        update=beta[...,i,None]*(v[...,i,:]-prediction)
        updates.append(update)
        after=decayed+k[...,i,:,None]*update.unsqueeze(-2)
        states.append(after)
        outputs.append(t.matmul(q[...,i,None,:],after).squeeze(-2))
    if return_updates:return t.stack(outputs,dim=-2),states,t.stack(updates,dim=-2)
    return t.stack(outputs,dim=-2),states
