# HYPIC validation scope and next gates — 2026-10-10

## Evidence that must stay separate

| Question | Evidence already available | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Historical practice result | 2026-09-06 1024-token/c32 LongBench-v2 and GSM8K success on physical NPU4–7 | A prior bounded success | A matching baseline or outcome on NPU0–3 |
| Current natural-request quality | `quality-context-41984-clean2`: 2048-token/c32, three complete LongBench-v2 and GSM8K runs per arm, clean isolation and release | All-request scores under natural chat payloads | HYPIC in-path quality: those payloads supplied no usable segment partition, and the strict audit found zero worker-hot PIDs |
| Explicit-segment 2048 quality, later source | r13 `c12060c`, c8 LongBench-v2 127×3: 230/381 no-cache versus 219/381 HYPIC; four-worker hot proof 368/381 | Valid all-request negative quality observation and incomplete universal hot coverage for that identity | Original-source or c32/GSM8K result |
| Explicit-segment 2048 quality, original source | r16 `3ad0967`, c8 LongBench-v2 127×3: 224/381 versus 210/381; frozen stricter gate `REJECT_OR_QUALIFY` | Valid all-request quality decline under the r16 ruler | Historical 1024/c32 or default 2048/c32 acceptance; the 3.6745 pp drop is descriptively inside the 5.5118 pp baseline repeat range of the older criterion, but cannot overturn r16's preregistered decision |
| Output-cap sensitivity | r17 original source, c8, 1024-token LongBench-v2, new matched baseline and HYPIC roots | Once complete, isolates the output cap relative to r16 at fixed c8/source | Historical 1024/c32 reproduction or current 2048/c32 Skill acceptance |
| Matched speed, later source | r13 six-phase fixed-output performance on NPU0–3: median weighted TPOT 74.727578 → 58.643006 ms, strict hot 120/120 | Bounded c16 performance benefit for `c12060c` and its frozen service identity | Original-source speed or quality safety; speed cannot override a failed quality gate |

## Correct execution order

1. Preserve the live r17 no-cache controller `exec-000000000000012b` and immutable root. Poll the same handle; never restart because a progress file is quiet. On terminal state independently audit all 127 samples/381 scored responses, hashes, source identity, continuous physical NPU0–3 isolation and exact owned release. Start the frozen HYPIC-only r17 arm only if that audit passes and physical NPU0–3 plus port 8223 are actually free. Then run the preregistered paired audit. Do not revise r13/r16 verdicts post hoc.
2. Interpret r17 only as a cap-sensitivity test. If it changes the quality pattern, identify cap as a bounded contributor, not as a proven unique root cause; if it does not, continue diagnosis without inventing a GDN, RoPE, HCCL or cache cause.
3. For the still-missing full current Skill claim, prospectively freeze a separate explicit-segment 2048-token/c32 matched quality identity. Include complete LongBench-v2 and GSM8K repetitions, deterministic canary, source/image/model/evaluator hashes, one-switch treatment, per-request activation eligibility and a continuous physical NPU0–3 guard. Score **all** preregistered requests, including cold or fallback ones, and report deployment quality separately from strict in-path attribution. GSM8K requests that cannot activate HYPIC remain off-path safety evidence, never hot-path proof. Reuse earlier baseline units only after the full service, payload, dataset and evaluator fingerprints and raw hashes match; otherwise create a fresh matching baseline.
4. Reuse existing matched performance only within its exact source and service identity. After a valid quality gate for any changed identity, obtain the matching repeated performance evidence needed for that identity; do not splice r13 speed into r16/r17 or a future c32 quality pair.
5. Independently audit raw rows, response IDs, activation evidence, hashes, worker/device mapping, uninterrupted isolation, and exact resource release. Record separate decisions for evidence validity, deployment effect, mechanism attribution, performance, quality, historical reproduction and adoption. Negative or incomplete outcomes remain legitimate experiment conclusions, not reasons to add a new operator experiment automatically.

## Scope guard

This task is HYPIC end-to-end validation and related Skill acceptance. Do not schedule another isolated GDN operator run unless an end-to-end result creates a new, explicitly frozen attribution question. Do not use NPU4–7 or modify foreign processes. A passive container device mapping is not physical occupancy; a real foreign NPU0–3 process is.
