# DASC Qwen3.6-27B Ascend Piercing Report

Date: 2026-09-18  
Decision: **failed for the current plugin implementation; paper mechanism
inconclusive on this checkpoint/runtime**

## Executive verdict

The workstream implemented a paper-derived DASC-NR adaptation as a
plugin-owned monkeypatch for Qwen3.6-27B on Ascend vLLM-Ascend v0.23.0. It
reached a real TP4 service on physical NPU4-7 and proved the intended cache
allocation, split-attention reshape, state copy, native recurrent consumption,
and prefix-cache lifecycle paths. The final strict numerical canary still
failed: identical deterministic cache-hit requests produced different
continuations.

This rejects the current implementation before performance or GSM8K admission.
There is no valid throughput, TTFT, TPOT, or E2E accuracy result for DASC from
this workstream. It would be misleading to benchmark a numerically unstable
candidate.

The failure is narrower than a rejection of the paper. No author implementation
was available for direct parity, so the delivered code is explicitly labeled a
paper-derived DASC-NR Ascend adaptation. The remaining fault domain is
state production, attention KV semantics, aggregate lifecycle ordering, or
another producer/consumer boundary not distinguished by row-copy evidence.

## Target and delivery boundary

- Paper: *DASC: Decay-Aware State Compression for Hybrid Linear-Attention
  Serving*, arXiv:2608.30386v1.
- Model: `/cache/efim/Qwen3.6-27B`.
- Runtime: pinned image
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
  (`quay.io/ascend/vllm-ascend:v0.23.0`).
- Hardware: physical NPU4-7, TP4.
- Delivery: repository-owned plugin/monkeypatch only; upstream vLLM,
  vLLM-Ascend, CANN, model weights, and the original image were not modified.
- Correctness policy: performance and E2E quality are forbidden until exact
  deterministic cache-hit replay passes.

## Mechanism implemented

The adaptation builds a real-weight head-retention plan, stores a compact
persistent checkpoint representation, and materializes retained state into
request-owned dense active slots at cache-load/resume boundaries. It also
normalizes Ascend kernel block identifiers to manager rows, preserves omitted
head evolution across ordinary decode steps, and handles mixed attention/GDN
cache aggregation through plugin-controlled allocation and lifecycle hooks.

The current TP-contiguous selector retains 1728 raw heads but stores 2084 after
TP MAX-padding, removing 220 heads. A group-balanced combinatorial bound stores
1828 and removes 476. These are storage bounds only, not throughput claims.

## Important corrections discovered during piercing

1. Restoring compact state before every forward is semantically wrong. DASC
   Load semantics apply at a true new/resumed cache boundary; repeated restore
   erases omitted-head updates accumulated after the first token.
2. Ascend GDN metadata may use kernel block identifiers while the cache manager
   copies manager rows. The live block ratio must be resolved from available
   runtime geometry and applied before native recurrent execution.
3. Keeping all heads is not a dense physical identity control when aggregate
   page padding, grouping, offsets, or allocation sizes differ.
4. In split K/V attention storage, dense hybrid page slack can sit at the end
   of each one-dimensional split allocation. A stock reshape then interprets
   the slack as payload. The final plugin adapter trims only the verified
   logical prefix for reshape while preserving the allocation pointer and
   reservation; unknown, quantized, or non-contiguous layouts fail closed.
5. Complete state-row transport is consumer-side evidence, not proof that the
   state producer and attention/cache lifecycle are semantically correct.

## Control chain

The decisive dense eager control, v12r29, passed three exact stopped
`VERIFIED` responses, identical replay, and a prefix-cache-hit delta of 3072.
This excludes eager execution itself as the source of instability.

v12r30 then covered all 384 canonical state-copy and before/after-native keys
across four TP workers, 48 GDN layers, and two state families, while strict
replay still failed. That excluded missing middle-layer state transport.

v12r37 exposed a separate pre-readiness split-attention reshape defect caused
by dense-page slack. v12r38 proved the compatibility adapter with 64 prepared
and 64 adapted layer-worker events. v12r39 showed that a coherent foreign
non-target TP service transition must not be mistaken for target-lane
invasion. Neither attempt produced numerical evidence.

