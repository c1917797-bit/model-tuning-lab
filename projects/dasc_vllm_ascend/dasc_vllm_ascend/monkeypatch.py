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
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .config import DascConfig
from .evidence import emit
from .metadata import remap_ascend_gdn_metadata
from .runtime import BoundActiveStateBridge
from .selector import (
    align_retained_heads_tp,
    retained_head_indices,
    unique_head_axis,
)
from .spec import compact_mamba_spec


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


def _install_aligned_hybrid_grouping_patch(config: DascConfig, kv_cache_utils: Any) -> None:
    """Group aligned attention and heterogeneous Mamba pages in one pool.

    vLLM 0.23 normally rejects the different per-layer Mamba page sizes before
    allocation. In align mode both attention and Mamba layers consume the same
    token-block lifecycle, so a UniformTypeKVCacheSpecs aggregate is the
    truthful physical representation: its page is the sum of the exact inner
    layer pages rather than a dense per-layer maximum.
    """
    if getattr(kv_cache_utils, "_mst_dasc_aligned_hybrid_installed", False):
        return

    from vllm.v1.kv_cache_interface import (
        AttentionSpec,
        HiddenStateCacheSpec,
        KVCacheGroupSpec,
        MambaSpec,
        UniformTypeKVCacheSpecs,
    )

    original = kv_cache_utils.get_kv_cache_groups

    @functools.wraps(original)
    def get_dasc_groups(vllm_config, kv_cache_spec):
        hidden = {
            name: spec
            for name, spec in kv_cache_spec.items()
            if isinstance(spec, HiddenStateCacheSpec)
        }
        filtered = {
            name: spec
            for name, spec in kv_cache_spec.items()
            if not isinstance(spec, HiddenStateCacheSpec)
        }
        attention = {
            name: spec
            for name, spec in filtered.items()
            if isinstance(spec, AttentionSpec)
        }
        mamba = {
            name: spec
            for name, spec in filtered.items()
            if isinstance(spec, MambaSpec)
        }
        known = len(attention) + len(mamba) == len(filtered)
        block_sizes = {spec.block_size for spec in filtered.values()}
        aligned = mamba and all(
            spec.mamba_cache_mode == "align" for spec in mamba.values()
        )
        heterogeneous = len({spec.page_size_bytes for spec in mamba.values()}) > 1

        if not (known and attention and aligned and heterogeneous):
            return original(vllm_config, kv_cache_spec)
        if hidden:
            raise DascRuntimeUnsupported(
                "DASC heterogeneous grouping does not yet support hidden-state cache"
            )
        if len(block_sizes) != 1:
            raise DascRuntimeUnsupported(
                f"DASC align mode requires one token block size, got {block_sizes}"
            )

        # The aggregate changes page accounting only. Preserve the model's
        # storage/layer order here; the Ascend input-batch dispatch ambiguity is
        # adapted separately without mutating this authoritative group.
        ordered = dict(filtered)
        aggregate = UniformTypeKVCacheSpecs(
            block_size=next(iter(block_sizes)),
            kv_cache_specs=ordered,
        )
        emit(
            config.evidence_path,
            "heterogeneous_cache_grouped",
            mode=config.mode,
            attention_layers=len(attention),
            mamba_layers=len(mamba),
            mamba_page_sizes=sorted(
                {spec.page_size_bytes for spec in mamba.values()}
            ),
            aggregate_page_bytes=aggregate.page_size_bytes,
        )
        return [KVCacheGroupSpec(list(ordered), aggregate)]

    kv_cache_utils.get_kv_cache_groups = get_dasc_groups
    kv_cache_utils._mst_dasc_aligned_hybrid_installed = True


