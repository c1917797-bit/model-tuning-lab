# Qwen3.8 NVFP4 on Ascend 910B4 Handoff

## Qwen3 control r1 raw-artifact audit (2026-09-14)

Re-read all1428 request rows across c1/c5/c8/c16 from completed Qwen3 r1.
Verified manifest/summary/row SHA256, dataset357 identities and input-message
hashes, reconstructed response text from SSE events, output hashes, usage token
counts, nonempty natural-stop/no-reasoning conditions, TPOT algebra and all
P50/P95/P99 values using an independent interpolation implementation.
Audit: `/cache/austinov/eval-runs/qwen3-r1-raw-audit-0r_80e2s/audit.json`,
SHA256 eed532f4e0b81f7c683bfaf7b728c0c0f5f7c27686a7eff8d978476e98e741ad.
All checks passed; original performance numbers unchanged. Reuse this valid
r1 rather than rerunning without cause. This does NOT finish three-repeat
paired comparison or certify candidate quality. Raw SSE events lack independent
per-event receipt timestamps; capture timing relies on the pinned audited v4
benchmark, while arithmetic and reported quantiles were independently checked.

## Cross-model HumanEval scoring preparation (2026-09-14)

Actual CPU-only execution-manifest smoke completed using source a5e7eda:
`/cache/austinov/eval-runs/humaneval-manifest-full-1usep7e5` contains full164
canonical fixtures (164 passed) and full164 raising fixtures (0 passed).
Both sample/problem/result hashes were recomputed and match manifests.
Canonical manifestSHA a2f2b651a98e83979e77333548e71d050fdd4265e4e58ba453bdb3ce95fd1ec3;
negative manifestSHA f0998e0b561d71728bf044e23ce9632287e7d566bc0cc493d428add126587fa8.
First two-item fixture attempt at `/cache/austinov/eval-runs/humaneval-manifest-smoke-frrhl2u1`
was correctly rejected by official evaluator because full problem set requires
all164 attempted. Preserved, not a model failure. Do not relax this check.
These fixture results are NOT model accuracy. CPU containers used no NPU,
network none, read-only root, bounded CPU/memory and disposable source copy;
original image/host framework unchanged. Live MMLU unit remained active and
advanced to1447/56168 requests during this check.

Added `qwen38-nvfp4-ascend/compare_switch_humaneval.py` for the model-switch
comparison; the older quantization-specific scorer remains unchanged. Native
prompt hashes may differ across models, but full HumanEval/0..163 source
documents, generation protocol, extracted samples, and executed completions
must match their evidence. Each outcome must be a real boolean and consistent
with its execution result. Reports include paired pass@1 differences and an
explicitly approximate interval, not an automatic lossless/migration verdict.
Generator now records source-document hash and frozen protocol. Disposable
execution entrypoint emits a manifest binding sample/problem/result hashes,
evaluator source hashes, 3-second timeout and 4 workers. Comparator checks this
chain and cross-arm evaluator identity. Model/image identity and actual sandbox
isolation still require the separate runtime artifact audit.
Focused dependency-free tests cover native-template differences, missing and
duplicate tasks, source/request drift, serving errors, extraction/execution
mismatch, non-boolean outcomes, and disk checksum/protocol corruption.
These are tooling fixtures, NOT new model quality results. No NPU service or
active MMLU source was changed. HumanEval model generation remains pending.
Usage after both full generation and sandbox runs:
`python3 qwen38-nvfp4-ascend/compare_switch_humaneval.py --control-dir <Q3-generation> --candidate-dir <Q38-generation> --control-results <Q3-samples.jsonl_results.jsonl> --candidate-results <Q38-samples.jsonl_results.jsonl> --data-root /cache/austinov/eval-data/general --output <fresh-report.json>`.

00:17UTC non-interrupting SQLite backup saved to
/cache/austinov/eval-runs/mmlu-cache-checkpoint-ic03wkan,708entries,
integrity_check=ok, cacheSHAcce878d2050a01b01489d04fac29453b1c5aa9b80afc91adad84f91d6ee48162.
Manifest binds copied input/evaluator/image/model/profile identity hashes.
Source opened read-only and SQLite backup used (not unsafe live file copy).
Full PID3862919 remains running/unpaused and continues beyond snapshot.
This is a cache checkpoint, NOT a full result or tested resume implementation.
User priority question still unanswered; no additional task stopped.

## 00:14 UTC — full client RESUMED; paired32 alternative NOT promoted

Diagnostic L1i2ED completed32/32 with all4labels in top20, winners31/32 match.
abstract_algebra doc2 differs: standard C=-1.5972367525,D=-1.5210561752
choosesD; next-token C=D=-1.5680167675 ties and first-max choosesC. Max relative
logprob difference0.3577424287791473. Do not claim numerical/full equivalence,
accuracy regression direction, or established root cause. Alternative NOT
accepted as replacement; no fabricated missing scores or silent tie handling.
SummarySHA2534899d0729b7b9eb59c84c1829cacebbee92369f9277b0d1309c21c595f36f;
referenceSHA6cc8ebdc387034d06eac3c276113c4329cae8a7678c4262adfcb05dc9e93e6ba.
Exact full clientf1c3f7bf6dcb0263b760135c50a6f3898a140fa6d53631f6f0b73c4b5075f790
unpaused manually; verified running/paused=false, safety timer stopped only
AFTER successful unpause. R3 model/unit remain live. Full SQLite read-only
count confirms583 completed cached requests (unnamed table), matching logs.
Asked async user whether to checkpoint MMLU and prioritize performance/GSM8K/
HumanEval within12h, then resume full MMLU, versus keep MMLU first accepting
>12h. NO response received at this checkpoint: keep current full job running.
Any future resume must validate same model/image/data/harness/protocol and
copy a consistent cache snapshot into a fresh run; never overwrite originals.

## LIVE00:08 UTC — bounded paired32 diagnostic, full CLIENT temporarily paused

Model1adbdddbad6e and unitr3 remain running. Full CPUclient
f1c3f7bf6dcb0263b760135c50a6f3898a140fa6d53631f6f0b73c4b5075f790
is intentionally docker-paused (not stopped; caches/progress preserved) to
avoid ~25min diagnostic queueing behind its8requests. Safety resume timer
mtl-mmlu-resume-20260914.timer active, scheduled10min after pause (~00:17UTC).
Unpause this exact client EARLIER when diagnostic ends; never leave paused
or duplicate full run. Model/NPU lease remains owned by r3 throughout.
Diagnostic container7483cb8b39b7a36722a42d3abdfbe5dd80ff36954c1cfb072e1c45641bcdaacb
artifact /cache/austinov/eval-runs/mmlu-next-token-paired32-L1i2ED.
Eight MMLU subjects first4each: abstract_algebra, professional_law, anatomy,
high_school_mathematics, high_school_physics, high_school_us_history,
logical_fallacies, clinical_knowledge. Standard5shot reference128 optioncalls
at clientc1, then probe_mmlu_next_token.py automatically compares32questions.
Reference27/128 completed at00:07:55. Diagnostic only, not full quality or
performance. Use actual result/token coverage/margins before any promotion.

## 2026-09-14 00:00 UTC throughput / next-token diagnostic

Current r3 full evaluator PID3862919/container
f1c3f7bf6dcb0263b760135c50a6f3898a140fa6d53631f6f0b73c4b5075f790
passed6-item5shot canary6/6 and reached actual full requests23:51. First
hundreds returned, no repeat OOM observed. Standard echo prompt-logprob
method ~0.6requests/sec is too slow for remaining12h deadline; do not promise
completion on that basis. R3 stays active, do not duplicate it.
Bounded alternative diagnostic source9d3b332, artifact
/cache/austinov/eval-runs/mmlu-next-token-probe-WAufEH/probe/summary.json.
Four existing MMLU canary docs, exact harness _encode_pair then factor common
continuation prefix; four residual tokens32/33/34/35. One completion returns
raw next-token top20 probabilities using return_tokens_as_token_ids=true.
All4labels present in all4cases; winners4/4 match standard method, BUT maximum
relative logprob difference0.24182689174813277. NOT numerically identical,
NOT a validated full replacement. Concurrency/prefill/cache execution differs;
no attribution of numeric drift is established. Diagnostic timings under
concurrent quality load are NOT performance evidence. Needs broader paired
validation, especially small-margin questions, before changing formal method.
Original image supports /generative_scoring with label_token_ids but response
only exposes first label score; no need to modify framework to explore it.
Do not infer all labels are always in top20; missing labels require explicit
fallback, never fabricated scores. Old generation-answer MMLU remains excluded.

