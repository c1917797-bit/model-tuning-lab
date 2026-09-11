# Maintainer Handoff

## 0. Status

- Last updated: 2026-09-10.
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
- The drrqr-causal-kernel-selector-v1 iteration is also complete and rejected
  at its held-out CPU gate. The selector used calibration captures 0-11 only,
  but on untouched captures 12-15 its Dk64 normalized-QK RMSE was 0.079352171
  versus 0.022558974 for energy-Dk64, a 251.754350 percent worsening. It
  retained only 0.535215 mean Q energy despite 0.777442 mean K energy. No NPU
  replay was admitted or started. Report SHA256:
  77e08035e819c6d680da929687cb8b65d5ce5a45df3784b4914c90c34df5bad9.
  The drrqr-causal-exchange-prototype-v1 representative screen is complete and
  rejected. It accepted 364 train-only swaps across 96 heads and improved mean
  train RMSE by about 11.7 percent while preserving the 98 percent Q/K energy
  floors, but held-out aggregate RMSE improved only 2.163152 percent; three
  heads worsened by more than 5 percent. No NPU replay was admitted. Report
  SHA256: 32ce108ce430e81e221547b6b9244d47a9971ddab5d54cad4ae9bc500dd1b38a.
  The drrqr-causal-exchange-regularized-v1 screen is complete and rejected. With
  64 training tokens and one swap per head, 82/96 heads improved, no head
  worsened over 5 percent, and Q/K energy ratios stayed above 0.991, but
  aggregate held-out RMSE improved only 2.268935 percent, far below the 10
  percent gate. No NPU replay was admitted. Report SHA256:
  c110a0dc37b7b0eed976dc81c5f0bfc2ab873f738f9fb4f3cac1f239b2fb6300.
  Stop Q/K-only selector tuning. The
  drrqr-rich-state-calibration-capture-v1 iteration adapted the existing
  pass-through observer to the 16 frozen non-evaluation calibration rows:
  exact 128-token raw-ID prompts, indices 0-11 reserved for later fitting and
  12-15 for later admission, one prefill plus eight decode steps, six layers
  and all ranks. It must pass software gates and a fresh physical-NPU4-7
  ownership preflight before one bounded dense capture; it is not a candidate,
  performance run or accuracy test. One launch attempt
  (exec-0000000000001233) stopped at the pre-launch provenance gate with
  ValueError: build source is not the plugin repository: the old build
  manifest names its original immutable source path, while the new observer
  tools run from a relocated source root. The failure occurred before output
  directory creation, model loading or NPU use. Preserve the original manifest
  and SHA. The shared build verifier now accepts relocation only after proving
  the original build snapshot, relocated runtime package, wheel and installed
  package byte-for-byte; it records the original and verified paths separately.
  The real 0.1.11 artifacts passed that gate in operation
  exec-0000000000001263 without model loading or NPU use. A subsequent formal
  launch (exec-000000000000127e) also stopped before output creation, model
  loading or NPU use: using the relocated runtime root as the container working
  directory caused Python package discovery to resolve that source tree instead
  of the installed wheel. Preserve this failure as a pre-launch environment
  defect. The bounded correction is to run the same absolute launcher from
  /tmp, allowing the launcher to verify the relocated source root while the
  installed-package identity check resolves site-packages; refresh NPU4-7
  ownership immediately before that corrected gate retry. The corrected
  service (exec-0000000000001283) and collector
  (exec-000000000000128b) completed successfully and cleaned their process
  group. The independent audit (exec-000000000000129b) loaded all 3456 tensor
  archives: 59136 tensors / 7220984832 logical bytes, 384 state trajectories
  and 3072 byte-exact decode state transitions. It also passed request/token
  and receipt hashes, finite tensors, stable state-storage metadata,
  operator-to-post-RMS byte binding, actual Ascend source identity and loaded
  native-library identity. Audit SHA256:
  edfc6780adde0dff36f1fd3872452f0d2ad77541e06ac500de3eb3ec72e5b2a5.
  This admits the corpus as selector input only, not as a candidate, endpoint
  performance, task accuracy or portability result. The next iteration must
  fit a named recurrence-aware selector on indices 0-11 only and make its
  admission decision only on untouched indices 12-15.
- The drrqr-recurrent-trajectory-selector-v1 iteration is complete and
  rejected. Its first run is preserved as invalid because the fit comparator
  labelled energy still exchanged coordinates. After fixing only that proven
  baseline-identity defect, the corrected run proved the frozen energy plan had
  zero changed heads, zero swaps and unit Q/K retained-energy ratios, with
  heldout loaded only after fit lock. The locked read-feedback selector improved
  heldout post-RMS relative-L2 by only 3.570486 percent and selected-state
  relative-L2 by 1.140319 percent; only 53/96 heads were non-worse and the
  worst head regressed 14.621819 percent. It failed three predeclared gates and
  was not admitted to NPU replay, endpoint performance or task accuracy.
  Corrected report SHA256:
  0ee9838dfe41fecb4b89b01963764f51fcf02f4009c611b7eac5cc7ce99ddaa5.
  Stop tuning nearby recurrence-weighted coordinate-exchange objectives. The
  next DRRQR iteration must test a materially different structured
  recurrence-compensation/subspace design with an explicit foldability and
  Ascend cost model before any operator work.
