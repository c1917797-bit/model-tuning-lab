# DRRQR on Ascend: durable success and failure experience

Date: 2026-09-12

## Purpose and claim boundary

This document condenses the historical Qwen3.8-27B DRRQR work into reusable
engineering evidence. It does not replace the raw reports, practice-iteration
records, or current handoff. The accepted product target remains a reproducible
10 percent or greater end-to-end output-throughput improvement against the
frozen dense contract with no final LongBench-v2 or GSM8K decline.

The current best comparable candidate remains energy-Dk64 at 141.564496 output
tok/s, 4.752041 percent above the frozen dense 135.142469917 tok/s. It is a
promising development baseline, not an accepted result. Its selector is an
experimental joint normalized Q/K energy top-k rule, not the paper-exact
StrongRRQR implementation.

## Eight durable conclusions

1. The frozen dense contract is reusable until a material model, runtime,
   common-optimization, topology, device, or workload change occurs.
2. Execution-path proof is mandatory. The service uses the Ascend gating,
   independent L2-normalization, and native recurrent path; conclusions drawn
   from an unused Triton implementation were superseded.
3. Stateful numerical gates need complete multi-step state evidence. No
   NaN/Inf and short token agreement are not correctness proofs.
4. Logical rank must be separated from physical padding. Dk104 and Dk88 were
   invalid on the frozen native decode CopyOut path; Dk128 and Dk64 were valid.
5. Better Q/K energy, normalized-QK error, or state error does not guarantee
   better recurrent output or task quality. The selector objective must cover
   the behavior that matters downstream.
6. Microbenchmark gains do not predict service gains. A packed QKV/L2
   composition improved its isolated graph screen but regressed the endpoint
   against the prior energy-Dk64 service.
7. Operator work is admitted only when it enables a concrete DRRQR candidate.
   Fusion is staged by semantic boundary and must pass NPU numerical/state
   gates before endpoint performance and final accuracy.
8. Fusion cost must be counted at the actual native-loop multiplicity. In the
   current TP worker, one Q/K head serves three value heads; moving Q/K
   normalization into a per-value-head loop without reuse would compute it
   three times and can lose even when it removes global launches.

## Outcome classes and recovery rules

- **Accepted foundation** admits only the next evidence layer. Numerical or ABI
  success is not endpoint or accuracy success.
- **Rejected** stops the tested configuration or nearby family named by its
  evidence; it does not reject all DRRQR.
- **Invalid** contributes no algorithm trend. Repair path identity,
  comparability, alignment, or measurement before interpreting it.
- **Failed tooling/environment** preserves the operation and exact error, then
  permits a bounded retry only after the external defect is proven corrected.
- **Inconclusive** permits one disambiguation only when its result can change a
  candidate decision; otherwise return to the DRRQR mainline.

## Evidence ledger

| Outcome | Tested result | Durable lesson | Claim ceiling |
|---|---|---|---|
| accepted foundation | A frozen same-stack dense development baseline and fixed protocol were recorded. | Reuse it; rebaseline only on a listed material change. | Development comparison only, not final three-run acceptance. |
| invalid | Dk104/Dk88 crossed 16-aligned local-state padding incorrectly while Dk128/Dk64 did not. | Keep the non-aligned-width guard; do not infer a pruning-rate trend from invalid runtime output. | Frozen native decode shape path. |
| accepted foundation | Prefill Dk128/104/88/64 and decode Dk128/64 passed their declared golden gates. | Validate prefill and decode independently for every new logical rank. | Operator numerical correctness for tested shapes. |
| accepted screen | Energy-Dk64 produced the best comparable endpoint screen at +4.752041 percent. | Preserve it as the current candidate/control while searching for the remaining DRRQR-specific gain. | One paired endpoint screen; no quality or portability acceptance. |
| rejected | Layerwise Dk48/Dk64/Dk80 allocation had no feasible equal-budget improvement over all-Dk64. | Do not resume simple equal-cost heterogeneous layer widths. | Tested energy-selector allocation only. |
| rejected | Cosine StrongRRQR, causal-kernel, exchange, recurrence-weighted exchange, sparse projection, dense-prefill transition, and tail-sketch variants missed held-out fidelity/foldability gates. | Stop nearby coordinate-only tuning; require a materially different recurrence-aware and foldable design. | Tested selector/compensation families, not all DRRQR. |
| accepted foundation | Rich teacher capture passed request/token, tensor, state-transition, source, and loaded-library audits. | Reuse its locked fit/held-out split for cheap candidate admission. | Selector input corpus only. |
| rejected/inconclusive | Dk80 passed short numerical gates but failed a concurrent mixed service cohort; later probes localized a first non-finite boundary outside the recurrent cache path. | Bind anomalies at the real phase/cache/operator seam before adapting a kernel; do not let a generic framework anomaly replace the DRRQR objective. | Tested concurrent configuration only. |
| rejected | A Dk64 reduction specialization passed parity but regressed NPUGraph replay. | Eager wins are insufficient for graph-served inference. | Tested kernel variant only. |
| rejected | Packed QKV/L2 passed exact parity and improved isolated graph timing, then reached 140.583188 tok/s, below energy-Dk64. | Reject at the endpoint gate; move to a larger measured seam rather than stack small launches. | Tested two-kernel composition only. |
| accepted foundation | Native packed normalized-QKV Stage 1 passed batch1/16, eight-step, eager/full-FP32-state/NPUGraph exact parity on physical NPU4. | Packed addressing and derived shape contracts are safe enough to admit raw normalization work. | ABI/storage correctness on the qualified 910B environment only. |
| accepted source audit | The active decode path normalizes each Q/K head with FP32 square/sum/rsqrt, epsilon 1e-6 and a BF16 materialization boundary; the native recurrence maps three value heads to each Q/K head. | Preserve the exact arithmetic boundary and reuse each normalized shared Q/K head instead of blindly recomputing it per value head. | Source and cost-model guidance only; no new NPU or endpoint result. |
| failed tooling | Two native builds were terminated by an unintended 30-second remote default; one later attempt found the dedicated container stopped. | Use an explicit asynchronous job timeout, poll the same operation, and inspect container/device state before any bounded retry. | Tool and environment handling only. |

## Current directional decision

Continue the energy-Dk64 mainline with the uniquely named native operator
stages. Stage 1 is complete at its strict claim ceiling. The Stage 2 source and
multiplicity audit is complete, but implementation and NPU validation have not
started. The next bounded step is raw packed Q/K normalization with FP32
square/sum/rsqrt, epsilon 1e-6, the required BF16 materialization boundary, and
reuse across value heads that share one Q/K head. Its numerical criterion must
be declared before execution. Gating is admitted only after that stage passes
its numerical and NPUGraph gates. A fixed-output endpoint screen follows only
if the graph path is materially promising; final LongBench-v2 and GSM8K remain
last.

Do not resume MTP, speculative decoding, quantization, retraining, nearby
Q/K-only selector search, simple heterogeneous widths, the K64 reduction
specialization, or the rejected Triton materializer as substitutes for this
mainline.

## Traceability

The authoritative decision records are
`.agents/evals/practice-iterations/drrqr-*.yaml`; the live resume state is
`.agents/HANDOFF.md`. Large reports remain outside Git and are bound by the
paths and SHA256 values in those records.
