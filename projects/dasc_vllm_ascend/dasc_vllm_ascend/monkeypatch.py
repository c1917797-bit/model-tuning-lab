"""DASC-NR numerical prefix-state restore monkeypatch.

This canary intentionally retains dense cache allocation. It validates restore
semantics on the real Ascend state lifecycle before physical cache
virtualization is attempted.
"""

from __future__ import annotations

import functools
import hashlib
import importlib.metadata
import inspect
import itertools
import math
from pathlib import Path
from typing import Any

from .config import DascConfig
from .evidence import emit


class DascRuntimeUnsupported(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _ensure_ascend_global_patch() -> None:
    try:
        import vllm_ascend
    except Exception as error:
        raise DascRuntimeUnsupported(
            "MST_DASC_ENABLE=1 requires vllm-ascend"
        ) from error
    ensure = getattr(vllm_ascend, "_ensure_global_patch", None)
    if ensure is not None:
        ensure()


def _retained_mask(module: Any, state: Any, config: DascConfig):
    import torch
    import torch.nn.functional as functional

    cached = getattr(module, "_mst_dasc_retained_mask", None)
    if cached is None:
        a_log = module.A_log.detach().float().reshape(-1)
        dt_bias = module.dt_bias.detach().float().reshape(-1)
        if a_log.shape != dt_bias.shape:
            raise DascRuntimeUnsupported(
                f"DASC decay parameter mismatch: {a_log.shape} vs {dt_bias.shape}"
            )
        decay = -torch.exp(a_log) * functional.softplus(
            dt_bias + config.representative_a
        )
        horizon = math.log(config.epsilon) / decay
        cached = horizon > config.w_max
        if not bool(cached.any()):
            raise DascRuntimeUnsupported("DASC selector retained zero local heads")
        module._mst_dasc_retained_mask = cached

    axes = [axis for axis, size in enumerate(state.shape) if size == cached.numel()]
    if len(axes) != 1:
        raise DascRuntimeUnsupported(
            "DASC cannot map local decay heads to temporal state: "
            f"state={tuple(state.shape)} heads={cached.numel()} axes={axes}"
        )
    return cached, axes[0]


def _copy_temporal_nr(
    module: Any,
    state: Any,
    state_copy_func: Any,
    block_ids: Any,
    src_block_idx: int,
    dest_block_id: int,
    accept_token_bias: int,
    tensor_view_from_ptr: Any,
    config: DascConfig,
) -> tuple[int, int]:
    copy_spec = state_copy_func(
        state, block_ids, src_block_idx, accept_token_bias + 1
    )
    destination = state[dest_block_id]
    if copy_spec.num_elements != destination.numel():
        raise DascRuntimeUnsupported(
            "DASC-NR canary supports only complete temporal rows: "
            f"copy={copy_spec.num_elements} row={destination.numel()}"
        )
    source = tensor_view_from_ptr(
        state, copy_spec.start_addr, copy_spec.num_elements
    ).view_as(destination)
    retained, head_axis = _retained_mask(module, destination, config)
    indices = retained.nonzero(as_tuple=False).flatten()
    destination.zero_()
    destination.index_copy_(
        head_axis,
        indices,
        source.index_select(head_axis, indices),
    )
    return int(retained.sum().item()), retained.numel()


def _install_state_restore_patch(config: DascConfig, mamba_utils: Any, ascend_patch: Any) -> None:
    if getattr(mamba_utils, "_mst_dasc_nr_installed", False):
        return
    original_collect = mamba_utils.collect_mamba_copy_meta
    original_copy = mamba_utils.do_mamba_copy_block
    original_preprocess = mamba_utils.preprocess_mamba

    def collect_dasc(
        copy_bufs,
        kv_cache_config,
        copy_funcs,
        group_ids,
        src_block_idx,
        dest_block_idx,
        accept_token_bias,
        req_state,
        forward_context,
    ):
        if not getattr(req_state, "_mst_dasc_prefix_restore", False):
            return original_collect(
                copy_bufs,
                kv_cache_config,
                copy_funcs,
                group_ids,
                src_block_idx,
                dest_block_idx,
                accept_token_bias,
                req_state,
                forward_context,
            )
        if accept_token_bias != 0:
            raise DascRuntimeUnsupported("DASC prefix restore requires token bias zero")
        plans = getattr(copy_bufs, "_mst_dasc_temporal_plans", None)
        if plans is None:
            plans = []
            copy_bufs._mst_dasc_temporal_plans = plans

        for group_id in group_ids:
            block_ids = req_state.block_ids[group_id]
            dest_block_id = block_ids[dest_block_idx]
            layer_names = kv_cache_config.kv_cache_groups[group_id].layer_names
            for layer_name in layer_names:
                module = forward_context[layer_name]
                caches = module.kv_cache
                if len(caches) != 2 or len(copy_funcs) != 2:
                    raise DascRuntimeUnsupported(
                        f"DASC expects conv and temporal state at {layer_name}"
                    )
                conv = caches[0]
                conv_copy = copy_funcs[0](
                    conv, block_ids, src_block_idx, accept_token_bias + 1
                )
                offset = copy_bufs.offset
                copy_bufs.src_ptrs.np[offset] = conv_copy.start_addr
                copy_bufs.dst_ptrs.np[offset] = conv[dest_block_id].data_ptr()
                copy_bufs.sizes.np[offset] = (
                    conv_copy.num_elements * conv.element_size()
                )
                copy_bufs.offset += 1
                plans.append(
                    (
                        layer_name,
                        module,
                        caches[1],
                        copy_funcs[1],
                        block_ids,
                        src_block_idx,
                        dest_block_id,
                        accept_token_bias,
                    )
                )

    def copy_dasc(copy_bufs):
        original_copy(copy_bufs)
        plans = getattr(copy_bufs, "_mst_dasc_temporal_plans", [])
        try:
            for plan in plans:
                layer_name = plan[0]
                module = plan[1]
                retained, total = _copy_temporal_nr(
                    *plan[1:],
                    tensor_view_from_ptr=ascend_patch._tensor_view_from_data_ptr,
                    config=config,
                )
                if not getattr(module, "_mst_dasc_activation_emitted", False):
                    emit(
                        config.evidence_path,
                        "prefix_temporal_restore",
                        layer=layer_name,
                        mode=config.mode,
                        retained_local_heads=retained,
                        total_local_heads=total,
                        w_max=config.w_max,
                        epsilon=config.epsilon,
                        representative_a=config.representative_a,
                    )
                    module._mst_dasc_activation_emitted = True
        finally:
            copy_bufs._mst_dasc_temporal_plans = []

    @functools.wraps(original_preprocess)
    def preprocess_dasc(
        scheduler_output,
        kv_cache_config,
        cache_config,
        mamba_state_idx,
        input_batch,
        requests,
        forward_context,
        copy_funcs,
        copy_bufs,
    ):
        if cache_config.mamba_cache_mode != "align":
            raise DascRuntimeUnsupported(
                "DASC numerical canary requires mamba_cache_mode=align"
            )
        finished = scheduler_output.finished_req_ids
        preempted = scheduler_output.preempted_req_ids or set()
        resumed = scheduler_output.scheduled_cached_reqs.resumed_req_ids
        for req_id in itertools.chain(finished, preempted, resumed):
            mamba_state_idx.pop(req_id, None)
        for req_id in input_batch.req_ids:
            req_state = requests[req_id]
            req_state._mst_dasc_prefix_restore = (
                req_id not in mamba_state_idx and req_state.num_computed_tokens > 0
            )
        try:
            return original_preprocess(
                scheduler_output,
                kv_cache_config,
                cache_config,
                mamba_state_idx,
                input_batch,
                requests,
                forward_context,
                copy_funcs,
                copy_bufs,
            )
        finally:
            for req_id in input_batch.req_ids:
                requests[req_id]._mst_dasc_prefix_restore = False

    mamba_utils.collect_mamba_copy_meta = collect_dasc
    mamba_utils.do_mamba_copy_block = copy_dasc
    mamba_utils.preprocess_mamba = preprocess_dasc
    mamba_utils._mst_dasc_nr_installed = True


def install(config: DascConfig) -> None:
    _ensure_ascend_global_patch()
    versions = {name: _version(name) for name in ("vllm", "vllm-ascend")}
    if any(value.split("+")[0] != "0.23.0" for value in versions.values()):
        raise DascRuntimeUnsupported(
            f"DASC requires vLLM/vLLM-Ascend 0.23.0, got {versions}"
        )

    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import (
        QwenGatedDeltaNetAttention,
    )
    from vllm.model_executor.models.qwen3_5 import Qwen3_5ForConditionalGeneration
    from vllm.v1.worker import mamba_utils
    from vllm_ascend.ops import gdn
    from vllm_ascend.patch.worker import patch_mamba_utils as ascend_patch
    from vllm_ascend.worker import model_runner_v1

    guarded_sources = {
        "gdn": (gdn, config.expected_gdn_sha256),
        "mamba_patch": (ascend_patch, config.expected_mamba_patch_sha256),
        "model_runner": (model_runner_v1, config.expected_model_runner_sha256),
    }
    source_evidence = {}
    for name, (module, expected_sha) in guarded_sources.items():
        source = inspect.getsourcefile(module)
        if source is None:
            raise DascRuntimeUnsupported(f"Cannot resolve live Ascend {name} source")
        source_sha = _sha256(Path(source))
        if source_sha != expected_sha:
            raise DascRuntimeUnsupported(
                f"Live Ascend {name} source differs from audited source: {source_sha}"
            )
        source_evidence[f"{name}_source"] = source
        source_evidence[f"{name}_sha256"] = source_sha

    original_load = Qwen3_5ForConditionalGeneration.load_weights
    if getattr(original_load, "_mst_dasc_loader", False):
        return

    @functools.wraps(original_load)
    def load_then_install(self, weights):
        result = original_load(self, weights)
        if (
            QwenGatedDeltaNetAttention._forward_core
            is not gdn.AscendGatedDeltaNetAttention._forward_core
        ):
            raise DascRuntimeUnsupported(
                "Ascend Qwen GDN worker dispatch is not installed"
            )
        _install_state_restore_patch(config, mamba_utils, ascend_patch)
        emit(
            config.evidence_path,
            "worker_dispatch_verified",
            mode=config.mode,
            **source_evidence,
            vllm_version=versions["vllm"],
            vllm_ascend_version=versions["vllm-ascend"],
        )
        return result

    load_then_install._mst_dasc_loader = True
    Qwen3_5ForConditionalGeneration.load_weights = load_then_install
    emit(
        config.evidence_path,
        "plugin_registered",
        mode=config.mode,
        **source_evidence,
        vllm_version=versions["vllm"],
        vllm_ascend_version=versions["vllm-ascend"],
    )
