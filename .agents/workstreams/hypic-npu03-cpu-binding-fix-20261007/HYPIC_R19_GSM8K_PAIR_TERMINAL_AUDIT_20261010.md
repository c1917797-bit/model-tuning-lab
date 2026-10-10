# R19 repaired-source GSM8K max-2048/c32 paired terminal audit

The frozen r19 GSM8K no-cache and HYPIC-only arms are terminal. This is an
**off-path, runtime-enabled safety** result: the natural GSM8K requests do not
carry the explicit HYPIC segment boundaries of the LongBench in-path ruler.
It cannot prove HYPIC hot-path quality or overturn the separately rejected
LongBench-v2 pair.

- Frozen source: `4429e35177979c874bf053ab29789e4773f39b22`;
  image: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
  Physical NPU0–3, TP4, c32, natural EOS, temperature/seed 0, max output
  2048, 1319 GSM8K samples × three repetitions per arm. The only treatment
  switch was `VLLM_ASCEND_HYPIC_ENABLE=0/1`; the evidence-file path also
  differed as required by the arm.
- Baseline controller `exec-0000000000000433` and HYPIC controller
  `exec-00000000000004a3` exited 0. The candidate finished all three units
  at 2026-10-10 17:11 UTC and released its exact owned container.
  Candidate-only independent audit `exec-0000000000000510` exited 0 before
  the frozen paired auditor `exec-0000000000000512` was run exactly once;
  the latter exited 0.
- Independent audit replays 3957 raw rows per arm against the frozen dataset,
  prompt-token counts and evaluator; checks source attestation, one-switch
  service fingerprint, receipts and SHA256 hashes, 991/990 clean continuous
  physical-isolation samples, and exact owned container/NPU/port release.
  There were no foreign PIDs, probe errors, or service-log errors.

| GSM8K score | No cache | HYPIC |
| --- | ---: | ---: |
| Repetition 1 correct / 1319 | 1280 | 1281 |
| Repetition 2 correct / 1319 | 1274 | 1279 |
| Repetition 3 correct / 1319 | 1284 | 1280 |
| Total correct / 3957 | 3838 | 3840 |
| Length-limited by repetition | 10 / 11 / 7 | 6 / 11 / 10 |

The candidate improved 12 paired responses, regressed 10, and left 3935
unchanged: +2/3957, or +0.05054 percentage points. Its mean correct count
remains within the measured baseline-run range, and its mean length-limit
count does not exceed the baseline-run maximum. The frozen **GSM8K off-path
quality decision is PASS**. This is not a losslessness, in-path activation,
or full HYPIC adoption claim.

Immutable paired audit:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r19-c32-2048-gsm8k-paired-audit.json`,
SHA256 `496f1dfacb3c3a8dd03f8ee07368fb142b432498c0ee5dbb5722e1d4f85fd187`.
Baseline/candidate arm-result SHA256:
`03a2093873b2dbf3a0f675c7d0d47d83cadd0389192e10fb491ca03525ece897` /
`3814b62c948bdc275cc3ef221678191c1160b97dbe2f7907c545f89f108dfa9b`.
Both arm roots remain immutable. The same-source explicit-segment LongBench
quality decision remains `REJECT_OR_QUALIFY` (227/381 → 219/381); repaired
source same-identity performance and an admissible adoption decision are not
established.
