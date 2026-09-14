# Maintainer Handoff

## Repository integration update — 2026-09-12

Integrated the validated DRRQR paper-parity and source-selection/baseline
lessons. Exact source: `4617c5e4ccd8f4dc1c996bfc9b64f3f44bb30b72`;
target parent: `80cf967c929dc40842f47a15f0601b0a9b7b686a`.
See `docs/BRANCH_CONSOLIDATION_20260912.md` for retention and remaining work.
The older runtime descriptions below are historical, not current occupancy.

## Branch-local SlimInfer update — 2026-09-14

On branch `work/sliminfer-qwen36-ascend-piercing-20260914`, the Qwen3.6-27B
TP4 identity and read-only runtime metadata canaries passed on physical
NPU4-7, and the lane was released. The metadata run captured a real prefill
and decode on all four ranks. All 16 full-attention layers shared one
AscendMetadata; the 48 GDN layers shared three metadata objects by relative
position in the repeating layer pattern. The top-level slot mapping was empty,
while the live full-attention slot mapping was nested in AscendMetadata.

This proves runtime structure only. Real SlimInfer pruning, Tail-Replay state
reconstruction, performance, and accuracy are still unproven. The user
approved preserving the SlimInfer result and prioritizing an independent
Tail-Replay 5%/10% GDN-state and first-token numerical canary. Resume at
`.agents/experiments/exp-20260914-sliminfer-qwen36.yaml`,
`docs/SLIMINFER_IDENTITY_CANARY_20260914.md`, and
`docs/SLIMINFER_RUNTIME_METADATA_CANARY_20260914.md`.


## 0. Status

- Last updated: 2026-09-09.
- Repository: Model Tuning Lab, a Git-native Ascend NPU model-inference optimization workspace.
- Current `main` integrates the HYPIC Paper-to-Ascend historical reproduction,
  the expanded Paper-to-Ascend pipeline, and tightened Ascend opportunity,
  runtime-path, evidence, collective-lifecycle, and container-state gates.
- Latest integrated handoff/skill checkpoint: `3286008 docs: align paper-to-ascend with hypic reproduction flow`.
- Integrated maintainer model: `orient -> hypothesize -> baseline -> change -> verify -> measure -> decide`, with pushed evidence, negative-result retention, and explicit recovery checkpoints.
- Fresh clones route machine-bound work through `chicaihong01-host-maintenance`: resolve `chicaihong01/ma` through AWMCP, pass the operator-provided value only in the connector `verify` field, prove the direct target, then enter `/opt/host/vnf/austinov/model-tuning-lab`.
- The repository has two long-lived business workstreams. A hypothesis does not
  receive a permanent worktree; it stays inside its owning task and is archived
  immediately after a terminal decision.
- Active branch-local work is not integrated product truth:
  - `work/qwen35-performance-delivery` owns the Qwen3.5 production
    performance loop. Its current user gate is at least 40% lower TTFT P95 and
    at least 20% lower TPOT P95 at c1/c5/c8/c16 versus the frozen TP4 MTP-off
    `query_rewrite` baseline, with zero material quality regressions.
    BF16, no quantization/retraining/MTP/speculation, and runtime-monkeypatch
    delivery are mandatory. It is blocked on a valid NPU0-3 lease.
  - `work/drror-objective-loop-skill-20260909` owns the DRRQR/Objective
    optimization task. Its current captured-teacher fidelity iteration is
    in progress and must remain isolated from Qwen3.5 delivery.
  - The old dense-MTP, prefix-cache, ShortGPT, and duplicate query-rewrite
    candidates are superseded. Immutable remote tags retain their evidence;
    rejected code is not merged into `main`.
  - `work/drror-objective-loop-skill-20260909` retains imported DRRQR/objective
    history for adaptation; it is not integration-ready and remains branch-local.
- Local Git state alone does not prove current target-host runtime state. Re-check NPU, container, port, memory, process, controller, and worktree ownership before touching hardware.
- Validation in this maintenance turn: Git status/log checks passed; `git diff --check` on the documentation update passed; a CRLF-tolerant Maintainer Skill Tree structure check passed with 26 skills. `./scripts/validate-mst.sh` was attempted on Windows and failed on CRLF shell-script parsing before repository checks; `python -m pytest` was attempted with the local Python 3.9 and failed because `pytest` is not installed. Run full validation on the Linux target before claiming execution readiness.

## 1. North Star

Make every Ascend inference optimization claim reproducible, auditable, rollback-safe, and resumable from Git alone. Preserve successful, rejected, inconclusive, and failed experiments while keeping failed active code out of the final safe tree.

```text
orient -> hypothesize -> baseline -> change -> verify -> measure -> decide
   ^                                                           |
   +---------------- Git evidence and next loop <---------------+
```

## 2. Current Focus

The integrated `main` focus is now a reusable Paper-to-Ascend operating system:

