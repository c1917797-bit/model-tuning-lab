# SparQ Attention: Ascend applicability gate

Start: 2026-09-22 22:22 UTC. Deadline for this paper: 2026-09-23 22:22 UTC.
This workstream has native ABI and one real-model diagnostic result, but no
end-to-end throughput or task-accuracy result. It is not accepted.

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

First native ABI probe (v1) reached physical NPU4 through a non-privileged
container mapping, but CANN 9.1 rejected the call before calculation:
`attnMask` was absent while `sparseMode=3`. The exact error requires
`sparseMode=0` when no mask is provided. This is a probe-call failure, not a
SparQ numerical or performance result. The immutable result is
`/cache/cch/sparq-page-abi-20260923-v1/result.json` (SHA256
`e4ab461749d581aae36cd80f8ad420938ad8a5f2930156b809d532e7ba76cb8e`).
The next run changes only that parameter and writes a new v2 directory.

The v2 probe passed on physical NPU4 with native FIA for batch 1 and 16,
two changed page tables, eager and NPUGraph replay. The maximum absolute
error against full-precision attention over exactly the selected support was
0.001910031; repeated identical graph replay was bitwise stable. Result:
`/cache/cch/sparq-page-abi-20260923-v2/result.json` (SHA256
`12920016294cdecd888037c50921e5c10ebdf18f573f7dec0a8fa4f1fd6f0203`).
This does **not** validate SparQ's top-r/top-k selector, task accuracy, TP4
service dispatch, or throughput. Those remain the next gates.

The separate synthetic GQA selector probe initially failed NPUGraph capture:
constructing a fresh NPU tensor from a host constant caused a synchronous
host-to-device copy in GLOBAL capture mode. A device-derived latest-page index
fixed that failure without changing the selection rule. The v2 probe passed
batch 1/16 with changed Q, eager and replay, max absolute error 0.001363218
against exact attention on the chosen support. Its batch-16 page adapter
covered only about 53.3% of the paper top-128 tokens with three of five pages
on **random synthetic** Q/K; this is an accuracy-risk signal, not a real-model
quality estimate. The result is
`/cache/cch/sparq-selector-npu-20260923-v2/result.json` (SHA256
`b1dd5fac5331591d03d0be07dd4bc51956a9b12ffad086ac5a82389b28581e62`).
No service patch, TP4 dispatch, E2E throughput or task accuracy claim follows.

The next attention candidate is Self-Indexing Attention
(https://arxiv.org/abs/2609.13205), which reports Qwen3.6 hybrid-model
results and is training-free, but no author repository was located during
this initial audit. It must not be called an official-code port without one.

## Real-model diagnostic, 2026-09-23

An explicit opt-in, non-mutating plugin observed the real Qwen3.6 TP4 decode
path on physical NPU4–7. Its source is in
`projects/qwen36-paper-portfolio/plugin/qwen36_sparq_probe/`. The successful
v5 audit is `/cache/cch/sparq-real-qwen36-v5/audit.jsonl` (SHA256
`e66a1f3a90b976ac40c3cf759d9e6b551658b28377968b2d1bf20d1a7d950b05`).
Each worker reached `language_model.model.layers.3.self_attn.attn` at one
9002-token decode position; the live native page size was 128, with 71 pages.
The request used `ignore_eos` only to force this diagnostic decode. The plugin
returned the original dense output and did not run an accuracy or performance
candidate. Services v1–v5 were stopped, not deleted; v5 was stopped cleanly.

At 25% page budget, the four TP ranks retained 94.53–100% of the paper's
top-128 token positions, but sparse-vs-dense layer-output maximum absolute
error was 0.10156–0.96875. At 50%, top-128 page recall was 100% on all ranks,
yet maximum absolute error remained 0.05469–0.41406. These are diagnostic
intermediate errors, **not** the user's 1% end-to-end task-accuracy threshold.
The second, warm selector path took 1.79–2.19 ms per rank, whereas its native
sparse FIA call took 0.48–0.61 ms. The cold first selector took 68–82 ms.
Selector timing includes full-K cache gathering, PyTorch operations and host
synchronization; it is not a production timing estimate. Top-K recall alone
does not preserve the dense output because omitted attention mass still
contributes. A direct Python page selector is not a credible +10% end-to-end
candidate without an algorithm-specific selector and omitted-value correction.

The startup failures were preserved: v1 hit a v0.23 general-plugin import
cycle and v2 replaced the image's CANN `PYTHONPATH`, hiding `acl`; v3 had no
decode in the first EOS-terminated request; v4 exposed that `layerIndex` is
only populated for the optional Hamming path and is zero here. The fixed
probe captures `layer.layer_name`. An API startup log's 1536 attention block
size is hybrid-cache planning, not this native FIA cache tensor's 128-page
layout. None of these failures is a paper numerical result.

The inspected `CANN/ops-transformer` BlitzSparseAttention documentation
accepts dense K/V plus block-index metadata, not vLLM's live paged-KV table;
it is therefore not a drop-in replacement. Source reuse may still be possible
if an adapter avoids full-KV repacking. This source audit does not establish
that an operator has been generated or deployed.

The v6 follow-up tested the paper's omitted-mass correction on a *different*
20719-token real-model prompt, with 162 native pages. The one-shot probe read
the entire historical V to construct an exact mean for diagnosis; it did not
implement a production running mean. At 25% page budget, uncorrected max
absolute error across TP ranks ranged 0.107–0.313 and corrected error
0.107–0.235. At 50%, the ranges were 0.051–0.152 and 0.051–0.130. Some
individual ranks worsened slightly. Warm selector wall time was 1.87–2.40 ms,
native sparse FIA 0.48–0.64 ms. The output is
`/cache/cch/sparq-real-qwen36-v6/audit.jsonl` (SHA256
`5e9e4841d62ec45e1b45c5f46a9e9cc25585303dc176466ab68b06388ec1b863`).
The v6 service was stopped cleanly and NPU4–7 returned to their idle HBM
baseline with no running processes.

**Scoped decision:** reject the direct Python selected-page adapter under the
pre-registered selector-cost/quality gate. Do not label the original
token-level SparQ paper ineffective, and do not label these one-layer tensor
errors as a LongBench-v2/GSM8K failure. A credible revival would need a
fused selector over the paged key cache, selected-token (not merely selected-
page) sparse attention, and a request/layer-safe running-V mean. None has
passed current NPU or service gates. No SparQ E2E performance or final task
accuracy result exists. The next paper-level loop will prioritize Quest,
whose algorithm is page-native and has official code, ahead of Self-Indexing
Attention's token-level 1-bit pipeline.
