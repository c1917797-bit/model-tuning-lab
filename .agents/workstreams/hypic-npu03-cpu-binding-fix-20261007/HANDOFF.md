# HYPIC NPU0–3 — current handoff

## 2026-10-12 r23 disabled AUDITED; enabled RUNNING

Disabled controller exec-0000000000000ccd finished exit0 after 611.6 seconds.
All four responses persisted (two warmups, one max2048 target, one post request).
Independent auditor exec-0000000000000cdb passed: source/image, physical0-3,
framework-rank/PID/namespace inventory, 114 clean isolation probes, zero capture
files in disabled mode, exact container removal and port release.
Audit: /cache/cch/hypic-npu03-cpu-binding-fix-20261007/r23-state-disabled-independent-audit.json
SHA256 38f25f63e7d0e114c23bc9c8229f189e047d8a440097c4292a07e04403d46bab.
This is diagnostic-wrapper control evidence, not full quality or paper success.

After a fresh chicaihong01/ma direct-route resolution, enabled controller
exec-0000000000000cdc started with the same frozen code/contract and was polled
RUNNING. Its own admission checks physical0-3/8223 and exclusive fresh root.
Raw root: /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r23-state-enabled
Exact owned container: hypic_npu03_bindingfix_quality_hypic_only_20261007_hotpath-cache10r23-state-enabled
Do not restart on observation timeout. Poll same handle/raw root; after terminal,
inspect terminal.json and run r23_state_audit.py --mode enabled with shared py311.
If capture/activation fails, preserve exact failure phase and do not rerun the
same bytes. Do not modify frozen support files while this service is active.
r19/r22 judgments remain unchanged. No remote/main synchronization is claimed.

## 2026-10-12 r23 disabled controller RUNNING

Started exact operation exec-0000000000000ccd asynchronously (7200s timeout).
Operation poll confirmed RUNNING, not terminal. Owning code checkpoint f40e5897.
Raw root: /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r23-state-disabled
Exact owned container: hypic_npu03_bindingfix_quality_hypic_only_20261007_hotpath-cache10r23-state-disabled
The controller performs fresh physical0-3/8223 admission and continuous guard.
Startup log at exec0cce shows pinned HYPIC v0.8.5 plugin installation complete;
service health, requests, disabled proof and release are NOT yet established.
Do not restart on slowness, lost observation or heartbeat. Poll same operation
and inspect this root. On terminal inspect terminal.json then run independent
r23_state_audit.py --mode disabled with shared py311. Enabled mode is NOT started;
admit it only after disabled audit passes and fresh route/lane/port checks.

## 2026-10-12 r23 bounded integrated diagnostic frozen

r23_state_diagnostic.py reuses the unchanged guarded quality service and pinned
4429e3 HYPIC source. Only sample59 (20414 prompt tokens, boundary16384) is used:
two 1-token warmups, one natural-EOS max2048 target, one 1-token post-uninstall
request. First disabled observer, independent audit, then enabled observer.
This tests observer integration and sampled residuals, NOT full quality or speed.
r23_state_preregistration.json SHA256:
b1197dfe932a656c083feea7fa15d40c7c9ce08c581c4ac84c7b30deec0320e5.
Two new roots are quality-context-41984-hotpath-cache10r23-state-disabled/enabled
under the existing external raw base. Never resume or reuse either root.
The new independent auditor binds source, Docker physical device declarations,
physical host/namespace PID map, framework Worker_TP rank logs, continuous guard,
exact release, four sealed snapshots and same-step hot receipts.
48 host tests passed exec0cca; both no-device preflights exec0cc9, structure/static
checks exec0ccb passed. Live capture remains unproven. Next run disabled only;
run r23_state_audit.py --mode disabled with shared py311 after terminal success;
only then admit enabled after fresh physical0-3/8223 checks.

## 2026-10-12 pinned-image request-identity correction (CPU only)

Pinned-image inspection (exec0cb7/0cb9/0cba, no network, no devices,
read-only owned --rm containers) verified vllm 0.23.0+empty,
vllm-ascend 0.23.0, torch 2.10.0+cpu and torch-npu 2.10.0.post4.
TP get_tp_group().world_size/rank_in_group exists in the actual image.

Found an integration defect in the new observer, NOT a demonstrated HYPIC
quality cause: it required a pre-known exact internal request ID, but vLLM
appends eight random hex characters to the external chat ID. The bounded
diagnostic must send an explicit unique body request_id without an overriding
X-Request-Id header, n=1 and one prompt, configure request_id as chatcmpl- plus
that value, and independently verify the response ID. Randomization stays ON.
Observer now matches only the exact external ID plus the eight-hex suffix,
binds once, rejects ambiguity/rebinding, and passes the actual internal ID into
capture metadata and post-validation step receipts. No general prefix matching.
Ordinary install callers still default to exact-ID matching.

