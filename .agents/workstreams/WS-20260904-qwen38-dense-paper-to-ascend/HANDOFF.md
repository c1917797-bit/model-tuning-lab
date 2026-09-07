# Workstream Handoff — WS-20260904-qwen38-dense-paper-to-ascend

Updated: 2026-09-07T09:30:00Z

## Status

A new quality-first DRRQR follow-up is active under experiment identity
`state-reduction-qwen36-dk112-quality-first-20260907`. It does not revise or
overwrite the completed Dk64/Dk96 rejection. The only new candidate is Dk112
(128 -> 112, 12.5% aligned Q/K reduction). Its checkpoint build is the
CPU/storage-only AWMCP operation `exec-0000000000000cb7`; it exited 0 after
190904 ms. Independent audit operation `exec-0000000000000cbb` passed:
Dk112, 48 layers, 96 tensors, six rewritten shards and nine unchanged
hardlinked shards. Manifest SHA256 is
`033eac4d29e12e9f219b213f12a15ebd3217e183f353c43c2200bb47f149243a`.
The persisted structural audit SHA256 is
`0d9efd2418d9b34e3ef16b78949c366d79992b587bc53cc6110b7fd058e6a12c`.
No Dk112 NPU service, benchmark, quality run or profile has begun,
and no Dk112 benefit or quality claim is currently allowed.

The new records are:

- `experiment-state-reduction-qwen36-dk112-quality-first-20260907.json`;
- `evidence-state-reduction-qwen36-dk112-quality-first-20260907.json`;
- `decision-state-reduction-qwen36-dk112-quality-first-20260907.json`;
- `knowledge-proposals-state-reduction-qwen36-dk112-20260907.json`.

The allowed future runtime lane is exactly host NPU4-7, container-visible
0-3, TP4, CPU0-95, port8226 and HCCL range 27020-27120. NPU0-3 remains outside
scope even if a read-only outer status reports it idle. At the 2026-09-07
preflight all eight cards were empty; that observation does not grant authority
outside NPU4-7.

### Dk112 exact recovery

Build operation `exec-0000000000000cb7` is terminal-successful and must not
be restarted. To re-audit without mutation, run:

```bash
sha256sum /cache/cch/Qwen3.6-27B-gdn-drrqr-dk112/drrqr_manifest.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/cache/cch/Qwen3.6-27B-gdn-drrqr-dk112/drrqr_manifest.json')
x = json.loads(p.read_text())
assert x['target_head_k_dim'] == 112
assert x['changed_layers'] == 48
assert x['changed_tensor_count'] == 96
assert len(x['changed_shards']) == 6
print('Dk112 manifest structural gate: PASS')
PY
```

If and only if the operation is terminal-failed, preserve the partial output
before retrying:

```bash
mv /cache/cch/Qwen3.6-27B-gdn-drrqr-dk112 /cache/cch/Qwen3.6-27B-gdn-drrqr-dk112.failed-exec-0000000000000cb7
docker run --rm --network none -v /cache:/cache sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1 python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/build_qwen36_drrqr_checkpoint.py --src /cache/efim/Qwen3.6-27B --dst /cache/cch/Qwen3.6-27B-gdn-drrqr-dk112 --capture-dir /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/calibration/captures --calibration-jsonl /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/calibration/longbenchv2-16x2048-tokenids.jsonl --official-rrqr /cache/cch/LinearAttentionPruning/src/key_reduction/pruners/rrqr.py --new-head-k-dim 112 --expected-linear-layers 48 --tp-size 4 --captures-per-rank 16
```

