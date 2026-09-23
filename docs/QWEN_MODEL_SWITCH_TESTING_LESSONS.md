# Qwen model-switch benchmark: maintainer lessons and trusted test gates

This runbook captures the successful patterns, failure modes, and evidence gates learned while evaluating whether a production Qwen3-32B deployment should move to Qwen3.8-27B on Ascend/vLLM. Its main goal is to prevent expensive but non-actionable benchmark runs: protocol credibility must be proven before long performance or quality matrices are allowed to consume hours of NPU time.

## Decision boundary

A model-switch benchmark is not a race to produce the largest throughput number. A production switch recommendation needs evidence in five separate layers:

1. **Real Natural-EOS user experience**: E2E latency, request throughput, success/error behavior, and stability across concurrency.
2. **Pure inference performance**: TTFT for prefill/first-token behavior, TPOT and output-token throughput for decode behavior.
3. **Output-length and termination behavior**: completion-token distribution, `stop`/`length`, empty/near-empty outputs, and pathological tails.
4. **Reference-backed quality**: LongBench-v2, GSM8K, or an equivalent task with real reference answers.
5. **Operational stability**: service health, timeout/failure behavior, NPU resource state, long-running stability, and clean recovery.

Do not collapse these into one score. In particular, if a candidate finishes sooner mainly because it emits fewer tokens or terminates earlier, report that as **earlier termination / shorter output**, not as a faster inference engine.

For latency decisions, use **p95 as the primary metric**. Report p50 for typical experience and p99/max for pathological tails. Means alone are not sufficient.

## What worked well

### Fail closed before recovery

Before restarting any benchmark controller or model service, verify all of the following:

- no old controller is still alive;
- no same-name container is running or left in an unsafe state;
- the serving port is free and not owned by another workload;
- NPU0-7 are free of non-task workers;
- model, image, dataset, runner, and evaluator identities match the frozen record;
- already completed and audit-valid cells/runs are preserved and skipped.

Only recover from a known, frozen controller or run script. Never modify raw result files to make an audit pass.

### Separate benchmark validity from model behavior

Transport success is not the same as useful model behavior. A cell can be 357/357, zero errors, and all `finish_reason=stop` while still containing suspicious empty outputs or extremely long responses. Record these behaviors explicitly instead of hiding them inside an overall throughput number.

### Use a staged admission pipeline

The most effective anti-waste pattern was:

1. **Identity gate**: freeze model/image/data/runner/evaluator/protocol identity.
2. **Cheap smoke**: small request set through the exact production-representative endpoint.
3. **Warmup + compile quiescence**: exercise the measured concurrency first, wait for JIT/compiler activity to become quiet, then measure.
4. **Full-dataset sentinel**: run all 357 query-rewrite requests once at a representative concurrency before allowing a full matrix.
5. **Early quality screen**: run the minimum reference-backed quality test needed to determine whether the candidate is still credible.
6. **Full matrix only for a credible Go candidate**: 1/5/8/16 x3 and full quality repetitions only after earlier gates pass.

This asymmetry is intentional: the evidence burden for recommending a production switch is higher than the evidence burden for concluding that a candidate should not replace the incumbent.

### Keep performance and quality independent

The frozen `query_rewrite.jsonl` workload contains 357 rows whose `answer` fields are empty. It is valid for latency, throughput, termination behavior, and paired-output stability. It is **not an accuracy oracle** and must never be presented as reference-backed quality evidence.

Quality must come from datasets with real references, such as LongBench-v2 and GSM8K, using a frozen evaluator, data SHA, decode configuration, and auditable per-run results.

## Failure modes and misclassifications

### 1. `all stop` was too strict for the original Natural-EOS path

An early validator treated any `finish_reason=length` as a failed cell. This misclassified a very small number of legitimate context-limit events as whole-cell failures.

The safer rule is explicit: distinguish natural `stop` from bounded context-limit exceptions, record exceptions separately, and never relabel `length` as Natural EOS. A context-limit event is a model/runtime behavior to audit, not a reason to rewrite raw results.

