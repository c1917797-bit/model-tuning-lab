---
name: ascend-performance-optimization
description: Use when measured Ascend inference bottleneck evidence must be converted into one bounded optimization candidate across compute, memory, scheduling, communication, compilation, or lifecycle paths; do not use it merely to run benchmarks or collect profiles.
---

# Ascend Performance Optimization

## Purpose

Convert an evidenced Ascend inference bottleneck into the smallest credible
optimization treatment, then hand that treatment to canary, delivery,
performance, and quality gates. This skill owns candidate selection and
implementation strategy. It does not replace profiling or benchmark evidence.

## Entry gate

Before changing code or configuration, require:

- one active experiment/workstream and one declared primary metric;
- a comparable baseline and exact model, runtime, image, source, hardware,
  topology, workload, and feature identities;
- measured attribution or a bounded diagnostic hypothesis;
- the affected phase, shapes, call frequency, covered fraction, and optimistic
  end-to-end opportunity bound;
- one primary variable, rollback, abort threshold, and owned resources.

If attribution is missing, route to `ascend-cannbot-profiler`. If perfect
removal of the measured cost cannot reach the declared milestone, reject or
redirect the candidate before implementation unless it unlocks a separately
named and testable successor.

## Model-path gate

Never assume the target is Dense or that MTP/speculative decoding is disabled.
Record which execution paths are actually enabled and which the task permits:

- Dense attention/MLP;
- MoE routing, expert placement, dispatch, packing, GMM, and collectives;
- MTP, speculative decoding, draft/verify scheduling, and acceptance behavior;
- quantized or mixed-precision paths;
- prefix/KV cache, chunked prefill, graph/compile, and scheduler policies.

Optimize only the live permitted path. A result from one path does not transfer
to another without a fresh source map, opportunity bound, and baseline.

## Bottleneck classification

Classify the primary bottleneck before choosing a treatment:

1. compute or operator;
2. memory movement, allocation, KV/cache, or capacity;
3. scheduler, batching, queueing, or CPU launch;
4. HCCL communication, synchronization, placement, or topology;
5. graph capture, compilation, specialization, or cold-start;
6. lifecycle, process ownership, leakage, restart, or resource contention.

Read [references/optimization-contract.md](references/optimization-contract.md)
when creating the candidate ledger or choosing among these classes.

## Candidate policy

For every candidate, record the causal chain:

`measured symptom -> attributed cause -> changed seam -> expected local delta
-> expected service metric -> disproof signal`.

Prefer, in order:

1. an exact supported configuration or official runtime path;
2. a removable plugin/monkeypatch against the pinned official image;
3. a bounded framework or backend source change;
4. a native operator, kernel, collective, or system change only when the lower
   risk seams cannot express the treatment and the additional scope is
   explicitly admitted.

One candidate changes one primary mechanism. Diagnostic instrumentation is not
part of the treatment unless its overhead is isolated. Do not combine local
wins whose denominators, model paths, or baselines differ.

## Workflow

1. Freeze the entry-gate evidence in the experiment record.
2. Classify the bottleneck and identify the smallest live source/configuration
   seam with `ascend-source-map` when needed.
3. Create a candidate ledger with expected benefit, risk, correctness oracle,
   resource ceiling, activation proof, rollback, and disproof signal.
4. Implement the cheapest falsifiable version. Use
   `ascend-canary-implementation` for the first one-variable runtime proof.
5. For a surviving local runtime technique, use
   `runtime-monkeypatch-delivery` before formal service benchmarking.
6. Verify exact-shape correctness, all required process/rank activation,
   intended physical-NPU execution, and disabled control.
7. Use `ascend-benchmark-evidence`: run the preregistered fail-fast screen
   before the complete repeated concurrency matrix.
8. Use `ascend-model-quality-evaluation` whenever output semantics, precision,
   quantization, routing, cache behavior, MTP/speculation, or model decisions
   can change.
9. Classify the result through `ascend-inference-tuning-loop`; preserve
   accepted, rejected, inconclusive, and failed evidence.
10. Recover rejected/failed active code while retaining its commits and
    artifacts. A successor must change a material hypothesis or treatment.

## Acceptance boundary

An optimization is accepted only when:

- live-path activation and the disabled/control path are proven;
- correctness and applicable quality gates pass;
- primary latency/throughput thresholds pass across comparable repetitions;
- tail, memory, stability, lifecycle, and neighboring-resource gates do not
  regress beyond declared limits;
- the service result fits the predeclared opportunity bound or the discrepancy
  is explained with evidence;
- rollback restores official behavior and releases owned resources.

A faster operator is component evidence, not a service win. A service win is
not automatically transferable to another model path, concurrency, output
length, accelerator generation, TP/DP layout, or feature configuration.

## Verification

- Candidate ledger and experiment record resolve to exact commits and hashes.
- Only one primary treatment differs between baseline and candidate.
- The applicable canary, monkeypatch, benchmark, and quality validators pass.
- Negative results leave the safe branch tree disabled or recovered.
- `./scripts/validate-mst.sh` and `git diff --check` pass.
