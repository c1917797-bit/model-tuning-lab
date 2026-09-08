# Qwen3.5 Performance Optimization

This directory is the reviewable home for Qwen3.5 inference-performance
experiments in Model Tuning Lab. It keeps the benchmark protocol, decision
gate, and safe runner together while operator source changes remain in the
separate
[`ops-transformer-lab`](https://github.com/c1917797-bit/ops-transformer-lab)
repository.

## Current candidate

The current candidate evaluates an opt-in asynchronous HCCL finalize path for
Qwen3.5-27B row-parallel decode MMAR on Ascend 910B4:

- tensor parallelism: TP4 on physical NPU0-3;
- dtype: BF16;
- exact shapes: `M=1, K=1536, N=5120` and
  `M=1, K=4352, N=5120`;
- activation switch:
  `ASCEND_MATMUL_ALLREDUCE_M1_ASYNC_FINALIZE=1`;
- baseline/candidate comparison: frozen one-switch A/B;
- no quantization, retraining, MTP, or speculative decoding.

The operator implementation is disabled by default and fails closed outside
the exact shape and datatype gate. The source-level candidate is available in
the
[`feature/qwen35-m1-async-finalize`](https://github.com/c1917797-bit/ops-transformer-lab/compare/main...feature/qwen35-m1-async-finalize)
branch comparison.

## Contents

- `scripts/benchmark_qwen35_mmar_async_finalize.py` measures both exact
  decode shapes across four HCCL ranks, captures deterministic correctness
  evidence, and runs at least 5,000 alternating-shape stress calls per rank.
- `scripts/evaluate_qwen35_mmar_async_finalize.py` compares frozen baseline
  and candidate artifacts, enforcing per-shape performance, geometric-mean,
  correctness, and stress gates.
- `scripts/run_qwen35_mmar_async_finalize_frozen_ab_npu03.sh` owns the
  end-to-end safety envelope: cooperative NPU0-3 lease, live device/container/
  port checks, one-shot containers, immutable image verification, provenance,
  and SHA256 manifests.

## Status and evidence boundary

The harness and operator build are validated, but this candidate is not an
accepted end-to-end optimization yet. It must not be described as meeting the
2x TTFT/TPOT objective until the frozen c1/c5/c8/c16 service protocol,
correctness gate, and repeated P95 measurements pass.

Existing broader-workstream evidence remains:

- best trusted TTFT P95 speedup: about `1.913x`;
- best trusted TPOT P95 speedup: about `1.208x`.

Those numbers belong to the earlier bounded-MMAR service candidate and are not
performance claims for the async-finalize source change.

## Safe execution

The runner requires explicit paths and digests for both operator packages and
refuses to reuse an existing output directory:

```bash
export OUTPUT_ROOT=/cache/austinov/<new-artifact-directory>
export BASELINE_OPP_ROOT=/absolute/path/to/baseline-opp
export BASELINE_OPP_ENV=/absolute/path/to/baseline/set_env.bash
export BASELINE_OPERATOR_COMMIT=<full-commit>
export BASELINE_PACKAGE_SHA256=<sha256>
export CANDIDATE_OPP_ROOT=/absolute/path/to/candidate-opp
export CANDIDATE_OPP_ENV=/absolute/path/to/candidate/set_env.bash
export CANDIDATE_OPERATOR_COMMIT=<full-commit>
export CANDIDATE_PACKAGE_SHA256=<sha256>

./qwen35-performance-optimization/scripts/run_qwen35_mmar_async_finalize_frozen_ab_npu03.sh
```

Before execution, independently prove that NPU0-3 and ports 29943-29944 are
available and that no active workstream owns them. NPU4-7 are never exposed to
the runner.

The default image is
`quay.io/ascend/vllm-ascend:v0.23.0`. It is started with `--rm`; operator
packages and the repository are mounted from the host. The runner performs no
package installation and no `docker commit`, and verifies that the image ID
and repository digests are unchanged after the A/B.

## Required decision artifacts

Each run produces baseline and candidate JSON, logs, before/after NPU,
container, process, and port snapshots, a provenance record, `decision.json`,
and `SHA256SUMS`. Keep generated outputs under `/cache/austinov`; do not
commit datasets, model weights, credentials, raw profiler traces, or generated
benchmark artifacts.