The manifest is bound in `state_reduction_dk112_runner.py`; py_compile and
`git diff --check` passed in operation `exec-0000000000000cbc`. NPU execution
was intentionally not started because the current task scope excludes operating
NPU4-7. After explicit renewed authorization, the exact first runtime command is:

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_dk112_runner.py --arm drrqr-dk112 --phase smoke
```

Only after that smoke passes, run fresh baseline quality and Dk112 quality
first. Passing means only `no-material-regression-observed`; it is not
`lossless-proven`. Performance and profiling are conditional on both datasets
passing the fresh baseline-variability gate.

The state-reduction paper piercing is **complete**. Official Strong RRQR Dk64
(50%) and Dk96 (25%) both failed the frozen GSM8K quality gate and are rejected
for this workload. Dk96 performance means were slightly favorable, but all
three-run intervals overlap, so no stable serving acceleration is claimed.
The final evidence audit passed and NPU4-7/port8225 are released. Profiling was
not started because the preregistered quality gate failed.
The consolidated success/failure and recovery analysis is in
`MAINTAINER_RETROSPECTIVE.md`; the state-reduction failure ledger contains
16 classified rejected attempts and its knowledge-proposal ledger contains
11 scoped proposals.
The completed `DRRQR论文穿刺续跑` heartbeat was deleted; it will not restart
or re-poll this experiment.

The operator-selected HYPIC historical reproduction is **complete**:

- experiment: Qwen3.6-27B, TP4, four Ascend 910B4 cards;
- resource lane used: host NPU4-7, CPU0-95, port 8224;
- baseline: native prefix cache off, HYPIC off;
- treatment: native prefix cache off, HYPIC on;
- only arm switch: `VLLM_ASCEND_HYPIC_ENABLE`;
- accepted units: **18/18**;
- independent evidence audit: **passed, zero errors**;
- decision: adopt for this frozen workload with quality guardrails;
- integration state: ready for maintainer review.

NPU0-3 was a protected external lane throughout the formal run. Do not use
this handoff as authority to inspect or alter it.

Controller operation `exec-00000000000009ab` exited 0 at
2026-09-06T17:31:34Z. Both exact experiment containers are exited,
`OOMKilled=false`, and port 8224 has no listener.

## Frozen ruler

| Variable | Value |
|---|---|
| model | `/cache/efim/Qwen3.6-27B` |
| image | `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1` |
| HYPIC | 0.8.5, commit `3ad0967589304cd8fc4e7cff02f48ecc6125c89f` |
| topology | TP4, host NPU4-7, container-visible 0,1,2,3 |
| budget | `max_model_len=40960`, `max_num_batched_tokens=40960` |
| performance | 32768 input, 16384 shared, 1024 fixed output, 40 requests, concurrency 16, two warmups, three runs per arm |
| quality | LongBench-v2 127 and GSM8K 1319; concurrency 32, max output 1024, seed 0, temperature 0, thinking off, three runs per arm |
| excluded | CEval by operator decision |
| unavailable | authoritative NIAH+ files; no substitute |

The employee reference is contextual evidence, not pooled evidence:
Qwen3.5-27B, TP2, 2× Ascend 910C, HYPIC 0.8.5.

## Final results

| Metric | Baseline mean | HYPIC mean | Change | Employee change |
|---|---:|---:|---:|---:|
| TTFT ms | 40357.590939 | 22747.767959 | -43.6345% | -46.6% |
| TPOT ms | 74.507463 | 60.357689 | -18.9911% | -18.4% |
| output tok/s | 123.765347 | 168.402919 | +36.0663% | +38.5% |
| duration s | 331.419626 | 243.252621 | -26.6028% | -27.8% |

The performance direction and approximate magnitude reproduced. Absolute
latencies are not expected to match because model version, hardware generation
and tensor parallelism differ.

| Dataset | Baseline mean | HYPIC mean | Delta | Baseline three-run range |
|---|---:|---:|---:|---:|
| LongBench-v2 | 46.194226% | 45.931759% | -0.262467 pp | 5.511811 pp |
| GSM8K | 96.158706% | 96.007076% | -0.151630 pp | 0.379075 pp |

Both quality deltas are inside measured baseline repeat ranges. This supports
"no material regression observed" for the frozen ruler; it does not prove
universal losslessness.

## Evidence

- output root:
  `/cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906`
- aggregate:
  `historical-reproduction-summary.json`,
  SHA256 `741a5ad225682452062143f776af81949961d11ecf946b4da64ade3a118f935e`
- report:
  `HISTORICAL_REPRODUCTION_REPORT.md`,
  SHA256 `f30ac5decb07145f78ee41a038874aaf3c059423f16ed73df0ea617fcd5fcb79`
- independent audit:
  `historical-reproduction-evidence-audit.json`, `ok=true`,
  `accepted_units=18`, `errors=[]`
- treatment activation:
  `hypic-only/performance.run1.json` has
  `hot_path_verified=true`, `hot_path_missing=[]` and
  `evidence_failures=[]`
- experiment, evidence and decision ledgers:
  `experiment-hypic-formal-npu4-7-tp4-b40960.json`,
  `evidence-hypic-formal-npu4-7-tp4-b40960.json`,
  `decision-hypic-formal-npu4-7-tp4-b40960.json`

Formal no-cache/HYPIC profiling was not repeated because the employee ruler was
a serving benchmark plus accuracy comparison. HYPIC activation is proven by
strict runtime event evidence. Existing native msprof captures belong to the
separate PDC-coexistence experiment and must not be pooled.

## Successes worth reusing

1. Freeze model, image, dataset hashes, prompt/scorer, topology, traffic shape
   and budget; change one algorithm switch only.
2. Treat host-to-container device remapping as an explicit invariant.
3. Budget the private suffix plus seam sink: 16384 + 8 required at least
   16392 physical tokens; changing the budget required a new artifact root.
4. Require hot-path proof in addition to favorable latency.
5. Run three repetitions and compare accuracy deltas with measured baseline
   variability rather than an invented generic tolerance.
6. Persist per-sample JSONL and resume only indexes without an accepted
   `ok=true` row.
7. Stop/restart the identical service between performance and quality phases.
8. Accept completion only after an independent hash/count/index audit.

## Failures and recoveries

- A preflight attempt used host IDs 4-7 inside a remapped container. Measurement
  never began; the failure was archived. Use container-visible 0-3.
- The earlier 16384 token budget could not admit a 16384 suffix plus an
  8-token seam. It was rejected and never pooled with the corrected case.
- Baseline GSM8K run2 lost service after 923 successes. The resumable evaluator
  preserved valid rows and retried only missing indexes.
- An incomplete-report renderer indexed an absent GSM8K aggregate. The renderer
  was changed to render only present datasets and self-tested before resume.
- The first resumed treatment service exited cleanly before measurement. The
  controller restarted the same exact configuration; no accepted unit was
  discarded and no algorithm failure was inferred.

## Exact verification command

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/audit_hypic_historical_reproduction.py \
  --root /cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906 \
  --output /cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906/historical-reproduction-evidence-audit.json
```

