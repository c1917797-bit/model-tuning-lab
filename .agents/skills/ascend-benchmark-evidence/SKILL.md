---
name: ascend-benchmark-evidence
description: Use to design, run, compare, or review Ascend NPU model-inference benchmarks; require correctness-first, apples-to-apples evidence and separate cold, steady, boundary, lifecycle, and resource measurements.
---

# Ascend Benchmark Evidence

## Purpose

Produce evidence strong enough to accept or reject an inference optimization
without confusing environment drift, warmup, caching, or workload changes with
real improvement.

## Protocol

1. Freeze model and tokenizer revisions, dtype or quantization, batch and
   sequence distributions, request concurrency, parallelism, seeds, dataset
   slice, framework settings, compilation or graph mode, and device binding.
2. Declare the primary metric and thresholds before running the candidate.
3. Run correctness gates first: load success, output validity, numerical or
   task-quality tolerance, deterministic checks where applicable, and expected
   NPU execution.
4. Measure baseline and candidate with the same commands and controlled order.
   Use explicit warmups, multiple measured repetitions, and report dispersion.
5. Separate these evidence classes:
   - cold/startup: import, model load, compile, first token, first request;
   - steady: throughput, request latency, TTFT, TPOT, and token latency;
   - boundary: batch, sequence length, concurrency, memory pressure, and OOM;
   - lifecycle: repeated start/stop, long soak, cache reuse, and recovery;
   - resources: NPU memory/utilization, CPU, RAM, I/O, power, and process count.
6. Report units, sample count, p50/p95/p99 where meaningful, errors, timeouts,
   and excluded runs with reasons.
7. Store concise summaries in Git and store raw logs/traces externally with
   checksums and retention information.
8. Classify the result using `ascend-inference-tuning-loop` and commit/push the
   measurement stage even when it fails or shows no benefit.

## Warmup, specialization and generalization

Treat startup warmup as a deployment treatment, not automatically as faster
model arithmetic. Freeze a bounded synthetic/development warmup policy before
examining held-out evaluation inputs or their exact length list. Do not replay
the evaluation corpus to manufacture a generalization claim.

Report time-to-ready, warmup cost, first unseen-shape latency and steady-state
latency separately. Compare matched process/cache states and controlled run
order; a second control repetition is not a candidate. When warmup itself is
the variable, include its startup and resource cost rather than silently
excluding it from the comparison.

Separate executable/compile caches from prompt KV/prefix caches. Use distinct
warmup and measured-request cache salts and verify the observed cache behavior.
Test both unseen contents and unseen shape/batch/concurrency combinations with
the same frozen policy. Same-content or same-shape replay proves neither.

New compilation files and slow requests are correlation evidence until
request/phase timestamps and compilation events are aligned. Inspect the real
specialization key and dispatch path: an already-dynamic length parameter does
not exclude specialization through another compile-time parameter. Do not
change compiler safety settings or remove specializations without a bounded
correctness/performance experiment on the pinned runtime.

Keep historical references and fresh same-environment controls as distinct
denominator IDs. Read P95 from the raw repetition results, not a P50 summary.
Fingerprint dirty source bytes, launcher and patch hashes as well as Git HEAD;
equal commits alone do not prove equal deployed code.

## Measurement hygiene and long-matrix integrity

Treat any concurrent host work that can perturb latency as part of the
measurement environment. Large model-file hashing, operator compilation,
package builds, profiler collection, storage scans, competing inference jobs,
and cache-destructive diagnostics must run outside measured windows unless they
are the declared experimental variable. CPU-only work can still invalidate an
NPU latency run through host CPU, memory, storage, launch, or scheduling
contention.

If such work overlaps a measured cell, preserve the original artifact and mark
the cell contaminated or inconclusive. Record the overlap window and known
workload, then create a separately identified rerun under matched lifecycle and
cache state. Never overwrite the original cell, silently drop it, or choose the
faster of contaminated and clean runs after seeing the result.

For long benchmark matrices, make progress and recovery auditable per unit:

- one controller owns the matrix and serializes cells by default;
- every cell records start/end, workload identity, repetition, cache salt or
  equivalent isolation key, request/error/finish counts, and an artifact hash;
- controller state records the last completed cell and fail-closed status;
- final summaries are recomputed from immutable per-cell artifacts and have
  their own checksum;
- service cleanup/resource release is recorded separately from experiment
  completion.

