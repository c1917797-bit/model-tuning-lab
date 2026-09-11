# Long-matrix baseline lessons

Read this reference when a baseline spans a full dataset, several concurrency
levels, repeated cells, or a separate quality pass. It records one concrete
Qwen3.8 TP8/full357 case and the decisions that generalize from it. The
authoritative case record is
`.agents/experiments/exp-20260910-qwen38-tp8-full357-baseline.yaml`.

## What succeeded

- One controller serialized four concurrency levels with three repetitions
  each. All 12 performance cells completed and every request finished without
  an application error.
- Immutable per-cell artifacts survived the long run. The final summary was
  recomputed from repetition results, hashed, and retained outside Git while a
  concise structured record was committed.
- The summary used the median of repetition-level metrics and retained P95/P99,
  throughput, request rate, request counts, units, and protocol identity.
- Model identity separated checkpoint bytes and architecture metadata from the
  served API alias. A stale alias was recorded as provenance risk rather than
  silently treated as proof of the loaded model.
- Performance completion, quality completion, cleanup, and promotion were kept
  as different states. This allowed useful performance evidence to be preserved
  without overstating the final decision.
- The result was committed and pushed even though it could not be promoted as a
  clean baseline. A failed gate is still durable evidence when its scope and
  limitations are explicit.

## What failed or remained unproven

- One measured cell overlapped a large weight-file hash read and observed
  operator-build activity. NPU exclusivity alone did not prevent CPU, memory,
  storage, or compilation interference.
- The other cells were structurally complete, but there was no continuous
  full-window proof that the host was interference-free. Absence of a noticed
  conflict is weaker than positive isolation evidence.
- A later quality controller stopped on an operational `npu-smi` command
  failure after producing a well-formed prefix. The prefix was retained, but it
  was not promoted to a full-population score and did not prove a model-quality
  regression.
- The service alias named another model family. Because the loaded path and
  metadata were captured independently, the performance run remained
  interpretable, but alias-only consumers could have reached the wrong
  conclusion.
- A completed 12/12 performance matrix did not imply a completed experiment:
  correctness, quality, lifecycle evidence, isolation, and cleanup each needed
  their own completion markers.

## Reusable decisions

1. Pre-register a cell identity containing workload, concurrency, repetition,
   cache/lifecycle state, model fingerprint, launcher fingerprint, and expected
   request count.
2. Before every measured cell, capture an interference fence: active benchmark
   controllers, inference services, NPU processes, CPU-intensive builds,
   profilers, storage scans, large hashes, and relevant container activity.
3. Observe the same signals through the measured interval. A start-only
   snapshot cannot prove full-window isolation.
4. If interference overlaps a cell, keep the artifact and label it
   `contaminated` or `inconclusive`. Schedule a new cell identity; never
   overwrite, silently exclude, or select the faster observation.
5. Aggregate only compatible repetitions. State the aggregation rule, retain
   dispersion and tails, and make the summary reproducible from immutable cell
   files.
6. Give performance, quality, service lifecycle, audit, and cleanup separate
   status fields. Promotion requires every declared gate; completion of one
   stage does not infer completion of another.
7. Treat controller/tool failures as operational until output evidence proves a
   model-quality failure. Preserve valid prefixes but do not score an undeclared
   prefix as the full population.
8. Record actual model bytes/metadata separately from the served name. Refuse an
   apples-to-apples claim when the effective model identity cannot be proven.

## Minimum clean rerun gate

A rerun may replace an inconclusive cell in the promoted baseline only when it
has a new immutable identity, matched protocol and lifecycle state, complete
request counts, zero unexplained errors, full-window interference evidence, and
an artifact hash. Keep the earlier cell as history and link the superseding
cell; do not mutate the earlier summary in place.

The clean-baseline decision remains `inconclusive` until the declared quality
population also completes or the experiment contract explicitly scopes quality
out before execution.
