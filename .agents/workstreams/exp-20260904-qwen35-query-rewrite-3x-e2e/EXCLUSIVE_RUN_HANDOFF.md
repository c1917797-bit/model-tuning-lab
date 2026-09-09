# Exclusive optimization continuation

User clarification 2026-09-06: TP4/DP2 FULL_AND_PIECEWISE is inherited
parameter-optimization experience and a candidate, never a replacement baseline.
The earlier withdrawal interpretation is superseded.

Goal: TTFT and TPOT each at least 2x faster on real query_rewrite c1/c5/c8/c16,
with correctness evidence, BF16, no quantization and no training.
Preserve both completed TP8 MTP-OFF and MTP-ON baseline groups.
Immutable denominator: TP8/DP1 MTP-OFF v5; summary SHA256
e3e03a5f1a5ce8d3e2d5f35ccf6a410d5d96555ad9012ba5881fd9227246639d.

The user authorizes exclusive physical NPU0-7 during the several-hour run.
Precisely identify and stop competing inference tasks and their orchestrators,
preserving logs/data. Keep host infrastructure and access services running.
Historical protected p0 leases no longer apply; always inspect live state.

Historical operation: exec-00000000000004e3 (terminal, startup failed).
Container: qwen35_tp4_dp2_fullpiece_user_exclusive_v3_20260906T0010Z.
Evidence root:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-dp2-fullpiece-user-exclusive-v3-20260906T0010Z

Historical observation: only this container running; eight physical TP workers,
about 16659 MB each; compilation underway. Readiness and results are unproven.
Poll this operation before any new launch. Never edit executing scripts.
Prior operation 04e0 exited 48 because p0_run reappeared; no candidate traffic.
That competing container was then stopped.

Next: verify readiness, effective config, correctness and three-repetition
matrix; compare with immutable baseline, preserving topology differences.
Choose subsequent parameter/algorithm/operator changes from profiling.
An unknown-variable warning alone does not prove an Ascend setting inactive;
check installed-source readers and actual runtime activation.

## Latest continuation

Operation 04e3 failed before readiness. During PIECEWISE graph capture,
aclnnMatmulAllReduce returned 207005 and EE1023: too many streams created.
This is a startup/resource failure, not measured performance regression.
The exact container was stopped after capturing logs; operation exited 70.
service.log SHA256:
fcdffdce308959f9f6572aae74bd2d6b16d05fe82b2f58ff362766514ef0e227.

Completed operation: exec-00000000000004eb (exit 0; all 12 cells complete).
Current container: qwen35_tp4_dp2_decodeonly_exclusive_20260906_v1.
Current output:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-dp2-decodeonly-exclusive-20260906-v1
Launcher mode tp4-dp2 uses baseline-equivalent FULL_DECODE_ONLY compilation
settings and TP4/DP2. This changes more than the graph-mode string relative
to the user fullpiece candidate; do not claim a pure graph-mode ablation.
It retains BF16, MMAR, real workload and original TP8 performance denominator.

Competing p0_run reappeared during this new candidate startup. Inspection
identified bash /cache/austinov/p0/orch2.sh, PID 1630218. The exact p0_run
container was stopped, then the verified orch2 process was terminated.
Subsequent docker ps showed only the target candidate. Check for recurrence.
The interference occurred before benchmark traffic; inspect startup validity
and ensure exclusive resources before accepting any measured cell.

Validation of the documentation stage: maintainer tree PASS (18 skills),
git diff --check PASS. Commit/push command was rejected by automatic review
because the destination was unverified for internal metadata. No successful
commit or push is claimed. Do not bypass the rejection; verify destination
and authorization or obtain approval before exporting these records.

## Superseding checkpoint: 2026-09-06 00:34 UTC

04eb is terminal; do not poll it as an active benchmark or relaunch unchanged.
384/384 requests completed without request errors. Three-repeat median TTFT /
TPOT speedups versus original TP8 OFF are c1 2.092/1.228, c5 1.440/1.340,
c8 1.121/1.549, c16 1.843/1.219. The final 2x goal is NOT achieved.
Candidate service stopped normally. Summary SHA256:
42a769c6ae6a4f9c864687fad6f5e3c5cd79631bc8e41bf9f575d92e8dd9fe4d.
Decision SHA256:
91c2e1fdfb10b00b4441e81f67d82fafae64c614632f1bcd37b0449afdbd9eba.

CRITICAL QUALITY AUDIT: all 357 dataset answer fields are empty strings,
including the first 32 measured records. Similarity to those references is an
empty-output diagnostic, not semantic correctness. The c8 hold-correctness
decision cannot prove semantic regression; other cells cannot prove correctness.
Both baseline and candidate had 69/384 whitespace-empty outputs. Preserve the
original artifacts; establish a separately versioned meaningful quality gate.

