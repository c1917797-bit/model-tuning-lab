# Tail-Replay Qwen3.6 Ascend piercing handoff

Updated: 2026-09-14

## Current state

- Branch: work/tail-replay-qwen36-ascend-piercing-20260914.
- Worktree:
  /opt/host/vnf/austinov/worktrees/tail-replay-qwen36-ascend-piercing.
- Base checkpoint: 822231451916206dcc60f12341871619f2a4472c.
- The paper, exact Qwen3.6/vLLM-Ascend paths, and the preceding SlimInfer
  runtime metadata result have been reviewed.
- A separate opt-in plugin implements a read-only recurrence oracle. It is
  disabled by default and has now run once on Ascend TP4.
- All pinned-image no-device tests pass: 29 total, eight Tail-Replay-specific.
- The successful NPU run used a 650-token prompt and covered all 48 GDN
  layers, four TP ranks, and both 5% and 10% ratios (384 result rows).
- Every exact-split control passed the frozen 0.01 global relative-L2 gate.
  Worst global relative L2 was 0.00302486 at 5% and 0.00349135 at 10%.
- Zero-state tail-only recurrence was not close to the full recurrent state:
  mean global relative L2 was 0.518888 at 5% and 0.494324 at 10%; worst values
  were 0.886842 and 0.877730.
- This is a recurrence-only mechanism result, not full Tail-Replay correctness,
  performance, quality, or rejection evidence.
- NPU4-7 were released after the successful run; this is not a future lease.

## Immediate recovery

1. Read repository AGENTS.md, this file, PAPER_INGESTION.md,
   ARCHITECTURE_FIT.md and SOURCE_MAP.md.
2. Resolve chicaihong01 directly and verify branch/worktree identity.
3. Read
   /cache/cch/tail-replay-qwen36-ascend-tp4-20260914/recurrence-oracle/short-v4/summary.json.
4. Recheck all NPU status but claim only physical NPU4-7.
5. Implement a non-mutating full GDN-group replay canary: restore/replay the
   causal-convolution state, propagate tail hidden states across the three GDN
   layers after each full-attention boundary, and compare boundary hidden
   states plus first-token logits.
6. Preserve exact-split controls and run a short TP4 request before any
   prefix-cache or performance integration.

## Interpretation gate

The recurrence-only gate passed and admits a full GDN-group replay canary.
That canary must validate convolution state, hidden propagation and first-token
logits with an exact-replay control. Only a passing full-group numerical gate
admits prefix-cache integration and paired cache-hit TTFT screening.
