# DASC on Ascend: Terminal Piercing Report

## Decision

**No-go for the current implementation and acceptance target.**

The result does not reject the DASC paper in general. It rejects the current
Qwen3.6-27B, TP4, vLLM-Ascend v0.23 plugin candidate because the first required
service-level correctness gate failed. Performance, LongBench-v2, and GSM8K
were therefore not run or claimed.

## Target contract

- Model: Qwen3.6-27B.
- Hardware: physical Ascend NPU4-7, TP4.
- Delivery boundary: removable plugin/monkeypatch; upstream framework and image
  remain unchanged.
- Correctness order: mechanism activation -> state/cache integrity ->
  deterministic cache-hit replay -> end-to-end performance -> task quality.
- Performance target: at least 10% throughput improvement under the fixed
  1024-output-token protocol, with TTFT and TPOT reported separately.
- Final quality target: LongBench-v2 and GSM8K must not regress; the user's
  stated 1% tolerance concerns end-to-end GSM8K, not intermediate state
  correctness.

## What was implemented and proven

The latest bounded candidate
`padded-attention-reshape-coherent-nontarget-npu4-7-v12r40` was not a CPU
mock or branch-only test:

- the live cache-hit counter increased by 4608 tokens;
- all four TP workers executed the recurrent-state lifecycle;
- the state-index mapping covered all 48 GDN layers and both state indices;
- 384 exact physical state copies were paired with first-resumed-token
  before/after boundaries;
- destination rows changed and source rows remained unchanged;
- dense-page padding and padded-attention reshape structural checks passed;
- the tested non-target-device isolation and preflight checks passed.

These results establish mechanism activation and structural plumbing. They do
not establish numerical correctness.

## Failing gate

With fixed decoding settings (temperature 0, seed 0, thinking disabled) and an
identical cache-hit request repeated three times, the candidate produced three
different length-terminated strings:

1. “To process the user's request, I will first address the request to provide the”
2. “The user wants to generate a output for the "next" model in the chain”
3. “To process the user's request, I will first address the request to output the”

The artifact records:

- `prefix_cache_hit_observed=true`
- `prefix_cache_hit_delta=4608`
- `identical_replays=false`
- top-level `ok=false`

The dense eager exact-prefix control used the same class of cache-hit replay and
returned `VERIFIED` three times:

- `prefix_cache_hit_observed=true`
- `prefix_cache_hit_delta=3072`
- `identical_replays=true`
- `ok=true`

Therefore the failure is not explained by eager execution alone. The strongest
supported conclusion is that the candidate's recurrent-state/cache lifecycle
does not preserve deterministic model semantics after reuse.

## Why no performance or GSM8K result follows

A task-level tolerance cannot repair an unstable execution relation. If an
identical request has no deterministic candidate output, throughput and GSM8K
would measure a mixture of invalid state histories rather than one defined
algorithm. Running them would create misleading numbers, so the experiment
stopped at the numerical gate.

## Reusable engineering lessons

1. A cache-hit counter proves reuse occurred, not that restored state is
   correct.
2. Structural row-copy, padding, and layer-coverage checks are necessary but
   cannot replace a service-level replay oracle.
3. Always run the dense control in the same eager/graph mode before blaming the
   runtime's general determinism.
4. Separate end-task accuracy tolerance from intermediate semantic integrity.
5. Once a deterministic failure is localized and repeated, do not rerun the
   same candidate. Re-entry requires a materially new state reconstruction
   invariant and a new first-token proof.

## Re-entry condition

DASC should be reconsidered only if a new implementation can prove, before any
performance run:

- exact ownership and reconstruction of every recurrent state component at the
  cache boundary;
- deterministic first-token and multi-token replay on all four TP workers;
- identical repeated cache-hit outputs under fixed decoding settings;
- the same result in the intended graph mode, with a matching dense control.

Without that new evidence, the queue advances to the next paper.

## Evidence identity

The source artifacts remain outside Git under
`/cache/cch/dasc-qwen36-ascend-20260915`; only their paths, hashes, and
bounded verdict are recorded in
`projects/dasc-ascend/evidence/terminal-audit.json`.
