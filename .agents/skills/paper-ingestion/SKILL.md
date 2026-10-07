---
name: paper-ingestion
description: Use to extract a research paper into implementable inference hypotheses, separating paper claims, required model/runtime mechanisms, benchmark assumptions, and non-transferable parts before Ascend work begins.
---

# Paper Ingestion

## Purpose

Convert a paper from prose into a bounded engineering hypothesis. This skill is
for understanding what the paper actually changes and what must be true before
an Ascend implementation is worth attempting.

## Workflow

1. Identify the paper, version, source, and any code/artifact links used.
2. Extract the claimed optimization target: training, inference, model
   architecture, runtime scheduler, KV/cache layout, operator, kernel,
   communication, or system configuration.
3. Summarize the mechanism in implementation terms: inputs, changed dataflow,
   state added or removed, algorithmic complexity, and expected overhead.
4. List required prerequisites: checkpoint structure, tokenizer/model config,
   dtype/quantization, serving framework features, CANN/operator support,
   hardware topology, and whether retraining is required.
5. Separate portable ideas from paper-specific assumptions such as GPU-only
   kernels, unavailable training data, custom checkpoints, or benchmark-only
   shortcuts.
   For a derivative that implements only a paper subset, run its bounded-scope
   and full-scope capability/source audits when available. Record both the
   supported mechanism IDs and the full-scope missing IDs; an expected
   full-scope failure is evidence of a boundary, not a failed bounded result.
   Do not promote a passing C1/C2 hot-reuse audit to a paper-complete claim
   when distributed C3 or another required mechanism remains absent.
6. Translate the paper into one or more candidate hypotheses, each with one
   primary variable and an expected bottleneck it should improve.
7. Record uncertainty explicitly. Unknown architecture or runtime prerequisites
   route to `ascend-architecture-fit` or `ascend-source-map`, not implementation.

## Source-backed migration selection

When the user wants a new GPU-to-Ascend contribution, distinguish that objective
from reproducing or adopting an existing Ascend implementation. Rank candidates
by a concrete missing target capability and measured opportunity, not by paper
headline speedup or the mere existence of a repository.

- Record the exact title/version and whether the source is a research paper,
  competition technical report, or engineering repository. Do not silently
  substitute one for a user-required publication type.
- Verify the paper-to-code link, core implementation files, fixed commit,
  reference tests, supported shapes/dtypes, and redistribution license. An
  empty repository, framework dependency, or related implementation does not
  satisfy a requirement for the paper's source. Public visibility alone does
  not establish permission to redistribute it.
- Check target implementations and relevant PRs. Keep proposed, implemented,
  merged, released, installed, activated, and validated states separate. A
  shared name such as GDN, solve_tri, or fused prefill does not establish that
  two implementations use the same paper algorithm.
- Record author baseline and workload before quoting gains. A competition
  reference, eager framework, or cache-disabled denominator is not equivalent
  to the installed optimized serving baseline. A failed search means source
  availability is unconfirmed, not that no code exists.
- Recommend a bounded candidate with explicit unknowns. Do not describe a
  source-compatible method as high-probability or proven on the target model
  before architecture, missing-implementation, and bottleneck checks pass.

For the motivating cases and evidence boundaries, read
[selection and baseline lessons](references/selection-baseline-lessons.md).

## Ingestion note

Produce a concise paper ingestion note suitable for an experiment record or
workstream handoff:

- paper identity and source;
- mechanism summary;
- required model/runtime/hardware prerequisites;
- expected performance path and possible new overhead;
- whether retraining is required;
- candidate first hypothesis;
- evidence gaps and next checks.

For a retrospective ingestion after implementation has already begun, label
the sequence honestly: the note may validate current fit, but it cannot turn
an omitted pre-implementation applicability gate into a historical pass.

## Boundaries

- Do not treat author benchmark claims as local evidence.
- Do not infer checkpoint support from paper compatibility alone.
- Do not open a tuning workstream until the first hypothesis passes the
  Paper-to-Ascend applicability gate.
