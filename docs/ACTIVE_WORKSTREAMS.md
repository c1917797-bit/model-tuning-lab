# Active Workstreams

This repository is the single Git control plane for two business tasks.
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

## Mounted supporting workstreams

The following branches are separate validation, reproduction, or research
workstreams. They do not increase the count of long-lived business tasks, but
their worktrees remain active until their branch-local gates close:

- `work/qwen35-experience-ingestion-20260909`: clean and synchronized, but
  explicitly marked `needs-revalidation` before main integration.
- `work/qwen35-sparse-prefix-reproduction`: dirty; preserve all 23 current
  status entries and do not archive or clean it.
- `work/qwen38-nvfp4-ascend-910b4-20260910`: dirty; preserve all 18 current
  status entries. Its branch name is historical and its branch-local handoff
  owns the current model-switch evaluation truth.
- `work/sliminfer-qwen36-ascend-piercing-20260914`: clean and synchronized,
  but active in `attempted-resource-wait`; no SlimInfer NPU result exists.

After the temporary governance worktree is integrated and reclaimed, the
expected registered inventory is seven worktrees: `main` plus the two business
tasks and these four supporting workstreams. The configured budget is eight;
one slot remains for a genuinely independent task.

## Archive policy

Terminal hypotheses are retained by immutable annotated tags and removed from
the active branch list. Local worktrees may be reclaimed only when they are
clean and reachable and no process, resource lease, dependency, or container
mount declaration still references the path.

Current archive tags include:

- `archive/qwen35-query-rewrite-pre-canonical-20260909`
- `archive/qwen35-shortgpt-semantic-reject-20260909`
- `archive/qwen35-pr-pre-canonical-20260909`
- `archive/consolidated-20260912/drrqr-paper-parity-lessons-20260911`

On 2026-09-14, with explicit operator authorization, 116 stopped containers
that referenced only the superseded query-rewrite and ShortGPT worktrees were
removed. No running container, Docker volume, image, active experiment
worktree, or external evidence root was removed. Those two clean worktrees and
the already-integrated paper-parity worktree were then reclaimed only after
their exact tips were proven reachable through immutable remote archive tags.
The two local `archive-local/*` branches remain as additional recovery names.