Expected: exit 0, `ok=true`, `accepted_units=18`, `errors=[]`.

## Exact recovery/resume command

This command is idempotent against validated artifacts: it verifies and skips
accepted units. Run its self-test first and never start it while another
authoritative controller is live.

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
export HYPIC_OUTPUT_ROOT=/cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906
export HYPIC_MODEL_NAME=qwen36-formal-npu4-7-tp4-b40960
export HYPIC_PORT=8224
export HYPIC_CPUSET=0-95
export HYPIC_BASELINE_CONTAINER=qwen36_hypic_nocache_baseline_npu4_7_tp4_b40960
export HYPIC_TREATMENT_CONTAINER=qwen36_hypic_only_npu4_7_tp4_b40960
export HYPIC_EXPERIMENT_ID=hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906
export HYPIC_HOST_NPU_FIRST=4
export HYPIC_HOST_NPU_LAST=7
export HYPIC_VISIBLE_DEVICES=0,1,2,3
export HYPIC_CONTAINER_DEVICE_FIRST=0
export HYPIC_TP_SIZE=4
export HYPIC_HCCL_PORT_RANGE=26000-26100
export HYPIC_MAX_NUM_BATCHED_TOKENS=40960
export HYPIC_REFERENCE_SHA256=204b01d76eff8a0fd69a4a048de44da8385c6bfdc250c1efb8af542b63fb438c
bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh --self-test
bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh
```

## Delivery

Worktree branch:
`work/WS-20260904-qwen38-dense-paper-to-ascend`.

Intended review destination is
`https://github.com/c1917797-bit/model-tuning-lab`, but this workstream did
not push and did not fabricate or alter Git identity.

## Completed state-reduction paper piercing

This is a separate experiment from HYPIC and must not be pooled with it.

- paper: *The Key to State Reduction in Linear Attention: A Rank-based Perspective*,
  arXiv 2602.04852v2;
- official code: `camail-official/LinearAttentionPruning` at
  `919d8667d951c385e08510bc1267c2e7049a4f56`;
