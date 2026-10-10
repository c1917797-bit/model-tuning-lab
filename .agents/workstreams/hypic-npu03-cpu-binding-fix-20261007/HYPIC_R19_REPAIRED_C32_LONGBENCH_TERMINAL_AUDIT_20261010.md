# R19 repaired-source LongBench 2048/c32 paired terminal audit

The frozen repaired-source LongBench-v2 experiment is terminal and independently
audited. This is an all-request quality result, **not** a full HYPIC adoption or
GSM8K result.

- Frozen protocol: `HYPIC_R19_REPAIRED_C32_2048_PREREGISTRATION_20261010.json`.
  Qwen3.6-27B BF16 TP4 on physical NPU0–3, explicit segment boundaries,
  concurrency 32, natural EOS, max output 2048, 127 samples × 3 repetitions
  per arm. Both arms mounted source `4429e35177979c874bf053ab29789e4773f39b22`
  and pinned image `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`;
  the declared treatment was only `VLLM_ASCEND_HYPIC_ENABLE=0/1`.
- Control root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-baseline`.
  Candidate root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-hypic`.
  Do not overwrite or rerun either root.
- Candidate controller `exec-0000000000000392` finished all 127 samples and
  381 scored responses but exited 1 at 2026-10-10 13:43 UTC with
  `RuntimeError: candidate scored boundary/hot coverage incomplete`.
  Preserve this mechanism-gate failure. The frozen independent paired auditor
  `r19_repaired_c32_longbench_audit.py` ran as `exec-00000000000003f6`,
  exited 0, and verified the complete all-request quality pair separately.
- The independent audit replays identities, every row and scorer, the one-switch
  seam, three-run short-canary equality, the integrated 32-sample capacity wave,
  source attestation, uninterrupted physical isolation, and exact release.
  Control/candidate guard samples: 865/997, with no foreign process or probe
  error. Candidate container
  `1e186957c93fbc94e5188c2fe1a8d6fd8c60ffbb11109c833283d347ea5eca68`
  was removed; owned NPU workers and port 8223 were released.
- LongBench score: control **227/381** (per run 74/77/76) versus HYPIC
  **219/381** (73/70/76), **−2.0997 percentage points**. The candidate
  mean of 73 correct/run is below the observed control-run floor of 74.
  Paired responses improved 15 and regressed 23. Difficulty=easy and
  length=short are category cliffs. Length-limited outputs increased
  49→67, and the candidate mean of 22.33/run exceeds the control-run
  maximum of 17. Frozen quality decision: `REJECT_OR_QUALIFY`.
- All 381 candidate scored requests match explicit-boundary events, but the
  frozen audit reports only 134 aggregate verified-hot requests and four
  worker-hot events; this is insufficient for a claim that every scored
  request exercised the four-worker hot path. It does **not** erase the valid
  all-request quality regression. The exact cause of the regression and hot
  shortfall is not yet isolated.
- Frozen paired audit:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r19-c32-2048-longbench-paired-audit.json`,
  SHA256 `40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`.
  Candidate arm-result SHA256
  `c1b7283c8d46ffb330af3be35232703d9b935819813a68288eb02b0608abdb74`.

Read-only, post-hoc stratification of the 381 audited row pairs found 204
both-correct, 139 both-wrong, 15 candidate-only-correct, and 23
control-only-correct responses. In 15 of those 23 control-only-correct
responses, the control stopped naturally while the candidate reached the
2048-token length cap; the converse transition occurred in 3 of the 15
candidate-only-correct responses. Correctness varied across the three runs
for 13/127 control samples and 22/127 candidate samples; extracted predictions
varied for 19/127 and 30/127, respectively. For example, sample 059 was
correct and naturally stopped in all three control runs, while all three
candidate runs hit the cap and were scored wrong. These associations prioritize
output-length and concurrent decode investigation but do **not** prove
whether truncation causes the wrong answer, is a symptom of altered generation,
or is linked to HYPIC materialization. No frozen decision was changed.

A second supplementary, post-hoc event join used the documented API-to-internal
request-ID prefix relation in `hotpath_quality_full.py`: each internal ID
has exactly one scored API ID prefix followed by an eight-hex suffix.
All 536 `worker_hot_request_verified` events uniquely join to 134 scored
requests, with exactly the same four container worker PIDs (265–268) for each.
The other 247 scored requests have no such event proof; call them **unproved**,
not proven cold. In the 134 proved-hot rows, control/candidate correctness was
83→79 (8 regressed, 4 improved). In the 247 unproved rows it was 144→140
(15 regressed, 11 improved). These groups were selected by observed runtime
activation and are not randomized. They show the eight-net-response loss is
not confined to one observed stratum, but do not identify its technical cause
or turn 134/381 into universal hot-path coverage.

Allowed claim: this repaired-source max-2048/c32 LongBench all-request pair
shows a quality regression under a clean, matched, one-switch experiment.
Forbidden claims: HYPIC quality preservation, full adoption, per-request
four-worker mechanism coverage, GSM8K safety, or repaired-source performance
benefit. The historical six-phase performance gain used a different source
and remains source-scoped; it cannot override this result. GSM8K is separately
frozen and unrun. The next work is read-only discrepancy localization from
these immutable responses, followed by a single prospective bounded fix only
if evidence supports one; complete the frozen GSM8K safety pair separately
when the physical NPU0–3 lane and port are truly idle.
