# ENEC lossless weight compression: current-service applicability gate

Date: 2026-09-28 UTC. This is a paper/source and live-launch applicability
decision, not a new NPU candidate, benchmark, or paper-wide rejection.

## Mechanism and source

- Paper: https://arxiv.org/html/2604.03298v2, especially Section VI-C.
- Released code: https://github.com/hpdps-group/ENEC. The authors target
  Ascend 910B2/CANN 8.2 and implement a lossless BF16 weight compressor and
  NPU decompressor. They explicitly compare against a **single-NPU** baseline
  that keeps most weights on NPU and repeatedly transfers offloaded layers
  from CPU. Their TTFT/TPOT gains come mainly from avoiding those transfers.
- This is not a faster BF16 GEMM or attention algorithm. A faster decompressor
  cannot remove per-token CPU-to-NPU weight transfers if the serving path has
  no such transfers.

## Installed target and decision scope

The frozen target is Qwen3.6-27B BF16, vLLM-Ascend v0.23.0/CANN 9.1,
TP4 on physical NPU4-7. The recorded FFD v5 service launch in
`tools/run_ffd_real_probe.py` maps exactly those four cards, sets
`--tensor-parallel-size 4`, has no CPU weight-offload option, and successfully
served a 20,718-token request. The existing dense profile attributes the
decode hot path to on-device MatMul and attention; it does not report a
per-layer CPU weight-transfer seam. This proves the current service can run
with the BF16 checkpoint resident across four cards. It does **not** prove
that every possible workload or memory-pressure regime avoids offload.

Decision: **inapplicable to the frozen TP4 steady decode service as the next
paper-specific +10% route**. Porting ENEC's compressor/decompressor here would
address a different, absent CPU-offload bottleneck. Do not manufacture that
bottleneck by forcing a single-card baseline, nor transfer the paper's 4.1x
TTFT / 3.9x TPOT claim to this setup. ENEC remains potentially useful for a
separately authorized model-too-large/CPU-offload workload, provided that
live transfer time is first measured and a fresh matched control is defined.

Historical local artifacts relevant to the next quantization screen already
exist under `/cache/cch/qwen36-smoothquant-20260923/` and
`/cache/cch/qwen36-awq-w4a8-20260923/`. Their summaries are screening clues,
not current matched acceptance evidence. Reuse their source/checkpoint
identities and failure record before any new W4A8 candidate; do not repeat
an unchanged conversion or call a native quantization path a novel paper gain.

No NPU load was started for this ENEC gate. Physical NPU4-7 were observed
idle at 0% AICore, no process, about 2868-2872 MB HBM on this date.