1. **Paper-to-Ascend pipeline:** `paper-to-ascend` now routes through paper ingestion, architecture fit, source mapping, canary implementation, benchmark evidence, CANN/profiler attribution when needed, reproduction mode, and reporting.
2. **HYPIC reproduction pattern:** historical/practice-result reproduction uses `paper-to-ascend-reproduction` with a frozen one-switch A/B denominator, mechanism activation evidence, resumable artifacts, and independent fail-closed audit.
3. **Target-host safety:** `chicaihong01-host-maintenance` remains the gate for any live device work. Runtime state is not inherited from this local clone.
4. **Qwen3.5 two-track boundary:** Paper-to-Ascend may produce a bounded
   candidate and mechanism evidence, but only the separate `query_rewrite`
   performance workstream owns its frozen denominator, final quality gate,
   serving delivery contract, and performance acceptance decision.

Keep the distinction between three kinds of knowledge explicit:

1. integrated repository truth on `main`;
2. branch-local or artifact-root experiment state;
3. live host state that must be re-proven each session.

## 3. Recent Progress

- Normalized the Qwen3.5 task onto
  `work/qwen35-performance-delivery` at
  `/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery`. The
  scheduler-diagnostic checkpoint is pushed, while unvalidated prefetch and
  terminal ShortGPT material are preserved under archive tags.
- Two archived local worktrees are temporarily retained only because exited
  experiment containers still declare their old paths as mounts. Do not remove
  those worktrees or containers until exact ownership and restart requirements
  are reviewed.
- Consolidated target-host worktrees from eight to five: every committed
  checkpoint was pushed, two superseded experiment worktrees were safely
  reclaimed, and the transient consolidation worktree was removed after
  integration. Dirty or not-ready worktrees were preserved.
- Isolated and integrated only the three validated maintainer-skill commits
  from a history-coupled branch. DRRQR/project imports remain branch-local.

- Integrated the Ascend maintainer skills, experiment schema, workstream policy, and commit-implies-push tuning flywheel.
- Diagnosed low ordinary memory as a roughly 1.9 TiB 1 GiB HugeTLB reservation rather than ordinary process consumption; no risky hugepage release was performed.
- Migrated the canonical target-host repository to `/opt/host/vnf/austinov/model-tuning-lab`, retaining `/cache/austinov/model-tuning-lab` as a compatibility symlink.
- Repaired Git HTTPS runtime/CA handling without disabling TLS verification.
- Prepared source workspaces for `vllm-ascend`, CANN `ops-transformer`, `cannbot-skills`, and `cann-recipes-infer` under `/home/mtuser/cch`.
- Verified the vLLM-Ascend container had `torch_npu.profiler`, `msprof`, and `asys`; profiler guidance now lives in `ascend-cannbot-profiler`.
- Built a Dynamic MoE Paper-to-Ascend exemplar and preserved a useful negative result: local expert GMM improved, but routing/packing overhead dominated whole-block latency. The implementation was rejected while the paper/full-model claim remained inconclusive.
- Integrated HYPIC reproduction lessons: a changed environment can reproduce direction and approximate magnitude only with a fresh same-denominator A/B, mechanism activation proof, repeated performance/quality units, resumable raw artifacts, and independent audit.
- Expanded the Paper-to-Ascend skill system with `paper-ingestion`, `ascend-architecture-fit`, `ascend-source-map`, `ascend-canary-implementation`, `paper-to-ascend-reporting`, `ascend-cannbot-profiler`, and `paper-to-ascend-reproduction`.
- Separated the active Qwen3.5 performance loop from the historical dense-MTP
  Paper-to-Ascend experiment. The MTP paper candidate is no longer an allowed
  implementation route for the performance objective and no longer claims
  NPU0-3.
- Completed the runtime-only bounded-MMAR activation gate on physical NPU0-3.
  All four TP workers activated the monkeypatch and the c1 three-repeat screen
  achieved `1.9128x` TTFT P95 but only `1.2085x` TPOT P95 versus the frozen
  MTP-off baseline. The candidate was rejected before full-matrix expansion;
  NPU0-3 were released and the unrelated NPU4-7 workload was untouched.

## 4. Current Action

For a new maintainer, start by treating this repository as ready for handoff but not as proof of live host state.

1. Read `AGENTS.md`, this handoff, `docs/RUNBOOK.md`, and `docs/LESSONS_LEARNED.md`.
2. If the next task touches `chicaihong01`, use `chicaihong01-host-maintenance` before any remote or NPU action.
3. If the next task is another paper/practice result, start with `paper-to-ascend`; for historical reproduction or adoption claims, include `paper-to-ascend-reproduction` and its evidence contract.
4. Before using any claimed NPU/port lane, read the relevant target-host branch-local handoff and prove current ownership in the same session.
5. For Qwen3.5 work, identify the task ID before acting: paper selection and
   mechanism migration go to the Paper-to-Ascend workstream; cumulative
   `query_rewrite` serving optimization and final acceptance go to the
   performance workstream.

