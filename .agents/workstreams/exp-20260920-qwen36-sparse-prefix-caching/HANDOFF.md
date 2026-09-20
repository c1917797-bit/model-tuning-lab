# Sparse Prefix Caching — Qwen3.6/Ascend piercing

## Status

- Stage: re-entered (atomic native-KV/GDN plugin adapter implemented; NPU
  validation pending).
- Start: 2026-09-20.
- Hard timebox: 24 hours from this workstream start.
- Queue position: 6, after completed MXR, DeltaLog, approximate inversion,
  KVBuffer, and HYPIC investigations.
- Resource lane: physical NPU4-7 only; container-visible device mapping must be
  re-proved immediately before every NPU launch.

## Paper fidelity

- Paper: arXiv:2605.05219, Sparse Prefix Caching for Hybrid and Recurrent LLM
  Serving.
- Official source:
  arabel1a/sparse-prefix-caching@d3050d44ed9d878c396cf3fcf632d63743ffed5b.
- Exact mechanism: store full attention KV plus sparse exact recurrent/conv
  checkpoints; restore the deepest checkpoint not beyond the token match and
  recompute the remaining suffix. Distribution-aware placement uses the
  paper's O(NM) dynamic program over the observed overlap histogram.
- Official implementation is a Hugging Face prototype for a single
  Qwen3.5-0.8B layer group. It is not a vLLM serving integration and its dry
  simulation or CUDA timing is not Ascend performance evidence.

## Applicability evidence

- /cache/efim/Qwen3.6-27B/config.json SHA256:
  69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c.
- The checkpoint has 64 layers with a repeating three linear-attention / one
  full-attention pattern, FP32 recurrent state, and cache enabled.
- Frozen vLLM-Ascend source is v0.23.0 commit
  5cb98caaadeff42b5b62b996e34bb2aaa29d20fd.
- Source inspection found hybrid cache coordination, mamba_cache_mode=align,
  recurrent/conv state indices, and explicit GDN initial/final state handling.
  This is a plausible integration seam, not yet proof that arbitrary sparse
  checkpoint extraction/restoration is correct in the production service.

## Predeclared gates

1. Prove the real v0.23 Qwen3.6 path can extract and restore both GDN recurrent
   state and convolution state at an aligned checkpoint without modifying
   upstream vLLM/vLLM-Ascend.
2. Implement only in this workstream as an independently named, explicit
   opt-in monkeypatch/plugin.
3. On NPU4-7, require greedy replay to match the no-restore reference for
   emitted token IDs and final cache tensors under repeated hit/miss,
   partial-overlap, slot-reuse, and graph/eager cases relevant to the service.
4. Only after correctness, compare the distribution-aware policy against the
   strongest fixed checkpoint policy under the same cache-state byte budget,
   request stream, model, image, TP4 topology, and general runtime options.
5. Performance ruler: 40 requests, concurrency 16, fixed 1024-token output,
   three measured repetitions per arm after explicit warmup. Report output
   throughput, TTFT, TPOT, duration, HBM, cache hit depth and restored/replayed
   tokens.
6. Paper acceptance requires at least 10% end-to-end output-throughput gain
   over the strongest same-budget control with correctness passed. A no-cache
   comparison may be reported but cannot replace the same-budget control.
7. If performance passes, final LongBench-v2 and GSM8K use thinking off,
   temperature 0, seed 0, max_tokens 2048 and normal EOS. The final algorithm
   is not accepted if either paired task accuracy decreases.

## Early stop conditions

- No safe production state extraction/restoration seam is found.
- State/KV restoration is not numerically correct on the real NPU path.
- The candidate cannot beat the strongest same-budget fixed strategy after
  one evidence-backed implementation loop.
- The workload has no meaningful partial-prefix overlap, making checkpoint
  placement irrelevant.
- The 24-hour workstream budget expires. Preserve evidence, decide no-go or
  inconclusive, recover active failed code, and advance to queue position 7.

## Immediate next action

Run a container import/bootstrap canary on NPU4-7 with HYPIC and this plugin,
then run the smallest cold-producer / hot-consumer exact-prefix case. Require
evidence that native full-attention KV and the ready HYPIC GDN checkpoint expose
the same computed-token boundary. Do not start a serving performance comparison
until greedy token equality, repeated replay, and plugin hot-path activation are
all proven.

## Attempted implementation

- Added projects/sparse-prefix-ascend as a separate vLLM general plugin.
- Reimplemented the paper's distribution-aware O(NM) placement recurrence and
  a same-count balanced control.
- The runtime adapter requires HYPIC explicitly and replaces only HYPIC's
  aligned exact-prefix candidate positions; state/KV extraction, storage,
  restore, replay, and kernels remain identical between arms.
- The adapter validates schema, absolute plan path, checkpoint count, range,
  uniqueness and runtime block-size identity, and fails closed on drift.
- Five focused unit tests pass, including fail-closed plan validation and a
  fake-HYPIC monkeypatch test. These are implementation checks, not NPU or
  performance evidence.
- Source audit found that native v0.23 align mode retains only the final
  recurrent state for a request. It does not natively implement the paper's
  multiple sparse checkpoints. HYPIC's validated material store is therefore
  the selected production seam.

## Runtime re-entry

- The earlier thin-adapter no-go remains valid: changing only checkpoint
  candidates cannot cross HYPIC's native-cache guard.
- New bounded hypothesis: keep full-attention KV under the native vLLM cache,
  keep GDN/conv checkpoints under HYPIC's transactional material store, and
  expose a hit only when both owners agree on the exact checkpoint boundary.
- The plugin now predicts a ready recurrent hit without pre-advancing the
  request, hides native KV for cold/uncommitted prefixes, bounds
  Request.block_hashes to the ready checkpoint during the native lookup, and
  lets the existing HYPIC wrapper validate and attach the worker restore plan.
- The adapter is gated to the reviewed HYPIC v0.8.5 scheduler SHA256 and fails
  startup on drift. No HYPIC, vLLM, vLLM-Ascend or CANN source is modified.
- Ten focused software tests pass. They are not NPU correctness evidence.
- For the frozen 26-request overlap histogram, distribution-aware checkpoints
  3072/7680 reduce replay by 27,648 tokens versus the same-budget balanced
  3072/6144 control (58.7% less replay work), so an end-to-end opportunity still
  exists.
