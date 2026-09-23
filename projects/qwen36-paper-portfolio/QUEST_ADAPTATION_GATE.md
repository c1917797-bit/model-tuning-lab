# Quest page selection: Qwen3.6 Ascend adaptation gate

Formal start: 2026-09-23 00:20 UTC. Paper deadline: 2026-09-24 00:20 UTC.
This is a pre-registered workstream, not a new performance or accuracy result.

## Mechanism and source boundary

- Paper: https://arxiv.org/abs/2406.10774v2
- Author repository: https://github.com/mit-han-lab/Quest at
  `01c1623bf9395009520874e989e29f683203b357` (GitHub commit view).
- Quest stores element-wise min/max Key per KV page. For a query coordinate,
  choose the larger of `q_j * min_j` and `q_j * max_j`, then sum across the
  head dimension as a page criticality upper-bound estimate. Select the
  highest-scoring pages, retaining the current partial page, and run exact
  attention over the selected pages.
- The released author implementation uses a CUDA/FlashInfer cache manager,
  asserts batch size one in `QuestAttention.py`, and lists GQA as TODO. We are
  adapting the algorithm, not claiming a drop-in official Ascend port.

## Why this is the next bounded test

The frozen Qwen3.6 TP4 decode profile attributes 27.40025% of aggregated
NPU operator time to attention. This is not critical-path time, but merits
a service screen if the selector is cheap and NPU numerically valid.
The installed v0.23 native FIA has a paged block-table interface. A prior
selected-page ABI probe passed batch 1/16 eager and graph on physical NPU4.
The preceding SparQ page adapter scanned full K each decode and had a
1.87–2.40 ms warm selector diagnostic cost per layer/rank; Quest's page
summary is intended to avoid this full-K scan. It still requires maintaining
min/max summaries under vLLM page allocation, reuse, prefix sharing and
graph replay; one-shot recomputation does not prove deployability.

The deployed model has 16 full-attention layers, 24 Q heads, 4 KV heads and
head dimension 256. TP4 places six Q heads and one KV head on each worker.
The author's per-query-head page lists therefore cannot directly become one
native per-request table. The first adaptation uses the *maximum* estimated
criticality across the six local Q heads to propose a shared page set.
Compare that set against each head's native Quest ranking and dense output;
this GQA union substitute is a distinct implementation variant.

## Stop/go sequence

1. Pin source, live model/runtime geometry and physical4–7 availability.
2. One non-mutating real-model decode diagnostic: construct exact page min/max
   from live Key cache once, score pages for all six query heads, propose
   25%/50% page budgets and compare native selected-page FIA with dense.
   Report per-head selected mass, output error and selector time separately
   from one-time summary construction. A tensor mismatch is not the user's
   final 1% task-accuracy bound.
3. If quality is plausible, implement plugin-owned incremental page-summary
   storage with explicit slot/page lifecycle and version capability gates.
   Prefer reusable Ascend/native ops; generate a custom operator only for a
   measured algorithm-specific gap. No modifications to upstream repositories.
4. Require physical NPU4 batch1/16 eager/NPUGraph numerical and lifecycle
   checks, then TP4 worker dispatch. Only then run a profiler-off fixed-1024
   dense/candidate E2E screen. Three paired runs and final LongBench-v2/GSM8K
   follow only for a plausible >=10% candidate.
5. Record a scoped no-go and advance within 24 hours when an abort condition
   is met; do not repeat deterministic failures without a new code hypothesis.

Current precision allowance is at most 1% loss on each final matched E2E
task, not on intermediate tensors. Report both percentage-point and relative
loss; do not declare accepted if the interpretation remains ambiguous.

The official repository was inspected through GitHub primary-source pages;
the host's direct `git ls-remote` timed out. Do not claim it was cloned or
that its CUDA kernels were run on Ascend.

## Real TP4 diagnostic and scoped decision (2026-09-23)

The first service was stopped before any request after a cache-shape review:
native paged Key is `[pages, 128, 1, 256]`, so the one-shot diagnostic must
flatten the singleton KV-head dimension before page min/max. The corrected
same-image shape test passed, and a fresh v2 service ran on physical NPU4–7.
The corrected opt-in probe returned the original dense output unchanged.
One 20,718-input/4-output request produced one `real_decode_sample` on each
TP rank, at layer 3, 20,719 live KV tokens and 162 native 128-token pages.
The service was stopped and all four cards returned to the idle HBM baseline.

Evidence: `/cache/cch/quest-real-qwen36-v2/audit.jsonl`, SHA256
`94f458927736b562a751d77b3346b7542b02a3a43025b6c50e38c9a3564fbaa6`.
The 25% shared-page proposal retained as little as 42.876% exact attention
probability mass on a local Q head; at 50%, the minimum was 62.520%.
Across ranks, maximum absolute attention-output difference from dense was
0.102–0.363 at 25% and 0.050–0.194 at 50%. The first-call page score took
31.8–34.5 ms per rank versus 0.46–0.71 ms for a selected-page native FIA;
that score timing includes initial operator/dispatch overhead and is **not**
a steady-state or E2E estimate. The one-time full-cache summary build took
42.3–44.7 ms and must not be charged to every decode in a real integration.

Decision: reject this direct six-Q-head shared-max Quest page adapter for the
current fixed workload. Its pre-registered useful-budget support gate fails,
so do not invest in summary-lifecycle integration or claim a Quest throughput
or task-accuracy result. This is not a proof that all Quest implementations,
per-head native kernels, or other workloads fail. Reopen only with a new
mechanism that solves the GQA page-set conflict *and* a credible low-overhead
selector; do not simply increase the page budget without an E2E opportunity
argument. Move to a distinct measured hotspot.