- model: unmodified `/cache/efim/Qwen3.6-27B` baseline versus independent
  `/cache/cch/Qwen3.6-27B-gdn-drrqr-dk64` and
  `/cache/cch/Qwen3.6-27B-gdn-drrqr-dk96` treatments;
- resource lane used: host NPU4-7, container-visible 0-3, TP4, CPU0-95,
  port 8225; now released;
- calibration caveat: delivered LongBench-v2 first 16 source-ordered rows,
  frozen to 2048 tokens, because FineWeb-Edu is absent. This is an Ascend
  adaptation, not paper-exact calibration;
- completed: 3072-file capture audit, official Strong-RRQR Dk64 checkpoint,
  real-weight Dk64 Ascend smoke, baseline performance 3/3, baseline quality
  LongBench-v2 3/3 plus GSM8K 3/3, Dk64 treatment performance 3/3 and
  Dk64 treatment quality 6/6; quality operation
  `exec-0000000000000b5a` exited 0;
- Dk64 quality decision: LongBench-v2 passed, but GSM8K mean was
  96.108163%, -0.202173 pp versus baseline. The loss exceeded the baseline
  three-run range of 0.151630 pp, so Dk64 failed the preregistered quality
  gate and is not adoptable;
- Dk96 fallback checkpoint build `exec-0000000000000be9` exited 0. Manifest
  SHA256 is
  `a8f8f162f15fb6e4717ed509927d93c549a2ef01eca4c88e45e75cdf900b16fc`;
  independent audit confirmed 48 layers, 96 target shapes, six rewritten
  shards, nine unchanged hardlinked shards and the sole config delta
  `linear_key_head_dim: 128 -> 96`;
- Dk96 real-weight smoke `exec-0000000000000bf0` exited 0, returned exactly
  `ASCEND_DRRQR_OK`, and logged the GDN path with `head_k_dim=96`; container
  exited without OOM and NPU4-7 were released;
- Dk96 formal performance operation `exec-0000000000000bf2` exited 0.
  Every repetition accepted 40/40 requests with exact 1024-token output.
  Mean changes versus baseline are TTFT -0.401006%, TPOT -0.442686%,
  output throughput +0.380717%, and duration -0.327093%. All raw three-run
  intervals overlap the baseline intervals, so no repeat-separated serving
  benefit is claimed;
- launcher attempt `exec-0000000000000c15` exited 2 after 20 ms because
  its path contained a nonexistent `scripts/` component. No measurement,
  container or NPU workload started; this is logged as an orchestration failure;
- complete: corrected Dk96 formal repeated-quality operation
  `exec-0000000000000c1b` exited 0 after 7,988,385 ms;
- accepted Dk96 LongBench-v2 run1: 60/127 = 47.244094%, 127/127
  successful, zero failures, exact unique indexes 0-126; summary SHA256
  `005f533016d8c63e68e77f664036f1d50cd76fd643f9d4c328e3c2d42a58b728`,
  details SHA256
  `63f717d4bec3a3fbca2af77b7b5d5d8b51a0007fbdc86541e1d55e6be7c77d66`.
  The recorded and independently computed details hashes agree. The controller
  then advanced to LongBench-v2 run2;
- accepted Dk96 LongBench-v2 run2: 66/127 = 51.968504%, 127/127
  successful, zero failures, exact unique indexes 0-126; summary SHA256
  `826c51296dd7f31bb8f68448a7ae65f79a3acda3eb3a36c6a3749ff68aaeb3a9`,
  details SHA256
  `8f83c0477ed486a115bc9d4a90b8edad4085b2e109bf76d1704b23b28316e71d`.
  The recorded and independently computed details hashes agree. The controller
  then advanced to LongBench-v2 run3;
- accepted Dk96 LongBench-v2 run3: 62/127 = 48.818898%, 127/127
  successful, zero failures, exact unique indexes 0-126; summary SHA256
  `acbc12b9f7aa71a7436b2c3ae882c0110d5934a60d4839df0c2af6507355e256`,
  details SHA256
  `59773f08263dd4366e1ccd5a12b0ac32bf5bed0b19ebabbb01af3da1fcb63ffc`.
  Across the three Dk96 runs, mean accuracy is 49.343832%, sample SD is
  2.405552 pp and the delta versus baseline is +3.674541 pp, so
  LongBench-v2 passes the preregistered gate. The controller then advanced to
  GSM8K run1;
