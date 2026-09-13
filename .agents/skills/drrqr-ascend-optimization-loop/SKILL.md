---
name: drrqr-ascend-optimization-loop
description: Use when selecting, implementing, or reviewing a DRRQR state-reduction candidate in projects/drror_vllm_ascend. Keep algorithm and Ascend operator work tied to the fixed joint endpoint and stop repeated dead-end variants.
---

# DRRQR Ascend Optimization Loop

## Purpose

Preserve the reusable learning from the Qwen3.8-27B DRRQR program so a fresh
maintainer continues the performance-and-accuracy objective instead of
repeating invalid experiments or turning an operator probe into the goal.

Use this skill with `mst-practice-iteration-planning`,
`ascend-inference-tuning-loop`, `ascend-benchmark-evidence`, and the nearest
project `AGENTS.md`. Current measurements and resume state belong in the
practice-iteration YAML and `.agents/HANDOFF.md`, not in this skill.

## Fixed decision target

The product claim is joint: the same admitted DRRQR candidate must meet the
project's frozen end-to-end throughput target, TTFT/TPOT protocol, and final
LongBench-v2/GSM8K quality gates. A selector, cache layout, native operator,
microbenchmark, report, commit, or push is only an enabling checkpoint.

Keep paper-exact StrongRRQR separate from experimental energy or
recurrence-aware selectors. Never relabel a successful variant as exact paper
reproduction.

## Reusable success patterns

1. Freeze a reusable dense contract and rebaseline only after a declared
   material change. Candidate-only code proven inactive in dense mode does not
   force a new baseline.
2. Prove the loaded Ascend path before optimizing it. Source text from another
   backend, an unused kernel, or a similarly named op is not execution evidence.
3. For recurrent state changes, compare output and the complete mutable state
   across changing steps, untouched slots, guards, storage identity, eager and
   NPUGraph. Finite-only checks are insufficient.
4. Separate logical Dk and coordinate order from physical alignment, padding,
   tiling and SoC dispatch. Derive shapes from tensors, validate grouping, use
   unique opt-in operators, and keep a correctness fallback.
5. Captured teacher trajectories with a locked fit/held-out split are useful
   admission screens. They reduce NPU cost but cannot prove endpoint speed or
   task accuracy.
6. Stage native fusion one semantic boundary at a time. A packed-addressing
   stage may require bitwise parity; normalization and gating require
   predeclared arithmetic criteria before execution. Count work at the actual
   head and sequence multiplicity: shared Q/K heads can make a naive
   per-value-head fusion recompute normalization and lose despite fewer launches.
7. Before opening an implementation iteration, run two source-only admission
   checks. First prove the proposed saving is not already active in the plugin
   or loaded model path. Then translate the measured seam into a deliberately
   optimistic endpoint ceiling. If perfect removal cannot close a material
   part of the current joint gap, stop before code, build, NPU, or service work.
8. For a structural rank or channel change, build a full-path foldability map
   before implementation: checkpoint rows and columns, post-convolution
   nonlinearities, recurrent state, normalization and gating, output
   projection, cache allocation, scheduler identity, and graph keys. The
   reduced dimension must remain reduced through the hot path. Charge any
   dense reconstruction, gather, conversion, or hidden expansion against the
   endpoint-headroom case.

## Reusable failure and stop rules

- Non-aligned native state widths that cross padded rows are runtime-invalid
  until their CopyOut/storage path is fixed. Do not interpret their output as a
  pruning trend or weaken the alignment guard.
- Stop nearby Q/K-only coordinate-selector tuning after held-out evidence shows
  that energy retention, normalized-QK error, and recurrent output fidelity do
  not move together. A materially different recurrence-aware design needs a
  new cost and foldability argument.
- Do not optimize a state proxy alone. Better state relative error can coexist
  with worse post-recurrence output.
- Reject a candidate that wins an isolated eager or graph microbenchmark but
  loses the fixed endpoint screen. Profile only if one bounded diagnostic can
  change the implementation decision.
