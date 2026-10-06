# DAMP cache identity v1 — CPU/pre-writer preparation, default OFF

Scope: source-bound Ascend runner cache allocation/group observation, early
FA cache-zero admission, and all-layer mixed-turn byte-footprint admission.
No Docker, build, Torch load, NPU execution, Git mutation, or real serving
validation was performed by this preparer. This package never emits ready=true,
NPU-pass, protected-lifecycle, memory-saving, or performance claims.

## Real seams and source evidence

- Actual NPUModelRunner._update_states(self, scheduler_output), runner lines
  729–744, delegates to GPUModelRunner._update_states. The parent removes
  finished requests then calls _zero_block_ids at lines 1151–1154 BEFORE
  adding/reordering new rows. Paused requests remain in runner.requests.
- observe_cold(runner, config, raw, typed) is called AFTER the core-owned
  typed reshape returns, BEFORE native _init_kv_zero_meta. It records actual
  typed storage bases, nbytes, offsets, shapes, strides, dtypes, groups and
  config.kv_cache_tensors.shared_by. It never copies cache contents.
- Actual AscendKVBlockZeroer.init_meta(self, attn_groups_iter,
  kernel_block_sizes, cache_dtype, runner_only_attn_layers,
  static_forward_context) uses separate K/V axis-0 views, skips Mamba,
  deduplicates data_ptr, and sets a uniform page width:
  stride(0)*element_size*(spec.block_size/kernel_block_sizes[gid][0]).
  The kernel actually stores int32 zeros; the int64 comment is not the ABI.
- SOURCE_MANIFEST pins the stopped-image snapshots supplied by MAIN and the
  byte-identical source interfaces. Metadata/source inspection is not proof
  that the runtime device table, native writers, or scheduler lifecycle have
  been successfully exercised.

## Explicit opt-in wiring (no automatic registration)

Import adapter.py independently. MAIN/core plugin supplies the native
FullAttentionSpec/MambaSpec classes, actual immutable image ID, and ALL48
frozen continuous LeaseBooks. Their class source file must match the frozen
continuous contract; sharing one module object is not assumed.

1. Owner(image_id, full_attention_type, mamba_type, leases).
2. Call owner.observe_cold(runner,config,raw,typed) from the core-owned reshape
   wrapper. No persistent dense state sidecar or allocator replacement.
3. install_zeroer_init(AscendKVBlockZeroer, owner_for_zeroer, enabled=True).
   The resolver must select this exact runner's new zeroer. The original
   generator is consumed once/materialized; all native scalar/tensor args
   and native return identity are retained. Unknown owners remain native.
4. install_runner_update(NPUModelRunner,owner_for,enabled=True). It checks
   both the actual NPU override and its GPU superclass source/signature,
   calls owner.before_update BEFORE the native early FA zero writer, and
   retains its native return. Missing/invalid cold/paused/byte evidence
   retires this owner and does not call the native writer.
5. AFTER actual native metadata production, prepare source-bound CPU
   NativeReceipt objects via owner.native_receipt(kind,layer,md,values,
   original_unbound_producer). GDN producer is pinned
   AscendGDNAttentionMetadataBuilder.build; FA producer is pinned
   NPUModelRunner._build_attention_metadata. This package does not invent that
   observer or read metadata device tensors. Until a reviewed live observer
   provides ALL48 GDN and ALL16 FA values, before_model raises Pending.
   Diagnostic D2H, if separately permitted by MAIN, must be labelled and
   excluded from formal performance. Merely binding original functions is
   not proof that an observer ran.
6. owner.before_model(runner,turns,native_cpu_receipts,owner.ticket) returns
   AdmittedTurn only after paused/all-active GDN leases and FA reads/writes
   compare by absolute byte intervals and actual post-reorder CPU block
   tables. Physical block IDs are expanded by actual source-bound ratios.
   FA receipt values: request_ids, query_start_loc, seq_lens, slot_mapping.
   GDN values are the complete frozen continuous verify_native schema.
   Metadata object IDs and producer paths/hashes bind each receipt.
7. Core safety API: admitted.require_layer(prefix,md)->Turn;
   admitted.before_writer(prefix,turn,md); admitted.writer_started(prefix);
   admitted.layer_succeeded(prefix). Whole-model success calls
   admitted.commit() after exactly48 layer successes. Exceptions call
   admitted.retire(prefix,reason,retry_allowed=False); no native fallback or
   state retry after partial writes. Empty finished-only updates can release
   leases after the original native update succeeds.

## Scope and pending gates

Text-only, eager, prefix off, mamba cache none, TP4/CP1, maximum16 actual rows,
no async/speculative/cache-transfer/preemption-relocation/streaming/recompute.
Unscheduled pause is supported in the CPU lease/allocated-FA superset check;
it is not a proven native lifecycle. Zero spans are guarded at update entry.
The subsequent model-metadata admission occurs AFTER that native early zero
stage, but BEFORE conv/state/FA core writers; failure there is not a claim
that no earlier native zero was executed.

The CPU checks conservatively protect ALL allocated FA blocks of retained
requests, including unused allocation. This may reject a safe native layout;
it must not be silently weakened merely to admit serving. A cold pointer
alone, identical slot IDs, frozen source, or these software fixtures are not
shared-FA/GDN NPU lifecycle proof. Actual source-bound CPU producer observers,
48-instance writer integration, paused/resumed mixed lifecycle, slots/reset,
all-batch/mixed NPU parity, pointer/guard budget checks, and matched E2E/quality
remain independent required gates. Normal graph paths are not admitted.

Software-only command (MAIN may run without loading Torch):
PYTHONDONTWRITEBYTECODE=1 python3 -B projects/damp-ascend/integration/cache_identity_v1/test_contract.py
