# r16 original-source full quality pair — terminal audit

This prospective pair tested whether the historical HYPIC source alone
preserves quality under the *new* LongBench-v2 max-2048/c8 ruler on
physical chicaihong01 NPU0–3. It does not revise the historical
1024/c32 result or the completed r13 result.

Both arms used Qwen3.6-27B BF16 TP4, context 41984, CPU 112–191,
the pinned official image
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
memory fraction 0.85 and HYPIC cache 3584 MiB/10 segments. Both
mounted the clean original source `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`;
only HYPIC enablement/evidence path differed. Dataset, scorer, sample
IDs, prompts, explicit boundaries, seed/temperature 0, thinking off,
natural EOS and three scored responses per sample matched.

The independent `python3 -B audit_r16_original_source_full.py` replay
passed: each arm has 127/127 samples and 381/381 hashed, rescored
responses, matching source/service identity, continuous clean physical
isolation (999/1078 samples) and exact owned release. Baseline controller
`exec-0000000000000060` exited 0; candidate
`exec-00000000000000ae` exited 1 *after* all responses solely because
the preregistered hot-coverage gate failed. That is a separate
activation failure, not missing quality data. After cleanup a fresh
NPU0–3 process check and port 8223 check were empty.

The immutable baseline/candidate roots are respectively
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r16-full-baseline`
and
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r16-full-hypic`.
Arm-result SHA256: `29b3e05141a80210c674132747207d7df83158d09a00744a367e4d5bcb88a9f7`
and `16848b2c4cfcfd00cc7108c530151bd871826997ab8fb413794977dcc68ad284`.
The external independent audit
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r16-original-source-full-quality-audit.json`
has SHA256 `52914becb93266ac4a27e8491b40bf8456b566ee8f828038250098bfec33a4ee`.

| Frozen measure | No-cache | HYPIC-only |
| --- | ---: | ---: |
| Correct / 381 | 224 (58.79%) | 210 (55.12%) |
| Correct per repetition | 71 / 78 / 75 | 70 / 71 / 69 |
| Length-limit finishes | 52 | 64 |
| Paired flips | — | 16 improved / 30 regressed |
| Aggregate verified hot | — | 364 / 381 |

The all-request delta is −3.6745 percentage points. Candidate mean
correct/run 70 is below the baseline floor 71; candidate mean length
finishes/run 21.33 exceeds baseline maximum 20; easy and short strata
fall below baseline repeat ranges. Thus the *predeclared* quality
decision is `REJECT_OR_QUALIFY`. The original source has a serialized
four-worker sentinel and aggregate hot activity, not per-scored-request
four-worker telemetry; universal mechanism attribution is unproven.

r13 on later `c12060c` was also negative (230/381→219/381), while
its matched performance was positive. r15's eight selected cases
(13/24 original versus 10/24 later source) were diagnostic, not a
population predictor. The source change alone is not an established
quality root cause. Do not pool source/ruler runs or splice r13 speed
onto r16 quality. This bounded current-ruler regression does not
invalidate the historical 1024/c32 result or prove a specific
RoPE/GDN/cache defect. Original-source adoption performance is not
admitted after this quality gate failure; any repair requires a new
prospective one-variable, same-identity control on NPU0–3.