def _install_heterogeneous_cascade_guard(
    config: DascConfig, model_runner_class: Any
) -> None:
    """Disable cascade attention for the synthetic heterogeneous cache group.

    vLLM 0.23 passes the aggregate UniformTypeKVCacheSpecs to its cascade
    heuristic, which accepts only AttentionSpec. Cascade attention is an
    optional execution optimization, so returning None retains the normal
    attention path while preserving the shared attention/Mamba block lifecycle.
    """
    if getattr(model_runner_class, "_mst_dasc_cascade_guard_installed", False):
        return

    from vllm.v1.kv_cache_interface import UniformTypeKVCacheSpecs

    original = model_runner_class._compute_cascade_attn_prefix_lens

    @functools.wraps(original)
    def compute_without_heterogeneous_cascade(self, *args, **kwargs):
        cache_config = getattr(self, "kv_cache_config", None)
        groups = getattr(cache_config, "kv_cache_groups", ())
        if any(
            isinstance(group.kv_cache_spec, UniformTypeKVCacheSpecs)
            for group in groups
        ):
            if not getattr(self, "_mst_dasc_cascade_guard_emitted", False):
                emit(
                    config.evidence_path,
                    "heterogeneous_cascade_disabled",
                    mode=config.mode,
                    cache_groups=len(groups),
                )
                self._mst_dasc_cascade_guard_emitted = True
            return None
        return original(self, *args, **kwargs)

    model_runner_class._compute_cascade_attn_prefix_lens = (
        compute_without_heterogeneous_cascade
    )
    model_runner_class._mst_dasc_cascade_guard_installed = True


