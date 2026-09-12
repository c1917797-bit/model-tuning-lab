## 模型信息

### 运行环境
- NPU 型号: Ascend 910B4
- 单卡 HBM: 32 GiB class; exact available/used memory must be captured for
  each live run
- 部署卡数: TP4/DP1 on physical NPU0-3; physical NPU4-7 protected
- 量化模式: none; BF16
- 执行模式: official vLLM-Ascend 0.23.0 image, ephemeral container,
  runtime patch by read-only mount and PYTHONPATH only

### 模型架构

Qwen3.5-27B dense hybrid model,
`Qwen3_5ForConditionalGeneration`, served as
`Qwen3-5/Qwen3.5-27B`. The measured scenario includes prefill and
autoregressive decode under TP4. Existing legacy profiling points to
decode-side row-parallel MatMulAllReduce/HCCL as a major hotspot, but that
profile is not yet accepted as the exact current-control round0 profile.

### 模型当前状态

The exact official-image control is runnable. A verified fresh-control
checkpoint completed activation, natural-EOS smoke, and one c1/c16 fail-fast
repetition with 32/32 requests and zero errors. The formal scenario is
`optimization-analysis/qwen35-27b-tp4-910b4/scenario.md`.
`agentic/baseline/baseline_metadata.json` now exists and explicitly records
that the checkpoint is partial: the complete c1/c5/c8/c16 three-repeat
baseline, exact-control round0 profiling, and perf-breakdown analysis remain
pending.

### 部署基线

- Image: `quay.io/ascend/vllm-ascend:v0.23.0`
- Image ID:
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
- Model: BF16, TP4/DP1, physical NPU0-3, no quantization, no MTP or
  speculative decoding
- Dataset: `/cache/cch/query_rewrite.jsonl`, SHA256
  `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`
- Fresh-control artifact:
  `/cache/austinov/qwen35-t12-aicpu-first-control-r2-20260909-064538`
- Observed first repetition:
  c1 TTFT/TPOT P95 `6310.5760/29.1070 ms`;
  c16 TTFT/TPOT P95 `30092.5770/210.9910 ms`
- Evidence boundary: these TTFT values contain cold/dynamic-compilation
  tails; c5/c8 and repetitions 2/3 are missing, so no final denominator is
  claimed.

## 场景与验收口径

- Performance grid: c1/c5/c8/c16, three repetitions, 32 frozen requests per
  cell, median of the three per-run P95 values.
- Target: TTFT P95 at least 40% lower and TPOT P95 at least 20% lower at
  every concurrency.
- Quality: 32-row length-stratified paired canary before expensive
  measurement; all 357 rows paired before promotion; temperature 0, seed
  1024, identical prompts, natural EOS, and zero material regressions.
- Dataset limitation: all 357 `answer` values are empty. The valid claim is
  paired semantic no-regression on this frozen workload, not general
  reference-answer accuracy.
- Final implementation boundary: runtime-only monkeypatch/plugin; no
  vLLM/vLLM-Ascend source mutation, image mutation, quantization, retraining,
  MTP, or speculative decoding.

## 已通过 Plan 速览

None. Existing t11/t12, AICPU-first, and IPC-fullmesh results are legacy
pre-CANNBot evidence and are not formal passed Plans.

## 当前 round 目标

Round0 prerequisites only:

1. Confirm the exact current-control runtime fingerprint against any proposed
   legacy profile reuse.
2. If equivalence cannot be proven, capture a fresh exact-control round0
   profile after the full resource gate.
3. Run `model-infer-perf-breakdown` with one fixed, user-confirmed
   structure/cluster breakdown spec.
4. Use the resulting time distribution and measured/theoretical operator gap
   to drive candidate discovery.

Do not initialize `plan-dashboard.md` until scenario, round0 profiling,
profile analysis, and candidate discovery prerequisites are complete.

## 进度概览
| 阶段 | 结论 | 性能变化 |
|------|------|---------|
| 场景定义 | 已记录 | 不适用 |
| 精度基线 | 部分完成；fresh control 可运行，32 canary 仅为既有候选的有界证据 | 不适用 |
| round0 profiling | 待采集或证明旧 profile 身份完全一致 | 未判定 |
| baseline perf-breakdown | 待分析 | 未判定 |
| 候选发现 / Dashboard | 尚未开始 | 未判定 |

<!-- ===== 以上为常驻区，不清除 ===== -->

<!-- ===== 以下为工作区，阶段推进时归档并清空 ===== -->

No active round implementation. This update created documentation only and
did not start, stop, inspect, or modify a container and did not use an NPU.

### 2026-09-09 round0 bounded profile analysis

Completed the requested four-rank prefill/decode breakdown from the existing
native msprof capture and frozen official-MMAR/GDN component artifacts. The
formal report is
`optimization-analysis/qwen35-27b-tp4-910b4/round0/perf-breakdown.md`.

Key findings: steady decode is dominated by the overlapping MMAR AICPU
envelope (about 28.0 ms/token on rank 0), while the prefill K1536 path has a
large rank skew: ranks 0/2/3 report roughly 7-8 ms AI Core intervals versus
0.15-0.55 ms on rank 1. Official isolated fused MMAR is 2.39-2.73x faster
than the full-model decode envelope, making lifecycle/queue/communication
diagnosis higher priority than isolated MatMul tuning. Fresh GDN fusion is
about 2.95x in the small-M microbenchmark but is not sufficient evidence for
the end-to-end target or for prefill.

True theoretical gaps remain **missing** because the capture lacks a
supported operator-theoretical artifact/chip configuration and a reliable
HCCL topology/bandwidth model. Overlapping AICPU, AI Core, and MatMul unions
were not added. This analysis did not start, stop, inspect, or modify a
container, did not use an NPU, and did not modify product/plugin code.

### 2026-09-11 T19 exact GDN-terminal budget

The exact T16 four-rank timeline now proves that the GDN terminal
`RMSNorm -> K1536 MMAR` seam cannot close the remaining c1 TPOT gap by
itself. Across 5,040 paired GDN calls per rank, median norm-start-to-envelope
end is 62.5-63.5 us. Its optimistic zero-cost upper bound is 3.048 ms/token
over 48 layers, versus 6.0985 ms/token required. It is rejected as a
standalone candidate and retained only as a possible stack component.

The next candidate-discovery step is source admission for the full dense
`gate_up -> SwiGLU -> K4352 MMAR` union. The external CANN image build was
still active, so this round intentionally performed no NPU timing.