p0_run repeatedly recreated after the benchmark. A stop attempt was rejected
by safety review; no bypass is authorized. Confirmation was requested. At
00:29 all eight NPUs had no processes, and at 00:34 docker ps remained empty.
This is only a snapshot, not a lease. No new optimization job is active.

Next: recheck devices and launchers, then prepare current-topology profiling
and calibrated correctness checks. Existing capture_qwen35_tp4_profile.sh
launches old TP4/DP1 settings and is NOT a matching TP4/DP2 profiler. Do not
reuse old profile evidence as current-path activation proof. Do not silently
change frozen timing protocol or mark missing semantic evidence as passed.

## Diagnostic startup 2026-09-06 00:59 UTC

Container qwen35_tp4_dp2_profile_20260906T0059Z, immutable ID
262cfae9a638b43884d111a1a1d9a2af90fb492879c03f31243d1d1c8c39a496,
was launched through the eight-card idle/reservation guards (no ignores),
RUNTIME_ROLE=tp4-dp2 and ENABLE_DYNAMIC_PROFILING=1. Launcher operation
053b is completed; the container itself is the live startup handle. Initial
logs confirm TP4/DP2 arguments. Readiness and sockets are NOT yet verified.
No benchmark traffic or profile collection has run. Next inspect health and
run scripts/resolve_qwen35_dp_profile_workers.py against this exact container;
capture both TP0 targets, not the first match. Preserve logs before cleanup.
The new profiling switch defaults OFF; normal baseline launch is unchanged.

## Superseding diagnostic result and candidate checkpoint: 02:24 UTC

Diagnostic service reached HTTP 200. Both TP0 sockets (container PIDs 256,
259) were verified. Capture operation exec-0000000000000540 completed exit 0.
Profile root:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profile-captures/tp4-dp2-dual-tp0-20260906T0109Z
Both attach sessions logged start/stop/quit success and exported. Real request
finished naturally with 113 tokens. Device 4 / PID 259 emitted op_summary;
do not equate empty peer output with failed inference. Active op_summary hash:
a9e68c64d5102d6f5248f95df88d38f65023b1c14a5dd76ca2fe8f4624a6dbcd.
Summed task duration: MMAR categories 64.89%, MatMulV2 23.51%, GDN 1.10%.
Gate/up shape [1,5120] x [8704,5120] accounts for 974935.48 us of summed
MatMulV2 time. These are not wall-time percentages or performance claims.

Candidate proposal: configs/qwen35-query-rewrite-gdn-prefetch-proposal.yaml.
Source findings: stock gate/up trigger accepts self_attn, not linear_attn;
model has 48 linear-attention and 16 full-attention layers. Model wrapper uses
language_model.model, whereas stock context lookup expects model.start_layer.
GemmaRMSNorm has no prefetch cleanup; SwiGLU has cleanup, but zero down ratio
still invokes preprocess. Do not implement a prefix-only patch and assume safe
activation. Context, dependency and cleanup require numerical/device tests.

scripts/qwen35_prefetch_target.py is an isolated resolver, NOT runtime wiring.
scripts/test_qwen35_prefetch_target.py passed 6 structural tests inside the
current official container (operation 0559). Host Python lacks unittest.
No candidate prefetch patch is active, no new E2E improvement is proven.
The diagnostic service was still running at the last observation; recheck it
before reusing or stopping. Preserve its logs and container identity. Do not
start a second service against occupied devices. Changes are not pushed due
to the previously documented export authorization boundary.

## Current candidate startup: 03:19 UTC

Old diagnostic container was stopped after preserving service-final.log and
container-final.json under the dual-profile root. New guarded container:
qwen35_tp4_dp2_prefetch64_20260906T0314Z
ID: 15972a316efd22a335ad79312f5e9239aaf1ce94c22293e9a23aace386560788.
Launcher 0567 completed; container is live. All eight worker logs report
64 hooks installed. HTTP health remains unavailable during initialization.
No candidate traffic has been sent. Do not equate installed hooks with graph
replay activation or correct full-model output. Next check compilation/health,
then bounded canary and frozen E2E protocol. No profiler enabled for this run.

Candidate uses direct torch_npu.npu_prefetch hooks, not the stock global-state
prefetch mechanism. It binds each layer weight and dependency locally, with
ratio 0.1, BF16 and token threshold <500. Fresh-container-only patch is
scripts/qwen35_prefetch_load_hook.patch. Installer is
scripts/qwen35_gateup_prefetch_hooks.py; default disabled. Primitive and
simplified hooked-chain numerical checks at batch 1/5/8/16 were exactly equal
(operations 055c and 0560); these are NOT full-model quality gates.

## Prefetch64 screening completed: 03:39 UTC