### 2. Shorter output was almost mistaken for a faster engine

Request/s and E2E can improve simply because a model emits fewer tokens. Always report TTFT, TPOT/output tok/s, E2E/request throughput, and completion-token distribution separately.

Correct wording when applicable:

> The candidate ends earlier / emits less on this workload, therefore requests complete faster.

Do not replace that with “the inference engine is faster” unless TTFT/TPOT/output-token evidence supports the claim.

### 3. Pre-rendered `/v1/completions` was not production-representative no-thinking evidence

The initial performance runner sent already-rendered ChatML strings to `/v1/completions`. Although the service had `enable_thinking=false` in default chat-template kwargs, that setting only applies when the server renders a chat template. It is not automatically applied to a fully rendered completion prompt.

Those old results remain useful diagnostic evidence, but they must not be used as the sole basis for a production switch when production uses `/v1/chat/completions` with explicit thinking control.

The corrected path is `/v1/chat/completions` with per-request `chat_template_kwargs.enable_thinking=false`, plus a tokenization cross-check between `/tokenize` and completion usage.

### 4. `0 error + stop` can still hide empty-output behavior

Qwen3.8 consistently produced a substantial number of empty-content responses on the query-rewrite workload. Because the workload's reference answers are also empty, these cannot be classified as accuracy failures from this dataset alone. They must instead be tracked as a model-behavior signal and evaluated against business semantics or reference-backed tasks.

Do not silently convert empty content into a transport error; do not silently ignore it either.

### 5. Cold-start/JIT compilation polluted TTFT and TPOT

The first measured concurrency shapes triggered compiler activity (`bisheng`, `hivmc`, `clang`), causing tens of seconds of apparent TTFT and extreme TPOT values. Those values were not steady-state inference latency.

The fix is to warm the exact endpoint, model, request set, and concurrency first; wait until compile processes are quiescent; only then begin the measured pass. Cold-start/compile cost may be reported separately if production startup latency is a decision criterion.

### 6. Remote executor timeout killed a long controller

A long benchmark controller launched under a remote executor with a 30-second timeout was terminated even though the benchmark itself was healthy. This also prevented normal trap-based cleanup from completing.

For long controllers, use a persistent launcher (`nohup`/`setsid` or an equivalent supervised process), record the controller PID, and confirm that it survives independently of the command transport. If a launcher interruption occurs, re-check containers, port ownership, NPU workers, and DRRQR before restarting.

### 7. Mutable status files should not be treated as immutable evidence

`status.json` can legitimately change after result files are generated. A global `SHA256SUMS` file that includes mutable status can therefore show a mismatch even when result JSONL/summary/audit artifacts are intact.

Freeze and verify the artifacts that actually establish evidence: evaluator/data/model/runner identity, raw result rows, summaries, audits, and protocol manifests. Treat mutable status/heartbeat files separately.

## Corrected chat-path sentinel: diagnostic facts

The following values came from a corrected `/v1/chat/completions` sentinel with explicit `enable_thinking=false`, BF16 TP8, the frozen 357-row query-rewrite dataset, and all requests completing with `stop`. They are **single-sentinel evidence, not a three-repeat final benchmark**.

| Metric | Qwen3-32B | Qwen3.8-27B |
| --- | ---: | ---: |
| Requests | 357/357 | 357/357 |
| Errors | 0 | 0 |
| TTFT p95 | ~0.901 s | ~14.001 s |
| TPOT p95 | ~141 ms | ~342 ms |
| E2E p95 | ~4.78 s | ~91.3 s |
| Request throughput | ~2.55 req/s | ~0.300 req/s |
| Output throughput | ~59.1 tok/s | ~48.7 tok/s |
| Completion tokens | 8,276 | 58,095 |
| Empty-content responses | 0/357 | 92/357 |

Interpretation: this sentinel is a strong No-Go signal for a direct switch, because the candidate is worse not only in total completion time but also in TTFT, TPOT, and output-token throughput, while generating far more tokens and a high empty-output rate. It still does not replace repeated performance evidence or reference-backed quality evidence if a formal Go decision is required.