- The drrqr-pairwise-orthogonal-projection-v1 iteration is complete and
  rejected. Its at-most-two-sparse orthonormal Dk64 transforms and static cost
  gate were valid, but three-fold cross-validation over calibration indices
  0-11 made post-RMS relative-L2 75.012854 percent worse than frozen
  energy-Dk64. Only 9/96 heads were non-worse and the worst head ratio was
  4.511841; state relative-L2 improved only 0.390987 percent. Previously viewed
  indices 12-15 were not used. No fresh capture, NPU replay, integration,
  endpoint benchmark or task accuracy followed. Report SHA256:
  16cd56031ca22fee6a934f8a154731bd9cb6d9eb39fdb86f7d5dbe464c04cb75.
  Stop nearby sparse-subspace variants. The next algorithmic test should keep
  dense prefill and exact first-token state construction, then transition once
  to aligned energy-Dk64 state for decode, with cache conversion and phase
  identity designed explicitly before endpoint work.
- The drrqr-dense-prefill-dk64-decode-v1 iteration is complete and rejected.
  Exact dense prefill followed by a single frozen energy-Dk64 transition
  improved aggregate decode state relative-L2 by 59.985923 percent and made
  85/96 heads non-worse, but aggregate decode post-RMS relative-L2 worsened by
  2.183104 percent and the worst head regressed 33.790207 percent. The full
  project suite passed 501 tests. No fresh capture, NPU replay, integration,
  endpoint benchmark or task accuracy followed. Report SHA256:
  94389564a28c28e9eaa1f2baf91502ada40140661b4a12d4c5775325e44edc2e.
  Do not retry nearby dense-prefill transition variants or optimize a state
  proxy alone. The next bounded algorithmic direction is an explicit low-cost
  decode-tail/output correction with static foldability and Ascend cost gates.
- The drrqr-tail-dot-recurrent-compensation-v1 iteration is complete and
  rejected. Its fixed, data-independent 64-to-16 signed Walsh-Hadamard tail
  sketch preserved the Dk64 recurrent state bitwise and kept a five-eighths
  dense Q/K projection-width cost model, but decode post-RMS worsened 5.583663
  percent, prefill post-RMS worsened 5.857686 percent, only 51/96 heads were
  non-worse, and the worst head ratio was 3.672526. The full project suite
  passed 505 tests. No NPU replay, integration, endpoint benchmark or task
  accuracy followed. Report SHA256:
  ecca3e9d2b16eaad16108f672879bec66eefede46f8216340da65b5f6a18f9ab.
  Do not tune the sketch seed or width. The evidence points away from the
  instantaneous tail dot and toward historical reads from discarded state
  columns; any next candidate must represent that term under a bounded aligned
  state/projection budget.
- The drrqr-historical-tail-sketch-foldability-v1 source/configuration audit is
  complete and rejected before implementation. A dense 64-to-16 transform over
  discarded post-convolution coordinates cannot be exactly folded through the
  channel-specific causal-convolution kernels and enabled SiLU activation.
  Computing it after convolution would retain the discarded source channels and
  invalidate the claimed five-eighths projection/conv cost. No CPU replay, NPU
  run, endpoint benchmark or task accuracy followed. Resume with the exact
  aligned uniform energy-Dk80 plan (SHA256
  934ef84ddea2ab0544ac0146d1ab4c3a8fd47d53e97cde6222a3ac2b2ca648ae)
  for an integrated fixed-1024-token endpoint screen. Dk80 is a concrete
  historical-state-retention DRRQR candidate, not the rejected equal-cost
  mixed-layer plan. Only a promising endpoint result admits candidate-specific
  Ascend fusion or data-movement work.
- The drrqr-uniform-dk80-endpoint-screen-v1 iteration is complete and rejected
  before performance. The exact Dk80 plan passed short prefill, recurrent decode
  eager/state and recurrent NPUGraph gates; the corrected four-worker service
  also reached HTTP health with exact plan, wheel and worker identities. Its
  mandatory 16-request, 32768-input/16-output mixed sequence gate then produced
  13 HTTP 400 responses caused by NaN serialization; only three measured
  requests plus the warmup returned 200. All 512 expected mixed-prefill calls
  were observed across four workers. Receipt SHA256:
  7130f9dbdf73caaa0cb98c50c14cd5ed3b85a8cb07a3360c29b7ca03732ccc86.
  No endpoint performance, profiling or accuracy run followed. This rejects
  Dk80 endpoint promotion but does not yet distinguish algorithm instability
  from the production-length chunk-prefill path, which dispatches through
  chunk_gated_delta_rule_fwd_h and chunk_fwd_o rather than the separately
  validated recurrent decode operator. Resume with the single-request,
  seam-bound drrqr-dk80-prefill-kernel-isolation-v1 iteration. Build a
  plugin-owned Dk80 prefill adapter only if finite inputs first become
  non-finite inside that chunk boundary; otherwise return to a mathematically
  different exactly foldable DRRQR algorithm/state design.
