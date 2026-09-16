# v12r18 scheduler-awareness audit

Status date: 2026-09-16

## Decision

Do not run the original property-only v12r18 bytes on NPU. The proposed root
cause remains valid, but the first fix was incomplete because it covered
worker cache configs and not the scheduler config after upstream reduction.

The corrected one-variable successor keeps the attention manager selected by
upstream while carrying an explicit Mamba-lifecycle marker into the reduced
scheduler config. It remains an all-head identity diagnostic; it does not add
pruning, performance tuning, or a second algorithm.

## Authoritative source chain

The audit used the official vLLM `v0.23.0` tag at commit
`0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665`.

1. `vllm/v1/kv_cache_interface.py` defines `KVCacheConfig.has_mamba_layers`
   by checking only whether each group's outer spec is `MambaSpec`.
2. DASC represents aligned attention plus heterogeneous Mamba layers as one
   outer `UniformTypeKVCacheSpecs`, so the unmodified property returns false.
3. `vllm/v1/engine/core.py` calls
   `generate_scheduler_kv_cache_config(kv_cache_configs)` before constructing
   the scheduler.
4. `vllm/v1/core/kv_cache_utils.py` deep-copies one worker config and replaces
   every `UniformTypeKVCacheSpecs` outer spec with its first inner spec.
5. DASC deliberately keeps attention first. This correctly selects the
   full-attention block manager, but it also removes the inner Mamba specs
   before `Scheduler.__init__` reads `has_mamba_layers` and
   `needs_kv_cache_zeroing`.
6. `Scheduler.__init__` enables aligned prefill splitting only when
   `has_mamba_layers` is true. Without it, a 1,938-token prefill can cross the
   1,536-token cache boundary without materializing the recurrent state at
   that boundary, making later prefix reuse restore an invalid state.

This explains why both the bridge and bridge-bypassed all-head controls could
start successfully yet diverge only after prefix-cache hits.

## Consumer coverage

A complete `vllm/v1` search at the pinned tag found no other consumers of
`has_mamba_layers` or `needs_kv_cache_zeroing`:

- the worker reads `needs_kv_cache_zeroing` after physical cache allocation to
  initialize block-zero metadata;
- the scheduler snapshots both properties during construction;
- `need_mamba_block_aligned_split` gates the waiting-request and
  running-request prefill scheduling paths;
- `needs_kv_cache_zeroing` gates collection of newly allocated block IDs for
  zeroing in each scheduler output.

Cache-manager selection is independently driven by the reduced outer spec.
Keeping attention first therefore remains necessary to retain
`FullAttentionManager`; changing the first spec to Mamba would select
`MambaManager` and lose full-attention allocation semantics. The corrected
patch changes only lifecycle flags and deliberately leaves manager selection
unchanged.

## Corrected seam

The plugin patch now covers both representations:

- worker config: detect inner `MambaSpec` members inside the aggregate so
  physical cache zeroing remains enabled;
- scheduler config: wrap the actual alias imported by `vllm.v1.engine.core`,
  detect Mamba before upstream reduction, call the original reducer, keep the
  resulting attention spec, and attach an explicit Mamba-lifecycle marker;
- import timing: patch the defining `kv_cache_utils` function first; if
  EngineCore is already loaded, patch its existing alias after proving both
  references are identical, otherwise let its later import pick up the
  patched definition without forcing a circular import;
- `KVCacheConfig.has_mamba_layers`: honor the explicit marker, native direct
  Mamba groups, or inner aggregate Mamba members;
- fail closed if the EngineCore and `kv_cache_utils` function aliases differ,
  or if upstream reduction no longer yields attention managers;
- emit `heterogeneous_scheduler_mamba_awareness_preserved` only after the
  real reducer runs and both Mamba flags are true.

The regression test reproduces upstream's deep-copy/first-inner reduction. It
requires the reduced spec to remain `FullAttentionSpec`, both lifecycle flags
to be true for the mixed aggregate, and both flags to remain false for a pure
attention config. Separate tests require a detached already-loaded EngineCore
alias to fail closed and an unloaded EngineCore to use the deferred path.

## Required gates before NPU

1. Reconcile these bytes with the unpublished chicaihong01 v12r18 commit; do
   not run the earlier property-only snapshot.
2. Run the focused plugin test and the complete pinned-image suite.
3. Record the live imported EngineCore, `kv_cache_utils`, and
   `kv_cache_interface` paths and hashes.
4. Require the scheduler-preservation evidence event before accepting service
   readiness.
5. Run one immutable all-head control only. Require exact first resumed token,
   identical repeated continuation, positive prefix-hit delta, and cleanup of
   the owned container.

A pass permits reintroducing the all-head bridge and then W64 pruning. A fail
closes this scheduler-awareness implementation and moves localization to the
actual checkpoint materialization boundary; it does not justify changing the
selector or starting performance/quality experiments.
