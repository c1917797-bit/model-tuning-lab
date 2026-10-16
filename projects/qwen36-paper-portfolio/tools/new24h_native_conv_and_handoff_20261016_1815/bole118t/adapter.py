"""Three-node ND-cache BOLE experiment. No import-time device operations.

Not a worker installer. Input Q/K must already have native RoPE applied.
Canonical ND [page, block, KVhead, D] only; NZ is explicitly unsupported.
"""
import math
import os
from dataclasses import dataclass


def need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class Owner:
    request: str
    generation: int
    slot: int
    length: int
    version: int


def bits(t, a, b):
    return a.shape == b.shape and a.dtype == b.dtype and t.equal(
        a.contiguous().view(t.uint8), b.contiguous().view(t.uint8))


def identity(x):
    return (x.data_ptr(),x.untyped_storage().data_ptr(),x.storage_offset(),
            tuple(x.shape),tuple(x.stride()),str(x.dtype),str(x.device))


def validate(t, owner, q, k, v, kc, vc, table):
    need(isinstance(owner, Owner) and owner.request and
         all(type(x) is int and x >= 0 for x in
             (owner.generation, owner.slot, owner.length, owner.version)), 'owner')
    need(q.shape == (3, 6, 256) and k.shape == v.shape == (3, 1, 256),
         'actual TP4-derived Q6/KV1/D256, root plus two siblings')
    need(q.dtype == k.dtype == v.dtype == kc.dtype == vc.dtype == t.bfloat16,
         'no automatic dtype conversion')
    need(kc.ndim == 4 and kc.shape == vc.shape and kc.shape[1:] == (128, 1, 256)
         and kc.is_contiguous() and vc.is_contiguous(), 'explicit ND cache, block128; NZ refused')
    need(len({str(x.device) for x in (q, k, v, kc, vc)}) == 1, 'one device')
    need(kc.untyped_storage().data_ptr() != vc.untyped_storage().data_ptr(), 'disjoint K/V')
    need(isinstance(table, (tuple, list)) and all(type(x) is int for x in table),
         'audited CPU block table; no hidden D2H')
    required = (owner.length + 2 + 127) // 128
    need(len(table) >= required and len(set(table)) == len(table) and
         all(0 <= x < kc.shape[0] for x in table), 'complete unique physical block ownership')
    for x in (q, k, v, kc, vc):
        need(bool(t.isfinite(x).all()), 'finite input/cache')


