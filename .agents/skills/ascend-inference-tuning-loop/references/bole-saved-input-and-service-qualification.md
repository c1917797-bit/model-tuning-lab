# Saved-input diagnosis and bounded BOLE service qualification

Use after a BOLE/GDN component, native-control, consumer or service-entry failure.
These are verified stage lessons, not a new technology acceptance report.
Read the linked original records before reusing any result; an old PASS grants
neither a new resource lease nor a later-stage PASS.

## Evidence-backed successes and what changed the next action

1. **Reuse the exact failed inputs to discriminate causes.** The saved native-AR
   attention replay reproduced all 256 original outputs bitwise. Under unchanged
   pointwise bounds, BF16 had 39 failures with either inner-precision setting;
   FP16 had zero with either setting. This supports a boundary-precision repair
   for that private control, not a general claim that BF16 or production vLLM
   is wrong. Preserve original BF16 results, label FP16 as a new variant, and
   require the subsequent model/control comparison. A source-derived private
   AR implementation is not the untouched production dispatcher.
2. **A narrow reader repair can avoid recapturing model tensors.** R20's receipt
   comparison reused `expected` for a dictionary, overwriting the rank counter.
   The repair renamed only the local cast variable, bound the original producer
   root and recorded the new reader identity; original math and tensor bytes
   stayed unchanged. Preserve the failed parent. Qualify captured completeness,
   ownership, source/raw hashes and the complete independent consumer under a
   new result identity before using the recovered evidence. Do not mark the old
   run PASS or assume all remaining model discrepancies disappeared.
3. **Carry the actual mechanism into an incremental service test.** Service v6
   passed a bounded TP4 first-request test: 131-token prefix, four output tokens,
   component gates, actual scheduler publication, HTTP token-ID joins and
   all-rank retirement. G1 v2 then passed two distinct sequential requests, each
   with two output tokens, including process calibration reuse. These close
   specific service edges. G1 observed no physical slot reuse and zero cross-step
   next-counter acknowledgements; those edges remain unverified. Native-AR
   comparison, long output, graph/concurrency coverage, tasks and formal timing
   cannot inherit this PASS.
4. **Optimize only the paper-linked computation and independently replay it.**
   GDN replay v2 retained the original Torch P construction and checked fused
   O/U and selected states on 192 captured frames in two layouts (384 frame-layout
   cases). Independent original-bound checks passed; P and post-call inputs were
   checked bitwise. This is numerical qualification of that component, not its
   service integration or a measured speedup.

## Failures that must change preparation

- **Validate hook installation order against the real lifecycle.** Service v5
  loaded weights but its first prefill saw a premature target-head wrapper.
  V6 delayed installation until native prefill capture and independently checked
  actual hybrid-cache geometry. A mock that begins after installation misses
  this boundary. Exercise cold prefill -> install -> use -> restore/retire,
  with duplicate/early install negatives and explicit single ownership. Keep
  controller/environment failures separate from the first worker failure.
- **Treat provenance tooling as executable code, not infallible evidence.**
  GDN timing v1 failed before samples because class-level source reflection could
  not locate the dynamically loaded AscendBackend. The source-qualified repair
  binds the actual compiler methods and their files; an unknown method still
  rejects. Its same-image nine-control pass is not an actual timing result.
  Test the real reflection/loader path, not an ordinary static class fixture.
- **Keep the diagnostic runtime inside its own budget.** The saved-reader
  continuation exposed an unavailable CPU-affinity choice and a whole-file hash
  allocation exceeding its controller cap. Use actual effective cgroup CPU
  membership and bounded streaming hashes; include the reader in aggregate
  host budgets. Do not rerun an expensive NPU producer to fix a CPU-reader seam.
- **Match task inputs to the frozen scorer.** The retained task audit identifies
  a removed GSM answer-format instruction while the original strict scorer
  remained. A new input variant must preserve original token IDs where specified,
  prove the exact intended edit and check the actual tokenizer/template on all
  rows. Never relax the scorer to conceal an input-contract defect. Use the
  latest explicit task scope for new runs; do not silently union superseded task
  lists or claim smoke accuracy as full scoring.

## Reusable regression scenarios

| Trigger | Required action and check | Prohibited promotion |
| --- | --- | --- |
| Saved-reader variable shadowing | Replay original record through the complete repaired consumer; math/source/raw unchanged | Failed parent becomes PASS |
| Native-control precision disagreement | Same inputs, original bitwise replay, independent oracle, explicit boundary variants | Private control represents production dense |
| Two successful sequential requests | Record actual slots, counters, retirements and missing event classes | Sequential requests prove reuse or long decode |
| Dynamic backend reflection failure | Check actual method identity/file hashes; negative unknown method; rerun affected timing gate | No samples means no benefit |
| Device-free reader cannot fit | Repair actual affinity/streaming and joint budget; reuse qualified capture | Needlessly recapture or raise reserves |
| Prompt/scorer mismatch | Freeze new input identity; exact diff and real tokenizer/scorer checks | Rewrite old inputs or loosen scoring |