Service reached readiness and matrix operation 056a completed exit 0.
One repetition: 128/128 requests, zero errors. c1/c5/c8/c16 TTFT p50 ms:
917.165/970.735/1042.434/1224.209; TPOT p50 ms:
34.375/35.978/43.464/56.274.
Evidence root: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-dp2-prefetch64-20260906T0314Z
Summary hash: fa6482122717e2ffeb61f9aae4adeca73a4b60caaa53908e7e8709262d5a9310.
Decision: do not promote; screening misses 2x goal and provides no compelling
improvement over unprefetched TP4/DP2. Single repetition vs three-repeat
control is insufficient for a precise causal regression claim. No semantic
quality pass is inferred from empty-reference scores. Next preserve service
logs/config and either perform a bounded attribution check or recover this
candidate; do not blindly run more repetitions to seek a favorable result.
Container may still be serving after matrix completion: inspect before cleanup.

## Profiling attribution follow-up: 03:54 UTC

Screening container was stopped normally by operation 0570, with service-final.log,
container-final.json and matrix summary checksums verified. No data deleted.
Logs contain 8 hook-install confirmations but no explicit npu_prefetch execution
record. Absence of graph-break text does not prove prefetch dispatch.

New diagnostic-only guarded container: qwen35_prefetch64_profile_20260906T0354Z
ID: 086f000d65c05766d2897ef58e5e9181b441ece72254695a5ff0886dcbd5a2a2.
Launcher operation 0573 completed. Uses same prefetch64 settings plus dynamic
profiling; readiness not yet verified. After HTTP 200 resolve both TP0 sockets
and use capture_qwen35_dp_live.py with a fresh output directory. Goal is actual
prefetch dispatch/overhead attribution, not another benchmark or promotion.

## Capture job dispatched: 03:59 UTC

Operation exec-0000000000000577 is running: bounded readiness wait (120 attempts,
5 seconds apart), then dual-TP0 capture against exact container 086f000d65c0.
Output: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profile-captures/prefetch64-dual-tp0-20260906T0359Z
Do not launch another capture. Poll 0577 and inspect this directory. Initial
health was unavailable while graph compilation progressed; NPU0-7 all healthy,
one VLLM worker per card, only the diagnostic container running. The job fails
if that exact container stops. No new E2E result or activation proof yet.

## Capture completed and first attribution: 04:09 UTC

0577 completed exit 0. Request naturally stopped at 104 output tokens; profiling
timings are not acceptance evidence. Active trace is PID258/device0; PID261
was the other attached replica. Active op_summary has 160975 rows, SHA256
7fa3afd57d795b02694eea5cbab036f5204fe930f1ff8a8e9c3a127877bb3279.
No prefetch/CMO string found in op_summary rows; this does not prove absence
of execution. Next inspect api_statistic/task_time/trace event names, then
preserve service logs and stop this exact diagnostic container when finished.
Gate/up MatMulV2 [1,5120]x[8704,5120] mean duration: unprefetched 133.626 us
(7296 calls), prefetch64 133.416 us (6656 calls): no material kernel benefit.
MMAR summed task durations are higher in candidate, but devices differ (4 vs0),
output lengths differ, and these are profiler runs, so no causal E2E claim.
Container 086f000d65c0 still healthy and running; do not launch another service.
Maintain no-promote decision for prefetch64; original baseline unchanged.

## Prefetch path closed pending activation evidence: 04:14 UTC

057d completed: api_statistic 166 rows and task_time 652204 rows contain no
prefetch/CMO match; trace event names also contain none. This is absence of
direct activation evidence, not proof of no dispatch. Do not spend another
full E2E matrix on this unchanged candidate.
057e preserved service-final.log, container-final.json and request.json with
SHA256SUMS verification all OK, then stopped exact container 086f000d65c0.
No deletion; docker ps now empty. No active benchmark or profiler job remains.
Next re-orient on the dominant MMAR/communication cost: read prior mmar-off
and selective-FFN-NZ decisions before choosing a current TP4/DP2 controlled
candidate. Existing config files alone are not evidence of successful trials.
Do not reintroduce quantization, alter frozen baseline, or relaunch prefetch64.

## Current candidate startup: 04:19 UTC

Historical TP4/DP1 selective gate/up NZ showed no stable incremental E2E gain;
old MMAR-off control used a different topology/protocol denominator. Neither
settles current TP4/DP2 communication overhead. New single-variable candidate:
RUNTIME_ROLE=tp4-dp2-mmar-off sets both environment MMAR=0 and additional
config enable_matmul_allreduce=false. All other plain TP4/DP2 defaults remain;
no prefetch, MTP, profiler or quantization. Baseline defaults remain unchanged.
Bash syntax passed. Eight-card idle/reservation and port guards passed.
Launcher 0583 completed, new container qwen35_tp4_dp2_mmaroff_20260906T0419Z:
e1aef34694b6ca7678b758eb9e83c9d7bf200eddad167e5ae0fd05743d6e4042.
Readiness not checked yet. Next verify effective MMAR-off and health, then run
one screening repetition of frozen first32 at c1/c5/c8/c16. Compare original
TP8 v5 and incremental unprefetched TP4/DP2 separately. Promote only after
repeatability and calibrated correctness; screening alone is not acceptance.

## MMAR-off screening dispatched: 04:24 UTC

