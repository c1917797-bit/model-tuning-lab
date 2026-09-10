# Maintainer Handoff

## 0. Status

- Last updated: 2026-09-09.
- Repository: Model Tuning Lab, a Git-native Ascend NPU model-inference optimization workspace.
- Current `main` integrates the HYPIC Paper-to-Ascend historical reproduction and the expanded Paper-to-Ascend maintainer skill pipeline.
- Latest integrated handoff/skill checkpoint: `3286008 docs: align paper-to-ascend with hypic reproduction flow`.
- Integrated maintainer model: `orient -> hypothesize -> baseline -> change -> verify -> measure -> decide`, with pushed evidence, negative-result retention, and explicit recovery checkpoints.
- Fresh clones route machine-bound work through `chicaihong01-host-maintenance`: resolve the live `chicaihong01` manager topology through AWMCP, prefer `ma`, use a target-proven sibling only after topology refresh when needed, pass the operator-provided value only in the connector `verify` field, prove the direct target, then enter `/opt/host/vnf/austinov/model-tuning-lab`.
- The repository-specific active worktree budget is eight.
- Active Qwen3.8 DRRQR worktree:
  /opt/host/vnf/austinov/worktrees/exp-20260904-qwen38-gdn-native-state-layout
  on branch work/drror-objective-loop-skill-20260909. The frozen dense
  performance baseline is 135.142469917 output tok/s and the fixed +10 percent
  target is 148.656716909 output tok/s. The best comparable energy-Dk64 screen
  is +4.752041 percent; it is not accepted.
- The real captured-teacher fixed-beta screen is complete and rejected:
  144/144 dense128/energy64/beta64 trajectories passed numerical and graph
  gates, but beta64 failed 5/144 robustness windows despite a 0.888847 global
  error ratio. Report SHA256:
  ef3df3559bd0ae234c79dda6bafd643177bb412020cb31d8988d0a98150ef3a2.
  No accuracy or endpoint-performance run followed. Resume from
  drrqr-aligned-width-replay-v1, not from fixed beta.
- The aligned Dk48/Dk64/Dk80 captured-teacher screen is complete and accepted
  for full-layer sensitivity capture. All 192 trajectories and 1728 steps
  passed native eager/state/NPUGraph gates. Global mean relative-L2 was
  0.408052174/0.293664554/0.205922839, Dk80/Dk64 was 0.701218, and all 144
  local windows passed with a worst ratio of 1.026426. Report SHA256:
  f635211b4e06dea25a9cf16aa047e403fe6c5ab4fda2506d45bc554882338803.
  This is not endpoint performance or accuracy.
- The promoted all-48-layer Dk48/Dk64/Dk80 replay and exact constrained
  allocation are complete. All 1152 candidate trajectories and 10368 steps
  passed native-NPU replay, but no Dk48 layer passed the frozen five-percent
  local-window gate. Under the uniform-Dk64 total state budget the only
  feasible assignment is all 48 layers at Dk64, with zero aggregate fidelity
  improvement. This rejects only the simple equal-cost energy-selector
  layerwise-width plan. It does not reject DRRQR, exact StrongRRQR, a named
  recurrence-compensation design, endpoint performance, task accuracy, or
  portability. Merged report SHA256:
  de807118e7146c1a1d8dcce6111c3229a6e0d8916a163b3644d0496fd9d0057f.
  Allocation report SHA256:
  20739274c3b18408231b93d89c3ca9f7133ec945176dc9a0898e4bdfdd5dae50.
- The drrqr-cosine-selector-screen-v1 iteration is complete and rejected at
  its CPU pre-screen. Kernel-normalized StrongRRQR Dk64 produced normalized-QK
  RMSE 0.034322883 versus 0.023197267 for energy-Dk64, a 47.960894 percent
  worsening across 768 frozen capture files and all 48 linear-attention
  layers. No NPU replay was admitted or started. Report SHA256:
  71d2a657f6fd8c9fb5b1392f0ea13eef086aba1434b9f297011d4f23e4453305.
  Resume by designing one recurrence-aware coordinate objective against the
  preserved teacher trajectories, not by retrying cosine StrongRRQR,
  implementing heterogeneous cache, or starting generic operator/profiling
  work.
- Two Qwen3.5 branch-local tracks are deliberately separate and are not
  integrated product truth:
  - `work/exp-20260904-qwen35-query-rewrite-3x-e2e` owns the production
    performance loop. Its current user gate is TTFT P95 and TPOT P95 >=1.5x
    at c1/c5/c8/c16 versus the frozen TP4 MTP-off `query_rewrite` baseline.
    BF16, no quantization/retraining/MTP/speculation, and runtime-monkeypatch
    delivery are mandatory. It is blocked on a valid NPU0-3 lease.
  - `work/exp-20260904-qwen35-dense-mtp-paper-to-ascend` is the paper
    migration/research track. Its old MTP candidate is policy-rejected, owns
    no NPU/port lease, and must select a new non-speculative paper before any
    further experiment.
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
5. **Qwen3.8 DRRQR:** keep algorithm selection primary. The complete
   all-48-layer equal-cost energy-selector width allocation was rejected, so
   do not implement mixed-Dk cache/runtime support for it. The next bounded
   decision must test one named selector or recurrence-compensation change
   against the preserved teacher evidence. Only after numerical admission
   should a concrete DRRQR candidate enter model integration, fixed-1024-token
   endpoint screening, and targeted profiling. Final accuracy remains last.

