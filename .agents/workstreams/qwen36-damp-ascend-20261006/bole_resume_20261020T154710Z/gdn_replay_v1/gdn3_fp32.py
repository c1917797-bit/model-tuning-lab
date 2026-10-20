"""ADVISORY ONLY: source-P FP32 three-node GDN kernel experiment.

No device, model, thread, stream or owner is created here. The public calls
remain disabled until an existing owner supplies both explicit opt-ins and
exact source references. This module does not install a production dispatcher.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


_KERNEL_MODULE = None


def need(value, message):
    if not value:
        raise ValueError(message)


def disabled():
    return dict(schema='bole.gdn3-source-p-fp32-advisory/v1', enabled=False,
                NPU=False, kernel_launched=False, mathematically_qualified=False,
                model_ready=False, formal_success=False)


def _gate(t, *, enabled, arm_verified, C, source_refs):
    if enabled is not True:
        return False
    need(os.environ.get('BOLE_GDN3_TRITON_ENABLE') == '1' and arm_verified is True,
         'explicit opt-in inside an already admitted existing NPU owner')
    need(C is not None and type(source_refs) is dict and
         set(source_refs) == {'implementation', 'kernels', 'reference'},
         'three exact implementation/kernel/original-core source references')
    for reference in source_refs.values():
        C.checked(reference)
    need(C.ref(__file__) == source_refs['implementation'],
         'exact source-bound advisory implementation')
    need(hasattr(t, 'npu') and t.npu.is_initialized(),
         'the existing owner must initialize its own mapped device first')
    need(t.npu.matmul.allow_hf32 is False, 'original common FP32 HF32-OFF policy')
    return True


def _backend(C, source_refs):
    # The default-OFF import path never imports Torch, Triton or a native worker.
    global _KERNEL_MODULE
    path = C.checked(source_refs['kernels'])
    need(path.name == 'gdn3_triton_kernels.py' and
         path.parent == Path(__file__).resolve().parent,
         'exact private sibling kernel path before importing any kernel code')
    if _KERNEL_MODULE is None:
        # Resolve by the checked absolute sibling path, never ambient sys.path.
        name = '_bole_gdn3_kernels_' + source_refs['kernels']['sha256']
        need(name not in sys.modules, 'fresh exact source-bound kernel module')
        spec = importlib.util.spec_from_file_location(name, str(path))
        need(spec is not None and spec.loader is not None,
             'ordinary exact-file Python source loader')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
            need(C.ref(module.__file__) == source_refs['kernels'],
                 'kernel source stable across JIT definition import')
        except BaseException:
            sys.modules.pop(name, None)
            raise
        _KERNEL_MODULE = module
    need(C.ref(_KERNEL_MODULE.__file__) == source_refs['kernels'],
         'cached private kernel belongs to this exact source variant')
    return _KERNEL_MODULE


def _tensor_domain(t, tensors):
    need(all(isinstance(x, t.Tensor) and x.dtype == t.float32 and
             x.device.type == 'npu' for x in tensors),
         'explicit existing-device FP32 tensors; no dtype/device conversion')
    need(len({str(x.device) for x in tensors}) == 1,
         'all operands belong to one existing mapped device')
    need(all(bool(t.isfinite(x).all()) for x in tensors),
         'finite original operands before the experimental kernel')


def _strides(x):
    return tuple(int(v) for v in x.stride())


def execute_verify(t, q, k, v, beta, gamma, state, ancestors, depth, *,
                   enabled=False, arm_verified=False, C=None, source_refs=None,
                   tile_v=32):
    """Compute all three O/P/U, with no cache publication or dispatch install.

    Public qualification scope is exactly the current TP4 C1 geometry. Inputs
    can be strided. State is canonical [B,H,Dk,Dv], even when its live native
    storage is a transposed [B,H,Dv,Dk] arena. P uses the original Torch sequence
    from core112, deliberately avoiding a new device log/exp implementation.
    """
    if not _gate(t, enabled=enabled, arm_verified=arm_verified, C=C,
                 source_refs=source_refs):
        return disabled()
    _tensor_domain(t, (q, k, v, beta, gamma, state))
    need(tuple(q.shape) == tuple(k.shape) == tuple(v.shape) == (1, 12, 3, 128),
         'only actual qualified-target C1/TP4 three-node vector geometry')
    need(tuple(beta.shape) == tuple(gamma.shape) == (1, 12, 3) and
         tuple(state.shape) == (1, 12, 128, 128),
         'explicit FP32 per-node gates and canonical recurrent-state geometry')
    need(type(depth) is int and depth == 1 and
         isinstance(ancestors, t.Tensor) and ancestors.dtype == t.bool and
         tuple(ancestors.shape) == (3, 3) and ancestors.device == q.device,
         'exact root-plus-two-siblings metadata and one nilpotent update depth')
    expected = t.tensor([[False, False, False], [True, False, False],
                         [True, False, False]], dtype=t.bool, device=q.device)
    need(bool(t.equal(ancestors, expected)), 'no linear chain or other topology')
    need(bool((gamma > 0).all()), 'same original finite-positive decay domain')
    need(type(tile_v) is int and tile_v in (32, 64),
         'exact divisors of 128; no padded logical outputs')

    # This is the unchanged expression/order in the original core112.verify.
    # Replaying against original core112 must additionally prove P bitwise.
    mask = ancestors.to(dtype=t.float32, device=q.device)
    inclusive = mask + t.eye(3, device=q.device, dtype=t.float32)
    logg = gamma.log()
    p = t.exp(t.matmul(logg, inclusive.transpose(-1, -2)))
    need(bool(t.isfinite(p).all() and (p > 0).all()),
         'original factor ratios have finite strictly positive denominators')
    ratio = p.unsqueeze(-1) / p.unsqueeze(-2)
    need(bool(t.isfinite(ratio).all()),
         'all original ratios are finite, including masked-off matrix entries')
    output = t.empty((1, 12, 3, 128), dtype=t.float32, device=q.device)
    updates = t.empty_like(output)
    kernel = _backend(C, source_refs)
    # No CUDA-specific compiler knobs, tl.dot, lower precision or HF32 mode.
    kernel.forward_ou[(12, 128 // tile_v)](
        q, k, v, beta, p, ratio, state, output, updates,
        *_strides(q), *_strides(k), *_strides(v), *_strides(beta),
        *_strides(p), *_strides(ratio), *_strides(state),
        H=12, DV=128, TILE_V=tile_v)
    need(bool(t.isfinite(output).all() and t.isfinite(updates).all()),
         'actual kernel results are finite before any candidate publication')
    return dict(
        schema='bole.gdn3-source-p-fp32-execution/v1', enabled=True,
        output=output, factors=(p, updates),
        receipt=dict(source_refs=dict(source_refs), parents=(-1, 0, 0),
                     shape=(1, 12, 3, 128), state_layout='B,H,Dk,Dv',
                     input_strides=dict(q=_strides(q), k=_strides(k), v=_strides(v),
                                        beta=_strides(beta), gamma=_strides(gamma),
                                        state=_strides(state)),
                     p_construction='original Torch log/matmul/inclusive/exp',
                     ratio_construction='original Torch FP32 broadcast division',
                     p_bitwise_identity_checked_here=False, tile_v=tile_v,
                     compiler_options='installed Ascend backend defaults',
                     FP32_contraction_disabled_proven=False,
                     FP32=True, HF32=False, tl_dot_used=False, tl_division_used=False,
                     kernel_launched=True, source_inputs_written=False,
                     persistent_cache_written=False,
                     mathematically_qualified=False, model_ready=False,
                     formal_success=False))


def execute_commit(t, state, k, factors, terminal, *, enabled=False,
                   arm_verified=False, C=None, source_refs=None, tile_k=32,
                   tile_v=32):
    """Return a PRIVATE canonical selected state; never write the live arena."""
    if not _gate(t, enabled=enabled, arm_verified=arm_verified, C=C,
                 source_refs=source_refs):
        return disabled()
    need(type(factors) in (tuple, list) and len(factors) == 2,
         'original P/U factor tuple')
    p, u = factors
    _tensor_domain(t, (state, k, p, u))
    need(tuple(state.shape) == (1, 12, 128, 128) and
         tuple(k.shape) == tuple(u.shape) == (1, 12, 3, 128) and
         tuple(p.shape) == (1, 12, 3), 'same exact factorized target geometry')
    need(bool((p > 0).all()), 'same finite positive original factor denominators')
    need(terminal is None or type(terminal) is int and terminal in (0, 1, 2),
         'one selected root or sibling, or explicit cancellation')
    need(type(tile_k) is int and tile_k in (16, 32, 64) and
         type(tile_v) is int and tile_v in (16, 32, 64),
         'exact divisors of state axes; no padded logical state writes')
    if terminal is None:
        private = state.clone()
        launched = False
    else:
        # Same original core112.commit division before the fixed path mask.
        # Computing every denominator also rejects its masked-off infinities.
        weights = p[..., terminal:terminal+1] / p
        need(bool(t.isfinite(weights).all()), 'all original commit weights finite')
        private = t.empty((1, 12, 128, 128), dtype=t.float32, device=state.device)
        need(private.untyped_storage().data_ptr() != state.untyped_storage().data_ptr(),
             'private selected output must not alias the live preimage')
        kernel = _backend(C, source_refs)
        kernel.selected_state[(12, 128 // tile_k, 128 // tile_v)](
            state, k, p, weights, u, private, *_strides(state), *_strides(k),
            *_strides(p), *_strides(weights), *_strides(u), H=12, DK=128, DV=128,
            TILE_K=tile_k, TILE_V=tile_v, TERMINAL=terminal)
        launched = True
    need(bool(t.isfinite(private).all()), 'finite private selected state')
    return dict(
        schema='bole.gdn3-source-p-fp32-selected-state/v1', enabled=True,
        selected_state=private,
        receipt=dict(source_refs=dict(source_refs), terminal=terminal,
                     processed_nodes=() if terminal is None else (0,) if terminal == 0 else (0, terminal),
                     state_layout='B,H,Dk,Dv', FP32=True, HF32=False,
                     compiler_options='installed Ascend backend defaults',
                     FP32_contraction_disabled_proven=False,
                     kernel_launched=launched, source_inputs_written=False,
                     persistent_cache_written=False, scheduler_committed=False,
                     mathematically_qualified=False, model_ready=False,
                     formal_success=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.parse_args()
    print(json.dumps(disabled()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