Source anchors in image 660ce23a...:
- chat_completion/serving.py:256-280; SHA256 b6f42caa8aa6b45ccaefd266c1ff8994e55e3e3ab41e829ed0fb9c454487d9a2
- engine/serving.py; SHA256 38b242a091b2b4502a58b7d9b8a274ac17611b383fecc30e9b714f5da9c8dc75
- v1/engine/input_processor.py:223-240; SHA256 c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15

45 host tests passed exec0cbd (including ambiguity, bad suffix, one-time binding
and actual-ID Session propagation); static package check and diff check passed
exec0cbe. Manifest pins revised support bytes and actual 3020be48 package base.
These are not device proofs. No NPU task, quality rerun, frozen runtime edit or
foreign-resource mutation occurred. r19/r22 conclusions remain unchanged.

Next executable milestone remains ONE r20 known-hot integrated sample (prefer59):
finish its small guarded controller + independent capture/step/rank auditor,
freeze exact layers/request/raw root, verify real import/activation and launch
only after fresh direct route and physical0-3/8223 admission. Do not replace this
with another broad host-only framework, unchanged c32 wave or standalone GDN.
Do not infer slot/material correctness from source inspection or CPU tests.

## 2026-10-11 serving-loader/package host checkpoint

numerical_state_loader.py now arms a narrow HYPIC import/registration hook.
It installs state observers after the original register/apply_patches completes,
and obtains initialized TP rank only at the first selected hot forward. Each
worker capture seals only after all four component stages and the exact step
receipt; owned observer hooks are then removed. Failure leaves no success seal.

state-observer-package adapts the repository template with a byte-bound
entrypoint, opt-in sitecustomize and common launcher. It verifies support-file
hashes before loading. Disabled startup does not import HYPIC or the observer.
Enabled invalid configuration terminates startup (78), avoiding Python's normal
sitecustomize-error swallowing. This package is DRAFT, not a delivery candidate.
Manifest image/runtime-version fields refer to prior pinned-image evidence and
must be checked at admission; its evidence commit currently denotes the
pre-package base, not the later package checkpoint.

41 host tests passed (088a); static package identity passed (0888), and disabled
launcher subprocess passed (0889). Tests cover lifecycle order, disable, unload,
duplicate/late installation refusal, incomplete-capture no-seal, and packaged
enabled/disabled startup without importing the real runtime. Actual device
worker activation, rank/PID mapping and live import compatibility remain untested.

Next pin the manifest to this code checkpoint, freeze one known-serial-hot r20
sample and exact selected layer names/request ID/new raw root, then run the
bounded integrated diagnostic only after live preflight and independent-auditor
readiness. Do not expand back into another unchanged c32/full quality wave.
No NPU task was launched and no frozen plugin bytes or old verdicts changed.

## 2026-10-11 raw-writer and step-receipt checkpoint (host only)

Added a source-bound post-validation wrapper in numerical_state_observer.py.
It emits a selected request/rank/PID/step receipt only after the existing
hybrid validator returns successfully. Disabled mode does not inspect modules;
uninstall restores the exact original callable. Independent join_step_receipts
requires all four matching identities, source digest and selected-layer inventory.
This is host-tested machinery, NOT actual device step proof yet.

numerical_state_writer.py exclusively creates bounded per-worker raw files
(32 events / 64 MiB maximum), fsyncs contents, and seals the exact inventory and
digests. Missing seal, mismatched worker/request, nonfinite data, budget overrun,
tampering, extra files and symlink artifacts fail closed. No raw output is
committed. A digest seal detects later changes but is not hardware write protection
or independent provenance attestation.

Seven new tests plus the prior 26 passed (exec0870, 33 total). Next finish the
disabled serving loader/manifest, transactional installation/rollback and actual
rank/PID inventory binding; then freeze and admit one bounded integrated request.
Template and package-validator contracts were read. No device workload started,
no runtime plugin source changed; material-generation correctness remains unproved.

Read-only host snapshot exec086a at about 09:03 UTC found NPU0-3 without
processes and 8223 free; recheck before any launch. Root filesystem / reports
100% used, but /cache has 199 GiB available. CPU test temporaries were routed
to /cache/cch. No unrelated cleanup or foreign task change was performed.

## 2026-10-11 independent numerical reconstruction checkpoint (host only)

numerical_state_audit.py reconstructs NeoX KV relocation, GDN T@H+S and
conv-tail updates from captured inputs without importing production HYPIC.
It compares against captured actual destinations, reports CPU-float64 and
destination-cast residuals, and makes no automatic numerical/quality verdict.
This isolates replay/composition residuals; it does NOT independently regenerate
the cached material T/S/KV or prove their producer generation is correct.

