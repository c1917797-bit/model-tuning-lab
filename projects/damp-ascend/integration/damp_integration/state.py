"""Transient prefill packing in the exact operator value-major ABI."""
from .contract import RECIPROCAL_127_FP32, require

def pack_native(state, plan, torch):
    require(tuple(state.shape) == (1, 12, 128, 128), "prefill scratch must contain one state only")
    # Native [B,Hv,V,K] -> SR/value and key permutation; no retained dense cache.
    t = state.float() / plan.sr[None, :, :, None]
    t = torch.gather(t, 2, plan.pv[None, :, :, None].long().expand_as(t))
    t = torch.gather(t, 3, plan.pk[None, :, None, :].long().expand_as(t))
    high = t[..., :16].to(torch.float16).contiguous()
    groups = t[..., 16:].reshape(1, 12, 4, 32, 112)
    amax = groups.abs().amax(dim=3)
    scales = torch.where(amax == 0, torch.ones_like(amax), amax * RECIPROCAL_127_FP32)
    require(bool(torch.isfinite(high).all().item()), "prefill FP16 high overflow/nonfinite")
    require(bool((torch.isfinite(scales) & (scales > 0)).all().item()),
            "prefill low scales overflow/underflow/nonfinite")
    low = (groups / scales.unsqueeze(3)).round().clamp(-127, 127).to(torch.int8).reshape(1, 12, 128, 112).contiguous()
    return high, low, scales.contiguous()

def cache_contract(states, torch):
    require(len(states) == 4, "persistent GDN cache must contain four typed states")
    conv, high, low, scales = states
    slots = int(conv.shape[0])
    expected = (((slots, 12, 128, 16), torch.float16),
                ((slots, 12, 128, 112), torch.int8),
                ((slots, 12, 4, 112), torch.float32))
    require(conv.dtype == torch.bfloat16 and tuple(conv.shape[1:]) in ((3, 2560), (2560, 3)),
            "native conv state changed")
    for tensor, (shape, dtype) in zip(states[1:], expected):
        require(tuple(tensor.shape) == shape and tensor.dtype == dtype and tensor.is_contiguous(),
                "packed cache shape/dtype/contiguity mismatch")
    require(all(s.device == conv.device for s in states), "typed cache device mismatch")
    spans = sorted((s.data_ptr(), s.data_ptr() + s.numel() * s.element_size()) for s in states)
    require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), "typed state buffers alias")
    return slots

