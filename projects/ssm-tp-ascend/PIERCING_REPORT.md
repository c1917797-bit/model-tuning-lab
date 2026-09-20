# Scaling State-Space Models with Tensor Parallelism — Ascend piercing report

## Current decision

- Paper: arXiv:2602.21144v1.
- Target: Qwen3.6-27B, vLLM/vLLM-Ascend 0.23.0, CANN 9.1, TP4,
  physical NPU4-7.
- Delivery boundary: independent opt-in plugin/monkeypatch.
- Status: applicability gate in progress; no performance or accuracy claim.

## Mechanism mapping

| Paper mechanism | Current Qwen3.6/vLLM-Ascend state | Candidate status |
| --- | --- | --- |
| Channel-wise SSM sharding | GDN q/k/v/z and local recurrent/conv work are already TP-sharded | Existing upstream capability |
| Sharded recurrent/conv cache | State shapes and cache indices include TP partitioning | Existing upstream capability |
| Packed-parameter-aware partitioning | Qwen GDN packed weights use TP-aware loaders | Existing upstream capability |
| FP32-to-FP16 AllReduce payload | Applicability unknown; model activations are BF16 | Must prove real collective dtype |
| Communication/computation fusion | vLLM-Ascend exposes fused MM-AllReduce and ReduceScatter paths | Must prove selected production path |

## Evidence boundary

The paper evaluates Mamba-family models on NVIDIA GPUs and did not expose
official code at the time of this audit. This workstream is an independent
Qwen3.6/Ascend adaptation. It will not claim paper reproduction merely because
the runtime already implements related TP sharding.

The first valid decision depends on live TP4 evidence: selected collective,
payload dtype, tensor geometry, call count and critical-path contribution. No
operator microbenchmark or summed kernel duration will substitute for
end-to-end evidence.
