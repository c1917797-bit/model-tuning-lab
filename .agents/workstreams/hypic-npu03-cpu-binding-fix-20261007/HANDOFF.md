# HYPIC NPU0–3 — current handoff

## 0. Status

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
- Historical Decode gap before r6: r2/r4/r5 guards caught the external
  `Maxon4ick_vllm` on NPU0; r3 failed occupied-lane preflight. All roots
  are terminal, immutable, and documented in `task.json`; exact owned
  resources were released. The r5 stale attempt label was fixed before r6.
  A separate 30-minute clean idle monitor admitted r6. Do not touch
  external work.
- Updated 2026-10-09. Workstream: `work/hypic-npu03-cpu-binding-fix-20261007`; checkout: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`.
- Retry21 completed the missing HYPIC-only/repeat3 phase on physical NPU0-3.
  Independent replay verifies 40/40 fixed-output rows, 42 unique IDs, 40/40
  four-worker hot proof, 164 clean guard samples, source identity, and exact
  release. The frozen six-phase performance audit is now valid: median
  weighted TPOT 74.727578 -> 58.643006 ms (21.5243% faster), TTFT P95
  86.628571 -> 45.759196 s, throughput 1.298735x. See
  `HOTPATH_CACHE10PERF_RETRY21_AND_SIX_PHASE_TERMINAL_AUDIT_20261009.md`.
- Retry19 terminally failed before health/scoring: its continuous guard captured foreign PID 1731309 on physical NPU2 twice, with 46 total samples and zero probe errors. It produced zero scored requests; only retry19's exact owned service container was removed. The five receipts replay-pass `verify_retry19_environmental_failure.py`; see `HOTPATH_CACHE10PERF_RETRY19_TERMINAL_AUDIT_20261009.md`. This is environmental, not a HYPIC verdict.
- Retry20 for the HYPIC-only/repeat3 sixth phase terminally failed before health/scoring: guard captured foreign PID 1890601 on physical NPU3 (container `efc5e45e…`), with 36 samples and zero probe errors. It produced zero scored requests/metrics; only the exact owned service was removed. Replay audit: `HOTPATH_CACHE10PERF_RETRY20_TERMINAL_AUDIT_20261009.md`; verifier `verify_retry20_environmental_failure.py`. A 14:38 UTC follow-up still saw external PIDs 1890601 and 1920829 on NPU3; port 8223 was free. Keep monitoring, do not stop or modify the external task, and do not launch until a new direct-route snapshot proves physical NPU0–3 and 8223 idle.
- Paired LongBench-v2 explicit-boundary max-2048 quality is complete and valid: no-cache 230/381, HYPIC 219/381, delta -2.8871 percentage points (`REJECT_OR_QUALIFY`). Strict four-worker hot coverage is 368/381 and fails universal mechanism attribution. Read-only matched-hot repetition pairs show candidate answer variability exceeds baseline; see `HYPIC_R13_RESPONSE_VARIABILITY_DIAGNOSIS_20261009.md`. This is not causal proof or a reclassification.
- All six matched performance phases have an independent valid audit, and all
  120 candidate scored requests have four-worker hot-path proof. Retries15-20
  remain immutable environmental isolation failures, not HYPIC performance
  outcomes. Retry4's partial responses are contaminated and invalid; the original full single-service baseline and phase roots remain immutable.
- Main Skill inventory is 29: all 29 now have provenance-checked cases, with
  7 bounded verified and 22 partial. Five previously missing maintainer-system
  Skills passed an isolated real Python-repository transformation fixture.
  `ascend-cannbot-profiler` now has real Prefill and Decode captures but
  remains partial: the original numeric column gate missed, and no
  profiler-driven quality root cause or main integration is proven.
- The r6 profiler/Skill checkpoint was pushed and independently verified at
  `3b1b59e3c22b30a31c19c9fdb108cb786b60cc84`; do not claim main integration.

## 1. North Star

Finish the frozen HYPIC experiment without changing its technical question or acceptance rules, then map its evidence to the relevant Skills. Keep mechanism activation, deployed effect, quality, performance, isolation, and adoption as separate conclusions.

## 2. Current Focus

The frozen performance and quality comparisons are complete; quality remains
rejected. Four-rank Prefill/Decode profiler capture and parsing replay-pass,
including the retained first-parser failure. The read-only response-variability
replay narrows the next quality question but does not isolate cause. Preserve
the original Prefill numeric miss and the partial main-29 Skill inventory.

## 3. Recent Progress

- Retry21 and the six-phase audit replay-pass with
  `verify_hotpath_cache10_matched_performance.py`. Three-run median effects:
  weighted TPOT -16.084572 ms/token (-21.5243%), TTFT P95 -40.869375 s,
  throughput 1.298735x. Strict performance hot coverage is 120/120.
- r13 quality audit is immutable and independently valid for 127 samples × 3 repetitions per arm, 381 scored responses per arm.
- No-cache/screen, HYPIC/screen, HYPIC/repeat2, no-cache/repeat2, and no-cache/repeat3 have independent phase audits; see their audit paths in `task.json`.
- Retry14 guard recorded foreign `cannbench_ds` PID 242978 on physical NPU1 in 18 clean-probe samples. The service did not reach health and produced zero scored requests. Only the exact retry14-owned container was removed. Audit: `HOTPATH_CACHE10PERF_RETRY14_TERMINAL_AUDIT.md`.
- `verify_paper_to_ascend_reproduction_case.py` now verifies retry14 receipts and its four startup/capability events, without treating them as measured performance.
- The isolated repository-transformation suite replay-passes and adds bounded
  verified cases for `mst-agentsmd-authoring`, `mst-repo-transformation`,
  `mst-runtime-skill-boundary`, `mst-skill-governor`, and
  `mst-skill-tree-design`. The Cannbot boundary case re-proves current
  `/cache/cch` source locations; the later four-rank captures are separately audited.

## 4. Current Action

Do not launch another quality, matched-performance, Prefill, or Decode phase.
The r6 Decode root is terminal and immutable. Replay both profiler audits,
record the parser-environment lesson, and analyze the trace without treating
overlapping kernel sums as removable wall time. No CANN/HCCL root cause is
yet proven. NPU4-7 remain outside this task.

## 5. Next Actions

1. Run the focused HYPIC, six-phase performance, Prefill profiler, and
   case-registry replay checks.
2. Map the final performance success and quality rejection to the exact Skills;
   do not convert performance success into an unconditional deployment claim.
3. Replay the completed r6 Decode audit and add its success and first
   parser-environment failure to the `ascend-cannbot-profiler` case. Keep
   full Skill acceptance partial until the remaining attribution and
   integration gates are met. Upgrade the other partial cases only through
   their missing real behavioral gates; all 29 have provenance, not full
   acceptance.
4. Commit only a reviewed coherent checkpoint. Push only when authentication
   works and then verify the live remote ref.

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