- Do not build a replacement native operator for an unbound anomaly. First
  locate the earliest non-finite or divergent tensor in the actual concurrent
  prefill/decode and cache path.
- A generic launch-saving or framework optimization is not DRRQR progress
  unless it enables a named DRRQR candidate; if general, apply it equally to
  the dense control.
- Do not retry a failed build or remote command merely because the client wait
  ended. Preserve the operation identity and prove terminal state first.
- Treat generated CANN runtime identity as a vendor bundle, not one op_api
  library. Load and hash the matching opmaster and opsproto from the same
  packaged vendor root before interpreting an operator result.
- If an arithmetic stage diverges at the first step while guards, pointers,
  untouched slots and metadata remain valid, classify it as a numerical
  failure. Stop performance and accuracy work; do not relabel the storage
  checks as partial arithmetic acceptance or relax exactness after the fact.
- Do not infer portable bitwise equivalence from algebraically identical
  reductions or reciprocal-square-root expressions across Triton and AscendC.
  Reduction topology, compiler lowering, fusion and final BF16 truncation are
  part of the observed numerical contract. A different implementation needs
  its own predeclared numerical criterion.
- Do not reopen projection or convolution slicing merely because it appears in
  a next-step note. Audit the active weight transformer and trace shapes first;
  the current uniform Dk64 path already selects Q/K projection and matching
  convolution rows before the original loader and TP sharding.
- Stop a launch/fusion branch when even its perfect endpoint ceiling is below
  the open gap. In the frozen Dk64 profile, separate L2 normalization is only
  about 0.202 ms per decode step and the full packed front end about 2.046 ms;
  neither can alone supply the required approximately 3.182 ms TPOT reduction.
- Preserve a lower semantic stage that passed its declared gates when a later
  arithmetic stage fails. Recover the active tree to that safe stage, retain
  the failed implementation and evidence in Git history, and never promote the
  earlier ABI or storage pass into acceptance of the failed arithmetic.
- Do not admit two-sided value/state reduction from an optimistic compute
  ceiling alone. Reducing Dv changes the RMS denominator and removes matching
  output-projection columns. First lock layer-shared coordinates and any
  foldable scalar on fit-only data, then require exact-checkpoint projected
  output and retained-post-RMS robustness on untouched data. If both the least
  aggressive target-crossing width and its control fail by a large margin,
  close the value-width branch instead of tuning nearby coordinates or gains.
- Distinguish metric granularity from selector granularity. Reporting
  per-head errors for one layer-shared coordinate set does not test static
  per-head coordinate sets. If that distinction can change a material
  decision, allow one predeclared fit-locked per-head screen while holding
  gains and all other freedoms fixed. If both layer-shared and per-head plans
  fail the same untouched projected-output and post-RMS gates by multiples,
  close nearby coordinate and gain selectors before NPU work. More selector
  freedom is not evidence of fidelity when the score ignores cross-column
  cancellation in the downstream projection.
- Preserving a retained value head's complete Dv width and RMS denominator
  does not make whole-head deletion low loss. For Qwen3.8 Nv48/Nk16, keeping
  one of each three independently parameterized value heads and folding all
  three output blocks with bounded scalars had enough optimistic cost headroom
  but failed all 18 cross-validated layer-fold projected-output comparisons;
  aggregate projected and feature error ratios were 3.887735 and 3.451611.
  Close nearby head choices and scalar ranges. Any reopened value-head route
  must define a materially different recurrent state/dynamics representation,
  not add freedom to the same select-one-and-fold mechanism.
- A best fit-locked rank-1 direction across each three-head group is a stronger
  necessary-capacity test than selecting one head. If it fails while being
  allowed to reconstruct from all three already-computed Dk64 operator outputs
  and retain the original three gates, RMS applications and output blocks,
  stop static one-direction value-state mixtures before dynamics or NPU work.
  The Qwen3.8 oracle failed all 18 layer-fold gates with aggregate projected
  ratio 5.410002 and operator-state reconstruction relative-L2 0.553733.
  Also calculate the post-value-source ceiling separately: retaining dense
  value projection/convolution while reducing only recurrent and downstream
  work credited 2.645949 ms/token, below the 3.181665 ms/token open gap.
