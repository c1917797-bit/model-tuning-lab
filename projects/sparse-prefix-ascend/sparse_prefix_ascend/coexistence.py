"""Atomic native-KV / HYPIC-GDN coexistence for vLLM 0.23.

The paper keeps full-attention KV under the normal prefix cache while recurrent
checkpoints have an independent lifecycle.  HYPIC 0.8.5 already provides the
transactional GDN/conv material store, but its cumulative-prefix scheduler
rejects native prefix caching and pre-advances requests before vLLM can look up
KV blocks.

This adapter changes only those two integration seams:

* ready HYPIC prefixes are *predicted* before scheduling, not pre-advanced;
* the native KV lookup is allowed only for the predicted prefix and is bounded
  to exactly that prefix.

The existing HYPIC scheduler then verifies the native computed-token boundary,
attaches the normal exact-prefix worker plan, and restores recurrent state.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

_HYPIC_SCHEDULER_SHA256 = (
    "c19155be244b0fdca6cb97bf1a3c475568bfb1635e36512568d59735c241c55f"
)


class _CachingGuardBypass:
    """Expose false to HYPIC's legacy guard, then true to native vLLM."""

    def __init__(self) -> None:
        self.reads = 0

    def __bool__(self) -> bool:
        self.reads += 1
        return self.reads > 1


class _NativePrefixGate:
    """Temporarily bound native prefix lookups to ready recurrent material."""

    def __init__(self, manager: object, state: object, hypic_scheduler: object):
        self.manager = manager
        self.state = state
        self.hypic_scheduler = hypic_scheduler
        self.original: Callable | None = None
        self.had_override = False
        self.previous_override: object | None = None
        self.installed = False

    def install(self) -> None:
        original = getattr(self.manager, "get_computed_blocks", None)
        if not callable(original):
            raise RuntimeError(
                "Sparse Prefix requires KVCacheManager.get_computed_blocks()."
            )
        coordinator = getattr(self.manager, "coordinator", None)
        hash_block_size = int(
            getattr(coordinator, "hash_block_size", 0) or 0
        )
        if hash_block_size <= 0:
            raise RuntimeError(
                "Sparse Prefix could not determine the native hash block size."
            )
        empty = getattr(self.manager, "empty_kv_cache_blocks", None)
        if empty is None:
            raise RuntimeError(
                "Sparse Prefix requires KVCacheManager.empty_kv_cache_blocks."
            )

        instance_dict = getattr(self.manager, "__dict__", None)
        self.had_override = isinstance(instance_dict, dict) and (
            "get_computed_blocks" in instance_dict
        )
        if self.had_override:
            self.previous_override = instance_dict["get_computed_blocks"]
        self.original = original
        state = self.state
        hs = self.hypic_scheduler

        def get_computed_blocks_with_gate(request, *args, **kwargs):
            req_id = hs.extract_request_id(request)
            predicted = (
                None
                if req_id is None
                else state.scheduler_advanced_prefixes.get(str(req_id))
            )
            # Native KV must never become visible before all recurrent shards
            # have committed a matching checkpoint.
            if predicted is None:
                return empty, 0
            _seg_hash, prefix_end = predicted
            prefix_end = int(prefix_end)
            if bool(getattr(request, "skip_reading_prefix_cache", False)):
                return empty, 0
            if prefix_end <= 0 or prefix_end % hash_block_size:
                raise RuntimeError(
                    "Sparse Prefix recurrent checkpoint is not aligned to the "
                    f"native hash block size: prefix={prefix_end} "
                    f"hash_block={hash_block_size}."
                )
            hashes = getattr(request, "block_hashes", None)
            if not isinstance(hashes, (list, tuple)):
                raise RuntimeError(
                    "Sparse Prefix requires Request.block_hashes."
                )
            keep = prefix_end // hash_block_size
            if len(hashes) < keep:
                raise RuntimeError(
                    "Sparse Prefix request has fewer native block hashes than "
                    f"the ready checkpoint: hashes={len(hashes)} keep={keep}."
                )
            original_hashes = hashes
            request.block_hashes = list(hashes[:keep])
            try:
                result = original(request, *args, **kwargs)
            finally:
                request.block_hashes = original_hashes
            try:
                native_tokens = int(result[1])
            except (IndexError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Sparse Prefix could not parse the native prefix result."
                ) from exc
            if native_tokens != prefix_end:
                raise RuntimeError(
                    "Sparse Prefix atomic cache transaction is incomplete: "
                    f"ready recurrent checkpoint={prefix_end}, "
                    f"native KV hit={native_tokens}."
                )
            return result

        setattr(
            self.manager,
            "get_computed_blocks",
            get_computed_blocks_with_gate,
        )
        self.installed = True

    def restore(self) -> None:
        if not self.installed:
            return
        self.installed = False
        if self.had_override:
            setattr(
                self.manager,
                "get_computed_blocks",
                self.previous_override,
            )
            return
        try:
            delattr(self.manager, "get_computed_blocks")
        except AttributeError:
            if self.original is not None:
                setattr(self.manager, "get_computed_blocks", self.original)


