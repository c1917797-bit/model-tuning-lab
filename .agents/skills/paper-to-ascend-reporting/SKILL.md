---
name: paper-to-ascend-reporting
description: Use to turn a Paper-to-Ascend experiment into a handoff-ready evidence report with paper mechanism, fit decision, source map, baseline/candidate results, profiler findings, decision scope, and next loop.
---

# Paper-to-Ascend Reporting

## Purpose

Make Paper-to-Ascend results reusable. The report should let a future maintainer
understand what was tried, why it fit or did not fit, what evidence exists, and
what next action is safe without reading the full chat history.

## Workflow

1. Gather the paper ingestion note, architecture-fit decision, source map,
   experiment record, benchmark summaries, profiler summaries, artifact paths,
   and Git stage commits.
2. State the decision exactly: `accepted`, `rejected`, `inconclusive`, or
   `failed`.
3. Scope the decision: paper idea, implementation, operator/router, block,
   service, or full model. Do not overstate.
4. Summarize correctness first, then performance, then resource and profiler
   evidence.
5. Record environment comparability: source commit, model/tokenizer identity,
   runtime/container, CANN/driver/firmware, physical NPU IDs, workload, and cache
   state.
6. Include negative evidence and excluded runs with reasons.
7. Identify the next loop: continue, profile, re-baseline, choose another paper,
   select another architecture, request retraining authorization, or stop.
8. Update branch-local handoff and durable lessons when the result should guide
   future work. Reconcile global `.agents/HANDOFF.md` only during serialized
   integration.

## Report shape

Use this compact structure unless the target repository already has a stricter
format:

- paper and mechanism;
- target model/runtime fit;
- source map and implementation seam;
- experiment variable and protocol;
- baseline and candidate summary;
- correctness and target-device proof;
- profiler/operator evidence when used;
- artifacts and hashes;
- decision and scope;
- recovery state;
- next loop.

## Boundaries

- Do not include credentials, model weights, datasets, raw traces, or large logs.
- Do not replace experiment YAML with prose; the report complements the record.
- Do not treat chat history as handoff state.