Logs confirm enable_matmul_allreduce=False on all eight workers. Service was
still initializing, health unavailable, no ERROR/Traceback matches observed.
Operation exec-0000000000000586 now owns a bounded readiness wait and then
the frozen matrix, one repetition, c1/c5/c8/c16, role candidate, TP4/DP2.
Output: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-dp2-mmaroff-20260906T0419Z
Poll 0586 and candidate-run.json; do not launch a duplicate or change scripts
while the matrix is executing. Container e1aef34694b6 remains the exact target.

## MMAR-off completed; no promotion: 04:39 UTC

candidate-run.json completed all four cells, 128/128 zero errors and natural
stops. c1/c5/c8/c16 TTFT p50 ms: 946.520/1051.113/1065.669/1637.080;
TPOT p50 ms: 34.403/39.919/40.307/56.894;
output tokens/s: 21.133/88.922/129.393/132.248.
Summary SHA256 c236ce6d2c23e7a375c647de13e227990ed7587f0b097888d5b4a1387de5c22d.
Decision: reject screening for lack of incremental benefit vs plain TP4/DP2;
not final-target compliant. Single-vs-three-repeat comparison is not a precise
causal regression measurement. Empty reference quality remains unvalidated.
058c saved service/container snapshots and verified all eight evidence file
checksums; stopped exact container e1aef34694b6 normally, no files deleted.
No live candidate now. Next examine bounded FULL_AND_PIECEWISE capture sizes
as a distinct recovery from the failed huge capture list, after source and
historical checks. Do not repeat the unchanged failed fullpiece configuration.

## Bounded fullpiece recovery startup: 04:44 UTC

New role tp4-dp2-fullpiece-bounded retains user fullpiece settings but reduces
capture list to [1,2,4,8,16,2048], maximum 2048. Hypothesis: fewer captured
graphs avoid stream exhaustion while retaining a roughly 2K prefill bucket.
This is a resource-recovery candidate, not proven compatibility or speedup.
Local /cache/cch/vllm-ascend HEAD 222677fc differs from image source; its stream
error advice is NOT exact-image validation. Verify installed runtime logs.
Bash syntax and all eight-card idle/reservation/port guards passed. Launcher
0590 completed, container qwen35_fullpiece_bounded_20260906T0444Z:
340b4e331254a8eb61a72e766e8acd575195c5a273df1d306ba61f38c0ffec03.
Readiness not yet checked. Next inspect capture completion/errors; only after
health 200 run frozen one-repeat c1/c5/c8/c16 screening. MMAR on, MTP off,
prefetch off, no quantization. Baseline and failed original fullpiece unchanged.

## Bounded fullpiece screening submitted: 04:49 UTC

Container still compiling, HTTP unavailable at initial check. Operation 0592
now owns bounded readiness wait plus frozen one-repeat candidate matrix.
Exact target 340b4e331254; output candidates/tp4-dp2-fullpiece-bounded-20260906T0444Z
under the experiment evidence root. Do not start duplicate traffic. Poll 0592,
inspect health and capture errors. This operation will fail if container exits
or readiness deadline expires; preserve evidence even when no matrix exists.

## Bounded capture succeeds: 04:54 UTC

Both TP0 workers report graph capture finished (21/15 seconds, 0.43 GiB).
Health 200; 0592 matrix running c1. Runtime logs prove PIECEWISE bucket2048
execution and FULL decode1. This resolves startup only, not performance.
A short-lived unrelated container d9535d7862e3 (kind_taussig) appeared in
docker ps, but disappeared before exact inspect (No such object). Its device
use is unknown. Do not assert exclusive/no-interference for this screen;
inspect future arrivals precisely, never kill an unidentified replacement.

## Bounded fullpiece screen completed: 05:04 UTC

All 128 requests completed, zero errors. c1/c5/c8/c16 TTFT p50 ms:
465.963/816.175/798.618/868.258; TPOT p50 ms:
29.019/34.576/44.172/61.147; output tokens/s:
20.107/84.530/86.661/135.774. Summary SHA256:
c51261bf0ae1880ade9b3abdaae4fc0f0a3599e956733c1137c75c98319b9210.
Decision: startup recovery succeeds, no promotion for mixed E2E result.
Versus previous plain TP4/DP2, high-concurrency TTFT falls but TPOT rises;
single repetition and possible transient interference prevent causal claims.
No final-target compliance or semantic-quality pass. Preserve recovery recipe
as compatibility experience, not accepted cumulative performance gain.
Cleanup operation 059a is saving logs/config/checksums and stopping exact
340b4e331254; it was still running at last poll. Verify terminal status before
new launch. Next prioritize attribution of persistent long TTFT tails and
output-length/quality drift rather than another ungrounded parameter sweep.

## Tail diagnostics preparation: 05:09 UTC

