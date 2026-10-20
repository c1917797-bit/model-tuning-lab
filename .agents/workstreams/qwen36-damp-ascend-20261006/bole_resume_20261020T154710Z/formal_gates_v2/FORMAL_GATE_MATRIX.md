This v2 preparation follows the explicit R115 task replacement and R118 renewal. Current tasks are GSM8K, HumanEval and MMLU. The older LongBench-v2 list remains historical; it is not unioned into new acceptance. No execution or qualification is claimed.

# Prospective formal acceptance gates — advisory, no measured results

The exact 9 October and 16 October protocols are immutable historical sources.
The current user instruction renews work until success; their expired campaign
cutoffs must not be rewritten or described as a new user deadline. The current
MODEL_AUTHORITY horizon is an admission-ticket constraint, not a user deadline.

| Gate | Required evidence | Rejection or unresolved condition |
|---|---|---|
| Source and delivery | One frozen candidate plugin/monkeypatch source; explicit ON and default OFF; unchanged base image; no training/distillation; original full checkpoint manifest, tokenizer, native/runtime/driver source identities | A config hash alone is not weights identity; a new source cannot inherit the old source's pass |
| Production service scope | Independent model/runtime qualification covers every measured request, reuse after warmup, actual concurrency, 1024 performance output tokens, 2048 task cap and required input/cache geometries | The C1/131/four-token experiment is insufficient; a source flag or successful HTTP request alone cannot qualify this |
| Prospective freeze | Policy, source, stack, generation profiles, workload IDs/order, prompt-token IDs, warmup, concurrency, variants, invalidation policy, metric definitions, task/scorer versions pinned into each launch source before data | No post-result change of workload, aggregation, prompt, scorer, exclusion, baseline or source |
| Three matched rounds | Three rounds with OFF/ON; identical image/weights/tokenizer/TP4, physical 4–7, stack, inputs/order, concurrency/arrival policy and common optimizations | Unmatched runs, different precision/common fixes, changed generation settings or selective discarded slow rounds |
| Formal timing | Profiling and diagnostic tensor capture OFF; actual full stream token IDs; 1024 generated tokens per request; common monotonic clock; complete HTTP/SSE and done events; no errors | Four-token smoke, estimated token counts, missing stream/done events, nonfinite/negative times, partial requests, retries hidden in a sample |
| E2E throughput | Prospective definition: total actual output tokens / (last measured request end − first measured submit); all three ratios and raw token/time totals | Protocols do not specify ratio aggregation. Do not select an aggregation after observing gains |
| Conservative prospective decision | This proposal chooses **each of the three ON/OFF ratios ≥1.10**; this is a stronger engineering condition, not a quoted additional user requirement | Report also pooled/count-time ratio, arithmetic mean, median and geometric mean; do not use one favorable summary to hide a failing pair |
| TTFT and TPOT | Per-request client-observed TTFT = first nonempty token-delta receipt − submit; TPOT = (last token-delta receipt − first)/(1024−1); report mean/median/p95 and chunk counts | Do not call an HTTP response duration TTFT or infer token-level engine timing from client chunks; exclude empty role/usage chunks from first token |
| All-request feature use | Independent frontend/engine/worker identity joins; every eligible measured request on all four ranks accounts for all 1023 processed decode inputs through BOLE; zero native/unattributed fallback for final ON | First request only, one active step followed by native generation, activation env var only, or a four-rank average hiding one inactive rank |
| Formal resource validity | Owned launch/cleanup, physical mapping, protected 0–3 untouched, complete observed monitoring, no foreign work during timing, fixed CPU/client placement and common resource policy | A foreign target process or a monitoring gap invalidates the whole affected round for a documented cause; retain the invalid evidence and use a new ID |
| Composition, when applicable | Freeze the composition decision and real A/B source mapping before timing. Measure D/A/B/A+B (prefer three complete rounds); numerical qualification for the actual components; combined A+B full tasks versus D | A/B need real measured variants, not dummy work. The protocol does not require A-only or B-only to achieve 10%; final combined candidate does. Do not evade composition by relabeling two independent techniques as one |
| Latest task scope | GSM8K, HumanEval, MMLU; official dataset revision, split, complete case list, preprocessing/truncation, prompts/chat template, tokenizer, metric and independent scorer pinned before inference | Do not silently replace a task, choose an easy subset, alter answer extraction, or mix source revisions |
| Task generation | Thinking OFF at actual prompt-render/runtime boundary; max_tokens=2048; normal EOS; deterministic matched baseline/candidate policy; actual input and completion token IDs | Removing thought text after generation does not prove thinking OFF. Performance's fixed-length/ignore-EOS profile cannot be reused for final tasks |
| Smoke before full | Frozen nonempty smoke case IDs; genuine scored smoke for the same candidate/source/profile before each full evaluation; full task admission follows measured remaining ticket budget | A source-only smoke or a smoke produced after the full run does not satisfy ordering; a smoke score is not a full-task score |
| Complete scoring | Exactly one actual completion and independent item-level score for every frozen case; join outputs to official frozen cases, scorer source and owned CPU execution | Retried/failed/truncated cases cannot disappear from denominator. Normal-EOS runs can hit the 2048 cap: retain and score those length stops, report their count |
| Loss calculation | Recompute weighted metric from frozen case weights and independent item outcomes. Report signed score delta, positive percentage-point loss and positive relative loss separately; conservatively both ≤1% | Use exact arithmetic before presentation rounding. If baseline score is zero, relative loss is undefined; fail closed rather than invent 0% |
| Final status | Performance, all three full task comparisons, runtime/activation, identity/resources, composition (if applicable) and source integrity all pass | Partial service/diagnostic passes remain partial; do not promote actual service flags or certify unmeasured gains |

