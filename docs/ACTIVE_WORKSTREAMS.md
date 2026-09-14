# Active Workstreams

This repository is the single Git control plane for multiple business tasks.
Reusable maintainer skills, safety policy, experiment schemas, and integrated
handoff truth live on `main`. Implementation and live evidence remain on the
owning task branch until their gates pass.

## 1. Qwen3.5 performance delivery

- Branch: `work/qwen35-performance-delivery`
- Worktree: `/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery`
- Goal: at least 40% lower TTFT P95 and 20% lower TPOT P95 at
  c1/c5/c8/c16, with zero material quality regressions.
- Delivery: removable runtime Python plugin against the unchanged official
  vLLM-Ascend 0.23.0 image.

All operator, scheduler, monkeypatch, benchmark, quality, and PR preparation
belong to this workstream. Do not create a long-lived worktree for each
hypothesis.

## 2. DRRQR / Objective optimization

- Branch: `work/drror-objective-loop-skill-20260909`
- Current worktree:
  `/opt/host/vnf/austinov/worktrees/exp-20260904-qwen38-gdn-native-state-layout`
- Goal and current bounded iteration are defined by the branch-local task,
  handoff, and `.agents/evals/practice-iterations/` records.

This branch currently has an in-progress captured-teacher fidelity iteration
and an exited container that declares the current worktree path. Do not rename,
split, or move it while either condition remains.

## 3. SlimInfer Qwen3.6 Paper-to-Ascend piercing

- Branch: `work/sliminfer-qwen36-ascend-piercing-20260914`
- Worktree:
  `/opt/host/vnf/austinov/worktrees/sliminfer-qwen36-ascend-piercing`
- Goal: test a faithful, architecture-aware SlimInfer port on the same
  Qwen3.6-27B TP4 ruler used for the HYPIC-style report.
- Current decision: the removable plugin and four-rank identity path are
  verified on physical NPU4-7; algorithmic pruning, performance, and accuracy
  remain unproven.
- Next gate: a whole-prompt-only semantic pruning canary that preserves
  absolute RoPE positions, uses compact KV positions for full attention, and
  rejects resumed/chunked prompt state until its semantics are implemented.

This is an independent Paper-to-Ascend workstream. HYPIC measurements are a
reporting/protocol reference only and are not a SlimInfer baseline or result.

## Archive policy

Terminal hypotheses are retained by immutable annotated tags and removed from
the active branch list. Local worktrees may be reclaimed only when they are
clean and reachable and no process, resource lease, dependency, or container
mount declaration still references the path.

Current archive tags include:

- `archive/qwen35-query-rewrite-pre-canonical-20260909`
- `archive/qwen35-shortgpt-semantic-reject-20260909`
- `archive/qwen35-pr-pre-canonical-20260909`

The first two archived worktrees remain on disk only because stopped
experiment containers retain mount declarations. Removing those container
records is a separate environment cleanup decision, not a Git shortcut.