- accepted Dk96 GSM8K run1: 1265/1319 = 95.905989%, 1319/1319
  successful, zero failures, exact unique indexes 0-1318; summary SHA256
  `b11d73a90aa7af15752f99b7fa7e32deee75ed37874353dcdae8553e9633dd12`,
  details SHA256
  `6bdc392670d17a05a196356c4251d2857fc0951c1365ae3edf762a93a5205ac4`.
  The recorded and independently computed details hashes agree. This single
  run is not a gate decision; the controller advanced to GSM8K run2;
- accepted Dk96 GSM8K run2: 1268/1319 = 96.133434%, 1319/1319
  successful, zero failures, exact unique indexes 0-1318; summary SHA256
  `19b6d7ae20f2bdb28315f5ae932bac842877486b0893a23972c666a7027ba751`,
  details SHA256
  `6fffa04b79357e1cc9d179550e44b849732a3c1bcbb0cf03e751e5c10a3e08f9`.
  The recorded and independently computed details hashes agree. Run3 requires
  at least 1272 correct for the final three-run mean to pass the frozen GSM8K
  gate; the controller advanced to run3;
- accepted Dk96 GSM8K run3: 1266/1319 = 95.981804%, 1319/1319
  successful, zero failures, exact unique indexes 0-1318; summary SHA256
  `c836f122866709835377dfbb5e2e60964adac6dda8baa28c3ccd80ff9a37231d`,
  details SHA256
  `5e11e9cbffe39d3262fc6dd88df5fd5a622404f9670bc4a70ec71776cd59df29`;
- final Dk96 GSM8K mean is 96.007076%, -0.303260 pp versus baseline.
  This exceeds the baseline three-run range 0.151630 pp, so Dk96 fails the
  frozen quality gate and is rejected. Profiling was intentionally not
  started under the preregistered rule;
- final summary completed with errors=0. Final evidence audit verified 9
  performance runs, 18 quality summaries/details, Dk96 container exited 0
  without OOM, NPU4-7 empty and port8225 free. NPU0-3 were not inspected.
  Report: `/cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/STATE_REDUCTION_PIERCING_REPORT.md`.
  Audit: `/cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/final-evidence-audit.json`;
- accepted treatment quality: LongBench-v2 run1 is 63/127 =
  49.606299%, summary SHA256
  `4396f56d515d2da5054b849c82757221d769ac183ec44d16df51d9527289046d`,
  details SHA256
  `5250567dfb8c4e5467e79e5d5f599bc4161e499432dabfda7f3d32e83f6079c5`;
  run2 is 59/127 = 46.456693%, summary SHA256
  `11aa6e11f133adef83234807b69fa743a202db0606bb9fee0fdcdd982ebfb5c8`,
  details SHA256
  `9cd5e4c2b93003a9f44cc9d9f0ea5dcd9943147f5a1356f990a5b3ec7638ec2e`.
  run3 is 62/127 = 48.818898%, summary SHA256
  `3821194a84c9c3eb4830a810aff349919fcef82b02db565b1161b18d7991b6af`,
  details SHA256
  `0ae2e181bdb0e0910b66fc62736532f543603715c2e16ad9698f3360e935b59a`.
  All three runs are 127/127 successful, zero-failure, exact-index audited.
  Their mean is 48.293963% (sample SD 1.639107 pp), +2.624672 pp
  versus the baseline mean, so LongBench-v2 passes the preregistered gate;
- accepted treatment GSM8K run1: 1269/1319 = 96.209249%, 1319/1319
  successful, zero failures, exact indexes 0-1318; summary SHA256
  `fab6abc4d9d53507831197951135a44854bb1e8eb3e7de9823adffee639e906d`,
  details SHA256
  `87045034f4144e8f25d707783c90bca3268560915f491c04bac896f1edd0a035`;
- accepted treatment GSM8K run2: 1267/1319 = 96.057619%, 1319/1319
  successful, zero failures, exact indexes 0-1318; summary SHA256
  `5929311e641cbbf32361b425b31fd137e4f9e759da1a08111ef9587d84d4c56d`,
  details SHA256
  `e72b72c3d623ae1236095a1f7256fd9bdcc11697d4366059bc8abb2c4237f274`;