## Metric details and validity boundaries

Performance uses an explicit fixed-1024 profile, for example max_tokens=1024 and
ignore_eos=True. Final tasks use normal EOS and max_tokens=2048. These are
different declared generation profiles. The proposals require streaming delta
token IDs supported by the installed completion protocol. Client chunk arrival
is an observed delivery clock; it is not an engine-token clock. Multi-token
chunks are reported so latency summaries remain interpretable.

The protocol does not prescribe a throughput aggregation formula. The proposed
all-three-pairs rule is declared before the first formal measurement. The reader
reports every pair, pooled throughput ratio, mean, median and geometric mean. It
never chooses the largest result. The pooled ratio is
`(sum ON tokens / sum ON elapsed) / (sum OFF tokens / sum OFF elapsed)`.

For task scores b and c in [0,1], report signed pp delta `100*(c-b)`,
positive pp loss `100*max(0,b-c)`, and positive relative loss
`100*max(0,b-c)/b`. Both positive losses must be ≤1. A zero baseline blocks the
relative-loss decision in this conservative proposal. Item weights and the
official metric (including any task/subject aggregation) are frozen; this
proposal does not invent new GSM8K extraction, HumanEval execution, or MMLU/
LongBench scoring rules.

## Independent-reader trust boundary

The lightweight final reader recomputes stream token/time arithmetic, matching,
activation accounting, item-score arithmetic and acceptance predicates itself.
It composes source-pinned **executed** independent validators for frontend/
worker lineage, runtime configuration, resource validity, actual task prompt
rendering, official scoring and broader model qualification. A bare passed flag
is insufficient: each proof has the exact predeclared reader source package,
subject/input Ref3s, actual CPU-owner identity, Devices[] execution, clean exit,
retained output Ref3 and unchanged source before/after. The actual validator
implementations and official scorers must exist and be audited before formal
admission; this proposal supplies no fake substitute for them.

The prepared policy intentionally lacks actual candidate/source/stack/reader
Refs and cannot be executed as a successful formal manifest. Those concrete
artifacts must be frozen in the new launch packet. No current service artifact
or production-readiness flag is changed by this advisory work.
