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
