# Tail-Replay Qwen3.6 Ascend piercing handoff

Updated: 2026-09-15

## Final update

- The TP4 entry diagnostic, full three-GDN-group oracle, and isolated first
  real decode-token comparison have now completed on physical NPU4-7.
- The final pinned-image suite passes 42/42.
- First-decode exact controls passed 64/64 and live caches were bitwise
  preserved 64/64.
- The 5% and 10% candidates produced mean group-output relative L2 of
  0.053577 and 0.051287, with mean recurrent-state relative L2 of 0.502004
  and 0.476821 respectively. Every candidate group-output result exceeded
  the 0.01 exact-control ceiling.
- The tested candidates are closed as mechanism-rejected and were not admitted
  to cache-hit TTFT, performance, or task-quality testing.
- Final report: `TAIL_REPLAY_ASCEND_PIERCING_REPORT.md`.
- Final evidence and decision records use the 20260915 filenames in this
  directory. Older records remain as historical stage evidence.
- The owned experiment container was stopped and physical NPU4-7 were
  confirmed free after the run.

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
- A non-mutating full three-layer GDN-group oracle is implemented in the
  plugin. It clones the exact boundary hidden/residual pair, isolates both
  convolution and recurrent state, and is designed to record exact-full versus
  5%/10% suffix replay metrics.
- Two TP2 staging attempts used physical NPU6-7 only. v1 was a capacity/startup
  failure: model weights left negative KV-cache capacity. v2 became healthy and
  completed the fixed 650-token request, but emitted no group attempts or
  results. The strict summary rejected it with all 32 expected rank/group keys
  missing. This is a hot-path activation failure, not a Tail-Replay numerical,
  performance, quality, or rejection result.
- Before the patch-order correction, the pinned-image suite passed 40/40 and
  the focused suite passed 20/20 after adding the pre-filter group-entry event.
- The v2 activation failure has now been source-attributed: the plugin wrapped
  `Qwen3_5DecoderLayer.forward` before
  `vllm_ascend.patch.worker.patch_qwen3_5` replaced it with the final Ascend
  forward. The corrected plugin waits for that Ascend patch module, then wraps
  the final function and emits `group_oracle_ascend_patch_order_verified`.
  The pinned-image suite passes 42/42 and the focused Tail-Replay suite passes
  21/21 after this correction. The corrected bytes have not yet run on NPU.
- TP2 staging artifacts are under
  /cache/cch/tail-replay-qwen36-ascend-tp2-staging-20260914/full-group-oracle/short-v2.
  request/response/runtime/summary SHA256 values are respectively
  1236c33d92c4b659286f5229630cdfe4bf909c4628c43c9d321c253ac00beb4e,
  c32648edfaab89fc975ca3bd8807baa08c2e93b90f97a9ac9c5b8204020bd3f4,
  b58ef3833e5554dde67f2a1395946b8bdf11b2a47e5a615870c900e7c5b5f15a,
  and 490e3de07c23a11249bd0ea9803818144c68cbccf4930f1b92d18a0fd7a6dcee.
- NPU6-7 were confirmed released after TP2 staging. NPU4-5 were occupied by an
  unrelated task at the last check. Neither observation is a future lease.

## Immediate recovery

1. Read repository AGENTS.md, this file, PAPER_INGESTION.md,
   ARCHITECTURE_FIT.md and SOURCE_MAP.md.
2. Resolve chicaihong01 directly and verify branch/worktree identity.
3. Read
   /cache/cch/tail-replay-qwen36-ascend-tp4-20260914/recurrence-oracle/short-v4/summary.json.
4. Recheck all NPU status but claim only physical NPU4-7.
5. Read FULL_GROUP_ORACLE_DESIGN.md, the TP2 short-v2 strict summary, and the
   latest full-group implementation.
6. Run a fresh 650-token TP4 entry-only diagnostic after rechecking physical
   NPU4-7. Set the minimum capture threshold above 650 so only patch-order and
   `group_oracle_group_start_seen` evidence is emitted. Require all four ranks.
7. Run one 650-token TP4 group-oracle request only when all physical NPU4-7
   are free and the entry diagnostic has proved activation. Preserve exact
   controls and do not retry an NPU fault blindly.
8. If all-rank exact controls pass, interpret group state/boundary errors and
   implement the separate first-token reconstructed-cache comparison before
   any prefix-cache or performance integration.

## Interpretation gate

The recurrence-only gate passed and admits a full GDN-group replay canary.
The first full-group staging request did not activate the wrapper, so it
validated only startup/request plumbing and the fail-closed evidence checker.
The actual worker invocation seam must be proven next. Once active, the group
stage validates convolution state, recurrent state and hidden propagation with
an exact-replay control; it still does not validate first-token logits. Both the
group gate and the following isolated first-token cache-swap gate must pass
before prefix-cache integration and paired cache-hit TTFT screening.
