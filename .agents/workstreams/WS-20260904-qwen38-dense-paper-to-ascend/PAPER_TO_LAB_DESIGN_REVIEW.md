# Paper-to-Lab Design Review

Updated: 2026-09-06

## Executive judgment

The overall design is reasonable and unusually strong on reproducibility,
resource isolation and fail-closed evidence. It is suitable as a lab landing
framework, but the workstream has mixed three different scientific questions
and once used the wrong baseline for a historical comparison. The framework
should be retained; the experiment ledger and comparison scopes should be
split.

The current authoritative state is:

- the Qwen3.6 Dk64 speed-oracle candidate failed its performance gate;
- the Qwen3.6 PDC-only versus PDC+Hypic experiment completed and rejected
  adoption for that configuration;
- the Qwen3.6 no-cache versus Hypic-only historical-ruler reproduction is
  paused after the complete baseline performance phase and baseline
  LongBench-v2 run 1;
- no historical-ruler treatment result exists, so no Hypic gain may yet be
  reported for that question.

## Design from paper to laboratory

    paper claim
        -> mechanism and addressable cost
        -> implementation boundary
        -> cheap feasibility oracle
        -> paper-aligned treatment
        -> frozen ruler and orthogonal controls
        -> isolated execution lifecycle
        -> activation/correctness/performance/quality/profile evidence
        -> fail-closed decision
        -> reusable knowledge and resumable handoff

### 1. Convert the paper into falsifiable claims

For each paper feature, record:

- the claimed mechanism;
- the exact model subgraph or runtime path it can change;
- the expected metric and direction;
- what the paper does not implement in the current system;
- a falsifier that can stop the experiment early.

For the state-reduction paper, fixed-first-channel and L1 pruning are
feasibility probes. They are not DRRQR and cannot support a paper-complete or
accuracy-lossless conclusion. True DRRQR is the paper-aligned treatment.

### 2. Use a cheap performance oracle before expensive qualification

A structural candidate first has to show a stable warm performance signal on
real weights. Only then is it worth paying for broad quality, native profiling
and a second-model generalization run. This early-stop rule worked correctly
for Qwen3.6 Dk64: median TPOT was 369.1616 ms/token for baseline and
369.1632 ms/token for treatment, so the candidate was rejected before
expensive qualification.

### 3. Define controls by one-switch differences

The general paper-to-Ascend matrix is:

| Group | Native Ascend change | Paper algorithm |
|---|---:|---:|
| G1 | off | off |
| G2 | on | off |
| G3 | off | on |
| G4 | on | on |

This is appropriate for interaction and integration questions. A historical
reproduction is a separate two-arm question: no-cache/Hypic-off versus
no-cache/Hypic-on. It must not be pooled with PDC-only versus PDC+Hypic.

### 4. Freeze the ruler before measuring

Freeze model/checkpoint identity, image digest, device mapping, CPU set,
prompt and dataset hashes, request order, generation semantics, concurrency,
warmups, repetitions, metric parser and service configuration. Each result
must bind to these identities by hash.

Performance and quality deliberately use different generation semantics:

- performance uses fixed output and may use ignore_eos=true;
- quality uses temperature 0, seed 0, thinking disabled and ignore_eos=false.

For the current historical reproduction, dataset selection also follows the
successful practice: LongBench-v2 and GSM8K are runnable with the delivered
files; CEval is excluded by operator decision; NIAH+ remains unavailable
because its authoritative source files do not exist and must not be
substituted.

### 5. Isolate resources and lifecycles

The current Hypic lane is exactly host NPU0-3 plus CPU112-191. Host NPU4-7 and
their workload are out of scope. Only one arm may run at a time, and cleanup
may stop only the exact experiment-owned container.

Performance, quality and profiling are separate service lifecycles. Restart
the identical configuration between performance and quality. Use a profile
clone with only the declared profiling delta; never time capture hooks as
part of the A/B benchmark.

### 6. Build independent evidence gates

An adoption decision requires all of the following:

1. runtime activation evidence proves the intended path ran;
2. semantic canaries and request counters prove valid execution;
3. repeated performance evidence shows a stable improvement;
4. repeated quality evidence stays within measured baseline variation and
   exposes per-dataset cliffs;
5. native profiling attributes the gain to the target region;
6. missing paper features and unsupported generalization remain explicit.

A valid profile capture is not algorithm acceptance, and a speed result is
not quality evidence.

### 7. Decide fail-closed

Adopt only when a single candidate passes every required gate. Otherwise use
iterate, reject or pending. A paused or incomplete experiment must never
inherit a conclusion from a different experiment.

## What is well designed

| Design choice | Assessment |
|---|---|
| One-switch A/B and G1-G4 matrix | Correct; exposes the baseline and interaction effect |
| Three repetitions and measured baseline variation | Correct; avoids single-run and generic-noise claims |
| Phase restart between performance and quality | Correct; prevents cache, graph and profiler contamination |
| Hash-bound datasets, configs and artifacts | Correct; prevents accidental ruler mixing |
| Exact device/container ownership | Correct and essential on the shared eight-card host |
| Fail-closed preflight and resumable controller | Correct; preserves evidence and avoids duplicate long runs |
| Independent runtime, quality and profile gates | Correct; prevents performance-only adoption |
| Early performance stop for structural candidates | Efficient and scientifically defensible |

## What needed correction

1. The workstream name and early documents still say Qwen3.8 while the current
   target is Qwen3.6-27B. This is provenance, not the current target, and must
   not leak into commands or conclusions.
2. Dk64 paper reproduction, PDC coexistence Hypic and no-cache historical
   Hypic reproduction are different questions. They now have separate
   experiment/evidence/decision records.
3. The first Hypic comparison used PDC-only as baseline. That result is valid
   for coexistence, but it cannot explain the employee no-cache versus
   Hypic-only result.
4. Qwen3.5-27B TP2 employee measurements and Qwen3.6-27B TP4 current
   measurements may be compared by direction and relative delta, not by
   demanding identical absolute latency or throughput.
5. Controller syntax checks alone were insufficient. Serialized argv,
   evaluator schema and idempotent artifact gates also need self-tests.
6. The canonical handoff became a long diary and contained stale states. The
   current snapshot is now short; detailed history is in the retrospective
   and archived handoff.

## Recommended operating model

Keep three ledgers:

- Track A — paper-derived Dk64/DRRQR: currently rejected for the tested
  Qwen3.6 speed-oracle; reopen only for a materially different implementation.
- Track B — PDC coexistence Hypic: completed, evidence complete, adoption
  rejected for the tested configuration.
- Track C — employee historical ruler: paused and incomplete; resume only on
  explicit operator instruction, then finish baseline quality, treatment
  performance, treatment quality and final comparison.

This revised design is reasonable for laboratory use. Its main residual risk
is not the measurement framework; it is scope discipline. Every report must
name the exact track, denominator, model, TP degree and missing gates.
