# R12 bounded integrated first-divergence probe — 2026-10-15

## Why this next action
R9, R10, R11 all fail final SSM shadows on a nonzero continuation at layer0/step9.
R11 preserves native4key/12value geometry, yet failed ranks0/1/2; output and
conv pass, state does not. Source121/177clean/exact release audit0770 passes.
The cause is NOT established. Do not infer it from residual magnitudes across
different schedules, and do not run another blind implementation variant.

## Frozen unchanged treatment and bounds
Keep R11 C1/C2/sharedWY/actual-prefix2passes/material/conv/private commit,
official image/model/TP4, and .01/.003 shadow thresholds unchanged.
Independent diagnostics only, disabled by default, exact source/config binding.
Only rank0 and layer language_model.model.layers.0.linear_attn; capture the
first failed same-input serialized shadow group, maximum two requests and
four live windows. Stage coordinates include exact request/rank/PID/step,
source and packed offsets, has_initial_state, state slot, public generation,
window kind/length and chunk-vs-recurrent reference selection.
No C3, no standalone GDN campaign, no quality/performance claim.

## Capture contract to implement and host-test before admission
1. A per-call private capture context, absent/no side effects when disabled.
   Observe actual inputs/outputs at the packed and serialized boundaries;
   no recomputed stand-in mislabeled as actual tensor evidence.
2. Preserve independently cloned CPU samples for one declared key/query head
   and its associated value head (head0), all128 coordinates and selected
   live-window token rows; retain raw full coordinates for the sampled head.
   Q/K after normalization, original V, log gates/beta, incoming H, actual
   prefix-terminal, cached T/S, suffix seed, actual final H/conv and matching
   serialized boundaries. Exact window lengths must determine bounded bytes.
3. Retain only on the first numerical failure; discard passed-call samples.
   Exclusive new raw directory, <=64MiB total tensors and <=32 records.
   Fail closed before writes if bounds, identity or paired coordinates fail.
   Never serialize an accelerator tensor without an explicit CPU clone.
   Seal files, manifest, sizes/SHA256; no pickle-based independent audit.
4. Independent audit first compares same-coordinate normalized Q/K/V/gates
   and incoming states, then prefix terminal, cached composition, suffix seed,
   suffix final. Report first observed divergence and frozen scaled residuals.
   Head sampling is not full tensor equivalence. CPU FP64 recurrence for
   captured inputs is an independent numeric reference, not proof of native
   BF16 kernel equivalence or PIC/full-context equivalence.
5. Add negative tests for mislabeled stage/step/request/generation, missing
   records, mutation, over-limit data and disabled zero-capture behavior.
   Test capture rollback/exception ordering with no actual native cache writes.

## Device and progression gate
Only after implementation + host tests + independent audit + new package and
contract + published checkpoint + fresh direct route/physical0-3/8233/HCCL/newroot
admission: one integrated16/c16/32768/fixed64 diagnostic with original2B2A warmups.
Observe same exact controller/root until terminal. No unchanged R11 retry.
If sampler bounds cannot cover actual first failed group, retain explicit
incomplete evidence; do not silently increase bounds or call it a diagnosis.
Full enabled/disabled/performance/quality/lifecycle goals remain unachieved.
Fixed deadline2026-10-15T19:04:09Z; no new starts after it.