When designing, auditing, or resuming a full-corpus multi-concurrency matrix,
read [references/long-matrix-baseline-lessons.md](references/long-matrix-baseline-lessons.md).
It captures the reusable success pattern and the promotion failures observed in
the Qwen3.8 TP8 full357 baseline without turning that single run into a universal
model rule.

Do not run a second benchmark against the same service merely because a long
matrix appears slow. Parallel clients change scheduling and batching and create
a different experiment unless concurrent controllers are explicitly the
treatment. Likewise, a service restart creates a new compilation/cache
lifecycle: cold, warm and restarted repetitions must be labeled rather than
pooled as if they were one steady-state population.

## Quality-oracle scope

Name the strongest oracle the dataset actually supports:

- reference-answer metrics require populated, trustworthy reference answers;
- deterministic byte equality is strong evidence for identical execution but
  not a substitute for semantic review when valid reduction order, natural
  stopping, or runtime scheduling changes bytes;
- when reference answers are absent, use same-runtime paired control/candidate
  review over frozen indexes and state the claim as task-specific semantic
  no-regression, not general accuracy preservation.

For paired review, automatically accept byte-identical rows and review every
different pair for retained intent, facts, constraints, completeness, and
readability. Record row identities, capture hashes, reviewer/time metadata,
request errors, finish reasons, and the number of material regressions. A
small canary may advance a candidate but cannot stand in for the declared
full-corpus promotion gate.

If a quality controller or serving process fails before the declared population
is complete, preserve the valid completed rows with stable identities and
hashes, but classify the suite as incomplete. Do not calculate or promote a
final accuracy/pass-rate from a prefix unless the protocol explicitly defines
that prefix as the evaluation population. Distinguish at least model/output
quality failure, request/transport failure, serving lifecycle failure,
evaluator/scorer failure, and post-run audit/cleanup failure. An operational
failure can invalidate completion without proving a model-quality regression.

## Translation and progression gates

Operator or microbenchmark speedup is mechanism evidence, not a service result.
Before predicting E2E impact, record the real service shapes, affected calls,
covered fraction, baseline and candidate per-call delta, overlap or critical
path, and an optimistic maximum service-level benefit. Then measure the same
candidate bytes in the service.

Separate diagnostic instrumentation from the candidate treatment. Profiled or
instrumented timing may select a hypothesis, but must not be reported as the
candidate's performance result unless the instrumentation overhead is isolated.

Use a predeclared fail-fast progression: first run correctness and representative
low/high boundary concurrency. Expand to the full repetition matrix only when
every primary metric passes its progression threshold and no safety, quality,
or tail-risk gate fails. Preserve the stopped result; do not consume a full
matrix to reconfirm a clearly missed gate.

## Comparability Gate

Do not compare results when material source, model, hardware, driver, firmware,
CANN, framework, container, power mode, topology, workload, or cache state
differs. Re-baseline instead.

## Review Traps

- Throughput alone can hide latency or correctness regressions.
- Averages can hide tails and instability.
- A single warm run cannot establish steady-state performance.
- Host telemetry cannot prove physical NPU execution.
- A faster compile cache hit is not a cold-start improvement.
- Matching response bytes are strong deterministic evidence, but they are not
  automatically full semantic accuracy when generation is stochastic, natural
  stopping differs, or the reference dataset lacks ground-truth answers. State
  the exact quality claim the oracle supports.

## Verification

- Baseline and candidate environment fingerprints match.
- Correctness gates pass before a performance win is accepted.
- Commands, thresholds, repetitions, and exclusions are recorded.
- Candidate bytes, activation evidence, and diagnostic overhead treatment are
  recorded.
- Microbenchmark claims include an E2E translation bound and are not relabeled
  as service wins.
- Cold, steady, boundary, lifecycle, and resources are reported separately or
  explicitly marked out of scope.
- Raw artifact hashes resolve and no protected data is committed.
- The reported precision or quality claim does not exceed the dataset oracle.
- Quality completion proves the declared population was fully collected and
  scored; partial clean rows after a lifecycle failure remain partial evidence.
- Heavy diagnostics are outside measured windows or the affected cells are
  explicitly classified as contaminated/inconclusive with preserved artifacts.
- Long matrices can be resumed and independently recomputed from per-cell
  identity, completion markers and hashes rather than trusting only a summary.