059a completed exit0: all eight checksums OK, exact container stopped. No
running container at check. Existing benchmark JSON stores only aggregates,
not request latencies; retrospective index-to-tail analysis is impossible.
Added default-off --diagnostic-request-metrics to qwen35_query_rewrite_bench.py.
Allowlisted index, TTFT/TPOT/E2E, token counts, finish reason and response hash
are added after measurement; no raw text and no request/timing changes.
py_compile and --help passed (059e); end-to-end diagnostic output still untested.
Next run a mocked privacy/default-output test, then launch plain TP4/DP2 for
a c1 diagnostic pass using this flag and inspect tail/length associations.
Do not overwrite old benchmark artifacts or treat this diagnostic as baseline.

## Tail diagnostic startup: 05:14 UTC

05a0 mocked main() with flag false/true: default excludes diagnostic field;
enabled field has exactly eight allowlisted keys, no raw question/answer/output
markers. Tests passed without writing fixture files or contacting inference.
Guarded plain TP4/DP2 service launched by 05a1, container:
qwen35_taildiag_20260906T0514Z
17277f18630393a60f990a369954d2075ddb6393c68cf963e4bcdc8224c4ade2.
No MTP, prefetch or profiler; MMAR on, FULL_DECODE_ONLY. Not ready yet.
Next after health200 run qwen35_query_rewrite_bench.py c1, limit32, repeat1,
seed1024, frozen dataset hash, --diagnostic-request-metrics, fresh diagnostic
output path. Analyze per-index TTFT, prompt/output length and EOS-only cases.

## Tail diagnostic job submitted: 05:19 UTC

05a3 owns bounded readiness wait then c1 first32 diagnostic, exact container
17277f186303. Output /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/diagnostics/tail-c1-20260906T0514Z.json
Fresh-output guard passed; initial health unavailable during compilation.
No duplicate request job. Poll 05a3, then analyze allowlisted per-request rows.

## Tail diagnostic result: 05:29 UTC

Output exists, 32 completed/zero errors, SHA256
51f5da983adaef497faead244dc706b17d30c8a6d398bb87a5b673122ab3b408.
Per-index TTFT >5 seconds: 4=5906,5=5933,10=5884,12=5871,14=11848,
15=5698,18=6298,22=5840 ms. Prompt lengths only 1807-2570 overall;
adjacent similar-length requests often take ~430ms. Long-tail TPOT stays
~28.9ms, suggesting a pre-first-token wait rather than slow sustained decode.
This is a hypothesis, not root cause. EOS-only indices 2/17/27/31 have tiny
legacy TPOT; retain frozen denominator but do not use them as decode evidence.
Next inspect installed image DP wave/idle scheduling and shared-memory poll
logic, correlate service log timing. Initial core.py/core_client.py grep
found only generic timeout sites; no causal 5-second wait identified yet.
Service 17277f186303 remains live for read-only source/log diagnostics. Do not
start another candidate. Confirm 05a3 terminal before any additional requests.

## Same-service warm diagnostic: 05:34 UTC

Installed shm wait polls notification socket; timeout text alone does not
prove delayed delivery. No runtime compile log after startup found in check.
05a3 handle expired (not_found), output complete and process guard found no
active benchmark. 05ab now runs c1 repeat2 on same service, diagnostic flag,
fresh output diagnostics/tail-c1-warm-r2-20260906T0534Z.json. No runtime change.
Purpose: distinguish persistent waits from warm-cache/startup effects, not
performance acceptance. Poll 05ab; compare per-index lengths/tails with r1.

## Warm result and cache-isolation diagnostic: 05:44 UTC

r2 completed32/errors0; TTFT max1736.966 ms, p50 886.396 ms; no >5s tails.
Output7745 tokens; SHA cdee9b7b3125315fce5f371e1d9b540183c5b65e16a0cf5459e6cadebd00a385.
This weakens persistent fixed-wait hypothesis; cache versus first-execution
effects remain confounded. Added diagnostic-only cache-salt CLI (requires
request-metrics flag); default None preserves baseline request payload.
05ae now executes c1 repeat3 with fresh shared salt taildiag-20260906T0544Z,
same live service, output diagnostics/tail-c1-salted-20260906T0544Z.json.
Syntax/process/fresh-output guards passed. Salt diagnostic is NOT comparable
acceptance performance and does not replace baseline. Confirm effective salt
support before attributing outcome to cache isolation; no fresh restart.

## Salted diagnostic completed: 05:54 UTC

32 completed/errors0; TTFT max1757.266,p50437.708 ms, no >5s tails.
SHA 32cc95d855bcc5c833455e861bda6cc8bacba073febc98b6bd4079020b1dec4c.
Installed protocol accepts cache_salt; render serving forwards it and
kv_cache_utils.py adds it to first-block hash extras. Same salt within run
still allows within-run prefix sharing. First-execution overhead hypothesis
is strengthened, not proven; do not blame DP poll or CANN JIT without trace.
Compiler interface explicitly disables jit_compile at lines164/214.
Output totals r1/r2/salted=6916/7745/7819; hashes differ16/20 vsr1, EOS-only
counts4/5/4. Same-runtime output drift is real, not an optimization proof.
Next preserve live service logs and diagnose a genuinely cold first shape with
timestamped request/profile boundaries, or validate warmup on disjoint prompts.
Do not warm benchmark prompts then present that as an algorithmic gain.
Container17277f186303 remains live; no new benchmark should be inferred active.

