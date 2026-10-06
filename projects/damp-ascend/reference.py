"""DAMP equation-derived reference, NOT a performance implementation.

Native storage axes are [slot,Hv,Dv,Dk]; quantization groups run along Dv.
Per-Hv key gathers deliberately occur AFTER shared Q/K and nonlinear conv.
No claim of official-source fidelity, fused execution, or vLLM cache integration.
"""
from dataclasses import dataclass
import torch

# IEEE754 FP32 bits0x3c010204; explicit arithmetic contract, not CPU division.
SCALE_RECIPROCAL_FP32 = 0.007874015718698502

@dataclass(frozen=True)
class Layout:
    c: torch.Tensor
    pv: torch.Tensor
    pk: torch.Tensor
    khi: int = 16
    group: int = 32

@dataclass
class Packed:
    high: torch.Tensor
    codes: torch.Tensor
    scales: torch.Tensor

def state_gather(x, index, dim):
    shape = [1, index.shape[0], 1, 1]
    shape[dim] = index.shape[1]
    target = list(x.shape)
    target[dim] = index.shape[1]
    return x.gather(dim, index.reshape(shape).expand(target))

def vector_gather(x, index):
    return x.gather(-1, index.unsqueeze(0).expand_as(x))

def transform_state(s, layout):
    t = s.float() / layout.c[None, :, :, None]
    return state_gather(state_gather(t, layout.pv, 2), layout.pk, 3)

def restore_state(t, layout):
    s = state_gather(t.float(), layout.pk.argsort(dim=1), 3)
    s = state_gather(s, layout.pv.argsort(dim=1), 2)
    return s * layout.c[None, :, :, None]

def transformed_inputs(q, k, v, layout):
    return (vector_gather(q.float(), layout.pk),
            vector_gather(k.float(), layout.pk),
            vector_gather(v.float() / layout.c[None], layout.pv))

def restore_output(o, layout):
    c_reordered = layout.c.gather(1, layout.pv)
    return vector_gather(o.float() * c_reordered[None],
                         layout.pv.argsort(dim=1))

def int8_groups(x, group):
    shape = x.shape
    x = x.float().reshape(*shape[:-1], shape[-1] // group, group)
    maximum = x.abs().amax(-1)
    scales = torch.where(maximum == 0, torch.ones_like(maximum), maximum * SCALE_RECIPROCAL_FP32)
    codes = torch.round(x / scales.unsqueeze(-1)).clamp(-127, 127).to(torch.int8)
    return codes.reshape(shape).contiguous(), scales.contiguous()

def pack(t, layout):
    x = t.float().transpose(-1, -2).contiguous()
    high = x[:, :, :layout.khi].to(torch.float16)
    codes, scales = int8_groups(x[:, :, layout.khi:], layout.group)
    return Packed(high.contiguous(), codes, scales)

def unpack(packed, layout):
    b, h, kl, dv = packed.codes.shape
    low = packed.codes.reshape(b, h, kl, dv // layout.group, layout.group).float()
    low = (low * packed.scales.unsqueeze(-1)).reshape(b, h, kl, dv)
    return torch.cat((packed.high.float(), low), -2).transpose(-1, -2).contiguous()

def storage_bytes(packed):
    return sum(x.numel() * x.element_size()
               for x in (packed.high, packed.codes, packed.scales))

def gdn_step(s, q, k, v, log_decay, beta, q_scale=1.0):
    decayed = s.float() * log_decay.float().exp()[..., None, None]
    residual = v.float() - (decayed * k.float().unsqueeze(-2)).sum(-1)
    updated = decayed + (beta.float().unsqueeze(-1) * residual).unsqueeze(-1) * k.float().unsqueeze(-2)
    return updated, (updated * q.float().unsqueeze(-2)).sum(-1) * q_scale

def retention_weights(future_log_decay):
    # Future steps t+1..t+H; never include current t.
    return 1.0 + (2 * future_log_decay.double().cumsum(1)).exp().sum(1)

def risk(e, retention, anchor_weights):
    # Weight errors before averaging; head-only mean decay is invalid.
    return (e.double() * retention[..., None] *
            anchor_weights.double()[:, None, None]).sum(0)
