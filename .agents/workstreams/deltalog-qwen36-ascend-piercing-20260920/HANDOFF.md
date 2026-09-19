# DeltaLog Qwen3.6 Ascend Piercing

## Terminal decision — no-go for the frozen concurrency-16 objective

Closed at `2026-09-19T22:17:43Z`. The method has a valid exact-semantic
mechanism, but the target service opportunity is too small. Applying the
paper's best `1.86x` local speedup to the measured recurrent share gives only
`1.02135x-1.02289x`; an optimistic 50% reduction gives
`1.02312x-1.02480x`; even perfect deletion of the complete recurrent operator
gives only `1.04734x-1.05087x`. The affected share required for `1.10x` is
`19.6617%`, versus `4.520%-4.840%` observed.

Artifact:
`/cache/cch/deltalog-qwen36-ascend-20260920/opportunity-gate-v1/opportunity-audit.json`,
SHA256 `ef297a2b19b21705be48f2771e64708174884c97d361b8d2b8e874f259bbfefc`.
Four focused tests passed. This is a diagnostic opportunity bound, not an E2E
performance or quality result. No operator or service A/B was run, and NPU4-7
were not consumed because the upper bound failed first.

## Scientific question

Can exact deferred materialization of Gated DeltaNet recurrent states improve
Qwen3.6-27B end-to-end output throughput by at least 10% under the frozen
`32768 input / 16384 shared / 1024 output / 40 requests / concurrency 16`
contract, as an opt-in vLLM-Ascend plugin on physical NPU4-7?

Activated `2026-09-19T22:11:56Z`; hard deadline
`2026-09-20T22:11:56Z`.

## Method identity and transfer risk

DeltaLog keeps a dense recurrent-state base and a bounded compact update log.
Most decode steps append to the log; periodic merges materialize the dense
state. The method is intended to preserve exact model semantics. The paper
reports up to `1.86x` affected-kernel speedup and `1.08x-1.20x` E2E TPOT on
Qwen3.6-35B-A3B, but its favorable state-materialization shares are reported
at batch 64 (`25.2%`) and batch 256 (`44.6%`). These values cannot be imported
into the current concurrency-16 acceptance point.

No paper-linked public implementation was identified in the activation
search. A future target implementation may be called `faithful-port` only
when it preserves the paper equations, bounded-log lifecycle, merge policy,
and exact outputs; it must not be called `paper-exact`.

## Target evidence

The immutable four-rank, 30-decode-step Ascend trace at concurrency 16 is:

`/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/prefill-mc2-mixed-v1/profile-current-v1/baseline/profile-summary.v1.json`

SHA256:
`b3bddd3b1a8b96571f20c59d801aa21da3da673f875f86a3b04318afbdb480a8`.
The recurrent GDN operator occupies only `4.520%-4.840%` of NPU interval.
The first gate therefore applies the paper's best `1.86x` local speedup and
also an intentionally optimistic 50% local reduction bound. Kernel
attribution is diagnostic, not an E2E measurement.

## Resource policy

Physical NPU4-7 have first priority for this portfolio. Before every NPU run,
freshly inspect NPU processes, HBM, device mappings, containers, and UDA
ownership. Stop only an exact new external workload that actually uses
physical4-7. A device declaration without a real process and non-idle HBM is
not a blocker. Never touch physical NPU0-3.