## Final physical experiment: v12r40

Artifact root:
`/cache/cch/dasc-qwen36-ascend-20260915/padded-attention-reshape-coherent-nontarget-npu4-7-v12r40`

Operation: `exec-0000000000001e49`

The controller pinned the exact tolerated foreign container identity and
allowed only coherent idle or full-TP4 states on physical NPU0-3. It rejected
partial non-target TP states and every foreign PID on target NPU4-7. The owned
service passed preflight, model load, HCCL, readiness, post-readiness ownership,
and request execution.

Passed mechanism gates:

- 4 worker-dispatch and 4 TP-geometry events;
- 64/64 padded-attention prepared/adapted events;
- 192/192 dense-page physical-cache bindings;
- 384/384 exact state copy/before-native/after-native keys;
- source rows remained unchanged and native destination rows updated;
- required lifecycle branches were reached;
- prefix-cache-hit delta was 4608.

Failed numerical gate:

- short exact output: `"OK\n\n"` rather than `"OK"`;
- three identical-prefix requests at temperature 0, seed 0, and thinking
  disabled produced three different continuations;
- `identical_replays=false`;
- `replay_exact_verified=false`;
- overall physical canary `ok=false`.

## Evidence identity

| Artifact | SHA256 |
| --- | --- |
| `physical-canary.json` | `56f41fbfa41a823e8d05f7f8942e33be3f57a18fcdb643df840ebd343f371433` |
| `state-index-verdict.json` | `fa2c003e3280caef08b7ffe597dbfdbd6351fa9409d8f94f3cc1a6c862589377` |
| `full-layer-state-verdict.json` | `5e8aa50a90fd087033ecf95eb2537d30f97e678241dfdbdcd9a963f77dc128e6` |
| `dense-page-padding-verdict.json` | `3472758fa56442875847a9afe9d8f3cf78a21c5d7baecfc23598c0783e8bb1f7` |
| `padded-attention-reshape-verdict.json` | `d5acfdcd09762b3b8c2aeef9414c53e1126eacbbe575eb54e11b2c1a0f977047` |
| `evidence.jsonl` | `8b17d01977b2f7e5dadde3d5e4a59ea88c8667c1468d889e9110c6e1aa0a0922` |
| `service.log` | `e32ddff30e79d75e05b91a1f085b82236f5a0e7c05eec50ddb9b621baa41a48c` |
| `artifacts.sha256.json` | `dae4f89f64aae9724f2a45b0b16cbeb7b1bfb21a1bc62d9f2ae21ee995b9dcb5` |

## Performance and quality

No DASC performance run was admitted. Therefore this workstream has no valid
DASC throughput, TTFT, or TPOT gain to report.

No GSM8K or other E2E quality run was admitted. Therefore it has no valid DASC
accuracy delta to report. This is intentional gate enforcement, not missing
positive evidence.

## Software and governance validation

- The complete pinned-image, no-device plugin/workstream suite passed 251/251
  at the v12r38 implementation checkpoint.
- The final v12r38-v12r40 controller regression set passed 10/10 after the
  report and handoff update.
- `task.json` parses as JSON.
- `./scripts/validate-mst.sh` passes all 26 maintainer skills.
- `git diff --check` passes.
- Ruff is not installed in the pinned image, so no Ruff result is claimed.

## Decision and recovery

The current plugin-owned implementation is rejected as
`failed_current_plugin_implementation_paper_inconclusive`. Keep it opt-in and
disabled by default. Preserve all negative evidence and do not reuse immutable
result roots or completed idempotency keys.

The two evidence-driven corrective NPU iterations allowed by the 24-hour
timebox have been consumed. Do not spend another loop on unchanged bytes or
more state-row tracing. A revisit is justified only by a materially new
hypothesis that directly observes producer output, attention KV state, or
aggregate lifecycle ordering at a token/logit boundary, or by release of an
author implementation that changes the parity basis. Otherwise, move the
piercing budget to the next algorithm.
