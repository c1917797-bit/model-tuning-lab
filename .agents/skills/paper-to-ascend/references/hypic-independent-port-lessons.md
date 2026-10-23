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
