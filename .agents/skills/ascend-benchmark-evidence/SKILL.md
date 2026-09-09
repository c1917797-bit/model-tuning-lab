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
