# Prospective HYPIC in-path quality ruler (2026-10-08)

This is a new scientific question and denominator. The frozen clean2 natural
suite is off-path safety evidence and the single-sample canary is path proof;
neither supplies this ruler's baseline score. Preserve both unchanged.

## Scope and frozen inputs

- Qwen3.6-27B BF16, pinned source/image/weight index and 41,984 context as
  checked by `binding_off_quality.preflight`; TP4 on physical NPU0-3 only,
  cpuset 112-191, port 8223. NPU4-7 and unrelated containers are excluded.
- LongBench-v2's 127 frozen samples, unchanged prompt builder and AIS Bench
  first-option scorer. Clean2 no-cache run1 is used **only** to pin each
  sample ID and measured prompt-token count; its scores are not reused.
- Each scored request has explicit ends `[boundary, prompt_tokens]`, where
  `boundary = min(16384, floor((prompt_tokens - 2048) / 16) * 16)`; all 127
  prompts are 10,352-39,642 tokens and fit with a 2,048-token cap. Before
  each sample's measured answers, send two identical one-token observations.
- Three natural-EOS scored answers per sample, maximum output 2,048,
  temperature/seed 0, thinking off, ignore_eos=false. No failed or retried
  request is silently accepted. Same payload and warm policy in both arms.
- Per-sample task concurrency **8**, deliberately lower than the old c32
  off-path suite to keep each repeated prefix resident while its three
  scored answers complete. This is a new matched ruler; c32 scores may not be
  pooled or called equivalent. Score 381 rows per arm, with unique
  (sample_index, repetition) identity and response SHA256.

## Admission and acceptance

Run a candidate-only 3-sample pilot (sample 0 and the shortest/longest prompt)
before the full baseline. It must show an explicit boundary and positive
verified hot reuse on all three scored requests, with four distinct worker-hot
PIDs on the first. If it fails, preserve pilot evidence and repair the protocol
before spending the full baseline window.

Each full arm uses a fresh exact-owned quality service; the only arm variable
is HYPIC enablement. The first sample runs alone as an activation sentinel,
then the remaining samples use concurrency 8. Require four distinct worker-hot
PIDs on the candidate sentinel's scored request and no worker-hot events in
the no-cache arm. The candidate's summed verified-hot-request count must cover
all 381 scored answers; inspect any shortfall rather than relaxing this gate.
The 10-second physical-lane guard must find no foreign NPU0-3 process or
unobservable interval. Prove exact container, worker, and port release for
each arm. Perform an independent raw-row/hash/scorer audit after both arms.

Predeclared score rule: aggregate HYPIC correct/381 must be at least baseline
correct/381 (nonnegative percentage-point delta); also report all three run
scores, paired flips, baseline variability, difficulty/length strata, and
length-limit rate. A category cliff outside the corresponding baseline
three-run range prevents an unqualified pass. If a score rule fails, preserve
the valid result as rejection/inconclusive rather than altering the ruler.
This is scoped in-path LongBench quality, not short-prompt GSM8K or C3 proof.

The completed clean2 LongBench runs took 14-24 minutes each at c32, but this
ruler adds two observations per sample and uses c8. The recent one-sample
canaries took roughly 9 minutes per service including about 7 minutes to load;
project approximately 2-4 hours per full arm plus service transitions and
independent audit, with a conservative 10-hour overall monitoring window.
Persist one sample at a time outside Git and keep exact operation IDs for
recovery. A terminated partial attempt is not resumed in place: preserve its
rows and use a new root after auditing the stop cause. Never restart a live
controller. On timeout or lane intrusion,
preserve partial rows and release only the exact-owned container; do not pair
an invalid control arm with a clean treatment. Commit only concise contracts,
scripts, hashes, and decisions, then push the work branch.

## Pilot-1 tooling failure retained

`hotpath-pilot-hypic` operation `exec-000000000000127c` completed all three
requests and released its exact container, but controller exit 1 occurred at
the final request-ID join. The OpenAI response exposes a shorter `chatcmpl-`
ID; scheduler evidence appends an internal suffix. Exact string equality was
therefore an invalid audit rule. Offline inspection found 3/3 unique prefix
matches, 3/3 scored `complete_hybrid_repair` events, 4 distinct worker-hot
PIDs on the first scored request, and no foreign NPU0-3 process. This is a
tooling/audit failure, not an algorithm failure or a controller pass. The
successor `pilot2` uses unique-root replay with a one-to-one prefix join;
pilot-1 raw artifacts and its nonzero exit remain unchanged.
