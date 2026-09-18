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
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .config import DascConfig
from .evidence import emit
from .metadata import StableAscendGDNMetadataRemapper, remap_ascend_gdn_metadata
from .runtime import RequestActiveStateBridge
from .selector import (
    align_retained_heads_tp,
    retained_head_indices,
    unique_head_axis,
)
from .spec import compact_mamba_spec


class DascRuntimeUnsupported(RuntimeError):
    pass


def _resolve_kernel_blocks_per_manager_block(
    manager_block_table: Any,
) -> tuple[int, tuple[str, ...]]:
    """Resolve the physical-manager to logical-kernel block ratio.

    vLLM-Ascend v0.23 names this ratio 'blocks_per_phys_block' while
    upstream vLLM block tables use 'blocks_per_kv_block'. Geometry is an
    independent cross-version check when both physical and logical block
    sizes are exposed. Conflicting sources fail closed.
    """
    candidates: dict[str, int] = {}
    for attribute in (
        "blocks_per_phys_block",
        "blocks_per_kv_block",
    ):
        value = getattr(manager_block_table, attribute, None)
        if value is None:
            continue
        try:
            candidates[attribute] = int(value)
        except (TypeError, ValueError) as error:
            raise DascRuntimeUnsupported(
                f"DASC aggregate cache block-id scale {attribute} is invalid"
            ) from error

    physical = getattr(manager_block_table, "physical_block_size", None)
    logical = getattr(manager_block_table, "logical_block_size", None)
    if physical is not None and logical is not None:
        try:
            physical_value = int(physical)
            logical_value = int(logical)
        except (TypeError, ValueError) as error:
            raise DascRuntimeUnsupported(
                "DASC aggregate cache block geometry is invalid"
            ) from error
        if (
            physical_value < 1
            or logical_value < 1
            or physical_value % logical_value != 0
        ):
            raise DascRuntimeUnsupported(
                "DASC aggregate cache block geometry is not exactly divisible"
            )
        candidates["physical_block_size/logical_block_size"] = (
            physical_value // logical_value
        )

    if not candidates:
        raise DascRuntimeUnsupported(
            "DASC cannot resolve the aggregate cache block-id scale"
        )
    if any(value < 1 for value in candidates.values()):
        raise DascRuntimeUnsupported(
            "DASC aggregate cache block-id scale must be positive"
        )
    scales = set(candidates.values())
    if len(scales) != 1:
        raise DascRuntimeUnsupported(
            "DASC aggregate cache block-id scale sources disagree: "
            + repr(candidates)
        )
    return scales.pop(), tuple(sorted(candidates))


def _install_head256_prefill_fallback_patch(
    config: DascConfig, device_operator: Any, device_utils: Any
) -> None:
    """Route unsupported Qwen3.5 256-wide prefill heads to fusion attention.

    Ascend 910B's FIA TND path rejects a 256-wide no-RoPE head.  Upstream
    vLLM-Ascend already provides a paged-KV-aware NPU fusion-attention fallback
    for another unsupported large-head geometry (512).  Reuse that exact
    adaptor for Qwen3.5's 256-wide full-attention layers; decode remains on the
    existing paged-attention selection and supported FIA geometries are left
    untouched.
    """
    if getattr(device_operator, "_mst_dasc_head256_prefill_installed", False):
        return

    original = device_operator.npu_fused_infer_attention_score

    @classmethod
    def attention_with_head256_prefill_fallback(
        cls,
        query,
        key,
        value,
        attn_metadata,
        *,
        key_cache,
        value_cache,
        current_key,
        current_value,
        num_heads,
        num_key_value_heads,
        head_size,
        scale,
        is_prefill_no_cache,
        **kwargs,
    ):
        if head_size == 256:
            return device_utils.npu_large_head_prefill_attention(
                query,
                current_key,
                current_value,
                attn_metadata,
                key_cache=key_cache,
                value_cache=value_cache,
                num_heads=num_heads,
                num_kv_heads=num_key_value_heads,
                head_size=head_size,
                scale=scale,
                is_prefill_no_cache=is_prefill_no_cache,
            )
        return original(
            query=query,
            key=key,
            value=value,
            attn_metadata=attn_metadata,
            key_cache=key_cache,
            value_cache=value_cache,
            current_key=current_key,
            current_value=current_value,
            num_heads=num_heads,
            num_key_value_heads=num_key_value_heads,
            head_size=head_size,
            scale=scale,
            is_prefill_no_cache=is_prefill_no_cache,
            **kwargs,
        )

    device_operator.npu_fused_infer_attention_score = (
        attention_with_head256_prefill_fallback
    )
    device_operator._mst_dasc_head256_prefill_installed = True
    emit(
        config.evidence_path,
        "head256_prefill_fallback_installed",
        mode=config.mode,
        head_size=256,
        backend="npu_fusion_attention",
    )


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


