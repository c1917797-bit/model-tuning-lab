# Independent HYPIC port: reusable success and failure lessons

Read for stateful PIC/C1/C2 ports, scheduler-boundary regressions, interrupted
quality runs, or claims that mechanism activation implies paper reproduction.
Evidence snapshot: work/hypic-independent-20261013 at
`d54357c71a5e0c37f8fd6c88e177b541dd47f310` (2026-10-17).
The later lesson ingestion does not create new device evidence.

## Scope and evidence boundaries

This campaign independently implemented C1/C2 on 27B, Ascend 910B, single TP4.
The user excluded distributed C3/dual instances and permitted learning the
earlier experiment's ideas/protocol, not copying its algorithm/operator/runner/
scheduler code. Those are this task's choices, not universal Skill restrictions.
Likewise 48 C1 / 16 C2 layers, four ranks, output caps and tolerances below are
historical facts, not mandatory values for other models.

The paper-method ledger must retain omissions/adaptations. Success under this
scope cannot be labelled all distributed HYPIC capabilities or deployment.

## What worked, what failed, what remains

| Evidence | Supported conclusion | Unsupported conclusion |
| --- | --- | --- |
| R22 first-batch Canary: 17 private responses, 17 unscored producers, all 17 joined across four ranks with 48 C1 / 16 C2, eviction/new generation/rebuild, 1,728 C1 shadows passed | Bounded integrated mechanism, source, isolation and exact owned release passed | Full 381-response quality, all scheduler geometries, service speed or lifecycle |
| R21 valid G1/G3 first pair: TPOT 280.611652 -> 303.993810 ms; TTFT P95 340898.009290 -> 390713.633260 ms | Whole-service regression: +8.332568% TPOT, +14.613058% TTFT P95 | Optimization success, three repeated pairs, or impossibility of the paper |
| R21 full-quality worker C1 shadow failure before actual slot commit; zero valid scored outputs | Executed implementation path failed; retain same-input numerical evidence | A valid task-accuracy drop or root cause inferred from later connection-refused errors |
| R22 full quality interrupted at frozen deadline: 215 attempts, 207 request successes; 121 stop, 86 length, eight cutoff failures | Partial transport/finish evidence; independent source/isolation/release audit passed | Complete 381, natural EOS for every response, paired accuracy or algorithm rejection |
| R23 strict journal recovery: 11 focused host tests; old journal recovers 215/207, original error retained | Host-side evidence-retention repair | Frozen service integration, NPU validation or recovered full quality |

R22's observed short suffix was 36 rows. The previous 56-row suffix was inferred,
not captured; passing the former does not prove exact reproduction of the latter.
The numerical thresholds in this case were unchanged, not relaxed for a pass.

## Change future decisions

1. **Choose the right oracle.** Compare same-semantics RoPE/state/convolution
   operations with independent numerical references. PIC changes attention
   context and may be approximate: do not demand native full-context tensor or
   generated-token equality by default. Approximation does not excuse NaNs,
   bad slots, incorrect composition or task regression. Freeze task scoring and
   acceptable deltas independently; answer EM and output-token equality differ.
2. **Target observed failure geometry.** Select actual packed first-batch,
   short-tail and eviction/rebuild cases, not repeated easy serial examples.
   Join actual hot events to request, step, layer, rank and material generation.
   Installation and native fallback are not algorithm activation. Cold requests
   stay in functional counts; eligibility for hot claims is predeclared.
3. **Measure the whole service.** Saved rows and locally faster operations may
   be outweighed by synchronization, material transfer, metadata or fallback.
   Use the matched first screen to choose one attributable repair. Do not
   expand an unchanged negative treatment merely to fill a matrix.
4. **Keep quality and speed independent.** An authorized quality study can
   continue after negative speed. Positive speed cannot overturn quality
   failure; quality success cannot establish acceleration. Final delivery needs
   both and executed rollback.
5. **Make interruption a tested path.** The old controller assigned
   `responses` only after the whole workload returned. Its interrupted summary
   was empty despite durable per-response events. Persist incrementally, test
   the real finally path, and recover only strict identity-checked records.
   Never rewrite the old root or change failed/partial status to valid.
6. **Budget real work.** Include public producers, initialization and audits,
   not just scored requests. Report attempts, completed requests, scored
   samples and correctness separately. A natural-stopping cap still permits
   length truncation; retain it under the original scoring policy.
7. **Treat ownership and reachability as separate facts.** Refresh direct
   route/host identity, inspect physical PIDs with container/cgroup/namespace
   evidence, and release only the exact owned container. Passive mappings do
   not prove use; old idle snapshots do not reserve cards. A control-plane
   timeout is not permission to relaunch.
8. **Do not turn an audit transient into model work.** In the recorded R22
   release audits, initial strict port binds failed; unchanged read-only audit
   replays later passed. Inspect exact owned state and TCP evidence, then
   replay the audit if justified. Do not relax the port gate or rerun the model.

## Source ledger and replay

All filenames below are under
`.agents/workstreams/hypic-independent-20261013/` at the evidence checkpoint.
Retrieve historical bytes from Git; raw datasets/responses/traces remain outside
Git, with hashes and locations in the reports/contracts.

- `R22_FIRSTBATCH_CANARY_R1_TERMINAL_20261017.json`: bounded success,
  controller 1178 / independent audit 1199.
- `R21_FIRST_PAIR_DECISION_20261017.json`: valid negative service pair,
  controls 1101/1126 and candidate 10cc/10fc.
- `R21_FULL_HYPIC_R1_FAILURE_20261017.json`: worker failure, 114e/115a.
- `R22_FULL_HYPIC_R1_DEADLINE_TERMINAL_20261017.json`: cutoff, 119b/11f3.
- `R23_PARTIAL_RESPONSE_HOST_READINESS_20261017.json`: host-only repair,
  tests 11f8 and static check 11f9.

