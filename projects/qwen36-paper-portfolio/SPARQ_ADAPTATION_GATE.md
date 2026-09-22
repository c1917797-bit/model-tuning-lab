# SparQ Attention: Ascend applicability gate

Start: 2026-09-22 22:22 UTC. Deadline for this paper: 2026-09-23 22:22 UTC.
This is a planned experiment, not an NPU result.

## Why this paper

- Official paper: https://arxiv.org/abs/2312.04985v6
- Author code: https://github.com/graphcore-research/sparq-gpt-fast/tree/with-sparq
- Its decode path selects the largest-magnitude query coordinates, scores cached
  keys on those coordinates, selects top-K KV positions, performs full-score
  attention on the selected support, and optionally interpolates with a running
  value mean. The official source supports a single-cache mode; it documents a
  replay limitation in its running-mean implementation. We must not copy that
  lifecycle bug into vLLM continuous batching.
- It requires no model retraining. Its GQA reduction recipe is author-described,
  but Qwen3.6-27B and Ascend are not paper-evaluated models/platforms.
- The public `sparq.py` uses `repeat_interleave` to expand grouped K/V heads
  before its generic top-r/top-k routine. The paper's dedicated GQA recipe
  instead aggregates query magnitudes and approximate scores within each KV
  group; use the paper recipe as the GQA oracle and the code as the generic
  selection oracle. Do not repeat the full KV cache in the Ascend adapter.

## Measured target, not a promised speedup

The frozen dense TP4 profile at input 32768 / prefix 16384 / output 1024 /
concurrency 16 shows decode attention 27.40025% and BF16 MatMulV2 50.29700%
of aggregated NPU operator time. The attention figure is a diagnostic operator
sum, not a critical-path share. Decode attention is the target; the matmul
hotspot is a separate paper branch and must not be credited to SparQ.

The rank-0 decode trace calls `FusedInferAttentionScore` 480 times across
30 decode steps, with BF16 query shape `[16,6,256]`, KV-cache shape
`[5484,128,256]`, and a paged block table. Main MatMulV2 shapes have leading
dimension 16, so single-token narrow-MatMul papers do not fit this workload.

## Source reuse and gap

Pinned vLLM-Ascend v0.23.0 `attention_v1.py` reaches the native
`npu_fused_infer_attention_score` through `DeviceOperator`, with a paged KV
table. Its opt-in Hamming sparse path already replaces the decode block table
and sequence lengths. This is a potential integration seam, **not** SparQ
algorithm evidence: Hamming selection and SparQ top-r/top-K are different.

The pinned `npu_sparse_flash_attention` path is MLA-specific; the inspected
CANN operator documentation requires one KV head and D=512/Dr=64. It cannot
be assumed compatible with this GQA D=256 path. `BlitzSparseAttention` is a
separate experimental operator with per-head `sabi` block indices and BF16
GQA support, but its documented interface accepts dense K/V tensors, not a
paged-KV block table. A read-only search of the CANN 9.1 operator tree in the
existing v0.23 container found no installed BlitzSparseAttention artifact.
The source implementation may be reusable after plugin-owned packaging;
installed availability, paged-KV adaptation and graph compatibility remain
unproven. Reuse an existing native primitive only after its exact ABI is
verified.

The model file is actually `/cache/efim/Qwen3.6-27B/config.json`
(SHA256 `69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c`),
not the originally guessed `/cache/austinov/Qwen3.6-27B` path. It declares
`Qwen3_5ForConditionalGeneration` despite the serving directory's Qwen3.6
name, 24 Q heads, 4 KV heads, D=256, and 16 full-attention layers among 64.
The measured TP4 trace has six local Q heads, so this configuration has one
local KV head per worker. This removes the per-head block-table-union issue
for **this TP4 configuration only**; it does not establish portability to
other TP degrees or model shapes. Verify the deployed module and exact model
identity again before loading.

The frozen v0.23 Hamming route is a separate possible integration seam:
`get_kvcomp_decode_params` substitutes a request-level block table and
effective sequence lengths before `FusedInferAttentionScore`. SparQ's GQA
recipe instead sums query magnitudes and approximate scores within each KV
head group before choosing per-KV-head support. With one local KV head on the
current TP4 workers, one request-level table can represent that support.
For environments with more than one local KV head, a table union may erase
sparsity; gate those environments separately. Quantify selector cost and
page-level support quality before building a service adapter.

## First adaptation and falsification order

1. Pin the author code commit/source hash and reproduce its top-r/top-K output
   on identical toy inputs. The author implementation is the mechanism oracle.
2. Audit GQA head grouping, live cache page size, per-layer slot lifecycle,
   graph/static-shape rules and memory overhead. Do not duplicate the full KV
   cache merely to imitate the CUDA-friendly `store_twice` mode.
3. Build one independent, explicit-opt-in selected-page variant. If page
   selection changes support from the paper's token-level top-K, label it an
   Ascend adaptation and compare its selected support/quality separately.
4. Run NPU4 batch-1/16 eager and graph correctness, then TP4 dispatch on
   physical NPU4-7. A passing tensor gate is not a performance result.
5. Run one profiler-off service screen against the frozen same-stack dense
   control. Continue to three paired runs and final accuracy only if it is
   plausibly on track for +10%; otherwise record implementation no-go and
   immediately advance to the next paper.

The next attention candidate is Self-Indexing Attention
(https://arxiv.org/abs/2609.13205), which reports Qwen3.6 hybrid-model
results and is training-free, but no author repository was located during
this initial audit. It must not be called an official-code port without one.
