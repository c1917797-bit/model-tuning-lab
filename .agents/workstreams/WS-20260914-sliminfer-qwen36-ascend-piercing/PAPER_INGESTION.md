# SlimInfer paper ingestion

## Identity and claim

- Paper: *SlimInfer: Accelerating Long-Context LLM Inference via Dynamic Token
  Pruning*, arXiv:2508.06447v2, AAAI 2026.
- Public implementation: `https://github.com/Longxmas/SlimInfer`.
- The public repository exposed one commit at review time, but the exact commit
  could not yet be resolved from the target host because the outbound Git
  operation did not complete. No root `LICENSE` file was visible in the public
  tree, so its code must not be copied or vendored into this repository.
- Paper numbers are contextual evidence only. The reported maximum is 2.53x
  TTFT and 1.88x end-to-end latency for Llama-3.1-8B on one RTX 4090; the
  efficiency E2E case generates only 16 tokens.

## Method chain

1. Partition prompt tokens into 64-token blocks.
2. Build eight-token semantic key units by mean pooling keys.
3. Score active prompt blocks with a four-query recent window and the maximum
   semantic-unit score per block.
4. At configured later layers, keep a fixed number of top-ranked prompt tokens
   (paper/source presets use staged 12K/6K/4K for Qwen2.5 and 8K/4K/2K for
   Llama).
5. Cache hidden states for removed blocks so later decode-time activation can
   restore them.
6. Keep generated response tokens.
7. Maintain layer-specific active prompt KV; predictor-free reuse of the next
   layer's active set avoids a swap when overlap is high.
8. Otherwise move inactive prompt KV to CPU and prefetch required blocks;
   asynchronous overlap is a second mechanism, not part of the pruning-only
   attribution.

The official implementation supports batch size one in its custom decode path
and replaces Hugging Face Qwen2/Llama model loops. It is not a vLLM, paged-cache,
tensor-parallel, continuous-batching, or Ascend implementation.

## Portable idea versus paper-specific assumptions

Portable:

- blockwise prompt importance from pooled keys and recent queries;
- layer-wise active token sets;
- hidden-state restoration and stable absolute token identity;
- overlap-aware cache movement.

Non-transferable without implementation:

- CUDA events/streams and FlashAttention2;
- Hugging Face batch-one cache objects;
- pure full-attention model loop;
- contiguous per-sequence tensors rather than vLLM flattened batches and paged
  cache slots.

## First hypothesis

H1: a rank-consistent, per-request SlimInfer planner and layer-specific token
stream can reduce Qwen3.6-27B prefill work enough to improve the frozen 32K
HYPIC ruler after accounting for gather/scatter, metadata, GDN-state, and cache
movement overhead.

This is admitted only as a bounded architecture/serving feasibility hypothesis.
The no-offload pruning core must be isolated before asynchronous NPU/CPU cache
movement is added.

## Falsifiers

- the hybrid GDN/full-attention cache contract cannot represent layer-specific
  token counts without an unsafe scheduler rewrite;
- perfect removal of the affected full-attention/MLP work cannot produce a
  meaningful end-to-end gain;
- selection/restoration cannot be deterministic and identical across TP4 ranks;
- NPU numerical or multi-step state checks fail;
- the fixed-output performance screen shows no useful gain after overhead;
- LongBench-v2 or GSM8K crosses its measured baseline rejection boundary.