## Diagnostic evidence sealed: 05:59 UTC

05b4 verified no benchmark process, preserved tail-service-final-20260906T0514Z.log
and tail-container-final-20260906T0514Z.json under diagnostics. Five evidence
hash checks in tail-SHA256SUMS-20260906T0514Z passed. Exact service stopped,
no data deleted. No live candidate now. Installed compiler disables ACL JIT
before npugraph_ex setup; blanket JIT explanation is unsupported.
Next implement diagnostic-only timestamp boundaries and cold-shape capture
on fresh plain TP4/DP2 dynamic-profile service, without full-workload warmup.
Use a disjoint warmup if required for profiler attachment. Preserve original
non-profile baseline and do not claim target achieved by changing warmup.

## Cold profiling prepared, resource conflict: 06:04 UTC

Profile helper now supports --skip-warmup and request wall-time boundaries;
capture helper --cold-profile-index forwards skip-warmup/index. Defaults intact,
py_compile passed; runtime cold mode not tested. Intended target index4.
05b6 launch refused exit48: p0_mp reserves NPU4-7. No diagnostic container
was created. Exact conflicting ID 4ab45217800d35f04ea1f944d93890e09beb02885de89b730b21307e70c76582,
started06:00:50, bash /cache/austinov/p0/serve_mp.sh, TP4 Qwen model port8100,
maxlen41984 and prefix caching disabled. This is not our frozen diagnostic.
Prior p0-stop safety denial remains relevant: do not bypass it or terminate
replacement orchestration without resolving authority. Safe source/record work
can continue; do not start an eight-card service while this conflict exists.

## Offline validation while conflict persists: 06:09 UTC

p0_mp exact4ab45217800d still running; no new eight-card launch attempted.
05b9 mocked profile main() with skip-warmup false/true: two versus one request,
correct target index4, ordered wall timestamps, raw response absent and
performance_evidence=false all passed. No device requests or fixture writes.
Cold runtime integration still awaits free devices or resolved stop authority.

## Persistent resource conflict: 06:24 UTC

p0_mp was recreated: current ID672ffe22549683e8cc062e635c8b37305b98e7846ba1142b858eb6fd33537d94,
same serve_mp.sh command and NPU4-7 reservation (verified05bc), still running
at05bd. Old4ab452 ID is stale. No task-owned inference job is currently active.
Cold diagnostic implementation and offline tests are ready; eight-card launch
remains blocked by resource ownership/stop-authority boundary. Do not retry
denied stop through another route or use stale container IDs. Resume with
fresh device/container checks when resources are released or authority resolved.

## p0_mp relevance audit: 06:30 UTC

Read-only source audit identifies FFN micro-pipeline, not unrelated model work:
mk_micropipe.py splits >=4096-token FFN input into K tiles, computes local down
matmul then all-reduce on separate stream. Container env K=2. orch_mp.sh uses
random40K input, output1000 ignore-EOS, c16, not frozen query_rewrite. MP0 only
results present at check; no MP2 benefit yet evidenced. Short sky-question
greedy equality check does not exercise >=4096-token modified branch, so it
cannot validate micro-pipeline correctness. Do not import a PASS uncritically.
Possible future reuse requires branch-triggering BF16 numerical tests and E2E
on our workload; c1 ~2K input normally below threshold. Current p0 still holds
NPU4-7, owner unresolved, no stop attempted and no new task service launched.

## USER SUPERSEDING SCOPE: four-card joint optimization started

User explicitly moved this loop to physical NPU0-3, TP4/DP1. Leave NPU4-7
and p0_mp untouched. Joint parameter/algorithm/operator changes are allowed
when justified by a coherent hypothesis; verify numerical/semantic correctness
and actual runtime branch, then E2E before stacking. No quantization/training.
New four-card reference is separate from immutable eight-card v5; never claim
cross-topology improvement as causal optimization gain. Shared host contention
from p0 must be recorded even with disjoint NPUs.
Launcher role tp4-dp1-npu03 checks/maps only0-3, no ignored reservations.
Container qwen35_tp4dp1_npu03_ref_v1, ID
2e1cfc928aa676144da875fa5924d9113a9cf7678a9f72dc51d5e62c292810ae.
05c6 launched; 05c8 verified exact0-3 device mappings, MST18skills PASS,
git diff --check PASS. Initialization ongoing, no readiness claim yet.
Operation05c7 owns readiness wait then MTP OFF reference c1/c5/c8/c16 x3.
Output baselines/tp4dp1-npu03-ref-v1 under experiment evidence root.
Next inspect05c7 and baseline-run.json, preserve table/hashes; then MTP ON
four-card control with identical protocol, profiling, hypothesis, implementation,
correctness, E2E measurement, decision and rollback/stack. Existing8card and
failed attempts remain immutable. Push remains prohibited until export approved.
Any heartbeat text still asking eight-card launch or stopping p0 is STALE.

