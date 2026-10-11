# r22 bounded output-logprob oracle — terminal handoff

Status: both arms and the independent paired audit are terminal. The
machine-readable contract remains the immutable
`HYPIC_R22_C32_LOGPROB_ORACLE_PREREGISTRATION_20261011.json`.
The adapter and independent auditor are
`r22_c32_logprob_oracle.py` and `r22_c32_logprob_oracle_audit.py`.

This is the shortest non-repeating numerical screen after r19's full
max-2048/c32 rejection. Use exactly the repaired r19 plugin commit
`4429e35177979c874bf053ab29789e4773f39b22`, official pinned image,
Qwen3.6-27B, TP4, physical NPU0–3, original 10-segment material budget,
explicit boundaries, two warm requests and three scored max-2048 requests per
sample. Select indexes 64–95 at c32 and request token-level top-five logprobs
only for sample 082's scored requests. All 32 prompts remain concurrent;
repetitions within each prompt remain serial. The scored 082 payload differs
identically in both arms, so old r19 baseline cannot be spliced in. R19's
preceding waves 0–63 are deliberately omitted: this is not an exact cache
history replay, and a non-reproduction cannot rule out the original failure.

Before device work, both adapter `--check` modes and independent auditor
`--check` passed; host-only r22 tests passed 3/3; the unchanged r19 tests
passed 3/3 separately. A combined r19/r20/r22 test process is invalid:
historical test modules mutate shared adapter globals, and r20's old
"root absent" test is now expected to fail because r20 is terminal. Do not
mislabel that combined-process failure as a product regression. The source
tree is clean at 4429e3. `validate-mst.sh` passes all 29 structural Skill
checks, which is not functional Skill acceptance.

Baseline controller `exec-0000000000000774` and auditor
`exec-00000000000007a4` completed; the independent baseline audit passed 96
rows, 160 IDs, 324 clean isolation samples, source identity and exact release.
Candidate controller `exec-00000000000007ae` completed 32/32 samples and
96/96 responses, then exited 1 on incomplete candidate boundary/hot coverage.
Independent `--arm hypic-only` audit passed 96 rows, 160 IDs, source identity,
363 clean isolation samples and exact release; 34/96 scored requests had
four-worker proof and sample 082 had 0/3.

The frozen `--pair` audit exited 0 and wrote
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r22-c32-logprob-oracle-paired-audit.json`
with SHA256
`23568b259c3bff7b3da562db0532a817c1705972ac283af55f8245d197185e1a`.
Both arms scored 54/96. Sample 082 was correct and naturally stopped in all
three repetitions in both arms. Cross-arm first-token differences at
124/23/212 were comparable to within-arm variation (baseline 23/34/23;
HYPIC 34/34/57). Since that traced request had no HYPIC hot proof and the
wave omits r19's first two waves, this is inconclusive about causality and
does not alter r19's full-suite rejection. Both exact experiment services
were released. Do not rerun/reuse the roots, stop foreign work, or use NPU4–7.

The paired audit compares first differing generated-token position, top-two
logprob margin and within-arm token variability for sample 082. A
hot-proven, naturally stopped loss with a material output-numerics deviation
justifies deeper direct KV/GDN/position-state capture; it does **not** itself
identify that component. In this run the selected sample was correct in both
arms, candidate hot proof was 0/3, and token divergence was comparable to
within-arm variation; report inconclusive. The next device experiment needs a
source-level numerical oracle that verifies HYPIC hot execution and directly
distinguishes KV/GDN/position state. This bounded diagnostic cannot override
r19's frozen `REJECT_OR_QUALIFY` or replace a later corrected-source full
127×3 quality and same-source performance/rollback audit.
