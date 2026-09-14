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
  disabled by default and has not yet run on NPU.
- All pinned-image no-device tests pass: 29 total, eight Tail-Replay-specific.
- No Tail-Replay correctness, performance or quality result exists yet.
- Last observed NPU4-7 state was released; this is not a future lease.

## Immediate recovery

1. Read repository AGENTS.md, this file, PAPER_INGESTION.md,
   ARCHITECTURE_FIT.md and SOURCE_MAP.md.
2. Resolve chicaihong01 directly and verify branch/worktree identity.
3. Recheck all NPU status but claim only physical NPU4-7.
4. Verify container device mappings, mounts, ports, CPU/memory and a fresh
   artifact path.
5. Run one eager TP4 service with only ascend,tail_replay_ascend enabled.
6. Send one fresh single-request prefill in the configured 128-4096-token
   window and preserve all four-rank JSONL evidence.
7. Stop the service and prove NPU4-7 release before interpreting results.

## Interpretation gate

Every one of 48 GDN layers on all four ranks must emit both 5% and 10% rows.
The exact head-then-tail split must pass the frozen relative-L2 harness limit.
Only then summarize the zero-tail recurrence error distribution.

Passing this gate does not prove Tail-Replay output quality or speed. It only
admits a full GDN-layer/group replay canary. Failure is a terminal negative for
the current recurrence harness until a concrete source/layout defect is found.