- Before proposing an in-place recurrent-state/cache operator, inspect the
  active torch mutation schema and caller. A mutable `Tensor(a!)` passed
  directly from the cache means state update is already in place. Bind profile
  kernels to input shapes and per-layer call counts: QKV Slice/Concat traffic
  must not be relabelled as state-cache traffic. Treat compact allocation as a
  capacity mechanism until a fixed-workload per-token saving is identified.
- Do not repair a numerically failed fusion merely because its bug is now
  understood. Recompute the performance admission with all source-removable
  work, surviving per-layer launches and an optimistic measured graph floor.
  If the corrected mechanism still cannot close the open endpoint gap before
  charging its added arithmetic, stop before code, build or NPU.
- After closing the visible operator seams, express the open TPOT gap as a
  fraction of the complete DRRQR-attributable sublayer budget. Partition
  key/state, layout/fusion, value/output and whole-layer effects. Do not admit
  another selector when perfect removal of its partition is insufficient; a
  reopened program must name a mechanism whose affected fraction exceeds the
  measured threshold with margin for launches and added work.
- Audit nominal rank zero by semantics, not by its label. If Dk0 makes the
  complete algorithm-bearing residual branch zero, it is branch or layer
  pruning rather than a reduced recurrent representation unless a new
  derivation proves otherwise. Its relative-L2 against every nonzero local
  teacher output is exactly one, so evaluate the integer layer-removal count
  and frozen local windows before writing bypass code or launching NPU work.

## Iteration workflow

1. Read the frozen baseline, current handoff, latest DRRQR iteration record,
   and the actual model/operator path.
2. Restate the still-open joint gap and name one medium-term DRRQR capability
   that can materially close it.
3. Prove the proposed work is not already active and calculate its optimistic
   endpoint ceiling from the frozen profile before treating it as a candidate.
4. Admit one bounded short experiment with pass, rejected, failed, invalid and
   inconclusive exits declared before implementation.
5. Prefer the cheapest faithful gate: source/foldability, held-out trajectory,
   target-NPU numerical/state, integrated activation, endpoint, then accuracy.
6. Adapt an operator only when it removes a measured DRRQR-specific seam or is
   required for a valid logical-rank/state design.
7. Require exact source/build/load identities and preserve all negative
   artifacts outside Git with hashes in the iteration record.
8. Promote one evidence level at a time. On failure, recover the active tree;
   on rejection, stop the tested variant; on invalidity, repair comparability
   without assigning an algorithm trend.
9. Recheck long-, medium-, and short-term alignment before choosing the next
   loop. Commit and push the coherent checkpoint.

## Portability review

Before implementation, record model-level benefit, saved and added
compute/memory/data movement, supported dtype/shape contracts, alignment and
compiler assumptions, backend capability dispatch, and when the gain may
disappear. A fallback proves correctness availability, not portable speedup.
Each admitted environment ultimately needs its own paired NPU evidence.

## Evidence sources

- `projects/drror_vllm_ascend/AGENTS.md`
- `projects/drror_vllm_ascend/docs/experiments/qwen38-drrqr-correctness-20260908/FROZEN_BASELINE_V1.json`
- `projects/drror_vllm_ascend/docs/experiments/qwen38-drrqr-correctness-20260908/DRRQR_ASCEND_EXPERIENCE.md`
- `.agents/evals/practice-iterations/drrqr-*.yaml`
- `.agents/HANDOFF.md`

## Verification

- The short iteration names its DRRQR candidate, joint gap, evidence level,
  claim ceiling, stop rule, portability assumptions, and next action.
- Historical failures are linked, not generalized beyond tested scope.
- The active handoff and iteration record agree.
- `./scripts/validate-mst.sh`, focused project checks, and
  `git diff --check` pass before push.
