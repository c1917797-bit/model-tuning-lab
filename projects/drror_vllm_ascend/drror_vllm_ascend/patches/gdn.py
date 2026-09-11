"""Reduced-shape prefill dispatch for the Ascend GDN implementation."""

from __future__ import annotations

import contextvars
import functools
import inspect

from ..diagnostics import emit_evidence
from ..envs import DrrqrConfig

SUPPORTED_REDUCED_KEY_DIMS = (32, 64, 80, 96, 112)


def install_decode_packed_qkv_l2(
    gdn_cls,
    gdn_module,
    config: DrrqrConfig,
    *,
    kernel=None,
) -> None:
    """Fuse Dk64 pure-decode QKV packing and Q/K normalization.

    The audited fallback remains active for dense layers, prefill, mixed
    prefill/decode, and speculative decode.  On the admitted pure Dk64 path,
    the packed kernel is fail-closed and the two immediately following module
    L2 calls become identities because the kernel already materialized the
    exact BF16-normalized boundary.
    """
    original_rearrange = gdn_cls.rearrange_mixed_qkv
    original_l2norm = gdn_module.l2norm_fwd
    identity = (config.plan_path, config.plan_sha256, "packed-qkv-l2-v1")
    installed = getattr(original_rearrange, "_drror_packed_qkv_l2_config", None)
    if installed is not None:
        if installed != identity:
            raise RuntimeError("DRRQR: packed QKV L2 already bound to another plan")
        return
    if kernel is None:
        from ..kernels.packed_qkv_l2 import packed_qkv_l2

        kernel = packed_qkv_l2
    normalized_outputs = contextvars.ContextVar(
        "drrqr_packed_qkv_l2_outputs", default=()
    )

    def metadata_for(instance):
        metadata = getattr(gdn_module.get_forward_context(), "attn_metadata", None)
        return metadata.get(instance.prefix) if isinstance(metadata, dict) else metadata

    def pure_decode(metadata, tokens):
        return (
            metadata is not None
            and getattr(metadata, "spec_sequence_masks", None) is None
            and getattr(metadata, "num_prefills", 0) == 0
            and getattr(metadata, "num_decodes", 0) > 0
            and int(getattr(metadata, "num_decode_tokens", -1)) == int(tokens)
        )

    @functools.wraps(original_rearrange)
    def rearrange(instance, mixed_qkv):
        normalized_outputs.set(())
        if mixed_qkv is None:
            return original_rearrange(instance, mixed_qkv)
        metadata = metadata_for(instance)
        if not pure_decode(metadata, mixed_qkv.shape[0]):
            return original_rearrange(instance, mixed_qkv)
        if instance.head_k_dim != 64:
            return original_rearrange(instance, mixed_qkv)
        h_qk = instance.key_dim // instance.tp_size // instance.head_k_dim
        h_v = instance.value_dim // instance.tp_size // instance.head_v_dim
        if (h_qk, h_v, instance.head_v_dim) != (4, 12, 128):
            raise RuntimeError("DRRQR: packed QKV L2 runtime shape contract failed")
        result = kernel(
            mixed_qkv,
            h_qk=h_qk,
            h_v=h_v,
            d_k=instance.head_k_dim,
            d_v=instance.head_v_dim,
        )
        normalized_outputs.set(result[:2])
        return result

    @functools.wraps(original_l2norm)
    def l2norm(value, *args, **kwargs):
        pending = normalized_outputs.get()
        if pending and value is pending[0]:
            normalized_outputs.set(pending[1:])
            return value
        return original_l2norm(value, *args, **kwargs)

    rearrange._drror_packed_qkv_l2_config = identity
    l2norm._drror_packed_qkv_l2_config = identity
    gdn_cls.rearrange_mixed_qkv = rearrange
    gdn_module.l2norm_fwd = l2norm
    emit_evidence(
        config,
        "packed_qkv_l2_patch_installed",
        component="gdn",
        plan_sha256=config.plan_sha256,
        implementation="plugin-triton-two-kernel-v1",
        admitted_path="pure-nonspec-decode-tp4-dk64",
        fallback="audited-v0.23-rearrange-and-l2norm",
    )


