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

## 2026-09-24 environment gate checkpoint

The equation-derived diagnostic is
`tools/run_kvarn_tile_npu_probe.py`; it is not the author's CUDA/Triton
implementation and does not establish paper fidelity, cache integration,
performance, or accuracy. Static AST inspection passed and a wrong key
transpose was corrected before launch. The physical NPU4 -> container NPU0
attempt failed before numerical operations: `torch.npu.get_device_name(0)`
reported invalid device id. The first failure is retained in stopped Docker
container `qwen36_kvarn_tile_npu4_v1_20260924`. A second attempt with the
driver mounted wrote
`/cache/cch/qwen36-kvarn-ascend-20260923/tile-npu-v2/report.json`, status
`failed`, zero completed cases. Default-network, preserved-physical-ID, and
four-card 4–7 visibility canaries also reported HAL device count zero; no
KVarN numerical result was produced.

The host still reported healthy/idle NPU4–7, but kernel logs showed UDA
`Conflict open udevid=4; ns_id=0`. `/proc/uda/namespace_node` mapped device
4 and the other devices to `root_tgid=2178262`; its cgroup identified running
container `agentgpu-910b4-qwen35-4b-aiv-v1`. `docker top` showed only
`sleep infinity`, yet its UDA namespace held device 4. A requested stop was
rejected by safety review because that container maps physical NPU0–7,
outside the protected 4–7 scope. No container was stopped or deleted, and no
indirect namespace workaround was used. This is an environment blocker, not
a paper no-go. Continue paper-specific store/decode preparation while the
device boundary is resolved; do not launch a service or claim throughput.

## 2026-09-24 UDA release and tile numerical checkpoint