## LIVE23:30 UTC — bounded logprob workspace attempt

Unit mtl-q38-quality-20260913-r3.service active, MainPID3774324.
Artifact /cache/austinov/eval-runs/switch12h-qwen38-quality-workspace-20260913-hlBZAo
Container1adbdddbad6eeea8e3a01c0201ec0611a57e5ecb06c264890f98b818bc61cc4c.
Startup23:30:20UTC from0cdb1fb; profile file confirms0.75/2048. Full quality
pipeline, no performance claims from this service. Await6-item canary and
actual full scoring before declaring the OOM mitigation verified. Freshgate:
8empty/noholders, portfree, leaseobtained, MemAvailable84190480KiB, external
manager-only bash container unchanged. Old r2 is terminal, do not resume it.

## 23:24 UTC full MMLU failure — proven NPU prompt-logprob OOM

Second attempt pJYHxH reached full56168 requests then NPU worker failed in
sampler.compute_logprobs -> logits.log_softmax(dtype=float32): allocation2.84GiB,
only2.40GiB free on NPU0 (similar NPU5); active25.79GiB. Scheduler dump has
3220-token prompts and two3072-token prefill chunks. Docker process exit0 did
NOT mean successful evaluation. Full service.live.log SHA256
c1fe1d6f761ad37c95dc1d4fc4f65db9a5449099b33bc706bb13fd7b6625e655.
Systemd controller survived, disproving controller-loss as sufficient cause
of this second failure. First attempt cause cannot be proven retrospectively.
Stopped exact failed unit r2 and CPUca02cc7a45fa after preserving inspect/logs;
MainPID0/failed, only unrelated bash container remains. No full scores.
Fix now prepared: QUALITY ONLY gpu_memory_utilization0.75 and maxbatched2048,
same on both models, recorded server-profile.json. Performance retains0.90/
32768; do not pool quality service timing with performance results. Dataset,
BF16/five-shot/seed/length/scoring unchanged. Canary adds professional_law2
alongside abstract_algebra2/GSM8K2 before full run. Server-death polling now
aborts invalid scoring rather than allowing endless connection retries.
Syntax, comparator regression, MST checks pass; NPU OOM fix not yet proven.

## Standard text comparison preparation / live23:15 UTC

Recovery unit3572690 remains active; 8worker gate passed, small canary actual
MMLU2/2 and GSM8K2/2 with n-shot5 verified. Full phase began23:12:26;
CPU evaluator ca02cc7a45fa6d15b88a1e1ebe18fef834b0eda74273957fc3eab01dec745e7e
is preparing full requests. No full score yet. Do not repeat completed canary.
Added compare_standard_text_quality.py for the CURRENT lm-eval likelihood
MMLU protocol (old score_text_quality.py is generation-answer extraction and
must NOT score these artifacts). New entry verifies full local documents,
counts, five shots, pinned harness/protocol, raw response presence and recorded
score consistency; pairs native-model runs by identical dataset documents,
not identical tokenizer/prompt bytes. Reports MMLU micro/macro/subjects and
GSM8K strict, discordant pairs and labeled normal-approximate paired95CI.
This is not provenance certification or a lossless/migration acceptance gate.
Dependency-free synthetic tests pass including invalid artifact rejection;
actual full local population validated58tasks15361rows; MST/diff pass.
Run once BOTH full results exist:
python3 qwen38-nvfp4-ascend/compare_standard_text_quality.py --control <Q3-results.json> --candidate <Q38-results.json> --data-root /cache/austinov/eval-data/general --output <fresh-external-report.json>

## Current recovery 2026-09-13 23:03 UTC (supersedes earlier LIVE entries)

User approved continuing current order: MMLU/GSM8K, HumanEval, remaining
performance comparison. At23:00:05 Docker recorded old NPU service f1055dc
die(exitCode0) then destroy; evaluator began ConnectionRefused retries.
Termination cause remains unproven (no observed OOM event). Preserved old
evaluator inspect and quality-full.recovered.log in oOH3fa artifact before
stopping ONLY exact owned CPU container1248efadb5f0. It is now absent.
No full score from that interrupted attempt is valid or claimed.
Launcher2289a3b now records exact evaluator cidfiles and cleans only these
owned IDs if interrupted. Shell syntax/MST26skills/diff checks passed, pushed.
Recovery uses transient systemd unit mtl-q38-quality-20260913-r2.service,
MainPID3572690; independent of AWMCP exec ancestry. No claim that this proves
the prior root cause. Active/running verified, startup23:03:13UTC.
Artifact /cache/austinov/eval-runs/switch12h-qwen38-text-recovery-20260913-pJYHxH
NPU container b49c1d4e438d03df23219b033c4f8e26d9f7df3df71b2681997fab73618d5032.
Same fixed image, TP8 BF16/seed1024/thinkingfalse, original model and protocol.
Fresh launch gate: all8NPUs empty/noholders, portfree, leaseobtainable,
MemAvailable84215892KiB. Sole external running container321c36f70aac onlybash
and manager devices; left untouched. Follow unit MainPID plus exact container
and new artifact status/logs; never duplicate a live run on gateway timeout.
Automatic small5-shot canary then full58tasks15361rows remains configured.
HumanEval and full paired performance matrix are still outstanding.

## Live recovery observation 2026-09-13 22:58 UTC

AWMCP transient transport outage recovered without restarting any workload.
Controller3385497 is now absent; its termination cause is NOT established.
Do NOT use the stale redirected quality-full.log as a liveness signal.
Owned NPU service f1055dcda5e4572b2dbcd56b14c275c074ecd680c9b16c2730688b81b6d99f84
is running, OOMKilled=false. CPU evaluator container
1248efadb5f030ccabcbeea28501163a11804786b3d93438a5bbe20081665f6b
and process3474870 remain live, CPU~100%; Docker logs show advancing MMLU
tokenization ~45171/56168. Full scoring is not yet complete. Observe exact
containers directly; do not relaunch or duplicate the evaluation. Original
shell cleanup can no longer be assumed: at evaluator termination preserve
Docker logs/inspect, verify full results/counts/hashes, and explicitly perform
only owned service cleanup before advancing the next arm. Existing heartbeat
must use these live handles, not missing controller or stale file timestamps.
Actual small canary results confirm n-shot=5 for MMLU and GSM8K, each2/2;
this establishes plumbing only, not full accuracy. MemAvailable49449148KiB
is below the NEW-launch48GiB gate; do not launch another service now, and
do not stop the healthy existing evaluation solely for that launch threshold.
All original-image/framework restrictions remain unchanged.

## Current goal — latest user clarification 2026-09-13

22:43 pre-scoring correction: historical2-item quality canary9ryELw explicitly
records n-shot mmlu_abstract_algebra=0, gsm8k=5. Its MMLU1/2 score was a0-shot
plumbing check, NOT the promised5-shot protocol. Individual MMLU default YAML
does not set num_fewshot; no group-inheritance claim is established. Fixed
run_standard_text_quality.py to set num_fewshot=5 explicitly for both task types,
assert constructed task configs and actual result n-shot values, and persist
shot counts in protocol metadata. Source fix made BEFORE current CPU evaluator
started; controller3385497 remained in NPU startup, no model/frame/image edits.
The controller hashes evaluator files immediately before launching the client,
so use evaluator.sha256 for exact scoring bytes rather than only startup commit.
Full offline construction passed58tasks/15361rows/all58five-shot, artifact
/cache/austinov/eval-runs/switch-five-shot-preflight-iRnuOM/full/results.json,
SHA256eff979b0e9bfda2f197bcd1bd0766dd360d65e5a88e8c1a8c52b06f7285da219.
Await actual concurrent5-shot canary before claiming full scoring began. Keep
old0-shot records unchanged and excluded from5-shot accuracy comparisons.

