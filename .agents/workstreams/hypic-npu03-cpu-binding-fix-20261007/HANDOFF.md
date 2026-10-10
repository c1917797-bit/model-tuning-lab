# HYPIC NPU0–3 — current handoff

## 0. Status

- r18 original-source 2048/c32 LongBench no-cache controller `exec-00000000000001d1` is live on its immutable baseline root; poll that exact handle and never restart for slow progress. The ruler is frozen in `HYPIC_R18_C32_2048_PREREGISTRATION_20261010.json`; 127 offline regressions and fresh physical NPU0–3/8223 idle admission passed. As of 08:28 UTC, short Canary repeated identically, service reached health, and the first scored sentinel completed; the integrated c32 wave is in flight. Audit the baseline independently after terminal release before starting the HYPIC arm. GSM8K controller/auditor and phase preregistration are frozen at `c0117fc9`; both-arm no-device checks, 1319-sample dataset check, one-switch seam, and syntax validation passed. GSM8K has not run; LongBench alone cannot establish full Skill acceptance.
- r17 original-source cap-1024/c8 diagnostic is terminal and independently audited. Baseline 179/381 versus HYPIC 174/381 (−1.3123 pp); 377/381 aggregate hot, candidate controller exit 1 on the frozen coverage gate, but complete all-request quality evidence, clean physical NPU0–3 isolation, and exact owned release. The diagnostic quality decision is `REJECT_OR_QUALIFY`; this neither changes r16 nor establishes historical 1024/c32 or current 2048/c32 acceptance. See `HYPIC_R17_CAP1024_TERMINAL_AUDIT_20261010.md`; immutable audit SHA256 `493f9773d31a49e4f0b7e9c7ba73ea12e9722b4a7409e95c5ea05965b12853b3`. Do not rerun either r17 root. Next freeze original-source 2048/c32 explicit-segment paired LongBench-v2 and GSM8K; do not splice later-source speed or off-path clean2 quality.
- r16 original-source full 2048/c8 quality pair is terminal and
  independently audited on physical NPU0–3: 224/381 no-cache →
  210/381 HYPIC (−3.6745 pp), `REJECT_OR_QUALIFY`; aggregate hot
  364/381 is a separate activation shortfall. Both 127×3 arms have
  valid source/score/guard/release evidence. The candidate's exit 1
  is the preregistered hot-coverage failure, not incomplete rows.
  See `HYPIC_R16_ORIGINAL_SOURCE_FULL_TERMINAL_AUDIT_20261010.md`
  and `MODEL_QUALITY_R16_TERMINAL_SKILL_CASE_20261010.md`.
  Do not launch original-source adoption performance after this gate;
  do not pool r13/r15/r16 or rewrite historical 1024/c32 success.
- r15 source-lineage E2E is terminal, independently audited and exactly released. On eight post-hoc-selected samples, original `3ad0967` scored 13/24 and current `c12060c` 10/24; this was a source-sensitivity signal, not a population or causal verdict. The subsequent full r16 original-source pair above supersedes any inference drawn from that selected subset. See `HYPIC_R15_SOURCE_LINEAGE_TERMINAL_AUDIT_20261010.md`.
- The source-map checkpoint `a863fee7` is committed locally, but its
  2026-10-09 GitHub HTTPS push failed with unavailable Username credentials.
  Do not claim origin/main or the workstream remote contains this or later
  reporting work. Do not retry identical authentication until credentials
  actually change. The worktree's current `git log/status` is authoritative
  for subsequent local commits.
- Latest 2026-10-09 r6 Decode profiler capture is terminal and independently
  audited. Controller `exec-000000000000059e` completed 512 output tokens
  with 64 post-start chunks; 441 raw files hash-check, 85 isolation samples
  are clean, and exact owned resources were released. A clean offline copy
  parsed in the pinned image under `exec-00000000000005cb` using only the
  shared driver management node, no numbered NPU devices or network.
  `verify_hypic_profiler_decode.py` proves 83,223 real NPU compute kernels
  inside the capture window on each of four ranks, spanning about 1.81 s;
  see `HYPIC_PROFILER_DECODE_AUDIT_20261009.md`. The first offline copy
  failed CANN export without the management node despite parser exit 0;
  retain it as a failure lesson. This does not repair the original Prefill
  preregistered `>=47` column miss or the frozen HYPIC quality rejection.