Nine new synthetic tests plus the existing seventeen passed (exec085a, 26 total).
Controls distinguish injected KV-key/value, GDN-state/conv and position errors,
reject incomplete/duplicate capture, cross-request/step/PID/layer mixing,
malformed tensor values, missing/duplicate/foreign hot receipts, and worker
inventory mismatches. These are CPU host tests, not NPU functional acceptance.

Source inspection found legacy worker_hot_request_verified receipts contain PID
and request but no step. The join therefore reports request-level coverage only,
explicitly step_level_hot_proven=false. Do not silently promote it to a
step-specific causal proof. Add a source-bound observer receipt at validation
completion and independently audit rank/PID inventory before device admission.

Next: exclusive raw-data writer, disabled loader/manifest, step receipt, rollback
tests and exact single-request capture contract. Selected-head/row scope and
producer-generation gaps remain. No NPU workload was started, no frozen source
was changed, r19/r22 verdicts and immutable roots are unchanged.

## 2026-10-11 observer/capture host checkpoint (no device admission)

numerical_state_observer.py now source-hash-binds in-memory function replacements
for KV replay completion, GDN pre-compose/post-state-write, and position rewrite.
It is disabled unless HYPIC_STATE_OBSERVER_ENABLE=1, requires explicit request
and layer allowlists, rejects changed modules/callables, and restores only its
own replacements. It does not edit the frozen runtime source on disk.

numerical_state_capture.py takes synchronous owned CPU snapshots of canonical
KV samples and actual destination slots, RoPE table rows, GDN incoming head0
state and T/S composition inputs, conv-tail reconstruction inputs, actual GDN
and conv destination states, and expected/actual positions. Scalar budget is
bounded; snapshots are diagnostic data, not proof of device or hot execution.
Only head0 and selected KV rows are captured: no full-layer/tensor equivalence
claim. Producer-generation integrity capture is still absent.

Seventeen host tests passed under shared py311 (0849), including frozen source
hash/injection checks, disabled no-op, unload, source refusal, owned snapshots,
bounds and synthetic actual-destination mismatches. These are not NPU tests.
Independent numerical reconstruction, raw-file writer, four-rank hot-receipt
join and serving entrypoint/manifest remain unimplemented. Do not launch a
service until these pieces and the bounded diagnostic contract are verified.


## 2026-10-11 numerical-oracle preparation, no device admission

Read HYPIC_NUMERICAL_STATE_ORACLE_SOURCE_MAP_20261011.md before continuing.
The unchanged clean runtime source remains 4429e3. Source inspection maps
canonical material, actual KV destination slots, GDN state/conv slots and
position rewrites separately; it does not identify the quality-loss cause.
numerical_state_oracle.py now rejects cross-request/rank/generation/coordinate
mixing and reports numerical deltas without claiming acceptance. Seven host
synthetic tests passed (0834), 29-Skill structure passed (0835), and diff check
passed (0836). The runtime observer is still NOT implemented. No new device
root or workload was created. The next milestone is capture integration and
independent hot-request receipt validation, not another full quality rerun.


## 2026-10-11 post-commit replay repair

After 4b4af34, the reproduction verifier failed with
`branch Skill version boundary changed`: its expected HEAD Skill blob still
identified the preceding revision, although the worktree SHA had been updated.
The expected blob now pins the actually committed Skill content
`4c07dd5f7a5e4010c857b30d77081b85450dd632`; both dependent case manifests
pin the revised verifier SHA. Main boundaries and frozen experiment judgments
are unchanged. Commit-time checks must include a post-commit replay, not just
a pre-commit worktree pass.

Host `python3 -B` replay passed reproduction and all case provenance checks
(exec 081e/081f); the registry contains 29 cases: 7 marked bounded verified
and 22 partial-evidence, no missing cases. This is provenance/status replay,
not a fresh functional rerun of all Skills. The shared py311 environment
lacks PyYAML (081b); the documented system-python replay works and no package
was installed. Structural validation passed 29 Skills (081c), diff check
passed (081d). No device workload was started; r19/r22 remain unchanged.


## 2026-10-11 r22 candidate terminal — bounded diagnostic inconclusive

The frozen no-cache controller `exec-0000000000000774` terminated exit 0 at
07:15:50 UTC with 32/32 samples and 96 scored responses. Independent auditor
`exec-00000000000007a4` exited 0, replaying 160 unique request IDs, source
identity, 324 clean physical isolation samples and exact owned release. The
immutable baseline arm-result SHA256 is
`b2e7bec9914974a40689ba29901c2f45628d36f2bb1b9f614660b02d88ad7e2e`.
Sample 082 has three scored token-logprob arrays of 480, 619 and 549 entries,
each with top-five alternatives. Never restart or reuse the baseline root.

