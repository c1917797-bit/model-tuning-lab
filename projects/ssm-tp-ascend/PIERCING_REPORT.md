# Scaling State-Space Models with Tensor Parallelism — Ascend piercing report

## Current decision

- Paper: arXiv:2602.21144v1.
- Target: Qwen3.6-27B, vLLM/vLLM-Ascend 0.23.0, CANN 9.1, TP4,
  physical NPU4-7.
- Delivery boundary: independent opt-in plugin/monkeypatch.
- Status: rejected at the applicability gate; no performance or accuracy claim.

## Mechanism mapping

| Paper mechanism | Current Qwen3.6/vLLM-Ascend state | Candidate status |
| --- | --- | --- |
| Channel-wise SSM sharding | GDN q/k/v/z and local recurrent/conv work are already TP-sharded | Existing upstream capability |
| Sharded recurrent/conv cache | State shapes and cache indices include TP partitioning | Existing upstream capability |
| Packed-parameter-aware partitioning | Qwen GDN packed weights use TP-aware loaders | Existing upstream capability |
| FP32-to-FP16 AllReduce payload | Live prefill/decode inputs, weights and outputs are already BF16 | No distinct lossless candidate |
| Communication/computation fusion | 192/192 layer/rank selections used fused `MatmulAllreduceRowParallelOp` | Existing selected production path |

## Evidence boundary

The paper evaluates Mamba-family models on NVIDIA GPUs and did not expose
official code at the time of this audit. This workstream is an independent
Qwen3.6/Ascend adaptation. It will not claim paper reproduction merely because
the runtime already implements related TP sharding.

## Live TP4 evidence

The read-only plugin instrumented all four workers without changing selection or
numerics:

- 48 GDN output projections times four ranks produced 192 selection events; all
  selected `MatmulAllreduceRowParallelOp`.
- Forty-four sampled calls covered warmup, request prefill and decode on all
  four ranks. Inputs, weights and outputs were BF16 in every sample.
- Observed input shapes were `(10240,1536)`, `(30,1536)`, and
  `(1,1536)`; output shapes were `(10240,5120)`, `(30,5120)`, and
  `(1,5120)`.
- One bounded request completed only to exercise prefill/decode hooks. Its
  latency and text are not benchmark or accuracy evidence.
- Evidence SHA256:
  `7e45b0f74b11bf7044e3d9bb2e381dc5a1eeeb07c917ec10e3e23e8ac2344f91`.

## Final decision

The paper does not leave a distinct, lossless plugin candidate on this stack.
Its state/cache/channel sharding and TP-aware packed loading are already
implemented upstream. The live boundary already uses fused MM-AllReduce with
BF16 payloads, so FP32-to-FP16 conversion is a no-op; reducing below BF16 would
violate the no-accuracy-loss boundary.

The predeclared applicability abort condition therefore fired. Profiling,
end-to-end A/B performance, LongBench-v2 and GSM8K were intentionally skipped:
there was no changed candidate path to compare. This is a scoped no-go for
Qwen3.6-27B on vLLM-Ascend v0.23, not a claim that the paper lacks value on a
runtime that still communicates FP32 state-space activations.