LIVE22:39 UTC Qwen3.8 full text-quality pipeline PID3385497 PPID1, container
f1055dcda5e4572b2dbcd56b14c275c074ecd680c9b16c2730688b81b6d99f84,
artifact /cache/austinov/eval-runs/switch12h-qwen38-text-full-20260913-oOH3fa.
Started22:38:45 from pushedb46df46; command run_switch_canary.sh qwen38 <out>
quality-full. Currently startup; after8rank/health gate, concurrency8 small
MMLU/GSM8K check, then full15361 standard text items. HumanEval not included.
Follow exact controller/container, quality-canary.log and quality-full.log;
do not duplicate on observation timeout. Fresh resources:8empty,noholders,
portfree,MemAvailable84238356kB,lease obtainable; unrelated bash container
unchanged. No input-normalization approval has arrived and no formal query
protocol was changed. Original candidate query failures remain part of report.

22:35 Qwen3 original repetition1 COMPLETE, finished22:34:01. Controller3208813
and owned containera19dae4cfa51 gone. All four357 cells passed: errors/empty/
reasoning/prompt mismatches/undefinedTPOT all0; all357 stop. P95 TTFT/TPOT ms:
c1 364.009888/44.242973; c5 764.495800/108.435290;
c8 965.979688/147.033256; c16 1375.014982/194.880301.
Full evidence/hashes: qwen38-nvfp4-ascend/qwen3-original-performance-r1.md.
Only one control repetition, NOT completed paired comparison; do not reuse old
raw-completion or normalized-input metrics as its candidate denominator.

Next advance independent standard quality while input-policy answer is pending:
run_switch_canary.sh qwen38 <fresh-out> quality-full. Same original BF16 service
configuration, no dataset normalization. Runs2-item MMLU/GSM8K live plumbing
check at concurrency8, then full57subject MMLU14042 plus GSM8K1319 at8. Fresh
per-run harness SQLite response cache preserves completed model calls for
controlled recovery (evaluator.py63/277-283 confirms supported use_cache). Never
reuse caches across model/config/protocol identities. Existing fresh-output
guard remains; manual recovery must verify identity before opting into reuse.
HumanEval remains separately required. Do not wait on query normalization to
block these independent quality datasets, nor call Qwen3.8 query validity fixed.
This advances requested scoring, not a performance acceptance or migration claim.
Recheck eight-card resources and exact lease before launch; no external edits.

22:19 Qwen3 original repetition1 advanced to FULL performance. Fresh32 canary
passed32/32,errors0,empty0,reasoning0,stop32. Controller3208813 is live; c1
benchmark child3255121 was verified with --limit0 and frozen dataset SHA, cap4096.
Artifact /cache/austinov/eval-runs/switch12h-qwen3-performance-r1-20260913-iRDuy1;
performance/manifest.json state running, cells initially empty. Follow c1.json
then c16/c5/c8; do not restart or call incomplete cell a result. Container and
lease remain owned by existing lifecycle. No normalization approval received.

LIVE22:13 UTC Qwen3-32B original-data performance repetition1: PID3208813 PPID1,
container a19dae4cfa516ecca08ef78ebd0de82ef9fb593bc7c81c5676ad6e984115b0cb,
artifact /cache/austinov/eval-runs/switch12h-qwen3-performance-r1-20260913-iRDuy1.
Started22:12:53 from pushed5c979c4; run_switch_canary.sh qwen3 <out> performance1.
Currently startup, will run fresh32 canary then357 each at1/16/5/8. Follow exact
job; do not launch any other NPU service. Resource gate immediately preceding:
8empty,noholders,portfree,MemAvailable84213256kB,lease obtainable, unrelated
Maxon4ick bash-only container untouched. Original-input model comparison and
full quality still incomplete. Awaiting user's input-policy response; unchanged
original control work can proceed without assuming normalization approval.

22:11 history diagnostic TERMINAL (finished22:10:38), PID3106750 and own
container085fd3f032d3 gone. Original12:8empty,1length; drop-empty-assistant12:
0empty,3length; HTTP errors0 both. Summary SHA256
6b1792ca263ae85772c7fba264eaa0e6ab782cc8714d29f396e493008e1c10a7 at
/cache/austinov/eval-runs/switch12h-qwen38-history-20260913-UvgopA/probe/summary.json.
Important input-structure evidence, not full quality/correctness or a proven
lossless fix. Cap64 truncations require natural-EOS validation. User was asked
asynchronously whether formal results keep original plus normalized supplement,
uniformly normalize both arms, or original only. No answer received yet; do not
silently replace the original protocol/data. Preserve all original results.
Meanwhile advance original Qwen3-32B control repetition1 using performance mode,
fresh32 validity canary then full357 c1/c16/c5/c8. This model's prior32 canary
passed; does not claim candidate acceptance or complete paired comparison. Run
run_switch_canary.sh qwen3 <fresh-out> performance 1 after fresh resource gate.
No new quality run before this performance stage. Final target remains full
paired three-repeat matrix plus MMLU/GSM8K/HumanEval, not these diagnostics.

LIVE22:01 UTC input-history diagnostic PID3106750 PPID1, container
085fd3f032d3e5465f20434344cb7bd0842cd1fc42a3ce1de57c1703cefb6fa4,
artifact /cache/austinov/eval-runs/switch12h-qwen38-history-20260913-UvgopA.
Started22:01:02 from pushed fa4e082; command history graph on on. Startup
currently running; follow exact PID/container and probe/summary.json, no duplicate.
Fresh gate:8NPUs empty, no physical holders, port10010free, MemAvailable84227468kB,
cooperative lease obtainable; unrelated Maxon4ick bash-only container untouched.
This24-call original/drop-empty-history paired diagnostic does not change the
dataset on disk and does not satisfy original-protocol performance acceptance.

21:59 cache-off diagnostic TERMINAL, finished21:58:22. PID2997867 missing and
exact owned containerbbf30a6eee39 gone.36/36 requests,errors0; greedyA9/12empty,
0length; greedyB9/12empty,1length; official5/12empty,1length. Summary SHA256
98e1f2c6fc89026aeeb45fbd195ea3a7bef9a8645331f24547f60e8ddfe42a67 at
/cache/austinov/eval-runs/switch12h-qwen38-cacheoff-20260913-T4RYhJ/probe/summary.json.
Disabling prefix/state cache alone did not fix empty outputs. Route closed.
Next launcher profile history invokes prepared paired empty-history diagnostic
on frozen12 cases (24 calls), original graph/MMAR-on/cache-on settings restored.
Command run_switch_probe.sh qwen38 <fresh-out> history graph on on. Original
messages versus remove-only-empty-assistant, seed1024, cap64. Do not represent
this changed-input diagnostic as natural-EOS full baseline or business accuracy.
Fresh resources/lease must pass before launch; no other services may be modified.

New data-structure hypothesis21:53:252/357 source requests contain empty
historical assistant messages;105 do not. Original32-row Qwen3.8 canary:
with-empty-history20 =>9empty outputs/11nonempty; without-empty-history12 =>
0empty/12nonempty. Association only, NOT causality. Actual failed samples have
nonempty final user messages; no user content is stored here.
Prepared probe_empty_history.py: paired original vs remove-only-empty-assistant
history for frozen12 diagnostic cases, cap64, original nonempty turns preserved,
separate raw artifacts/hashes. Dependency-free transformation checks passed.
This is NOT original-protocol baseline data and cannot silently replace business
inputs. Needs explicit protocol agreement before any deployment/acceptance use.
Do not launch while cache-off PID2997867/containerbbf30a6eee39 is live; at21:53
it was still compiling. Logs confirm enable_prefix_caching=False. After its
terminal result, if still empty, use baseline graph/MMAR-on/cache-on for a fresh
input-structure diagnostic. Existing current controller must not be edited/restarted.

