# r21 planned diagnostic: identify c32 HYPIC material victims per hot request

Status: **planned only; no new source bytes or NPU run admitted**. This is
an evidence-instrumentation diagnostic, not an optimization or a replacement
for the frozen r19 quality decision. The source worktree, final source hash,
controller/auditor hashes and output roots must be frozen in a separate
machine-readable preregistration before any device action.

## Scientific question and prior evidence

The r19 repaired-source c32/max-2048 LongBench pair is valid all-request
evidence: control 227/381 versus HYPIC 219/381, `REJECT_OR_QUALIFY`.
Twenty-three paired losses include eight four-worker-hot-proven losses; seven
of those eight hit the output cap and one naturally stopped. The r20 c1
post-hoc subset has both arms 9/9 correct and candidate 9/9 hot-proven.
Thus missing hot proof and the output cap are not sole causes. R19 logged
116 material evictions, but its report records counts without victim hashes;
no request-to-victim causal link exists. See
`HYPIC_R19_R20_LOAD_STATE_LOCALIZATION_20261011.md`.

Hypothesis to test: under c32, a prefix material record may be evicted or
replaced between scheduler admission and the worker's scored hot replay,
and the current aggregate proof does not distinguish a stale generation.
Alternative: all hot-proven wrong requests use a current, non-evicted
material; then investigate full-attention/GDN/position-state numerical
equivalence and decode scheduling, not eviction.

## Scope and design

- Start from immutable plugin commit
  `4429e35177979c874bf053ab29789e4773f39b22` in a **new** source
  worktree; do not edit `/cache/cch/hypic_vllm_ascend-hotproof-20261008`
  because r19/r20 audit identity depends on that tree.
- Add structured, bounded *diagnostic-only* fields: exact hash identities
  of ready/evicted material in scheduler reports and the material hash used
  by each worker's verified hot request. Do not alter admission, cache
  policy, output logits, worker planning, or model arithmetic. Add host-only
  tests that prove the new fields and unchanged behavior. Hashes are
  internal segment fingerprints, not prompt text.
- The primary A/B treatment remains only
  `VLLM_ASCEND_HYPIC_ENABLE=0/1`; both arms use the same instrumented source,
  image, model, TP4, physical NPU0–3, cpuset, port, generation settings and
  dataset/evaluator. Evidence-file paths may differ by arm.
- Prospective bounded c32 wave: LongBench-v2 indexes 33–64 inclusive in
  ascending order, 32 distinct prompts, two one-token warm requests then
  three max-2048 naturally stopping scored requests per sample, concurrent
  across 32 samples and serial within each sample. This includes r19's
  sample 059 and is **not** the full 127-sample ruler. No result from it
  changes the r19 population verdict.
- Baseline and HYPIC arms get separate fresh immutable roots. Run baseline
  to audited terminal/release before candidate. The paired auditor must
  replay 32 unique sample indexes, 96 scored rows and 160 total request IDs
  per arm, source/image/model identity, request hashes, scorer, per-request
  boundary and worker evidence, continuous physical isolation, exact owned
  cleanup, and hash joins. No post-hoc dropping of cold/unproved requests.
- Only physical NPU0–3 and port 8223 may be used. A passive 0–7 Docker
  device declaration is not active occupancy; actual foreign 0–3 processes
  or a busy port block admission. Never stop or modify foreign work or use
  NPU4–7. Campaign timeout must cover model startup plus long outputs;
  do not restart a live handle after a slow observation.

## Falsifiers and decision boundary

1. If no scored hot-proven candidate loss is observed, this bounded wave
   cannot test the stale-material hypothesis; report it as inconclusive.
2. If a hot-proven loss's exact material hash was evicted before its replay
   without a new matching ready generation, the stale-directory hypothesis
   gains direct evidence. It still needs a one-switch corrective intervention
   and fresh matched quality evidence before claiming causality.
3. If hot-proven losses occur with a current, non-evicted material identity,
   simple eviction attribution is weakened; pivot to a native-versus-HYPIC
   KV/GDN/position-state oracle under matched c32 traffic.
4. If the trace fields are missing or per-worker hash identities disagree,
   the diagnostic is invalid, not a quality pass or failure.

Instrumentation overhead disqualifies r21 timing from a performance win.
The r19 all-request rejection remains in force. Only a later corrected-source
full 127×3 matched pair and same-source performance/rollback audit can change
adoption. Before device work, record exact runtime/image/model hashes, trace
source commit, projected wall time, per-arm timeout, fresh roots, audit
scripts, rollback and continuous isolation contract in the final prereg.