## 5. Next Actions

1. Re-enter the target host through AWMCP and refresh the canonical target repository state: `git fetch`, `git status --short --branch`, `git log -8 --decorate --oneline`, and `git worktree list --porcelain`.
2. Start from `docs/ACTIVE_WORKSTREAMS.md`. Resume only one of the two
   canonical task branches; archived experiment worktrees are not active work.
3. For the Qwen3.5 performance loop, read branch commit
   `c71de549b3ee32030799d66198786d8619aba3c1`. Do not retry the rejected
   bounded-MMAR stack unchanged. Prove NPU0-3 ownership, then gate a materially
   new ASCEND910B decode MMAR/HCCL lifecycle implementation on exact BF16 M=1
   shapes before another E2E launch.
4. Do not recreate or resume the old MTP or prefix-cache worktrees. Their remote
   branches are evidence archives. Any new paper candidate requires a new
   workstream and must be non-speculative, no-retraining, and no-quantization.
5. For future Paper-to-Ascend work, choose the narrow route:
   - new paper idea: `paper-ingestion` -> `ascend-architecture-fit` -> `ascend-source-map` -> canary;
   - prior success or historical ruler: `paper-to-ascend-reproduction`;
   - low-level kernel/operator/profiler question: `ascend-cannbot-profiler`;
   - final result: `paper-to-ascend-reporting`.
6. Do not reuse HYPIC absolute numbers across model, accelerator generation, TP degree, cache denominator, or capacity-budget changes. Create a fresh experiment, baseline, and artifact root.
7. Re-run full validation on the Linux target before claiming the handoff is execution-ready.

## 6. Validation Commands

```text
git status --short --branch
git log -8 --decorate --oneline
git worktree list --porcelain
./scripts/validate-mst.sh
python -m pytest
git diff --check
```

For tuning evidence, also run the exact benchmark/profiling/audit commands declared in the experiment record and prove intended NPU processes in the same session.

## 7. Do Not Do

```text
- Do not use chat history as the only handoff state.
- Do not assume this local clone proves current chicaihong01 runtime state.
- Do not commit or print the AWMCP verification value; obtain it through the approved runtime channel and pass it only in the connector verify field.
- Do not ignore workstream claims, resource leases, controllers, or neighboring protected NPU lanes.
- Do not claim an improvement without one-switch or otherwise predeclared comparable baseline/candidate evidence and correctness gates.
- Do not choose a paper by novelty alone. First prove mechanism fit, bottleneck fit, source seam, and resource isolation.
- Do not apply architecture-specific methods to an incompatible checkpoint.
- Do not convert a rejected implementation into a rejected-paper claim; keep implementation, operator/block, service, full-model, and adoption scopes separate.
- Do not pool HYPIC, Dynamic MoE, prefix-cache, PDC coexistence, or other experiments across different denominators or scientific questions.
- Do not pool the Qwen3.5 Paper-to-Ascend c8 synthetic protocol with the
  frozen `query_rewrite` c1/c5/c8/c16 performance denominator.
- Do not treat a paper-level mechanism success as a production serving win;
  the performance workstream must independently prove activation, quality,
  P95/P99, throughput, and resource safety.
- Do not discard rejected, inconclusive, or failed experiments; recover active code while preserving evidence.
- Do not merge failed active code into main.
- Do not release the 1 GiB HugeTLB pool merely because many pages look free; identify OVS/DPDK/VNF consumers and define rollback first.
- Do not assume a container is ready because it exists; prove listener, health, real request, and NPU workers in the same session.
- Do not disable TLS verification to repair Git.
- Do not commit credentials, SSH material, shell history, private certificates, datasets, model weights, checkpoints, raw profiler traces, or large generated outputs.
```

## 8. Recovery / Resume Commands

```text
git status --short --branch
git log -8 --decorate --oneline
git worktree list --porcelain
sed -n '1,260p' AGENTS.md
sed -n '1,320p' .agents/HANDOFF.md
sed -n '1,340p' docs/RUNBOOK.md
sed -n '1,420p' docs/LESSONS_LEARNED.md
find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md -type f | sort
./scripts/validate-mst.sh
python -m pytest
git diff --check
```

If a `work/*` branch is active, read its `.agents/workstreams/<task-id>/task.json`, branch-local `HANDOFF.md`, experiment/evidence/decision ledgers, and exact audit/resume commands before acting.

HYPIC-specific takeover reminder: use the integrated `paper-to-ascend-reproduction` skill and its `references/evidence-contract.md`; keep machine-specific artifact roots and resource lanes in the workstream handoff, not in reusable skills.

Qwen3.5-specific takeover reminder: on chicaihong01 read the active target-host
branch-local handoff before acting:

```text
/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e/.agents/workstreams/exp-20260904-qwen35-query-rewrite-3x-e2e/HANDOFF.md
```