These checks are future regression requirements, not a claim that new software
or NPU tests were executed during this documentation update. Reuse the existing
[failure-to-action rules](failure-root-cause-and-next-action.md) and
[stage scheduling rules](portfolio-preparation-and-serial-admission.md);
do not create another controller or duplicate global checklist for these cases.
Release a failed device stage after verified own-only cleanup; its device-free
repair must not hold a different ready paper's lease. Verify actual handoff
timestamps before claiming utilization improved.

## Source records and remaining acceptance

All paths below are under
`.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/`:

- `R20_CONSUMER_REPAIR.json`: exact reader edits and unchanged-math identities.
- `NATIVE_AR_FA256_DECISION.json`: original/variant replay and unchanged gates.
- `SERVICE_MODEL_V6_AUDIT.json`: first-request service scope and explicit false
  whole/model/task/performance flags.
- `G1_MODEL_V2_AUDIT.json`: sequential requests and missing reuse/cross-step coverage.
- `GDN_REPLAY_V2_AUDIT.json`: 192 x 2 independent component qualification.
- `GDN_TIMING_V1_FAILURE.json`, `GDN_TIMING_CPU_V2_AUDIT.json`: failure and
  device-free repair, no timing samples.
- `TASK_SCOPE_RECONCILIATION.json`: latest frozen task scope and missing scores.

The ingestion checkpoint records which audit files were read and which raw
identity checks remain unconfirmed. These are recorded experiment results, not
new tensor re-adjudication. No new formal throughput or task-accuracy result is
established here. Required final evidence remains the frozen
matched whole-model performance and task contract; do not substitute kernel
timing, short HTTP output or this maintenance work.

## Historical first failed entry (retained, not the latest state)

The following records the earlier model131repair12 attempt. Later scoped
successes above do not rewrite this failure, and this failure must not be used
to claim that the current implementation has never entered the service.

## BOLE E2E case study: verified outcome and recovery lessons (2026-10-20)

Use this case when a BOLE/native-MTP experiment passes admission but fails at
full-model or independent-consumer validation.

- **Verified successes:** after updating the active authorization in the nested
  host and worker gates (not just the top-level manifest), the exact source
  readset reached 312 entries and source audit passed. The same-image software
  suite reached 136/136 only after the current authorization, command/output
  joins, and worker-window binding were consistent. The bounded Ascend run then
  created the TP4 container, launched four workers on physical cards 4–7,
  produced per-rank native MTP load receipts and reached the actual request and
  independent-consumer stages. These are stage successes, not paper acceptance.
- **Verified failure:** the terminal result for
  `run-bole-model131repair12-MAIN-20261020T123000Z` records
  `model_ready=false`, `candidate_qualification=false`, and the primary fault
  `original component mathematical gates failed` in the independent consumer.
  Preserve the raw metrics/vectors and classify this as a numerical/component
  gate failure; do not relabel it as a successful E2E or a performance result.
- **Nested stale gates matter:** the top-level `contract090.py` and
  `owned_substrate.py` were rebound, but the first software runs still failed
  because `worker_bootstrap.py` retained the old time window. Search all
  transitive launch, worker, controller, consumer, command, and receipt modules
  for old batch IDs/cutoff constants before regenerating the readset. Never infer
  closure from one passing source-audit report alone.
- **Unique output is part of provenance:** reusing an already-created output
  root correctly failed the launch gate. Allocate a new immutable output root
  per attempt and update both the source contract and command manifest; do not
  delete/overwrite a prior result just to make a retry fit.
- **Preserve original assertions:** one retry exposed failures in historical
  identity/inverse-edit tests. The right repair is to ledger the intended
  source delta and separate the newly batch-bound worker gate from genuinely
  immutable algorithm source—not to disable mathematical checks or broadly
  rewrite expected results. The eventual 136/136 pass is only a software gate.
- **Interpret load receipts narrowly:** the observed class was the unmodified
  `Qwen3_5MTP`, with `BOLE=false` and `forward_modified=false`. This confirms
  native MTP loading, not that the BOLE intervention is active. The independent
  consumer must verify actual intervention attribution, numerical/component
  invariants, and the registered model-level evidence before any promotion.
- **Control-plane timeouts are ambiguous:** after an AWMCP timeout, poll the
  original operation and inspect the remote process/container before retrying.
  This run remained alive through worker startup and later reached the
  independent consumer; launching a duplicate during that interval would have
  competed for the same leased cards.

For the next BOLE attempt, begin from the preserved terminal result and the
independent consumer's raw per-component metrics. Make one causal repair,
regenerate source and command refs, rerun the same-image suite, and only then
admit a fresh bounded TP4 run. Keep the successful admission/load/request stages
as stage evidence while the mathematical gate remains failed/pending.
