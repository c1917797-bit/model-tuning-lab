# KVarN to Ascend: bounded adaptation gate

Started 2026-09-23 17:42 UTC; stop this paper's first piercing loop by
2026-09-24 17:42 UTC. This is a source/profile gate, not an implemented
candidate or a performance/accuracy result. The target is Qwen3.6-27B BF16,
vLLM-Ascend v0.23.0/CANN 9.1, TP4 on physical NPU4–7, opt-in plugin delivery.

## Why this paper

The pinned four-rank dense decode profile (30 worker steps, 16-way concurrency)
has FusedInferAttentionScore at 27.40025% of summed operator time, 480 calls per
rank and about 360.9 ms per rank. Representative Q is `[16,6,256]` BF16 and
KV cache is BF16. A representative FIA row is about 0.75 ms, with AIC MAC
ratio 0.072 and AIC MTE2 ratio about 0.90. These counters motivate a KV-read
investigation; they do not prove HBM saturation, critical-path share, or a
10% end-to-end opportunity. The profile is
`/cache/cch/qwen36-paper-portfolio-synthesis-20260920/dense-profile-v1/profile-summary-v2.json`
(SHA256 `7d7554583eb202c26d51e946e8e3fd741e1a8578b1bba882f1af02104da06d81`).

[KVarN](https://arxiv.org/abs/2606.03458) has an
[author vLLM implementation](https://github.com/huawei-csl/KVarN), inspected
at `7586257f1c632e63187bfacbbe21ccb51540f7b3` in the read-only reference
checkout `/cache/cch/KVarN-paper-audit-20260923`. The author documents
Qwen3.6-27B hybrid-attention support: only full-attention KV is compressed;
GDN recurrent state is unchanged. Its mechanism is Hadamard rotation,
iterative two-axis variance normalization, and tile-wise asymmetric low-bit
quantization. The published `kvarn_k4v2_g128` preset is K4/V2; the cache uses
a packed tile record and a fused low-bit decode path. The target's native
attention block size 128 and head dim 256 match supported author geometry,
but this is only a shape match.

The author keeps the first 128 sink tokens and an in-progress tile in an
unquantized tail pool. A port must preserve that lifecycle, not simply
quantize each incoming KV token. The official configuration uses eight
variance-balancing iterations by default and aligns the packed D=256 tile
record for the vLLM cache allocator. These are part of the numerical and
memory-accounting contract to test on Ascend.

## Reuse and incompatibility

The deployed vLLM-Ascend source has an opt-in C8 KV path using INT8 cache,
ModelSlim-provided per-layer scales, and native FIA antiquantization. C8 is a
useful ABI/reference and possible **8-bit derivative** experiment, not a
faithful KVarN K4/V2 port. The inspected `ops-transformer` source documentation
for `aclnnFusedInferAttentionScoreV3` says Atlas A2 does not support BF16/FP16
query with INT4 KV. It describes an API/source capability, not proof of the
currently loaded binary's exact tiling. The author code's packed per-tile
record, two-axis scale metadata, tail lifecycle, and fused low-bit decode
cannot be passed unchanged to the native C8/FIA ABI. A faithful fast port
therefore needs a plugin-owned Ascend store/selected decode implementation or
another *verified* existing primitive with the same semantics. Do not modify
the upstream runtime, original image, or reference checkout.

## One-day decision sequence

1. Pin the serving image, real loaded FIA/CANN library identities, NPU4–7
   ownership and an existing dense baseline. Do not repeat profiling unless
   an exact kernel/tiling question remains unanswered.
2. Reproduce the author tile math on a real NPU for D=256, group=128, K4/V2:
   rotation, best-so-far variance balance, pack/depack and full-support
   attention against the author's PyTorch reference. Preserve any failed
   case; do not relax the numerical gate to manufacture a pass.
3. Audit the pinned `ops-transformer` kernel/ABI for a reusable low-bit path.
   If absent, use CannBot only for a precisely specified paper-specific
   store/decode operator; keep source/build identity in the plugin repository.
4. Require eager and NPUGraph state/output checks, including cache-tail,
   mixed prefill/decode, prefix identity and repeated replay, before a service
   performance screen. An INT8 adaptation must be labeled KVarN-derived and
   separately validated; it is not the author's K4/V2 result.
5. Run a single profiler-disabled matched dense/candidate fixed-1024 service
   screen only after correctness. Report throughput, TTFT and TPOT. A
   promising candidate proceeds to repeated performance and matched
   LongBench-v2/GSM8K with 2048 max output, no thinking, normal EOS; the
   latest user allowance is at most one percentage point loss per task.

At the 24-hour limit, record `accepted`, `rejected`, `inconclusive`, or
`failed` with exact scope. Do not call a source/API incompatibility a
paper-wide no-go, and do not promote capacity or a kernel microbenchmark to
the required end-to-end throughput gain. If no NPU-valid service candidate
exists by the deadline, preserve evidence and move to the next measured
attention/IO paper rather than continuing this loop indefinitely.