After a fresh owner/process check, the operator-authorized stop of
`agentgpu-910b4-qwen35-4b-aiv-v1` released its UDA namespace without deleting
the container. A new, non-overwriting run in
`qwen36_kvarn_tile_npu4_v3_20260924` exposed **only physical NPU4** as
container NPU0 (image digest
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`).
The report is
`/cache/cch/qwen36-kvarn-ascend-20260923/tile-npu-v3/report.json`, SHA256
`e5cd4605c6558bb3f590eb36f7c77b94f74e27bcf88b47127637236c1c454f9d`;
the probe script is SHA256
`1095f7e90ab7475b08a7a79a5d3cdb84412d84c459dbed9037a96eb03d5970a3`.

The equation-derived NPU smoke completed at batch 1 and 16: K and V pack
roundtrips were exact, all tested tensors finite, and the shared-packed-state
NPU-vs-CPU attention maximum absolute difference was at most `1.05e-7`.
Independently quantizing on CPU and NPU yielded a few different packed values
(K/V: 3/1 at batch 1, 12/5 at batch 16). The synthetic quantized-vs-dense
attention cosine was only 0.898/0.875, so **the report's `passed` status is a
backend shared-state execution/parity gate only**, not proof of model accuracy.
It is not the author's CUDA/Triton backend, vLLM cache integration, NPUGraph
validation, or an end-to-end throughput result. The next gate must establish
author-reference parity and a plugin-owned store/decode lifecycle before any
service performance claim.

## 2026-09-24 pinned author-reference parity checkpoint

`tools/run_kvarn_author_parity_probe.py` loaded the author's unmodified
PyTorch `sinkhorn.py`, `kvarn_store.py`, and `kvarn_decode.py` from Git commit
`7586257f1c632e63187bfacbbe21ccb51540f7b3` in a read-only mount. On
physical NPU4 (container NPU0), both batch 1 and 16 produced **bitwise exact**
K/V balanced tiles, scales, packed bytes, and dequantized tiles against our
equation probe. The one-shot container exited 0. The report is
`/cache/cch/qwen36-kvarn-ascend-20260923/author-parity-npu-v1/report.json`,
SHA256 `82eb48e487dee907cdf98bcb536b94c04c11a90008cde46b8e56fa32040dcce1`.

This proves the tested tile equations and byte layout match the pinned author
reference on this NPU. It does **not** prove the author's fused kernel, sink
and tail management, cache allocator integration, graph replay, end-to-end
speed, or LongBench-v2/GSM8K accuracy. Those remain mandatory gates.

## 2026-09-24 Triton Ascend mixed-record failure checkpoint

The v0.23 serving image contains Triton 3.2.0 with an Ascend backend, but not
TileLang. A plugin-owned, opt-in K4/V2 dequant primitive was attempted at
`plugin/qwen36_kvarn_ascend/tile_dequant.py`, tested by
`tools/run_kvarn_triton_dequant_probe.py` on physical NPU4 only. This is a
paper-specific operator prerequisite, **not** an attention or service result.

- `triton-dequant-npu-v1/report.json` (SHA256
  `88c3e0a77219780e5593214221ecc18cbbce6356cf5082c44bbe4b9dc7c4ceb3`):
  Triton rejected module-level byte-offset globals before compiling. The
  offsets were changed to explicit `tl.constexpr` parameters.
- `triton-dequant-npu-v2/report.json` (SHA256
  `901278b6142081eb2ff471d9985659f5f35a00069ee56726b4cd12cbef8b2f1e`):
  Ascend codegen rejected the source `uint8*` to `uint16*` cast used to load
  FP16 metadata. The next implementation used author-style two-byte loads.
- `qwen36_kvarn_triton_dequant_npu4_v3_20260924` exited 133 during compiler
  lowering with `InterleaveOptimization.cpp:136` asserting that a
  reinterpret-cast offset addend must equal one. No v3 JSON report was
  written; its preserved Docker log is the failure artifact. The operator
  SHA256 for this attempt is
  `ffc10883dfd5dec55c638f3fc55a60a57d7df68739999019fa42443d7e29d170`.

No test reached NPU dequant output, so numerical correctness remains
**unproven**. This is an implementation/compiler limitation for the mixed
`uint8`+FP16 record access, not evidence against KVarN's quantization or
attention mechanism. Next investigate a split-tensor metadata layout (packed
K/V bytes plus typed FP16 scale arrays) within the same plugin; only if that
passes can it be fused with decode and evaluated as a service candidate.

## 2026-09-24 split-metadata Ascend operator checkpoint

The plugin's `tile_dequant_split.py` separates packed K4/V2 payload bytes
from typed FP16 row/column scale and zero-point tensors while retaining the
pinned author's dequant equations. The first physical-NPU4 run failed before
output: BiShengHIR reported unsupported `uint32_t_to_float_rintmode` for a
Triton cast. Its report is `triton-split-npu-v1/report.json` (SHA256
`e3b3a1fa8d09ffe86098d9489565b9fd7a129219d2b791eea90375c32fc08f48`).
Since packed values are only 0–15 (K) or 0–3 (V), converting the byte to
signed int32 before floating conversion preserves their values exactly.

The corrected one-shot run `qwen36_kvarn_triton_split_npu4_v2_20260924`
compiled and passed on physical NPU4 / container NPU0. Both batch/tile
counts 1 and 16 gave finite **bitwise exact** K and V dequantized tiles versus
the pinned author's Python reference: zero mismatches and maximum absolute
error 0. Its immutable report is `triton-split-npu-v2/report.json` (SHA256
`ade9b3316e1fc845d6d170d20fa92d324f5e817724edb72b6baf2248dfa8ad14`);
operator SHA256 is
`75436f425b7c8c0d1e5ff26a8d62a309f0f3fff4fa75774d043060f105b992ca`.

This is a successful **operator numerical prerequisite**, not a KVarN service
candidate. It does not include fused attention, the sink/tail lifecycle,
cache manager, NPUGraph, end-to-end throughput, or model-task accuracy. The
split layout also changes the original packed-record cache ABI and must be
costed against the matched dense service; it cannot be assumed faster merely
because tile math is correct. Next gate is service-path feasibility, then
graph/state correctness, then a paired fixed-1024 E2E screen if time permits.

## 2026-09-24 fused attention and mixed-cache compiler checkpoint

`tile_attention_split.py` performs K4/V2 dequant inside the attention kernel,
without a full FP16 KV materialization to HBM. Its physical-NPU4 one-tile
test passed for 1 and 16 independent requests, with six local Q heads per KV
head. Against a full-precision-softmax reference over the author's restored
tile, the maximum absolute output error was `6.103515625e-5`, all outputs
finite. Report: `one-tile-attention-npu-v1/report.json`, SHA256
`1a06775dce9ec978eda7bc4edc63a5d4dd678b08b421bd34dc4a9ceb277d1522`;
operator SHA256
`a142845465e82ce17388b065c0a6e5d8bd775a2c2a486e4828347c75316791e5`.
This proves a narrow fused-compute compiler and numerical seam, **not** a
service or performance gain.

The first 3-block mixed-cache operator `decode_split.py` uses a block table
for an FP16 sink, compressed middle block, and partial FP16 tail. Four
non-overwriting NPU attempts were retained:

- `mixed-decode-npu-v1/report.json` (SHA256
  `c7f5027ab923237487227f7eb66240f17a721f4bbf77c188f517ae38096e3a63`):
  Triton variable-scope error before code generation.
- `mixed-decode-npu-v2/report.json` (SHA256
  `0f305c4e27620ad41c4f3ce0d1a899e2eeb85e77f2e02bc32b51ae559aeab674`):
  BiShengHIR rejects cbuf-to-cbuf copy with a dynamic sink/compressed branch.
- `mixed-decode-npu-v3/report.json` (SHA256
  `2d6e84cdc923f4330970049477e5e733c1c9740e48fadfe5c7182f9331e40566`):
  branchless source selection still hits the same cbuf-copy lowering failure
  because the dynamic nested loops remain.
- `mixed-decode-npu-v4/report.json` (SHA256
  `feb3519d814a7af80578e00105ce0f8fd142c184c404cb51d4f9926b4d3014ef`):
  removing those runtime branches moved compilation to memory planning, which
  rejects a 32×64×4 FP16 intermediate alignment.

All four fail **before** mixed attention executes. The validated one-tile
fused result must not be promoted to mixed-cache correctness. The next
algorithm-specific Ascend adaptation is to split compressed and FP16-pool
blocks into separate per-block partial attention kernels, then combine their
softmax-normalized outputs with log-sum-exp. This follows the author's
split-K reduction principle while avoiding the compiler's mixed-control-flow
path. It still needs NPU numerical/graph checks, real cache lifecycle and a
matched dense service screen before any E2E or quality claim.
