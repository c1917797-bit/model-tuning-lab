# Workstream Handoff — WS-20260904-qwen38-dense-paper-to-ascend

Updated: 2026-09-06T17:36:53Z

## Status

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

Final destination authorized by the operator:
`https://github.com/c1917797-bit/model-tuning-lab`.
Use the existing configured Git identity and do not overwrite upstream
`origin`.