def _tensor_sample_fingerprint(tensor: Any, *, max_samples: int = 64) -> dict[str, Any]:
    """Return an exact row digest plus bounded values for diagnosis.

    This helper is used at the first cache-hit transition. The normal scope is
    two representative layers; an explicit diagnostic-only switch expands it
    to all GDN layers. Copying those rows to the host is intentional: the
    numerical canary requires an exact byte digest and is never a performance
    measurement.
    """
    import torch

    flat = tensor.detach().reshape(-1)
    count = flat.numel()
    full = flat.to(device="cpu").contiguous()
    full_raw = full.view(torch.uint8).numpy().tobytes()
    if count == 0:
        indices: list[int] = []
        raw = b""
        finite = True
        sample_sum = 0.0
        sample_abs_max = 0.0
    else:
        sample_count = min(max_samples, count)
        if sample_count == 1:
            indices = [0]
        else:
            indices = [
                index * (count - 1) // (sample_count - 1)
                for index in range(sample_count)
            ]
        index_tensor = torch.tensor(indices, dtype=torch.long)
        sample = full.index_select(0, index_tensor).contiguous()
        raw = sample.view(torch.uint8).numpy().tobytes()
        sample_float = sample.float()
        finite = bool(torch.isfinite(sample_float).all().item())
        sample_sum = float(sample_float.sum().item())
        sample_abs_max = float(sample_float.abs().max().item())
    return {
        "shape": [int(value) for value in tensor.shape],
        "stride": [int(value) for value in tensor.stride()],
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "numel": int(count),
        "data_ptr": int(tensor.data_ptr()),
        "full_sha256": hashlib.sha256(full_raw).hexdigest(),
        "sample_indices": indices,
        "sample_sha256": hashlib.sha256(raw).hexdigest(),
        "sample_finite": finite,
        "sample_sum": sample_sum,
        "sample_abs_max": sample_abs_max,
    }


def _state_row_diagnostic_layer_names(
    names: list[str], *, full_scope: bool
) -> tuple[str, ...]:
    """Select a deterministic diagnostic scope without changing execution."""
    if not names:
        return ()
    if full_scope:
        return tuple(names)
    return tuple(dict.fromkeys((names[0], names[-1])))


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


def _install_heterogeneous_cache_config_awareness_patch(
    config: DascConfig,
    kv_cache_config_class: Any,
    kv_cache_utils: Any,
    engine_core: Any = None,
) -> None:
    """Preserve Mamba lifecycle flags across scheduler-config reduction.

    vLLM 0.23 reduces a ``UniformTypeKVCacheSpecs`` group to its first inner
    spec before constructing the scheduler. DASC deliberately puts attention
    first so the scheduler keeps the full-attention block manager, but that
    reduction otherwise erases the aggregate's inner Mamba layers. Mark the
    reduced scheduler config explicitly while teaching worker configs to
    inspect aggregate members. This restores block-aligned prefill splitting
    and cache zeroing without changing the scheduler's manager type.
    """
    if getattr(
        kv_cache_config_class,
        "_mst_dasc_heterogeneous_awareness_installed",
        False,
    ):
        return

    from vllm.v1.kv_cache_interface import (
        AttentionSpec,
        MambaSpec,
        UniformTypeKVCacheSpecs,
    )

    original_has_mamba = kv_cache_config_class.has_mamba_layers
    original_generate = kv_cache_utils.generate_scheduler_kv_cache_config
    if engine_core is None:
        engine_core = sys.modules.get("vllm.v1.engine.core")
    if (
        engine_core is not None
        and engine_core.generate_scheduler_kv_cache_config is not original_generate
    ):
        raise DascRuntimeUnsupported(
            "EngineCore scheduler cache-config alias differs from kv_cache_utils"
        )

    def aggregate_has_mamba(cache_config: Any) -> bool:
        for group in cache_config.kv_cache_groups:
            spec = group.kv_cache_spec
            if not isinstance(spec, UniformTypeKVCacheSpecs):
                continue
            if any(
                isinstance(inner_spec, MambaSpec)
                for inner_spec in spec.kv_cache_specs.values()
            ):
                return True
        return False

    @property
    def has_mamba_layers(cache_config: Any) -> bool:
        original_getter = getattr(original_has_mamba, "fget", None)
        if original_getter is None:
            raise DascRuntimeUnsupported(
                "KVCacheConfig.has_mamba_layers is no longer a property"
            )
        return bool(
            getattr(cache_config, "_mst_dasc_has_mamba_layers", False)
            or original_getter(cache_config)
            or aggregate_has_mamba(cache_config)
        )

    @functools.wraps(original_generate)
    def generate_dasc_scheduler_config(kv_cache_configs):
        preserve_mamba = any(aggregate_has_mamba(cfg) for cfg in kv_cache_configs)
        scheduler_config = original_generate(kv_cache_configs)
        if preserve_mamba:
            groups = scheduler_config.kv_cache_groups
            if not groups or not all(
                isinstance(group.kv_cache_spec, AttentionSpec) for group in groups
            ):
                raise DascRuntimeUnsupported(
                    "DASC scheduler reduction no longer preserves attention managers"
                )
            scheduler_config._mst_dasc_has_mamba_layers = True
            emit(
                config.evidence_path,
                "heterogeneous_scheduler_mamba_awareness_preserved",
                mode=config.mode,
                scheduler_group_specs=[
                    type(group.kv_cache_spec).__name__ for group in groups
                ],
                has_mamba_layers=scheduler_config.has_mamba_layers,
                needs_kv_cache_zeroing=(
                    scheduler_config.needs_kv_cache_zeroing
                ),
            )
        return scheduler_config

    kv_cache_config_class.has_mamba_layers = has_mamba_layers
    kv_cache_utils.generate_scheduler_kv_cache_config = (
        generate_dasc_scheduler_config
    )
    if engine_core is not None:
        engine_core.generate_scheduler_kv_cache_config = (
            generate_dasc_scheduler_config
        )
    kv_cache_config_class._mst_dasc_heterogeneous_awareness_installed = True
    emit(
        config.evidence_path,
        "heterogeneous_cache_config_awareness_installed",
        mode=config.mode,
        scheduler_alias_patched=engine_core is not None,
        scheduler_alias_deferred=engine_core is None,
        preserves_attention_manager=True,
        restores_mamba_block_aligned_split=True,
        restores_kv_cache_zeroing=True,
    )