LIVE21:49 UTC cache-off diagnostic: PID2997867 PPID1, container
bbf30a6eee39d35c709ea63e5d474151c234ffc8f6244cf97d526b8e116ab812,
artifact /cache/austinov/eval-runs/switch12h-qwen38-cacheoff-20260913-T4RYhJ.
Started21:48:28 from pushed e6a13ba, command sampling graph on off. Currently
startup, no diagnostic results yet. Follow exact process/container, do not
duplicate. Fresh gate:8NPUs empty, no physical holders, portfree,
MemAvailable84252136kB, cooperative lease obtainable, sole unrelated running
Maxon4ick container bash/shared-manager only and untouched. Prompt audit JSON
SHA2560deb89459860a2010d1ba42ba45ec8910016f9864cb9e13e0c565037093b5278.
Transient Git push timeout recovered on retry; no TLS/security changes.

Offline prompt identity audit PASSED108 cases from graph/recipe, eager and
MMAR-off runs: native HF template input_ids == actual response.prompt_token_ids
for every case, usage counts match, same messages never changed token sequences.
Artifact /cache/austinov/eval-runs/switch-prompt-audit-NDkmM3/audit.json.
Uses fixed-image tokenizer, no model inference. Initial audit GqpCzf failed
because Transformers returns BatchEncoding; corrected audit extracts input_ids.
This rules out observed frontend token drift, NOT model arithmetic/weight issues.
Next bounded diagnostic isolates prefix/state-cache lifecycle: graph, MMAR-on,
same BF16 weights, same36 sampling requests, but --no-enable-prefix-caching and
corresponding --mamba-cache-mode none. Sixth launcher arg off selects this policy;
command run_switch_probe.sh qwen38 <fresh-out> sampling graph on off. No other
framework edits. This is a cache-policy diagnostic, not an accepted deployment.
If empties remain, close this cache-policy-only fix; do not repeat unchanged.
Require fresh eight-card/port/memory/lease checks before starting. Full baseline
and quality scope remains unchanged; no automatic promotion of diagnostic data.

21:40 MMAR-off diagnostic TERMINAL (finished21:39:28). PID2841060 missing;
exact owned container8d8155054e91 gone.36/36 responses,0HTTP errors. GreedyA:
8/12empty,0length; greedyB:9/12empty,1length; official:8/12empty,0length.
Artifact /cache/austinov/eval-runs/switch12h-qwen38-mmaroff-20260913-oMQll2/probe/summary.json
SHA2566af79439a577c25a3b54e34de033e5fc680687d93c1962d22a62ab6c3b0abcdf.
Image logs explicitly confirmed enable_matmul_allreduce=False. Disabling MMAR
alone is NOT a fix. Do not repeat unchanged MMAR-off/eager/recipe diagnostics.
No active NPU run remains from this lifecycle; recheck physical resources before
next launch. Main performance baseline and full quality remain incomplete.
Next localization should target prompt-to-first-token/prefill behavior rather
than asserting a decode-only root cause. Native rendered token identity versus
chat frontend and prefix/state lifecycle remain unisolated. Use exact image
source, not the newer host checkout, and predeclare one changed hypothesis.

Quality-runner preparation: --tasks mmlu gsm8k expands exactly57 MMLU subjects
plus GSM8K; duplicate tasks rejected. --concurrency1/5/8/16 explicitly forwards
to pinned TemplateAPI.num_concurrent (api_models.py122/182); default remains1.
Protocol metadata saved with results. Full task-construction preflight with8
passed in fixed device-free/network-disabled CPU container:58tasks/15361rows,
artifact /cache/austinov/eval-runs/switch-quality-preflight-nh6rJJ/full/results.json,
SHA25691ca07313559a7e98ac569fd45a4aceea8ab0e942d7f12ff08987001e080c194.
No quality model requests were issued. Concurrent model-scoring still requires
small live validation before full scaling; do not label preflight as accuracy.
At21:39 MMAR-off controller2841060 remains live with31/36 case artifacts.
Official HF model metadata fetch timed out; local weight SHA identities are
complete but independent upstream provenance remains unverified. No weights
downloaded or changed. Local directory has no HF download metadata.

Performance preparation while MMAR diagnostic is live: run_switch_canary.sh now
accepts performance <repeat1|2|3>. It keeps the same owned service/lease, runs
the existing32-row canary first, then run_switch_performance_repeat.py with
full357 cells in boundary-first order1,16,5,8. Each cell has separate warmup,
v4 metrics/raw rows/hashes; error/empty/truncation fails that lifecycle without
discarding prior valid cells. Fresh output is mandatory. This implements ONE
arm/repetition, not the full paired result. Schedule lifecycles Q3/Q38, Q38/Q3,
Q3/Q38 for AB/BA/AB; do not launch while current probe owns cards or before
candidate validity is fixed. Current production launcher still uses MMAR-on;
do not silently adopt the diagnostic configuration. No full matrix ran yet.

LIVE21:29 UTC: MMAR-off graph diagnostic started21:28:53, PID2841060 PPID1,
container8d8155054e910c8c531fd60197b53e412b7cd479c52f471f49b5a8b4de15feac,
artifact /cache/austinov/eval-runs/switch12h-qwen38-mmaroff-20260913-oMQll2.
Code checkpoint942925f pushed. Exact command run_switch_probe.sh qwen38
<artifact> sampling graph off. Startup logs confirm Ascend platform activated;
health and MMAR-off config activation still need confirmation. Follow this job,
do not duplicate. Fresh gate: eight NPUs empty, no physical-device holders,
port10010 free, MemAvailable84251536kB, cooperative lease obtainable; sole
external running container Maxon4ick only bash/shared manager devices, untouched.

21:25 UTC eager diagnostic is TERMINAL (finished21:22:25); PID2665758 and
owned container8ed2453c45d9 are gone. All36 requests executed, HTTP errors0.
Greedy A9/12 empty,1 length; greedy B8/12 empty,0 length; official8/12 empty,
0 length. Summary SHA2562bcddadee9fe8afd5e050b45a61dc21ac1fea7bafc6ec8dc538407c2a3a1de73
under /cache/austinov/eval-runs/switch12h-qwen38-eager-20260913-wvQ790/probe.
Eager did not fix business validity; diagnostic status passed is NOT acceptance.
Read-only fixed-image source confirms non-spec decode calls the same Ascend
custom recurrent op as spec decode; prefill uses chunk_gated_delta_rule and
casts saved state to configured dtype. First-token EOS alone does not establish
decode state precision as root cause. Do not blindly change state precision.
Next bounded hypothesis: enabled MMAR path may affect outputs; compare the same
sampling36 cases with graph mode and only MMAR disabled. Fifth argument of
run_switch_probe.sh selects on(default)/off, setting both additional_config and
environment consistently. Command: qwen38 <fresh-out> sampling graph off.
Acceptance for further validation: no empty/error outputs and reproducible
greedy repeats; truncations still require later natural-EOS canary. This is a
diagnostic, not a new benchmark or proven fix. If empties remain, close this
configuration-only hypothesis without full-matrix expansion. Preserve original
image/weights; exact-owned-container cleanup only. Recheck resources before launch.

LIVE at21:10 UTC: eager diagnostic PID2665758, PPID1; container
8ed2453c45d9f9e4928bf0fe75163ad51bdd8030d2eb88364f6b8be65728b949;
artifact /cache/austinov/eval-runs/switch12h-qwen38-eager-20260913-wvQ790.
Started21:05:52 using94bae36. Logs prove enforce_eager=True and Cudagraph
disabled at21:07:00. Still warming up at21:10, not terminal. Follow exact job;
do not restart based only on shared-memory wait messages.
Complete weight-byte SHA256 manifests now available in this artifact root:
qwen38-weights.sha256 (18 shards), manifest SHA256
a21eacf961df7d6b3009cc6fb43652ba80bfb978b5869fc8a98602ba588f9ff0;
qwen3-weights.sha256 (17 shards), manifest SHA256
845959b3f0be0a6111fc2a646c856fd3d1c728179f6c3946fa4057cde2d70fb5.
Each manifest's complete unique file population matches its model index.
Hasher PID2674267 finished; no errors in weight-hash.log. Low-priority hashing
overlapped startup diagnostics only, not a reported performance run. These bind
local weight bytes; not independent upstream provenance or accuracy proof.