- accepted treatment GSM8K run3: 1267/1319 = 96.057619%, 1319/1319
  successful, zero failures, exact indexes 0-1318; summary SHA256
  `bd62db3b496746471c76bf3d16bf55ccb3a5e076edc028e31a1bd66d7e71a508`,
  details SHA256
  `98925497b09f93df524a28058475e7b8a6d03a762ec12c91f1dfbf023b114314`;
- forbidden: any benefit, lossless, adoption or full-reproduction claim before
  treatment performance, repeated quality, native profiling and independent
  final audit.

Baseline performance raw run means:

| Run | TTFT ms | TPOT ms | output tok/s | measured duration s |
|---:|---:|---:|---:|---:|
| 1 | 40556.828397 | 75.804468 | 120.010388 | 341.303788 |
| 2 | 37443.801750 | 72.544506 | 128.687989 | 318.289223 |
| 3 | 37370.040124 | 72.537494 | 128.759025 | 318.113624 |
| mean | 38456.890090 | 73.628823 | 125.819134 | 325.902211 |

Dk64 treatment performance raw run means:

| Run | TTFT ms | TPOT ms | output tok/s | measured duration s |
|---:|---:|---:|---:|---:|
| 1 | 39843.659653 | 74.246411 | 122.245494 | 335.063475 |
| 2 | 36193.819163 | 70.412754 | 132.735702 | 308.583142 |
| 3 | 36198.085898 | 70.439270 | 132.710317 | 308.642169 |
| mean | 37411.854905 | 71.699479 | 129.230504 | 317.429595 |

Mean Dk64 changes versus baseline are TTFT -2.717420%, TPOT
-2.620365%, output throughput +2.711329%, and duration -2.599742%.
All directions are favorable, but the baseline and treatment three-run ranges
overlap. Therefore this is not yet evidence of a repeat-separated stable serving
benefit. Every performance file passed 40/40 success and exact 1024-token output
validation; Dk64 run3 SHA256 is
`17bc2e3f569bb07c524a329d22cb0540771cbb75b57b5301f54213961e1ac1d8`.

Dk96 treatment performance raw run means:

| Run | TTFT ms | TPOT ms | output tok/s | measured duration s | artifact SHA256 |
|---:|---:|---:|---:|---:|---|
| 1 | 40837.282183 | 76.028506 | 119.223907 | 343.555258 | `32a7d0136b98ac66056dd897c3516e14a8cc5af7a3f87ae5c649d0650f40e694` |
| 2 | 37025.522791 | 71.945349 | 129.837447 | 315.471391 | `91bcc4632fb251f95fe8ae422ae00b20ac8a3df76cc51b27803be4ae223b3190` |
| 3 | 37045.221750 | 71.934779 | 129.833092 | 315.481972 | `9e95f1c810a44e00bd33132cddfa2b5046d5e57906708dc3c8eecf2d848fdfc6` |
| mean | 38302.675575 | 73.302878 | 126.298149 | 324.836207 | — |

The Dk96 performance container exited 0 without OOM. Host NPU4-7 were
independently observed with no running process before quality started. NPU0-3
retained the external Qwen3.5 workload and were not altered.

Baseline repeated quality evidence:

| Dataset | runs (correct/total) | mean | sample SD | range |
|---|---|---:|---:|---:|
| LongBench-v2 | 56/127, 61/127, 57/127 | 45.669291% | 2.083269 pp | 3.937008 pp |
| GSM8K | 1269/1319, 1271/1319, 1271/1319 | 96.310336% | 0.087544 pp | 0.151630 pp |

These values define the predeclared quality guardrail. Dk64 and Dk96 both
completed all six quality repetitions. Dk64 GSM8K mean loss was 0.202173 pp
and Dk96 loss was 0.303260 pp; both exceed the baseline range 0.151630 pp.

Exact current-state check:

```bash
cat /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/controller-status.json
```

Operation `exec-0000000000000c1b` is terminal and successful. No experiment
resume is required. To regenerate and independently re-audit derived artifacts:

```bash
python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/summarize_state_reduction_formal.py --root /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906
```

Do not run the native-profile runner for this completed identity: the frozen
protocol intentionally skipped profiling after the Dk96 quality failure.
LoRA recovery, a new calibration corpus or another pruning ratio must receive
a new experiment identity and fresh same-denominator baseline.