- New profiler diagnostic deadline: 2026-10-10 04:42:44 UTC. The frozen
  HYPIC six-phase performance and r13 max-2048 paired quality are complete;
  they are not to be repeated. The quality decision remains
  `REJECT_OR_QUALIFY` despite the measured performance gain.
- `ascend-cannbot-profiler` now has a real four-rank Prefill capture on
  physical NPU0-3. Retry2 Prefill produced 281 nonempty raw files and 88
  clean guard samples; exact owned resources were released. The same pinned
  image parsed copies of all four ranks into valid trace, kernel, op, and API
  outputs. `verify_hypic_profiler_prefill.py` replays the raw and parsed
  evidence; see `HYPIC_PROFILER_PREFILL_AUDIT_20261009.md`.
- CANN 9.1.0 / torch_npu 2.10.0.post4 emitted 46 detailed
  `kernel_details.csv` columns on each rank, including Level1 and
  PipeUtilization fields. The preregistered `>=47` numeric gate missed and is
  recorded as a protocol deviation. The branch-local maintainer Skill now
  specifies a version-aware semantic-field gate for future cases; it is not
  yet main/remote truth.
- Updated 2026-10-09. Workstream: `work/hypic-npu03-cpu-binding-fix-20261007`; checkout: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`.
- Retry21 completed the missing HYPIC-only/repeat3 phase on physical NPU0-3.
  Independent replay verifies 40/40 fixed-output rows, 42 unique IDs, 40/40
  four-worker hot proof, 164 clean guard samples, source identity, and exact
  release. The frozen six-phase performance audit is now valid: median
  weighted TPOT 74.727578 -> 58.643006 ms (21.5243% faster), TTFT P95
  86.628571 -> 45.759196 s, throughput 1.298735x. See
  `HOTPATH_CACHE10PERF_RETRY21_AND_SIX_PHASE_TERMINAL_AUDIT_20261009.md`.
- Paired LongBench-v2 explicit-boundary max-2048 quality is complete and valid: no-cache 230/381, HYPIC 219/381, delta -2.8871 percentage points (`REJECT_OR_QUALIFY`). Strict four-worker hot coverage is 368/381 and fails universal mechanism attribution. Read-only matched-hot repetition pairs show candidate answer variability exceeds baseline; see `HYPIC_R13_RESPONSE_VARIABILITY_DIAGNOSIS_20261009.md`. This is not causal proof or a reclassification.

## 1. North Star

Finish the frozen HYPIC experiment without changing its technical question or acceptance rules, then map its evidence to the relevant Skills. Keep mechanism activation, deployed effect, quality, performance, isolation, and adoption as separate conclusions.

## 2. Current Focus

The frozen performance and quality comparisons are complete; quality remains
rejected. Four-rank Prefill/Decode profiler capture and parsing replay-pass,
including the retained first-parser failure. Read-only variability and strict-
mode replay rule out non-strict combined-Prefill, but do not isolate cause. Preserve
the original Prefill numeric miss and the partial main-29 Skill inventory.

## 3. Recent Progress

- Retry21 and the six-phase audit replay-pass with
  `verify_hotpath_cache10_matched_performance.py`. Three-run median effects:
  weighted TPOT -16.084572 ms/token (-21.5243%), TTFT P95 -40.869375 s,
  throughput 1.298735x. Strict performance hot coverage is 120/120.
- r13 quality audit is immutable and independently valid for 127 samples × 3 repetitions per arm, 381 scored responses per arm; retain the original full single-service baseline.
- No-cache/screen, HYPIC/screen, HYPIC/repeat2, no-cache/repeat2, and no-cache/repeat3 have independent phase audits; see their audit paths in `task.json`.
- Retry14 guard recorded foreign `cannbench_ds` PID 242978 on physical NPU1 in 18 clean-probe samples. The service did not reach health and produced zero scored requests. Only the exact retry14-owned container was removed. Audit: `HOTPATH_CACHE10PERF_RETRY14_TERMINAL_AUDIT.md`.
- `verify_paper_to_ascend_reproduction_case.py` now verifies retry14 receipts and its four startup/capability events, without treating them as measured performance.
- The isolated repository-transformation suite replay-passes and adds bounded
  verified cases for `mst-agentsmd-authoring`, `mst-repo-transformation`,
  `mst-runtime-skill-boundary`, `mst-skill-governor`, and
  `mst-skill-tree-design`. The Cannbot boundary case re-proves current
  `/cache/cch` source locations; the later four-rank captures are separately audited.

## 4. Current Action

Do not relaunch frozen r13–r17 quality, matched-performance, Prefill,
Decode or isolated GDN phases. r13 is positive performance and
negative quality under `c12060c`; r16 and r17 are negative quality
under original `3ad0967` at distinct 2048/c8 and 1024/c8 rulers. Keep
identities and decisions separate. Next freeze the missing original-source
2048/c32 explicit-segment LongBench-v2 and GSM8K pair; do not add a new
operator detour. No CANN/HCCL/GDN quality root cause is proven. NPU4–7
remain outside this task.

## 5. Next Actions

1. Validate and checkpoint the r17 terminal audit, exact raw hashes, focused
   regressions and full Maintainer Skill Tree validator.
2. Keep r13 positive performance and r13/r16 negative quality in separate
   source/ruler identities. Preserve the completed profiler and parser
   failure; do not use them to assign RoPE/GDN/cache causality.
3. Prospectively freeze a new 2048/c32 original-monkeypatch identity with
   explicit LongBench-v2 boundaries, matching GSM8K, deterministic canary,
   c32 capacity proof, full paired quality, uninterrupted isolation and exact
   release. Keep full Skill acceptance partial until those and same-source
   performance/integration gates are actually met; do not relaunch old roots.
4. Commit only a reviewed coherent checkpoint. Push only when authentication
   works and independently verify the live remote ref.

## 6. Validation Commands

From this branch worktree:

```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_paper_to_ascend_reproduction_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hotpath_cache10_matched_performance.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_mst_transformation_suite.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_ascend_cannbot_profiler_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_profiler_prefill.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_profiler_decode.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_profiler_retry5_failure.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_r14_variability_terminal.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_r16_original_source_full_terminal.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p 'test_*.py'
git diff --check
```

The live performance phase is complete; these commands replay its immutable
receipts and repository case mappings. See `HANDOFF_HISTORY.md` for older
checkpoints.

## 7. Do Not Do

- Do not reuse or overwrite any experiment root, pool rows across attempts, or change the frozen workload/acceptance criteria.
- Container mapping alone is not proof of NPU use; real physical PIDs are. Do not stop or modify foreign work.
- Do not use NPU4–7, claim HYPIC performance from environmental failures, or claim adoption despite the quality rejection.
- Do not make an unapproved retry, push, or main integration claim. Keep credentials, model weights, datasets, and raw profiles out of Git.

## 8. Recovery / Resume Commands

Read repository `AGENTS.md`, `.agents/HANDOFF.md`, the relevant maintainer Skills, this handoff, `task.json`, and `HANDOFF_HISTORY.md`. Resolve `chicaihong01/ma` and prove a direct AWMCP route in each session. Before any device action, freshly capture physical `npu-smi` process state and port 8223; never infer state from a container declaration or prior snapshot.

Use `task.json` for the active milestone, latest attempt, and exact next gate; use the immutable reports for raw evidence and hashes. After a reviewed checkpoint, push only to the named workstream branch if authorized authentication is available, then independently verify upstream equality.