def _predict_ready_waiting_prefixes(
    scheduler: object,
    *,
    state: object,
    config: object,
    hypic_scheduler: object,
) -> dict[str, tuple[int, bytes, int]]:
    """Predict exact hits without mutating Request.num_computed_tokens."""

    hs = hypic_scheduler
    if (
        not config.enable_prefill_pruning
        or state.pending_materializations
        or len(state.cache) == 0
    ):
        return {}
    predicted: dict[str, tuple[int, bytes, int]] = {}
    for request in hs._waiting_requests(scheduler):
        req_id = hs.extract_request_id(request)
        previous = hs._computed_tokens(request)
        if req_id is None or previous != 0:
            continue
        if not hs._request_can_replay(request, state=state):
            continue
        token_ids = hs._token_ids_for_request(
            request,
            req_id=req_id,
            state=state,
        )
        if not token_ids:
            continue
        entry = state.cache.longest_materialized_prefix(
            token_ids,
            min_ready_step=state.step_id,
            prefix_fingerprint=lambda end, req_id=req_id, token_ids=token_ids: (
                hs._request_prefix_hash(
                    req_id,
                    token_ids,
                    end,
                    state=state,
                )
            ),
        )
        if entry is None:
            continue
        prefix_end = len(entry.token_ids)
        if (
            prefix_end < config.min_rewrite_tokens
            or prefix_end >= len(token_ids)
        ):
            continue
        state.scheduler_advanced_prefixes[req_id] = (
            entry.seg_hash,
            prefix_end,
        )
        predicted[req_id] = (previous, entry.seg_hash, prefix_end)
        if not state.first_prune_logged:
            hs.emit_evidence(
                "sparse_prefix_native_kv_transaction",
                component="sparse_prefix_ascend",
                request_id=req_id,
                checkpoint_tokens=prefix_end,
                prefix_hash=entry.seg_hash.hex(),
                native_kv_owner=True,
                recurrent_owner="hypic_material_store",
            )
            state.first_prune_logged = True
    return predicted


def _scheduler_classes() -> tuple[type, ...]:
    classes: list[type] = []
    imports = (
        ("vllm.v1.core.sched.scheduler", ("Scheduler",)),
        ("vllm.v1.core.sched.async_scheduler", ("AsyncScheduler",)),
        (
            "vllm_ascend.core.scheduler_dynamic_batch",
            ("SchedulerDynamicBatch",),
        ),
        (
            "vllm_ascend.core.scheduler_profiling_chunk",
            ("ProfilingChunkScheduler",),
        ),
        (
            "vllm_ascend.core.recompute_scheduler",
            ("RecomputeScheduler", "AsyncRecomputeScheduler"),
        ),
        (
            "vllm_ascend.patch.platform.patch_balance_schedule",
            ("BalanceScheduler",),
        ),
    )
    for module_name, names in imports:
        try:
            module = __import__(module_name, fromlist=list(names))
        except Exception:
            continue
        for name in names:
            value = getattr(module, name, None)
            if isinstance(value, type) and value not in classes:
                classes.append(value)
    return tuple(classes)