The ingestion eval `hypic-independent-lessons-20261023.yaml` tests decision
boundaries, not a claim that all 29 Skills function. Its replay checks historical
raw hashes and report arithmetic without allocating NPUs. Revalidate source,
environment and authority before any later device phase.

## 2026-10-25 addendum: explain why, then choose the next small experiment

This adds decision evidence to the historical snapshot above. Read the
[source-bound decision ledger](../../../workstreams/hypic-independent-20261013/HYPIC_REUSE_DECISIONS_R25_R27_20261025.json)
for exact commits, files, hashes, line ranges and the remaining uncertainty.
It is curated learning, not a new raw experiment or a completed reproduction.

### Outcomes established by the current evidence

- **R25 is a useful negative result.** Both eager G1/G3 arms completed 40 fixed-
  output requests and independent audits; G3 had 40/40 same-step four-rank 48/16
  body-skip coverage. Weighted TPOT nevertheless rose 280.067788 to 319.769327 ms
  (+14.175689%), and TTFT P95 rose 22.075207%. This shows that real mechanism
  activation did not yield service acceleration for that variant. It does not
  show the paper is impossible, nor justify filling the unchanged 12-cell matrix.
- **R27 G1 resolves only native graph feasibility.** The bounded native control
  completed three requests, 199 clean isolation observations and live release.
  Four ranks logged native FULL capture; the local-first rank directly logged
  replay. It does not establish the HYPIC counterpart, graph speed or full task
  quality. Keep a later graph pair separate from R25 eager timings.
- **R27 G3 isolates a startup ordering failure.** It served zero HTTP requests;
  independent source/isolation/release checks passed with 370 clean observations.
  Native G1 finished compilation at 09:29:36 before capture at 09:30:07. G3
  began capture at 09:45:19, first compiled the installed forward inside it,
  then failed at 09:45:38: `npugraph_ex_compile -> set_compile_mode ->
  npu_config.synchronize -> 107027 (stream is captured)`. The direct cause is
  established. Whether applying `skip_compiled=True` to every NONE call also
  suppressed a genuine compiler warmup remains the upstream hypothesis.
  The next small test should route only source-proven non-request warmups
  through native compilation, retaining actual PIC prefill/snapshot/lease gates.
  This is not a validated repair, a task-quality result or an explanation of
  the whole R25 eager regression.
- **Read the evidence producer before inventing a gate.** In this pinned vLLM,
  `info_once` defaults to local-first logging. Requiring a replay line from
  every worker would reject a valid run because of logger suppression. This
  lesson is to derive observability from source, not to require this logger,
  rank count or a graph experiment for every paper.

### Source capability is not measured causality

The original successful source was read from Git commit `3ad0967`, separately
from that checkout's `4429e35` HEAD. No reference algorithm code was executed,
copied, imported or mounted.

| Source observation | What it does and does not explain |
| --- | --- |
| Original C1 supports budget/watermark-dependent NPU residency and shared staged materials; the current pool uses CPU canonical data/private copies and device transfers | A plausible cost difference. Actual old residency/hit rates and attributed time are unknown. Current C1 already packs waves, shares WY, and acquires once per unique body/layer/wave; do not falsely call it repeated per-request T/S upload. |
| Original C2 groups placements by segment/anchor; current C2 acquires, relocates and writes per selected plan | A candidate batching opportunity, not evidence that copying the implementation is needed or that it caused 14% regression. |
| Original evidence emitter append/write/closes; current emitter also fsyncs each event | A durability/overhead policy difference. Its service cost has not been isolated; do not remove evidence durability to manufacture a win. |
| Current 27B RoPE geometry fits its config; FP32 newly computed sin/cos differs from the official BF16-cache path | Parameter agreement is not finite-precision identity, a numerical defect, or proof of lossless task quality. |

### Reuse the decision, not all of this campaign's machinery

For a later paper, keep four short fields: **proved**, **hypothesis**,
**environmental blocker**, and **next minimum falsification**. Select the first
missing causal link rather than repeatedly exercising a passed component.

Here the next graph question is the already-authorized bounded HYPIC counterpart,
then one fresh matched graph pair if it passes. Residency/C2 batching/I/O claims
need a bounded attribution measurement before choosing one repair. A RoPE
rounding hypothesis needs same-input primitive evidence and then the frozen
paired task-quality evaluation; PIC/native full-context token equality is not
the default approximation oracle.

A resource admission failure is separate again: R24 OFF R1 encountered an
external task before creating a container or request. That was environmental
blocking, not an HYPIC result and not proof of today's occupancy. Concrete
devices, ports, verification transport, output caps and deadlines remain in the
case record, not universal requirements for the next paper.

### Preserve the learning's own provenance

The Skill entrypoint remains unchanged. Before this addition, the 2026-10-16
case's frozen document replay already failed its older Skill-source pin
(operation 160d); this reference append does not repair or conceal that failure.
The separate [source-pin successor case](../../../workstreams/hypic-independent-20261013/PAPER_TO_ASCEND_INDEPENDENT_HYPIC_CASE_20261025_LESSONS_PIN.json)
uses current Skill sources while preserving the old case and its historical
partial scope. Replay it with `python3 -B validate_independent_hypic_case.py
--case PAPER_TO_ASCEND_INDEPENDENT_HYPIC_CASE_20261025_LESSONS_PIN.json
--document-only` from that workstream. This checks document bindings only.
Historical replay, a new reference, or bounded graph evidence does not certify
the full Paper-to-Ascend workflow or all 29 Skills.