21:03 sampling diagnostic TERMINAL, completed36 requests; own service cleaned.
Artifact /cache/austinov/eval-runs/switch12h-qwen38-sampling-20260913-43OW1b,
probe/summary.json SHA256494c1100be85bd1913bb24617f0c48567d7970e2f9cb37e905371952ffac22ea.
Greedy A:8/12 empty,1 length; greedy B:7/12 empty,1 length; official recipe:
7/12 empty,2 length. Recipe change did not fix business validity. Two greedy
repeats differ on some examples despite same seed; root cause not established.
Successor: same sampling-profile requests with only execution mode changed:
run_switch_probe.sh qwen38 <fresh-out> sampling eager. This selects --enforce-eager
instead of graph compilation settings; all model/data/cache/TP/recipe settings
remain as before. Goal is isolate graph-path involvement, not accept a new
performance baseline. Do not expand full quality before performance validity
issue is resolved; retain every negative result. No external service edits.

CURRENT LIVE RUN at20:56 UTC: sampling diagnostic PID2544764 (PPID1),
container d0468a73dcdc79a8c8078b9f6cf7686b802f2a20ff7067d558c5a2dd3879f04e,
artifact /cache/austinov/eval-runs/switch12h-qwen38-sampling-20260913-43OW1b.
Started20:51:46, still compiling at20:55. Do not duplicate/restart on a wait
warning. Follow probe/summary.json and actual process/container. Source dc5511a.
Same-session config audit: installed editable finder maps vllm_ascend to
/vllm-workspace/vllm-ascend/vllm_ascend, not the host checkout. Installed
ascend_config.py lines354-365 prioritize additional_config. service.live.log
at20:52:53 and20:54:03 explicitly records enable_matmul_allreduce=True and
enable_flashcomm1=False. Core unknown-env warnings do NOT prove these settings
are ignored. No framework edits were made; current measured configuration stays
unchanged. Do not use host checkout's newer deprecation behavior as image truth.

20:47 quality API canary PASSED; PID2430859 terminal, owned container cleaned.
Artifact /cache/austinov/eval-runs/switch12h-qwen38-quality-fixed-20260913-9ryELw:
quality-canary/results.json SHA256f9b5c168f5de78f6394ea0201ae74b744e64005742fca7a02131e8fa8bfa5651.
MMLU abstract_algebra1/2, GSM8K strict/flexible2/2. Scoring plumbing only, NOT
overall accuracy. Return to performance blocker before full quality expansion.
Push recovered; dd0f32a includes HumanEval prep and CPU evaluator backend fix.
Next: run_switch_probe.sh qwen38 <fresh-out> sampling, all9 empty plus3 nonempty
controls, two greedy repeats and official nonthinking recipe (temp0.7/top_p0.8/
top_k20/presence1.5), cap256. Joint recipe diagnosis, not single-factor causality
or a replacement baseline. Reference local model README lines252-253/502-503.
Preserve truncation and empty outputs; any new deployment recipe requires its
own matched control and validation. User asks fixing problems and continuing,
not casually stopping the overall task. Keep original framework untouched.

20:34 correction: quality controller2336761 is TERMINAL, failed20:31:59 before
model requests. CPU-only evaluator AutoTokenizer import auto-loaded torch_npu
and failed backend initialization. Owned server was cleaned up. See XJ5TBA
quality-canary.log; no quality scores exist from this attempt. Successor changes
only CPU evaluator environment TORCH_DEVICE_BACKEND_AUTOLOAD=0. Actual
NoThinkingCompletions/tokenizer/payload test passed in otherwise matching
device-free network-disabled container (exec-0000000000000024). Do not apply
this environment setting to the NPU server. A fresh live scoring retry is next.
HumanEval prep commit1ed70b7 push encountered slow transfer then an HTTPS
authentication failure; retain local checkpoint and retry without exposing
credentials or disabling TLS. Earlier e34c878/01c28d3 are pushed.

HumanEval generation preparation: run_switch_humaneval.py implements pinned
v0.4.13 humaneval_instruct user prompt and assistant gen_prefix, native local
no-thinking continuation, temperature0/seed1024/max1024, upstream stop strings
and first-fence extraction. It writes raw per-item request/response plus hashes
and samples.jsonl; executes NO generated code. Feed samples only to existing
run_humaneval_sandbox.sh, then paired scoring. Full164 candidate tokenizer
render preflight passed in fixed network-disabled/device-free container
(exec-0000000000000021). This is NOT model generation or accuracy evidence.
Endpoint argument is the full /v1/completions URL. Fresh output directories
prevent overwriting prior evidence. Integration and real generation remain next.

CURRENT RUN 20:26 UTC: standalone quality controller PID2336761, PPID1,
container85e23ed6b56477d575bdbcc7e357f188250ab798e6f8cee5ed3580ea2829adb1,
artifact /cache/austinov/eval-runs/switch12h-qwen38-quality-20260913-XJ5TBA.
Command run_switch_canary.sh qwen38 <artifact> quality. Follow this exact job;
do not launch another service. Source checkpoint e34c878 adds isolated CPU
evaluator against owned TP8 server: MMLU abstract_algebra and GSM8K, limit2 each,
then exact-container cleanup. This validates scoring plumbing, not full accuracy.
Next must inspect quality-canary/results.json and logs, then scale to full tasks
and pair Qwen3 control; HumanEval and performance matrix remain required.
Prelaunch verified eight NPUs empty, no physical-device fuser holders, portfree,
MemAvailable84224300kB. Remaining Maxon4ick container only bash, shared manager
devices, no physical0-7 declarations. It was not changed.

Empty-output diagnostic finished20:22:02 and its container is gone. All three
empty cases1/2/5 reproduce first-token EOS248046 under nonstream/special-token
visibility. Summary SHA25641c5fe42864145239819c212289319480cfbe43e7f41b56a729ffabe14a9f0f3
under /cache/austinov/eval-runs/switch12h-qwen38-probe-20260913-Smh123/probe.
Diagnostic state passed means the probe executed, NOT business validity passed.
Nonempty control0 differs between variants (8vs12 tokens), so do not infer
deterministic equivalence or a root cause from these diagnostics alone.

20:22 diagnostic partial evidence: indices1/2 nonstream remain empty; visible
token IDs are [248046]. Local tokenizer_config identifies248046 as<|im_end|>,
and generation_config lists it as EOS. Thus these cases emit EOS as first token,
not a streaming-client omission. ignore_eos continues role-delimiter tokens;
it is diagnostic only, not a fix or quality result. Probe still running, do not
restart. Remaining case results and underlying model/template/runtime cause
are not yet determined.
Added run_standard_text_quality.py for exact upstream MMLU subjects/GSM8K,
local custom datasets, native no-thinking templates and seed1024 payloads.
Device-free fixed-image task-construction preflight passed for abstract_algebra
and GSM8K (exec-0000000000000012). No live model scoring is claimed; next gate
is a tiny API/scoring run after the current diagnostic finishes. HumanEval
generation/execution remains separate. Never pool preflight with model accuracy.

