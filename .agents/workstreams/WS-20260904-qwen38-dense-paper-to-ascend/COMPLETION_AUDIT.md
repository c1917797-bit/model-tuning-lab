# Completion Audit — WS-20260904-qwen38-dense-paper-to-ascend

This audit distinguishes reusable tooling from real experiment completion. A
passing fixture proves control flow only; it does not prove performance,
accuracy, runtime activation, or adoption.

## Active no-cache versus Hypic-only historical reproduction

Status: complete on the superseding corrected-budget NPU4-7 TP4 experiment.

All 18 planned units passed the independent raw-artifact audit. Against the
fresh no-cache baseline, HYPIC changed mean TTFT by -43.6345%, TPOT by
-18.9911%, output throughput by +36.0663% and duration by -26.6028%.
LongBench-v2 changed by -0.2625pp and GSM8K by -0.1516pp; both deltas are
inside the corresponding observed baseline three-run ranges. Treatment run1
passed the strict HYPIC hot-path gate with no missing events or evidence
failures.

The employee performance direction and approximate magnitude reproduced on
Qwen3.6-27B TP4. Absolute-value equality with Qwen3.5-27B TP2 is outside scope,
and the quality evidence authorizes only "no material regression observed",
not universal losslessness.

Authoritative records use the suffix
`hypic-formal-npu4-7-tp4-b40960`. The output root is
`/cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906`.
The final audit has `ok=true`, `accepted_units=18`, and `errors=[]`.
Both exact experiment containers are exited without OOM and port 8224 is
released.

## Independent Hypic v0.8.5 piercing addendum

Status: formal performance, both active semantic canaries, all available
baseline/treatment quality, both native profiles and the strict final evidence
audit are complete. Adoption is rejected for the current configuration.

Completed: Qwen3.6-27B TP4 served on host NPU0-3 with exact image, source and
configuration identity. PDC-only and PDC+Hypic each completed the formal
32768-input/1024-output, 40-request, concurrency-16 performance arm. Treatment
improved mean TTFT by 16.8893%, throughput by 1.0473% and duration by 1.0365%;
weighted TPOT was effectively flat. Runtime evidence proves the C1/C2 hot path
activated without materialization failure. The identical 32768-token active
relocation canary passed on both arms with matching prompt, public-segment and
response hashes. Baseline LongBench-v2 and GSM8K each completed three
zero-failure repetitions. Treatment LongBench-v2 completed three zero-failure
repetitions with a +0.524934pp mean delta that is within measured baseline
variation. Treatment GSM8K completed three 1319/1319 zero-failure runs at
96.360879%, 96.057619% and 95.830174%; mean 96.082891%, -0.176902pp
versus baseline and within its repeated-run range. The run3 matching delta was
-0.682335pp, so this does not authorize an accuracy-lossless claim. The baseline rank0
native profile completed with profiler/workload exit code zero and 228 non-empty
files totaling 175150491 bytes. The treatment rank0 profiler exited zero,
captured 4/4 successful fixed-output requests and preserved 234 non-empty files
totaling 184536157 bytes. Its raw benchmark exit remains 1 because algorithm
coexistence acceptance is false; the independent capture gate does not
reinterpret that failure. The final non-volatile evidence audit checked 37
inventory files plus every baseline/treatment profile payload with zero errors.

Failed/blocked gates: full coexistence is false; the treatment profile traffic
also lacks `position_independent_hot_path`,
`mixed_batch_native_decode_isolation`, `mixed_decode_latency_protection` and
`mixed_decode_grouped_reclaim`. Authoritative NIAH+ files are missing and
paper C3 distributed scatter/transfer is not present. CEval is intentionally
excluded by operator decision. See
`experiment-hypic-qwen36.json`,
`evidence-hypic-qwen36.json` and `decision-hypic-qwen36.json`.

Historical comparison boundary: the supplied prior result is a real
Qwen3.5-27B/TP2/Hypic-only versus no-prefix-cache test. The current experiment
is Qwen3.6-27B/TP4/PDC+Hypic versus PDC-only. Compare relative deltas only.

