"""Independent restricted native-FP32 compressed trajectory; parent executes.

No candidate pack/update imports. Only eager, B1/B16, SR powers of two and
exact BF16 transformed V are supported. This is NOT yet NPU-validated.
"""
import torch
from independent_oracle import ValueMajorPacked, pack_value_major, unpack_value_major


def _exact(a, b):
    return (a.shape == b.shape and a.dtype == b.dtype and
            torch.equal(a.contiguous().view(torch.uint8),
                        b.contiguous().view(torch.uint8)))


def _nd(tensor, device):
    import torch_npu
    converted = torch_npu.npu_format_cast(tensor.to(device).contiguous(), 2)
    if torch_npu.get_npu_format(converted) != 2:
        raise RuntimeError('native golden requires explicit physical ND(2)')
    return converted


def _validate_power2(layout):
    c = layout.c
    if c.device.type != 'cpu' or c.dtype != torch.float32:
        raise ValueError('independent static plans/SR must be CPU FP32')
    if c.shape != (12, 128) or not torch.isfinite(c).all() or not (c > 0).all():
        raise ValueError('SR must be finite positive [12,128]')
    mantissa, _ = torch.frexp(c)
    if not (mantissa == 0.5).all():
        raise ValueError('native golden scope permits identity/power-of-two SR only')


def step(before, layout, q, k, v, g, beta, ids, native_op, device):
    """One step of OWN independent trajectory; returns packed state + evidence.

    native_op must be the provenance-verified actual native recurrent callable.
    All inputs except that callable/device are CPU. The caller owns scheduling,
    frozen source/library evidence, report retention and comparison thresholds.
    Output cast boundaries are returned separately, never hidden.
    """
    _validate_power2(layout)
    if layout.khi != 16 or layout.group != 32:
        raise ValueError('requires high16/group32')
    for x in (q, k, v, g, beta, ids, before.high, before.low, before.scales):
        if x.device.type != 'cpu':
            raise ValueError('golden state and turn inputs must be independent CPU copies')
    b = q.shape[0]
    if b not in (1, 16) or q.shape != (b, 4, 128) or k.shape != q.shape:
        raise ValueError('requires B1/B16, HQ4, K128')
    if v.shape != (b, 12, 128) or g.shape != (b, 12) or beta.shape != g.shape:
        raise ValueError('requires value heads12, V128 and per-head gates')
    if any(x.dtype != torch.bfloat16 for x in (q, k, v, beta)) or g.dtype != torch.float32:
        raise ValueError('native QKV/beta BF16 and g FP32 required')
    slots = before.high.shape[0]
    if ids.dtype not in (torch.int32, torch.int64):
        raise ValueError('golden slot IDs must be INT32/INT64, not silently truncated')
    ids = ids.long()
    if ids.shape != (b,) or ids.unique().numel() != b or (ids < 0).any() or (ids >= slots).any():
        raise ValueError('unique in-range state indices required')
    state_cpu = unpack_value_major(before, layout)
    if state_cpu.shape != (slots, 12, 128, 128):
        raise ValueError('native physical FP32 state must be [S,12,128,128]')
    pk = layout.pk.long()[None].expand(b, -1, -1)
    pv = layout.pv.long()[None].expand(b, -1, -1)
    qe = q.repeat_interleave(3, 1).gather(2, pk).contiguous()
    ke = k.repeat_interleave(3, 1).gather(2, pk).contiguous()
    vt = (v.float()/layout.c[None]).gather(2, pv).contiguous()
    vb = vt.bfloat16()
    if not torch.isfinite(vb).all() or not _exact(vb.float(), vt):
        raise ValueError('V/SR is not exactly BF16; casting would change the native problem')
    state = _nd(state_cpu.clone(), device)
    lengths = _nd(torch.tensor([0]+[1]*b, dtype=torch.int32), device)
    nids = _nd(ids.to(torch.int32), device)
    # Native accepts NK12=NV12; its ProcessHead ratio is 1. No candidate call.
    out = native_op(_nd(qe, device), _nd(ke, device), _nd(vb, device), state,
                    beta=_nd(beta, device), scale=128**-0.5,
                    actual_seq_lengths=lengths, ssm_state_indices=nids,
                    num_accepted_tokens=None, g=_nd(g, device), gk=None)
    updated = state.cpu()
    reordered_out = out.cpu()
    if updated.dtype != torch.float32 or reordered_out.dtype != torch.bfloat16:
        raise RuntimeError('native runtime violated FP32-state/BF16-output contract')
    if not torch.isfinite(updated).all() or not torch.isfinite(reordered_out).all():
        raise RuntimeError('native golden produced nonfinite values')
    untouched = torch.tensor([s for s in range(slots) if s not in ids.tolist()], dtype=torch.long)
    if not _exact(updated.index_select(0, untouched), state_cpu.index_select(0, untouched)):
        raise RuntimeError('native changed an untouched FP32 slot')
    inv = layout.pv.long().argsort(-1)[None].expand(b, -1, -1)
    original_fp32_after_native_cast = reordered_out.float().gather(2, inv)*layout.c[None]
    original_bf16 = original_fp32_after_native_cast.bfloat16()
    if not torch.isfinite(original_bf16).all() or not _exact(original_bf16.float(), original_fp32_after_native_cast):
        raise RuntimeError('restored power-of-two output under/overflow or extra BF16 rounding')
    selected = pack_value_major(updated.index_select(0, ids), layout)
    result = before.clone()
    for name in ('high', 'low', 'scales'):
        getattr(result, name).index_copy_(0, ids, getattr(selected, name))
    if any(not _exact(getattr(result, n).index_select(0, untouched),
                      getattr(before, n).index_select(0, untouched))
           for n in ('high', 'low', 'scales')):
        raise RuntimeError('independent quantizer changed an untouched packed slot')
    return {'packed': result, 'original_output_bf16': original_bf16,
            'native_output_reordered_bf16': reordered_out,
            'restored_fp32_after_native_bf16_cast': original_fp32_after_native_cast,
            'native_updated_selected_fp32': updated.index_select(0, ids),
            'transformed_value_bf16': vb,
            'value_cast_exact': True, 'restored_cast_exact': True,
            'native_fp32_untouched_exact': True,
            'scope': 'restricted power2-SR native arithmetic; eager only; not a performance or quality result'}
