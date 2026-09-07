# Maintainer Retrospective

Checkpoint: 2026-09-07T06:46:28Z

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

## State-reduction / DRRQR completed retrospective

### Scientific outcome

The paper *The Key to State Reduction in Linear Attention: A Rank-based
Perspective* (arXiv 2602.04852v2) was evaluated with the official
Strong-RRQR implementation at commit
`919d8667d951c385e08510bc1267c2e7049a4f56`. This was an explicitly scoped
Ascend adaptation, not a paper-exact reproduction: FineWeb-Edu was unavailable,
so calibration used the first 16 source-ordered LongBench-v2 rows, frozen to
2048 tokens and bound to SHA256
`d146eede2a438154ea8c1bf9785dffa12f8a81e56fa370ff48be4d924e908111`.

The mechanism is feasible on Qwen3.6-27B TP4 and Ascend 910B4:

- the capture audit accepted exactly 3072 files = 48 linear-attention layers x
  four TP ranks x 16 calibration samples;
- the layer set was derived from `text_config.layer_types`, not incorrectly
  assumed to be contiguous 0-47;
- independent Dk64 (50% pruning) and Dk96 (25% pruning) checkpoints passed
  structural audits;
- real-weight Ascend smoke tests exercised `head_k_dim=64` and
  `head_k_dim=96`.

Neither operating point is adoptable for the frozen workload. Baseline GSM8K
was 96.310336% with a measured three-run range of 0.151630 pp. Dk64 was
96.108163% (-0.202173 pp) and Dk96 was 96.007076% (-0.303260 pp), so both
failed the preregistered quality gate. LongBench-v2 passed for both candidates,
but one dataset cannot override a failed critical dataset.

Performance did not rescue either candidate. Dk64 means changed TTFT -2.717%,
TPOT -2.620%, throughput +2.711% and duration -2.600%. Dk96 means changed
TTFT -0.401%, TPOT -0.443%, throughput +0.381% and duration -0.327%. Every
baseline/treatment three-run interval overlapped. These are favorable mean
directions, not repeat-separated stable serving gains.

Decision: **reject Dk64 and Dk96 for this frozen workload**. It is valid to
claim source verification and mechanism feasibility. It is not valid to claim
paper-exact reproduction, losslessness, stable Ascend serving acceleration or
adoption. The paper's H100 training sequence-mixer result is a different
denominator and must not be pooled with this full-model serving experiment.

### What worked

1. Source identity, calibration identity, model, image, topology, prompts,
   evaluator, traffic and repetitions were frozen before treatment comparison.
2. Capture was bounded behind a readiness sentinel and disabled during A/B.
3. The full layer x rank x sample Cartesian product was audited before
   conversion.
4. The baseline checkpoint remained unchanged; candidate shards were
   independently materialized and shape-audited.
5. Real-weight smoke and runtime dimension evidence preceded expensive A/B.
6. Baseline, Dk64 and Dk96 each retained three complete 40/40 fixed-output
   performance repetitions.
7. Every quality run retained per-sample JSONL, exact unique indexes, zero
   failures and matching summary/detail hashes.
8. A milder fallback remained a separate treatment and did not overwrite the
   negative Dk64 result.
9. The preregistered gate prevented unnecessary native profiling after quality
   failure.
10. The final fail-closed audit verified nine performance runs, 18 quality
    summary/detail pairs, artifact hashes and resource release.

### Failures kept as evidence

Sixteen rejected attempts remain in
`experiment-failures-state-reduction-qwen36.json`. They are classified
separately from scientific outcome:

- launcher authoring, quoting and path errors occurred before measurement;
- offline package resolution and a source-image ABI mismatch were environment
  integration failures;
- assuming contiguous linear-attention layer IDs was a model-structure defect;
- remote-executor cwd/command-shape mistakes affected only read-only checks;
- summary field, timestamp, quoting and incomplete-state defects were
  post-processing failures and did not mutate accepted raw artifacts;
- the final handoff validator initially selected a nonexistent JSON key; the
  failed read-only check was logged, corrected against the actual schema and
  rerun without touching experiment evidence.