## Step 1 — fixed ruler

Status: incomplete.

Proved: the contract fixes NIAH+, LongBench v2, GSM8K and CEval; it enforces
three unique repetitions, mean/std, five performance metrics, quality A/B/C
evidence and immutable input/config hashes. GSM8K data exists locally.

Missing: materialized and hashed NIAH+, exact LongBench v2 and CEval; the
employee-success prompt/scorer/split configuration; resolved request rate,
warmup/cold exclusion, concurrency and dataset batch/few-shot values; and a
successful production freeze report.

Acceptance: valid resource intake, resolved `runtime-config.json`, and a
frozen-input report whose four dataset hashes match every production result.

## Step 2 — G1 baseline

Status: incomplete.

A historical real-weight service/profile was observed, and G1 switch/lifecycle
semantics are verified offline. Those measurements did not use the frozen
four-dataset ruler and cannot be the final denominator. NPU0-3 is occupied and
replacement is not authorized.

Acceptance: three warm performance and quality rows for every model/dataset
cell plus G1 profiles, all bound to one ruler and stable checkpoint/service
identities.

## Step 3 — G1-G4 ablation

Status: contract complete; real execution incomplete.

Proved: G1=no native/no DRRQR, G2=native only, G3=DRRQR only, G4=both; two model
inventories and the native patch are hash-verified; lifecycle dry-run, cleanup
and exact-prefix resume passed without executing a workload.

Missing: true DRRQR checkpoints/manifests for both models, proof that the native
operator activates instead of falling back, a ready fresh preflight, a complete
lifecycle journal and production rows.

## Step 4 — two-model generalization

Status: model selection complete; experimental evidence incomplete.

Qwen3.8-27B and Qwen3.5-4B are verified same-family GDN models of different
sizes. Acceptance requires complete performance, quality and winning-candidate
profile coverage for both under one ruler.

## Step 5 — accuracy-lossless gate

Status: implementation complete; production evidence absent.

Conditions A/B/C are enforced per model/dataset/treatment. B derives its
threshold from hash-bound three-run G1 observations. C requires exactly 512
output tokens and canonical output hashes. Production evidence cannot mix
rulers, checkpoints, services or canary inputs.

Acceptance: a passing production quality report covering both models, all four
datasets and every treatment versus G1. Until then no accuracy-lossless claim is
allowed.

## Step 6 — decision

Status: renderer complete; authoritative decision is `iterate`.

Adoption requires one unique winner across all five metrics, no below-threshold
model/dataset/metric cell, matching performance/quality scope and bindings, and
a verified G1-versus-winner profile on both models with capture disabled and
lower target-region time.

Acceptance: production `decision.json` with `decision=adopt`, no blockers,
one recommended group, a scoped quality claim and embedded profile verification.

## Step 7 — reusable assets

Status: substantially complete, pending real-run validation.

Available: ruler/treatment/resource/preflight/profile verifiers; lifecycle
verifier and dry-run-default resumable executor; summarizer, noise builder,
quality gate and decision renderer; configuration/evidence templates; runbook,
troubleshooting, resource request and handoff commands. The Hypic addendum also
has a fail-closed evidence verifier that checks inventory hashes, quality
JSONL/summary counters, canary rulers and every native-profile payload. Its live
mode passes with only the explicitly volatile treatment runtime-event sink
excepted; final strict verification remains pending producer shutdown.

Still required: populate them with received resources, run them end to end on
the authorized NPU0-3 lane, and preserve completed production artifacts.

## Safety and current verdict

- Never operate host NPU4-7 or CPU0-95.
- Never replace/stop the NPU0-3 baseline without exact ownership authorization.
- Re-resolve topology and rerun read-only preflight before execution.
- Do not invent Git identity, commit, or push.
- Workstream records are staged; the experimental `gdn.py` hook is unstaged.

Not complete: Steps 1-6 lack real frozen-suite production evidence. The next
state-changing input is the requested benchmark/data/DRRQR resource bundle; NPU
execution separately requires explicit NPU0-3 ownership authorization.