## Trusted test gates for future model-switch work

### Gate 0: identity and environment

Record and verify:

- actual model path/checkpoint identity, not only the served alias;
- image digest and vLLM/vLLM-Ascend version;
- dtype, TP/DP/PP, seed, context length, and model-specific serving options;
- dataset paths, row counts, and SHA256;
- runner/evaluator SHA256;
- endpoint and thinking-control semantics;
- cache-isolation policy;
- NPU allocation and conflicting workload state.

If any identity drifts, stop. Do not reinterpret an old run as equivalent.

### Gate 1: production-representative smoke

Use a small fixed subset at representative low/high concurrency. Require:

- all requests complete;
- zero transport/evaluator errors;
- exact prompt-token agreement between tokenization and completion usage;
- no reasoning leakage when thinking is disabled;
- expected finish reasons;
- privacy-safe per-request metrics and hashes;
- explicit tracking of empty/whitespace-only output.

Do not admit a full benchmark while unexplained pathological latency is still present.

### Gate 1b: warm steady-state verification

Run an unmeasured warm pass at the exact concurrency. Wait for compiler/JIT processes to be quiet. Then repeat the same requests as the measured pass. If warm and measured behavior is still unstable, investigate before proceeding.

### Gate 2: full-dataset sentinel

Run the complete workload once at a representative concurrency. Inspect p50/p95/p99/max TTFT/TPOT/E2E, throughput, completion-token distribution, finish reasons, empty-output rate, and per-request auditability.

Do not automatically proceed to the full matrix merely because the sentinel is technically valid.

### Gate 3: early reference-backed quality

Before expensive performance repetition, obtain enough reference-backed evidence to determine whether the candidate remains plausible. Reuse a historical quality baseline only when model/evaluator/data/protocol identities match and its audits remain valid.

If the candidate already shows a large, repeatable performance disadvantage and no quality advantage capable of justifying it, stop with a No-Go rather than spending NPU hours for completeness.

### Gate 4: full Go evidence

Only a candidate still credible after Gates 0-3 should consume the full budget. For a Go recommendation, require repeated corrected-chat performance across all intended concurrency points plus complete reference-backed quality repetitions and operational-stability checks.

If fixed-length tests are used, treat them as diagnostics to isolate decode cost from output length. They do not substitute for production-representative Natural EOS.

## Maintainer handoff checklist

Before handing the task to another maintainer, record:

- decision objective and current Go/No-Go status;
- authoritative runbook and controller paths;
- exact protocol identities and SHA records;
- active controller/service/container/port/NPU state;
- completed audit-valid cells/runs;
- current or next unit of work;
- known failure modes and whether they are resolved;
- safe-recovery preconditions;
- raw result, summary, audit, and log locations;
- whether automatic monitoring/recovery is enabled or disabled;
- last update timestamp.

Never put credentials, tokens, private keys, or verification secrets in handoff documents.

## Pause and cleanup checklist

When a user asks to pause:

1. stop the benchmark/evaluator controller;
2. stop/remove the owned model container;
3. verify the serving port is released;
4. verify NPU workers are gone;
5. restore DRRQR or other intentionally paused background services;
6. disable any automation that could relaunch the task;
7. preserve existing raw results and audit state unchanged;
8. write a clear paused-state handoff entry so the next restart does not duplicate work.

## Non-negotiable prohibitions

- Do not modify raw benchmark/eval outputs to pass validation.
- Do not restart after SHA/protocol drift without explicit re-qualification.
- Do not rerun already audit-valid work unless the protocol intentionally changes and the old evidence is explicitly reclassified.
- Do not claim quality from a dataset with empty or non-reference answers.
- Do not claim engine speed from shorter answers alone.
- Do not recommend a production switch from one throughput metric or one benchmark cell.
- Do not automatically change production routing/model configuration after a lab Go; use a controlled canary/A-B step first.
