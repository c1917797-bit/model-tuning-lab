# Qwen3.6 paper portfolio synthesis

## Status

- Stage: evidence complete; pending commit/push at the time of this file edit.
- Base: the pushed DUET terminal checkpoint 63a25ca.
- Scope: aggregate the completed 10-paper queue and select the next measured
  Ascend hotspot; this is not an eleventh paper result.
- Hardware lane: physical NPU4-7 only.

## Invariants

1. HYPIC is a prior successful reference, not a new result from this workstream.
2. Local kernel speedups and NPU kernel-time shares are opportunity evidence,
   not end-to-end performance.
3. Mutually exclusive implementations of the same mechanism are not additive.
4. DASC and Sparse Prefix remain closed until a materially new deterministic
   replay hypothesis exists.
5. A new optimization candidate must remain an explicit, disabled-by-default,
   fail-closed vLLM-Ascend plugin/monkeypatch.

## Completed evidence

1. Materialized a machine-readable cross-paper matrix and overlap-aware Amdahl
   audit.
2. Captured one fresh Qwen3.6 dense TP4 profile on physical NPU4-7 with prefill
   and decode separated, four ranks, and exactly 30 decode iterations.
3. Exported all eight trace trees offline in a no-device container and bound
   them to the service/client hashes.
4. Identified a 14.15340% shape-filtered GDN decode fusion seam. A 10% decode
   phase gain requires at least 2.79680x local speedup under the diagnostic
   Amdahl model.
5. Confirmed the current v0.23 source seam calls causal-conv, fused gating,
   separate Q/K normalization, and the custom recurrent operator in one GDN
   Python call chain.

## Decision

Proceed to a new bounded self-evolution loop for an exact-semantics GDN decode
mega-op. It must be an explicit opt-in plugin monkeypatch and must first pass a
cannbot/ops-transformer feasibility review. This synthesis stage did not
generate an operator and did not use cannbot to generate one.

Artifacts:

- profile summary v2 SHA256:
  `7d7554583eb202c26d51e946e8e3fd741e1a8578b1bba882f1af02104da06d81`
- export receipt SHA256:
  `87f13d128d8479b765bf97967e714718597411f835174ee4a91bdbab67a47103`

## Acceptance

The evidence requirements are complete. Commit/push and the maintainer-skill
validation remain the closeout operations. This stage does not satisfy the
final performance or quality acceptance contract.
