"""Explicit SAME-total-budget compact storage provider. DEFAULT OFF.
No controller, Torch import, admission, native cache deletion or allocator hole search.
The unchanged official cache factory decides native config from the reduced budget.
This leaf is an allocation seam; old padding worker/consumer MUST NOT accept it.
"""
import copy
from collections import defaultdict
import hashlib
import inspect
import os
import types
from pathlib import Path

FLAG = "QWEN36_KIVI_EXPLICIT_CACHE_PROVIDER"
TOTAL_BYTES = 6 * 1024**3
UTILS_SHA = "b89f9afa7f95fcc30412ae2031d5370a23e95f35d068fa14e5824dce1c900ee5"
INTERFACE_SHA = "8d6be98bbf75b3d55007b64ccf5afef047ca01790a432522f70a196412c103d9"
NATIVE_SHA = "c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"
RUNNER_SHA = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
LIFECYCLE_SHA = "20e49b37b1fc62201dd749813e5aba56dd9211bbaf140c672dca5162e190a533"
WRITER_SHA = "051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b"
MAX_LENGTH = 33792
SLOTS = 16

def need(value, message):
    if not value:
        raise ValueError(message)

def pin(value, digest):
    path = Path(inspect.getfile(inspect.unwrap(getattr(value, "__func__", value))))
    need(path.is_absolute() and path.is_file() and not path.is_symlink()
         and hashlib.sha256(path.read_bytes()).hexdigest() == digest,
         "exact original source identity: " + str(path))

def json_copy(value):
    import json
    return json.loads(json.dumps(value, sort_keys=True))

def native_summary(config, interface):
    """Scalars from REAL KVCacheConfig, not invented LAYOUT or model permission."""
    need(type(config) is interface.KVCacheConfig, "actual native KVCacheConfig")
    groups = []
    for group in config.kv_cache_groups:
        spec = group.kv_cache_spec
        if type(spec) is interface.FullAttentionSpec:
            need(spec.num_kv_heads == 1 and spec.head_size == spec.head_size_v == 256
                 and spec.sliding_window is spec.attention_chunk_size is None
                 and spec.kv_quant_mode == interface.KVQuantMode.NONE,
                 "actual regular Qwen TP4 FA D256/KV1 without alternate quantization")
            kind = "FA"
            spec_fields=dict(dtype=str(spec.dtype),head_size_v=spec.head_size_v,
                             page_size_padded=spec.page_size_padded)
        else:
            need(type(spec) is interface.MambaSpec
                 and spec.mamba_cache_mode == "none" and spec.num_speculative_blocks == 0
                 and spec.block_size == MAX_LENGTH,
                 "actual unchanged none-mode GDN, no speculative cache")
            kind = "GDN"
            spec_fields=dict(shapes=[list(s) for s in spec.shapes],dtypes=[str(d) for d in spec.dtypes],
                             page_size_padded=spec.page_size_padded,mamba_type=str(spec.mamba_type))
        need(type(spec.block_size) is int and spec.block_size > 0
             and type(spec.page_size_bytes) is int and spec.page_size_bytes > 0,
             "actual positive native page geometry")
        groups.append(dict(kind=kind, names=list(group.layer_names),
                           block_size=spec.block_size, page_bytes=spec.page_size_bytes,spec_fields=spec_fields))
    all_names = [name for group in groups for name in group["names"]]
    need(len(groups) == 4 and sorted(g["kind"] for g in groups) == ["FA", "GDN", "GDN", "GDN"]
         and all(len(g["names"]) == 16 for g in groups)
         and len(all_names) == len(set(all_names)) == 64,
         "source-supported 16FA/48GDN four-group shared-native layout")
    for group in groups:
        for name in group["names"]:
            index = int(name.split(".layers.", 1)[1].split(".", 1)[0])
            need(0 <= index < 64 and group["kind"] == ("FA" if index % 4 == 3 else "GDN"),
                 "actual layer kind/pattern preserved")
    need(sorted(int(n.split(".layers.",1)[1].split(".",1)[0]) for n in all_names)==list(range(64)),
         "all original model layer indices exactly once")
    need(len({g["page_bytes"] for g in groups}) == 1, "actual uniform hybrid page bytes")
    pools = [dict(size=t.size, shared_by=list(t.shared_by)) for t in config.kv_cache_tensors]
    need(type(config.num_blocks) is int and config.num_blocks > 0 and len(pools) == 16,
         "actual positive native block count and all16 pools")
    expected = [dict(size=groups[0]["page_bytes"] * config.num_blocks,
                     shared_by=[g["names"][i] for g in groups]) for i in range(16)]
    need(pools == expected, "official allocator shared_by/size/order unchanged")
    return dict(num_blocks=config.num_blocks, groups=groups, pools=pools,
                native_bytes=sum(p["size"] for p in pools))