- The seam-bound drrqr-dk80-prefill-kernel-isolation-v1 iteration is complete
  and inconclusive about the prior concurrent NaN. After correcting two
  preserved launch defects, plugin 0.1.13 served one exact 32768-token prompt
  on physical NPU4-7. All four workers recorded all 48 linear-attention layers
  and all 11 declared raw/normalized/chunk/state/GDN stages: 192 complete
  traces, no NaN or Inf, and no arithmetic change. The request returned HTTP
  200 with one length-terminated token. Evidence SHA256:
  ce0e5243594bad01540fbcf1e4ea849e6513a5172c79ff98ec5759e1c6299162.
  This disproves only a deterministic failure for that serial pure-prefill
  prompt; it does not clear the earlier 13/16 failures under the concurrent
  mixed-prefill/decode regime and does not justify a replacement prefill
  operator. Resume with drrqr-dk80-mixed-cache-state-isolation-v1, preserving
  the original 16-prompt cohort and binding per-request phase, state-cache
  slots/storage and the first non-finite GDN boundary before any operator work.
- The drrqr-dk80-mixed-cache-state-isolation-v1 diagnostic is complete.
  Plugin 0.1.17 reproduced the mixed cohort outcome: 10/16 HTTP 200 and six
  NaN serialization failures. All four workers first bound non-finiteness at
  call 7, `language_model.model.layers.3.self_attn.o_proj`: the one-row
  decode input was non-finite while the 32768-row prefill input, both split
  outputs and the prior layer-2 MLP MC2 boundary were finite. Evidence SHA256:
  805cd19839d1d4c2aa3692df9d023d700287122397088869409c9611aaacce0e.
  This rejects Dk80 cache/recurrent or fused-prefill adaptation for this
  anomaly and stops the mixed-MC2 diagnostic chain. It does not reject Dk80
  under another valid common path. An initial 0.1.16 diagnostic was invalid
  because a whole production tensor was promoted to FP32 and exhausted HBM;
  0.1.17 replaced it with bounded finite summaries. Commit 804d9b9 preserves
  the implementation. The exact service was stopped and physical NPU4-7 were
  clean afterward. Resume on the energy-Dk64 DRRQR mainline with the
  independently named plugin-owned native decode layout control described in
  NATIVE_DECODE_PROTOTYPE_SEAMS.md; do not resume mixed MC2 diagnosis.
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
   summaries, and the completed drrqr-recurrent-trajectory-selector-v1
   iteration YAML.
2. If the next task touches `chicaihong01`, use `chicaihong01-host-maintenance` before any remote or NPU action.
3. If the next task is another paper/practice result, start with `paper-to-ascend`; for historical reproduction or adoption claims, include `paper-to-ascend-reproduction` and its evidence contract.
4. Before using any claimed NPU/port lane, read the relevant target-host branch-local handoff and prove current ownership in the same session.
5. For Qwen3.5 work, identify the task ID before acting: paper selection and
   mechanism migration go to the Paper-to-Ascend workstream; cumulative
   `query_rewrite` serving optimization and final acceptance go to the
   performance workstream.

## 5. Next Actions

1. Re-enter the target host through AWMCP and refresh the canonical target repository state: `git fetch`, `git status --short --branch`, `git log -8 --decorate --oneline`, and `git worktree list --porcelain`.
2. For Qwen3.8 DRRQR, treat the completed and independently audited
   drrqr-rich-state-calibration-capture-v1 corpus as frozen selector input and
   the corrected recurrent-transition-selector-v2 and porp-cv-v1 results as
   rejections of bounded coordinate exchange and sparse subspace replacement.
   Do not tune nearby Q/K score or pairwise-projection variants. Predeclare a
   dense-prefill to aligned-Dk64-decode transition, including state/conv-cache
   conversion, scheduler and graph identity, and a dual-path weight strategy
   with a portable fallback.
   Do not implement the rejected mixed-Dk cache plan, broaden profiling, or run
   final accuracy before a replacement candidate passes its numerical gate and
   a fixed-1024-token endpoint screen.
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
.agents/evals/practice-iterations/drrqr-rich-state-calibration-capture-v1.yaml
.agents/evals/practice-iterations/drrqr-aligned-width-replay-v1.yaml
.agents/evals/practice-iterations/drrqr-full-layer-sensitivity-budget-v1.yaml
.agents/evals/practice-iterations/drrqr-recurrent-trajectory-selector-v1.yaml
.agents/evals/practice-iterations/drrqr-pairwise-orthogonal-projection-v1.yaml
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
