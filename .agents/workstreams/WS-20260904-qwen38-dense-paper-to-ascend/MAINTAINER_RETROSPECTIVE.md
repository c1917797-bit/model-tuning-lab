# Maintainer Retrospective

Checkpoint: 2026-09-06T17:36:53Z

## Outcome

The HYPIC historical-ruler reproduction completed on Qwen3.6-27B TP4:

- 18/18 planned units accepted by an independent fail-closed audit;
- TTFT -43.6345%, TPOT -18.9911%, output throughput +36.0663%,
  duration -26.6028%;
- LongBench-v2 -0.2625pp and GSM8K -0.1516pp, both inside measured
  baseline three-run ranges;
- strict HYPIC treatment hot-path evidence passed;
- both experiment containers exited without OOM and port 8224 was released.

Decision: adopt HYPIC for this exact frozen workload with quality monitoring.
Do not generalize this to universal losslessness, another cache denominator,
model, topology or traffic shape.

The employee practice was useful because it supplied a concrete workload,
algorithm configuration, datasets and expected effect direction. It was not a
drop-in result: the current model changed from Qwen3.5-27B to Qwen3.6-27B,
the hardware from 2×910C to 4×910B4, and TP2 to TP4. Those changes required a
fresh baseline and a scoped reproduction claim.

## Evidence ledger

| Evidence | State |
|---|---|
| controller | `exec-00000000000009ab`, exit 0 |
| accepted units | 18/18 |
| aggregate | `historical-reproduction-summary.json`, SHA256 `741a5ad225682452062143f776af81949961d11ecf946b4da64ade3a118f935e` |
| report | `HISTORICAL_REPRODUCTION_REPORT.md`, SHA256 `f30ac5decb07145f78ee41a038874aaf3c059423f16ed73df0ea617fcd5fcb79` |
| independent audit | `historical-reproduction-evidence-audit.json`, `ok=true`, zero errors |
| hot path | treatment performance run1: verified, no missing events/failures |
| resources | both exact containers exited; port 8224 released |

Artifact root:
`/cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906`.

Formal experiment/evidence/decision records have the suffix
`hypic-formal-npu4-7-tp4-b40960`.

## What worked

### One-switch, same-denominator A/B

Both arms disabled native prefix caching and shared the same checkpoint, image,
topology, scheduling budget, traffic, datasets and evaluator. Only
`VLLM_ASCEND_HYPIC_ENABLE` changed. This made the measured gain attributable
to HYPIC rather than to ordinary prefix caching or a different capacity limit.

### Topology as experiment identity

Host NPU IDs and container-visible IDs were recorded separately. The current
TP4 case received a fresh artifact root instead of reusing a TP2 or earlier TP4
baseline. That prevented cross-topology pooling.

### Admission arithmetic before measurement

The private suffix contained 16384 tokens and the seam sink consumed 8 more.
A physical admission budget of 16384 was therefore invalid; the minimum was
16392. The corrected case used 40960 in both arms and started a new evidence
ledger.

### Activation proof plus outcome proof

Good latency alone was insufficient. Treatment run1 also had to show the
materialization, scheduling, grouped replay, repair, native-decode isolation
and worker hot-path events with no missing gate or evidence failure.

### Repeated quality and measured noise

Three baseline and three treatment repetitions were retained for each dataset.
The final quality interpretation compared mean deltas with the actual baseline
run ranges. This supports "no material regression observed" without inventing a
generic tolerance or claiming exact equality.

### Durable resumability

Quality rows were written per sample with index, success state and response
hash. After service loss, the evaluator kept accepted rows and retried only
indexes without `ok=true`. Completed units were hash-validated and skipped by
the controller on resume.

### Independent completion audit

The final audit did not trust file presence. It verified:

- six performance artifacts, 40/40 success and fixed 1024-token output;
- twelve quality summaries and JSONLs;
- exact row counts and complete unique index sets;
- zero failed rows and correct-count agreement;
- unique canonical response hashes;
- summary-to-details and aggregate-to-summary hashes;
- stable dataset and evaluator identities;
- strict treatment hot-path evidence.

## What failed and why

| Failure | Root cause | Correct response |
|---|---|---|
| initial device preflight | host IDs were reused inside a container remapped to local IDs | archive the pre-measurement failure; use explicit host/container maps |
| 16384-budget treatment | suffix plus seam exceeded admission capacity | reject the case; create a new 40960-budget experiment and baseline |
| baseline GSM8K interruption | serving endpoint disappeared after 923 accepted rows | keep valid rows; retry missing indexes only; do not average a partial run |
| incomplete renderer crash | report code assumed an absent GSM8K aggregate existed | make incomplete rendering conditional; self-test before resuming accelerator work |
| first resumed treatment instance exited | service lifecycle failure before measurement, no OOM | restart the exact configuration; preserve already accepted units |
| first independent audit run failed | audit helper used `with_suffix` and erased `.runN` | keep fail-closed behavior, fix the auditor, rerun to zero errors |

None of these operational/tooling failures was relabeled as an algorithm
regression. Conversely, none was ignored: every failed attempt either remained
rejected evidence or was repaired and independently revalidated.

## Profiling boundary

The employee ruler asked whether serving performance and accuracy improved.
The completed formal decision therefore uses benchmark metrics, quality scores
and strict runtime activation events.

Native msprof evidence already exists for the separate PDC-only versus
PDC+HYPIC coexistence question. That experiment rejected coexistence adoption.
Its profile artifacts remain useful diagnostic evidence but must not be pooled
with this no-cache/HYPIC-only A/B.

For a future paper whose mechanism claim depends on a kernel, communication or
memory effect, profiling must be part of the frozen contract and performed on
both baseline and the unique candidate with identical stimulus.

## Reusable maintainer rules

1. Translate a paper claim into a falsifiable mechanism, outcome metrics and
   explicit failure explanations before reserving accelerators.
2. Freeze all invariants and declare the one treatment switch.
3. Include hardware generation, card count, TP degree, cache denominator and
   capacity budgets in the experiment identity.
4. Resolve host/container device mapping and CPU/port ownership in a read-only
   preflight; never infer ownership from container-local device numbers.
5. Keep performance and quality lifecycles separate. Fixed-output performance
   sampling and EOS-respecting deterministic quality sampling are different
   contracts.
6. Require multiple repetitions and report dispersion, not only means.
7. Require mechanism activation evidence; otherwise a favorable delta is only
   correlation.
8. Persist raw per-request/per-sample artifacts and bind them with SHA256.
9. Resume by verified unit and sample identity; never restart a still-live
   authoritative controller.
10. Keep separate decisions for feasibility, coexistence, historical
    reproduction and adoption.
11. Complete only after an independent fail-closed audit and resource release.
12. State allowed and forbidden claims explicitly.

These rules are materialized in
`.agents/skills/paper-to-ascend-reproduction/SKILL.md`; detailed evidence
contracts live under that skill's `references/` directory.

## Decision boundary

Allowed:

- the employee performance direction and approximate magnitude reproduced on
  Qwen3.6-27B TP4;
- the observed quality changes were within measured baseline repeat ranges;
- HYPIC is adoptable for the frozen workload with quality monitoring.

Forbidden:

- identical absolute results across Qwen3.5/3.6, 910C/910B4 or TP2/TP4;
- universal losslessness;
- pooling the rejected 16384-budget case;
- pooling the separate PDC-coexistence profile;
- treating CEval or an invented NIAH+ substitute as executed evidence.

## Next maintainer action

Review the final decision and skill commit. For another paper or model, create
a new experiment ID, fresh artifact root and fresh baseline, then instantiate
the reusable skill rather than copying the machine-specific values above.