def _install_heterogeneous_mamba_lifecycle_patch(
    config: DascConfig, mamba_utils: Any
) -> None:
    """Teach vLLM's Mamba copy lifecycle about the aggregate hybrid group.

    The aggregate cache group intentionally contains attention and heterogeneous
    Mamba layer specs so every layer shares one token-block lifecycle.  vLLM
    0.23's helper recognizes only groups whose outer spec is a MambaSpec and
    later iterates every layer name in such a group.  Preserve the aggregate
    scheduler group while exposing only its inner Mamba layers to the Mamba
    state-copy path.
    """
    if getattr(mamba_utils, "_mst_dasc_heterogeneous_lifecycle_installed", False):
        return

    import torch
    from vllm.v1.kv_cache_interface import MambaSpec, UniformTypeKVCacheSpecs

    original_get_groups = mamba_utils.get_mamba_groups
    original_create = mamba_utils.MambaCopyBuffers.create
    original_collect = mamba_utils.collect_mamba_copy_meta

    def aggregate_mamba_names(group):
        spec = group.kv_cache_spec
        if not isinstance(spec, UniformTypeKVCacheSpecs):
            return ()
        return tuple(
            name
            for name, inner_spec in spec.kv_cache_specs.items()
            if isinstance(inner_spec, MambaSpec)
        )

    def aggregate_groups(kv_cache_config):
        groups = []
        specs = []
        names_by_group = {}
        for group_id, group in enumerate(kv_cache_config.kv_cache_groups):
            names = aggregate_mamba_names(group)
            if not names:
                continue
            names_by_group[group_id] = names
            groups.append(group_id)
            specs.extend(group.kv_cache_spec.kv_cache_specs[name] for name in names)
        return groups, specs, names_by_group

    def get_dasc_mamba_groups(kv_cache_config):
        group_ids, specs, _ = aggregate_groups(kv_cache_config)
        if not group_ids:
            return original_get_groups(kv_cache_config)
        lifecycle = {
            (spec.block_size, spec.num_speculative_blocks, spec.mamba_cache_mode)
            for spec in specs
        }
        if len(lifecycle) != 1:
            raise DascRuntimeUnsupported(
                f"DASC aggregate Mamba lifecycle fields differ: {lifecycle}"
            )
        representative = specs[0]
        if representative.mamba_cache_mode != "align":
            raise DascRuntimeUnsupported("DASC aggregate requires Mamba align mode")
        if representative.num_speculative_blocks:
            raise DascRuntimeUnsupported(
                "DASC heterogeneous physical cache does not yet support speculative decoding"
            )
        return group_ids, representative

    @classmethod
    def create_dasc_copy_buffers(
        cls, max_num_reqs, kv_cache_config, copy_funcs, make_buffer
    ):
        group_ids, _, names_by_group = aggregate_groups(kv_cache_config)
        if not group_ids:
            return original_create(
                max_num_reqs, kv_cache_config, copy_funcs, make_buffer
            )
        mamba_group_ids, mamba_spec = get_dasc_mamba_groups(kv_cache_config)
        entries_per_req = (
            sum(len(names_by_group[group_id]) for group_id in mamba_group_ids)
            * len(copy_funcs)
        )
        count = max_num_reqs * entries_per_req
        return cls(
            src_ptrs=make_buffer(count, dtype=torch.int64),
            dst_ptrs=make_buffer(count, dtype=torch.int64),
            sizes=make_buffer(count, dtype=torch.int32),
            mamba_group_ids=mamba_group_ids,
            mamba_spec=mamba_spec,
        )

    @functools.wraps(original_collect)
    def collect_dasc_mamba_meta(
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
        _, _, names_by_group = aggregate_groups(kv_cache_config)
        if not any(group_id in names_by_group for group_id in group_ids):
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
        proxy_groups = list(kv_cache_config.kv_cache_groups)
        for group_id in group_ids:
            names = names_by_group.get(group_id)
            if names is not None:
                group = proxy_groups[group_id]
                proxy_groups[group_id] = SimpleNamespace(
                    layer_names=list(names),
                    kv_cache_spec=group.kv_cache_spec,
                )
        proxy_config = SimpleNamespace(kv_cache_groups=proxy_groups)
        return original_collect(
            copy_bufs,
            proxy_config,
            copy_funcs,
            group_ids,
            src_block_idx,
            dest_block_idx,
            accept_token_bias,
            req_state,
            forward_context,
        )

    mamba_utils.get_mamba_groups = get_dasc_mamba_groups
    mamba_utils.MambaCopyBuffers.create = create_dasc_copy_buffers
    mamba_utils.collect_mamba_copy_meta = collect_dasc_mamba_meta
    mamba_utils._mst_dasc_heterogeneous_lifecycle_installed = True
    emit(
        config.evidence_path,
        "heterogeneous_mamba_lifecycle_installed",
        mode=config.mode,
    )


def _retained_mask(module: Any, state: Any, config: DascConfig):
    import torch

    cached = getattr(module, "_mst_dasc_retained_mask", None)
    if cached is None:
        indices = retained_head_indices(module, config)
        cached = state.new_zeros(module.A_log.numel(), dtype=torch.bool)
        cached[indices] = True
        module._mst_dasc_retained_mask = cached

    return cached, unique_head_axis(tuple(state.shape), cached.numel())


def _install_physical_cache_patch(
    config: DascConfig,
    qwen_gdn_class: Any,
    get_forward_context: Any,
) -> None:
    """Install compact spec accounting and dense-ABI execution bridge."""
    if getattr(qwen_gdn_class, "_mst_dasc_physical_installed", False):
        return
    original_get_spec = qwen_gdn_class.get_kv_cache_spec
    original_core = qwen_gdn_class._forward_core

    @functools.wraps(original_get_spec)
    def compact_get_spec(self, vllm_config):
        dense_spec = original_get_spec(self, vllm_config)
        if dense_spec is None or len(dense_spec.shapes) != 2:
            raise DascRuntimeUnsupported(
                "DASC physical mode requires conv and temporal Mamba states"
            )
        retained = retained_head_indices(self, config)
        temporal_shape = tuple(dense_spec.shapes[1])
        head_axis = unique_head_axis(temporal_shape, self.A_log.numel())
        compact = compact_mamba_spec(
            dense_spec,
            state_index=1,
            head_axis=head_axis,
            retained_heads=retained.numel(),
        )
        self._mst_dasc_dense_temporal_shape = temporal_shape
        self._mst_dasc_temporal_head_axis = head_axis
        self._mst_dasc_max_active_blocks = (
            vllm_config.scheduler_config.max_num_seqs
            * (1 + dense_spec.num_speculative_blocks)
        )
        self._mst_dasc_dense_page_bytes = dense_spec.page_size_bytes
        self._mst_dasc_compact_page_bytes = compact.page_size_bytes
        return compact

    @functools.wraps(original_core)
    def physical_core(self, mixed_qkv, b, a, core_attn_out):
        forward_context = get_forward_context()
        metadata_map = forward_context.attn_metadata
        if metadata_map is None:
            return original_core(self, mixed_qkv, b, a, core_attn_out)
        if not isinstance(metadata_map, dict) or self.prefix not in metadata_map:
            raise DascRuntimeUnsupported("DASC cannot resolve live GDN metadata")
        original_metadata = metadata_map[self.prefix]
        remapped_metadata, plan = remap_ascend_gdn_metadata(original_metadata)

        bridge = getattr(self, "_mst_dasc_bound_bridge", None)
        if bridge is None:
            if len(self.kv_cache) != 2:
                raise DascRuntimeUnsupported(
                    "DASC physical mode requires two runner-owned cache tensors"
                )
            bridge = BoundActiveStateBridge(
                conv_storage=self.kv_cache[0],
                compact_temporal_storage=self.kv_cache[1],
                dense_temporal_shape=self._mst_dasc_dense_temporal_shape,
                temporal_head_axis=self._mst_dasc_temporal_head_axis,
                retained_indices=retained_head_indices(self, config),
                max_active_blocks=self._mst_dasc_max_active_blocks,
            )
            self._mst_dasc_bound_bridge = bridge
            emit(
                config.evidence_path,
                "physical_cache_bound",
                layer=self.prefix,
                mode=config.mode,
                dense_page_bytes=self._mst_dasc_dense_page_bytes,
                compact_page_bytes=self._mst_dasc_compact_page_bytes,
                persistent_bytes=bridge.persistent_bytes,
                num_blocks=self.kv_cache[0].shape[0],
            )

        original_cache = self.kv_cache
        conv_workspace, temporal_workspace = bridge.restore_active(plan.block_ids)
        self.kv_cache = (conv_workspace, temporal_workspace)
        metadata_map[self.prefix] = remapped_metadata
        succeeded = False
        try:
            result = original_core(self, mixed_qkv, b, a, core_attn_out)
            bridge.checkpoint_active()
            succeeded = True
            return result
        finally:
            if not succeeded:
                bridge.abort_active()
            metadata_map[self.prefix] = original_metadata
            self.kv_cache = original_cache

    qwen_gdn_class.get_kv_cache_spec = compact_get_spec
    qwen_gdn_class._forward_core = physical_core
    qwen_gdn_class._mst_dasc_physical_installed = True


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
    from vllm.distributed.parallel_state import get_tp_group
    from vllm.forward_context import get_forward_context
    from vllm.v1.worker import mamba_utils
    from vllm.v1.core import kv_cache_utils
    from vllm_ascend.ops import gdn
    from vllm_ascend.patch.worker import patch_mamba_utils as ascend_patch
    from vllm_ascend.worker import model_runner_v1

    guarded_sources = {
        "gdn": (gdn, config.expected_gdn_sha256),
        "mamba_patch": (ascend_patch, config.expected_mamba_patch_sha256),
        "model_runner": (model_runner_v1, config.expected_model_runner_sha256),
        "vllm_mamba_utils": (
            mamba_utils,
            config.expected_vllm_mamba_utils_sha256,
        ),
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
        if config.mode == "nr-numerical":
            _install_state_restore_patch(config, mamba_utils, ascend_patch)
        else:
            named_gdn_modules = sorted(
                (
                    (name, module)
                    for name, module in self.named_modules()
                    if isinstance(module, QwenGatedDeltaNetAttention)
                ),
                key=lambda item: item[0],
            )
            tp_group = get_tp_group()
            alignment = align_retained_heads_tp(
                named_gdn_modules, config, tp_group.device_group
            )
            emit(
                config.evidence_path,
                "tp_geometry_aligned",
                mode=config.mode,
                tp_rank=tp_group.rank_in_group,
                tp_world_size=tp_group.world_size,
                **alignment,
            )
            _install_physical_cache_patch(
                config, QwenGatedDeltaNetAttention, get_forward_context
            )
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
    if config.mode == "physical-cache-eager":
        _install_aligned_hybrid_grouping_patch(config, kv_cache_utils)
        _install_heterogeneous_cascade_guard(config, model_runner_v1.NPUModelRunner)
        _install_heterogeneous_mamba_lifecycle_patch(config, mamba_utils)
    emit(
        config.evidence_path,
        "plugin_registered",
        mode=config.mode,
        **source_evidence,
        vllm_version=versions["vllm"],
        vllm_ascend_version=versions["vllm-ascend"],
    )
