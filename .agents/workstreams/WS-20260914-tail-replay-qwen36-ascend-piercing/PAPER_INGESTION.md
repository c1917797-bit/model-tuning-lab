# Tail-Replay paper ingestion

## Identity and evidence boundary

- Paper: Tail-Replay: Escaping the Curse of Linear Attention in Prefix
  Caching for Hybrid LLMs, arXiv:2608.30310v1, 2026-08-31.
- License shown by arXiv: CC BY 4.0.
- A public implementation was not found in the paper or targeted web search on
  2026-09-14. This workstream therefore implements only what the paper defines
  and labels local design decisions explicitly.
- The paper evaluates Qwen3.6-27B, Qwen3.5-4B and OLMo-Hybrid-7B on H100 with
  PyTorch 2.9.1. Those measurements are motivation, not Ascend evidence.

## Method chain

1. Preserve exact token-addressable KV for every full-attention layer.
2. Preserve the output hidden of every full-attention layer for every cached
   token.
3. Split the hybrid model into independent groups: one full-attention boundary
   and the consecutive linear-attention layers following it.
4. On a prefix-cache hit of length m, retrieve the exact full-attention KV and
   the latest k=ceil(rm) cached boundary hiddens.
5. Start each GDN group's recurrent state at zero and replay only that recent
   tail through the group's linear-attention layers.
6. Skip the final FFN of a replayed group because the next group starts from an
   independently cached full-attention output.
7. Process the unmatched suffix and query with reconstructed GDN states and
   exact full-attention KV.
8. Only after correctness, overlap host-to-device KV transfer with replay.

The 5% and 10% replay budgets are separate algorithm arms. The zero-state-only
arm is an ablation, not Tail-Replay.

## Published Qwen3.6 observations

- LongBench average: full 0.426, zero-only 0.313, 5% replay 0.410 and 10%
  replay 0.417.
- RULER average: full 0.987, zero-only 0.299, 5% replay 0.985 and 10% replay
  0.986.
- At a 31,847-token matched prefix, full-prefill TTFT is 3605.2 ms; 5%
  replay with overlap and FFN skip is 251.8 ms, while 10% is 371.3 ms.
- The serving table reports mean TTFT over 20 timed repetitions and starts the
  clock at cache transfer or replay.

The paper demonstrates strong retention, not strict equality. Local adoption
therefore requires paired task evidence under this lab's quality rule.

## First local falsification gate

Before implementing cache storage or scheduler changes, intercept the exact
Ascend prefill recurrence inputs after causal convolution. For every real GDN
layer compare:

- one full zero-state recurrence;
- an exact head-then-tail split, which must reproduce the full state closely;
- a zero-state 5% tail;
- a zero-state 10% tail.

The exact split is a harness control. A failed exact split invalidates the
probe; only after it passes can zero-tail error be attributed to the paper's
approximation. This recurrence-only result is an optimistic upper bound because
it does not yet include hidden propagation, convolution-state reconstruction,
full-attention boundary caching, or first-token effects.