Keep the distinction between three kinds of knowledge explicit:

1. integrated repository truth on `main`;
2. branch-local or artifact-root experiment state;
3. live host state that must be re-proven each session.

## 3. Recent Progress

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

## 4. Current Action

For a new maintainer, start by treating this repository as ready for handoff but not as proof of live host state.

1. Read `AGENTS.md`, this handoff, `docs/RUNBOOK.md`, and `docs/LESSONS_LEARNED.md`.
   For Qwen3.8 DRRQR also read the project AGENTS.md, frozen baseline contract,
   GDN_TEACHER_CAPTURE.md, the captured-reference v2 and aligned-width
   summaries, and the active drrqr-full-layer-sensitivity-budget-v1 iteration
   YAML.
2. If the next task touches `chicaihong01`, use `chicaihong01-host-maintenance` before any remote or NPU action.
3. If the next task is another paper/practice result, start with `paper-to-ascend`; for historical reproduction or adoption claims, include `paper-to-ascend-reproduction` and its evidence contract.
4. Before using any claimed NPU/port lane, read the relevant target-host branch-local handoff and prove current ownership in the same session.
5. For Qwen3.5 work, identify the task ID before acting: paper selection and
   mechanism migration go to the Paper-to-Ascend workstream; cumulative
   `query_rewrite` serving optimization and final acceptance go to the
   performance workstream.

## 5. Next Actions

1. Re-enter the target host through AWMCP and refresh the canonical target repository state: `git fetch`, `git status --short --branch`, `git log -8 --decorate --oneline`, and `git worktree list --porcelain`.
2. For Qwen3.8 DRRQR, treat
   drrqr-full-layer-sensitivity-budget-v1 as complete and rejected. Use its
   preserved teacher evidence to predeclare one bounded selector or
   recurrence-compensation experiment. Do not implement the rejected mixed-Dk
   cache plan, broaden profiling, or run final accuracy before a replacement
   candidate passes its numerical gate and a fixed-1024-token endpoint screen.
3. Inventory active `work/*` branches/worktrees on the target host. Read each `task.json` and `HANDOFF.md` before touching files, containers, ports, processes, or NPUs.
4. For the Qwen3.5 performance loop, do not launch until NPU0-3 ownership is
   proven. Resume with the runtime-only bounded-MMAR/prefetch monkeypatch
   activation gate, fixed-input correctness, c1 fail-fast, then the
   c1/c5/c8/c16 x three-repeat matrix.
5. For Qwen3.5 Paper-to-Ascend, do not resume the old MTP experiment. Select a
   non-speculative, no-retraining, no-quantization paper from a measured dense
   bottleneck and treat its result as candidate input, not final performance
   evidence.
6. For future Paper-to-Ascend work, choose the narrow route:
   - new paper idea: `paper-ingestion` -> `ascend-architecture-fit` -> `ascend-source-map` -> canary;
   - prior success or historical ruler: `paper-to-ascend-reproduction`;
   - low-level kernel/operator/profiler question: `ascend-cannbot-profiler`;
   - final result: `paper-to-ascend-reporting`.
7. Do not reuse HYPIC absolute numbers across model, accelerator generation, TP degree, cache denominator, or capacity-budget changes. Create a fresh experiment, baseline, and artifact root.
8. Re-run full validation on the Linux target before claiming the handoff is execution-ready.

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
- Do not start a second container over physical NPUs already mapped into a
  running container merely because npu-smi shows no compute process. Inspect
  container device ownership and reuse the single audited owner when safe.
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

Qwen3.8 DRRQR-specific resume files:

```text
.agents/evals/practice-iterations/drrqr-aligned-width-replay-v1.yaml
.agents/evals/practice-iterations/drrqr-full-layer-sensitivity-budget-v1.yaml
projects/drror_vllm_ascend/AGENTS.md
projects/drror_vllm_ascend/docs/experiments/qwen38-drrqr-correctness-20260908/FROZEN_BASELINE_V1.json
projects/drror_vllm_ascend/docs/experiments/qwen38-drrqr-correctness-20260908/GDN_TEACHER_CAPTURE.md
projects/drror_vllm_ascend/docs/experiments/qwen38-drrqr-correctness-20260908/gdn-teacher-captured-reference.v2.summary.json
projects/drror_vllm_ascend/docs/experiments/qwen38-drrqr-correctness-20260908/gdn-teacher-width-curve.v1.summary.json
```

HYPIC-specific takeover reminder: use the integrated `paper-to-ascend-reproduction` skill and its `references/evidence-contract.md`; keep machine-specific artifact roots and resource lanes in the workstream handoff, not in reusable skills.

Qwen3.5-specific takeover reminder: on chicaihong01 read both target-host
branch-local handoffs before acting:

```text
/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e/.agents/workstreams/exp-20260904-qwen35-query-rewrite-3x-e2e/HANDOFF.md
/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-dense-mtp-paper-to-ascend/.agents/workstreams/exp-20260904-qwen35-dense-mtp-paper-to-ascend/HANDOFF.md
```