After a fresh direct-route, physical NPU0–3/8223 idle, root-absence and
same-source offline check, the frozen `hypic-only` candidate ran to 32/32
samples and 96/96 scored responses. Controller `exec-00000000000007ae`
terminated exit 1 after recording `candidate scored boundary/hot coverage
incomplete`; it was not restarted. Independent candidate audit
`r22_c32_logprob_oracle_audit.py --arm hypic-only` passed 96 rows, 160 unique
request IDs, source identity, 363 clean physical isolation samples and exact
owned release. Candidate score was 54/96; only 34/96 scored requests had
four-worker hot proof, and sample 082 had 0/3 hot proofs.

The frozen paired raw-artifact audit
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r22-c32-logprob-oracle-paired-audit.json`
exited 0 with SHA256
`23568b259c3bff7b3da562db0532a817c1705972ac283af55f8245d197185e1a`.
Both arms scored 54/96. All three sample-082 responses were correct and
naturally stopped in both arms. First differing-token positions were 124,
23, and 212; within-arm divergence positions were 23/34/23 for no-cache and
34/34/57 for HYPIC. The difference is within a similarly variable output
regime, and the traced sample lacks hot proof, so the diagnostic is
inconclusive about HYPIC causality. This 32-sample wave omits r19's first two
waves and cannot overturn r19's full-suite `REJECT_OR_QUALIFY`.

## 2026-10-11 r22 bounded output-numerics oracle — preregistration context

See `HYPIC_R22_C32_LOGPROB_ORACLE_HANDOFF_20261011.md` and its frozen JSON
contract. On unchanged r19 source 4429e3, the new adapter selects the
original third-wave indexes 64–95 at c32 and traces token logprobs for
sample 082 only. Both arm offline checks, independent auditor offline check,
three r22 host tests, standalone r19 tests and 29-Skill structural validation
pass. At freeze time neither arm had started; current execution state is
above. The wave omits r19's earlier two waves and is diagnostic only. Never
use NPU4–7 or change the r19 quality verdict.

## 2026-10-11 r21 admission reversal — no device run

The r21 source-only hash fields passed 211 host tests (one skipped) and were
committed separately at `b5f016adbc2945649d0b5c6c00944b4fe3f41327`.
Source inspection then showed that a hash-only c32 wave cannot observe actual
KV/GDN material contents or generation at replay; missing material already
fails closed in attention/GDN. The planned 32-sample device pair was **not**
launched. See the admission reversal in
`HYPIC_R21_C32_VICTIM_TRACE_PLAN_20261011.md`. Do not start r21 from that
old plan. Next build a direct, bounded native-versus-HYPIC KV/GDN/position
state numerical oracle, host-test and freeze it, then use only physical
NPU0–3 when actually idle. Preserve r19's rejection and all immutable roots.

## 2026-10-11 r21 diagnostic planned, not launched

`HYPIC_R21_C32_VICTIM_TRACE_PLAN_20261011.md` freezes the next *question*
and bounded workload. It does not authorize a device run yet: new source
bytes, host tests, final source identity, fresh roots and an independent
auditor still need to be frozen and checked. Preserve the immutable r19/r20
plugin source and evidence. Do not use instrumented timings as a performance
result or let a 32-sample diagnostic replace the full 127×3 quality ruler.

## 2026-10-11 r19/r20 read-only localization

See `HYPIC_R19_R20_LOAD_STATE_LOCALIZATION_20261011.md`. The r19 net
quality loss is 23 lost versus 15 gained paired rows; eight losses have
four-worker hot proof and seven losses stop naturally. Therefore neither
missing hot proof nor the 2048-token cap alone explains the regression.
Sample 059's first c32 wrong answer is hot-proven after a 242.42 s
admission-to-hot interval with five global material evictions, while its
serial counterpart is hot-proven/correct after 5.73 s with no evictions.
These are correlations only; no source-level cause has been isolated. Do
not relabel r19 or launch an unchanged c32 rerun. Prioritize a single
prospectively frozen state/scheduler diagnostic that can actually distinguish
mechanisms, then require a new full matched pair for adoption.

## 2026-10-11 r20 bounded diagnostic, terminal

The fresh-root, same-source serial control/HYPIC diagnostic is frozen in
`HYPIC_R20_SERIAL_DIAGNOSTIC_PREREGISTRATION_20261011.json`. It uses samples
059/082/126, explicit boundaries, 2048-token cap, two warm requests and
three scored repetitions per sample at concurrency 1. Source, model, image,
material-cache budget and physical NPU0–3 identity match r19; the only
within-r20 treatment switch is `VLLM_ASCEND_HYPIC_ENABLE`. Both adapter
`--check` modes, auditor `--check`, three host-only regressions and
historical request-hash replay passed. Both terminal arm roots and audits are
recorded below. This post-hoc-selected diagnostic
cannot overturn r19 or establish population quality.

Control arm `exec-0000000000000675` terminated exit 0 after 3/3 samples and
9/9 scored responses. Independent raw-artifact `audit_arm` replay passed:
9/9 correct, no length caps, 149 clean physical isolation samples, source
identity and exact owned resource release. Immutable arm-result SHA256 is
`07890fbb4c423aff06afe6036b7c5080da3babddf96d29cd899df9ab68944a54`.
Its root is `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r20-serial-baseline`.
The frozen HYPIC-only arm `exec-0000000000000690` also terminated exit 0,
with 3/3 samples and 9/9 scored responses. Independent candidate and paired
raw-artifact audits passed: both arms 9/9 correct, zero length caps,
candidate 9/9 four-worker hot proof, 149 clean physical isolation samples
per arm, source identity and exact owned release. Candidate arm-result SHA256
is `8cbdddb9284177dd6d020670af7af1b2e23ea31941fdf2df81e256a8a97640ce`.
Frozen paired audit SHA256 is
`44bd68b877f941af24422160941ca5006b8deabe5b3396f8e038fc3d6f41ae15`;
see `HYPIC_R20_SERIAL_DIAGNOSTIC_TERMINAL_AUDIT_20261011.md`. Both roots
are terminal and immutable. This post-hoc three-sample result does not
overturn r19's full-c32 quality rejection. Next localize the c32-specific
difference with existing r19 raw events before admitting any new device run.

## 2026-10-11 protocol-gap checkpoint

Read `HYPIC_R19_HISTORICAL_PROTOCOL_GAP_20261011.md` before launching
another quality phase. The prior reported natural-request/1024/TP2 quality
result and r19 explicit-segment/2048/TP4 result answer different questions.
R19 remains a valid all-request LongBench quality rejection, with a separate
134/381 four-worker-hot proof shortfall. No NPU work or frozen verdict change
was produced by this read-only comparison. A source-matched, new-root bounded
diagnostic must be frozen before any further full suite.

## 0. Status

- Current terminal r19 GSM8K off-path safety pair (2026-10-10): no-cache 3838/3957 (1280/1274/1284) versus HYPIC 3840/3957 (1281/1279/1280), +0.05054 pp; frozen GSM8K decision `PASS` for runtime-enabled natural requests only. Controller `exec-00000000000004a3` exited 0; candidate-only and paired independent audits `exec-0000000000000510`/`exec-0000000000000512` exited 0. Both arms' raw rows, source identity, 991/990 clean isolation samples, and exact owned release were verified. Paired audit SHA256 `496f1dfacb3c3a8dd03f8ee07368fb142b432498c0ee5dbb5722e1d4f85fd187`; see `HYPIC_R19_GSM8K_PAIR_TERMINAL_AUDIT_20261010.md`. This off-path pass does not override the explicit-segment LongBench regression or prove hot-path quality.
- Read-only r19 cache-pressure localization: 126 materialization-ready and 116 evicted events, zero materialization failures, and per-request four-worker proof 72/127, 35/127, 27/127 across the three scored repetitions at c32 with only 10 material segments. This is consistent with cache churn contributing to incomplete hot coverage, not proof of the quality-loss cause or a verdict change. See `HYPIC_R19_CACHE_PRESSURE_READONLY_DIAGNOSIS_20261010.md`; no new NPU run was launched.
- The matching GSM8K no-cache controller `exec-0000000000000433` is terminal and independently audited by `exec-00000000000004a0`: 1319×3 complete rows, correct counts 1280/1274/1284, length-limit counts 10/11/7, 991 clean guard samples, source identity and exact release. Immutable arm-result SHA256 `03a2093873b2dbf3a0f675c7d0d47d83cadd0389192e10fb491ca03525ece897`; see `HYPIC_R19_GSM8K_BASELINE_TERMINAL_AUDIT_20261010.md`. Its later paired off-path decision is recorded above.
- **Current terminal result (2026-10-10):** r19 repaired-source LongBench-v2 max-2048/c32 one-switch pair is complete and independently audited: no-cache 227/381 (74/77/76), HYPIC 219/381 (73/70/76), −2.0997 pp, `REJECT_OR_QUALIFY`. The HYPIC controller `exec-0000000000000392` exited 1 only after all rows because aggregate hot/boundary coverage was incomplete; the frozen paired auditor `exec-00000000000003f6` exited 0 and preserves that failure separately from valid all-request quality. Both arms have clean source/isolation/exact-release evidence; candidate guard had 997 clean samples. See `HYPIC_R19_REPAIRED_C32_LONGBENCH_TERMINAL_AUDIT_20261010.md` and immutable paired audit SHA256 `40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`. Do not restart/reuse these roots. The later GSM8K pair is terminal and off-path PASS as recorded above; no in-path quality adoption claim is established.
- Supplementary read-only r19 localization: across 381 within-arm repetition pairs, the median identical response-text prefix was 678 characters for control versus 186 for HYPIC, with each repetition pairing showing the same direction. This is a variability signal, not a causal diagnosis or frozen verdict change; see `HYPIC_R19_RESPONSE_PREFIX_VARIABILITY_DIAGNOSIS_20261010.md`.
- Supplementary paired-cluster sensitivity check: the observed -2.0997 pp LongBench difference has a post-hoc 20,000-draw interval of [-5.2493, +1.0499] pp over 127 paired sample clusters. The frozen quality gate still rejects; causal harm and preservation are both unproved. See `HYPIC_R19_QUALITY_UNCERTAINTY_DIAGNOSIS_20261010.md`.
- **New terminal baseline (2026-10-10):** r19 same-source no-cache LongBench controller `exec-000000000000032c` exited 0 at 12:14 UTC. Independent read-only audit `exec-0000000000000387` passed 127 samples/381 scored rows, 227 correct (74/77/76 by repeat), 865 clean isolation samples, source attestation, canary, integrated c32 wave, one-switch seam, and exact owned release. Immutable baseline root and hashes are recorded in `HYPIC_R19_BASELINE_TERMINAL_AUDIT_20261010.md`. This is a valid control arm, not a paired quality verdict; do not rerun or rewrite it.
- **Current terminal correction (2026-10-10):** r18 original-source c32/max-2048 HYPIC-only candidate failed after 33/127 complete samples (99/381 scored responses). Four TP workers hit missing GDN replay material; an async hot batch was planned before an eviction-bearing materialization report. The original `3ad0967` source lacks the known `4429e3` pending-materialization guard. Exact victim hash remains unproved. The 400 guard samples were clean and exact owned resources released. See `HYPIC_R18_C32_TERMINAL_FAILURE_AUDIT_20261010.md`. Never restart/reuse r18 candidate root. No r18 paired quality verdict.
- r18 original-source max-2048/c32 LongBench no-cache arm is terminal (`exec-00000000000001d1`, exit 0). Independent audit passed 127 samples, 381 scored responses, 223 correct, 870 clean guard samples, source attestation and exact owned release; arm-result SHA256 `7d17df0e23319ff55f2a798e2cc2a1e63f99504b23ad6fe5fb75936c0a4a3464`. Do not rewrite this immutable root. The matching HYPIC-only arm failed as described above. GSM8K has not run; no full r18 quality decision exists.
- r17 original-source cap-1024/c8 diagnostic is terminal and independently audited. Baseline 179/381 versus HYPIC 174/381 (−1.3123 pp); 377/381 aggregate hot, candidate controller exit 1 on the frozen coverage gate, but complete all-request quality evidence, clean physical NPU0–3 isolation, and exact owned release. The diagnostic quality decision is `REJECT_OR_QUALIFY`; this neither changes r16 nor establishes historical 1024/c32 or current 2048/c32 acceptance. See `HYPIC_R17_CAP1024_TERMINAL_AUDIT_20261010.md`; immutable audit SHA256 `493f9773d31a49e4f0b7e9c7ba73ea12e9722b4a7409e95c5ea05965b12853b3`. A separately labelled post-hoc repeat-variability diagnostic at `591ff7f4` found 28 candidate versus 10 baseline samples with variable correctness across three repeats; it does not alter the frozen decision or prove cause. Do not rerun either r17 root or splice later-source speed/off-path clean2 quality.
- r16 original-source full 2048/c8 quality pair is terminal and
  independently audited on physical NPU0–3: 224/381 no-cache →
  210/381 HYPIC (−3.6745 pp), `REJECT_OR_QUALIFY`; aggregate hot
  364/381 is a separate activation shortfall. Both 127×3 arms have
  valid source/score/guard/release evidence. The candidate's exit 1
  is the preregistered hot-coverage failure, not incomplete rows.
  See `HYPIC_R16_ORIGINAL_SOURCE_FULL_TERMINAL_AUDIT_20261010.md`
  and `MODEL_QUALITY_R16_TERMINAL_SKILL_CASE_20261010.md`.
  Do not launch original-source adoption performance after this gate;
  do not pool r13/r15/r16 or rewrite historical 1024/c32 success.
- r15 source-lineage E2E is terminal, independently audited and exactly released. On eight post-hoc-selected samples, original `3ad0967` scored 13/24 and current `c12060c` 10/24; this was a source-sensitivity signal, not a population or causal verdict. The subsequent full r16 original-source pair above supersedes any inference drawn from that selected subset. See `HYPIC_R15_SOURCE_LINEAGE_TERMINAL_AUDIT_20261010.md`.
- The source-map checkpoint `a863fee7` is committed locally, but its
  2026-10-09 GitHub HTTPS push failed with unavailable Username credentials.
  Do not claim origin/main or the workstream remote contains this or later
  reporting work. Do not retry identical authentication until credentials
  actually change. The worktree's current `git log/status` is authoritative
  for subsequent local commits.
- Latest 2026-10-09 r6 Decode profiler capture is terminal and independently
  audited. Controller `exec-000000000000059e` completed 512 output tokens
  with 64 post-start chunks; 441 raw files hash-check, 85 isolation samples
  are clean, and exact owned resources were released. A clean offline copy
  parsed in the pinned image under `exec-00000000000005cb` using only the
  shared driver management node, no numbered NPU devices or network.
  `verify_hypic_profiler_decode.py` proves 83,223 real NPU compute kernels
  inside the capture window on each of four ranks, spanning about 1.81 s;
  see `HYPIC_PROFILER_DECODE_AUDIT_20261009.md`. The first offline copy
  failed CANN export without the management node despite parser exit 0;
  retain it as a failure lesson. This does not repair the original Prefill
  preregistered `>=47` column miss or the frozen HYPIC quality rejection.
- New profiler diagnostic deadline: 2026-10-10 04:42:44 UTC. The frozen
  HYPIC six-phase performance and r13 max-2048 paired quality are complete;
  they are not to be repeated. The quality decision remains
  `REJECT_OR_QUALIFY` despite the measured performance gain.
- `ascend-cannbot-profiler` now has a real four-rank Prefill capture on
  physical NPU0-3. Retry2 Prefill produced 281 nonempty raw files and 88
  clean guard samples; exact owned resources were released. The same pinned
  image parsed copies of all four ranks into valid trace, kernel, op, and API
  outputs. `verify_hypic_profiler_prefill.py` replays the raw and parsed
  evidence; see `HYPIC_PROFILER_PREFILL_AUDIT_20261009.md`.
- CANN 9.1.0 / torch_npu 2.10.0.post4 emitted 46 detailed
  `kernel_details.csv` columns on each rank, including Level1 and
  PipeUtilization fields. The preregistered `>=47` numeric gate missed and is
  recorded as a protocol deviation. The branch-local maintainer Skill now
  specifies a version-aware semantic-field gate for future cases; it is not
  yet main/remote truth.
- Updated 2026-10-09. Workstream: `work/hypic-npu03-cpu-binding-fix-20261007`; checkout: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`.
- Retry21 completed the missing HYPIC-only/repeat3 phase on physical NPU0-3.
  Independent replay verifies 40/40 fixed-output rows, 42 unique IDs, 40/40
  four-worker hot proof, 164 clean guard samples, source identity, and exact
  release. The frozen six-phase performance audit is now valid: median
  weighted TPOT 74.727578 -> 58.643006 ms (21.5243% faster), TTFT P95
  86.628571 -> 45.759196 s, throughput 1.298735x. See
  `HOTPATH_CACHE10PERF_RETRY21_AND_SIX_PHASE_TERMINAL_AUDIT_20261009.md`.
