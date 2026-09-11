# Qwen3.5 v0.23 runtime lessons

Read this reference when maintaining Qwen3.x BF16 serving work that uses the
official vLLM-Ascend v0.23 runtime family. The evidence was distilled from the
`work/qwen35-performance-delivery` T20-T24 records on 2026-09-11. It is a
closed-route and decision guide, not a live resource snapshot or a claim that
the final Qwen3.5 performance objective has passed.

## What worked

- A read-only, removable Python monkeypatch in the unchanged official image
  can be proven active in every TP worker without rebuilding the image or
  overlaying framework source.
- The bounded-prefill treatment completed 32/32 requests with zero errors and
  natural EOS. Against its fresh identity-matched control, c1 TTFT P95 fell
  from 6310.576 ms to 808.224 ms, an 87.193% reduction. Retain this only as a
  TTFT component: TPOT improved just 2.835%, below the 20% gate.
- A separate stabilization pass exposed unseen-shape compilation and prevented
  warmup latency from being reported as steady performance. Use a distinct
  cache identity for the measured pass.
- The no-prefetch ablation also completed 32/32 with zero errors and natural
  EOS. Its differences from the prefetch-on run were only +1.77% TTFT and
  +0.087% TPOT. Removing both prefetch hooks is therefore a successful
  simplification, not a failed optimization.
- Existing immutable evidence from the same image, dtype, real weights, TP
  degree, and exact shapes can close a candidate without consuming another NPU
  lease. Revalidate all identity fields before reusing it.

## What failed and why

- The upstream experimental `SwigluGatedMlp` package matched the installed
  CANN tag and built unchanged, but its shared library had an unresolved
  internal matmul symbol. Stop before device execution. Do not hide an
  upstream ABI defect with copied local matmul code or an unrelated runtime
  library.
- Upstream presence is not a quality certificate. Inspect commit history,
  tests, support matrices, PR review, release ancestry, and removal reasons.
  Unknown non-promotion rationale is a risk signal; it does not authorize a
  parallel reimplementation.
- Later upstream source is reference material until its code is deliberately
  adapted and validated. Inspecting a v0.24 commit does not mean the official
  v0.23 runtime or image was upgraded.
- Weight prefetch was later removed upstream as underused/low-value, and its
  target-stack ablation showed no material value. Do not revive it unchanged.
  A deleted or deprecated graph/operator path remains closed unless a new
  supported implementation changes the premise.
- A later upstream GDN-gating route was rejected by opportunity math before
  device testing. The measured operator accounted for at most about 3.67% of
  the required c1 TPOT gap even under an impossible zero-cost assumption.
  Reject candidates whose complete recoverable critical-path budget cannot
  meet the declared gate.
- The installed Python schema and prose for `torch_npu.npu_ffn` appeared to
  allow BF16 SwiGLU, but the executable `aclnnFFNV2` kernel rejected the
  no-expert-token BF16 path for M=1/5/8/16. Runtime execution evidence
  outranks wrapper signatures and documentation. Do not cast to FP16 when BF16
  fidelity is part of the contract.
- A local FFN or GEMM win is not a TP service win. If a candidate breaks the
  existing Matmul-AllReduce boundary, benchmark the complete replacement
  chain, including the standalone collective, against the fused control.
- The existing decode SwiGLU median was about 4.39 us per layer, below the
  installed guidance's roughly 30-us vector threshold. Do not optimize a small
  named operator merely because a replacement exists.

## Trust and quality gates

- Performance and model quality are independent mandatory gates. A latency win
  never offsets an accuracy regression.
- A workload with empty reference answers can prove latency, completion,
  natural EOS, and paired-output stability, but cannot prove accuracy.
- Byte-identical paired outputs pass directly. Every non-identical pair needs
  a row-level, hash-bound decision; a summary-only approval is insufficient.
- Run the expensive reference-backed accuracy suite only after fail-fast
  performance passes. Require fresh identity-matched control/candidate runs,
  complete repetitions, zero request failures, and candidate accuracy no lower
  than control in every repetition and in the median.
- Exact response hashes may drift even without a treatment. Do not confuse
  nondeterminism with either correctness or regression; use paired semantic
  evidence and reference-backed scoring.

## Reusable admission sequence

1. Pin model bytes, official image digest, framework/CANN versions, dtype, TP
   degree, workload hash, cache state, and physical device mapping.
2. Audit the accepted, unmerged, experimental, deprecated, and removed
   upstream routes before writing code.
3. Compute a non-overlapping critical-path upper bound. Close routes that
   cannot satisfy the end-to-end gate even at zero cost.
4. Reuse the exact upstream or built-in implementation. Add only the smallest
   removable runtime adapter needed to reach the real call path.
5. Gate ABI/loadability, exact-shape numerical behavior, repeated stress,
   whole-chain communication cost, and per-worker activation before service
   benchmarking.
6. Run smoke and the preregistered fail-fast cells. Expand to the repeated
   matrix and expensive quality gate only after both TTFT and TPOT pass.
7. Record `accepted`, `partial-component`, `rejected`, `failed`, or
   `inconclusive`, with the premise that would permit reopening. Remove
   rejected hooks from the safe runtime while preserving their evidence.

Do not rerun a closed candidate unchanged. A retry needs a concrete changed
premise such as a new supported kernel release, repaired ABI, different
critical-path budget, or corrected evidence identity.
