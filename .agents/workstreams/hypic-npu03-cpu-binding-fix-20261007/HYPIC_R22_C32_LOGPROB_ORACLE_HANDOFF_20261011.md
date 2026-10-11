# r22 bounded output-logprob oracle — pre-device handoff

Status: host-only preflight passed; **no NPU run yet**. The machine-readable
contract is `HYPIC_R22_C32_LOGPROB_ORACLE_PREREGISTRATION_20261011.json`.
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

Run only after fresh direct `chicaihong01/ma` resolution, loaded
`host-development`, actual physical NPU0–3 and 8223 idle proof and fresh
root-absence proof. First run no-cache to terminal and independently audit
32 samples/96 scored/160 unique request IDs, source identity, continuous
isolation and exact owned release. Only then run the HYPIC arm and audit.
Do not stop foreign work, use NPU4–7, reuse r19/r20 roots, or restart a
live controller on observation timeout. Each arm has a 7200-second campaign
budget; monitor the same handle.

The paired audit compares first differing generated-token position, top-two
logprob margin and within-arm token variability for sample 082. A
hot-proven, naturally stopped loss with a material output-numerics deviation
justifies deeper direct KV/GDN/position-state capture; it does **not** itself
identify that component. If the loss does not recur, or differences are
indistinguishable from within-arm variation, report inconclusive. This
bounded diagnostic cannot override r19's frozen `REJECT_OR_QUALIFY` or
replace a later corrected-source full 127×3 quality and same-source
performance/rollback audit.