LATEST LIVE CHECKPOINT 20:17 UTC (supersedes running states below): Qwen3-32B
resumed control completed at20:12:57, passed request validity:32/32, errors0,
empty0, stop32, reasoning0, prompt-token mismatches0. c1 TTFT P95=376.284524ms,
TPOT P95=52.319630ms/token. This is a32-request canary, NOT full357 baseline
or semantic quality acceptance. Artifact:
/cache/austinov/eval-runs/switch12h-qwen3-resume-20260913-N4hS5H
canary.json SHA256 f88409839aa141e1636e0607a97615827a529fcc9105077e6a2d1c85772d1e6f
canary.rows.jsonl SHA256 c658180b8d1cfdf59aab0ee6c5cbc8efaa92bbe2309b7f28a883e5ebcf8663ba
Its controller2187839 and container715dd4c2360d are finished, not live.
Successor queue PID2224697 was verified live with PPID1; it started the existing
diagnostic container5250eac96940 at20:13. Artifact:
/cache/austinov/eval-runs/switch12h-qwen38-probe-20260913-Smh123
At20:17 weights were loaded and graph compilation underway. Follow this exact
queue/container and probe/summary.json; do not duplicate or restart on stale
status alone. Full MMLU/GSM8K/HumanEval model scoring and the repeated357 matrix
remain outstanding. Request validity success is not a semantic accuracy score.

LATEST LIVE CHECKPOINT 20:09 UTC: first Qwen3.8 canary completed32/32, errors0,
stop32, but9 empty outputs. Every empty response has usage completion_tokens=1;
raw SSE contains only empty role/finish and usage events. Not a missed visible
content field; EOS identity still needs nonstream/visible-special-token diagnosis.
Artifact /cache/austinov/eval-runs/switch12h-qwen38-20260913-fRMUzD:
canary.json SHA2569942a2f2513e47e620fe1ba2294f593a1e2b6be14bd3db3abf7708fba4939ecd;
rows SHA256e7da12ab6aec052e3e4d7a875d7f563142b0e1c8680784b268bc477f81969a4e.
This failed canary must not be treated as accepted full performance evidence.

The initial Qwen3 controller exec-0000000000000beb was lost during observed
gateway availability changes. Host verified no controller/container and log
Terminated; /switch12h-qwen3-20260913-mGp54E/status.json is stale, not running.
Restarted safely with nohup+setsid after resource checks; actual live controller
PID2187839, PPID1, SID2187839, container715dd4c2360d, artifact
/cache/austinov/eval-runs/switch12h-qwen3-resume-20260913-N4hS5H. Check exact
process cmdline/container/status rather than relying on resettable gateway exec IDs.
At20:09 it was loading17 model shards. Do not duplicate this run.
Prepared queue_switch_probe.sh to follow that exact controller, then run a fresh
Qwen3.8 diagnostic on3 observed empty examples and1 nonempty control, each with
nonstream, visible-special-token and ignore_eos16 variants. Last variant is
diagnostic ONLY, never quality/performance evidence. Inputs/outputs stay outside Git.

LATEST RESOURCE AUTHORITY / DEADLINE: user explicitly authorized stopping
qwen35_t37_pa_workspace_service_v1 and other containers proven to interfere with
this test. This supersedes earlier never-stop-external-container wording only
for conflicting containers, not unrelated services or arbitrary host processes.
Preserve inspect/logs, stop exact IDs, do not delete model/source/bind-mounted data.
Deadline for an evidence-backed result: 2026-09-14 07:40 UTC (12 hours from request).
Report completed results and explicit missing gates by then; never call partial
coverage complete. Continue full objective, not just the canary.
Stopped exact container 58dfe81c55e6a66d1ec377422c04443c822698c0ef5146473de5d2de682fac2b;
it auto-removed by its original --rm policy. Logs/inspect/diff saved under
/cache/austinov/eval-runs/switch-takeover-20260913-POeM1v. Eight NPUs and port10010
were verified released afterward. Maxon4ick_torch_910_dev was not stopped.
Use run_switch_canary.sh for fresh exact-ID-owned lifecycle and protected mounts.
ACTIVE RUN: exec-0000000000000be5, artifact directory
/cache/austinov/eval-runs/switch12h-qwen38-20260913-fRMUzD,
container prefix568af23e3ca3, startup at2026-09-13T19:45:17Z. Poll this exact
operation and status/service.live.log; do not start a duplicate on observation
timeout. Script runs Qwen3.8 TP8/DP1 BF16 then32 request canary and cleans up only
its exact container ID. This is not yet a completed canary or performance result.
Heartbeat qwen3-8 now runs every15minutes with the latest conflict-stop authority
and12-hour report deadline. Next arm is Qwen3-32B after this operation is terminal.

User now explicitly requests trustworthy continued testing to decide whether to
switch to Qwen3.8-27B. Current pair: Qwen3-32B BF16 vs Qwen3.8-27B BF16.
This supersedes the earlier Qwen3.5 correction below. Use SWITCH_VALIDATION.md.
The original NVFP4 QUALITY_PROTOCOL.md is historical, not this switch contract.

Resource gate now BLOCKS launch (exec-0000000000000bcf and subsequent inspect):
qwen35_t37_pa_workspace_service_v1 owns devices0-3, with VLLMWorker_TP PIDs
1735149/1735151/1735153/1735154. Port10010 is held by vllm PID1722640.
MemAvailable64578876kB. No external workload was changed. No lease acquired.
App heartbeat qwen3-8 is ACTIVE every30minutes for this task; unchanged blocked
resource state stays quiet. It must follow existing live jobs, never double-launch.
SSE timing/output guard dependency-free tests passed; MST26skills passed.

Historical chat sentinel has 92/357 empty candidate outputs despite status=valid.
That is not a business-valid run. v3 counts finish-only events as first token.
New chat_benchmark.py v4 fixes that, keeps raw SSE and response text outside Git,
marks one-token TPOT undefined, and rejects empty, whitespace-only, truncated or
reasoning-bearing output. Do not pool v3/v4 timings. Next gate: paired 32-request
diagnostic, not an unchanged full matrix.

Executable lm-eval text-task construction passed in the offline CPU-only image:
exec-0000000000000bc2, 58 tasks, 15361 rows, known-right/wrong MMLU scored 1/0.
HumanEval runtime scoring is separate and not proven by that test.
Prior checkpoint 6b5e8b6 is now pushed.

Latest offline scoring gates: HumanEval164 canonical solutions all passed;
164 intentional RuntimeError completions all failed in the existing restricted
CPU sandbox (exec-0000000000000bd4). evaluator-preflight-evidence.json contains
input/output/evaluator hashes; this is not model accuracy. Added external
NoThinkingCompletions evaluator subclass because upstream template rendering
does not forward enable_thinking. Actual tokenizers for Qwen3 and Qwen3.8 passed
no-thinking/continuation/tokenized payload checks (exec-0000000000000bdb).
The first import probe failed due missing PYTHONPATH, fixed by mounting and
selecting the pinned harness source; no package or framework installation.
Next: live paired32 chat diagnostic and a small MMLU/GSM8K API scoring canary
once the eight-card resource gate permits. No new model inference ran here.

### Superseded Qwen3.5 correction and preserved audit

Latest checkpoint: see `qwen38-nvfp4-ascend/BASELINE_REUSE.md` for the audited
Qwen3-32B c1/c5/c8 repeat-1 cells, hashes, truncation exceptions and conditional
reuse rules. Do not discard valid cells because their parent controller failed.
Offline standard-task data preflight now passes in the fixed device-free,
network-disabled container: 59 configs / 15525 test rows. HumanEval function
resolution is deliberately disabled for this inspection because upstream utils
runs a code_eval sample at import time. Executable evaluator wiring and scoring
remain incomplete; this is not a quality-score result. No NPU lease was taken.

Identity audit: /cache/austinov/Qwen3.8-27B has a Qwen3.8 model card and
config SHA256 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab.
Its qwen3_5 architecture does NOT identify it as Qwen3.5 weights. Exclude those
historical candidate results from the requested Qwen3.5 switch decision.
The local Qwen3.5 candidate is /cache/efim/Qwen3.5-27B, with a matching model
card, 11 visible safetensor shards, and config SHA256
f8d190c5b89c1521220f935d2567a587d6e291ed69066a45a106560b05a2174c.
Full shard/index and upstream provenance validation is still required.
Qwen3-32B control at /cache/austinov/Qwen3-32B has config SHA256
97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb.