def install_native_kv_coexistence(hypic_scheduler: object) -> tuple[str, ...]:
    """Patch HYPIC's validated exact-prefix path without editing its source."""

    source = Path(hypic_scheduler.__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != _HYPIC_SCHEDULER_SHA256:
        raise RuntimeError(
            "Sparse Prefix refuses an unreviewed HYPIC scheduler build: "
            f"path={source} sha256={digest}."
        )

    original_advance = hypic_scheduler._advance_ready_waiting_prefixes
    if not getattr(original_advance, "_sparse_prefix_predictor", False):
        def predict_ready(scheduler, *, state, config):
            return _predict_ready_waiting_prefixes(
                scheduler,
                state=state,
                config=config,
                hypic_scheduler=hypic_scheduler,
            )

        predict_ready._sparse_prefix_predictor = True
        predict_ready._sparse_prefix_original = original_advance
        hypic_scheduler._advance_ready_waiting_prefixes = predict_ready

    def patch_class(cls: type) -> bool:
        if cls.__dict__.get(
            "_sparse_prefix_native_kv_patch_installed",
            False,
        ):
            return False
        original_schedule = cls.schedule
        if not getattr(original_schedule, "_hypic_scheduler_wrapper", False):
            return False

        def schedule_with_sparse_prefix(self, *args, **kwargs):
            depth = int(
                getattr(self, "_sparse_prefix_schedule_wrapper_depth", 0) or 0
            )
            if depth:
                return original_schedule(self, *args, **kwargs)
            manager = getattr(self, "kv_cache_manager", None)
            if manager is None:
                raise RuntimeError(
                    "Sparse Prefix requires Scheduler.kv_cache_manager."
                )
            enabled = getattr(manager, "enable_caching", None)
            if enabled is not True:
                raise RuntimeError(
                    "Sparse Prefix requires native prefix caching enabled."
                )
            state = hypic_scheduler.get_or_create_runtime_state(self)
            gate = _NativePrefixGate(manager, state, hypic_scheduler)
            shim = _CachingGuardBypass()
            gate.install()
            manager.enable_caching = shim
            self._sparse_prefix_schedule_wrapper_depth = depth + 1
            try:
                return original_schedule(self, *args, **kwargs)
            finally:
                self._sparse_prefix_schedule_wrapper_depth = depth
                manager.enable_caching = enabled
                gate.restore()
                if shim.reads < 1:
                    raise RuntimeError(
                        "Sparse Prefix did not observe the reviewed HYPIC "
                        "native-cache guard."
                    )

        schedule_with_sparse_prefix._sparse_prefix_native_kv_wrapper = True
        schedule_with_sparse_prefix._sparse_prefix_original = original_schedule
        # Preserve HYPIC's runtime-hook proof after adding the outer wrapper.
        schedule_with_sparse_prefix._hypic_scheduler_wrapper = True
        cls.schedule = schedule_with_sparse_prefix
        cls._sparse_prefix_native_kv_patch_installed = True
        return True

    original_patch_method = hypic_scheduler._patch_schedule_method
    if not getattr(original_patch_method, "_sparse_prefix_patch_hook", False):
        def patch_method_then_sparse(cls, config):
            changed = original_patch_method(cls, config)
            return patch_class(cls) or changed

        patch_method_then_sparse._sparse_prefix_patch_hook = True
        patch_method_then_sparse._sparse_prefix_original = original_patch_method
        hypic_scheduler._patch_schedule_method = patch_method_then_sparse

    patched: list[str] = []
    for cls in _scheduler_classes():
        if patch_class(cls):
            patched.append(f"{cls.__module__}.{cls.__name__}")
    if not patched and not any(
        getattr(cls.schedule, "_sparse_prefix_native_kv_wrapper", False)
        for cls in _scheduler_classes()
    ):
        raise RuntimeError(
            "Sparse Prefix could not patch a reviewed HYPIC scheduler class."
        )
    logger.info(
        "Sparse Prefix native-KV/GDN coexistence active: %s",
        patched or "already patched",
    )
    return tuple(patched)