def _install_scheduler_branch_evidence_patch(
    config: DascConfig, scheduler_class: Any
) -> None:
    """Prove lifecycle flags reach the scheduler branches that consume them.

    A true config property is only precondition evidence.  This wrapper emits
    bounded, branch-local events without changing scheduling decisions.
    """
    if getattr(scheduler_class, "_mst_dasc_branch_evidence_installed", False):
        return

    original_init = scheduler_class.__init__
    original_split = scheduler_class._mamba_block_aligned_split
    original_schedule = scheduler_class.schedule

    @functools.wraps(original_init)
    def init_with_branch_evidence(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        emit(
            config.evidence_path,
            "scheduler_mamba_lifecycle_initialized",
            mode=config.mode,
            has_mamba_layers=bool(self.has_mamba_layers),
            need_mamba_block_aligned_split=bool(
                self.need_mamba_block_aligned_split
            ),
            needs_kv_cache_zeroing=bool(self.needs_kv_cache_zeroing),
            block_size=int(self.block_size),
        )

    @functools.wraps(original_split)
    def split_with_branch_evidence(self, request, num_new_tokens, *args, **kwargs):
        result = original_split(self, request, num_new_tokens, *args, **kwargs)
        changed = int(result) != int(num_new_tokens)
        first_call = not getattr(
            self, "_mst_dasc_split_branch_emitted", False
        )
        first_changed = changed and not getattr(
            self, "_mst_dasc_changed_split_branch_emitted", False
        )
        if first_call or first_changed:
            emit(
                config.evidence_path,
                "scheduler_mamba_aligned_split_executed",
                mode=config.mode,
                request_id=getattr(request, "request_id", None),
                num_computed_tokens=int(request.num_computed_tokens),
                num_prompt_tokens=int(request.num_prompt_tokens),
                requested_tokens=int(num_new_tokens),
                scheduled_tokens=int(result),
                changed=changed,
            )
            self._mst_dasc_split_branch_emitted = True
            if changed:
                self._mst_dasc_changed_split_branch_emitted = True
        return result

    def count_block_ids(value):
        if value is None:
            return 0
        if isinstance(value, dict):
            return sum(count_block_ids(item) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return sum(
                count_block_ids(item)
                if isinstance(item, (dict, list, tuple, set))
                else 1
                for item in value
            )
        return 1

    @functools.wraps(original_schedule)
    def schedule_with_branch_evidence(self, *args, **kwargs):
        output = original_schedule(self, *args, **kwargs)
        block_count = count_block_ids(
            getattr(output, "new_block_ids_to_zero", None)
        )
        first_call = not getattr(self, "_mst_dasc_zero_branch_emitted", False)
        first_nonempty = block_count > 0 and not getattr(
            self, "_mst_dasc_nonempty_zero_branch_emitted", False
        )
        if first_call or first_nonempty:
            emit(
                config.evidence_path,
                "scheduler_kv_zeroing_branch_executed",
                mode=config.mode,
                new_block_count=block_count,
                nonempty=block_count > 0,
            )
            self._mst_dasc_zero_branch_emitted = True
            if block_count > 0:
                self._mst_dasc_nonempty_zero_branch_emitted = True
        return output

    scheduler_class.__init__ = init_with_branch_evidence
    scheduler_class._mamba_block_aligned_split = split_with_branch_evidence
    scheduler_class.schedule = schedule_with_branch_evidence
    scheduler_class._mst_dasc_branch_evidence_installed = True
    emit(
        config.evidence_path,
        "scheduler_branch_evidence_installed",
        mode=config.mode,
    )


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

        if not (known and attention and aligned):
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
            "aligned_hybrid_cache_grouped",
            mode=config.mode,
            heterogeneous_mamba_pages=heterogeneous,
            attention_layers=len(attention),
            mamba_layers=len(mamba),
            mamba_page_sizes=sorted(
                {spec.page_size_bytes for spec in mamba.values()}
            ),
            aggregate_page_bytes=aggregate.page_size_bytes,
        )
        if heterogeneous:
            emit(
                config.evidence_path,
                "heterogeneous_cache_grouped",
                mode=config.mode,
                attention_layers=len(attention),
                mamba_layers=len(mamba),
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
    original_copy = getattr(mamba_utils, "do_mamba_copy_block", None)
    if (
        config.mode == "physical-cache-native-all-heads-state-index"
        and original_copy is None
    ):
        raise DascRuntimeUnsupported(
            "DASC state-index mode requires the Mamba copy executor"
        )

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
        aggregate_layer_count = 0
        diagnostic_rows = []
        for group_id in group_ids:
            names = names_by_group.get(group_id)
            if names is not None:
                aggregate_layer_count += len(names)
                group = proxy_groups[group_id]
                proxy_groups[group_id] = SimpleNamespace(
                    layer_names=list(names),
                    kv_cache_spec=group.kv_cache_spec,
                )
                if config.mode == "physical-cache-native-all-heads-state-index":
                    block_ids = req_state.block_ids[group_id]
                    source_block_id = int(block_ids[src_block_idx])
                    destination_block_id = int(block_ids[dest_block_idx])
                    previous_destination = getattr(
                        req_state, "_mst_dasc_running_state_block_id", None
                    )
                    if (
                        previous_destination is not None
                        and previous_destination != destination_block_id
                    ):
                        raise DascRuntimeUnsupported(
                            "DASC aggregate groups disagree on the running state row"
                        )
                    req_state._mst_dasc_running_state_block_id = destination_block_id
                    if not getattr(
                        mamba_utils,
                        "_mst_dasc_physical_row_diagnostic_emitted",
                        False,
                    ):
                        full_diagnostics = bool(
                            getattr(config, "full_state_row_diagnostics", False)
                        )
                        selected_names = set(
                            _state_row_diagnostic_layer_names(
                                names,
                                full_scope=full_diagnostics,
                            )
                        )
                        for layer_name in names:
                            if layer_name not in selected_names:
                                continue
                            module = forward_context[layer_name]
                            for state_index, (state, state_copy_func) in enumerate(
                                zip(module.kv_cache, copy_funcs)
                            ):
                                copy_spec = state_copy_func(
                                    state,
                                    block_ids,
                                    src_block_idx,
                                    accept_token_bias + 1,
                                )
                                element_size = state.element_size()
                                byte_offset = copy_spec.start_addr - state.data_ptr()
                                if byte_offset < 0 or byte_offset % element_size:
                                    raise DascRuntimeUnsupported(
                                        "DASC state-copy pointer is outside tensor alignment"
                                    )
                                element_offset = byte_offset // element_size
                                flat = state.view(-1)
                                if (
                                    element_offset + copy_spec.num_elements
                                    > flat.numel()
                                ):
                                    raise DascRuntimeUnsupported(
                                        "DASC state-copy source range exceeds storage"
                                    )
                                source_view = flat.narrow(
                                    0, element_offset, copy_spec.num_elements
                                )
                                destination_row = state[destination_block_id].view(-1)
                                if copy_spec.num_elements > destination_row.numel():
                                    raise DascRuntimeUnsupported(
                                        "DASC state-copy destination range exceeds row"
                                    )
                                destination_view = destination_row.narrow(
                                    0, 0, copy_spec.num_elements
                                )
                                row_stride_elements = int(state.stride(0))
                                diagnostic_rows.append(
                                    {
                                        "module": module,
                                        "state": state,
                                        "source_view": source_view,
                                        "destination_view": destination_view,
                                        "payload": {
                                            "layer": layer_name,
                                            "state_index": state_index,
                                            "source_block_index": int(src_block_idx),
                                            "destination_block_index": int(
                                                dest_block_idx
                                            ),
                                            "source_block_id": source_block_id,
                                            "destination_block_id": (
                                                destination_block_id
                                            ),
                                            "accept_token_bias": int(
                                                accept_token_bias
                                            ),
                                            "diagnostic_scope": (
                                                "all_gdn_layers"
                                                if full_diagnostics
                                                else "first_last"
                                            ),
                                            "copy_elements": int(
                                                copy_spec.num_elements
                                            ),
                                            "copy_bytes": int(
                                                copy_spec.num_elements
                                                * element_size
                                            ),
                                            "state_base_ptr": int(
                                                state.data_ptr()
                                            ),
                                            "copy_source_ptr": int(
                                                copy_spec.start_addr
                                            ),
                                            "destination_row_ptr": int(
                                                state[
                                                    destination_block_id
                                                ].data_ptr()
                                            ),
                                            "row_stride_elements": (
                                                row_stride_elements
                                            ),
                                            "source_pointer_block_id": int(
                                                element_offset
                                                // row_stride_elements
                                            ),
                                            "source_within_row_elements": int(
                                                element_offset
                                                % row_stride_elements
                                            ),
                                            "source_before_copy": (
                                                _tensor_sample_fingerprint(
                                                    source_view
                                                )
                                            ),
                                            "destination_before_copy": (
                                                _tensor_sample_fingerprint(
                                                    destination_view
                                                )
                                            ),
                                        },
                                    }
                                )
        proxy_config = SimpleNamespace(kv_cache_groups=proxy_groups)
        offset_before = int(getattr(copy_bufs, "offset", 0))
        result = original_collect(
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
        offset_after = int(getattr(copy_bufs, "offset", offset_before))
        if diagnostic_rows:
            copy_bufs._mst_dasc_physical_row_diagnostics = diagnostic_rows
        if not getattr(mamba_utils, "_mst_dasc_copy_branch_emitted", False):
            emit(
                config.evidence_path,
                "heterogeneous_mamba_copy_branch_executed",
                mode=config.mode,
                group_ids=[int(group_id) for group_id in group_ids],
                source_block_index=int(src_block_idx),
                destination_block_index=int(dest_block_idx),
                accept_token_bias=int(accept_token_bias),
                mamba_layer_count=aggregate_layer_count,
                copy_entries_added=offset_after - offset_before,
            )
            mamba_utils._mst_dasc_copy_branch_emitted = True
        return result

    def copy_dasc_mamba_blocks(copy_bufs):
        assert original_copy is not None
        result = original_copy(copy_bufs)
        diagnostic_rows = getattr(
            copy_bufs, "_mst_dasc_physical_row_diagnostics", ()
        )
        if diagnostic_rows:
            for row in diagnostic_rows:
                payload = dict(row["payload"])
                payload["source_after_copy"] = _tensor_sample_fingerprint(
                    row["source_view"]
                )
                payload["destination_after_copy"] = _tensor_sample_fingerprint(
                    row["destination_view"]
                )
                emit(
                    config.evidence_path,
                    "physical_state_copy_materialized",
                    mode=config.mode,
                    **payload,
                )
                module = row["module"]
                ready = list(
                    getattr(module, "_mst_dasc_state_row_diagnostics_ready", ())
                )
                ready.append(
                    {
                        "state_index": payload["state_index"],
                        "source_block_id": payload["source_block_id"],
                        "destination_block_id": payload[
                            "destination_block_id"
                        ],
                    }
                )
                module._mst_dasc_state_row_diagnostics_ready = tuple(ready)
            copy_bufs._mst_dasc_physical_row_diagnostics = []
            mamba_utils._mst_dasc_physical_row_diagnostic_emitted = True
        return result

    mamba_utils.get_mamba_groups = get_dasc_mamba_groups
    mamba_utils.MambaCopyBuffers.create = create_dasc_copy_buffers
    mamba_utils.collect_mamba_copy_meta = collect_dasc_mamba_meta
    if config.mode == "physical-cache-native-all-heads-state-index":
        mamba_utils.do_mamba_copy_block = copy_dasc_mamba_blocks
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
    model_runner_class: Any,
    get_forward_context: Any,
) -> None:
    """Install compact accounting and a graph-boundary dense ABI bridge."""
    if getattr(qwen_gdn_class, "_mst_dasc_physical_installed", False):
        return
    original_get_spec = qwen_gdn_class.get_kv_cache_spec
    original_model_forward = model_runner_class._model_forward
    original_dummy_run = getattr(model_runner_class, "_dummy_run", None)

    if original_dummy_run is not None:
        @functools.wraps(original_dummy_run)
        def dummy_run_with_explicit_scope(self, *args, **kwargs):
            previous = getattr(self, "_mst_dasc_dummy_scope", False)
            self._mst_dasc_dummy_scope = True
            try:
                return original_dummy_run(self, *args, **kwargs)
            finally:
                self._mst_dasc_dummy_scope = previous

        model_runner_class._dummy_run = dummy_run_with_explicit_scope

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
        preserve_dense_padding = getattr(
            config, "preserve_dense_page_padding", False
        )
        if preserve_dense_padding:
            if (
                config.mode
                != "physical-cache-native-all-heads-state-index"
                or retained.numel() != self.A_log.numel()
            ):
                raise DascRuntimeUnsupported(
                    "dense page-padding control requires native all-heads "
                    "state-index mode"
                )
            compact = dense_spec
        else:
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
        self._mst_dasc_page_padding_preserved = preserve_dense_padding
        return compact

    def bind_bridge(module):
        bridge = getattr(module, "_mst_dasc_bound_bridge", None)
        if bridge is not None:
            return bridge
        if len(module.kv_cache) != 2:
            raise DascRuntimeUnsupported(
                "DASC physical mode requires two runner-owned cache tensors"
            )
        bridge = RequestActiveStateBridge(
            conv_storage=module.kv_cache[0],
            compact_temporal_storage=module.kv_cache[1],
            dense_temporal_shape=module._mst_dasc_dense_temporal_shape,
            temporal_head_axis=module._mst_dasc_temporal_head_axis,
            retained_indices=retained_head_indices(module, config),
            max_active_requests=module._mst_dasc_max_active_blocks,
        )
        module._mst_dasc_bound_bridge = bridge
        module._mst_dasc_persistent_cache = module.kv_cache
        num_blocks = bridge.conv_storage.shape[0]
        expected_persistent_bytes = (
            module._mst_dasc_compact_page_bytes * num_blocks
        )
        if bridge.persistent_bytes != expected_persistent_bytes:
            raise DascRuntimeUnsupported(
                "DASC runner allocation does not match compact cache spec: "
                f"actual={bridge.persistent_bytes} "
                f"expected={expected_persistent_bytes}"
            )
        emit(
            config.evidence_path,
            "physical_cache_bound",
            layer=module.prefix,
            mode=config.mode,
            dense_page_bytes=module._mst_dasc_dense_page_bytes,
            compact_page_bytes=module._mst_dasc_compact_page_bytes,
            persistent_bytes=bridge.persistent_bytes,
            actual_page_bytes=bridge.persistent_bytes // num_blocks,
            allocation_matches_spec=True,
            num_blocks=num_blocks,
        )
        return bridge

    def verify_native_all_heads(module):
        if getattr(module, "_mst_dasc_native_all_heads_verified", False):
            return
        retained = retained_head_indices(module, config)
        if retained.numel() != module.A_log.numel():
            raise DascRuntimeUnsupported(
                "native all-heads control requires every local GDN head"
            )
        if len(module.kv_cache) != 2:
            raise DascRuntimeUnsupported(
                "native all-heads control requires two runner-owned cache tensors"
            )
        conv_storage, temporal_storage = module.kv_cache
        if tuple(temporal_storage.shape[1:]) != tuple(
            module._mst_dasc_dense_temporal_shape
        ):
            raise DascRuntimeUnsupported(
                "native all-heads temporal cache does not match the dense ABI"
            )
        num_blocks = conv_storage.shape[0]
        persistent_bytes = (
            conv_storage.numel() * conv_storage.element_size()
            + temporal_storage.numel() * temporal_storage.element_size()
        )
        if num_blocks <= 0 or persistent_bytes % num_blocks:
            raise DascRuntimeUnsupported(
                "native all-heads cache has invalid block geometry"
            )
        payload_page_bytes = persistent_bytes // num_blocks
        reserved_page_bytes = module._mst_dasc_compact_page_bytes
        reserved_bytes = reserved_page_bytes * num_blocks
        padding_bytes_per_page = reserved_page_bytes - payload_page_bytes
        padding_preserved = getattr(
            module, "_mst_dasc_page_padding_preserved", False
        )
        if padding_preserved:
            if (
                reserved_page_bytes != module._mst_dasc_dense_page_bytes
                or persistent_bytes >= reserved_bytes
                or padding_bytes_per_page <= 0
            ):
                raise DascRuntimeUnsupported(
                    "dense page-padding control did not preserve a larger "
                    "dense reservation"
                )
        elif persistent_bytes != reserved_bytes:
            raise DascRuntimeUnsupported(
                "native all-heads allocation does not match cache spec: "
                f"actual={persistent_bytes} expected={reserved_bytes}"
            )
        emit(
            config.evidence_path,
            "physical_cache_bound",
            layer=module.prefix,
            mode=config.mode,
            dense_page_bytes=module._mst_dasc_dense_page_bytes,
            compact_page_bytes=module._mst_dasc_compact_page_bytes,
            persistent_bytes=persistent_bytes,
            actual_page_bytes=payload_page_bytes,
            allocation_matches_spec=persistent_bytes == reserved_bytes,
            page_padding_preserved=padding_preserved,
            payload_bytes=persistent_bytes,
            payload_page_bytes=payload_page_bytes,
            reserved_bytes=reserved_bytes,
            reserved_page_bytes=reserved_page_bytes,
            padding_bytes_per_page=padding_bytes_per_page,
            payload_fits_reserved_page=persistent_bytes <= reserved_bytes,
            native_all_heads=True,
            num_blocks=num_blocks,
        )
        module._mst_dasc_native_all_heads_verified = True

    @functools.wraps(original_model_forward)
    def model_forward_with_physical_bridge(self, *args, **kwargs):
        forward_context = get_forward_context()
        metadata_map = forward_context.attn_metadata
        if metadata_map is None:
            return original_model_forward(self, *args, **kwargs)
        if not isinstance(metadata_map, dict):
            raise DascRuntimeUnsupported("DASC cannot resolve live GDN metadata")
        modules = getattr(self, "_mst_dasc_gdn_modules", None)
        if modules is None:
            modules = tuple(
                module
                for module in self.model.modules()
                if isinstance(module, qwen_gdn_class)
            )
            self._mst_dasc_gdn_modules = modules
        if config.mode in {
            "physical-cache-native-all-heads",
            "physical-cache-native-all-heads-state-index",
        }:
            for module in modules:
                verify_native_all_heads(module)
            if config.mode == "physical-cache-native-all-heads":
                return original_model_forward(self, *args, **kwargs)

            owner_ids = tuple(self.input_batch.req_ids)
            is_dummy = getattr(self, "_mst_dasc_dummy_scope", False)
            try:
                manager_block_table = self.input_batch.block_table[0]
            except (AttributeError, IndexError, TypeError) as error:
                raise DascRuntimeUnsupported(
                    "DASC cannot resolve the aggregate cache block-id scale"
                ) from error
            (
                kernel_blocks_per_manager_block,
                block_scale_sources,
            ) = _resolve_kernel_blocks_per_manager_block(manager_block_table)
            originals = []
            boundary_rows = []
            mapping_evidence = []
            copy_remap_active = False
            try:
                for module in modules:
                    if module.prefix not in metadata_map:
                        raise DascRuntimeUnsupported(
                            f"DASC metadata missing GDN layer {module.prefix}"
                        )
                    original_metadata = metadata_map[module.prefix]
                    remapper = getattr(
                        module, "_mst_dasc_state_index_remapper", None
                    )
                    if remapper is None:
                        remapper = StableAscendGDNMetadataRemapper()
                        module._mst_dasc_state_index_remapper = remapper
                    _, identity_plan = remap_ascend_gdn_metadata(
                        original_metadata
                    )
                    # Attention layers can virtually split one 1536-token
                    # scheduler block into smaller kernel blocks. GDN state
                    # storage remains indexed by the unsplit scheduler block,
                    # so normalize the live metadata ids before applying a
                    # copied running-state destination.
                    active_slots = (
                        identity_plan.block_ids
                        // kernel_blocks_per_manager_block
                    )
                    source_values = []
                    normalized_source_values = []
                    destination_values = []
                    if not is_dummy and owner_ids:
                        source_indices = (
                            original_metadata.non_spec_state_indices_tensor
                        )
                        if (
                            source_indices is None
                            or source_indices.ndim != 1
                            or source_indices.numel() < len(owner_ids)
                        ):
                            raise DascRuntimeUnsupported(
                                "DASC cannot align owners to native state indices"
                            )
                        source_values = [
                            int(value)
                            for value in source_indices[: len(owner_ids)]
                            .detach()
                            .to(device="cpu")
                            .tolist()
                        ]
                        normalized_source_values = [
                            value // kernel_blocks_per_manager_block
                            for value in source_values
                        ]
                        destination_values = []
                        for owner, source_value in zip(
                            owner_ids, normalized_source_values
                        ):
                            request = self.requests[owner]
                            destination_values.append(
                                int(
                                    getattr(
                                        request,
                                        "_mst_dasc_running_state_block_id",
                                        source_value,
                                    )
                                )
                            )
                        copy_remap_active = copy_remap_active or any(
                            source_value != destination_value
                            for source_value, destination_value in zip(
                                normalized_source_values,
                                destination_values,
                            )
                        )
                        mapping = {}
                        for source_value, destination_value in zip(
                            source_values, destination_values
                        ):
                            previous = mapping.get(source_value)
                            if (
                                previous is not None
                                and previous != destination_value
                            ):
                                raise DascRuntimeUnsupported(
                                    "DASC owners disagree on state-index remap"
                                )
                            mapping[source_value] = destination_value
                        plan_values = {
                            int(value)
                            for value in identity_plan.block_ids.detach()
                            .to(device="cpu")
                            .tolist()
                        }
                        if not set(mapping).issubset(plan_values):
                            raise DascRuntimeUnsupported(
                                "DASC owner state rows are absent from metadata plan"
                            )
                        for source_value, destination_value in mapping.items():
                            active_slots[
                                identity_plan.block_ids == source_value
                            ] = destination_value
                    remapped_metadata, _ = remapper.prepare(
                        original_metadata,
                        active_slots=active_slots,
                    )
                    metadata_map[module.prefix] = remapped_metadata
                    originals.append((module, original_metadata))
                    if source_values:
                        mapping_evidence.append(
                            {
                                "layer": module.prefix,
                                "source_state_indices": source_values,
                                "normalized_source_state_indices": (
                                    normalized_source_values
                                ),
                                "destination_state_indices": (
                                    destination_values
                                ),
                                "kernel_blocks_per_manager_block": (
                                    kernel_blocks_per_manager_block
                                ),
                                "block_scale_sources": list(
                                    block_scale_sources
                                ),
                                "metadata_pointer": int(
                                    remapped_metadata.non_spec_state_indices_tensor.data_ptr()
                                ),
                            }
                        )
                    diagnostics = getattr(
                        module, "_mst_dasc_state_row_diagnostics_ready", ()
                    )
                    for diagnostic in diagnostics:
                        state = module.kv_cache[diagnostic["state_index"]]
                        source_block_id = diagnostic["source_block_id"]
                        destination_block_id = diagnostic[
                            "destination_block_id"
                        ]
                        boundary_rows.append(
                            {
                                "module": module,
                                "state": state,
                                "payload": {
                                    "layer": module.prefix,
                                    "state_index": diagnostic["state_index"],
                                    "source_block_id": source_block_id,
                                    "destination_block_id": (
                                        destination_block_id
                                    ),
                                    "owner_ids": [str(owner) for owner in owner_ids],
                                    "source_state_indices": source_values,
                                    "normalized_source_state_indices": (
                                        normalized_source_values
                                    ),
                                    "destination_state_indices": (
                                        destination_values
                                    ),
                                    "kernel_blocks_per_manager_block": (
                                        kernel_blocks_per_manager_block
                                    ),
                                    "source_before_native": (
                                        _tensor_sample_fingerprint(
                                            state[source_block_id]
                                        )
                                    ),
                                    "destination_before_native": (
                                        _tensor_sample_fingerprint(
                                            state[destination_block_id]
                                        )
                                    ),
                                },
                            }
                        )
                initial_mapping_pending = not getattr(
                    self, "_mst_dasc_state_index_mapping_emitted", False
                )
                copy_mapping_pending = (
                    copy_remap_active
                    and not getattr(
                        self,
                        "_mst_dasc_copy_state_index_mapping_emitted",
                        False,
                    )
                )
                if mapping_evidence and (
                    initial_mapping_pending or copy_mapping_pending
                ):
                    emit(
                        config.evidence_path,
                        "gdn_running_state_indices_remapped",
                        mode=config.mode,
                        layer_count=len(mapping_evidence),
                        copy_remap_active=copy_remap_active,
                        kernel_blocks_per_manager_block=(
                            kernel_blocks_per_manager_block
                        ),
                        block_scale_sources=list(block_scale_sources),
                        representative_layers=(
                            mapping_evidence
                            if getattr(
                                config,
                                "full_state_row_diagnostics",
                                False,
                            )
                            else [mapping_evidence[0], mapping_evidence[-1]]
                        ),
                    )
                    if initial_mapping_pending:
                        self._mst_dasc_state_index_mapping_emitted = True
                    if copy_remap_active:
                        self._mst_dasc_copy_state_index_mapping_emitted = True
                for row in boundary_rows:
                    emit(
                        config.evidence_path,
                        "first_resumed_token_state_boundary_before",
                        mode=config.mode,
                        **row["payload"],
                    )
                result = original_model_forward(self, *args, **kwargs)
                for row in boundary_rows:
                    payload = row["payload"]
                    state = row["state"]
                    emit(
                        config.evidence_path,
                        "first_resumed_token_state_boundary_after",
                        mode=config.mode,
                        layer=payload["layer"],
                        state_index=payload["state_index"],
                        source_block_id=payload["source_block_id"],
                        destination_block_id=payload[
                            "destination_block_id"
                        ],
                        source_after_native=_tensor_sample_fingerprint(
                            state[payload["source_block_id"]]
                        ),
                        destination_after_native=_tensor_sample_fingerprint(
                            state[payload["destination_block_id"]]
                        ),
                    )
                    row["module"]._mst_dasc_state_row_diagnostics_ready = ()
                return result
            finally:
                for module, original_metadata in originals:
                    metadata_map[module.prefix] = original_metadata

        active = []
        succeeded = False
        is_dummy = getattr(self, "_mst_dasc_dummy_scope", False)
        try:
            owner_ids = tuple(self.input_batch.req_ids)
            restore_mask = None
            for module in modules:
                if module.prefix not in metadata_map:
                    raise DascRuntimeUnsupported(
                        f"DASC metadata missing GDN layer {module.prefix}"
                    )
                original_metadata = metadata_map[module.prefix]
                remapper = getattr(module, "_mst_dasc_metadata_remapper", None)
                if remapper is None:
                    remapper = StableAscendGDNMetadataRemapper()
                    module._mst_dasc_metadata_remapper = remapper
                bridge = bind_bridge(module)
                if is_dummy:
                    # Capture uses synthetic metadata, not scheduler requests.
                    # Reuse the same buffers later used for real graph replay.
                    if bridge.active_owners:
                        raise DascRuntimeUnsupported(
                            "DASC dummy execution cannot overwrite live request state"
                        )
                    remapped_metadata, plan = remapper.prepare(original_metadata)
                    if plan.block_ids.numel() > bridge.workspace_cache[0].shape[0]:
                        raise DascRuntimeUnsupported(
                            "DASC dummy state count exceeds fixed workspace capacity"
                        )
                    for tensor in bridge.workspace_cache:
                        tensor.zero_()
                    module.kv_cache = bridge.workspace_cache
                    metadata_map[module.prefix] = remapped_metadata
                    active.append((module, bridge, original_metadata, (), plan.block_ids))
                    continue
                state_indices = original_metadata.non_spec_state_indices_tensor
                if state_indices is None:
                    raise DascRuntimeUnsupported(
                        "DASC request bridge requires non-spec state indices"
                    )
                if state_indices.ndim != 1 or state_indices.numel() < len(owner_ids):
                    raise DascRuntimeUnsupported(
                        "DASC request bridge cannot align requests to state indices"
                    )
                source_blocks = state_indices[:len(owner_ids)]
                if restore_mask is None:
                    restore_mask = source_blocks.new_tensor(
                        [
                            self.requests[owner].num_computed_tokens > 0
                            for owner in owner_ids
                        ],
                        dtype=bool,
                    )
                prior_owners = bridge.active_owners
                bridge.release(
                    tuple(prior_owners.difference(owner_ids))
                )
                continuing = tuple(
                    owner for owner in owner_ids if owner in prior_owners
                )
                new_owners = tuple(
                    owner for owner in owner_ids if owner not in prior_owners
                )
                request_slots = bridge.activate(
                    owner_ids, source_blocks, restore_mask
                )
                if (
                    new_owners
                    and not getattr(
                        module, "_mst_dasc_request_init_emitted", False
                    )
                ):
                    restored_count = sum(
                        self.requests[owner].num_computed_tokens > 0
                        for owner in new_owners
                    )
                    emit(
                        config.evidence_path,
                        "request_active_state_initialized",
                        layer=module.prefix,
                        mode=config.mode,
                        new_request_count=len(new_owners),
                        restored_prefix_count=restored_count,
                        zero_initialized_count=len(new_owners) - restored_count,
                    )
                    module._mst_dasc_request_init_emitted = True
                if (
                    continuing
                    and not getattr(
                        module, "_mst_dasc_request_continuity_emitted", False
                    )
                ):
                    emit(
                        config.evidence_path,
                        "request_active_state_continued",
                        layer=module.prefix,
                        mode=config.mode,
                        continued_request_count=len(continuing),
                    )
                    module._mst_dasc_request_continuity_emitted = True
                sorted_blocks, order = source_blocks.sort()
                if sorted_blocks.unique().numel() != sorted_blocks.numel():
                    raise DascRuntimeUnsupported(
                        "DASC active requests share a physical state block"
                    )
                slots_by_sorted_block = request_slots.index_select(
                    0, order
                )
                remapped_metadata, plan = remapper.prepare(
                    original_metadata,
                    active_slots=slots_by_sorted_block,
                )
                if not plan.block_ids.equal(sorted_blocks):
                    raise DascRuntimeUnsupported(
                        "DASC metadata contains state blocks outside active requests"
                    )
                module.kv_cache = bridge.workspace_cache
                metadata_map[module.prefix] = remapped_metadata
                active.append(
                    (module, bridge, original_metadata, owner_ids, source_blocks)
                )

            result = original_model_forward(self, *args, **kwargs)
            for _, bridge, _, owners, destination_blocks in active:
                if not is_dummy:
                    bridge.checkpoint(owners, destination_blocks)
            succeeded = True
            return result
        finally:
            if not succeeded:
                for _, bridge, _, owners, _ in active:
                    bridge.release(owners)
            for module, _, original_metadata, _, _ in active:
                module.kv_cache = module._mst_dasc_persistent_cache
                metadata_map[module.prefix] = original_metadata

    qwen_gdn_class.get_kv_cache_spec = compact_get_spec
    model_runner_class._model_forward = model_forward_with_physical_bridge
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
    from vllm.v1.core.sched.scheduler import Scheduler
    from vllm.v1.kv_cache_interface import KVCacheConfig
    from vllm_ascend.ops import gdn
    from vllm_ascend.device import device_op, utils as device_utils
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

    if config.mode == "compat-head256":
        _install_head256_prefill_fallback_patch(
            config, device_op.DeviceOperator, device_utils
        )
        emit(
            config.evidence_path,
            "compatibility_only_registered",
            mode=config.mode,
            **source_evidence,
            vllm_version=versions["vllm"],
            vllm_ascend_version=versions["vllm-ascend"],
        )
        return

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
                config,
                QwenGatedDeltaNetAttention,
                model_runner_v1.NPUModelRunner,
                get_forward_context,
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
    if config.mode in {
        "physical-cache-eager",
        "physical-cache-native-all-heads",
        "physical-cache-native-all-heads-state-index",
    }:
        _install_head256_prefill_fallback_patch(
            config, device_op.DeviceOperator, device_utils
        )
        _install_heterogeneous_cache_config_awareness_patch(
            config,
            KVCacheConfig,
            kv_cache_utils,
        )
        _install_scheduler_branch_evidence_patch(config, Scheduler)
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
