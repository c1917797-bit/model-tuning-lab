# Sparse Prefix Caching — Qwen3.6/Ascend piercing

## Status

- Stage: planned.
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

Audit the v0.23 hybrid cache manager and GDN state lifecycle end to end, map the
official checkpoint store to production cache groups, then write the smallest
NPU extraction/restore canary. Do not run the official CPU/dry simulator as a
substitute for this gate.