def install_prefill_patch(gdn_module, config: DrrqrConfig) -> None:
    """Observe the actual v0.23 module-global prefill call without changing it.

    v0.23 has no _chunk_gated_delta_rule_fused. Its Ascend core calls this
    module binding directly with state already in [N,Nv,Dk,Dv] layout and
    prebuilt per-request metadata. Preserve both the inputs and outputs.
    """
    original = gdn_module.chunk_gated_delta_rule
    identity = (config.plan_path, config.plan_sha256)
    installed = getattr(original, "_drror_prefill_config", None)
    if installed is not None:
        if installed != identity:
            raise RuntimeError("DRRQR: prefill already patched with another plan")
        return
    signature = inspect.signature(original)
    required = {"q", "k", "v", "initial_state", "cu_seqlens", "prebuilt_meta", "use_qk_l2norm_in_kernel"}
    if not required.issubset(signature.parameters):
        raise RuntimeError("DRRQR: v0.23 chunk_gated_delta_rule ABI changed")
    reported = False

    @functools.wraps(original)
    def dispatch(*args, **kwargs):
        nonlocal reported
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        q, k, v = values["q"], values["k"], values["v"]
        if q.shape[-1] == 128:
            return original(*args, **kwargs)
        if q.shape[-1] not in SUPPORTED_REDUCED_KEY_DIMS or k.shape[-1] != q.shape[-1] or v.shape[-1] != 128:
            raise RuntimeError("DRRQR: unexpected reduced prefill dimensions")
        starts, prebuilt = values["cu_seqlens"], values["prebuilt_meta"]
        state = values["initial_state"]
        if (
            starts is None
            or prebuilt is None
            or state is None
            or tuple(state.shape[-2:]) != (q.shape[-1], v.shape[-1])
            or state.shape[0] != starts.shape[0] - 1
            or values.get("head_first", False)
            or not values["use_qk_l2norm_in_kernel"]
        ):
            raise RuntimeError("DRRQR: prefill requires original state layout, normalization and chunk metadata")
        # No transposition, Q/K normalization, scale change, tensor copy, or
        # fallback is introduced by this v0.23 evidence hook.
        result = original(*args, **kwargs)
        if not reported:
            emit_evidence(
                config,
                "reduced_gdn_hot_path",
                component="gdn",
                plan_sha256=config.plan_sha256,
                key_head_dim=int(q.shape[-1]),
                value_head_dim=int(v.shape[-1]),
                sequence_count=int(starts.shape[0] - 1),
                token_count=int(q.shape[1]),
                backend="chunk_gated_delta_rule",
                query_shape=list(q.shape),
                key_shape=list(k.shape),
                value_shape=list(v.shape),
                initial_state_shape=list(state.shape),
                prebuilt_metadata_forwarded=True,
                state_layout="N,Nv,Dk,Dv",
                completed_python_call=True,
                note="Kernel return observed; asynchronous device completion requires request success",
            )
            reported = True
            # A production-length diagnostic must retain the binding for every
            # GDN layer in its one explicitly armed request. Normal treatment
            # restores the audited binding after the first successful call.
            if not config.prefill_diagnostic:
                gdn_module.chunk_gated_delta_rule = original
        return result

    dispatch._drror_prefill_config = identity
    gdn_module.chunk_gated_delta_rule = dispatch


