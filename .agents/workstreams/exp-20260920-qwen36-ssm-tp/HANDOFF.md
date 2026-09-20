# Scaling SSM Tensor Parallelism — Qwen3.6/Ascend piercing

## Status

- Stage: completed / rejected at the applicability gate.
- Start: 2026-09-20.
- Hard timebox: 24 hours from workstream start.
- Queue position: 7. HYPIC is a previously completed successful template, not
  part of this workstream.
- Resource lane: physical NPU4-7 only; port 8228.

## Paper fidelity

- Paper: arXiv:2602.21144v1, Scaling State-Space Models on Multiple GPUs with
  Tensor Parallelism.
- The paper contributes channel-wise model/state/cache sharding,
  packed-parameter-aware partitioning, and optional FP32-to-FP16 AllReduce
  payload conversion.
- The paper evaluates Mamba-family models on NVIDIA GPUs. Qwen3.6 uses a gated
  delta-rule recurrent mixer, so this is a mechanism adaptation rather than an
  identical model reproduction.
- The paper states that implementations will be made public upon acceptance.
  No official source release was located as of 2026-09-20. Any implementation
  here must be labelled an independent adaptation, not official-code fidelity.

## Applicability evidence already established

- Qwen3.6 GDN projection and recurrent/conv state are already sharded by TP.
- q/k/v/z/beta/alpha packed parameter loading is already TP-aware.
- Recurrent and convolution operations remain local to each TP shard.
- The GDN output projection is row-parallel and therefore has a residual
  boundary collective.
- vLLM-Ascend v0.23 exposes ordinary AllReduce, MM-AllReduce fusion and
  ReduceScatter paths. Live TP4 evidence proved that all 48 GDN output
  projections on all four ranks select fused MM-AllReduce.

These existing features cannot be counted as candidate gains. The live selected
path also already carries BF16 inputs, weights and outputs, so the paper's
optional FP32-to-FP16 communication conversion is not a remaining candidate.

## Predeclared gate

1. Instrument a fresh Qwen3.6 TP4 service to record the selected GDN output
   projection class, collective kind, payload dtype, tensor geometry and call
   count in all four workers.
2. Run a bounded 30-decode-step NPU profile and distinguish communication
   critical path from summed kernel time.
3. Abort if the collective payload is already BF16 and the paper's optional
   FP32-to-FP16 conversion is therefore a no-op or would reduce precision.
4. Abort if communication is below the Amdahl threshold: 9.09% even for total
   removal, or 18.18% for a credible 2x communication speedup.
5. If a real lossless opportunity remains, implement it only as an independent,
   explicitly enabled plugin/monkeypatch. Do not modify vLLM, vLLM-Ascend,
   CANN, the image, or the model.
6. Pass real-NPU exact greedy replay before performance.
7. Formal performance uses 40 requests, concurrency 16, fixed 1024-token
   output, three repetitions per arm with identical common optimizations.
8. Final acceptance also requires no LongBench-v2 or GSM8K loss at thinking
   off, temperature 0, seed 0, max_tokens 2048 and normal EOS.

## Final NPU evidence

- Probe container: `qwen36_ssm_tp_inventory_mmar_v1_20260920`, exited 0 and
  preserved.
- All four worker host PIDs were proven on physical NPU4-7.
- 192/192 layer/rank selection events used
  `MatmulAllreduceRowParallelOp`.
- Forty-four sampled runtime calls covered startup warmup, a 30-token request
  prefill and decode. All four ranks reported BF16 input, weight and output
  tensors.
- Input geometries observed: `(10240,1536)`, `(30,1536)`, and
  `(1,1536)`; corresponding outputs ended in 5120 hidden channels.
- Evidence:
  `/cache/cch/ssm-tp-qwen36-npu4-7-20260920/inventory-mmar-v1/evidence.jsonl`
  (SHA256
  `7e45b0f74b11bf7044e3d9bb2e381dc5a1eeeb07c917ec10e3e23e8ac2344f91`).

## Decision

Reject this paper as a distinct Qwen3.6/vLLM-Ascend v0.23 plugin optimization.
The relevant sharding is already upstream, fused MM-AllReduce is already
selected, and its actual payload is already BF16. FP32-to-FP16 conversion would
be a no-op; lowering below BF16 would violate the lossless/no-accuracy-loss
boundary.

No performance or task-accuracy test was run because no candidate changed the
execution path. An A/B between identical paths would be invalid evidence.
Physical NPU4-7 were released after the canary. The read-only probe remains
available for future runtime/version audits and is inert unless explicitly
enabled.

## Next action

Advance to queue position 8, EPD-Serve, and apply an early deployment-boundary
gate before using NPU time.
