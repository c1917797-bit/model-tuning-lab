"""Independent C2/conv mathematical references, not serving hooks."""
import torch
import torch.nn.functional as F

def rotate_partial_neox(keys, positions, inv_freq):
    if keys.ndim != 3 or positions.shape != (keys.shape[0],):
        raise ValueError("expected [tokens,heads,dimension] and one position/token")
    if inv_freq.ndim != 1 or 2*inv_freq.numel()>keys.shape[-1]:
        raise ValueError("invalid rotary dimensions")
    dtype=torch.float64 if keys.dtype==torch.float64 else torch.float32
    half=inv_freq.numel()
    angles=positions.to(dtype)[:,None]*inv_freq.to(dtype)[None,:]
    cosine,sine=angles.cos()[:,None,:],angles.sin()[:,None,:]
    first=keys[...,:half].to(dtype);second=keys[...,half:2*half].to(dtype)
    result=keys.clone()
    result[...,:half]=(first*cosine-second*sine).to(keys.dtype)
    result[...,half:2*half]=(second*cosine+first*sine).to(keys.dtype)
    return result

def relocate_keys(public_keys, old_positions, new_positions, inv_freq):
    """Create a private key copy; never rotate a shared public cache in place."""
    if old_positions.shape != new_positions.shape:
        raise ValueError("position identity mismatch")
    return rotate_partial_neox(public_keys,new_positions-old_positions,inv_freq)

def causal_conv_reference(inputs, weights, tail=None, bias=None, activation=None):
    """Depthwise causal cross-correlation; weights ordered oldest to newest."""
    if inputs.ndim!=2 or weights.ndim!=2 or inputs.shape[1]!=weights.shape[0]:
        raise ValueError("expected [tokens,channels] and [channels,width]")
    channels,width=weights.shape
    if width<1:raise ValueError("positive width required")
    dtype=torch.float64 if inputs.dtype==torch.float64 else torch.float32
    previous=torch.zeros(width-1,channels,dtype=dtype,device=inputs.device) if tail is None else tail.to(dtype)
    if previous.shape!=(width-1,channels):raise ValueError("conv tail shape mismatch")
    joined=torch.cat((previous,inputs.to(dtype)),dim=0)
    outputs=[]
    for i in range(inputs.shape[0]):
        window=joined[i:i+width]
        value=(window.T*weights.to(dtype)).sum(dim=-1)
        if bias is not None:value=value+bias.to(dtype)
        if activation=="silu":value=F.silu(value)
        elif activation is not None:raise ValueError("unsupported activation")
        outputs.append(value)
    output=torch.stack(outputs) if outputs else torch.empty(0,channels,dtype=dtype,device=inputs.device)
    next_tail=joined[-(width-1):].clone() if width>1 else joined[:0].clone()
    return output.to(inputs.dtype),next_tail
