# Qwen3.5-27B Sparse Prefix Caching reproduction

## Objective and status
Reproduce Sparse Prefix Caching for Hybrid and Recurrent LLM Serving
(arXiv:2605.05219), then measure performance and quality on the actual
Qwen3.5-27B checkpoint on Ascend 910B4. Status: planned, not baselined.
No model execution, accuracy result, or performance improvement is claimed.

## Scope and ownership
- Parent business task: Qwen3.5 performance; this is a bounded paper reproduction,
  not another permanent business stream. Archive this worktree after integration.
- User now authorizes physical NPU4-7 when no actual compute process uses them.
  A running/exited container device declaration alone does not block use.
- Do not stop or modify external containers. Recheck actual processes before
  allocation, coordinate cooperative leases, check ports and MemAvailable >=48 GiB.
- No NPU lease currently held; no controller or experiment container exists.
- Preserve BF16, original weights, no retraining/quantization/MTP/speculation.
- Preserve original host/image vLLM-Ascend; use removable runtime injection into
  disposable containers with read-only code mounts. No source overlay or commit.
- Existing performance worktree is dirty and ahead of upstream; do not stage,
  overwrite, reset or absorb those changes.

## Frozen known identity (2026-09-11)
- Starting repository: 31c43a4c249c9d4c597372f47d989a7c10b2c9c4.
- Local official image ID:
  sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
- Repository digest:
  quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a
- Model path, model/tokenizer hashes, source import paths, CANN versions,
  CPU binding and service port: not yet frozen. Never substitute Qwen3.6/3.8.

## Source intake and reproduction risks
- Paper: https://arxiv.org/abs/2605.05219
- Experimental repository: https://github.com/arabel1a/sparse-prefix-caching
- Repository revision and code license: must be pinned/verified before reuse or
  redistribution. No author source has been vendored here.
- Observed public strategies.py uses O(M*N^2) enumeration, whereas the paper
  describes an O(M*N) solver. Reproduce original first; evaluate solver changes
  separately. Include planning cost when paid online.
- checkpoint_cache.py correctness helper calls checkpoint_positions with tag
  instead of required type. Full-hit path returns dummy hidden output; it is not
  a first-token correctness oracle. Validate logits and generated sequences.
- Author timing separates checkpoint capture into untimed runs. Our deployment
  measurements must include capture, restore, copies, replay and eviction.
- Prior independent JS recurrence screen: 700 tiny cases matched brute force,
  maximum difference 8.881784197001252e-16. This is NOT execution of author Python,
  full algorithm verification, Qwen accuracy or NPU evidence; rerun durably.
- Main checkout under /cache/cch/vllm-ascend has Mamba hit/alignment code, but is
  not proven identical to the official image. Inspect pinned image before edits.

## Planned comparisons
1. Author algorithm reproduction: original DP vs exhaustive tiny-case oracle;
   zero budget/histogram, concentrated/tied distribution, block alignment,
   update/replan and memory budget cases. Pin sources and hash inputs/results.
2. Workload opportunity: tokenize actual query_rewrite with exact chat template;
   estimate checkpoint benefit using past-only observations, no future leakage.
3. Baseline arms: no reuse (context only), native cache, fixed shared-prefix
   checkpoint, uniform checkpoints. Treatment: distribution-aware checkpoints.
   Equal memory budgets and identical arrival order; distinguish cold/warm cache.
4. Validate entire model state: Attention KV, GDN recurrent state, convolution
   history and positional/cache metadata. Cover full/partial/no hit, repeated
   restore, branch divergence, one-token suffix and eviction. Check immutable
   checkpoint ownership; device .to() may alias, so prevent in-place corruption.
5. Real-weight smoke, paired 32-sample canary, then c1/c16 screen and
   c1/c5/c8/c16 three repetitions with per-request TTFT/TPOT, P50/P95/P99,
   throughput, memory and failures; paired all-357 query_rewrite natural-EOS
   quality gate. Ground-truth-free equality is not general task accuracy.
6. Baseline-repeat variability, exact tokens/logits where meaningful and
   adjudicated differences determine the quality claim. Report improvements,
   regressions and inconclusive results alike. No invented performance numbers.
7. Legacy delivery target (TTFT -40%, TPOT -20% each concurrency) remains a
   separate acceptance question; this prefill algorithm is not presumed to
   accelerate decode. Reproduction completion does not require hiding a null result.

## Next action
Push this planning checkpoint, pin author source without redistribution,
inspect the immutable image's actual runtime APIs and model path, and run the
CPU reproduction tests. Acquire/recheck NPU4-7 only when ready for real smoke.
Read .agents/skills/paper-to-ascend-reproduction and its evidence contract.
All long commands use one tracked operation handle; poll rather than duplicate.
Git fetch timed out once, then succeeded on bounded retry. AWMCP was healthy.

## Evidence and release
Raw model/data/log outputs belong outside Git under a unique /cache/austinov
artifact root (not yet allocated). Record SHA256 and exact commands per stage.
No experiment resources have been allocated, so there is nothing to stop.
