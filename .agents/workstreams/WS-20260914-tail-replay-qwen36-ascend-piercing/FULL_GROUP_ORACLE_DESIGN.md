# Tail-Replay full GDN-group oracle design

Updated: 2026-09-14

## Why the recurrence-only result is insufficient

The first NPU oracle replayed suffixes after causal convolution and reused
dense per-layer projected inputs. It validated the recurrent ABI and showed
large zero-tail state error, but it did not implement the paper's GDN-group
replay. Qwen3.6 carries hidden_states and residual separately, and each
GDN layer also owns a short causal-convolution state. Those semantics must be
included before a quality or rejection decision.

## Exact live boundary

The pinned Qwen3.6 execution uses 64 decoder layers with groups
[0,1,2], [4,5,6], ..., [60,61,62] separated by full-attention layers.
The oracle clones the exact hidden_states and residual pair entering each
group. For the first group, residual is absent and the embedding output is
the boundary. For later groups, the pair is the exact live result after the
preceding full-attention layer and its MLP.

## Functional replay

For each of the three layers the oracle executes, in order:

1. fused residual RMS normalization;
2. the live QKVZ and BA projections;
3. the Ascend causal-convolution custom operator with an isolated zero cache;
4. the live Q/K/V rearrangement and fused GDN gating;
5. the Ascend chunk gated-delta-rule path with an isolated zero state;
6. output gating, projection, residual normalization and MLP.

The exact harness replays the full boundary sequence. Candidates replay only
the final 5% or 10% from zero convolution and recurrent state. The oracle
never swaps its outputs into the serving request.

## Evidence and gate

For every group and TP rank, the oracle records:

- materialized boundary output (hidden_states + residual);
- final convolution state for each layer;
- final recurrent state for each layer;
- runtime source identities and cache shapes.

The full-sequence exact replay must remain finite and stay within relative
L2 0.01 for all outputs and states. A failure is a harness failure, not an
algorithm result. Only after exact controls pass may the 5%/10% metrics be
interpreted.

## Explicit limitation

This stage does not install reconstructed caches and therefore cannot compare
first-token logits, quality, TTFT or throughput. If its candidate state errors
are plausible, the next stage will snapshot the exact full-attention KV cache,
substitute reconstructed GDN convolution/recurrent caches in an isolated
first-token decode, and compare logits before any performance integration.