- Paired LongBench-v2 explicit-boundary max-2048 quality is complete and valid: no-cache 230/381, HYPIC 219/381, delta -2.8871 percentage points (`REJECT_OR_QUALIFY`). Strict four-worker hot coverage is 368/381 and fails universal mechanism attribution. Read-only matched-hot repetition pairs show candidate answer variability exceeds baseline; see `HYPIC_R13_RESPONSE_VARIABILITY_DIAGNOSIS_20261009.md`. This is not causal proof or a reclassification.

## 1. North Star

Finish the frozen HYPIC experiment without changing its technical question or acceptance rules, then map its evidence to the relevant Skills. Keep mechanism activation, deployed effect, quality, performance, isolation, and adoption as separate conclusions.

## 2. Current Focus

The frozen performance and quality comparisons are complete; quality remains
rejected. Four-rank Prefill/Decode profiler capture and parsing replay-pass,
including the retained first-parser failure. Read-only variability and strict-
mode replay rule out non-strict combined-Prefill, but do not isolate cause. Preserve
the original Prefill numeric miss and the partial main-29 Skill inventory.

## 3. Recent Progress

- Retry21 and the six-phase audit replay-pass with
  `verify_hotpath_cache10_matched_performance.py`. Three-run median effects:
  weighted TPOT -16.084572 ms/token (-21.5243%), TTFT P95 -40.869375 s,
  throughput 1.298735x. Strict performance hot coverage is 120/120.