def install_decode_observer(gdn_cls, gdn_module, config: DrrqrConfig) -> None:
    """Observe an unchanged v0.23 decode branch after worker patches install.

    Do not replace torch.ops: retain the original core/operator and graph path.
    Q/K shapes come from the original rearrange result. The recorded branch is
    the audited non-speculative AscendC decode branch after its core returns.
    """
    original_core = gdn_cls._forward_core
    identity = (config.plan_path, config.plan_sha256)
    installed = getattr(original_core, "_drror_decode_config", None)
    if installed is not None:
        if installed != identity:
            raise RuntimeError("DRRQR: decode observer already bound to another plan")
        return
    original_rearrange = gdn_cls.rearrange_mixed_qkv
    active = contextvars.ContextVar("drrqr_decode_shape_observation", default=None)
    reported = False

    @functools.wraps(original_rearrange)
    def rearrange(self, mixed_qkv):
        if reported:
            return original_rearrange(self, mixed_qkv)
        result = original_rearrange(self, mixed_qkv)
        observation = active.get()
        if observation is not None and result[0] is not None:
            q, k, v = result
            if q.shape[1] == observation["decode_tokens"]:
                observation.update(query_shape=list(q.shape), key_shape=list(k.shape), value_shape=list(v.shape))
        return result

    @functools.wraps(original_core)
    def core(self, mixed_qkv, b, a, core_attn_out):
        nonlocal reported
        if reported:
            return original_core(self, mixed_qkv, b, a, core_attn_out)
        metadata = getattr(gdn_module.get_forward_context(), "attn_metadata", None)
        candidate = metadata.get(self.prefix) if isinstance(metadata, dict) else metadata
        if candidate is None or getattr(candidate, "num_decodes", 0) <= 0:
            return original_core(self, mixed_qkv, b, a, core_attn_out)
        if getattr(candidate, "spec_sequence_masks", None) is not None:
            raise RuntimeError("DRRQR: speculative decode is outside the bound runtime contract")
        observation = {"decode_tokens": int(candidate.num_decode_tokens)}
        token = active.set(observation)
        try:
            result = original_core(self, mixed_qkv, b, a, core_attn_out)
        finally:
            active.reset(token)
        state = self.kv_cache[1]
        qshape = observation.get("query_shape")
        # A heterogeneous plan may retain early dense Dk128 layers.  Keep
        # observing until the first reduced layer instead of treating that
        # intentional dense layer as a contract violation.
        if qshape and qshape[-1] == 128 and state.shape[-1] == 128:
            return result
        if not qshape or qshape[-1] not in SUPPORTED_REDUCED_KEY_DIMS or state.shape[-1] != qshape[-1]:
            raise RuntimeError("DRRQR: completed decode did not expose expected reduced Q/K/state shapes")
        emit_evidence(
            config,
            "reduced_gdn_decode_branch",
            component="gdn",
            plan_sha256=config.plan_sha256,
            backend=(
                "packed_qkv_l2+npu_recurrent_gated_delta_rule"
                if config.packed_qkv_l2 and qshape[-1] == 64
                else "npu_recurrent_gated_delta_rule"
            ),
            prefix=str(self.prefix),
            query_shape=observation["query_shape"],
            key_shape=observation["key_shape"],
            value_shape=observation["value_shape"],
            state_shape=list(state.shape),
            state_layout="N,Nv,Dv,Dk",
            key_head_dim=int(qshape[-1]),
            value_head_dim=int(state.shape[-2]),
            token_count=observation["decode_tokens"],
            completed_python_call=True,
            observation=(
                "audited v0.23 recurrent core returned; plugin packed QKV/L2 "
                "adapter active before unchanged torch.ops"
                if config.packed_qkv_l2
                else "unchanged audited v0.23 core decode branch returned; torch.ops was not replaced"
            ),
        )
        reported = True
        # Restore both exact v0.23 methods after the first successful decode
        # observation.  Existing instances resolve these class attributes on
        # each call, so the hot path no longer pays observer/contextvar costs.
        gdn_cls._forward_core = original_core
        gdn_cls.rearrange_mixed_qkv = original_rearrange
        return result

    core._drror_decode_config = identity
    # Keep calling the immediately wrapped implementation, but preserve the
    # raw Ascend core as the provenance anchor when observers are layered.
    core._drror_core_original = getattr(
        original_core, "_drror_core_original", original_core
    )
    gdn_cls._forward_core = core
    gdn_cls.rearrange_mixed_qkv = rearrange
