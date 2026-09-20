# Scaling SSM Tensor Parallelism — Qwen3.6/Ascend piercing

## Status

- Stage: planned / applicability gate in progress.
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
  ReduceScatter paths. Which one Qwen3.6 actually selects is not yet proven.

These existing features cannot be counted as candidate gains. The only
remaining paper-derived opportunity is communication optimization on the real
selected path.

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

## Immediate next action

Complete source selection audit for RowParallelLinear, then add a read-only
runtime probe that reports the selected GDN output-projection implementation
and payload dtype. Launch one fresh non-privileged TP4 service on physical
NPU4-7 only after rechecking devices, containers, ports and memory.