- r13 quality audit is immutable and independently valid for 127 samples × 3 repetitions per arm, 381 scored responses per arm; retain the original full single-service baseline.
- No-cache/screen, HYPIC/screen, HYPIC/repeat2, no-cache/repeat2, and no-cache/repeat3 have independent phase audits; see their audit paths in `task.json`.
- Retry14 guard recorded foreign `cannbench_ds` PID 242978 on physical NPU1 in 18 clean-probe samples. The service did not reach health and produced zero scored requests. Only the exact retry14-owned container was removed. Audit: `HOTPATH_CACHE10PERF_RETRY14_TERMINAL_AUDIT.md`.
- `verify_paper_to_ascend_reproduction_case.py` now verifies retry14 receipts and its four startup/capability events, without treating them as measured performance.
- The isolated repository-transformation suite replay-passes and adds bounded
  verified cases for `mst-agentsmd-authoring`, `mst-repo-transformation`,
  `mst-runtime-skill-boundary`, `mst-skill-governor`, and
  `mst-skill-tree-design`. The Cannbot boundary case re-proves current
  `/cache/cch` source locations; the later four-rank captures are separately audited.

## 4. Current Action

Do not relaunch frozen r13–r19 LongBench roots, matched-performance, Prefill, Decode,
or isolated GDN phases. r18
original-source 2048/c32 baseline is valid but its candidate failed during
runtime, without a paired quality verdict. The r19 repaired-source LongBench
pair is now terminal and independently audited as a valid all-request quality
regression with separate hot-path shortfall. Read-only localization found
length-limit and response-variability associations, not a proven root cause.
The frozen GSM8K pair is terminal and independently audited as an off-path
safety PASS. Do not rerun either arm. Admit any later
device phase only with fresh
direct-route physical NPU0–3 and port 8223 idle proof and continuous
isolation. The paired in-path LongBench quality rejection remains unchanged.
The r19 LongBench controller's post-row hot-coverage raise exceeded the
Skill's two-lens deployment-quality rule; the independent audit preserved
the valid negative all-request score and failed universal-hot attribution.
See `HYPIC_R19_CONTROLLER_GATE_RETROSPECTIVE_20261010.md`. Do not edit the
frozen controller; a successor must version its logic and test partial-hot
receipts prospectively.
Keep original-source performance, repaired-source quality, and any later
repaired-source performance as distinct claims. NPU4–7 remain outside scope.