Resource observation at 2026-09-13 18:42 UTC: NPU0-7 report no processes;
fuser reports no holders of davinci0-7; port 10010 is free; MemAvailable is
84210248 kB. The sole running Maxon4ick_torch_910_dev container is privileged
and docker top shows only bash. This is a point-in-time observation, not an
acquired lease. User requires eight-card exclusive operation: stop this task's
launch/measurement if another owner uses any card, never stop their workload.

The current business decision is whether to switch Qwen3-32B BF16 to
Qwen3.5-27B BF16 under vLLM-Ascend. NVFP4 exploration is paused. The directory
and branch names are historical and intentionally retained to avoid creating
another worktree. Do not treat an automated old objective as a new model choice.

Acceptance needs matched query_rewrite c1/c5/c8/c16 repeated performance,
MMLU, GSM8K and HumanEval scores, plus output-length and business-quality
context. Verify actual model/checkpoint identity; a Qwen3.8-labelled path and
a Qwen3.5 served alias alone prove neither identity. Historical TP8/DP1 data
must not be represented as TP4/DP2. Preserve the original official image.

Existing artifact roots to audit before rerunning:
- /cache/austinov/eval-runs/qwen3-32b-comparison
- /cache/austinov/eval-runs/qwen-switch-chat-natural-eos-gate1b
- /cache/austinov/eval-runs/qwen38-tp8-full-baseline

The standard-quality controller failed loading cais/mmlu over an unavailable
network. Local datasets exist. offline_standard_data.py now provides local
lm-eval custom_dataset callables without changing prompts or scoring. Host
data validation passed: MMLU 57 subjects/14042 test/285 dev, GSM8K 7473 train/
1319 test, HumanEval 164 unique tasks; malformed subject paths are rejected.
This is data-layer validation only: task wiring and datasets-library execution
still need testing, then serving/quality gates. No model test was launched.

All status, resource assignments and next actions below are historical unless
revalidated against this corrected goal and live ownership.

## Status

- Dedicated worktree: `/opt/host/vnf/austinov/worktrees/qwen38-nvfp4-ascend-910b4`.
- At 2026-09-10T17:09:35Z the live gates changed to available: NPU0-7 had no
  processes, Docker had no running containers, port 10110 was free, and
  MemAvailable was 81,485,876 kB. The current workstream may use physical
  NPU0-3 for its exact disposable-container lifetime; NPU4-7 remain protected.
  Re-prove all of these immediately before launch.
- The mandatory pre-launch recheck at 2026-09-10T17:18:37Z found 81 retained
  Docker containers declaring one or more of physical NPU0-3: 79 are exited
  and 2 are created. Although no container is running and NPU0-7 have no
  process, the user's explicit gate rejects any external container device
  declaration. No service was started and no container was stopped, removed,
  or modified.
- The fixed image's vLLM core can parse this official checkpoint through
  `modelopt_mixed` and already handles its Qwen3.5 prefix aliases. Do not
  translate it into the separate ModelSlim `quant_model_description.json`
  format.
- The actual blocker is that the Ascend platform does not list
  `modelopt_mixed` as supported, and vLLM core's selected per-layer methods are
  GPU implementations rather than Ascend execution methods.
- The checkpoint is mixed precision: 193 dense NVFP4 layers at group size 16
  and 208 FP8 layers. The fixed image registers `W4A16_MXFP4` only for MoE and
  defaults that path to group size 32; no dense group-16 registration exists.
- ops-transformer contains useful E2M1/A16F4 source, but it is not proof of
  910B4 support: FP4-specific kernels are under `arch35`, and the per-group
  checker accepts only 32/64/128/256 while this checkpoint requires 16.
- A device-free, network-disabled build probe in the fixed image selected the
  real top-level `matmul_all_reduce` target for `ascend910b`. Configuration,
  host/arch22 tiling compilation, and 298 kernel objects succeeded before the
  deliberately bounded probe was stopped. The op contract explicitly says
  FP8/FP4 support is new on Ascend 950 and requires antiquant group sizes that
  are multiples of 32. This closes direct reuse for the checkpoint's group-16
  NVFP4 tensors; it is not an NPU execution or speed result.
- A dependency-free exact-format reference codec and tests are now present.
- A separately installable vLLM general plugin now registers
  `modelopt_mixed_ascend_bf16_reference`. It preserves core ModelOpt layer
  resolution, reconstructs NVFP4/FP8 weights with per-fused-shard scales, uses
  BF16 linear compute, and refuses construction unless the explicit reference
  opt-in is set. It does not emulate activation quantization and is therefore
  an integration/quality upper-bound reference, not the final quantized path.
- The reference test passed both on the host and in a network-disabled,
  device-free, disposable `quay.io/ascend/vllm-ascend:v0.23.0` container.
- The fixed image itself contains CANN 9.1.0, Bisheng, ATC, OPP, msprof and
  cannsim. A read-only CANNBot environment check passed inside a disposable
  container, so it can also be used as the isolated build environment.
- The exact official snapshot is complete at
  `/cache/cch/Qwen3.8-27B-NVFP4`. All three shards have recorded SHA256
  identities in `checkpoint-evidence.json`.
- The BF16 control is complete at `/cache/austinov/Qwen3.8-27B`: all 18
  safetensor shards are present (55,563,006,776 bytes), its architecture is
  `Qwen3_5ForConditionalGeneration`, and it has no quantization config.
- A fail-closed checkpoint inspector passes host and fixed-image tests.
- Representative rows from all three shards were independently decoded against
  NVIDIA ModelOpt commit
  `079078de9d3cd26fa5baafdb754bba29dde24f7d`: all 15,360 sampled values
  matched exactly (maximum absolute error `0.0`). Together with the full
  checkpoint inspector, this verifies the packed-nibble, finite-E4M3 local
  scale, FP32 global scale, and group-16 storage contract. It does not yet
  prove end-to-end model accuracy.
- The checkpoint inspector now also validates every FP8 layer's rank-2
  `F8_E4M3` weight plus scalar FP32 `input_scale` and `weight_scale`. All 208
  FP8 layers pass, so all 401 mixed-precision layer declarations now have a
  checked tensor-storage contract. This still does not validate an Ascend FP8
  execution path.
- A proposed `nvfp4_group16_matmul` L0 operator contract now exists under
  `qwen38-nvfp4-ascend/operator/`. CANNBot strict validation passes stages
  1-7 with no warnings. Stages 8-11 are explicitly skipped because the current
  formula harness cannot preserve relational `K:K/2:K/16` symbolic shapes;
  executable tensor truth remains covered by `validate_real_tensor.py`.
- The contract correctly exposes finite-E4M3 checkpoint data as raw `uint8`
  bytes because Ascend 910B4 has no native FP8 dtype. It does not claim native
  FP8 hardware support.
- No NPU kernel, performance result, or accuracy result is claimed yet.
- The quality protocol is now frozen in `QUALITY_PROTOCOL.md`. Stable request
  manifests were generated for 57-subject MMLU (14,042 tests), GSM8K (1,319),
  and HumanEval (164), with source/output SHA256 identities recorded in
  `quality-protocol-evidence.json`. Strict MMLU/GSM8K paired scoring code and
  fixed-image unit tests pass. Generated artifacts remain ignored by Git.
- The old eight-device DP2 launcher has been removed. Matched launchers now
  expose only physical NPU0-3 and use TP4: `start_bf16_tp4.sh` for the control
  and `start_nvfp4_reference_tp4.sh` for the external reference plugin. Model
  and plugin mounts are read-only; candidate installation is confined to its
  disposable container layer. Shell syntax validation passes, but neither
  launcher has been executed while the lease is unavailable.
- Tokenizer audit found byte-identical `tokenizer.json` and
  `chat_template.jinja`, but different `tokenizer_config.json` defaults,
  including the pad token. Both launchers therefore explicitly mount the BF16
  tokenizer read-only at `/tokenizer` and pass `--tokenizer /tokenizer`.
- A resumable OpenAI-compatible quality request runner now renders each chat
  prompt locally with that tokenizer, records its SHA256, appends the full raw
  response, and fails fast on request error. Its fixed-image unit tests pass;
  it has not sent model requests while NPU0-3 are unavailable.
