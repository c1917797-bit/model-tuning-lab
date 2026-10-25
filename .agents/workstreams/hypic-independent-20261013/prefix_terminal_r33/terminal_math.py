"""Own prefix terminal-only recurrence; state arithmetic identical to retained reference."""
import torch
def terminal_boundary(q,k,v,log_decay,beta,initial_state,*,input_observer=None,hoist_gate_casts=False,gate_cast_observer=None):
    if type(hoist_gate_casts)is not bool:
        raise ValueError("explicit gate-cast placement boolean required")
    if gate_cast_observer is not None and not callable(gate_cast_observer):
        raise ValueError("callable gate-cast observer required")
    if q.shape!=k.shape or q.ndim!=4 or q.shape[0]!=1:
        raise ValueError("single-span query/key shape required")
    length=q.shape[1];hv=v.shape[2];hk=k.shape[2];dk=k.shape[3]
    if not 1<=length<=64 or hv%hk or v.shape[:2]!=(1,length):
        raise ValueError("bounded grouped-head token coverage required")
    if beta.shape!=(1,length,hv) or log_decay.shape!=beta.shape:
        raise ValueError("boundary gates mismatch")
    if initial_state.shape!=(1,hv,dk,v.shape[3]):
        raise ValueError("key-major boundary state mismatch")
    dtype=torch.float64 if q.dtype==torch.float64 else torch.float32
    def norm(x):
        y=x.to(dtype);y=y*torch.rsqrt((y*y).sum(-1,keepdim=True)+1e-6)
        return y.to(x.dtype).to(dtype)
    keys=norm(k).repeat_interleave(hv//hk,dim=2)[0]
    queries=norm(q).repeat_interleave(hv//hk,dim=2)[0]
    if input_observer is not None:
        input_observer(q=queries[None],k=keys[None],v=v,g=log_decay,beta=beta,
                       initial=initial_state,branch="independent_recurrent_le64")
    values=v[0].to(dtype);state=initial_state[0].to(dtype).clone();outputs=[]
    # Only conversion placement changes; each token's arithmetic order is retained.
    dispatches=0
    if hoist_gate_casts:
        decay_values=log_decay[0].to(dtype);gate_values=beta[0].to(dtype)
        dispatches=2
    for i in range(length):
        key=keys[i]
        if hoist_gate_casts:
            decay=decay_values[i].exp()[:,None,None]
            gate=gate_values[i][:,None,None]
        else:
            decay=log_decay[0,i].to(dtype).exp()[:,None,None]
            gate=beta[0,i].to(dtype)[:,None,None]
            dispatches+=2
        # Low-rank token update, independently derived (not chunk-output reuse).
        prediction=key.unsqueeze(-2)@state
        state=decay*(state-gate*key.unsqueeze(-1)*prediction)
        state=state+gate*key.unsqueeze(-1)*values[i].unsqueeze(-2)
    result=None,state[None]
    if gate_cast_observer is not None:
        gate_cast_observer({"length":length,"hoisted":hoist_gate_casts,
            "gate_conversion_dispatch_sites":dispatches,
            "gate_conversion_elements":2*length*hv,
            "accumulation_dtype":str(dtype),
            "log_decay_dtype":str(log_decay.dtype),"beta_dtype":str(beta.dtype),
            "scope":"source-executed Tensor.to dispatch sites, not hardware memcpy count"})
    return result
