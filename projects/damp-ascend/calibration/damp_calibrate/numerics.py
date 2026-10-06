"""CPU Torch; native [Hv,Dv,Dk], group32 along Dv, original-coordinate errors."""
from .rules import RECIPROCAL, require, sr_from_rms

def candidate(rms, alpha, torch):
    require(rms.device.type == "cpu" and rms.ndim == 2, "CPU per-head value RMS required")
    rows = [sr_from_rms(row, alpha) for row in rms.tolist()]
    return (torch.tensor([r[0] for r in rows], dtype=torch.float32),
            torch.tensor([r[1] for r in rows], dtype=torch.int64))

def storage_errors(state, sr, pv, torch, group=32):
    require(state.device.type == "cpu" and state.dtype == torch.float32 and state.ndim == 3,
            "CPU FP32 [Hv,Dv,Dk] state required")
    heads, values, keys = state.shape
    require(values % group == 0 and sr.shape == pv.shape == (heads, values)
            and sr.dtype == torch.float32 and pv.dtype in (torch.int32, torch.int64)
            and sr.device.type == pv.device.type == "cpu", "SR/PV/group geometry mismatch")
    require(bool(torch.isfinite(state).all()) and bool((torch.isfinite(sr) & (sr > 0)).all()),
            "nonfinite state/SR")
    require(all(sorted(row) == list(range(values)) for row in pv.tolist()), "PV not bijective")
    scaled = state / sr[:, :, None]
    require(bool(torch.isfinite(scaled).all()), "scaled FP32 state overflow")
    transformed = scaled.gather(1, pv.long()[:, :, None].expand_as(scaled))
    groups = transformed.reshape(heads, values // group, group, keys)
    maximum = groups.abs().amax(2)
    scales = torch.where(maximum == 0, torch.ones_like(maximum), maximum * RECIPROCAL)
    require(bool((torch.isfinite(scales) & (scales > 0)).all()), "INT8 scale under/overflow")
    codes = (groups / scales[:, :, None, :]).round().clamp(-127, 127).to(torch.int8)
    quant8 = (codes.float() * scales[:, :, None, :]).reshape_as(transformed)
    quant16 = transformed.half().float()
    inverse = pv.long().argsort(1)[:, :, None].expand_as(transformed)
    restored8 = quant8.gather(1, inverse) * sr[:, :, None]
    restored16 = quant16.gather(1, inverse) * sr[:, :, None]
    require(bool(torch.isfinite(restored8).all()), "INT8 restoration nonfinite")
    return ((restored8.double() - state.double()).square().sum(1),
            (restored16.double() - state.double()).square().sum(1))

def mixed_cost(error8, error16, weights, high, torch):
    require(error8.shape == error16.shape == high.shape and weights.shape == (error8.shape[0],),
            "mixed error geometry mismatch")
    return (torch.where(high, error16, error8) * weights.double()[:, None]).sum(1)
