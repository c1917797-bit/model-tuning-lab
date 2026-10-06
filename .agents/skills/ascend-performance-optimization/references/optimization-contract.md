# Ascend Performance Optimization Contract

Use this reference to turn profiling or benchmark evidence into one bounded
optimization candidate. Keep machine-specific paths and measured values in the
owning experiment, not in this reusable reference.

## Candidate ledger

Record at least:

| Field | Required evidence |
| --- | --- |
| Candidate ID | Workstream, experiment, branch, and commit |
| Runtime identity | Model/tokenizer, dtype/quantization, image, framework, CANN, driver, firmware |
| Execution path | Dense/MoE/MTP/speculation/cache/graph features actually enabled |
| Baseline | Workload, TP/DP, physical devices, port, warmup, repetitions, metric aggregation |
| Symptom | Measured phase and metric with raw artifact hash |
| Cause | Profiler/source evidence and confidence; label a diagnostic hypothesis explicitly |
| Opportunity bound | Covered calls, non-overlapped cost, optimistic local and E2E benefit |
| Treatment | One primary changed seam and exact candidate bytes/configuration |
| Activation | Per-worker/rank/process markers and disabled-control behavior |
| Guardrails | Correctness oracle, quality gate, memory/tail/stability/resource ceilings |
| Progression | Canary, fail-fast concurrency, full matrix, and stopping thresholds |
| Rollback | Disable/uninstall/restart/cleanup commands and expected proof |
| Decision | Accepted/rejected/inconclusive/failed plus next materially different hypothesis |

## Strategy matrix

### Compute or operator

Check real shapes, dtype, layout, call count, stream overlap, fusion incumbent,
and supported CANN/vLLM-Ascend paths. A microbenchmark must beat the correct
incumbent at service shapes and still pass E2E.

### Memory, KV/cache, or capacity

Separate bandwidth, allocation, fragmentation, copy, eviction, and capacity
effects. Report both latency and usable capacity. Never treat lower allocation
as a win when cache hit rate, output validity, or lifecycle safety regresses.

### Scheduler, batching, or CPU launch

Measure queueing, batch formation, engine steps, Python/CPU gaps, request
distribution, and tail behavior. Preserve request semantics and compare the
same arrival pattern, stopping behavior, and output-length distribution.

### Communication or topology

Prove physical rank/device mapping, collective call shapes, critical-path
overlap, cross-rank skew, and lifecycle correctness. A summed HCCL duration is
not removable wall time. Fresh-process and crash/restart canaries precede E2E.

### Graph, compilation, or specialization

Separate cold compile, first-unseen-shape, warmed shape, cache reuse, and mixed
arrival evidence. A cache hit or narrower shape set is not an arithmetic speedup.

### Lifecycle or resource contention

Attribute processes, containers, ports, device claims, CPU/NUMA placement,
memory, and leaked state before modifying code. Do not terminate or mutate
unowned workloads. Repeated start/stop and cleanup proof are part of acceptance.

## Candidate rejection rules

Reject or redirect before expensive runs when:

- the optimistic opportunity bound cannot reach the milestone;
- the candidate targets a path not enabled by the live workload;
- a supported exact path already provides the treatment;
- correctness or quality recovery depends on a forbidden feature;
- activation cannot be proven in every required process;
- the rollback is not bounded;
- the same candidate bytes already reached a deterministic terminal result.