## Four-card reference ready: 06:43 UTC

Health200 verified05d0; baseline-run.json records TP4/DP1, physical0-3,
three repetitions, c1/c5/c8/c16, no quantization. 05c7 confirmed running.
Matrix has started (no completed cell yet); do not edit benchmark/runtime
scripts or issue diagnostic traffic until this matrix is terminal. Earlier
shared-memory warning occurred during compilation and did not prevent startup.

## Four-card reference midpoint: 07:01 UTC

05e2 confirmed operation05c7 running, six of twelve cells completed
(all r1 plus c1/c5 r2). Do not edit executing benchmark/runtime scripts or
send diagnostic inference until terminal. First round all128 requests/errors0.
c1 r2 completed32/errors0: TTFT p50=920.190820 ms, max=973.911120 ms;
TPOT p50=35.319914 ms, p95=68.522311 ms. First-round c1 TTFT max was
22013.526420 ms; disappearance is not a demonstrated algorithmic gain.
Same-host p0_mp was recreated during this matrix: current short ID41294082aeec,
Up5minutes at07:01:29; prior672ffe ID is stale. Leave p0 and NPU4-7 alone.
Shared-host interference is a comparability caveat, not a proven cause.
MTP overlay HEAD37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd and clean tree
verified05dd. Launcher currently lacks four-card MTP role: after reference
terminal, add tp4-dp1-npu03-mtp-local-argmax and ensure its device scope
inherits only0-3, TP4/DP1, k1. Existing suffix matcher activates MTP mounts;
exact-match four-card selector must be extended too. Never use eight-card
mtp-local-argmax role for this new scope. No target speedup achieved yet.

## Reference complete and latest target confirmed

User explicitly confirmed continuous execution toward TTFT and TPOT each3x;
old persistent objective2x is stale. Physical0-3 scope remains. Heartbeat
qwen3-5-27b updated ACTIVE, every5minutes without prior72-run cap, target3x.
05c7 is TERMINAL completed exit0. 05ec checked all12 cell hashes,384 requests,
zero errors and natural EOS. Table and summary checksum: TP4_REFERENCE_V1.md.
Reference service2e1cfc928aa6 has NOT been stopped by this update. Next preserve
final service identity/logs and exact-stop this task-owned service after checking
no benchmark remains; add four-card MTP role and run same-protocol3rep control.
Do not restart completed reference or infer an MTP job is already launched.

## Superseding goal and four-card MTP control launched

Latest user goal explicitly changed to TTFT/TPOT each2x with lossless accuracy;
this supersedes previous3x wording, including TP4_REFERENCE_V1.md target prose.
Reference numeric data unchanged. Heartbeat updated to2x and lossless accuracy.
Do not substitute zero errors, empty answer metrics, or relaxed quality gates
for lossless correctness; MTP timing is exploratory until correctness evidenced.
05ef: shell syntax, git diff check and MST18skills PASS. New exact role
tp4-dp1-npu03-mtp-local-argmax selects TP4/DP1 and only0-3, k1.
05f0 preserved reference service-final.log SHA0365b91446e5ffa11924739cf1c0874bcd8c98bb19acebd35977e6e7656d96c8
and container-final.json SHA28d79ebc3d14f24c193bfe2306a765d5f91a52190245805803fecba0f5b1a864;
then exact-stopped2e1cfc928aa6. No data removed.
05f1 launched qwen35_tp4dp1_npu03_mtp_k1_v1, fullID
12b20e8ef0927e42c1c978d3cfea9fbf1324e9439855b5d3a09f12d50d48278c.
05f2 verified running and exact physical0-3 device mappings. No readiness yet.
05f3 owns readiness wait then c1/5/8/16 x3 matrix, role candidate, output
baselines/tp4dp1-npu03-mtp-k1-v1 (candidate-run.json/candidate-summary.json).
Poll05f3; never duplicate or edit executing scripts. Source overlay pinned
37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd. Next verify startup/device path,
matrix completion and correctness before accepting any speedup. No goal achieved.

## Lossless correctness pre-audit (05f6)

Immutable four-card OFF baseline itself has greedy output drift: identical
response hashes across all3 repetitions count9/32(c1),15/32(c5),10/32(c8),
14/32(c16). r1-vs-r2 changed22/16/18/17 respectively. Output-token totals:
c1=7162/6702/6464; c5=7195/7352/7004; c8=6741/6982/6551;
c16=6542/6316/7135. This is not evidence of accuracy loss or a tolerance
license. Simple hash equality against one noisy baseline cannot certify lossless
accuracy, and EOS-only matches must not count as semantic-quality proof.
Next correctness gate must control identical token prefixes/batch/cache state,
compare verifier token decisions/logits or mathematical/numerical operator
equivalence, and retain meaningful full-output validation. Do not relax the
user lossless requirement to mask baseline drift. No new inference was issued
during current MTP startup/matrix;05f3 last confirmed running at05f4.

