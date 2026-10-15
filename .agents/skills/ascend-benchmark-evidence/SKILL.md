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
   NPU execution. When native and higher-precision oracle results disagree,
   apply [independent numerical truth and native baselines](references/numerical-oracle-and-native-baseline.md)
   before assigning the failure or revising the numerical contract.
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

## Comparability Gate

Do not compare results when material source, model, hardware, driver, firmware,
CANN, framework, container, power mode, topology, workload, or cache state
differs. Re-baseline instead.

For resumable task-accuracy evaluations, bind every persisted response row to
the full protocol identity: model/tokenizer and runtime revision, dataset and
prompt/scorer hashes, sampling and thinking settings, EOS/stop behavior,
`max_tokens`, and candidate/baseline arm. On resume, reject rows whose identity
differs; use a fresh non-overwriting output root when any field changes. A
command-line change alone is insufficient if the evaluator silently skips
previously completed request IDs. Before applying a user-allowed accuracy loss,
state whether the limit means percentage points or relative percent, compute
both per final task, and do not reuse that task-level limit as an intermediate
NPU tensor/state numerical tolerance.

## Review Traps

- Throughput alone can hide latency or correctness regressions.
- Averages can hide tails and instability.
- A single warm run cannot establish steady-state performance.
- Host telemetry cannot prove physical NPU execution.
- A faster compile cache hit is not a cold-start improvement.

## Verification

- Baseline and candidate environment fingerprints match.
- Correctness gates pass before a performance win is accepted.
- Commands, thresholds, repetitions, and exclusions are recorded.
- A resumed run proves that every reused row has the current protocol identity;
  changed output caps cannot inherit older responses.
- Cold, steady, boundary, lifecycle, and resources are reported separately or
  explicitly marked out of scope.
- Raw artifact hashes resolve and no protected data is committed.