def field_bytes(pages, bits):
    need(type(pages) is int and pages > 0 and type(bits) is int and bits in (2, 4),
         "source-supported physical pages and precision")
    return (pages * (128 * 256 * bits // 8 + 4 * 256 * 4)
            + pages * 128 * (256 * bits // 8 + 8 * 4)
            + SLOTS * 257 * 256 * 2 + (32 // bits) * 4)

def overhead(allocation_margin_bytes):
    """Charge persistent B16 metadata, full-prefill gather and packed scratch.
    Margin is an explicit proposal for allocator/opaque-op overhead, NOT a proof
    of its bound. Actual peak and native FIA activations remain an NPU gate.
    """
    need(type(allocation_margin_bytes) is int and allocation_margin_bytes > 0,
         "explicit positive separately reported unmeasured allocation margin")
    return dict(
        persistent_metadata_bytes=16 * SLOTS * ((MAX_LENGTH + 127) // 128 + MAX_LENGTH + 4) * 8,
        # list(128-tile gathers) and cat(K,V) coexist; serial owners/layers.
        full_prefill_gather_peak_bytes=2 * 32768 * 256 * 2 * 2,
        packed_score_probability_result_bytes=SLOTS * 6 * MAX_LENGTH * 2 * 2 + SLOTS * 6 * 256 * 2,
        allocation_margin_bytes=allocation_margin_bytes,
    )

def policy(config):
    cc, mc, pc, sc = (config.cache_config, config.model_config,
                      config.parallel_config, config.scheduler_config)
    need(cc.kv_cache_memory_bytes == TOTAL_BYTES and cc.num_gpu_blocks_override is None,
         "same explicit total6GiB; no hidden block override")
    need(mc.max_model_len == MAX_LENGTH and mc.enforce_eager is True
         and pc.tensor_parallel_size == 4 and pc.pipeline_parallel_size == 1
         and pc.decode_context_parallel_size == pc.prefill_context_parallel_size == 1,
         "unchanged actual eager TP4 length33792")
    need(config.speculative_config is None and config.kv_transfer_config is None
         and cc.mamba_cache_mode == "none" and cc.enable_prefix_caching is False
         and sc.disable_hybrid_kv_cache_manager is False and 1 <= sc.max_num_seqs <= SLOTS,
         "native hybrid/GDN/no-prefix/no-transfer/no-speculative policy")
    # B16 is NOT silently changed to the smaller resident-capacity bound.
    return sc.max_num_seqs

def mixed_policy(config):
    """Fixed32768 staged/matched domain only; no preemption/replay authority."""
    need(policy(config) == 16, "actual B16 scheduler, not a reduced C7 workload")
    sc = config.scheduler_config
    need(sc.max_num_batched_tokens == 40960 and sc.enable_chunked_prefill is True
         and sc.async_scheduling is False and sc.scheduler_reserve_full_isl is True
         and sc.long_prefill_token_threshold == 0
         and sc.max_num_partial_prefills == sc.max_long_partial_prefills == 1
         and sc.max_num_scheduled_tokens in (None, 40960),
         "source-supported full-input reservation/chunked policy; preemption unsupported")
    return 16

def plan(config, specs, utils, interface, *, bits, allocation_margin_bytes):
    pin(utils.get_kv_cache_groups, UTILS_SHA)
    pin(utils.get_kv_cache_config_from_groups, UTILS_SHA)
    pin(interface.KVCacheConfig, INTERFACE_SHA)
    policy(config)
    # The pinned Ascend runner returns defaultdict(list), with SPEC values.
    # Do not invoke its missing-key factory or flatten/reorder native entries.
    need(type(specs) in (dict, defaultdict)
         and (type(specs) is dict or specs.default_factory is list)
         and len(specs) == 64, "actual get_kv_cache_spec whole64")
    need(all(type(name) is str and type(spec) in (interface.FullAttentionSpec, interface.MambaSpec)
             for name, spec in specs.items()), "actual per-layer FA/GDN specs, not grouped/list values")
    groups = utils.get_kv_cache_groups(config, copy.deepcopy(specs))
    dense = utils.get_kv_cache_config_from_groups(config, groups, TOTAL_BYTES)
    dense_summary = native_summary(dense, interface)
    fa = next(g for g in dense_summary["groups"] if g["kind"] == "FA")
    need(fa["block_size"] % 128 == 0, "native FA block consists of whole K128 pages")
    charged = overhead(allocation_margin_bytes)
    unit = dense_summary["native_bytes"] // dense.num_blocks
    selected = None
    for blocks in range(dense.num_blocks, 0, -1):
        pages = blocks * fa["block_size"] // 128
        compact = 16 * field_bytes(pages, bits)
        if blocks * unit + compact + sum(charged.values()) <= TOTAL_BYTES:
            selected = (blocks, pages, compact)
            break
    need(selected is not None, "same-budget space for native plus explicit compact and overhead")
    blocks, pages, compact = selected
    native_budget = blocks * unit
    candidate = utils.get_kv_cache_config_from_groups(config, groups, native_budget)
    actual = native_summary(candidate, interface)
    need(candidate.num_blocks == blocks and actual["native_bytes"] == native_budget,
         "actual factory must reproduce selected integer block count")
    per_request = sum((g.kv_cache_spec.max_memory_usage_bytes(config) +
                       g.kv_cache_spec.page_size_bytes - 1) //
                      g.kv_cache_spec.page_size_bytes for g in groups)
    need(per_request > 0 and blocks >= per_request + 1,
         "at least one full-length native request plus conservative null block")
    return dict(schema="kivi.explicit-same-budget-plan/v1", bits=bits, slots=SLOTS,
                pages=pages, max_length=MAX_LENGTH, total_budget_bytes=TOTAL_BYTES,
                dense_control=dense_summary, native=actual,
                native_budget_returned_bytes=native_budget, compact_logical_bytes=compact,
                overhead=charged, charged_total_bytes=native_budget + compact + sum(charged.values()),
                unassigned_bytes=TOTAL_BYTES-native_budget-compact-sum(charged.values()),
                official_concurrency_excluding_null=utils.get_max_concurrency_for_kv_cache_config(config, candidate),
                blocks_per_full_request=per_request,
                full_resident_upper_bound=(blocks-1)//per_request,
                conservative_null_blocks=1, requested_max_num_seqs=config.scheduler_config.max_num_seqs,
                scheduler_preemption_supported=False, allocator_peak_checked=False,
                original_native_all64_preserved=True, native_capacity_reduced=True,
                allocation_replaced=False, compact_new_allocation_explicit=True,
                model_ready=False, performance_ready=False, run_authority=False)

def native_raw_check(raw, config, describe):
    need(type(raw) is dict, "actual original native raw mapping")
    names = {n for p in config.kv_cache_tensors for n in p.shared_by}
    need(set(raw) == names, "all64 native raw entries unchanged")
    unique = {}
    for pool in config.kv_cache_tensors:
        t = raw[pool.shared_by[0]]
        need(all(raw[n] is t for n in pool.shared_by), "actual native same-pool handles")
        d = describe(t)
        need(d["logical_bytes"] == pool.size and d["storage_bytes"] >= pool.size
             and d["storage_offset_elements"] == 0 and d["data_ptr"] == d["storage_base"],
             "original allocator full storage root")
        need(d["storage_base"] not in unique, "distinct native pools")
        unique[d["storage_base"]] = d
    return unique

def make_worker(native_cls, utils, interface, lifecycle, torch, *,
                bits, allocation_margin_bytes, describe, qualify, publish, consume_allocations,
                install_after_native):
    """Explicit subclass factory; existing MAIN host supplies the existing lease.
    install_after_native(worker, state) MUST be a source-qualified new consumer/
    model adapter. The old padding worker is incompatible and is not called.
    No admission is synthesized here, including when allocation succeeds.
    """
    if os.environ.get(FLAG) != "1":
        return native_cls
    for fn, sha in ((native_cls.determine_available_memory, NATIVE_SHA),
                    (native_cls.initialize_from_config, NATIVE_SHA),
                    (native_cls.get_kv_cache_spec, NATIVE_SHA),
                    (lifecycle.CompactArena.__init__, LIFECYCLE_SHA),
                    (lifecycle.allocate_writer_arena, WRITER_SHA),
                    (lifecycle.seal_k_into, WRITER_SHA),
                    (lifecycle.seal_v_into, WRITER_SHA),
                    (utils.get_kv_cache_groups, UTILS_SHA),
                    (interface.KVCacheConfig, INTERFACE_SHA)):
        pin(fn, sha)
    need(all(callable(x) for x in (describe, qualify, publish, consume_allocations, install_after_native)),
         "actual qualified source-bound descriptors/consumer/installer and external authority")
    original_memory = native_cls.determine_available_memory
    original_init = native_cls.initialize_from_config
    original_specs = native_cls.get_kv_cache_spec

    class ExplicitProviderWorker(native_cls):
        def determine_available_memory(self):
            need(not hasattr(self, "_kivi_explicit_provider"), "one provider plan per native worker")
            qualify()
            mixed_policy(self.vllm_config)
            # Preserve original compile/profile_run and fixed-budget semantics.
            available = original_memory(self)
            need(available == TOTAL_BYTES, "original profile returns actual total6GiB")
            # Native worker forwards to this method; qualify that second ABI edge.
            pin(self.model_runner.get_kv_cache_spec, RUNNER_SHA)
            proposal = plan(self.vllm_config, original_specs(self), utils, interface,
                            bits=bits, allocation_margin_bytes=allocation_margin_bytes)
            ref = publish("EXPLICIT-CACHE-PLAN", proposal)
            self._kivi_explicit_provider = dict(plan=proposal, plan_ref=ref, arenas={}, state="planned")
            return proposal["native_budget_returned_bytes"]

        def initialize_from_config(self, config):
            qualify()
            mixed_policy(self.vllm_config)
            state = self._kivi_explicit_provider
            need(state["state"] == "planned" and not state["arenas"], "one exact native initialization")
            need(native_summary(config, interface) == state["plan"]["native"],
                 "actual scheduler-delivered cache config matches source-factory plan")
            runner = self.model_runner
            donor = runner._allocate_kv_cache_tensors
            pin(donor, RUNNER_SHA)
            need("_allocate_kv_cache_tensors" not in vars(runner),
                 "do not overwrite another instance allocator wrapper")
            state["state"] = "allocating"
            installed = None
            def allocate(actual_runner, actual_config):
                need(actual_runner is runner and state["state"] == "allocating"
                     and native_summary(actual_config, interface) == state["plan"]["native"],
                     "same actual runner/config exactly once inside native memory pool")
                raw = donor(actual_config)  # original zeros + all FA/GDN aliases, unchanged
                native = native_raw_check(raw, actual_config, describe)
                state["native_raw"] = raw
                state["native_descriptors"] = native
                fa = next(g for g in state["plan"]["native"]["groups"] if g["kind"] == "FA")
                # Original algorithm constructor: all allocations exposed in arena.pool.
                # Completed arenas remain reachable. A constructor exception retains
                # its traceback; no recycle/fallback/retry after a partial failure.
                for name in fa["names"]:
                    arena = lifecycle.CompactArena(torch, state["plan"]["pages"], SLOTS, bits,
                        runner.model_config.dtype, runner.device,
                        field_bytes(state["plan"]["pages"], bits))
                    state["arenas"][name] = arena
                torch.npu.synchronize()
                compact = {name: {key: describe(value) for key, value in arena.pool.items()
                                  if key not in ("allocated_bytes", "dense_shadow_bytes")}
                           for name, arena in state["arenas"].items()}
                # Independent whole-storage disjointness + physical-byte consumer.
                result = consume_allocations(state["plan"], native, compact)
                state["allocation_ref"] = publish("EXPLICIT-CACHE-ALLOCATED", dict(
                    schema="kivi.explicit-cache-allocation/v1", plan_ref=state["plan_ref"],
                    native=list(native.values()), compact=compact, independent=result,
                    initialized_compact=True, native_original_mapping_returned=True,
                    model_ready=False, run_authority=False))
                state["state"] = "allocated"
                return raw
            installed = types.MethodType(allocate, runner)
            runner._allocate_kv_cache_tensors = installed
            primary = None
            try:
                result = original_init(self, config)
                need(state["state"] == "allocated", "actual original allocator invoked and completed")
            except BaseException as error:
                primary = error
                state["state"] = "failed"
                raise
            finally:
                if vars(runner).get("_allocate_kv_cache_tensors") is not installed:
                    state["state"] = "failed"
                    cleanup = ValueError("restore only exact owned instance allocation wrapper")
                    if primary is not None:
                        raise BaseExceptionGroup("primary allocation plus exact restore failure",
                                                 [primary, cleanup]) from primary
                    raise cleanup
                del runner._allocate_kv_cache_tensors
            # Original reshape/bind/zeroer have completed. No layer/GDN view was replaced.
            qualify()
            state["state"] = "native_initialized"
            try:
                install_after_native(self, state)
            except BaseException:
                state["state"] = "failed"
                raise
            state["state"] = "consumer_installed"
            return result
    return ExplicitProviderWorker