## Parameter provenance correction (05f8)

User asked whether prior parameter experience was absorbed. Clarified current
four-card reference contains inherited optimization settings; it must be called
current-configuration reference, not exact original baseline. New
PARAMETER_PROVENANCE.md separates original-log facts, current values and unknowns.
Prefix caching and FULL_DECODE_ONLY were present in original engine log, so do
not indiscriminately classify all shared settings as contamination. Unknown
original env/flags are not defaults or false. Do not weaken baseline to create
speedup. Preserve all raw evidence and finish active MTP control unchanged.
05f3 running at05f8, startup shared-memory60s warning observed; no readiness or
failure claim. Live0-3 workers established05f7; do not restart on warning alone.

## MTP first-round evidence 07:36 UTC

05f3 confirmed live by0603; three cells complete (c1/c5/c8 r1), c16 next.
Startup finished by05fb and real SpecDecoding accepted/drafted counters seen
05fd: most observed windows76-88% acceptance, not an E2E speedup claim.
c1 r1 completed32/errors0,naturalEOS,6728 output tokens, TTFTp50=1014.183395ms,
TPOTp50=33.569001ms; SHA f7bf6917d89d9a0b7f0d7eff698cf8e227b80d34c082aa048c3a8b4ca05c8c9b.
c5 r1 errors0,32stop: TTFTp50=1192.837345ms,max=29515.696610ms;
TPOTp50=50.759859ms,p95=243.751988ms,max=6302.331070ms.
Large TPOT tail requires per-request length/stream-event diagnostic after matrix;
current aggregate files do not identify affected requests or prove root cause.
Keep zero/short-output denominator semantics explicit; do not modify live
harness to hide tails. No accuracy PASS or joint2x gain established.

## Single-replica profiling preparation

capture_qwen35_dp_live.py now forwards --expected-replicas (default2 preserved)
to existing resolver; use --expected-replicas 1 for TP4/DP1 diagnostic service.
0607 mock verified default2, explicit1 forwarding and invalid0 rejection;
no file writes or subprocess/device requests during mock. MST18skills and
git diff check PASS. Actual single-replica capture not yet run; service must
be started with dynamic profiling separately after measurement. Active05f3
MTP matrix remains untouched and confirmed live before this offline edit.

## MTP matrix completed 07:54 UTC

05f3 TERMINAL completed exit0;0611 verified12hashes,384requests,zeroerrors,
naturalEOS. See TP4_MTP_COMPARISON_V1.md for table and immutable summary hash.
Observed TTFT ratios OFF/ON c1/5/8/16=.986/.896/.879/.880;
TPOT=1.085/1.072/1.011/.914. No joint2x; lossless correctness not proved.
Do not adopt this MTPk1 configuration as solution; small low-c TPOT gain alone
insufficient and causal certainty limited by shared-host/output/cache caveats.
Container12b20e8ef092 remains running, no measurement process should remain;
verify before preserving final logs/identity and exact stop. Next separate
four-card OFF dynamic profiling, --expected-replicas 1, then hot-path change.
Do not rerun completed matrix by mistake. Goal remains unmet, not blocked.

## Four-card cold profiling launched

0612 verified no benchmark process and task-owned MTP container on0-3;
other container ca92a8661538 qwen36_hypic_nocache_baseline_npu4_5_tp2 uses4-5,
leave it untouched. Shared-host interference remains caveat.
0613 preserved MTP service-final.log SHA10982eb4f46e0c11fa8e668c2985ed2f82e5d8f54b840e4f9fe22c8c179cd8a0
and container-final.json SHAe51e79240cd6027fe60ab1335e2753816055aad5d4d3fde290743b7d42f6e02c;
exact-stopped12b20e8ef092, no deletion.
0614 started OFF dynamic-profile role tp4-dp1-npu03, ENABLE_DYNAMIC_PROFILING1,
qwen35_tp4dp1_npu03_profile_v1 ID
f8220d870b072108501dbd2bd57413467f7f32024d38b2cb9c66bcba872e9f57.
0615 owns readiness wait then capture_qwen35_dp_live.py --expected-replicas 1
--cold-profile-index 4, output profile-captures/tp4dp1-npu03-cold-v1.
No health/readiness or trace completion yet. Avoid any warmup/inference traffic
before cold capture, and do not edit capture scripts while0615 running.
This captures a first post-startup real shape without request warmup, not cold
process startup. Trace timing is diagnostic only, never E2E acceptance evidence.
Next verify0615, request boundaries, target PID/NPU map, trace hashes; inspect
prefill/decode critical path and distinguish startup-shape overhead from steady.
