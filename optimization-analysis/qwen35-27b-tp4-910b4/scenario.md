# Qwen3.5-27B TP4 Ascend 910B4 inference scenario

## Scope and objective

- Case: `qwen35-27b-tp4-910b4`.
- Repository: `/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery`.
- Model architecture: `Qwen3_5ForConditionalGeneration`.
- Model checkpoint: `/cache/austinov/Qwen3.8-27B`, served as
  `Qwen3-5/Qwen3.5-27B`.
- Framework image: the unchanged official
  `quay.io/ascend/vllm-ascend:v0.23.0`.
- Hardware and topology: Ascend 910B4, TP4/DP1 on physical NPU0-3 only.
  Physical NPU4-7 are excluded and protected.
- Precision: BF16, `quantization=None`.
- Excluded methods: retraining, MTP, speculative decoding, base-image
  mutation, vLLM/vLLM-Ascend source replacement, and final source overlays.
- Goal: at each of c1/c5/c8/c16, reduce median-of-three per-run TTFT P95 by
  at least 40% and TPOT P95 by at least 20%, with zero material semantic
  regressions.

## Runtime identity

The verified fresh-control artifact records:

- image ID:
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`;
- repository digest:
  `sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a`;
- model-config SHA256:
  `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`;
- tokenizer-config SHA256:
  `b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27`;
- weight-index SHA256:
  `77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df`.

The control must remain an ephemeral `--rm` container. The base image and
its site-packages are immutable. Any candidate code is loaded from a
read-only mount through `PYTHONPATH`; rollback is container recreation
without candidate activation.

## Reproducible input and generation protocol

- Dataset: `/cache/cch/query_rewrite.jsonl`.
- Dataset SHA256:
  `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`.
- Dataset size: 3,305,726 bytes and 357 JSONL rows.
- Prompt source: the row's raw `question` field. Raw questions, answers,
  and generated responses are confidential and are not committed.
- Performance selection: the frozen 32-request set defined by the experiment
  contract at each concurrency.
- Concurrency: 1, 5, 8, and 16.
- Repetitions: three per concurrency for a final decision.
- Decoding: temperature 0, seed 1024, natural EOS, and per-request
  `max_tokens` equal to the model-context remainder returned by
  `/tokenize`.
- Cache isolation: every warmup and measured request uses a run-unique
  `cache_salt`; warmup is excluded from measurement.
- Primary metrics: TTFT P95 and TPOT P95. P50 and P99 are diagnostic; a
  repeatable P99 regression above 10% is a commercial tail-risk flag.

The authoritative protocol is
`.agents/experiments/exp-20260904-qwen35-query-rewrite-3x-e2e.yaml`.
This service does not use the CANN Recipes `infer.sh`/YAML entry convention;
the maintained vLLM service launcher and benchmark driver below are the actual
scenario entry points.

## Reproduction commands

Run only after the host-maintenance resource gate proves NPU0-3 have no
process or container declaration, NPU4-7 are excluded, the selected ports are
free, MemAvailable is at least 48 GiB, and the cooperative NPU0-3 lease is
held for the complete container lifetime.

```bash
cd /opt/host/vnf/austinov/worktrees/qwen35-performance-delivery

VARIANT=control \
OUTPUT_ROOT=/cache/austinov/qwen35-control-<unique-run-id> \
bash qwen35-performance-optimization/scripts/start_qwen35_gdn_runtime_t12_supervised.sh

python3 scripts/run_qwen35_benchmark_matrix.py \
  --experiment-contract .agents/experiments/exp-20260904-qwen35-query-rewrite-3x-e2e.yaml \
  --model Qwen3-5/Qwen3.5-27B \
  --base-url http://127.0.0.1:10010 \
  --variant baseline \
  --run-id <unique-run-id> \
  --output-root /cache/austinov/qwen35-control-matrix-<unique-run-id>
```

Every output root and run ID must be new. These commands document the
reproduction contract; creating this scenario record did not execute them.

## Verified fresh-control checkpoint

Fresh-control root:
`/cache/austinov/qwen35-t12-aicpu-first-control-r2-20260909-064538`.

The activation report passed and recorded exactly one TP worker on each
physical NPU0-3, no NPU4-7 process, no privileged container, no source
overlay, the expected official image, and API readiness. The fixed smoke
ended naturally. The following first fail-fast repetition completed 32/32
requests with zero errors and natural EOS:

| Concurrency | TTFT P95 (ms) | TPOT P95 (ms) | Artifact |
| ---: | ---: | ---: | --- |
| 1 | 6310.576018947177 | 29.10703386078306 | `failfast/c1-r1.json` |
| 16 | 30092.57700643502 | 210.99100931006572 | `failfast/c16-r1.json` |

These TTFT observations contain pronounced cold/dynamic-compilation tails.
They prove the scenario runs and provide a fresh-control checkpoint, but they
are not the final denominator: c5/c8 and the remaining repetitions were not
collected for this control. A final performance claim requires a fresh,
same-environment, complete three-repeat control matrix.

## Machine-checkable quality contract

The quality gate is paired, same-runtime control versus candidate:

1. Before expensive performance measurement, capture a 32-row
   question-length-stratified canary with identical row indices, temperature
   0, seed 1024, per-request context remainder, and natural EOS.
2. Byte-identical responses pass automatically. Every differing response
   pair must be reviewed for retained intent, facts, constraints,
   completeness, and readability. Any material regression rejects the
   candidate.
3. Before promotion, repeat the paired protocol for all 357 rows. Require
   zero request errors, natural EOS for every request, and zero material
   regressions across every differing pair.
4. Raw paired captures remain restricted evidence under `/cache` with mode
   0600 and are never committed.

The existing 32-row AICPU-first canary is bounded evidence only: 24/32 outputs
were byte-identical, all eight differences were reviewed as equivalent or
better, and zero material regressions were recorded. It does not prove the
full 357-row requirement and does not transfer to a different candidate.

All 357 dataset `answer` fields are empty. Therefore answer similarity,
absence of an answer mismatch, and cross-run response hashes alone cannot
prove general model accuracy or “精度无损”. The permitted claim is limited
to paired semantic no-regression on this frozen workload and exact runtime
protocol.

## Performance acceptance contract

For each concurrency independently, compute the median of three per-run P95
values:

- `candidate_ttft_p95 / control_ttft_p95 <= 0.60`;
- `candidate_tpot_p95 / control_tpot_p95 <= 0.80`.

All 12 control cells and all 12 candidate cells must complete 32/32 requests
with zero errors and natural EOS. Do not mix TP8 results, historical source
overlay results, cold single repetitions, a different image/runtime, or a
different device topology into this denominator.

## Current blockers and next evidence

- The current exact-control round0 CANN profile and a CANNBot
  `model-infer-perf-breakdown` analysis have not yet been produced.
- The verified fresh control is an incomplete c1/c16 fail-fast checkpoint,
  not a complete c1/c5/c8/c16 three-repeat baseline.
- No current candidate has passed both the 40% TTFT and 20% TPOT target.
- The full 357-row paired quality gate remains candidate-specific and pending.

The next hardware action, only after a fresh resource gate, is to capture the
exact-control round0 profile and analyze it under a fixed breakdown spec.
Do not initialize a Plan Dashboard before that prerequisite and candidate
discovery are complete.