def slots(length, table, count):
    return [table[p // 128] * 128 + p % 128 for p in range(length, length + count)]


def prepare(t, owner, q, k, v, kc, vc, table):
    """Copy paged committed prefix into isolated branch pages, then stage nodes.

    No candidate token touches the committed cache. Source anchors intentionally
    materialize for this diagnostic component, never for performance claims.
    """
    validate(t, owner, q, k, v, kc, vc, table)
    length = owner.length
    npage = (length + 3 + 127) // 128
    sk = t.zeros((npage, 128, 1, 256), dtype=kc.dtype, device=kc.device)
    sv = t.zeros_like(sk)
    prefix_index = t.tensor(slots(0, table, length), dtype=t.int64, device=kc.device)
    if length:
        sk.view(-1, 1, 256)[:length].copy_(kc.view(-1, 1, 256).index_select(0, prefix_index))
        sv.view(-1, 1, 256)[:length].copy_(vc.view(-1, 1, 256).index_select(0, prefix_index))
    sk.view(-1, 1, 256)[length:length + 3].copy_(k)
    sv.view(-1, 1, 256)[length:length + 3].copy_(v)
    # True means forbidden. Root sees prefix/root; each child sees only its sibling-free path.
    mask = t.ones((3, length + 3), dtype=t.bool, device=q.device)
    mask[:, :length + 1] = False
    mask[1, length + 1] = False
    mask[2, length + 2] = False
    return dict(owner=owner, table=tuple(table), q=q.clone(), node_k=k.clone(), node_v=v.clone(),
                source_k=kc, source_v=vc, anchor_k=kc.clone(), anchor_v=vc.clone(),
                source_identity=(identity(kc),identity(vc)),
                scratch_k=sk, scratch_v=sv, mask=mask.contiguous(), status='STAGED',
                schema='bole.paged-three-node-trial/v1', qualified=False)


def native(t, torch_npu, trial, actual_abi, *, sparse_mode):
    """Call actual FIA TND+paged+arbitrary-mask. No claim that domain is supported.

    Sparse modes0/1 are independently measured in this new domain; BNSD success
    is deliberately not inspected as a qualification for this call.
    """
    need(os.environ.get('BOLE_PAGED_TREE_ENABLE') == '1', 'default OFF')
    need(trial['status'] == 'STAGED' and sparse_mode in (0, 1), 'fresh trial/mode')
    need(actual_abi.get('schema') == 'bole.actual-FIA-installed-ABI/v115' and
         actual_abi.get('NPU') is False and actual_abi.get('operator_executed') is False,
         'actual released CPU ABI receipt required')
    family = {n: str(s) for n, s in t.ops.npu.npu_fused_infer_attention_score._schemas.items()}
    need(family == actual_abi['schema_family'], 'exact runtime dispatcher family')
    required = {'query', 'key', 'value', 'atten_mask', 'block_table', 'input_layout',
                'block_size', 'actual_seq_lengths', 'actual_seq_lengths_kv',
                'num_key_value_heads', 'num_heads', 'scale', 'sparse_mode',
                'pre_tokens', 'next_tokens', 'inner_precise'}
    need(required <= set(actual_abi['argument_names']), 'actual paged/TND argument ABI')
    q = trial['q']; sk = trial['scratch_k']; sv = trial['scratch_v']
    block_table = t.arange(sk.shape[0], dtype=t.int32, device=q.device).reshape(1, -1)
    # Native installed _get_fia_params flattens the last two ND-cache axes.
    out, aux = torch_npu.npu_fused_infer_attention_score(
        query=q, key=sk.view(sk.shape[0], 128, -1), value=sv.view(sv.shape[0], 128, -1),
        atten_mask=trial['mask'], block_table=block_table, input_layout='TND',
        block_size=128, actual_seq_lengths=[3], actual_seq_lengths_kv=[trial['owner'].length + 3],
        num_key_value_heads=1, num_heads=6, scale=256 ** -.5, sparse_mode=sparse_mode,
        pre_tokens=2147483647, next_tokens=2147483647, inner_precise=2)
    need(out.shape == q.shape and out.dtype == q.dtype, 'exact observed TND output')
    need(bool(t.isfinite(out).all()), 'finite actual TND output')
    need(bits(t, trial['source_k'], trial['anchor_k']) and
         bits(t, trial['source_v'], trial['anchor_v']), 'prefix/cache immutable during verify')
    trial['status'] = 'VERIFIED'
    return out, aux


def commit(t, trial, current_owner, accepted_child):
    """Diagnostic ND scatter. None=cancel; -1=root only; 1 or2=root+child.

    Real model caller must own the whole block table and hold a scheduler-exclusive
    window. It must invalidate the generation on any partial-copy exception.
    """
    need(trial['status'] == 'VERIFIED', 'actual verified trial required')
    need(current_owner == trial['owner'], 'request/generation/slot/length/version changed')
    need(type(accepted_child) is int and accepted_child in (-1, 1, 2) or accepted_child is None,
         'accepted root path, not arbitrary node')
    kc, vc = trial['source_k'], trial['source_v']
    need((identity(kc),identity(vc))==trial['source_identity'],'cache view rebound')
    need(bits(t, kc, trial['anchor_k']) and bits(t, vc, trial['anchor_v']), 'stale cache anchor')
    path = [] if accepted_child is None else [0] + ([] if accepted_child == -1 else [accepted_child])
    trial['status'] = 'POISONED'  # Never permit retry after first possible write.
    if path:
        index = t.tensor(slots(current_owner.length, trial['table'], len(path)),
                         dtype=t.int64, device=kc.device)
        selected = t.tensor(path, dtype=t.int64, device=kc.device)
        kc.view(-1, 1, 256).index_copy_(0, index, trial['node_k'].index_select(0, selected))
        vc.view(-1, 1, 256).index_copy_(0, index, trial['node_v'].index_select(0, selected))
    trial['status'] = 'COMMITTED'
    return Owner(current_owner.request, current_owner.generation, current_owner.slot,
                 current_owner.length + len(path), current_owner.version + 1)
