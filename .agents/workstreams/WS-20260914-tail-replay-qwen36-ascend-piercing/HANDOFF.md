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
- A non-mutating full three-layer GDN-group oracle is now implemented in the
  plugin. It clones the exact boundary hidden/residual pair, isolates both
  convolution and recurrent state, and records exact-full versus 5%/10%
  suffix replay metrics. It has not run on NPU yet.
- The pinned-image offline suite now passes 38/38 tests, including 17 focused
  Tail-Replay tests, and early group-oracle plugin registration passes without
  importing the device backend.
- NPU4-7 were released after the successful run; this is not a future lease.

## Immediate recovery

1. Read repository AGENTS.md, this file, PAPER_INGESTION.md,
   ARCHITECTURE_FIT.md and SOURCE_MAP.md.
2. Resolve chicaihong01 directly and verify branch/worktree identity.
3. Read
   /cache/cch/tail-replay-qwen36-ascend-tp4-20260914/recurrence-oracle/short-v4/summary.json.
4. Recheck all NPU status but claim only physical NPU4-7.
5. Read FULL_GROUP_ORACLE_DESIGN.md and review the uncommitted or latest
   full-group implementation.
6. Run one 650-token TP4 group-oracle request only when all physical NPU4-7
   are free. Preserve exact controls and do not retry an NPU fault blindly.
7. If all-rank exact controls pass, interpret group state/boundary errors and
   implement the separate first-token reconstructed-cache comparison before
   any prefix-cache or performance integration.

## Interpretation gate

The recurrence-only gate passed and admits a full GDN-group replay canary.
The prepared first stage validates convolution state, recurrent state and
hidden propagation with an exact-replay control. It does not yet validate
first-token logits. Both the group gate and the following isolated first-token
cache-swap gate must pass before prefix-cache integration and paired cache-hit
TTFT screening.