## 5. Next Actions

1. Treat both r19 GSM8K roots and the paired audit as immutable terminal evidence; keep its off-path PASS separate from the LongBench in-path rejection.
2. Use the audited LongBench paired rows and HYPIC event evidence to narrow the early-response divergence, length-limit increase, and cache/scheduler hypotheses without relabeling correlation as cause.
3. If discrepancy localization supports one bounded repair, freeze a new
   source-matched control/treatment contract and short canary before any
   further LongBench rerun; do not rewrite r19. Only after quality is
   admissible consider same-source performance.
4. Map evidence to Skills, validate and commit coherent checkpoints. Push only
   when authentication works and independently verify the live remote ref.

## 6. Validation Commands

From this branch worktree:

```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_paper_to_ascend_reproduction_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hotpath_cache10_matched_performance.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_mst_transformation_suite.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_ascend_cannbot_profiler_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_profiler_prefill.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_profiler_decode.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_profiler_retry5_failure.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_r14_variability_terminal.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_r16_original_source_full_terminal.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p 'test_*.py'
git diff --check
```

The live performance phase is complete; these commands replay its immutable
receipts and repository case mappings. See `HANDOFF_HISTORY.md` for older
checkpoints.

## 7. Do Not Do

- Do not reuse or overwrite any experiment root, pool rows across attempts, or change the frozen workload/acceptance criteria.
- Container mapping alone is not proof of NPU use; real physical PIDs are. Do not stop or modify foreign work.
- Do not use NPU4–7, claim HYPIC performance from environmental failures, or claim adoption despite the quality rejection.
- Do not make an unapproved retry, push, or main integration claim. Keep credentials, model weights, datasets, and raw profiles out of Git.

## 8. Recovery / Resume Commands

Read repository `AGENTS.md`, `.agents/HANDOFF.md`, the relevant maintainer Skills, this handoff, `task.json`, and `HANDOFF_HISTORY.md`. Resolve `chicaihong01/ma` and prove a direct AWMCP route in each session. Before any device action, freshly capture physical `npu-smi` process state and port 8223; never infer state from a container declaration or prior snapshot.

Use `task.json` for the active milestone, latest attempt, and exact next gate; use the immutable reports for raw evidence and hashes. After a reviewed checkpoint, push only to the named workstream branch if authorized authentication is available, then independently verify upstream equality.