- HumanEval is now executable only through a bounded CPU sandbox: no network,
  read-only root, no capabilities, no privilege escalation, and explicit CPU,
  memory, PID and per-test limits. The shared evaluator is mounted read-only;
  its recognized execution guard is validated in a temporary copy. The
  official example executed six completions and correctly separated three
  passes from three failures/timeouts (pass@1 0.5). Full response preparation
  and paired 164-task pass@1 comparison code has fixed-image unit coverage.

## Current blockers

1. The earlier NPU0-3 process occupancy has cleared, but 81 retained containers
   still declare NPU0-3 (79 exited, 2 created). Under the explicit gate, the
   NPU0-3 lease is not obtainable. Do not start, stop, remove, or modify any
   container. Wait for owner cleanup or an explicit operator decision that
   narrows the declaration gate, then re-audit. NPU4-7 remain protected.
2. The fixed image now has a device-free validated external, fail-closed
   ModelOpt BF16 reference adapter, but it has not passed a four-rank model
   startup. Native or faithfully emulated activation quantization is still
   required before claiming the official NVFP4/FP8 runtime semantics.
   Native reuse of the ops-transformer FP4 path is closed for 910B4/group16.
   The next correctness-first implementation is exact ModelOpt NVFP4 and FP8
   decoding to BF16 weights at load time. That path can establish checkpoint
   semantics and full-model quality but must be labelled a BF16-compute
   fallback, not native quantized acceleration. A later 910B4 stream-dequant
   kernel is eligible only after this reference path passes.
3. Two pushes of the latest local commits failed with a transient GitHub TLS
   receive error. The commits and unpushed operator spec remain safe locally;
   retry without rewriting history.

## Next actions

1. On the next valid NPU0-3 lease, start the BF16 control with TP4 in a fresh
   disposable container and record four-rank activation, load time and memory.
2. Then start the BF16-compute reference plugin
   through a read-only mount and disposable installation. Require four-rank
   activation and record load-time plus per-rank memory before any request.
3. Run deterministic smoke and a small paired quality canary. Label these
   results as weight-fidelity BF16-compute reference results because activation
   quantization is not yet emulated.
4. Only after the reference adapter passes, evaluate a 910B4 group-16
   stream-dequant + BF16 Cube operator against it; do not port arch35 code.
5. Integrate through a read-only mounted plugin in a
   fresh disposable container and run BF16/NVFP4 paired performance and quality.

## Verified operations

- Chip detection: `exec-0000000000001385`, DCMI `Ascend910B4`.
- Host reference codec: `exec-0000000000001386`, pass.
- Fixed-image device-free codec: `exec-000000000000138c`, pass.
- Fixed-image CANNBot environment: CANN 9.1.0, pass with one non-blocking
  runtime-library-path warning.
- Checkpoint inspector host and fixed-image tests: pass.
- Complete official checkpoint contract: `exec-00000000000013df`; 3/3 shards,
  2,194 tensors, all 193 NVFP4 layers validated with zero ABI errors.
- Representative real rows from all three shards:
  `exec-00000000000013e3`, `exec-00000000000013e4`, and
  `exec-00000000000013e5`; 15,360 decoded values total, exact matches,
  maximum absolute error `0.0`.
- Checkpoint SHA256 manifest: `exec-00000000000013e6`; recorded in
  `checkpoint-evidence.json`.
- CANNBot strict L0 spec validation: `exec-000000000000001c`; stages 1-7
  PASS, stages 8-11 explicit SKIP for the documented relational-shape harness
  limitation, zero warnings and zero failures.
- Real `lm_head.weight` row-0 ModelOpt cross-check:
  `exec-00000000000013cd`, exact match, maximum absolute error `0.0`,
  packed-row SHA256
  `31c1dd3c007d2daca930d927d6217ade2a96ba42826bfd3ae8073c22d7f0c4d7`.
- Fixed-image ModelSlim/registry/API audit:
  `exec-000000000000003a` through `exec-0000000000000045`; recorded in
  `runtime-compatibility-evidence.json`. It proves that an external execution
  method adapter and dense group-16 scheme are required. It is device-free evidence,
  not an NPU support or speed claim.
- Mixed NVFP4/FP8 checkpoint inspector: host `exec-000000000000004b` and
  fixed-image read-only mount `exec-000000000000004d`; 193/193 NVFP4 and
  208/208 FP8 layers passed with zero tensor-contract errors.
- Fixed-image `torch_npu` public API contract and ops-transformer source audit:
  `exec-0000000000000064`, `exec-0000000000000066` through
  `exec-0000000000000069`. A2 documentation does not establish FP8/FP4
  `npu_quant_matmul`; ops-transformer group-16/910B4 capability remains
  unproven and must be probed rather than assumed.
- Offline ascend910b build probe: dependency discovery
  `exec-00000000000000d6`; real top-level build
  `exec-00000000000000f5`; bounded stop of the exact disposable container
  `exec-000000000000011a`; source identities and post-build inspection
  `exec-000000000000011e`. Configuration and arch22 host compilation passed,
  298 kernel objects were generated, and no full-build or FP4 capability claim
  is made.
- BF16 reference adapter tests: unit/load-after-process
  `exec-000000000000013a` (7/7 pass); real checkpoint NVFP4 and FP8 rows
  `exec-0000000000000136` (5120 and 6144 values, exact); standard package
  install and vLLM entry-point discovery `exec-0000000000000134`; all 401
  official layer mappings `exec-000000000000013b` (193 NVFP4, 208 FP8).
  Detailed evidence and preserved development failures are in
  `reference-adapter-evidence.json`.
- BF16 control and local evaluation data discovery: `exec-0000000000000148`,
  `exec-0000000000000147`, and dataset structure/count audit
  `exec-0000000000000149` through `exec-000000000000014a`.
- Frozen full quality manifests: `exec-000000000000014e`; fixed-image,
  network-disabled, device-free tests: `exec-000000000000014f` and
  `exec-0000000000000151`. See `quality-protocol-evidence.json`.
- Four-device TP4 launcher syntax validation: `exec-0000000000000159`, pass.
- Paired tokenizer identity/default audit: `exec-0000000000000161` and
  `exec-0000000000000162`.
- Quality request runner fixed-image, device-free tests:
  `exec-0000000000000163` (2/2 pass); updated launcher syntax validation:
  `exec-0000000000000164`.
- HumanEval sandbox development failures before execution or due input naming:
  `exec-0000000000000002`, `exec-0000000000000003`, and
  `exec-0000000000000008`; all are preserved in
  `quality-protocol-evidence.json`. Successful functional smoke:
  `exec-000000000000000c`, 3/6 pass and pass@1 0.5; result artifact SHA256
  `9e47a72acc1ffe3440a15f000f54a7b56233d34c8347a8085c728a52e2673db3`.
  HumanEval preparation/scorer unit tests: `exec-0000000000000017`, 4/4 pass.
- Available-resource snapshot: `exec-0000000000000024` through
  `exec-0000000000000027`; competing worktree/resource-claim audit:
  `exec-000000000000002a`. No running containers or NPU processes, port 10110
  free, MemAvailable 81,485,876 kB. The Qwen3.5 workstream's claim is
  conditional on its own live lease and has no live process/container; this
  workstream now owns the next exact NPU0-3 disposable-container lifetime.
- Mandatory declaration recheck: NPU state `exec-000000000000003a`, running
  containers `exec-0000000000000036`, all retained containers
  `exec-0000000000000039`, exact NPU0-3 declaration list
  `exec-0000000000000040`, and count `exec-0000000000000042`. The result
  supersedes the earlier lease interpretation: 81 retained declarations block
  startup under the user's stated gate.
- Whitespace/error check: `exec-0000000000001387`, pass.
- Live resource audit: `exec-000000000000138a` and
  `exec-000000000000138b`; NPU0-3 unavailable.

## Safety

Do not modify the fixed image, site-packages, host framework sources, external
containers, or NPU4-7. Store raw datasets, weights and runtime artifacts outside
Git and commit only code, protocols, manifests and summarized evidence.