The correct maintainer response was to record whether measurement or an NPU
workload had started, preserve the failed attempt, repair the narrow cause, and
revalidate the accepted attempt. None of these was relabeled as an algorithm
failure. Conversely, successful loading was not relabeled as benefit.

### Evidence and resource boundary

Artifact root:
`/cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906`.

- summary SHA256:
  `7f6ebb0e3fb667b173f9eacd8e4c31fcd3db0f829bab45adeabc0c5a39a9ed5e`;
- report SHA256:
  `0915a8b4fb3f9fb3333665d313e5bdd57bb08a2b9e75095a8525bbca2fc4dc91`;
- final-audit SHA256:
  `6e9990a64d4bd2d311e88553a845fcfec070c8c2407c9d1230b144fa6e47ede1`.

The final audit reports no errors. The experiment-owned Dk96 container exited
0 with `OOMKilled=false`; host NPU4-7 had no process and port 8225 was free.
NPU0-3 contained an external Qwen3.5 workload and was not inspected or altered.
This record grants no authority to touch NPU0-3.

Profiling is intentionally absent, not forgotten. The frozen protocol required
all quality gates to pass before native profiling. Running the profile now
under the same experiment identity would violate the preregistration.

### Exact audit and recovery

Read-only current-state check:

```bash
cat /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/controller-status.json
```

The authoritative quality operation `exec-0000000000000c1b` is terminal and
successful, so there is no experiment resume command. To regenerate derived
summary/report files and rerun their built-in independent audit:

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/summarize_state_reduction_formal.py \
  --root /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906
```

Expected: exit 0; summary `status=complete`, `errors=[]`; final audit
`ok=true`; nine performance runs and 18 quality summary/detail files.

Do not run `state_reduction_native_profile.py` for this completed identity.
LoRA recovery, a different calibration corpus, or another pruning ratio
(including a new approximately 20% point) is a new scientific question and
requires a new experiment ID, artifact root and fresh same-denominator
baseline.

### Promotion decision

The repeated, decision-changing lessons are promoted into
`knowledge-proposals.json`: derive hybrid layer sets from model config, name
calibration substitutions, gate profiling after quality, and preserve negative
operating points. Machine-specific quoting/path incidents remain only in the
failure ledger and this retrospective.

## Next maintainer action

### 2026-09-07 quality-first DRRQR continuation

The Dk64/Dk96 rejection remains immutable. The operator asked to pursue a
precision-preserving performance point, so a new experiment was preregistered:
`state-reduction-qwen36-dk112-quality-first-20260907`. Its Dk112 candidate
removes 16 of 128 Q/K channels per head (12.5%), retaining a 16-channel-aligned
dimension. This is deliberately more conservative than the rejected Dk96
25% candidate.

The continuation changes two process choices, not the historical evidence:

1. use a fresh baseline and artifact root rather than reinterpreting the old
   ruler;
2. run repeated quality before performance/profiling because quality was the
   prior decision-limiting gate.

Checkpoint construction reuses the already hashed 3072 activation captures
and exact Strong RRQR source so pruning ratio is the sole algorithm change.
The reused calibration remains an explicitly disclosed LongBench-v2 adaptation,
not paper-original FineWeb-Edu; it is also an evaluation-family leakage risk
and therefore cannot support a general losslessness claim.

At this update, CPU/storage-only build operation
`exec-0000000000000cb7` is authoritative and running. No NPU measurement has
started. Exact recovery, resource limits and claim boundaries are at the top
of `HANDOFF.md`. Candidate lessons are isolated in
`knowledge-proposals-state-reduction-qwen36-dk112-20260907.json` and must not
be promoted until repeated evidence changes a decision.

Review the two independent decisions: HYPIC is adopted only for its exact
frozen workload, while DRRQR Dk64/Dk96 are rejected for theirs. For another
paper, model, calibration corpus, recovery method or pruning ratio, create a
new experiment ID, fresh artifact root and fresh baseline, then instantiate
the reusable skill rather than copying machine-specific values above.
