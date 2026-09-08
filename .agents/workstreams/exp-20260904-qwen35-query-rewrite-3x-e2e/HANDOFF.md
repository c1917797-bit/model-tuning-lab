# Qwen3.5-27B query_rewrite E2E Optimization

## Maintainer takeover snapshot

### 0. Status

- Workstream: `exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Branch-local state: active; not integrated. At 2026-09-08T13:59Z the
  external `vllm-ep-310p-research-910b-monitor` workload owned physical
  NPU0-3, so t12 correctly remained stopped at its resource gate.
- Latest pushed checkpoint is `5b8567b` on
  `pr/qwen35-mmar-async-finalize-gate`.
- The worktree still contains pre-existing modified benchmark/profile scripts
  and untracked historical handoff/config/prefetch files. They were not staged
  or altered by the takeover. Inspect ownership path by path; never use
  `git add -A` or treat a dirty worktree as disposable.
- Latest user stop gate supersedes the historical 1.5x/2x/3x labels: median
  of three per-run P95 values must show at least 40% lower TTFT and 20% lower
  TPOT at c1/c5/c8/c16 versus the frozen MTP-off baseline.
- Final delivery is BF16, no quantization, no retraining, no MTP/speculative
  decoding, and runtime Python monkeypatch only.

### 1. North Star

Deliver a reproducible Qwen3.5-27B Ascend 910B4 serving stack whose real
`query_rewrite.jsonl` TTFT and TPOT tails meet the current stop gate without
semantic-quality loss. This workstream owns the production performance claim;
Paper-to-Ascend may propose methods but does not own this denominator or its
acceptance decision.

### 2. Current Focus

Activate the attempted t12 source-overlay-free runtime monkeypatch for the
historically retained GDN qkvz/ba projection fusion plus gate/up prefetch 0.1.
First require four-worker activation, API readiness, an unchanged-image/mount
audit, and a fixed natural-EOS smoke. Then run c1/c16 fail-fast before the
full repeated matrix and 32-sample same-runtime semantic gate.

### 3. Recent Progress

- Frozen the first 32 records of `/cache/cch/query_rewrite.jsonl`, SHA256
  `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`.
- Locked c1/c5/c8/c16 x three repetitions, median per-run P95 decisions, P99
  tail guard, P50 secondary reporting, and a paired semantic-quality gate.
- Historical GDN projection fusion plus gate/up prefetch produced P95 speedups
  TTFT 2.206x/1.938x/1.930x/1.910x and TPOT
  1.381x/1.651x/1.753x/1.980x. It is useful hypothesis evidence but is not
  final because it used source overlays; c1 TPOT also misses the current 1.5x
  gate.
- Device-free monkeypatch activation, pass ordering, matrix contract, and
  decision-gate tests pass.

### 4. Current Action

The current AWMCP session proves direct host execution works. A first t12
launcher attempt exposed and fixed a generated-shell defect before Docker
creation. The corrected launcher then refused startup with exit 48 because
`vllm-ep-310p-research-910b-monitor` had appeared and started four
`VLLMWorker_TP` processes on physical NPU0-3 (PIDs 520084-520087, about
27.9 GiB process memory each). Do not stop or bypass this external owner.
NPU4-7 remain protected. Recheck the live resource state and resume only after
NPU0-3 and all container declarations are genuinely released.

The follow-up plan audit completed the environment-independent preparation.
Plain pip 26 editable install was intentionally tested offline and failed in
operation exec-0000000000000786 because build isolation tried to reach PyPI.
The maintained install_editable.sh instead disables index access and build
isolation; operation exec-0000000000000789 passed in the exact official image
with network=none and zero NPU devices. The reviewed offline suite
exec-00000000000007a1 passed projection-fusion, dual control/candidate
activation, independent 0.60 TTFT and 0.80 TPOT P95 thresholds, all-357-row
quality, prefix-cache isolation, exact-container stop, syntax, JSON/YAML, MST,
and diff checks. VALIDATION_PLAN.md is now the authoritative ordered plan.

The latest resource snapshot, exec-00000000000007a0 at
2026-09-08T14:40:29Z, still showed the same external NPU0-3 owner (PIDs
520084-520087), a protected NPU4-7 workload (PIDs 816932-816935), and only
36513068 kB MemAvailable. Do not allocate until these conditions clear.

### 5. Next Actions

1. Re-prove container, port, process, memory and physical NPU ownership
   immediately before allocation; use only NPU0-3 and an unclaimed port.
2. Wait for the external NPU0-3 owner to exit, then run the t12 runtime-only
   launcher under its full-lifetime cooperative lease; do not add vLLM or
   vLLM-Ascend source overlays and do not touch NPU4-7.
3. Require API readiness, all four TP worker activation markers, fused weight
   loading, a fixed-input natural-EOS smoke, and image/mount evidence.
4. Because the environment has materially drifted, collect a fresh
   same-environment MTP-off control as the primary denominator. Keep the
   immutable historical baseline only as a continuity reference.
5. Run a 32-row paired semantic canary, then c1/c16 fail-fast screens. Treat
   near-threshold/cold-tail results as inconclusive until enough repetitions
   resolve them; reject early only on a clear material miss.
6. On a passing screen, run control and candidate at c1/c5/c8/c16 x three
   repetitions. Use
   qwen35-performance-optimization/scripts/analyze_qwen35_current_targets.py:
   TTFT P95 ratio must be <=0.60 and TPOT P95 ratio <=0.80 in every cell.
7. Run the final paired quality capture over all 357 frozen rows. Byte-exact
   outputs pass automatically; review every difference and reject any material
   regression. The empty answer field limits the claim to paired no-regression
   on this workload.
8. Promote to the standalone PR only after all eight P95 gates, activation,
   provenance, full quality, and tail-risk review pass. Otherwise preserve the
   failure and recover to the retained safe stack.

### 6. Validation Commands

```text
./scripts/validate-mst.sh
python3 scripts/qwen35_ascend_monkeypatch/test_deferred_activation.py
python3 scripts/test_analyze_qwen35_candidate_vs_original.py
python3 -m py_compile scripts/run_qwen35_benchmark_matrix.py
bash -n scripts/run_qwen35_tp4_dev_service.sh
git diff --check
```

### 7. Do Not Do

- Do not confuse this workstream with
  `exp-20260904-qwen35-dense-mtp-paper-to-ascend`; that branch used a
  different c8 synthetic protocol and its MTP candidate is excluded here.
- Do not use MTP, speculative decoding, quantization, retraining, or vLLM
  source edits.
- Do not use source overlays as final E2E evidence.
- Do not stop or modify NPU4-7 workloads.
- Do not promote one-repeat, P50-only, transport-only, or unreviewed
  hash-drift evidence.
- Do not stage the entire dirty worktree; unrelated pre-existing paths remain.

### 8. Recovery / Resume Commands

```text
git status --short --branch
git log -8 --decorate --oneline
sed -n '1,180p' .agents/workstreams/exp-20260904-qwen35-query-rewrite-3x-e2e/HANDOFF.md
cat .agents/workstreams/exp-20260904-qwen35-query-rewrite-3x-e2e/task.json
docker inspect vllm-ep-310p-research-910b-monitor
npu-smi info
ss -lntp
./scripts/validate-mst.sh
git diff --check
```

The sections below are the preserved chronological experiment log. They are
history, not the current resume point.

## Current action — selective K4352 online-HCCL screen

The next bounded loop is planned, not yet measured. Modify the opt-in arch22
online-HCCL path so it can be restricted to M=1, K=4352 only. K=4352 had the
larger operator gain (1.045172x), while enabling both K families regressed
every E2E cell. First prove K=1536 stays on the frozen path and K=4352 remains
numerically correct and at least 1.02x faster. Only then run one c1 and one c16
query_rewrite screen against the retained stack; abort on any primary P95
regression. Do not allocate NPU4-7.

## Current checkpoint — 2026-09-07 online HCCL tiling E2E rejection

The retained GDN projection-fusion plus gate/up-prefetch stack remains the
best candidate. An opt-in arch22 MatmulAllReduce online-HCCL-tiling package
passed the exact-shape operator gate but failed the real query_rewrite E2E
gate and must not be stacked.

- Operator commit: 2e637229708f881f7ee9cbd81793363a86cb1f3b; package SHA256:
  ed801ca2403264823425859d208c575c9bb2de20799b59069fd97a29ff0d1bf9.
- Frozen-package versus online-package BF16 TP4 microbench on physical
  NPU0-3 improved M=1 K1536/N5120 from 84.03975 to 82.11010 us
  (1.023501x) and K4352/N5120 from 83.67610 to 80.05965 us
  (1.045172x). Complete fused outputs stayed within the frozen BF16
  error envelope.
- Microbench evidence:
  /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/tp4-npu03-mmar-m1-online-tiling-frozen-ab-v3-20260907T013000Z.
- Real E2E operation exec-00000000000001a4 completed 12/12 cells,
  384/384 requests, zero errors and all natural stops on physical NPU0-3.
  The custom op-api, tiling and proto libraries were present in all four TP
  worker process maps, proving runtime loading rather than an
  environment-only claim.

Median-of-three P95 speedups versus the immutable MTP-off baseline:

| Concurrency | TTFT P95 | TPOT P95 | Retained TTFT P95 | Retained TPOT P95 |
|---:|---:|---:|---:|---:|
| 1 | 2.118032x | 1.370730x | 2.205635x | 1.380880x |
| 5 | 1.913080x | 1.628058x | 1.938439x | 1.650948x |
| 8 | 1.792036x | 1.727894x | 1.930063x | 1.752699x |
| 16 | 1.738706x | 1.243401x | 1.909847x | 1.979821x |

Decision: rejected. Every cell misses at least one 2x gate and every cell is
worse than the retained candidate. The largest incremental regression is c16
TPOT P95: 69.56010 ms to 110.75796 ms. Cold first repetitions also showed
large TTFT/TPOT tails, so the operator-only M=1 gain did not survive
dynamic-shape scheduling and online-tiling lifecycle costs.

E2E evidence root:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-npu03-qwen35-gdn-proj-fusion-prefetch0p1-mmar-online-tiling-nospec-v1-20260907T014000Z.
Decision SHA256:
ecf600fd34402c5262f2cc81d7d095f25da7a452e79e92dda9450d84bcef0504.
SHA256SUMS SHA256:
a9672a6ca7a4c29973daf09ff1f3d0cf81680d48d3166508311b838100c986a2.

Recovery is complete: the rejected candidate container exited normally.
The unrelated mlpbig.service and recreated p0_w workload were stopped after
exact identity checks; NPU0-3 are free. This workstream did not start, stop,
or modify any NPU4-7 workload. Do not retry online HCCL tiling unchanged.
The next loop should first instrument tiling-cache hit/miss and HCCL lifecycle
costs for real M=1/5/8/16 decode shapes, then require a multi-shape operator
gate before another E2E matrix.

## Current checkpoint — 2026-09-07 A2 operator triage

The retained candidate and immutable MTP-off denominator remain unchanged.
Two new profile-guided screens were completed without claiming unmeasured E2E
performance:

- A real BF16 TP4 NPU0-3 microbenchmark tested `HCCL_BUFFSIZE` 64, 128,
  256 and the retained 512 on the two exact Qwen3.5 decode MMAR shapes.
  None of 64/128/256 improved both shapes by the predefined 1.02x gate, so
  they were rejected before E2E and 512 remains retained.
- A materially different sequence-parallel probe disabled opaque MMAR before
  enabling the compiler pass. The compiled graph contained 832 ordinary
  `all_reduce` occurrences but zero `reduce_scatter` and zero
  `all_gather`; activation therefore failed and the candidate was rejected
  before a latency matrix.
- Activation evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/activation-probes/tp4-npu03-gdn-proj-sp-mmaroff-v1-20260907T000000Z`.
  The graph SHA256 is
  `cbc36a6bd1aa4cf89ed872e5fe12b981502841f3520388e006880cf6ffbf4d68`.
- The failed candidate was stopped by exact name. The retained stack was
  relaunched as `qwen35_gdn_proj_fusion_npu03_v3` on port 10012 and
  physical NPU0-3; wait for HTTP readiness before using it. NPU4-7 were not
  modified.

Operator direction is recorded in `A3_TO_A2_OPERATOR_BACKLOG.md`. The only
A3-only operator with a direct dense-model analogue is `FFN`, but using it
requires a new A2 BF16 gated-SwiGLU implementation and remains unverified.
The highest-value near-term task is still the existing A2/910B4
`MatmulAllReduce` path, because the retained profile attributes 64.9357% of
summed kernel duration to collectives and 48.1818% to its AICPU kernel.

## Current checkpoint — 2026-09-06 decode-only ShortGPT screen

The decode-only eight-layer skip candidate is rejected by an early real
Ascend 910B4 performance screen. This is a valid performance failure, not a
request failure: c1 and c16 each completed 32/32 requests with zero errors and
all natural stops. The comparison is same-repetition against the retained
GDN-projection-fusion plus gate/up-prefetch stack; it is deliberately a
one-repeat screen rather than a formal median-of-three A/B.

| Concurrency | Candidate TTFT P95 | Retained TTFT P95 | Candidate TPOT P95 | Retained TPOT P95 |
|---:|---:|---:|---:|---:|
| 1 | 11733.070 ms | 6298.129 ms | 36.747 ms | 28.312 ms |
| 16 | 18098.233 ms | 6796.297 ms | 160.800 ms | 67.777 ms |

At c1 the candidate regresses TTFT P95 by 86.29% and TPOT P95 by 29.79%.
At c16 it regresses TTFT P95 by 166.30% and TPOT P95 by 137.25%.
Do not expand this implementation to c5/c8 or three repetitions, and do not
repeat it unchanged. The prior 16-sample paired semantic review found no
material loss, but that bounded quality result cannot override the performance
rejection.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-decode-shortgpt8-nospec-screen-v1-20260906T200500Z`.
Decision SHA256:
`cee506499a940ec8c9e6cb17695888e10f9a4b4f54e7e8b686d8adccedfd363b`.
Manifest SHA256:
`cff09fdc93d0c5eaf00a3a8564d8099a55ce31836a9fd0aa420893fbe3d069cc`.
All manifest entries verify.

The candidate container is
`qwen35_decode_shortgpt8_npu03_v1` with exact ID
`b94b2b5a16b75cbb7c40e6511aa44b757e7dcc27ef43db4afe62d1b88cabadd1`
on physical NPU0-3. Before replacing it, stop only this guarded ID. The next
candidate should return to the retained stack and target the existing
ASCEND910B BF16 `MatmulAllReduce` path: the real profile attributes 64.9357%
of summed kernel duration to collectives and about 128 row-parallel MMAR calls
per decode step. Presence of the layer-skip environment and mounted source is
not runtime activation proof; any future algorithmic revisit must add direct
skip-branch activation evidence before allocating a full matrix.

## Hard gate — real-data-only reporting

All reported measurements and conclusions in this workstream must be
traceable to real execution output, inspected source, or an immutable evidence
artifact. Never fabricate, interpolate, extrapolate, or silently substitute a
missing value.

- Performance claims require the raw benchmark artifact, the exact baseline
  artifact, the comparison protocol, and a verified SHA256.
- Correctness claims require captured outputs or a named deterministic check.
  A missing or empty reference field is not positive correctness evidence.
- Profiling claims require the profiler export and its hash; summed kernel time
  must not be relabeled as wall-clock latency.
- Source-only hypotheses and operator documentation are labeled
  `unverified` until a real Ascend 910B4 run produces evidence.
- Failed, partial, contaminated, or non-comparable runs remain recorded as
  invalid/rejected evidence and must not contribute performance numbers.
- If the evidence cannot be recovered or independently verified, report
  `unknown` or `not measured`; do not infer a number.

The currently retained performance matrix and paired quality gate already
follow this rule; their evidence roots and SHA256 values are recorded below
and in `QUALITY_GATE_V1.md`.

## Current checkpoint — 2026-09-06 MMAR x3 residual probe

The retained candidate and frozen denominator are unchanged. The latest
profile-guided treatment was screened at operator level and rejected before
E2E:

- `torch_npu.npu_mm_all_reduce_base` exposes `x3`, but `x3` participates in
  the cross-rank reduction. Passing Qwen3.5's replicated residual directly
  therefore adds it once per TP rank and is numerically wrong.
- The semantics-preserving TP4 form contributes `residual / 4` on every rank
  and then runs standalone RMSNorm. A real BF16 910B4 microbenchmark on
  physical NPU0-3 passed correctness for all Qwen3.5 decode cells
  M=1/5/8/16 and K=1536/4352, N=5120.
- Despite correctness, the viable sequence reached only 0.655224x geometric
  mean speed versus `MMAR + AddRMSNorm`; its worst cell was 0.635134x.
  Decision: `reject-x3-residual-before-e2e`.
- Evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/mmar-x3-residual-npu03-v2/report.json`,
  SHA256
  `92b42c33c4449ee5f788b93e8337f8bd9becbe6a44e993140acabf8d2b673224`.
- The first orchestration attempt (operation `exec-000000000000064a`)
  stopped before timing because its HCCL socket port overlapped the live
  service. It is invalid evidence. The isolated-port rerun is operation
  `exec-000000000000064c`.
- Service `qwen35_gdn_proj_fusion_npu03_v1` remains healthy on port 10012.
  NPU0-3 contain only this task's four TP workers; NPU4-7 retain the external
  workload and were not modified.

Do not integrate or retry x3 residual fusion unchanged. Resume from the
retained GDN projection fusion candidate and select a mechanism that reduces
or overlaps the approximately 128 decode MMAR calls rather than adding a
per-layer residual scaling kernel. The primary P95 gaps remain unchanged.

## Previous checkpoint — 2026-09-06 GDN projection fusion

This checkpoint supersedes stale resource and resume statements below.

- Goal remains open: primary TTFT P95 and TPOT P95 must both improve by 2x
  at c1/c5/c8/c16 on the frozen query_rewrite workload, and semantic quality
  must satisfy `精读无损`. P50 is secondary and P99 is a risk guard.
  Quantization, retraining, and every form of speculative decoding are
  prohibited.
- Immutable denominator:
  `baselines/tp4dp1-npu03-ref-v1`, summary SHA256
  `cef6713367f387fd67c15c2cc0bdf071c33f58846b8ef9a041a489186aa0d9d4`.
- Active Ascend-only treatment: fuse Qwen3.5 GDN `qkvz` and `ba` input
  projections while retaining BF16 TP4/DP1, MMAR, NZ1, dense gate/up
  prefetch 0.1, async scheduling, FULL_DECODE_ONLY, and
  `speculative_config=None`.
- vLLM source worktree
  `/cache/cch/.worktrees/exp-20260906-qwen35-gdn-projection-fusion`
  is clean at `685fdf22098fb3a0aa8d582dda57063773606a02`.
  vLLM-Ascend adapter worktree
  `/cache/cch/.worktrees/exp-20260906-qwen35-gdn-projection-fusion-ascend`
  is clean at `d98e37ebb72acd71b5a35222fd7ab7f8049d41cb`.
- The first service attempt failed before readiness because
  `vllm_ascend/ops/gdn.py` still accessed the removed
  `in_proj_qkvz` attribute. The adapter commit above consumes
  `in_proj_qkvzba` and reconstructs the existing Ascend qkvz/ba contract.
  Do not run the vLLM patch without this adapter.
- Real 910B4 operator microbench on physical NPU0 measured 3.046x-3.085x
  median projection speedup at M=1/5/8/16, max BF16 absolute error
  `2.44140625e-4`. Evidence:
  `operator-microbench/gdn-projection-fusion-npu0-v1/report.json`, SHA256
  `fd66a8bef633ecfce6560ed5e6f96632573384596698f177b839101ee099c3f7`.
  This is operator evidence only.
- Service `qwen35_gdn_proj_fusion_npu03_v1` is live on port 10012 and
  physical NPU0-3. Its engine log proves vLLM-Ascend 0.23.0,
  `device_config=npu`, BF16, TP4/DP1, `quantization=None`, and
  `speculative_config=None`. NPU4-7 carry the external
  `qwen36_hypic_only_npu4_7_tp4_b40960` workload and must not be modified.
- All r1/r2/r3 repetitions completed: 384/384 requests, zero errors, all
  natural stops. Operation `exec-0000000000000425` ended successfully.
  Using the required median of the three per-run P95 values, TTFT P95
  speedup is 2.206x/1.938x/1.930x/1.910x and TPOT P95 speedup is
  1.381x/1.651x/1.753x/1.980x at c1/c5/c8/c16. The candidate therefore
  fails the primary all-cell 2x gate. P50 is secondary and cannot override
  this P95 decision.
- Machine-readable decision `decision.json` SHA256 is
  `69cec251d2b63648c2804452d914f121ff6994087e34957e90f28800ccaa4570`;
  final manifest SHA256 is
  `1ecd8a648622d8d9810664effdcd30044ad56f570495af97db3af83207401caa`.
  Evidence root:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-npu03-qwen35-gdn-proj-fusion-prefetch0p1-nospec-v1-20260906T161500Z`.
- A foreign `/cache/austinov/p0/watch03.sh` supervisor reappeared with
  PPID 1 during r1. It had not created a second NPU0-3 process and the live
  device table contained only the intended four TP workers. It was verified
  by exact cmdline and stopped. Remaining cells have a conflict guard; exit
  46 means preserve partial evidence and re-orient.

Resume from the `iterate-performance` decision. Keep the live service only
for the paired deterministic semantic gate or a directly stacked successor;
otherwise stop only the exact candidate container and verify NPU0-3 release.
The next hypothesis must primarily improve decode/TPOT P95 while preserving
the TTFT gains. Do not push unless the user explicitly requests it.

Current approved protocol: see `LOOP.md`. It supersedes historical TP4-only
instructions below. Both TP8 baseline groups are complete; see
`BASELINE_COMPARISON.md`. Operation `exec-0000000000000474` completed all
12 cells and 384/384 requests, then failed only in postprocessing because its
executing script was edited in place. Postprocessing was recovered manually.
Never edit a script while its process is executing.

## State

Authoritative current handoff: see `LESSONS.md` and `LOOP.md`. MTP OFF v5
remains the immutable denominator. MTP ON local-argmax k1 v3 completed 12/12
cells with zero errors and natural stops. It regressed TTFT at every concurrency
and its TPOT result was mixed, so k1 is rejected for performance. The next
bounded treatment is k1 -> k3. Recheck NPU0-7 before launch.

- Execution: `v11-diagnostics-queued-behind-protected-p0-r16`;
  integration: `shortgpt-remove8-held-semantic-regression`.
- Current resource state supersedes older idle snapshots below: the protected
  `p0_r15` chain ended after its FlashComm2 configuration failed both guarded
  startup attempts and wrote `R15_DONE` at 2026-09-05T13:49:39Z. Queue
  operation `exec-00000000000000f7` then passed its four-observation idle
  gate and launched exactly one v10 container on assigned physical NPU4-7 at
  13:50:44Z. Its positive activation gate later rejected the run with exit 72
  before query traffic. ShortGPT BI and its same-runtime control later passed,
  but remove8 failed the semantic gate. A single v11 diagnostics queue now
  waits for protected `p0_r16` to write `R16_DONE`; NPU0-3 remain out of
  scope. Do not start a duplicate queue or relaunch v10 unchanged.
- Branch: `work/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Worktree: `/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- The user assigned physical NPU4-7 to this task. The old
  `qwen38_gdn_fused_candidate` service was idle but used a
  non-comparable 41,984/16,384/no-prefix-cache protocol; it was retained for
  audit and stopped. Use NPU4-7 for current candidates.
- `scripts/run_qwen35_tp4_dev_service.sh` now refuses to start if
  `npu-smi` reports any process on NPU0-3 (exit 42), and profile mode refuses
  to reuse an existing output directory (exit 44). Mock-only tests prove both
  failures occur before `docker run`; never bypass these guards.
- The attempted workstream profile container
  `qwen35_query_rewrite_tp4_dev_profile` exited before serving when Triton
  Ascend `get_arch()` returned NULL during Qwen3.5 architecture inspection.
  The failed container is retained; its readiness observer was terminated and
  no workstream process remains on NPU0-3. This is a resource-ownership race,
  not valid profile evidence.
- Physical NPU0-3 are not required for the current loop.
- No baseline rerun is pending. The user designated the existing TP4
  `quick32-v3` artifacts as the immutable original denominator. Future
  runs use exclusive physical NPU4-7 for one candidate.
- FlashComm1 was really launched on physical NPU4-7 as run
  `flashcomm1-fixedorig-npu4-7-20260904T1816Z`. The v0.23.0 runtime proved
  both FlashComm1 and MatMulAllReduce active, then all four TP workers failed
  before readiness: the Qwen3.5 GDN graph attempted to place symbolic length
  `s59` into a sequence-parallel `ceil(s59/4)` buffer. No benchmark cell
  ran. Treat this as a runtime-compatibility failure, exclude FlashComm1 from
  the cumulative stack, and do not retry it unchanged.
- Immutable failure evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/flashcomm1-fixedorig-npu4-7-20260904T1816Z/service.log`
  (SHA256
  `35ef543dd9ab29d127ce01b2556b6abf8b0a46e9068320f7a97d4e69cf59e692`).
  The exact container was stopped; NPU4-7 remain the assigned candidate set.
- BF16 `weight_nz_mode=2` was then really launched alone on NPU4-7 as run
  `bf16-nz-fixedorig-npu4-7-20260904T1838Z`. All four workers proved NZ and
  MatMulAllReduce active and loaded 12.8785 GB of weights each, but
  `aclnnMatmulAllReduce` rejected its `x2` input because it was
  `FRACTAL_NZ` instead of the required `ND` format. No benchmark cell ran.
- BF16 NZ failure evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/bf16-nz-fixedorig-npu4-7-20260904T1838Z/service.log`
  (SHA256
  `0756f2a7770166afa54d4e4ff08178be13d6b81287a28fa861ec9e1b3ddf82b9`).
  The exact container was stopped. The next bounded recovery is NZ with
  MatMulAllReduce disabled, matching that setting in the fixed original.
- The NZ recovery run completed all four real cells with 32/32 requests, zero
  errors and natural stops. It improved TTFT by 2.03x/2.00x/1.97x at
  concurrency 1/5/8, but concurrency-16 TTFT regressed to 0.58x. TPOT improved
  only 1.33x-1.54x. Exact response hashes differed for 19/18/15/18 requests,
  so the analyzer returned `reject-correctness` and the treatment is excluded
  from the stack.
- NZ recovery decision:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/bf16-nz-mmar-off-fixedorig-npu4-7-20260904T1845Z/decision.json`
  (SHA256
  `323ee9620294fba17bfd678e30bab5012512e211c9016303e9c8ef0ddb2b791a`).
  The service log SHA256 is
  `bc6bb41f630cdaa2c2d44496e43ce591586d53566cb974d0066d379f08cfd438`.
- MatMulAllReduce enabled alone completed all four real NPU4-7 cells as run
  `mmar-on-fixedorig-npu4-7-20260904T1921Z`. Every cell completed 32/32
  requests with zero transport errors and natural stops. Against the immutable
  original, TTFT p50 improved 2.14x/2.11x/2.17x/2.25x at concurrency
  1/5/8/16, but TPOT p50 improved only 1.34x/1.38x/1.49x/1.55x. Exact response
  hashes differed for 17/20/17/15 requests, so the authoritative decision is
  `reject-correctness`; do not add MMAR to the cumulative stack.
- MMAR decision evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-on-fixedorig-npu4-7-20260904T1921Z/decision.json`
  (SHA256
  `870c8f04911b838670d4e0414b3846d14fa7cb2cb0774b15230a573f681ecc0b`).
  The service log SHA256 is
  `8ddc953a33dd994646d7214336a5a0a9b7d752d7fffc8e1b98f38120e1e610c0`.
  The exact candidate container self-cleaned; NPU4-7 have no running process,
  while the pre-existing NPU0-3 VLLM workers remained untouched.
- Because a nominally semantics-preserving MMAR switch still changed exact
  hashes and showed a large TTFT p50 shift, the next attribution step is a
  no-op BF16 control candidate on NPU4-7 matching the fixed original runtime
  switches (MMAR off, NZ mode 1, FlashComm1 off). It does not replace or
  relabel the immutable original; it calibrates run/device drift before the
  next operator or algorithm candidate is credited.
- The control is implemented as launcher mode `control-mmar-off` with
  `configs/qwen35-query-rewrite-control-mmar-off-candidate.yaml`. It keeps
  BF16, MMAR off, NZ mode 1, FlashComm1 off, TP4 and the frozen request
  protocol. It is an attribution control only: the fixed quick32-v3 artifacts
  remain the sole performance denominator and are not rerun or relabeled.
- The control completed as
  `control-mmar-off-fixedorig-npu4-7-20260904T1943Z` under AWMCP operation
  `exec-000000000000063b`. It reproduced the original runtime switches and
  completed every cell 32/32 with zero errors and natural stops. Its TTFT p50
  was 449.81/530.76/542.48/5903.78 ms and TPOT p50 was
  28.76/39.02/46.39/55.03 ms at concurrency 1/5/8/16.
- The control itself differed from the immutable original in 15/15/19/16
  response hashes. Therefore cross-run exact-hash equality is not a calibrated
  semantic correctness gate for this workload. Keep it as a reproducibility
  diagnostic and fail closed until aggregate reference-quality metrics pass.
  Future benchmark artifacts now add privacy-safe raw/whitespace-normalized
  exact-answer counts and normalized character-similarity summaries; they
  never store question, answer or response text.
- Relative to the same-device control, MMAR changed TTFT by
  1.04x/1.02x/1.09x/6.41x and TPOT by
  1.004x/1.000x/1.019x/1.053x. The c16 TTFT signal is large but comes from a
  single highly variable control cell; repeat/profile it before credit. MMAR
  remains outside the accepted stack because its net TPOT gain is at most
  5.3% and semantic correctness has not passed.
- Control evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/control-mmar-off-fixedorig-npu4-7-20260904T1943Z/decision.json`
  (SHA256
  `ff77a6fc8aadbf6d0561834b9f42a12a562cee76f5da4c4a6f9ae68eaf803b39`).
  The service log SHA256 is
  `6d3b7a82b31be3ab55d10107e68cd14c064bb2fdef90afe1567534692987c0bc`.
  NPU4-7 were released; NPU0-3 workers remained untouched.
- Fixed-runtime profiling is implemented as service mode
  `profile-mmar-off`; `capture_qwen35_tp4_profile.sh` selects it by default.
  It preserves MMAR off/NZ1/FlashComm1 off, disables async scheduling only for
  the profiler lifecycle, uses NPU4-7, and still enforces new output paths and
  the device idle guard.

## Authoritative comparison and stacking policy

This section supersedes later historical text that asks for a paired baseline,
three repetitions, all eight NPUs, or a new canonical baseline.

- Original: `tp4-dev-decodegraph/quick32-v3`, first 32 frozen records,
  one repetition, concurrency 1/5/8/16, seed 1024, natural EOS.
- The four original file hashes are embedded in
  `scripts/analyze_qwen35_candidate_vs_original.py`. A hash mismatch
  invalidates the run.
- Run only the candidate with
  `scripts/run_qwen35_tp4_candidate_vs_original.sh`. It starts one
  exact TP4 container on physical NPU4-7, runs four candidate cells, records the
  container/log/config hashes, stops only that container, then compares with
  the stored original.
- Correctness remains fail-closed: 32/32 completed, zero errors, natural stop,
  and exact per-request response hashes. Analyzer exit status is 0 for the 2x
  target, 2 for continue iterating, and 3 for correctness rejection.
- A treatment is isolated for attribution, then accepted treatments are added
  to the current best stack. Every single treatment and cumulative stack uses
  the same original denominator. The first supported cumulative mode is
  `flashcomm1-bf16-nz`; it combines two BF16 paths and is not
  quantization.
- Preserve the known caveat: quick32-v3 forced
  `enable_matmul_allreduce=false`. The user accepted it as the common
  denominator, so report the caveat but do not relaunch or relabel it.

## TP4 development evidence

- The user-supplied FULL_AND_PIECEWISE configuration with matmul-allreduce
  enabled failed during graph capture in `aclnnMatmulAllReduce`. The immutable
  startup log is
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/startup/original-config-matmul-allreduce-failure.log`
  (SHA256
  `fbe6f414bf5c5ced6295298bfe37e484e5e7f7efef4e94101ace599b4758fcb0`).
- Disabling matmul-allreduce removed that failure, but FULL_AND_PIECEWISE still
  failed with `EE1023 Too many streams are created`. Evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/startup/matmul-allreduce-off-full-piecewise-stream-exhaustion.log`
  (SHA256
  `3d6091716a0d3356a79caba742e048cd2972ae4ba4d75e89da0a9297eb6213d9`).
- The next attributable treatment, FULL_DECODE_ONLY with
  matmul-allreduce disabled, started successfully. Decode graph capture covered
  request counts 1, 2, 4, 6, 8, 10, 12, 14 and 16 in 20 seconds and consumed
  0.42 GiB graph memory. The service has 10.84 GiB KV cache per card and reports
  maximum 5.03 concurrent 133K-token requests.
- A real one-record raw/natural-EOS smoke completed 1/1 with zero errors:
  TTFT 1085.71 ms, TPOT 41.68 ms, E2E 5378.28 ms, 104 completion tokens.
  Artifact:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-dev-decodegraph/smoke-c1-r1.json`
  (SHA256
  `f2f959768f28b57d41e394b3be9379e3ef8e6cc65ebc9efea8d9650e0c2ae087`).
- The first 32-record run terminated at concurrency 1: 28/32 completed and four
  requests raised `RuntimeError`; it did not proceed to 5/8/16. The invalid
  artifact is
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-dev-decodegraph/quick32/c1-r1.json`
  (SHA256
  `a78b13517fe735f44f82f904fe4832e9a9371ad5dad1350f41c66fe8e1193768`).
  Do not use its latency values as a baseline.
- Diagnosis found that the harness recorded seed 1024 but omitted it from the
  request payload, and reduced all internal stream validation failures to only
  their exception type. The harness now sends the seed and emits only
  privacy-safe error-reason counts and failed-question SHA256 values.
- A concurrency-1 diagnostic rerun is active as AgentWeb operation
  `exec-0000000000000350`, writing to the new immutable
  `tp4-dev-decodegraph/quick32-v2/c1-r1.json` path.
- That rerun reproduced the same four cases and classified all of them as
  `stream completed without content`. A targeted privacy-safe SSE probe then
  proved each was a valid EOS-only completion: one choice event,
  `completion_tokens=1`, `finish_reason=stop`, zero visible characters and
  no HTTP/service error. The harness now defines TTFT at the first choice/token
  event, including EOS, rather than the first non-empty text fragment.
- The corrected quick32-v3 scaling run completed all four cells with 32/32
  natural-stop responses and zero errors:

  | concurrency | TTFT p50 | TPOT p50 | artifact SHA256 |
  |---:|---:|---:|---|
  | 1 | 928.33 ms | 38.47 ms | `ac39bc922b43d9472fe41f89bae25a0190cf20817147230f8725f151e3ce413a` |
  | 5 | 1092.27 ms | 53.83 ms | `68d2a3020bb52594e13560dd608afca1d611d61a37383aa94062bfe78784f7ae` |
  | 8 | 1082.31 ms | 67.62 ms | `4f9799a128128b1e34dca498256833c45f52373cd2486b4acd9298030d7d58ce` |
  | 16 | 2075.07 ms | 80.81 ms | `085c0a43a7a720ba42f1d83bf2ebacebb64e515d24bb3f040eabd5c046f777e4` |

  These are the user-designated immutable original baseline.
- The MTP candidate uses the same TP4 command plus only
  `{"method":"mtp","num_speculative_tokens":1}`. Readiness is tracked by
  AgentWeb operation `exec-0000000000000370`.

- MTP quick32-v1 completed under AgentWeb operation
  `exec-000000000000037d` in 762.12 s. Every cell completed 32/32 with zero
  transport errors and natural `stop`, but exact output hashes diverged.

  | concurrency | TTFT baseline -> MTP | speedup | TPOT baseline -> MTP | speedup | mismatches | artifact SHA256 |
  |---:|---:|---:|---:|---:|---:|---|
  | 1 | 928.33 -> 1166.99 ms | 0.795x | 38.47 -> 41.92 ms | 0.918x | 16/32 | `b57d8aa8346b8cebc1ce7c58163f0d25d8eab834091f2a1ede48fffccf8e6568` |
  | 5 | 1092.27 -> 1389.05 ms | 0.786x | 53.83 -> 62.28 ms | 0.864x | 20/32 | `1fd71a7d6bd5aa5a5629383d6528ea584cfa3be32760fa398fca01d493ef8337` |
  | 8 | 1082.31 -> 1408.59 ms | 0.768x | 67.62 -> 72.41 ms | 0.934x | 21/32 | `59bd1765d13ab5137fc4b7c4c83635788fb606271daecd6737b302ddf1e2d61a` |
  | 16 | 2075.07 -> 10619.90 ms | 0.195x | 80.81 -> 109.76 ms | 0.736x | 18/32 | `67bcd90ad027b21b8fdbc25bdddfb21c3b4f86256ad4d24902cb7052dbcc7035` |

  Decision: **reject MTP from the cumulative stack**. It fails correctness and
  regresses TTFT and TPOT at every measured concurrency.
- Source inspection proved `VLLM_ASCEND_PTO_CHUNK_GDN=1` has no reader in the
  installed vLLM/vLLM-Ascend source and is an inert legacy variable.
  Qwen3.5 actually binds to `AscendGatedDeltaNetAttention._forward_core`;
  decode uses the AscendC recurrent GDN op and prefill uses mixed chunk GDN.
- Torch/NPU profiling requires `--profiler-config.profiler=torch` and
  `--profiler-config.torch_profiler_dir=<dir>`. No comparable profile exists
  yet for this workload.

## Provisional algorithm and operator candidates

The first treatment after freezing the current development baseline is native
Qwen3.5 MTP speculative decoding. The frozen model is not merely compatible in
name: 'text_config.mtp_num_hidden_layers=1', and its weight index contains 15
MTP tensors covering 'mtp.fc', 'mtp.layers.0', 'mtp.norm' and the MTP embedding
norms. The installed vLLM 0.23.0 'SpeculativeConfig' explicitly declares the
'qwen3_5_mtp' method. Start with one speculative token, matching the single
model-provided MTP layer. Accept it only with exact response-hash equality,
zero errors, measured acceptance evidence and a paired decode profile. This is
the primary TPOT candidate because a one-layer MTP path can remove target-model
decode steps; the claim remains unproven until E2E A/B.

The next cumulative treatment is the fused GDN prefill path from vLLM-Ascend
upstream commit '77d13e2c0bfa9862b711b68811889e36b9d56aca'. It replaces the multi-kernel
chunk gated delta-rule prefill pipeline with
'torch_npu.npu_chunk_gated_delta_rule'. Reuse the audited patch from the
adjacent GDN workstream, but remeasure under this workstream's 133K,
prefix-cache-enabled protocol; its historical 41984/no-prefix-cache numbers
are not comparable. The current torch_npu package exposes the fused symbol, but
runtime applicability and correctness on 910B4 still require an isolated probe.

## Frozen inputs

- Model: `/cache/austinov/Qwen3.8-27B`; actual architecture
  `Qwen3_5ForConditionalGeneration`; all 18 indexed weight shards are present.
- Model config SHA256:
  `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`.
- Tokenizer config SHA256:
  `b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27`.
- Weight index SHA256:
  `77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df`.
- Dataset: `/cache/cch/query_rewrite.jsonl`, 357 records, 3,305,726 bytes.
- Dataset SHA256:
  `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`.
- Dataset records expose `question` and `answer`; never place raw content in Git or logs.

## Measurement target

Measure the first 32 records at concurrency 1, 5, 8 and 16, using three
repetitions per cell and the median of the three per-run P95 values for the
final decision. The current stop target is TTFT and TPOT each improved by at
least 50% versus the frozen MTP-off original baseline at every concurrency
(speedup >= 1.5x, candidate/baseline ratio <= 2/3), with zero request errors,
passing business correctness, and no unacceptable P99 regression. P95 is
primary; P99 is the tail guard and P50 is secondary.

The workstream identifier retains the original `3x` label for audit
continuity. The historical 2x target remains in older result narratives only;
the authoritative stop target was revised to 1.5x on 2026-09-07.

## Optimization loop

1. Acquire explicit exclusive ownership of the user-assigned physical NPU4-7.
2. Freeze request rendering, output policy, seed and service/runtime identity.
3. Verify, but do not rerun, the hash-locked original quick32-v3 artifacts.
4. Profile Prefill, Decode, GDN, MatMul/AllReduce, Attention, scheduling,
   graph coverage, layout conversion and host synchronization.
5. Add one attributable treatment to the latest accepted stack: operator,
   algorithm, or parameter.
6. Verify reference, microbenchmark, vLLM-Ascend integration, model
   correctness and query_rewrite E2E behavior.
7. Compare the treatment or cumulative stack against the immutable original.
   Use the retained single-treatment/ablation history to explain attribution.
8. Preserve accepted, rejected, failed and inconclusive results.
9. Add each accepted treatment to the current best stack and repeat until both
   TTFT and TPOT reach at least 1.5x at all four concurrencies.

The privacy-preserving streaming harness is
`scripts/qwen35_query_rewrite_bench.py`. One invocation measures one
concurrency/repetition cell, verifies the frozen dataset hash, and emits
TTFT/TPOT/E2E/throughput plus response hashes without recording prompts or
response text. It follows the maintainer-approved historical protocol: raw
`question` strings, temperature 0, natural EOS, and per-request
`max_tokens = max_model_len - real_prompt_tokens` resolved through
`/tokenize` before the measured window. Fixed-40 and normalized-2K protocols
are superseded and must not be mixed with this baseline.

`scripts/render_qwen35_runtime.py` validates the frozen final baseline
contract and renders a canonical argv/environment manifest. It fail-closes
unless topology is DP2/TP4 on NPU0-7, the benchmark grid is 1/5/8/16 × three
repetitions, request semantics remain raw-question/natural-EOS, and both
acceptance ratios remain 0.5. The manifest hashes both source YAML and
normalized runtime payload, preventing command drift when all eight NPUs
become available.

`scripts/run_qwen35_benchmark_matrix.py` executes the complete frozen
1/5/8/16 × three-repetition matrix against one already healthy service. It
checks the dataset hash before creating output, refuses an existing run
directory, validates every cell's model/data/concurrency/repetition identity,
requires zero errors, a complete request/hash set and natural stop for every
request, and checkpoints an atomic run manifest after each cell. A failed run
is retained with its exact failed cell and exception type; it is never silently
resumed or overwritten.

`scripts/run_qwen35_dp2tp4_baseline_service.sh` is the final-baseline
service entry point. It refuses an existing container or manifest, parses the
authoritative `npu-smi` process table and exits before rendering or Docker
when any physical NPU0-7 is occupied. On an idle host it renders the frozen
runtime manifest, passes its exact environment and argv to the fixed
`quay.io/ascend/vllm-ascend:v0.23.0` image, and exposes all eight devices.
Mocked occupied and idle-path tests prove both the ownership gate and the
rendered DP2/TP4/device/environment command.

`scripts/analyze_qwen35_candidate_vs_original.py` is the authoritative
decision gate. It verifies the four fixed baseline SHA256 values and requires
twelve candidate artifacts (concurrency 1/5/8/16 × repetitions 1/2/3),
identical model/data/request identities, zero errors, complete natural-stop
request sets and exact response-hash equality. For every concurrency it takes
the median of the three per-run P95 values and emits `final-target-met` only
when both TTFT and TPOT ratios are at most 2/3. It also requires the median
per-run P99 values not to regress by default, and reports median P50 as
secondary evidence. Older artifacts produced by this script with a 0.5/P50
gate are historical and must not be mistaken for the current acceptance
decision.

The decision gate consumes the matrix runner's canonical
`c<concurrency>/repeat-<index>.json` layout and `matrix-run.json` status
manifest. It retains read compatibility with historical flat
`c<concurrency>-r<index>.json` candidate directories. The synthetic contract
test exercises the canonical layout and a missing-third-repeat failure.

For the current NPU0-3 TP4 loop, invoke the matrix runner with
`--experiment-contract .agents/experiments/exp-20260904-qwen35-query-rewrite-3x-e2e.yaml`
and `--model Qwen3-5/Qwen3.5-27B`. This path is intentionally independent of
the historical DP2/TP4 eight-device runtime renderer. It hash-locks the
experiment contract and fail-closes unless the matrix is c1/c5/c8/c16 x three
repetitions, seed 1024 and 32 requests per cell. The runner passes both
`--seed 1024` and `--limit 32` explicitly to the streaming benchmark.

The final stack is expected to combine core operators, algorithms and
configuration. "One variable" applies to each attribution step, not to the
final candidate.

## Operator lane

Reusable sources under `/cache/cch` include `ops-transformer`,
`cannbot-skills`, `cann-recipes-infer` and `vllm-ascend`. Before editing
any of them, read their nearest `AGENTS.md`, create a dedicated source
worktree, and preserve existing dirty work. An operator is accepted only after:

1. reference correctness on real shapes;
2. repeated operator benchmark;
3. feature-flagged integration into vLLM-Ascend;
4. model-level correctness under DP2/TP4;
5. query_rewrite quick32 versus fixed-original E2E evidence and a
   candidate-only diagnostic profile.

## Profile analysis readiness

- `scripts/run_qwen35_profile_request.py` performs an unprofiled warmup on
  record 0, calls the service's `/start_profile` endpoint, profiles record 31,
  and always calls `/stop_profile` after a successful start. Warmup and
  profile use distinct, run-unique `cache_salt` values so prefix caching
  cannot hide the profiled prefill. Its artifact stores dataset, question and
  response hashes but no raw confidential text, and marks profiler timings as
  non-performance evidence.
- Use a unique `--run-id` for every capture. The service must expose both
  profiler endpoints; HTTP 404 means profiler configuration was not active.
  Never run this driver concurrently with a formal TTFT/TPOT cell.
- `scripts/analyze_ascend_profile.py` recursively discovers Ascend
  `kernel_details.csv` files, records each input SHA256, and emits
  `qwen35-ascend-profile-hotspots/v1` JSON with category shares and raw top
  kernels. It groups the complete GDN prefill pipeline rather than treating
  only `ChunkGatedDeltaRule` as the cost.
- Validation passed with a zero-dependency fixture, `py_compile`, and a
  15,298-row historical Ascend profile smoke. Summed kernel duration is
  explicitly marked as **not wall time** because streams can overlap; TTFT and
  TPOT remain authoritative only in the E2E benchmark artifacts.
- Current source routing is phase-specific: prefill uses the chunk GDN
  pipeline (including chunk rule, recompute, merge and transpose kernels);
  decode uses the AscendC `npu_recurrent_gated_delta_rule` custom operator.
  The next treatment must be chosen from the new fixed-request profile, not
  inferred from historical profiles belonging to another run.
- `scripts/capture_qwen35_tp4_profile.sh` is the fail-closed one-shot
  orchestration entry point. It requires explicit unique run/container/profile
  identities, delegates the NPU0-3 ownership guard to the service launcher,
  waits for health, verifies both profiler endpoints in OpenAPI, captures the
  isolated request, waits for `kernel_details.csv`, analyzes it, records
  artifact hashes, and stops only the exact container it started while
  retaining the stopped container and logs. Existing output paths are rejected.
- `scripts/compare_ascend_profiles.py` compares normalized baseline and
  candidate hotspot reports by category, kernel duration, calls, and
  microseconds per call. It rejects identical source profiles, hashes both
  reports, and labels every ratio diagnostic-only/non-acceptance evidence.
  Formal speed decisions remain exclusively in the frozen E2E A/B gate.
- At 2026-09-04 16:43:31 UTC, NPU0-3 remained owned by
  `qwen36_27b_dk64_treatment_npu0_3` (PIDs 4111982-4111985) and NPU4-7 by
  `qwen38_gdn_fused_candidate` (PIDs 1312892-1312895). Neither was touched.

## Resume

The real TP4 v5 profile attempt used record 31 (1845 prompt tokens, one
completion token) and proved `async_scheduling=False`, but `/stop_profile`
still returned HTTP 500 and killed the worker. This rejects the async scheduler
as the root cause; do not retry the same HTTP profiler path unchanged. The raw
rank0 data was nevertheless exported offline with `msprof`. Its immutable
`op_summary` CSV SHA256 is
`7a6578f697f00d9f0267b990931e6ec1770a064f1deb18c2e7ad7fa26163073f`.
Across 6,453 rows, `hcom_allReduce_` accounts for 4,299,824.02 us, 94.585%
of summed task duration, over 237 calls. This is diagnostic-only profiler
attribution, not wall time or acceptance evidence.

Do **not** treat MatMul+AllReduce enablement as a candidate over the canonical
baseline. Exact-image unit tests and `AscendConfig._get_config_value` prove
that the user-provided `VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1` is used when
the additional-config key is absent. The v5 TP4 development profile instead
explicitly forced both sources false, so its 94.585% AllReduce attribution is
useful failure evidence but is not a profile of the canonical baseline.
The baseline YAML and TP4 baseline/profile launchers now explicitly set
`enable_matmul_allreduce=true` to eliminate fallback ambiguity. Re-profile
that canonical configuration when NPU0-3 are free before selecting a new
treatment.

Offline inspection of the exact `quay.io/ascend/vllm-ascend:v0.23.0`
image confirms the activation chain: `ascend_config.py` gives the explicit
additional config precedence, `ops/linear_op.py` selects
`MatmulAllreduceRowParallelOp` for row-parallel layers, and TP>1 with
reduction enabled calls `torch_npu.npu_mm_all_reduce_base`. TP4 therefore
meets the static activation conditions for dense Qwen3.5. Runtime operator/log
evidence remains mandatory; static source inspection is not a performance
result.

The MTP route is complete and rejected. Preserve all baseline, invalid and MTP
artifacts. Wait for explicit exclusive ownership of NPU0-3, then launch the
accepted non-MTP TP4 configuration under a new immutable profile container name
and output directory, with explicit torch-profiler configuration, and profile a
fixed real request. Commit `439be7d` makes profile mode synchronous as the
leading fix hypothesis: the real v2 attempt completed its request but
`/stop_profile` returned HTTP 500 after torch_npu reported that its external
callback ran on a different thread. It emitted no `kernel_details.csv` and is
invalid. The fix still requires runtime validation because the v3 launch operation
`exec-0000000000000422` then exited 42 before Docker because `p0_ab` acquired
NPU0-3. Do not reuse either failed attempt's paths as evidence. Do
not treat `VLLM_ASCEND_PTO_CHUNK_GDN` as a treatment. Do not perturb either
external NPU0-3 or NPU4-7 workload. Do not wait for or acquire NPU4-7. When
NPU0-3 are explicitly released, run one candidate at a time with
`scripts/run_qwen35_tp4_candidate_vs_original.sh`; the original
baseline is never relaunched.

## Fused GDN portability boundary

The frozen upstream fused-prefill patch is commit `77d13e2c0` with SHA256
`d16712f909810c1dd1a7704d0a7d53434032f800cb2af1f9562d11475489a76e`.
It reports only a 5890us-to-4964us operator microbenchmark on a different model
and software baseline. The v0.23.0 image is vLLM-Ascend `5cb98caa` and its
`gdn.py` SHA256 is
`d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`.
The image exports `torch_npu.npu_chunk_gated_delta_rule`, but the frozen patch
does not apply cleanly to that source. Do not mount the newer full `gdn.py`
from `/cache/cch/vllm-ascend`; it contains broader API changes. Port only the
minimal fused-op hunks against the exact image source, keep a feature flag and
fallback, then require activation proof, reference correctness, real
query_rewrite comparison with the fixed original and a candidate profile.
Treat it as one cumulative operator
treatment, not evidence of the requested 2x result.

## Quantization route — prohibited

The user explicitly prohibited quantization. Keep the current model and all
accepted candidates in BF16. Do not download, generate, load, benchmark, or
accept W8A8, INT8, FP8, weight-only, or activation-quantized checkpoints.
The file configs/qwen35-query-rewrite-w8a8-candidate.yaml is retained only as
historical research provenance; it is not an executable candidate.

The remaining route is cumulative BF16 optimization: attributable runtime
parameters, semantics-preserving inference algorithms, and native/fused Ascend
operators, each behind the frozen correctness and real query_rewrite E2E gates.

## FlashComm1 decision and next BF16 candidate

FlashComm1 was the first real candidate, not Fused MC2. The exact v0.23.0 source
and model guide describe FlashComm1 as a sequence-parallel communication path
for dense Qwen3/high-concurrency TP, decomposing traditional AllReduce into
ReduceScatter and AllGather. It is isolated in
`configs/qwen35-query-rewrite-flashcomm1-candidate.yaml` and launcher mode
`flashcomm1`; canonical MatMulAllReduce remains enabled. Fused MC2 is routed
through MoE code and is out of scope for this dense model. `enable_prefill_mc2`
is also not selected because its documented recommended
`max_num_batched_tokens=TP*512` conflicts with the frozen 32768 baseline.

The real NPU4-7 launch proved the switch active. The runtime automatically
removed graph sizes 1, 2, 6, 10 and 14 because sequence parallelism requires
TP4 multiples, then failed during KV-cache initialization with a symbolic
`s59` versus `ceil(s59/4)` assignment mismatch on every TP worker.
FlashComm1 therefore failed the startup gate. This is not latency evidence and
does not reject the general communication method; it rejects this unchanged
v0.23.0 Qwen3.5 TP4 integration.

Use `scripts/run_qwen35_tp4_candidate_vs_original.sh` for the real TP4
decision. It requires unique `RUN_ID` and absolute new
`OUTPUT_ROOT`, starts only the selected candidate, records its
container inspect and log, runs first-32 once at 1/5/8/16, and emits a
correctness plus 2x decision report and hashes. Its trap stops only the exact
container it started; the underlying launcher rejects any existing process on
the selected physical device set.

The next candidate was BF16 weight `FRACTAL_NZ`, isolated as
`weight_nz_mode=2` in
`configs/qwen35-query-rewrite-bf16-nz-candidate.yaml` and launcher mode
`bf16-nz`. This is not quantization: exact-image source applies
`maybe_trans_nz` inside `AscendUnquantizedLinearMethod` and continues
through `unquantized_gemm`. Mode 1 leaves BF16 weights in ND, while mode 2
converts eligible non-conv1d weights. The real launch proved the previously
unknown interaction negative: `aclnnMatmulAllReduce` requires the weight
input in ND and rejected FRACTAL_NZ before readiness. Do not stack it with the
failed FlashComm1 path.

The fixed original actually used MatMulAllReduce disabled. Therefore the next
bounded recovery is `weight_nz_mode=2` with MatMulAllReduce disabled: relative
to the fixed original this changes only the BF16 weight layout, while testing
whether the startup failure belongs specifically to the fused communication
path. This variant still needs activation, exact response correctness and real
  E2E evidence before it can enter the best stack.

The recovery was implemented as launcher mode `bf16-nz-mmar-off` with
`configs/qwen35-query-rewrite-bf16-nz-mmar-off-candidate.yaml`. Both the
environment and additional-config explicitly disable MatMulAllReduce, NZ is
explicitly mode 2, FlashComm1 is false, and no quantization argument exists.
The real run proves this combination starts and can reduce low-concurrency
TTFT, but its response hashes and concurrency-16 behavior reject it.

The next bounded candidate is MatMulAllReduce enabled alone with NZ mode 1 and
FlashComm1 disabled. This is a valid single-variable treatment relative to the
actual fixed original, which forced MatMulAllReduce false, and it targets the
profiled AllReduce bottleneck without either failed interaction.

That candidate was implemented as launcher mode `mmar-on` and
`configs/qwen35-query-rewrite-mmar-on-candidate.yaml`. It explicitly keeps
NZ mode 1, FlashComm1 false and BF16/no quantization. Its real run met the TTFT
p50 target but missed the TPOT target and exact-hash gate, so it is rejected.

### Active resource handoff

The user confirmed that physical NPU4-7 are assigned to this workstream;
continue to leave NPU0-3 untouched. The separate bounded
`/cache/austinov/p0/pin_ab_47.sh` run completed and self-cleaned. Watcher
operation `exec-00000000000005d7` proved NPU4-7 were released without
disturbing the NPU0-3 workers. Deferred operation
`exec-00000000000005e6` then ran the complete MMAR candidate and also
self-cleaned. The post-run snapshot shows no process on NPU4-7 and the same
four pre-existing VLLM worker PIDs on NPU0-3.

## Baseline evidence correction

The prior TP4 `quick32-v3` metrics are now the user-designated fixed
original denominator for the 2x goal. They forced
`enable_matmul_allreduce=false`; this remains a mandatory caveat in
decision reports, not a reason to rerun baseline. Every candidate must match
the original first-32/one-repeat/request semantics and pass the hash-locked
analyzer. MTP remains rejected because it regressed and changed response
hashes.

## Fixed-runtime profiler handoff

Physical NPU4-7 are assigned to this workstream and are the only accelerators
that may be used here. Physical NPU0-3 remain occupied by an external TP4
workload and must not be stopped, reset, remapped, or included in a launch.
Inside the task container, physical NPU4-7 are mapped to logical device 0-3.

The first fixed-runtime profile attempt used vLLM 0.23.0's torch profiler API
through /start_profile and /stop_profile. It failed even with async scheduling
disabled. The exact image source creates TorchProfilerWrapper lazily from
GPUWorker.profile(), which runs through a multiprocess RPC path. CANN then
reported that its external init callback ran on a different thread from
registerClient. /start_profile returned 200, the real request completed, but
/stop_profile killed TP0, canceled the executor and returned 500. Preserve the
failed run at fixed-runtime-mmar-off-npu4-7-20260904T2004Z; do not retry this
unchanged API path.

The stable replacement is CANN dynamic attach. Service mode
profile-msprof-mmar-off preserves the fixed-runtime MMAR-off/NZ1/
FlashComm1-off settings and async scheduling, but sets PROFILING_MODE=dynamic
before model startup. The orchestrator scripts/capture_qwen35_tp4_msprof.sh
resolves one TP worker PID, attaches msprof, brackets only the real
query_rewrite request with interactive start/stop, exports op_summary_*.csv,
and emits privacy-safe hotspots. Ascend's multi-device restriction means one
TP rank is collected at a time; start with TP0, which is logical device 0 /
physical NPU4.

A single-card constant-memory matmul smoke on physical NPU4 proved this path:
operation exec-000000000000066f completed dynamic start, stop, quit and
export. The analyzer parsed 41,119 calls from the exported op-summary. The
smoke container self-cleaned and NPU4 returned idle. Profiler timings remain
diagnostic only and must never replace the frozen non-profile E2E metrics.

## Fixed-runtime profile result

Operation exec-0000000000000680 completed the first valid full-model CANN
dynamic profile. Run fixed-runtime-msprof-tp0-npu4-7-20260904T2043Z attached
to TP0, logical device 0 / physical NPU4, while TP4 executed one real record-0
request with 1810 prompt tokens and 104 completion tokens. The exported
op_summary has SHA256
3350ab8564e00f3cb1f549823445d411efa0dddc52f7c6739c961f68a0cb4d5f and
162,448 rows.

Whole-request summed rank-0 kernel duration attributes 64.1054% to MatMul,
16.4343% to collectives, 2.0516% to recurrent GDN, 1.0429% to the chunk-GDN
prefill family, and 1.1085% to attention. After the detected prefill boundary,
MatMulV2 is 70.702%, AllReduce 10.530%, and recurrent GDN 2.406%. The dominant
decode shapes are the TP-sharded FFN projections: 1x5120 by 8704x5120 and
1x4352 by 5120x4352.

One 173830.04us AllReduce occurred before the detected prefill window and
should not be reported as steady collective latency. Across 13,803 AllReduce
rows, p50/p95 are 22.86/23.70us. All profile sums remain diagnostic and are
not wall time. The profiler-inflated request TTFT/TPOT are never compared with
the immutable E2E baseline.

The task workers exited after export. NPU4-7 returned idle and the pre-existing
external NPU0-3 PIDs 1031654-1031657 remained unchanged. request.json contains
hashes, counts and timings only, with no raw response text.

## Next paper treatment: NPU Prompt Lookup Decoding

The profile demotes fused GDN from the first optimization slot. Its complete
prefill family is only 1.0429% of whole-request summed kernel time, whereas
steady decode is dominated by small-batch GEMM. MTP is already rejected, so
the next bounded training-free algorithm is the reference-verification idea
from LLMA (arXiv:2304.04487), specialized as Apoorv Saxena's code-level Prompt
Lookup Decoding method and implemented by the exact image's existing ngram_gpu
path. Prompt Lookup Decoding itself is a code release, not arXiv:2311.04934;
that identifier belongs to the unrelated Prompt Cache paper.

Launcher mode ngram-gpu uses five speculative tokens with n-gram lengths 2-5.
The exact v0.23.0 source dispatches it to
torch.ops._C_ascend.npu_ngram_spec_decode and ships a 910B kernel binary.
This also preserves async scheduling; the CPU ngram proposer would force an
incompatible scheduler change. The treatment keeps BF16, MMAR off, NZ1,
FlashComm1 off, TP4, graph policy, prefix caching, seed and request protocol.

Run scripts/run_qwen35_tp4_candidate_vs_original.sh with
CANDIDATE_MODE=ngram-gpu, a unique RUN_ID and a new absolute OUTPUT_ROOT.
Require zero errors, natural stops, privacy-safe labeled-reference quality,
speculative acceptance counters and the fixed-original 1/5/8/16 comparison.
Reject or retune if accepted spans do not offset verification overhead.

## NPU Prompt Lookup real result

The bounded `ngram-gpu` candidate ran on assigned physical NPU4-7 in BF16
with MMAR off, NZ1, FlashComm1 off and async scheduling preserved. Run
`ngram-gpu-fixedorig-npu4-7-20260904T2048Z` completed c1, then failed at c5.

At c1, 32/32 requests completed with zero errors. TTFT p50 was 781.240 ms
versus 928.329 ms original (1.188x better), but TPOT p50 was 185.297 ms
versus 38.472 ms (4.82x slower). At c5, 25/32 completed before the engine
stalled. The observed subset had TTFT 1626.369 ms and TPOT 412.783 ms, with
TPOT 7.67x slower than the original. c8 and c16 were not run.

Stall evidence was captured before intervention: four requests remained
Running, the generation counter froze at 17,686, and EngineCore repeatedly
logged `Poller timed out` for more than three minutes. There was no OOM.
Speculative counters recorded 13,087 draft steps, 65,435 draft tokens and
4,538 accepted tokens (6.934%). First-position acceptance was only 14.809%,
so even k=1 cannot pay for one extra target token. Do not retune this method.

The terminal decision is `reject-runtime-failure`. Decision SHA256 is
`09d43a3715bbd2bc266f94dca5f5468aa62735027bb73383df4d1cc13ed484ab`; the
run-level SHA256SUMS digest is
`9bebf07aa270e5cc3c1e54c712f9572d474cf7eac147a497284f2a1dd039579a`.
All artifacts are under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/ngram-gpu-fixedorig-npu4-7-20260904T2048Z`.

The failure-finalization path is now hardened: partial cells are preserved as
observed-only evidence, missing cells become `not-run`, the analyzer returns
exit 4 with a terminal rejection, and the orchestrator hashes only artifacts
that exist. Static and unit tests cover this path.

The exact candidate container exited after evidence capture. Physical NPU4-7
are idle and remain assigned to this task; external NPU0-3 PIDs
1031654-1031657 were unchanged.

## Next handoff action

Proceed to the profile-ranked dense FFN operator lane. Inspect exact
vLLM-Ascend 0.23.0 source plus `/cache/cch` operator-generation assets for a
BF16 shape-specialized or fused gate/up-SwiGLU-down path targeting the measured
decode projections `1x5120 x 8704x5120` and `1x4352 x 5120x4352`. Before E2E,
require reference correctness, repeated operator microbenchmarks and a
feature flag. E2E must reuse the immutable quick32-v3 denominator and only
physical NPU4-7.

## Selective dense FFN NZ checkpoint

The dense FFN lane now has a valid operator microbenchmark and a
feature-flagged vLLM-Ascend integration. The paper-level design basis is
DeepSpeed Inference (arXiv:2207.00032): for small-batch inference, specialize
GEMM scheduling/layout and only fuse regions whose measured economics justify
the extra implementation. On this host, the profile shows post-prefill
MatMulV2 at 70.702% while SwiGLU is only 0.9623% of summed kernel time, so the
first port targets weight layout rather than full FFN fusion.

Preserve the first microbenchmark directory
ffn-bf16-layout-npu4-20260904T220321Z as invalid/no-op evidence: internal
formats were disabled and both requested NZ tensors remained format 2. The
corrected run is ffn-bf16-layout-npu4-20260904T220321Z-v2, operation
exec-0000000000000722. It explicitly enabled internal formats and aborted
unless NZ tensors reported format 29.

The valid run used Qwen3.5 layer-0 real BF16 weights, TP4 rank-0 gate/up
[8704,5120] and down [5120,4352], M=1/5/8/16, 20 warmups, 100 timed
iterations and five rotated-order repeats. Converting both FFN projections to
NZ produced speedups 1.0803x, 1.0837x, 1.0841x and 1.0905x respectively
(1.0846x geometric mean). Every output was bit-identical to ND. Gate/up-only
NZ reached 1.0529x geometric mean; down-only reached 1.0269x.

The installed npu_ffn feasibility control failed exactly as its API contract
predicts: BF16 SwiGLU without experts is unsupported. Do not switch to FP16
and do not quantize.

Exact vLLM-Ascend source lives at
/cache/cch/.worktrees/exp-20260904-qwen35-selective-ffn-nz on branch
work/exp-20260904-qwen35-selective-ffn-nz, commit 71c25ec9, based on v0.23.0
commit 5cb98caa. It adds default-off
VLLM_ASCEND_ENABLE_DENSE_FFN_NZ=1 behavior for .mlp.gate_up_proj only.
.mlp.down_proj stays ND because it crosses MatmulAllReduce; attention and
recurrent weights also stay ND and global weight_nz_mode remains 1. The
selective policy test passed after this correction; all eight earlier linear
tests remain valid. Push to the upstream GitHub remote is blocked by missing
host credentials; the local commit is the authoritative checkpoint.

The model-tuning launcher mode is selective-ffn-nz. It is hard-restricted to
physical NPU4-7, verifies source commit 71c25ec9, and read-only overlays only
envs.py, utils.py and ops/linear.py into the exact image source tree.
Rollback is unset the feature flag/remove those three overlays. The next
first E2E attempt, operation exec-0000000000000758, rejected both-NZ during
graph-capture warmup: aclnnMatmulAllReduce requires down_proj x2 in ND and
returned 161002/EZ0017 for FRACTAL_NZ. No requests were measured. Evidence is
hashed under selective-ffn-nz-fixedorig-npu4-7-20260904T2218Z. The task-owned
container was stopped; physical NPU4-7 were released and external NPU0-3 PIDs
1031654-1031657 were unchanged.

Retry only gate/up NZ with down_proj ND and MMAR retained. Run immutable
quick32 at concurrency 1/5/8/16 against the fixed original. Profile only if
the corrected E2E candidate is retained.

## Selective dense gate/up NZ final E2E decision

The corrected gate/up-only service started successfully on assigned physical
NPU4-7 and operation exec-0000000000000778 completed every immutable quick32
cell. c1/c5/c8/c16 each finished 32/32 requests with zero errors and all
finish reasons were natural stop.

Versus the fixed original, TTFT p50 improved 2.080x/2.161x/2.148x/3.884x and
TPOT p50 improved 1.332x/1.383x/1.523x/1.471x. The 2x TTFT target is met, but
the 2x TPOT target is not.

Do not attribute the full fixed-original difference to gate/up NZ. Against the
already measured MMAR-only candidate, its incremental TPOT speedups are
0.992x/1.002x/1.025x/0.951x, with 0.992x geometric mean. The c16 TTFT delta is
an unpaired single-run outlier; c1 and c8 slightly regress.

Correctness is separately resolved. Operation exec-000000000000079d ran a
correctness-only c1 control on the same physical NPU4-7, same 32 records,
BF16, MMAR enabled, NZ1 and no quantization, with gate/up selective NZ absent.
Control and candidate both completed 32/32 with zero errors and natural stop;
both have six normalized-whitespace exact matches and normalized character
similarity mean 0.1875. The candidate raw-exact count is 4 versus control 5,
but the difference disappears under whitespace normalization. Combined with
the isolated real-weight bit-identical microbenchmark, the business
correctness gate passes.

Final decision: retain MMAR as the current best stack, reject gate/up NZ from
the cumulative stack for absent incremental TPOT benefit, and continue the
loop from MMAR. Do not enable VLLM_ASCEND_ENABLE_DENSE_FFN_NZ in the next E2E
candidate. The implementation remains default-off and preserved as reusable
operator evidence.

Artifacts:

- candidate: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/gate-up-nz-fixedorig-npu4-7-20260904T2232Z
- correctness control: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/correctness-controls/mmar-on-c1-quality-npu4-7-20260904T2300Z
- automated decision SHA256: b178d4d8e264cfb63206fd20bc7177aaa1770de657f25c24f1f1ef8e32601018
- semantic review SHA256: 704bf6abfe2d8c6f4185fc1b84d6f86159c76d11eadadd5e3ff7f7e5732f3b17
- candidate SHA256SUMS digest: 0edc12637a83fabed38462132fc4235186e4f8bdb96c2d8f3cb2078bbf14a2c3

The benchmark finalization script's literal Bash array escaping bug was fixed
and covered by a regression guard. The four measured cells were not rerun.
Both task containers exited, physical NPU4-7 are idle, and external NPU0-3
worker PIDs 1031654-1031657 are unchanged.

## Checkpoint publication status

Maintainer evidence and script fixes were committed locally as a29aa43. The
subsequent HTTPS push to origin failed because chicaihong01 has no GitHub
username/credential available. Do not retry unchanged. The local worktree and
branch are authoritative until credentials are provisioned; verify the final
HEAD recorded by the next checkpoint before handoff.

## MMAR-on dynamic profile and topology decision

The valid MMAR-enabled CANN dynamic profile is
`tp4-mmar-on-msprof-20260904T2313Z` (operation
`exec-00000000000007b8`). It used the retained BF16 stack on physical
NPU4-7: MMAR on, NZ1, FlashComm1 off, async scheduling on and
FULL_DECODE_ONLY. Record 0 completed with 1810 prompt tokens, 104 completion
tokens and natural stop. The exported op-summary has 162,448 rows and SHA256
`148f86b18d797d6f623b49812ed228d721ddf1fdd52468fc7fadc421fc9c3d6d`.

Summed rank-0 kernel duration is collective dominated: 64.8641% collective
and 24.5622% matmul. `MatmulAllReduceMc2AicpuKernel` accounts for 48.1673%
and `MatmulAllReduce` for another 16.5999%, each with 13,696 calls. These
sums overlap across streams and are diagnostic only; the profiler-inflated
request timing is not an E2E acceptance result.

The exact vLLM-Ascend Qwen3.5 dense guidance recommends the smallest TP that
fits and using remaining devices for DP because larger TP adds per-layer
AllReduce. On the four assigned 910B4 cards, the bounded translation was
TP4/DP1 -> TP2/DP2 while retaining MMAR and all other current settings.
Launcher/config support was added and validated in local commit `4794324`.
Both launcher and candidate orchestrator are now hard-restricted to physical
NPU4-7 so this workstream cannot launch on NPU0-3.

The startup gate `tp2-dp2-mmar-on-npu4-7-20260904T2330Z` rejected the
candidate before E2E. All four task cards reached 32,593-32,594 MiB HBM.
During `determine_available_memory -> profile_run`, multimodal encoder
attention then tried to allocate another 258 MiB with only 173.92 MiB free
and raised `torch.OutOfMemoryError`. No benchmark request ran, so there is
no latency claim. Do not weaken the immutable capacity contract
(`max_model_len=133000`, `max_num_batched_tokens=32768`,
`max_num_seqs=16`) merely to make this candidate start; treat any capacity
retune as a separate product tradeoff, not a performance win.

Hashed startup evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/startup-gates/tp2-dp2-mmar-on-npu4-7-20260904T2330Z`.
The SHA256SUMS digest is
`f38d2e484f3354e5820854cc39662acb529f8700c46877d583bf0e657a3006e8`.
The exact probe container was stopped. NPU4-7 returned to 2865-2866 MiB idle
HBM with no running processes; external NPU0-3 worker PIDs
1031654-1031657 remained unchanged.

Final topology decision: retain TP4/DP1 plus MMAR as the current best stack,
reject TP2/DP2 under the fixed serving-capacity contract, and continue the
TPOT loop from the retained stack. TTFT already meets the 2x target at all
four concurrency points; TPOT remains 1.343x/1.380x/1.486x/1.546x versus the
fixed original and is still the open objective.

### Text-only TP2/DP2 recovery also rejected

The follow-up mode `tp2-dp2-mmar-on-text-only` preserved HCCL_BUFFSIZE=512
and every text-capacity parameter, but set image/video limits to zero because
the query_rewrite benchmark is text only. Runtime activation was explicit:
all supported multimodal limits were zero and vLLM entered text-only mode.
This removed the earlier visual-encoder OOM and reduced the four task workers
to about 29,067-29,068 MiB HBM during initialization.

The topology still cannot satisfy the frozen 133k text capacity. The exact
memory profile was 25.17 GiB weights, 1.92 GiB torch peak increase and
0.50 GiB non-torch forward increase, for 27.59 GiB non-KV memory. At
`gpu_memory_utilization=0.90`, calculated KV memory was -1.05 GiB and both
DP engines rejected startup with `No available memory for the cache blocks`.
No request ran.

A higher utilization is not a sound recovery for the frozen capacity. Even
using the full reported 29.49 GiB as a conservative upper bound leaves only
1.90 GiB before graph memory. Existing TP4 evidence needs about 2.15 GiB for
one 133k request (10.77 GiB / 5.01 maximum concurrency); TP2 cannot require
less per rank than TP4. Therefore the fixed text capacity is infeasible
without reducing model length/batch capacity, offloading, or quantization.
Those are outside this candidate; quantization is explicitly prohibited.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/startup-gates/tp2-dp2-mmar-on-text-only-npu4-7-20260904T2345Z`;
SHA256SUMS digest
`7785a1f932bf4c4d9cc577b7179ce30560485a2039c6c8b10af53c253a161d2d`.
The exact container was stopped. NPU4-7 are idle at 2866-2867 MiB and
external NPU0-3 PIDs 1031654-1031657 are unchanged. Do not retry TP2/DP2
again unless the user explicitly changes the serving-capacity contract.

## HCCL AIV communication candidate rejected

The next one-variable communication treatment kept the retained BF16
TP4/DP1 MMAR stack unchanged and set `HCCL_OP_EXPANSION_MODE=AIV`. It used
physical NPU4-7 only, retained HCCL_BUFFSIZE=512, NZ1, FlashComm1 off, async
scheduling and FULL_DECODE_ONLY, and did not use quantization.

Operation `exec-0000000000000834` completed all four immutable quick32
cells. c1/c5/c8/c16 each finished 32/32 requests with zero errors and natural
stop. TTFT p50 versus the fixed original was 439.078/513.831/508.961/955.469
ms, or 2.114x/2.126x/2.127x/2.172x faster. TPOT p50 was
28.830/40.397/45.755/52.907 ms, or 1.334x/1.333x/1.478x/1.527x faster than
the fixed original.

The cumulative decision is based on the retained MMAR-only stack, not the
original. AIV's incremental TPOT speedups were
0.994x/0.966x/0.995x/0.988x, with 0.9854x geometric mean: about 1.46% slower.
Incremental TTFT was 0.989x/1.009x/0.982x/0.965x. Therefore reject AIV and
continue from MMAR-only; TTFT still meets the 2x goal, while TPOT remains
open.

The analyzer's exact cross-run hash gate reported hold, but fixed-runtime
hash drift is already calibrated and the AIV treatment changes communication
scheduling only. All 128 requests completed naturally with no error. The
recorded reference-quality summaries are preserved in the experiment YAML;
this is sufficient to classify the run as a performance rejection rather
than an unproven runtime failure.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-on-hccl-aiv-fixedorig-npu4-7-20260904T2353Z`.
The decision SHA256 is
`de05c9281c5e710e8f1bdc485b2fa2cfa1b6d245b08ba80ebf3d4641f1e586d4`;
the SHA256SUMS digest is
`82f601478bc58a7c7f68282a8d136639cb6e07f2d766e4d588ae1afc21947e3b`.
The exact candidate container exited. Physical NPU4-7 are idle at
2866-2867 MiB with no running processes; external NPU0-3 PIDs
1031654-1031657 remain unchanged.

Next, inspect the relocated `/cache/cch` operator-generation assets for a
feature-flagged, BF16, shape-specialized MatMulAllReduce or compatible
row-parallel projection treatment. Require isolated correctness and repeated
microbenchmarks before E2E. Do not revisit TP2/DP2, FlashComm1, prompt lookup,
MTP, gate/up NZ or AIV unchanged.

## Dense gate-up weight-prefetch candidate ready

The relocated source and operator assets were inspected before another
compile attempt. On 910B4, the available MatMulAllReduce V2/V3 sources do not
expose a new execution mode: V2 fixes commTurn=0/streamMode=1, while V3 uses
AI CPU on Atlas A2 and reserves CCU for Ascend 950. The fused
MatMulAllReduceAddRmsNorm path is deprecated and its current graph pass does
not cover decode sizes or the retained fused MMAR node. FlashComm2 is
prefill-oriented and loses its row-parallel branch whenever MMAR is enabled.

The next bounded candidate therefore uses vLLM-Ascend 0.23.0's existing
dense weight-prefetch path. It keeps the retained BF16 TP4/DP1 MMAR stack and
enables only dense MLP gate/up prefetch at ratio 1.0. Runtime caps the copied
prefix at 18 MB; attention, MoE and dense down-projection prefetch are
explicitly disabled. This path is eligible when decode token count is below
500 and starts from the preceding row-parallel o_proj completion, so it
targets the immutable c1/c5/c8/c16 TPOT cells without removing MMAR.

Launcher mode is `mmar-on-weight-prefetch-gateup`; manifest is
`configs/qwen35-query-rewrite-mmar-on-weight-prefetch-gateup-candidate.yaml`.
It is hard-restricted to physical NPU4-7 and contains no quantization. Compare
the complete quick32 matrix to the fixed original for the user-facing target,
but retain it cumulatively only if it improves TPOT over MMAR-only. Rollback
is selecting `mmar-on` or removing `weight_prefetch_config`.

## Dense gate-up 18 MB weight prefetch rejected

Operation `exec-000000000000086e` completed the real quick32 matrix on
physical NPU4-7. Container inspection and the service log confirm that the
isolated dense MLP gate/up prefetch config was active together with retained
MMAR, NZ1, async scheduling and FULL_DECODE_ONLY. No quantization was used.

c1/c5/c8/c16 each completed 32/32 requests with zero errors and all 128
finish reasons were natural stop. TTFT p50 versus the fixed original was
428.822/507.430/517.075/703.415 ms, or
2.165x/2.153x/2.093x/2.950x faster. TPOT p50 was
28.852/38.914/47.314/52.815 ms, or
1.333x/1.383x/1.429x/1.530x faster than the fixed original.

The cumulative gate fails. Against MMAR-only, incremental TPOT was
0.993x/1.002x/0.962x/0.990x with 0.9866x geometric mean, about 1.34% slower;
c8 regressed 3.81%. The c16 TTFT improvement is not sufficient to retain a
candidate that regresses the still-open TPOT objective. Final decision:
retain MMAR-only and reject the 18 MB prefetch treatment.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-on-weight-prefetch-gateup-fixedorig-npu4-7-20260905T001741Z`.
All SHA256SUMS entries verify. The decision SHA256 is
`0bf2914afd2e8f1d6aeeb283f967619bf128fec513e933d78bb3c8fec2c46ccd`;
the SHA256SUMS digest is
`ef77e98e3396aa7a97bb7779436ac183b68b6cb6f67fd810a5a6b57d5fd19cca`.

The exact candidate container exited. Physical NPU4-7 are idle at
2866-2867 MiB, and external NPU0-3 PIDs 1031654-1031657 are unchanged.
If weight prefetch is revisited, use a sub-cap ratio such as 0.1 so the
prefetched prefix is below the 18 MB cap; ratios at or above about 0.2 are
effectively the same cap for this approximately 89 MB gate/up shard.

## Sub-cap gate-up prefetch follow-up ready

The bounded follow-up changes only dense MLP gate/up prefetch ratio from 1.0
to 0.1, reducing the prefetched prefix from the 18 MB cap to about 8.9 MB.
All other retained MMAR settings and explicit zeros for attention, MoE and
down-projection prefetch are unchanged. Launcher mode is
`mmar-on-weight-prefetch-gateup-0p1`; it remains restricted to physical
NPU4-7 and contains no quantization. Accept only if the full quick32 matrix
improves TPOT cumulatively over MMAR without a material cell regression.

## Sub-cap gate-up prefetch provisionally retained

Operation `exec-0000000000000884` completed the full quick32 matrix on
physical NPU4-7. Container inspection and the service log confirm that dense
MLP gate/up prefetch ratio 0.1 was active with the retained MMAR, NZ1, async
scheduling and FULL_DECODE_ONLY stack. No quantization was used.

c1/c5/c8/c16 each completed 32/32 requests with zero errors and all 128 finish
reasons were natural stop. TTFT p50 was
423.975/490.437/492.489/895.936 ms, or
2.190x/2.227x/2.198x/2.316x faster than the immutable original. TPOT p50 was
28.834/37.976/44.146/51.922 ms, or
1.334x/1.417x/1.532x/1.556x faster than the immutable original.

Against retained MMAR-only, incremental TPOT was
0.9934x/1.0272x/1.0310x/1.0066x with 1.01445x geometric mean, about 1.45%
faster. The sole regression is c1 TPOT at 0.66%, while c5/c8/c16 improve.
Incremental TTFT geometric mean is 1.03104x, about 3.10% faster. This satisfies
the candidate's cumulative retention gate, so ratio 0.1 is provisionally
retained as the new stack. The final 2x TPOT objective remains open in every
cell; no completion claim is made.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-on-weight-prefetch-gateup-0p1-fixedorig-npu4-7-20260905T003601Z`.
All SHA256SUMS entries verify. Candidate config SHA256 is
`3b939c7350e29fb72f2a0c200a966473cc30e54b36dbc6725ac4ae8e49f1d851`;
decision SHA256 is
`d41bcdba2a3d1cb964062348d9a43271814bd07859aadb183b24c5db6a90865d`;
the SHA256SUMS digest is
`df47028cfaad83112d8e9624453d77f4387246499e5fe30b8560408bd50e445f`.

The exact candidate container exited. Physical NPU4-7 returned idle at 2866
MiB with no running processes. External NPU0-3 PIDs 1031654-1031657 were
unchanged. Rollback remains selecting launcher mode `mmar-on`; do not retest
prefetch ratios at or above about 0.2 because they hit the same 18 MB cap that
was already rejected.

## TP2/PP2 cumulative topology candidate ready

The next bounded candidate changes only the parallel topology from TP4/PP1 to
TP2/PP2 on physical NPU4-7. It retains BF16, MMAR, gate/up prefetch ratio 0.1,
NZ1, async scheduling and FULL_DECODE_ONLY, and uses no quantization. Unlike
the rejected TP2/DP2 route, pipeline parallelism keeps approximately one
quarter of model weights per rank instead of replicating the full model per
TP2 replica. The exact vLLM-Ascend 0.23.0 source has four-card TP2/PP2 E2E
coverage and explicit async-scheduling pipeline handling.

Run the fail-closed startup and memory gate first. Continue to the immutable
quick32 comparison only after service health and a natural-stop smoke pass.
The launcher is hard-restricted to physical NPU4-7. Rollback is selecting
`mmar-on-weight-prefetch-gateup-0p1`; there is no source overlay.

## TP2/PP2 topology rejected by c1 fail-fast gate

Operation `exec-00000000000008a4` proved that TP2/PP2 starts successfully:
the runtime accepted TP2/PP2/DP1, async scheduling, MMAR and dense gate/up
prefetch ratio 0.1, and MMAR layer logs reported `tp_size=2`. No quantization
was active. PP0/PP1 weights occupied about 13.09/14.27 GiB per rank and left
about 9.45/8.26 GiB for KV cache; the service exposed 510572 KV tokens and
returned HTTP 200.

The complete c1 cell was a hard performance rejection: 32/32 requests, zero
errors and all natural stops, but TTFT p50 was 465.656 ms and TPOT p50 was
48.082 ms. Relative to the retained TP4 stack this is 9.83% slower TTFT and
66.75% slower TPOT. Relative to the immutable original it is only 1.994x TTFT
and 0.800x TPOT, so the candidate cannot satisfy the all-concurrency 2x goal.
The result confirms that pipeline serialization overwhelms the smaller TP
collective at concurrency 1.

The exact candidate container was deliberately stopped at the start of c5
under the fail-fast policy; c8/c16 were not run. Consequently, the four c5
responses and 28 post-stop client errors are invalid for performance. The
generated `decision.json` mechanically labels this as runtime failure, but
the authoritative decision is c1 performance rejection, not a spontaneous
service crash.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp2-pp2-mmar-prefetch-0p1-fixedorig-npu4-7-20260905T005727Z`.
Every SHA256SUMS entry verifies; the c1 artifact SHA256 is
`bbde9f2586a7f5f493e583bdfd50ac98bd974000b6e5f67c178502eaa224afce`
and the SHA256SUMS digest is
`7d712223d6f9517f259e08f72866a71092fca05c5e4774861dea70bf44debe50`.
Physical NPU4-7 returned idle at 2865-2866 MiB, while external NPU0-3 PIDs
1031654-1031657 remained unchanged. Retain TP4 MMAR plus ratio-0.1 prefetch.

## Static decode-kernel candidate ready

The next bounded operator/compiler treatment retains the TP4 MMAR plus
ratio-0.1 gate/up prefetch stack and changes only
`ascend_compilation_config.enable_static_kernel` from false to true. The
exact vLLM-Ascend 0.23.0 compiler scopes static binaries to captured decode
gears, which matches the fixed 1/2/4/6/8/10/12/14/16 serving shapes. It uses
BF16 and no quantization and is restricted to physical NPU4-7.

Do not force the existing matmul-allreduce-add-RMSNorm pass into decode: its
source threshold excludes token counts below 513 and the corresponding CANN
operator API is marked for deprecation. XliteGraph is also not eligible in the
current image because the `xlite` package is absent. For static kernel, require
an activation log plus a valid c1 cell before allowing the rest of quick32.

## Static decode kernel rejected at high concurrency

Operation `exec-00000000000008c9` completed the full quick32 matrix on
physical NPU4-7. The runtime accepted the retained TP4 BF16 MMAR plus
gate/up-prefetch-0.1 stack with `enable_npugraph_ex=true` and
`enable_static_kernel=true`; `quantization=None`. The compiler explicitly
reported that static-shape kernels would accelerate aclgraph execution,
generated static run packages, captured all 9/9 FULL decode graphs in 418
seconds, and then served HTTP health 200.

All c1/c5/c8/c16 cells completed 32/32 requests with zero errors and all 128
finish reasons were natural stop. TTFT p50 was
432.649/499.907/506.878/5391.965 ms. TPOT p50 was
27.067/35.523/43.181/48.853 ms. Relative to the immutable original, TTFT
speedup was 2.146x/2.185x/2.135x/0.385x and TPOT speedup was
1.421x/1.515x/1.566x/1.654x.

Static kernels improve retained-stack TPOT by
1.065x/1.069x/1.022x/1.063x, or 1.05471x geometric mean. However, TTFT is
0.980x/0.981x/0.972x/0.166x versus retained, only 0.62767x geometrically.
The c16 TTFT p50 regression is 501.83%. It is not explained by a longer
candidate answer stream: static c16 produced 7038 completion tokens in
47.134 s versus retained 7283 tokens in 46.201 s. All static gears had already
been captured before service readiness. The evidence therefore shows
material high-concurrency first-token queueing, not a valid trade for the
already-achieved all-cell TTFT goal.

The analyzer records `hold-exact-hash-drift`, consistent with the previously
calibrated cross-run nondeterminism. That is not the rejection reason: every
request completed naturally without runtime error, and reference-quality
summaries remain in the observed run-to-run band. The authoritative
maintainer decision is to reject static kernel on performance and retain TP4
MMAR plus gate/up prefetch ratio 0.1.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-prefetch-0p1-static-kernel-fixedorig-npu4-7-20260905T011539Z`.
Every SHA256SUMS entry verifies. Candidate config SHA256 is
`b21d908a05602e80b0b1d00f1b8af32a559b5fcdbc79d3c39398639a4af0cc34`;
decision SHA256 is
`f7ff3380dddf1072e67c43ed4de50d69f9875b052bb74945399cc5ea2592ac54`;
SHA256SUMS SHA256 is
`d7bca4880afdce8d77075a5c0b60ffe60f8eb8125a9f15958e6f51fc685550bd`.
The exact candidate container exited. NPU4-7 are idle at 2865-2866 MiB with
no running processes, and external NPU0-3 PIDs 1031654-1031657 are unchanged.

## TASK_QUEUE_ENABLE=2 cumulative candidate ready

The retained service log proves that enhanced NPU graph compilation was
already active by default with `enable_npugraph_ex=true` and
`enable_static_kernel=false`. Therefore do not run a duplicate explicit
npugraph-ex candidate: the rejected static experiment changed only static
kernel behavior.

The next bounded parameter treatment keeps the retained TP4 BF16 MMAR plus
dense gate/up-prefetch-0.1 stack and changes only `TASK_QUEUE_ENABLE` from
1 to 2. The exact vLLM-Ascend 0.23.0 performance-tuning guide recommends level
2 to optimize the operator-delivery queue, which is applicable to the current
communication-dominated decode profile. The documented risk is higher memory
peak, so startup, HBM, health and natural-stop smoke are fail-closed gates.

Launcher mode is
`mmar-on-weight-prefetch-gateup-0p1-taskqueue2`; manifest is
`configs/qwen35-query-rewrite-mmar-on-weight-prefetch-gateup-0p1-taskqueue2-candidate.yaml`.
Shell syntax, launch mocks and a structural comparison prove that the runtime
diff is only `TASK_QUEUE_ENABLE: 1 -> 2`. It uses no quantization and is
restricted to physical NPU4-7. Roll back by selecting the retained
`mmar-on-weight-prefetch-gateup-0p1` mode.

## TASK_QUEUE_ENABLE=2 rejected at graph-capture startup gate

Operation `exec-000000000000090e` activated
`TASK_QUEUE_ENABLE=2` in the exact candidate container, retained BF16
TP4/DP1, MMAR, gate/up prefetch ratio 0.1 and `quantization=None`, then
failed before service readiness. During FULL_DECODE_ONLY graph capture,
`torch_npu` explicitly raised:
`Do not support TASK_QUEUE_ENABLE = 2 during NPU graph capture, please
export TASK_QUEUE_ENABLE=1/0`, followed by `ERR00007 PTA feature not
supported` on all four workers.

No HTTP health check succeeded and no benchmark request ran. This is a
startup/runtime compatibility rejection, not a performance result; make no
TTFT or TPOT claim for level 2. Do not combine level 2 with the retained graph
mode again. Removing graph capture to accommodate it would be a second major
variable and would discard a proven optimization, so it is not the immediate
recovery path.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-prefetch-0p1-taskqueue2-fixedorig-npu4-7-20260905T014744Z`.
All SHA256SUMS entries verify. Candidate config SHA256 is
`425dee8144446bd4b019c7bc5dafcbefd673f6621cc4c1e97973468e1381077c`;
decision SHA256 is
`dcb66e2534867bde7d8fc02c3e0101099231c4b77cffc63ea33752750de0e207`;
SHA256SUMS SHA256 is
`926e6c1d77a218fabde8354ed32382f0aa9402c65206efb12daaca8dea3a371c`.
The exact candidate container was stopped. NPU4-7 are idle and external
NPU0-3 PIDs 1031654-1031657 remain unchanged. Retain
`TASK_QUEUE_ENABLE=1`.

## TP2/DP2 capacity probes and 32K conditional tier rejected

The retained BF16 TP4/DP1 MMAR plus gate/up-prefetch-0.1 stack was translated
to TP2/DP2 on physical NPU4-7 without quantization. Two 133K text-only startup
probes were run before changing the serving contract. With
`max_num_batched_tokens=16384`, each worker used 26.64 GiB outside KV cache
and reported -0.10 GiB available KV. With 8192, non-KV memory fell to
26.16 GiB and available KV rose to 0.38 GiB, but one 133000-token request needs
4.30 GiB; vLLM estimated a maximum model length of only 6912. Both runs served
zero requests. Their decision and log hashes are sealed under:

- `tp2-dp2-prefetch0p1-text-bt16384-fixedorig-npu4-7-20260905T022500Z`
  (SHA256SUMS digest
  `487e2c03e84f85344b8747fed478802db8a0f8b14deb44805e2adf2d6b0d7b98`);
- `tp2-dp2-prefetch0p1-text-bt8192-fixedorig-npu4-7-20260905T023000Z`
  (SHA256SUMS digest
  `9579bbbb2417e23e95de9cff5720c65f4f80aff1cf5ce26210d527de177e9012`).

A final bounded conditional experiment reduced the context contract to 32768,
kept batch tokens at 8192, and set utilization to 0.95. This was explicitly a
composite recovery experiment, not a capability-equivalent single-variable
claim. It started successfully: 1.85 GiB KV cache and 51,492 KV tokens per DP
engine, 1.57 nominal 32K concurrency, all 9 FULL decode graphs captured, both
API servers healthy.

All four quick32 cells completed 32/32 requests with zero errors and all 128
finish reasons were natural stop. TTFT/TPOT p50 in milliseconds were:

| concurrency | TTFT | TTFT vs original | TPOT | TPOT vs original |
|---:|---:|---:|---:|---:|
| 1 | 433.673 | 2.141x | 47.854 | 0.804x |
| 5 | 521.514 | 2.094x | 53.443 | 1.007x |
| 8 | 543.193 | 1.992x | 55.959 | 1.208x |
| 16 | 3510.405 | 0.591x | 62.782 | 1.287x |

Compared with the retained TP4 stack, TPOT regressed
65.96%/40.73%/26.76%/20.91%, and c16 TTFT regressed 291.81%. Aggregate
reference quality remained in the calibrated run-to-run band (raw exact
4/4/4/4, whitespace-normalized exact 5/6/6/6, normalized-character similarity
mean 0.15625/0.1875/0.1875/0.1875). Exact hash drift remains diagnostic; no
semantic promotion is needed because the performance and capability gates
already reject the candidate.

Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp2-dp2-prefetch0p1-text-ctx32k-bt8192-gmu0p95-fixedorig-npu4-7-20260905T024000Z`.
All SHA256SUMS entries verify; the SHA256SUMS digest is
`bf754de82f92bf22dc2988559524bae2335edf5df81fe906ba3a631090521d5e`.
The exact container exited 0. NPU4-7 are idle, and external NPU0-3 PIDs
1031654-1031657 are unchanged.

Authoritative decision: reject TP2/DP2 for both the 133K production contract
and the 32K conditional tier. Retain the 133K TP4/DP1 MMAR plus sub-cap
gate/up-prefetch-0.1 stack. Do not scan smaller batch-token values or lower
context again; the next loop must target the communication-dominated
MatMulAllReduce/row-parallel operator path while preserving the current
service contract.

## Final operator loop and handoff checkpoint

The remaining communication hypothesis was tested rather than inferred from
API wording. Official current CANN documentation describes MC2 as disabled for
incremental scenarios, but the exact vLLM-Ascend 0.23.0 stack uses fused MMAR
during decode. A new TP4 BF16 microbenchmark therefore compared fused MMAR
against separate MatMul plus AllReduce on physical NPU4-7 for the two profiled
Qwen3.5 decode projection shapes, M=1/2/4/6/8/10/12/14/16, with 20 warmups,
100 measured iterations and five alternating repeats.

Separate execution achieved only 0.469982x geometric-mean performance versus
fused MMAR, with a minimum of 0.367575x. In other words, fused MMAR is about
2.13x faster and there is no measured small-M bypass range. Retain fused MMAR.
Evidence and checksums are under:

/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/mmar-policy-bf16-tp4-npu4-7-20260905T031000Z

The next operator route integrated FlashComm2-style overlap into the retained
stack in a dedicated source worktree. Three signed-off source commits were
tested: initial Qwen3.5 projection selection, exclusion of linear_attn.out_proj,
and arbitrary-leading-rank flatten/restore. Every attempt failed at the same
torch.compile profile-run in qwen_gdn_linear_attn.py:342: a rank-1 destination
versus rank-3 source copy_ mismatch. No service reached readiness and no E2E
latency result is valid. This is an architecture-contract failure for the
hybrid self-attention/GDN model, not evidence against FlashComm2 generally.
Do not make another projection-local patch; a retry requires an architecture-aware
global TP padding and symbolic graph design.

Source worktree:

/cache/cch/.worktrees/exp-20260904-qwen35-flashcomm2-oproj-mmar-mlp

Branch and clean HEAD:

work/exp-20260904-qwen35-flashcomm2-oproj-mmar-mlp
e161bbff4f5064c87c8a2c4c6c6f412cc9805dd5

The final bounded parameter experiment changed only HCCL_BUFFSIZE from 512 to
1024 while retaining BF16 TP4/DP1, MMAR, gate/up prefetch 0.1, NZ1, async
scheduling, FULL_DECODE_ONLY, 133K context and no quantization. It completed
all 128 requests with zero errors and natural stops:

| concurrency | TTFT p50 ms | TPOT p50 ms | TTFT vs original | TPOT vs original |
|---:|---:|---:|---:|---:|
| 1 | 437.137 | 28.806 | 2.124x | 1.336x |
| 5 | 495.111 | 38.670 | 2.206x | 1.392x |
| 8 | 495.836 | 44.256 | 2.183x | 1.528x |
| 16 | 872.205 | 50.093 | 2.379x | 1.613x |

It improved both metrics only at c16 and regressed at least one metric at
c1/c5/c8 versus HCCL_BUFFSIZE=512. Reject it and retain 512. The evidence
root is:

/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-prefetch-0p1-hccl-buff1024-20260905T031500Z

### Retained production candidate

The retained non-quantized stack is BF16 TP4/DP1, MatMulAllReduce on, NZ1,
FlashComm1/2 off, async scheduling, FULL_DECODE_ONLY, HCCL_BUFFSIZE=512,
dense gate/up weight prefetch ratio 0.1, max model length 133000.

| concurrency | TTFT p50 ms | TTFT speedup | TPOT p50 ms | TPOT speedup |
|---:|---:|---:|---:|---:|
| 1 | 423.975 | 2.190x | 28.834 | 1.334x |
| 5 | 490.437 | 2.227x | 37.976 | 1.417x |
| 8 | 492.489 | 2.198x | 44.146 | 1.532x |
| 16 | 895.936 | 2.316x | 51.922 | 1.556x |

TTFT meets the 2x target in all four cells. TPOT remains open in all four
cells and must not be described as complete.

### Measured platform prerequisite

The decisive profile contains 13,696 MMAR calls over 107 decode steps, about
128 row-parallel MMAR calls per step. Summed operator time is 48.214% in
MatmulAllReduceMc2AicpuKernel, 23.504% in MatMulV2 and 16.616% in
MatmulAllReduce. Raw fused MMAR is already faster than the separate fallback,
so the missing TPOT gain cannot be obtained by toggling fusion off.

A further material TPOT step now requires one of the following, with a fresh
microbenchmark and E2E gate: an upstream architecture-aware implementation
that reduces or overlaps those 128 serialized row-parallel collective paths;
or a separately approved change to model architecture, precision, training,
or the 133K serving contract. None of those broader changes is authorized by
this workstream. Do not resume by scanning HCCL buffer sizes, smaller contexts,
static kernel, TASK_QUEUE_ENABLE=2, TP2 topologies, ngram speculation, or
projection-local FlashComm patches; each is already closed by evidence.

### Resume and rollback

Maintainer worktree:

/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e

Retained launcher mode:

mmar-on-weight-prefetch-gateup-0p1

Rollback to the original runtime by selecting the baseline launcher/config and
leaving source overlays disabled. Physical NPU4-7 are idle after the final
run. This work used only physical NPU4-7, mapped to logical 0-3 inside its
containers; no unscoped device was touched.
All new microbenchmark, FlashComm2 and HCCL1024 SHA256 manifests verify.

## FlashComm2 runtime recovery and final E2E decision

This supersedes the earlier startup-only conclusion without changing the
retained production stack. The first three source attempts correctly exposed a
hybrid-model graph-contract problem, but they were not the final feasibility
boundary.

The source branch was advanced through three bounded fixes:

- dc48edac flattened the all-to-all send buffer to match the one-dimensional
  receive buffer. Compilation passed, then FULL capture failed on a stale
  padding specialization.
- 5b334581 derived padding from the selected projection's actual input rows.
  Capture still failed because the Python conditional specialized the pad away.
- 65f780ee made projection-local padding symbolic and unconditional, sliced the
  output back to the unpadded row count, and restored arbitrary leading
  dimensions.

Commit 65f780ee passed 7/7 focused tests in the official vLLM-Ascend 0.23.0
image, reached health readiness, completed every configured FULL capture size,
and served 128/128 BF16 requests with zero errors and natural stops on physical
NPU4-7. This proves the implementation is runnable.

The four-cell E2E result nevertheless rejects it from the cumulative stack:

| Concurrency | FlashComm2 TTFT p50 | FlashComm2 TPOT p50 | TTFT vs retained | TPOT vs retained |
| --- | ---: | ---: | ---: | ---: |
| 1 | 446.049560 ms | 31.186542 ms | 5.2065% slower | 8.1591% slower |
| 5 | 529.244360 ms | 40.589775 ms | 7.9129% slower | 6.8814% slower |
| 8 | 538.441695 ms | 47.400653 ms | 9.3308% slower | 7.3732% slower |
| 16 | 949.527025 ms | 54.298669 ms | 5.9816% slower | 4.5764% slower |

Exact response hashes differ from the immutable original in 19/16/16/15 cases.
Because calibrated same-runtime controls also drift, this is recorded as
semantic-business-check-required rather than a proven numerical regression.
It does not block the performance rejection, and no correctness promotion is
claimed.

Evidence:

/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/flashcomm2-symbolicpad-oproj1-mmar-prefetch-0p1-20260905T043000Z

Candidate config SHA256:
5f3340843ba97397f5b92e77a4f0b90d6b61df92127a7ce7fbb6b6dfe5854d90

Candidate run SHA256:
b66421bcceed114fe4ac7d20e122a4f1070c66d61783485527e4aeb653786812

Decision SHA256:
a997750518e0d2ad50b2697017457be6fd414f6953a080b549fc51f08fb515fd

SHA256SUMS digest:
32d5a4d30844da7172d9d9d202c89b8f8f2f25df2271fbd36d978f4c7ca9bf18

Source worktree:

/cache/cch/.worktrees/exp-20260904-qwen35-flashcomm2-oproj-mmar-mlp

Source branch:

work/exp-20260904-qwen35-flashcomm2-oproj-mmar-mlp

Source HEAD:

65f780eeadfe9486ccc2eb0f6b7507e778e27da9

Final decision: keep FlashComm1/2 off and retain
mmar-on-weight-prefetch-gateup-0p1. TTFT remains above 2x in all cells; TPOT
remains open at 1.33425x-1.55639x.

## Decode MMAR + Add + RMSNorm fusion checkpoint

The next bounded operator candidate targets the measured structural bottleneck
directly: fuse each row-parallel `MatMulAllReduce` result with the following
residual add and GemmaRMSNorm. Qwen3.5 requires the effective RMS gamma to be
`1 + checkpoint weight`; the microbenchmark preserves that contract and does
not use quantization.

The official vLLM-Ascend 0.23.0 custom fusion is not the candidate: its pass is
disabled by default and hard-gated to compile ranges starting above 512, so it
cannot cover decode M=1-16. Source commit
`0af938b233b583e338d4587933e7c8ef494bd5b4` exposes CANN 9.1
`aclnnMatmulAllReduceAddRmsNorm` through a default-off custom binding.
Follow-up commit `4cc7cd7fb03b796fcd090a373b9c087f5ace8de5` adds the
symbolic Meta implementation required by graph compilation; its C++ object
compiled and the extension relinked successfully in operation
`exec-0000000000000acb`. The isolated source worktree is:

`/cache/cch/.worktrees/exp-20260905-qwen35-mmar-add-rmsnorm-vllm`

The pinned extension SHA256 is
`6006e113bf7f52ba5561d9847dbdcc6960b89eff56228d5ab584344719347d23`.
The first completed microbenchmark predates the Meta-only follow-up and used
commit `0af938b2` with extension SHA256
`80690af0f21d913e1a27f956883382ad02808ef718a20817672af929c5ea37e0`;
the eager runtime path is unchanged.

A first real TP4 run completed all 18 Qwen decode shape cells on physical
NPU4-7. Every cell was faster than the retained tail, with 1.833736x geometric
mean speedup and 1.639195x minimum speedup. This is a performance signal, not a
promotion: the first harness used standard-deviation-1 values for both matmul
operands. The resulting large BF16 accumulation magnitude caused several
`add_out` comparisons to fail even though normalized-output maximum absolute
error stayed at or below 0.046875. Its immutable evidence is:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/mmar-add-rmsnorm-bf16-tp4-npu4-7-20260905T052100Z`

Result SHA256 is
`04f0da791e526a943f8293be2df2549591cc50e4fb12989f9598b79231e85388`;
SHA256SUMS digest is
`d0e3a600ec35c2b892d434ae1c3df8fddcbb09d27385513df683de13d806ad42`.

The harness now matches the official operator sample's model-like 0.1 input
scale. That rerun has not completed: after the first run, external container
`p0_aff` started a Qwen3.8-27B TP4 service and explicitly reserved
`/dev/davinci4..7`. Two later attempts failed in `aclInit` with Resource_Busy
before any candidate measurement. The user has confirmed that physical NPU4-7
are assigned to this optimization, but `p0_aff` is actively executing another
profiling/benchmark sequence on those cards; do not interrupt an active run
without explicit coordination. Container-device reservation guards now protect
both the microbenchmark and main E2E launchers because `npu-smi` can briefly
show no process while a container is initializing.

Resume only when both the container reservation check and `npu-smi` report
NPU4-7 free. Run the corrected microbenchmark into a new immutable directory.
Promote to model integration only if both outputs pass in every cell, geometric
mean speedup is at least 1.02, and no cell regresses. Until that happens, the
retained E2E stack and all reported TTFT/TPOT values remain unchanged; the 2x
TPOT goal is still open.

## Decode fused-tail promotion and current queue state

This supersedes the preceding checkpoint. The corrected physical-NPU4-7 TP4
BF16 run passed both outputs in all 18 shape/batch cells. Geometric-mean speedup
is 1.851721x and the slowest cell still improves by 1.706554x. Evidence:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/mmar-add-rmsnorm-bf16-tp4-npu4-7-corrected-meta-20260905T054401Z`

Result SHA256 is
`0dfe46d44c907e513e8fa2a0a6bc48e2c26c39fc981bfe30cc5f2fa29cb2d8ac`.
SHA256SUMS digest is
`b26ff6be069bb74c9eb278cdc9fa39ad5298ec7668a4ebfb8ea90c392573062e`.

Source HEAD `369bd1f627be033c3d4de162cf5e7f5c8b6453b2` adds the
default-off `ascend_compilation_config.fuse_decode_mmar_add_rmsnorm` pass. It
is restricted to non-sequence-parallel compile ranges from 1 through 16 tokens.
The candidate explicitly sets compile range endpoints `[16,32768]`; without
that split vLLM 0.23.0 creates one `(1,32768)` range and the guarded pass would
correctly remain inactive.
The pass intentionally skips `BasePattern.register()` so it is not also
installed as an unscoped process-wide npugraph replacement.
Launcher mode `mmar-on-weight-prefetch-gateup-0p1-fused-tail` pins the source,
extension and kernel hashes and overlays them read-only on the official 0.23.0
image. Roll back by selecting `mmar-on-weight-prefetch-gateup-0p1`.

The first E2E attempt (`exec-0000000000000b07`) correctly exited 48 before
launch because `p0_ck` began a separate three-point chunk sweep on NPU4-7 after
the microbenchmark finished. Do not stop it. Retry the frozen c1/c5/c8/c16 run
in a new immutable output directory when that sweep releases NPU4-7. Runtime
graph-match, service correctness, E2E latency and candidate profiling are still
open, so the retained stack and the TPOT decision have not changed yet.

## First live-graph rejection and matcher correction

The queued E2E launch proceeded after 'p0_ck' naturally completed. Operation
'exec-0000000000000b2d' loaded the pinned extension, kept quantization disabled,
and proved that vLLM created compile ranges '(1,16)' and '(17,32768)'. It did
not prove operator integration: both the saved 'computation_graph.py' and final
AOT binary contained zero
'npu_matmul_all_reduce_add_rms_norm' occurrences while the separate MMAR and
AddRMSNorm operators remained. The exact task container was stopped during c1
to avoid wasting the assigned cards. The orchestrator finalized the partial
matrix as 'reject-runtime-failure'; none of its latency is promotion evidence.

Immutable failure evidence:

'/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-20260905T063300Z'

Decision SHA256:
'4a181470e6083da0f0386bb62cfef00500a25cc7dd86fd8ea4ddff1cc9e57256'

Service-log SHA256:
'1be97aa2ca6eb56077be30f60d6bb81bb49b448e0ead0e52940318888cbd9869'

SHA256SUMS digest:
'8a35d576a6a7063ff29a7be442ed24c76804ef32dc728834c3681629d2075f35'

The saved live FX graph exposed the exact mismatch. Production
'MatmulAllreduceRowParallelOp' leaves 'reduce_op' at the torch_npu wrapper
default and records only 'bias=None'; the candidate pattern explicitly supplied
'reduce_op="sum"'. Inductor treats kwargs as pattern structure, so it could not
match. Source commit '5182fe9cbed58faa480a24cce3a439a7fada3767'
removes the redundant kwarg, adds compile-range applicability logging, and is
now pinned by launcher commit '0a687d85752bbd0b66885cf6f7f26cd86bdfefa1'.
Static compilation, launcher guards and YAML parsing pass.

The immediate retry ('exec-0000000000000b45') was again rejected before launch
because external container 'p0_cd' started a bounded cadence sweep on NPU4-7.
Do not stop it. Its parent is '/cache/austinov/p0/cadence.sh'; it tests 16384
and 32768, writes 'CADENCE_DONE', and removes its own container. Resume into a
new output root only after that parent exits, the marker exists, and NPU4-7
have no processes. Before allowing the four-cell matrix to continue, require a
positive fused-op count in the generated AOT; otherwise stop only the exact
task container, preserve diagnostics, and iterate again.

## Second live-graph rejection and dispatcher-target correction

After 'p0_cd' naturally completed, operation
'exec-0000000000000b53' launched the second live-graph attempt as
'fused-tail-v2-20260905T070801Z' on physical NPU4-7. The official v0.23.0
image loaded BF16 TP4 with quantization disabled, the pinned flag enabled, and
compile ranges '(1,16)' and '(17,32768)'. Both ranges compiled, but the
rank-0 computation graph still contained zero fused operators, 704 direct MMAR
occurrences and 767 AddRMSNorm occurrences. Counts across all four rank cache
trees were zero, 2816 and 3068 respectively. No benchmark result from this
attempt is valid. The exact task container was stopped before serving the
four-cell matrix.

Immutable diagnostic record:

'/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v2-20260905T070801Z/integration-check.json'

SHA256:
'643b6c2083432929f281e45f010ed9af2cb06e4925b6acc11b804dc05efee5f6'

The saved graph confirms the production target is the dispatcher node
'torch.ops.npu.npu_mm_all_reduce_base(..., bias=None)'. Source commit
'c36980d335d1f493cba824e489dd4828218a5f99' now registers the pattern against
that exact dispatcher op rather than the 'torch_npu' Python wrapper. It also
logs pass configuration and registration, in addition to range applicability
and final match count, so the next run can distinguish disabled pass,
registration mismatch and a zero-match graph. Static compilation, launcher
guards, YAML parsing and diff checks pass. Maintainer pin commit
'7b809a11b026f72c597bd296ba7f20b439d838a4' selects this source.

A new external container 'p0_hc' then reserved '/dev/davinci4..7' for a bounded
HCCL default/AIV comparison. Do not stop or modify it. Watcher
'exec-0000000000000b79' waits for its parent to exit and for
'HCCL_AB2_DONE' in '/cache/austinov/p0/hccl_ab2.log'. Only after both are true
and NPU4-7 have no process should the dispatcher-target candidate be relaunched
into a new immutable output root. Require positive configuration,
registration, '(1,16) applicable=True', '(17,32768) applicable=False' and
fused-op-count evidence before accepting any latency.

## Third activation, fourth E2E, profile, and v5 resume point

The dispatcher-target correction alone was not the last activation fix. Source
`8c7f7d03e92a177d9c0678b993ece5ac9f5f2254` also wires the default
`enable_npugraph_ex` dispatcher path through `GraphFusionPassManager`. The v3
live graph then reported 64 fused decode MMAR+Add+RMSNorm patterns on every TP
rank in compile range `(1,16)`; `(17,32768)` remained intentionally
inapplicable. Integration-check SHA256 is
`a00c7be3c48fe823fb7c49455394e2dbe07cb0a09f934f9f171738f441a1716a`.

Operation `exec-0000000000000ba3` completed the frozen v4 c1/c5/c8/c16 matrix
with 32/32 requests, zero errors and natural stops in every cell:

| Concurrency | TTFT p50 | TPOT p50 | TTFT vs original | TPOT vs original |
| --- | ---: | ---: | ---: | ---: |
| 1 | 427.284340 ms | 30.663734 ms | 2.172625x | 1.254636x |
| 5 | 504.170205 ms | 40.364770 ms | 2.166462x | 1.333615x |
| 8 | 514.147375 ms | 48.704635 ms | 2.105061x | 1.388304x |
| 16 | 718.708065 ms | 49.311666 ms | 2.887223x | 1.638793x |

This proves real E2E integration but rejects v4 on performance: TPOT misses 2x
in all four cells and c1/c5/c8 TPOT is worse than the retained cumulative
stack. Cross-run exact hashes still require semantic business review if a
future candidate is promoted; calibrated same-runtime controls also drift, so
hashes alone are not a proven semantic regression. Evidence root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v4-20260905T075844Z`

Decision SHA256 is
`9dc31fa5bfa08ec00c839ac8b5a12493df787ae036eede971389ab719a3dff49`;
SHA256SUMS digest is
`2ca1afa9c590031a118ee026849bde03000109decdabf3cf890d7630ca33cb73`.

The follow-up TP0 dynamic msprof (`exec-0000000000000bbb`) explains why the
1.85x isolated tail microbenchmark did not transfer fully. One real request
recorded 6720 fused kernels but also 6976 unfused MMAR and 6976 standalone
AddRmsNormBias calls. The saved graph showed that MLP-down tails were direct,
while attention tails copied the full MMAR output into a preallocated tensor
before the residual/RMS consumers. Collective kernels account for 66.4559% and
matmul for 23.2408% of summed kernel duration. These sums are diagnostic only,
not wall time. The exported op_summary SHA256 is
`3ead56d434d43e5fe4e94cf29494de6231c544463938812b89c1c9c1d166c744`.

Source HEAD `081953bd1ee1e897f03fb31c6223bb00608773fd` safely normalizes only
full-shape attention MMAR copies whose destination has no unrelated consumer,
allowing those tails to reach the existing fusion. Focused tests in the
official 0.23.0 image passed 3/3 in 16.05 seconds; py_compile and diff checks
passed. The patch is Python-only, so the extension remains
`6006e113bf7f52ba5561d9847dbdcc6960b89eff56228d5ab584344719347d23`
and the kernel library remains
`6a9fc72a66a6055eb522a251fa48632b0ba257f22fb8f91a2deedc05e03e8b6a`.
Maintainer commit `77aec0a685b2b450f3da2704eea5c692455c172d` pins this source.

The first v5 launch attempt (`exec-0000000000000bf3`) was correctly rejected
with exit 48 before Docker launch because `p0_pw` began a real workload and
reserved `/dev/davinci4..7`. Do not stop it. Do not reuse the already-created
`mmar-add-rmsnorm-v5-20260905T084211Z` output root. When `p0_pw` naturally
exits, recheck Docker reservations and `npu-smi`, generate a fresh run ID/root,
and launch `mmar-on-weight-prefetch-gateup-0p1-fused-tail`. Require 128 fused
patterns per rank in `(1,16)` before accepting any c1/c5/c8/c16 latency. Keep
NPU0-3 untouched.

## Fifth live compile rejection and GraphModule contract fix

After the first `p0_pw` run naturally released NPU4-7, operation
`exec-0000000000000c25` launched
`fused-tail-v5-20260905T091405Z` on physical NPU4-7. The model loaded in BF16
with quantization disabled, but compilation failed before readiness. The
npugraph_ex hook passes a `torch.fx.GraphModule` (display name `<lambda>`) to
the range-scoped pass; the attention-copy normalizer had only been tested with
a direct `torch.fx.Graph` and accessed `.nodes` on the module. No query_rewrite
benchmark request ran, so this attempt is integration-failure evidence only.

Immutable evidence root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v5-20260905T091405Z`

Service-log SHA256:
`6c52ea291d4f7e11ac3ddb1591426235b0d9f891d1611b4f12f0bcaf7e1e7de3`.

Source commit `c5496ef722b48bb00627efddcb47ef7497292b2a` now accepts either
`Graph` or `GraphModule` and mutates the module's underlying `.graph`.
The official vLLM-Ascend 0.23.0 image passed 4/4 focused tests in 8.84 seconds,
including the exact GraphModule input case; py_compile and diff checks pass.
The patch is Python-only, so both pinned binary hashes are unchanged.

A new external `p0_pw` container `f18fbb8ba358` started at 09:23 and currently
owns physical NPU4-7. Do not stop or modify it. When it exits naturally, verify
container reservations, `npu-smi` and port 10010, then launch source
`c5496ef7` into another fresh immutable root. Require 64 normalized attention
copies and 128 fused patterns per TP rank in `(1,16)`; require
`(17,32768) applicable=False`; only then accept the frozen c1/c5/c8/c16
latency matrix. NPU0-3 must remain untouched.

## Sixth live activation rejection and post-export copy fix

After `p0_pf` completed both profiler stages with `TRACE_OK` and
`PWPROF_DONE`, operation `exec-0000000000000c81` launched
`fused-tail-v8-20260905T102046Z` on physical NPU4-7. Source `c5496ef7`
compiled without the prior GraphModule exception and the large range correctly
reported `(17,32768) applicable=False`. However, every TP rank reported
`Normalized 0` and only `Fused 64` for `(1,16)`. The exact task container
was stopped before readiness and before any query_rewrite benchmark traffic.

Immutable evidence root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v8-20260905T102046Z`

Service-log SHA256:
`cd3efc93bac855c1e04244ac97193b41a947edcafbfe090e909f98d9a76253b1`.

A minimal official-image reproduction exposed the second contract mismatch:
`output[:n] = value` is `operator.setitem` in the Dynamo graph, but becomes
`aten.slice.Tensor` plus `aten.copy_.default` after export; a direct full
assignment becomes `aten.copy_.default`. Source commit
`573ea2940bdc546923c698de16ea49465e6976f5` now handles both exported forms,
requires full destination/value shape equality, rejects partial first-axis
slices, and still accepts both Graph and GraphModule inputs. The minimal
official vLLM-Ascend 0.23.0 overlay passed 7/7 focused tests in 8.52 seconds;
py_compile and diff checks pass. The Python-only change leaves both pinned
binary hashes unchanged.

The next live v9 run is queued behind external `p0_ov`, which owns NPU4-7 for
a bounded four-configuration/two-repeat overlap A/B chain. A second bounded
`mc2` chain is already waiting behind it. Do not stop or modify either chain.
Wait for `OVERLAP_AB_DONE` and `MC2_AB_DONE`, then recheck container
reservations, the NPU process table and port 10010. Launch a fresh immutable
root with source `573ea294`; require 64 normalized copies plus 128 fused
patterns per rank before accepting correctness or latency. NPU0-3 remain
strictly out of scope.

## Guarded v9 queue

The user reconfirmed that physical NPU4-7 are assigned to this optimization;
physical NPU0-3 remain out of scope. Maintainer commit
`a0231e958c1106a2e0a500e0991a12ff6bb2ec83` adds the tested queue entry point
`scripts/queue_qwen35_fused_tail_v9.sh`. Its focused shell test passes. The
queue requires both external completion markers and then four consecutive
15-second checks showing no NPU4-7 container reservation, no NPU4-7 process and
no listener on port 10010. It finally invokes the existing launcher, which
repeats its own reservation and process guards.

The direct AgentWeb manager restarted after operation
`exec-0000000000000cbb` was armed. Its journal then returned
`operation_not_found`; an exact process check found no queue or candidate
launcher, and no v9 output root had been created. External `p0_ov` still owned
NPU4-7, so this was a lost waiter rather than a partial candidate launch.

Recovery operation `exec-0000000000000004` is now the one active queue. It
was started only after a second exact duplicate check and is confirmed
running without NPU allocation. Poll this operation and do not launch another
v9 queue. At recovery time neither completion marker was present and
`overlap_ab` was still on its sequence-parallel configuration.

## Docker reservation guard correction

A live fail-closed probe on 2026-09-05 found that this host's Docker CLI parses
`docker inspect ID --format TEMPLATE` incorrectly: it treats the template as
another object. The earlier shell mocks had accepted that order, so the
waiting v9 queue and its service launcher would have failed after the external
chain completed. The queue, service launcher and fused-tail microbenchmark now
use `docker inspect --format TEMPLATE ID`, and the mock reproduces that live
contract. Focused queue/launcher tests and MST validation pass; a real probe
then detected `/p0_mc` and exited 48 without creating a task directory or
container.

Operation `exec-0000000000000004` captured the old function definitions.
Its exact waiter PID 283507 was verified and terminated before the MC2 marker
existed; no v9 candidate container or output root existed. Exactly one
corrected queue is now active as operation `exec-0000000000000060`, PID
579462. It is confirmed running without NPU allocation. Poll operation 0060
and do not launch another v9 queue.

The v9 E2E path now has a pre-traffic positive activation gate. It snapshots
the live log and requires exactly four rank observations for each of:
`(1, 16) applicable=True`, `Normalized 64`, `Fused 128`, and
`(17, 32768) applicable=False`. Any mismatch exits 72 before query traffic
and preserves `integration-check.json`, its source log, and hashes.

## v9 rejection, symbolic full-slice fix, and v10 resume point

Corrected queue operation `exec-0000000000000060` waited for both prior
external chains and four stable idle checks, then launched exactly one v9
container on physical NPU4-7 at 2026-09-05T12:50:17Z. The service loaded the
BF16 model with `quantization=None` and compiled both intended ranges.
Every TP rank reported `(1,16) applicable=True`, `Normalized 0`, and
`Fused 64`; all four also reported `(17,32768) applicable=False`.

The positive activation gate rejected the run with exit 72 before any
query_rewrite benchmark request. The exact container then exited and no
candidate cell or decision file was created. Immutable evidence root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v9-20260905T125017Z`

The integration-check SHA256 is
`246c0328669486df48968fc2bba137a26b70bda498bbc35e151d873b14b90cf0`;
the snapshotted service log SHA256 is
`6a51f35128178a9981f68dc39ea7fb9049f58bee40199bc5779898da00368d62`.
This is an integration rejection, not latency evidence, and the retained
stack remains unchanged.

Source inspection showed that the exported open-ended `output[:]` copy can
carry different symbolic names for the destination, slice, and MMAR first
dimension. Source commit
`4424cc24ecfa355ce2b17ab48e04fb6fc4944e39` accepts that case only when it
is an open-ended axis-0 slice, ranks and trailing dimensions match, and all
semantic destination users are the expected residual/RMS tail. A bounded
slice with different symbolic first dimensions is still rejected. The Python
files pass `py_compile` and `git diff --check`. The exact 0.23.0 image now
passes all 9 focused fusion-pass tests with device-backend autoload disabled
and the image's `torch_npu/dynamo` compatibility package on `PYTHONPATH`;
this includes the new symbolic-open-slice acceptance and bounded-slice
rejection cases without allocating an NPU. The unchanged extension and kernel
hashes remain pinned.

The v10 launcher pin, resource queue and shell mocks pass. The first launch,
`exec-00000000000000e6`, was submitted with a 30-second synchronous wait and
terminated on that tool timeout without leaving a host waiter or allocating an
NPU. Exactly one replacement operation,
`exec-00000000000000f7`, remains active in the asynchronous job lane.
`p0_r15` completed after both FlashComm2 startup attempts failed the runtime
constraint that parallel size 4 cannot equal/exceed global TP4, then wrote
`R15_DONE`. The v10 queue observed that marker, passed all four stable idle
checks, and launched
`mmar-add-rmsnorm-v10-20260905T135044Z` on physical NPU4-7. By
2026-09-05T13:53:31Z all four TP workers had loaded 12.8735 GB of BF16 weights
each with `quantization=None`; service readiness, the 64-normalized/128-fused
activation gate, correctness and benchmark traffic are still pending. Poll
operation f7 and do not start another v10 queue. A ShortGPT
diagnostic launch attempt `exec-00000000000000c8` was independently rejected
with exit 48 before Docker because `p0_r15` reserved NPU4-7; its empty output
root is not evidence and must not be reused. Run v10 first. Only if all four
ranks report `Normalized 64 / Fused 128` may benchmark traffic begin. After
v10 terminates, resume the separate ShortGPT workstream on the same guarded
resource set. Its source is pinned at
`54a6bb40ac83771538b3c859bcf9c55e2e51854a`: the diagnostic now samples both
the prompt head and tail and obtains rank zero from the initialized distributed
process group before falling back to launcher variables, avoiding shared-prefix
and duplicate-TP-rank bias. The ShortGPT maintainer workstream checkpoint is
`7ca6b5ed9c73c5e0762652be4d1d525f6dffe15a`. The exact 0.23.0 image passes
all 9 focused source tests with device-backend autoload disabled, and a separate
direct-module runtime smoke passes head/tail sampling, identity influence,
JSONL output, and distributed-rank precedence without allocating an NPU.
Real NPU BI collection remains the integration gate after v10 releases physical
NPU4-7.

That handoff is now executable without a scheduling gap: the only ShortGPT BI
waiter is asynchronous operation `exec-0000000000000131`, host PID
`1474376`. It is bound to the live v10 PID `1298706` and Linux start tick
`115030322`; it requires `R15_DONE`, exact predecessor termination, and four
stable Docker/`npu-smi`/port-10020 idle checks before starting a fresh BI
root. Poll it after v10 and never start a duplicate.

## v10 terminal evidence and live ShortGPT BI

This section supersedes the pending-state sentences immediately above.
Operation `exec-00000000000000f7` is terminal with exit 72. The real BF16,
non-quantized TP4 service reached the positive activation gate on assigned
physical NPU4-7, but every rank reported `(1,16) applicable=True`,
`Normalized 0`, and `Fused 64`, instead of the required 64 normalized copies
and 128 fused tails per rank. Every rank correctly kept `(17,32768)`
inapplicable. The gate sent zero query_rewrite requests, so there is no v10
latency matrix and the retained stack is unchanged.

Immutable v10 evidence root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v10-20260905T135044Z`

Hashes:

- `integration-check.json`:
  `fe6b7c528bba5f50029590d753c563eb2f009e4548de90a980a8a3ebad7a8946`
- `service-before-benchmark.log`:
  `3c6c10e3524e1b9ddeee6d8fa60e95ca26f101ac5e4956d78b02bebe5b120820`
- preserved real rank-0 `computation_graph.py`:
  `74fd420a59549557ab632c9c42fe9d830b58a0c482fd1ee67546235c58f8aae7`
- `activation-SHA256SUMS`:
  `a11398e69832a5fdb799d03e5c17fb9f682a67a13c8d91f33ab0d690f2589108`

The 1,039,860-byte read-only graph copy is
`live-computation-graph-rank0.py` in that root. It proves the actual GDN and
full-attention MMAR destination topology and following residual/RMS users,
but it does not yet prove which matcher guard rejected the second 64 tails.
Do not patch that path by inference alone and do not relaunch v10 unchanged.

The only current accelerator job is serialized ShortGPT BI operation
`exec-0000000000000131`, using fresh root
`/cache/austinov/eval-runs/exp-20260905-qwen35-shortgpt/bi-20260905T135854Z`.
It passed the predecessor and four-observation idle gates, then started one
BF16, non-quantized eager TP4 service on physical NPU4-7. Rank 0 emitted 64
startup BI observations during model initialization; the runner is designed
to move those aside after readiness and collect a fresh deterministic
32-prompt sample before analysis. Poll this operation only. If analysis
passes its coverage and rank-stability gates, freeze one layer set, launch a
fresh retained-stack semantic control first, and only then run correctness
plus the fixed c1/c5/c8/c16 query_rewrite matrix.

## ShortGPT terminal decision and v11 diagnostics queue

The ShortGPT paragraph above is historical. BI completed with all 64 layers,
2,048 formal observations, and minimum four-split Spearman
`0.9989926739926738`. The unpruned same-runtime control completed 128/128
requests. Frozen remove8 operation `exec-0000000000000195` also completed
128/128 requests and improved retained TPOT in every concurrency cell, but
c1/c8/c16 each lost `0.03125` mean normalized character similarity versus
control, exceeding the frozen `0.02` threshold. Its decision is
`hold-semantic-quality-regression`; it is not in the retained stack and
remove16/remove20 are forbidden. Evidence and hashes are in the separate
`exp-20260905-qwen35-shortgpt` workstream at maintainer checkpoint
`3680183`.

Operator source `5816eff11812fd9d54a1b433ca3d5ee1aad490f3`
adds rejection diagnostics only; fusion semantics and the M<=16 guard are
unchanged. The exact 0.23.0 image passes 9/9 focused tests. The launcher can
pin this explicit commit, and the generalized queue-label path plus resource
guards pass their shell tests.

Direct v11 attempt `exec-00000000000001ed` exited 48 before Docker creation
because protected `/p0_r16` already reserved physical NPU4-7. Exactly one
replacement queue, `exec-00000000000001fe`, now waits for
`/cache/austinov/p0/r16.log` to contain `R16_DONE`, then requires four
stable Docker/NPU/port-10010 idle observations. It will launch immutable root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v11-diagnostics-20260905T145100Z`

The unchanged positive gate still requires Normalized 64 and Fused 128 per
rank and rejects before query traffic otherwise. Poll operation 01fe only;
do not interrupt `p0_r16`, do not start another v11 queue, and do not touch
NPU0-3.

## v11/v12 terminal diagnosis and live v13

The v11 diagnostics queue is terminal with exit 72 before query traffic.
Each rank saw 128 MMAR nodes and 64 `aten.copy.default` nodes, but no copy
candidate under the old mutable-copy matcher. Immutable root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v11-diagnostics-20260905T145100Z`

Its integration-check, snapshotted service log and activation-manifest
SHA256 values are respectively
`4842411703e5dfb0ea4b77934b14ce5c109a6654b785a20a914c3febd96dcc66`,
`93795ca2b55b137540ac6a0cebdbf511d0051a5e27fdbe4ee7fc71f4ec4e535e`
and
`fb855dcb22a3571376a82cde43cb3297dc127438c4cdcd69662dc1f7ee992cab`.

Source `91602b1a21dc17ede35223d6ab91367b38ff0cfa` recognized functional
copy nodes and passed 11/11 focused tests, but real v12 then proved the next
guard: all 64 candidates per rank were rejected as unrelated users. v12 is
terminal exit 72 with zero query traffic at:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v12-functional-copy-20260905T154011Z`

The v12 integration-check, service snapshot and activation-manifest SHA256
values are
`7036fcff2d8fe1255546178d0aee05f0df027fbbedf341157751554ae0bedb50`,
`93c0e53d32e3b06476d36460cccdd946373e2dbe330a654a10d88284a974c793`
and
`f76de4238299f45c1a93e3a52aa3abe25caec29be261b07abe1575f6ef07918f`.

The preserved Dynamo graph and the v12 counters establish the real
functionalized chain as `slice -> copy -> slice_scatter`. Source
`d0c0fbd69ca1d19c8f5910f9ece8a5a9fbb65ef8` handles that bookkeeping
only for one full-shape axis-0 update with the expected residual/RMS semantic
users. Py-compile, diff checks and all 11 exact-image tests pass. Maintainer
commit `d7a91f2a6f7a66157ee2a675042374cd2266a682` pins it.

An unrelated `p0_r17` auxiliary sweep attempted invalid
`commTurn=4/8/16`; CANN requires zero in this topology. Its retry loop was
stopped by exact process group and container after the first decisive error.
The container remains recoverable as `Exited (137)`; nothing was deleted.

Exactly one v13 operation, `exec-00000000000002cb`, is active on physical
NPU4-7. It launched at 2026-09-05T15:52:44Z into:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v13-slice-scatter-20260905T155244Z`

Poll operation 02cb only. Do not launch a duplicate and do not touch NPU0-3.
The launcher must observe Normalized 64 and Fused 128 on all four ranks before
it sends any c1/c5/c8/c16 query_rewrite traffic.

## v13-v17 terminal fused-tail decision

The v13 paragraph above is historical. Operations v13 through v16 all ended
at the positive activation gate without sending query traffic. v13 and v14
remained at Normalized 0/Fused 64 per rank. Source
`9f99ed9d89e14e33129e071e1f245067db70cd73` added detach traversal and
v15 reached Normalized 48/Fused 112. The stricter nested-replay source
`4cde6b28bdffa0b3daffef1dd4512ef6cd5ee4d5` retained that coverage in
v16; bounded diagnostics proved the last 16 copies are dependency-ordered
functional updates, not ordinary transparent view bookkeeping.

The evidence SHA256 triples
`integration-check/service-before-benchmark/activation-SHA256SUMS` are:

- v13: `e25a42422904cc6fe7d407fd44b957dc973cd307e92fbdb0ae7294880e1ef272` /
  `3dfe2b59769a1be93382ba5614765665c4cf30b1fc9bb85f7ed96f1f2d4a0cf2` /
  `6e481578dfbd4ef5980def9c61da7b61388e5228a5d6e829fd347e4e4e50d70b`
- v14: `2a1ac932a8b2c1e397acfe518e33e0c47697e8cb2b6aca7f70e111c6c6ca7834` /
  `af0705df0be70d0a1ef4efbfc4c2361068fb295fcfed1a155b35111f72cf323c` /
  `555a2295f85301dc6e3d981730ae2e5a4e1728520a1253d66affa62b66d2ffbe`
- v15: `f6f1d9d19512cd6991c86f146673c369602be35a20f429350db3b2170b289116` /
  `19eaa809aa40ca2ddd36ac7269f4965bb8cc516fbb78b0e25cde599ccf82991f` /
  `9bbb9e63569ca5b52b8dd21ef6132171b9ccc7766c6d7cf011823f873e597b66`
- v16: `a24baeb15cd9dca8a098029e341917d4f5b136ccc81b8046fc4c1c0ceca8595b` /
  `5dda5f60b46f30fca8377e386b3a987b470358966c04675df12b6a01352b6cc6` /
  `5a4eda6bc00cba252004bd96a69aaa3d3e718ca62ea86d1bb24b6bbbac9e5c90`

v17 deliberately lowered the gate to the proven partial coverage and then
completed the real frozen query_rewrite matrix on BF16 TP4 physical NPU4-7:

| Concurrency | Candidate TTFT/TPOT ms | Versus original | Versus retained |
|---:|---:|---:|---:|
| 1 | 449.154935 / 31.077882 | 2.066834x / 1.237916x | 5.94% / 7.78% slower |
| 5 | 509.351810 / 39.713187 | 2.144423x / 1.355495x | 3.86% / 4.57% slower |
| 8 | 537.380605 / 46.910598 | 2.014050x / 1.441398x | 9.12% / 6.26% slower |
| 16 | 988.995720 / 55.591584 | 2.098159x / 1.453666x | 10.39% / 7.07% slower |

All 128 requests completed with zero runtime errors, and all four ranks
reported Normalized 48/Fused 112. Nevertheless both metrics regress versus
the retained stack in every cell, so the maintainer decision is
`reject-performance`. The analyzer's `hold-exact-hash-drift` output is
not the final stack decision: the fixed-runtime control already established
that cross-run hashes drift and require a same-runtime semantic review, while
the all-cell performance regression is independently decisive.

Immutable v17 root:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-add-rmsnorm-v17-partial-e2e-20260905T164000Z`

Key hashes are integration
`200a3892a4a56ee8cf701b03a26e6a8759bf1a87a5ec568a9e767927727c09ae`,
service snapshot
`e50cc4c423a02fbf4ba97fcd60457483af1ce9ea4154cf9e778b88fe152d1d1c`,
candidate-run
`9fb8bcbc04c0a9c1bdaec6522a728e56c4d7b84ac14a6b5843513e23f9281673`
and decision
`0a09bcabfad414e6825b51f1c0e2c7bde5757bccc142f8398c61ef5faa288416`.
The exact v17 container exited 0 and physical NPU4-7 are idle. The
pre-existing VLLM workers on NPU0-3 were not touched.

The retained result is unchanged: TTFT 2.1896x/2.2271x/2.1976x/2.3161x and
TPOT 1.3343x/1.4175x/1.5317x/1.5564x versus original at c1/c5/c8/c16.
Do not relaunch partial fused-tail or widen its final dependency chain without
a new whole-model economic argument. Select the next TPOT treatment from the
retained profile's dominant collective/matmul cost and the operator assets
under `/cache/cch`, use only physical NPU4-7, and preserve NPU0-3.

## FlashComm1 GDN shape repair and terminal v3 decision

FlashComm1 was revisited because the retained profile attributes most summed
kernel duration to communication. The work was isolated in
/cache/cch/.worktrees/exp-20260905-qwen35-flashcomm1-gdn-shape.
Three DCO commits make the implementation testable on vLLM-Ascend 0.23.0:

- 68683e2b7c0eb47bbb49685ed079b49003a13189 sizes the GDN output copy for
  a sequence-parallel destination.
- faed93717a61003cc2daf0abdbffdd61981a4bac makes SequenceRowParallelOp
  take precedence over MMAR when FlashComm1 is enabled.
- dc7ebdd55421d543e2e87398c2d601742d4a8336 keeps dense FlashComm1 enabled
  for every non-empty batch, avoiding profile/capture/replay shape changes.

The exact release image passed all 30 focused CPU tests. Real v1
exec-0000000000000367 exposed the selector-precedence bug before traffic.
Real v2 exec-0000000000000378 then exposed the num_tokens > 1000 threshold
mismatch during 16-token graph capture. Neither attempt produced performance
evidence.

Real v3 exec-000000000000039d used BF16 TP4/DP1 on physical NPU4-7 only.
The log proves SequenceRowParallelOp for self-attention o_proj, GDN out_proj
and MLP down_proj, and FULL decode graph capture completed for 16/12/8/4
tokens. All 128 query_rewrite requests completed with zero errors and natural
stop:

| Concurrency | Candidate TTFT/TPOT ms | Versus original | Versus retained |
|---:|---:|---:|---:|
| 1 | 536.273185 / 36.193100 | 1.731074x / 1.062960x | 26.49% / 25.52% slower |
| 5 | 614.038010 / 44.613011 | 1.778824x / 1.206622x | 25.20% / 17.48% slower |
| 8 | 611.372915 / 50.434046 | 1.770297x / 1.340698x | 24.14% / 14.24% slower |
| 16 | 610.802965 / 59.312175 | 3.397283x / 1.362479x | 31.83% faster / 14.23% slower |

The terminal maintainer decision is reject-performance. The c16 TTFT gain is
real but cannot compensate for TPOT regression in every cell and TTFT
regression in c1/c5/c8. FlashComm1 therefore remains disabled in the retained
stack. The analyzer output hold-exact-hash-drift is not a promotion decision:
cross-run hashes already drift in the fixed-runtime control, while the
all-cell performance failure is independently decisive.

Immutable v3 root:

/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/flashcomm1-gdn-shape-mmar-prefetch-0p1-v3-20260905T172500Z

Key SHA256 values are candidate-run
948f864e4719b545371c5ae84686a798de07970ba96cf9d889089cce6d2b935b,
decision
f53d5ec404cd5c979a5a658ac2ad1b053781657fd0d631e4a3e4c34a8e1159df,
service log
e15c3fdaf381aa766628738486613a87557af874565015127905cf92e001fe38,
and manifest
6185e523604f88c282fa59d1b84491a2dcaf839b62d1dbe8b06985fcff75193d.
The exact v3 container exited 0, physical NPU4-7 are released, and NPU0-3
were untouched.

The retained result remains TTFT 2.1896x/2.2271x/2.1976x/2.3161x and TPOT
1.3343x/1.4175x/1.5317x/1.5564x versus original at c1/c5/c8/c16. Do not
relaunch FlashComm1 v1-v3 unchanged. A future sequence-parallel attempt must
first explain and remove the measured TPOT tax, then pass all four frozen
cells before it can replace the retained stack.

## MTP k=1 local-argmax readiness checkpoint

The next primary treatment is exact Qwen3.5 MTP speculative decoding with one
draft token, stacked on the retained BF16 TP4/DP1 MMAR, NZ1, dense gate/up
prefetch-0.1, async-scheduling and FULL_DECODE_ONLY configuration. It does not
use quantization or retraining. The additional local-argmax path is exact for
the frozen temperature-0 query_rewrite workload: each TP rank computes its
local vocabulary maximum, and only value/index pairs are reduced instead of
gathering the full draft logits. Target-model verification remains the
correctness authority.

The isolated vLLM-Ascend 0.23.0 source worktree is
`/cache/cch/.worktrees/exp-20260905-qwen35-mtp-local-argmax`, branch
`work/exp-20260905-qwen35-mtp-local-argmax`, exact clean DCO commit
`2d08abd56466360b56738d5c48858dc32ddd1f6b`, based on
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`. The change adds
`Qwen3_5MTP.get_top_tokens` by delegating to the model's existing
`LogitsProcessor` and `lm_head`. Py-compile and diff checks passed, and the
focused test in the exact release image passed 3 tests. The first whole-tree
image mount hid packaged build metadata and was an invalid test setup; the
corrected read-only file overlays passed. Ruff is absent from that image, so
no Ruff result is claimed. One push attempt to the public upstream returned
HTTP 403; do not retry unchanged. The local commit is the handoff authority.

The umbrella launcher now exposes `CANDIDATE_MODE=mtp-local-argmax`, pins the
exact source commit, mounts only `patch_qwen3_5.py` read-only, keeps the
retained stack, and supplies
`{"method":"mtp","num_speculative_tokens":1,"use_local_argmax_reduction":true}`.
Syntax, launcher guard tests, YAML parsing/assertions, maintainer skill-tree
validation and diff checks pass. The candidate remains default-off.

At 2026-09-05T18:15:51Z, `p0_r17` was authoritatively running with physical
NPU4-7 reserved; live VLLMWorker_TP processes used about 16.1 GB on each card.
Independent workloads were also live on NPU0-3. Do not stop `p0_r17` and
never touch NPU0-3. Before launching, prove that `p0_r17` is terminal,
NPU4-7 have no processes or competing container reservations, and port 10010
is free. Then run the fixed c1/c5/c8/c16 query_rewrite candidate against the
immutable original baseline, capturing local-argmax activation, draft and
accepted-token metrics, zero-error/natural-stop correctness, decision JSON,
hashes and final resource release. Promote only if all correctness gates pass
and the cumulative result improves the retained stack toward both 2x targets;
otherwise reject it and preserve the retained non-speculative configuration.

## User-authorized TP8/DP1 baseline reconstruction

The user corrected the comparison boundary: the historical production baseline
was TP8/DP1, not the later TP4/DP1 quick32 baseline. The user supplied the
effective vLLM 0.23.0 engine configuration and reported historical c1 TTFT near
139 ms and TPOT near 22 ms. Those historical numbers are context only until a
same-host, same-dataset run reproduces them.

The reconstructed baseline keeps BF16 and quantization=None, uses physical
NPU0-7 as TP8/PP1/DP1/DCP1, disables custom all-reduce and enables Ascend MMAR, keeps
prefix caching, chunked prefill, async scheduling, max model length 133000, and
uses FULL_DECODE_ONLY with compile endpoint 8096 and capture sizes
1/2/4/8/16/24/32. It runs 32 immutable query_rewrite requests at c1/c5/c8/c16
for three repetitions and records request throughput, output-token throughput,
TTFT, TPOT and E2E latency.

The user explicitly authorized pausing the occupied workloads to make all eight
cards available. `qwen36_hypic_nocache_baseline_npu0_3` had already exited;
`p0_r17` was stopped after preserving logs and container inspection under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/resource-handoffs/tp8-baseline-20260905T182200Z`.
The device process table then proved NPU0-7 idle. The final v5 baseline
container exited 0 at 2026-09-05T19:23:02Z, and device release was re-proven
before the comparable TP8 MTP candidate started.

The config and launch path are
`configs/qwen35-query-rewrite-tp8-user-baseline.yaml`,
`scripts/run_qwen35_tp8_user_baseline_service.sh`,
`scripts/run_qwen35_tp8_baseline_matrix.py`, and
`scripts/run_qwen35_tp8_user_baseline.sh`. The TP4/DP1 improvement ratios are
superseded as user-facing goal evidence. The repeated TP8 baseline is now the
immutable denominator.

The valid v5 evidence root is
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp8-user-baseline-v5-20260905T184600Z`;
`matrix/baseline-summary.json` has SHA256
`e3e03a5f1a5ce8d3e2d5f35ccf6a410d5d96555ad9012ba5881fd9227246639d`.
All 12 cells completed 32/32 requests with zero errors and natural stop:

| concurrency | TTFT p50 | TPOT p50 | E2E p50 | output tok/s |
|---:|---:|---:|---:|---:|
| 1 | 889.69 ms | 35.45 ms | 6620.61 ms | 25.27 |
| 5 | 1028.58 ms | 47.84 ms | 9466.04 ms | 72.59 |
| 8 | 1043.88 ms | 60.82 ms | 14191.70 ms | 79.13 |
| 16 | 1966.45 ms | 69.30 ms | 21638.61 ms | 112.98 |

The service log proves vLLM-Ascend 0.23.0, BF16, no quantization,
speculation disabled, TP8/PP1/DP1/DCP1, custom all-reduce disabled and Ascend
MatMulAllReduce enabled on all eight workers.

## MTP local-argmax v1 interrupted before traffic

The first physical-NPU attempt was
`exec-00000000000005c4`, with immutable output root
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mtp-local-argmax-k1-20260905T181915Z`.
It started only after `p0_r17`, the NPU process table, competing container
reservations and port 10010 were checked. Four workers appeared only on
physical NPU4-7; NPU0-3 had no candidate process.

Startup parsed MTP k=1 and `use_local_argmax_reduction=true`, resolved
`Qwen3_5MTP`, loaded the target and draft weights, wrapped the draft model
with the ACL graph wrapper, allocated the KV cache, and reached 5/9 decode
graph captures. Before readiness, Docker sent SIGTERM at 18:25:24Z and
SIGKILL 60 seconds later. The container exited 137 with
`OOMKilled=false`; the service log contains no Python or NPU traceback.
No request ran, no candidate-run or decision JSON exists, and the explicit
local-argmax runtime activation message was not reached. This is therefore an
invalid externally interrupted attempt, not an algorithm-performance result.
The preserved service log SHA256 is
`9d825a2bc5bebdb0852b81678d7f5edc7f2af3af38f713182d4de2b424a25776`.
The NPU process table subsequently proved the candidate workers were gone.

After v5 completed and released NPU0-7, the comparable TP8 retry started under
AgentWeb operation `exec-000000000000063a`. Its immutable output root is
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k1-20260905T192433Z`
and its exact container is
`qwen35_tp8_mtp_local_argmax_20260905T192433Z`. It changes only speculation
OFF to Qwen3.5 MTP k=1 with `use_local_argmax_reduction=true`; every other
baseline runtime and workload setting is preserved. It currently owns
physical NPU0-7. Do not stop or compete with it. Next, prove readiness,
eight-worker and local-argmax activation, then complete the repeated matrix,
correctness, speculative-acceptance, decision and artifact-hash gates.

## User-provided TP4/DP2 FULL_AND_PIECEWISE candidate

On 2026-09-06 the user supplied a previously explored configuration believed
to have some benefit. Its distinguishing runtime shape is TP4/DP2 across
physical NPU0-7, max_num_seqs 16, max_model_len 133000,
max_num_batched_tokens 32768, prefix caching, aligned BF16 Mamba caches,
async scheduling, CPU binding, and FULL_AND_PIECEWISE capture with the explicit
size list through 3584. The environment also includes HCCL_BUFFSIZE=512,
TASK_QUEUE_ENABLE=1, OMP_NUM_THREADS=1, OMP_PROC_BIND=false,
MatMulAllReduce enabled, and Triton dump/debug settings.

This is queued immediately after the active TP8 MTP k=3 experiment. It is a
candidate, not a replacement baseline, and must run the same immutable
query_rewrite c1/c5/c8/c16 repeated protocol against the original TP8/DP1
MTP-OFF denominator. Report latency and capacity separately because DP2
changes topology. MatMulAllReduce and several environment settings are already
present in the denominator, so any gain cannot be credited to them without an
ablation. Installed 0.23.0 source inspection found no reader for
VLLM_ASCEND_PTO_CHUNK_GDN; retain that variable only as historical provenance
unless runtime dispatch proves otherwise. Related FULL_AND_PIECEWISE attempts
have previously failed graph/startup gates, so this retry must fail closed and
preserve activation or failure evidence.

The currently active immutable k=3 evidence root is
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k3-v2-20260905T215000Z`.
It uses the already-ready TP8 service on NPU0-7 and operation
`exec-00000000000004b7`; do not edit its executing scripts or launch a
competing service.

## MTP k=3 screen rejection and TP4/DP2 recovery boundary

MTP local-argmax k=3 completed one full c1/c5/c8/c16 screen on physical
NPU0-7: 128/128 requests, zero errors and natural stop. Prometheus counters
record 19,571 accepted of 29,481 drafted tokens (66.39%), with accepted counts
8,103/6,477/4,991 at draft positions 0/1/2. The latency screen was:

| concurrency | TTFT ms | TTFT speedup | TPOT ms | TPOT speedup |
|---:|---:|---:|---:|---:|
| 1 | 1017.58 | 0.874x | 23.54 | 1.506x |
| 5 | 1263.15 | 0.814x | 43.46 | 1.101x |
| 8 | 1293.01 | 0.807x | 52.31 | 1.163x |
| 16 | 12866.99 | 0.153x | 215.67 | 0.321x |

The all-concurrency gate therefore rejects k=3 without two additional
repetitions. The exact benchmark PID and container were stopped through guarded
targets, and NPU0-7 were proven process-free afterward. Evidence root:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k3-v2-20260905T215000Z.
The screen-decision SHA256 is
6c8698f8a52c1db91f5062f781e085b85101d5372ea7bbf283c544ea9f25ec95.

The first exact user-config TP4/DP2 FULL_AND_PIECEWISE attempt used the legacy
run_qwen35_dp2tp4_baseline_service.sh path and failed before model load:
the architecture-inspection subprocess could not obtain the Ascend device
target. Preserve it as launcher failure, not performance evidence, under
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-dp2-fullpiece-user-20260905T220500Z.

Commit a625b2b integrates the same user stack as the default-off
tp4-dp2-fullpiece-user runtime role into the device-mapping launcher already
proven by TP8 and MTP. Syntax, YAML, diff and the 18-skill maintainer tree pass.
At 2026-09-05T22:10:07Z, p0_r19 was again running on NPU4-7 while NPU0-3
were idle. The resource guard correctly rejected the new eight-card launch.
Do not stop p0_r19 without renewed explicit approval. Once approved, start
the new role, pass readiness/graph activation, then run one c1/c5/c8/c16
screen before deciding whether two more repetitions are justified.

## NPU0-3 tail gate and external-draft recovery

The TP4/NPU0-3 baseline is frozen at
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp4dp1-npu03-ref-v1`.
For every c1/c5/c8/c16 cell, candidate decisions now require TTFT and TPOT
P50/P95/P99; median-only gains cannot promote a candidate. The static-kernel
plus HCCL 1024 screen completed 128/128 requests but was rejected because no
cell passed both metrics across all three percentiles, and TPOT P99 regressed
at c5/c8/c16. Decision SHA256:
`54c0b690ca3e2c53794457711fa2585d20797365133b17f13e3eb0e955f4fa0a`.

External Qwen3.5-4B draft attempt v1 is preserved under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-draft4b-k3-mmar-prefetch0p1-v1-20260906T0954Z`.
It failed before traffic because vLLM 0.23.0 rewrote an explicit Qwen3.5
`draft_model` into `qwen3_5_mtp`, then tried to load hidden-size 2560 draft
weights into hidden-size 5120 MTP tensors. This is an invalid startup-contract
run, not performance evidence. The service log SHA256 is
`56afd1627a698f60c5922330a2259fd78a1415794a72858cc727863d17f67393`.

The isolated vLLM worktree
`/cache/cch/.worktrees/exp-20260906-vllm-draft-model-contract-fix` at commit
`e132e799a681ed10160ed86dbd216ed6035e96dc` fixes only the explicit
`method=draft_model` branch; MTP behavior is unchanged. Its overlaid
`vllm/config/speculative.py` SHA256 is
`a1d14995e80d9b82f37585e95b0b532d4c6d7bd42c36b4e6cc0e8363c5402cca`.
The launcher validates both commit and file hash before creating a container.
On resume, recheck that NPU0-3 are idle and NPU4-7 still belong to the protected
workload, then launch a unique v2 evidence root. First prove the service log
reports `method=draft_model`, the normal Qwen3.5 causal-LM architecture, and
successful target plus draft loading. Only then run c1 fail-fast and the full
P50/P95/P99 matrix. Do not rerun ngram_gpu or MP_FFN MP2 unchanged.

The repaired draft v2 subsequently proved `method=draft_model` and the normal
Qwen3.5 causal-LM architecture, then stopped at the next genuine contract:
generic DraftModelProposer does not support M-RoPE, and its padded extra-slot
copy kernel emits only one-dimensional positions. Preserve v2 under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-draft4b-k3-mmar-prefetch0p1-v2-20260906T1014Z`;
service-log SHA256 is
`58c9e4928d657bba3215df347c64da54a2d07a83945c4207808d0fc23c60f6e2`.
Do not bypass the assertion: a correct implementation must expand, update and
slot-map all three M-RoPE axes and needs independent semantic tests.

Suffix Decoding v1 from arXiv:2411.04975 ended before model-worker startup:
vLLM 0.23.0 rejects suffix proposals when async scheduling is enabled. Preserve
operation `exec-00000000000001dc` and evidence root
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-suffix-k16-mmar-prefetch0p1-v1-20260906T1020Z`;
the service-log SHA256 is
`79657365c4e2d835ea094e31575171fd6c89efaa0e8c64965811d52c7e1f58ca`.
This is an invalid integration run, not performance evidence.

The successor uses explicit `--no-async-scheduling`. That scheduler change is
required by the method and must be charged to its E2E result. The method remains
training-free, loads no draft model, and every proposal is verified by the
unchanged 27B target. It retains BF16 TP4 MMAR, NZ1 and gate/up prefetch 0.1 on
NPU0-3. Its decision must include TTFT and TPOT P50/P95/P99 for all c1/c5/c8/c16
cells plus speculative acceptance counters; zero errors and natural EOS are
necessary runtime gates, not proof of business semantic quality.

Suffix v2 is active as operation `exec-00000000000001e9`, run
`tp4-npu03-suffix-k16-sync-mmar-prefetch0p1-v2-20260906T1033Z`, under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-suffix-k16-sync-mmar-prefetch0p1-v2-20260906T1033Z`.
Before launch, the exact `orch_try.sh` process and `p0_try` container that
had auto-restarted on NPU0-3 were stopped; NPU4-7 remained untouched.

Suffix v2 then loaded all 18 target-model shards successfully but failed at KV
attention initialization: 16 draft tokens plus the current token yielded
`decode_threshold=17`, while Ascend fused TND attention permits at most 16.
It completed as exit 70 with zero requests; service-log SHA256 is
`a98c8d8580d5d9c9ac3af721e72e9ac2d685266a42dce55bf075ed554a8235cc`.
The bounded successor uses 15 draft tokens, giving effective threshold 16.
It is active as operation `exec-00000000000001f3`, run
`tp4-npu03-suffix-k15-sync-mmar-prefetch0p1-v3-20260906T1041Z`.
Readiness passed: the target compiled, exposed a 547,368-token KV cache,
captured all five FULL decode graphs, became healthy and began the real c1
query_rewrite traffic. Do not edit either executing launcher until this
operation is terminal.

## Suffix-k15 c1 terminal rejection

Operation `exec-00000000000001f3` is terminal after a guarded c1 fail-fast.
The complete c1 artifact contains 32/32 requests, zero errors and 32 natural
stops. A separate watcher verified the exact runner start time and container
ID, waited until the JSON was parseable with `completed=32`, saved Prometheus
and service logs, then stopped only this experiment before c5 began. The
container exited 0; matching task processes are absent and NPU0-3 are released.

Against frozen TP4/NPU0-3 baseline SHA256
`cef6713367f387fd67c15c2cc0bdf071c33f58846b8ef9a041a489186aa0d9d4`,
the complete c1 result is:

| Metric | Baseline P50/P95/P99 ms | Suffix P50/P95/P99 ms | Speedup P50/P95/P99 |
|---|---:|---:|---:|
| TTFT | 919.428 / 966.326 / 973.824 | 419.054 / 5949.488 / 6257.816 | 2.194x / 0.162x / 0.156x |
| TPOT | 35.320 / 39.046 / 58.663 | 138.443 / 158.124 / 159.432 | 0.255x / 0.247x / 0.368x |

Suffix accepted 3,606 of 11,949 drafted tokens (30.18%). The service exposed
captured normal decode graphs, but actual variable speculative batches ran
with graph mode NONE; the method also required synchronous scheduling. The
acceptance rate could not amortize these integration costs. This is a terminal
performance rejection for the current implementation, not a semantic failure
of target verification. Do not try k3/k5/k15 variants unchanged; resume only
after a concrete implementation keeps async scheduling and captured graph
execution.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-suffix-k15-sync-mmar-prefetch0p1-v3-20260906T1041Z`.
SHA256: c1 `37ebb85038327c7b57976964e145902b8860c939d89c83622ebe4545ff28e53f`,
decision `01d5a94bc3cafacac12dbaa3c74db798d1f866f27585b1d30e030b90c6afbb46`,
service log `71810580d69601d86f3ec803bdc30bbb788f4689a0de3697becf06bef6506804`,
Prometheus snapshot `4b770e7e5b0f84b185fcc7ce3ed663ae62ff48a6b0e537ce9607688dd5e25fff`.

The next optimization must preserve asynchronous scheduling and decode graph
execution. Existing profile evidence points to the roughly 128 serialized
row-parallel MMAR paths per decode step. Reinspect the exact installed MMAR
source and `/cache/cch` operator-generation assets before proposing a new
shape-specialized kernel; do not repeat commTurn, separate MatMul+AllReduce,
FlashComm, static-kernel or fused-tail variants already rejected above.

## TP4 MTP k3 local-argmax full screen

Run `tp4-npu03-mtp-k3-local-argmax-mmar-prefetch0p1-v1-20260906T113059Z`
completed all c1/c5/c8/c16 cells on physical NPU0-3: 128/128 requests, zero
errors and natural stops. NPU4-7 remained owned by
`qwen36_hypic_nocache_baseline_npu4_7_tp4_b40960` and was not touched.
The exact-image focused test for commit
`37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd` passed before launch.

| Concurrency | TTFT speedup P50/P95/P99 | TPOT speedup P50/P95/P99 |
|---:|---:|---:|
| 1 | 1.863x / 0.153x / 0.148x | 2.484x / 1.237x / 1.156x |
| 5 | 1.664x / 1.100x / 1.130x | 2.255x / 1.517x / 1.787x |
| 8 | 1.583x / 0.977x / 0.977x | 2.049x / 1.661x / 1.898x |
| 16 | 1.264x / 0.920x / 0.920x | 1.489x / 1.081x / 0.979x |

MTP accepted 17,524 of 26,487 draft tokens (66.16%). This is strong evidence
that repaired local-argmax MTP k3 is a useful decode component: TPOT P50
exceeded 2x at c1/c5/c8. It is not the final accepted stack because c16 TPOT,
all TTFT P50 values, and several P95/P99 cells miss the 2x target. The quality
gate remains unproven because `query_rewrite` has no meaningful nonempty
reference answers; target verification and transport success do not alone
prove 精读无损.

The generic analyzer failed after the valid matrix because its immutable hash
table belongs to another baseline. The authoritative TP4/NPU0-3 decision is
`decision-tp4-npu03.json`, SHA256
`647dee9bf76eb4b045a34e03013d045479349359301a4574ed23958f164bd0da`.
The launcher now selects the TP4 analyzer when the frozen TP4/NPU0-3 baseline
directory is explicit, preserving rather than bypassing provenance checks.
Next profile c16 speculative scheduling and create a paired semantic-quality
gate; do not claim the 2x/精读无损 goal yet.

## TP4 MTP k3 plus batched-token budget 40960

Run `tp4-npu03-mtp-k3-local-argmax-mmar-prefetch0p1-bt40960-v1-20260906T120316Z`
completed all 12 cells on physical NPU0-3: three repetitions at each of
c1/c5/c8/c16, 384/384 requests, zero errors and all natural stops. The
candidate container stopped cleanly, NPU0-3 were released, and the external
NPU4-7 workload remained unchanged. All entries in `SHA256SUMS` verify.

The denominator is the frozen MTP-off TP4/NPU0-3 baseline. Its engine log
explicitly records `speculative_config=None`; plugin registration messages
mentioning MTP do not mean that MTP was enabled.

| Concurrency | TTFT speedup P50/P95/P99 | TPOT speedup P50/P95/P99 |
|---:|---:|---:|
| 1 | 1.865x / 1.825x / 1.809x | 2.471x / 2.477x / 1.508x |
| 5 | 1.755x / 1.885x / 1.937x | 2.213x / 1.629x / 1.698x |
| 8 | 1.662x / 1.809x / 1.808x | 2.097x / 1.718x / 1.965x |
| 16 | 1.438x / 1.514x / 1.514x | 1.845x / 1.194x / 0.431x |

MTP accepted 55,147 of 83,688 draft tokens (65.90%). Raising
`max_num_batched_tokens` from 32,768 to 40,960 improves several warmed and
high-load medians, but it does not close the TTFT gap and c16 TPOT P99 becomes
highly unstable. Decision: `iterate-performance`; do not promote 40,960 as
the final setting or repeat this budget increase without new profile evidence.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-mtp-k3-local-argmax-mmar-prefetch0p1-bt40960-v1-20260906T120316Z`.
Decision SHA256:
`1ab379995199b7a1f99e7633d8e4f17f6756dd0816e87c6a097be969c6011df0`.

The user-approved comparison policy is now two-stage: during optimization,
compare only with the frozen MTP-off baseline; after a candidate passes the
2x performance and semantic-quality gates, run a same-protocol MTP-on baseline
for final attribution. The next action is c16 draft/verify and short-output
TPOT-tail profiling, followed by one graph-compatible algorithm/operator
change. 精读无损 remains unproven.

## Non-speculative constraint and Qwen3.5 GDN prefetch screen

The user subsequently prohibited speculative decoding. This supersedes the
two-stage MTP policy above: all future candidates and final validation must
show `speculative_config=None`. MTP, draft-model, suffix, ngram and local-argmax
speculation remain historical evidence only and must not be stacked or used to
claim completion.

The first conforming operator candidate is
`tp4-npu03-qwen35-gdn-prefetch0p1-nospec-v1-20260906T125239Z`. It extends the
existing CANN/torch_npu dense gate/up prefetch trigger from `self_attn.o_proj`
to Qwen3.5 `linear_attn.out_proj`, uses the model layer-index helper, and closes
the prefetch lifecycle after `GemmaRMSNorm`. Source commit is
`82a2dce763eb39c285744f6fc36e37728471a1c7`; integration commit is `474d4f5`.
Focused unit tests passed 3/3, and an NPU0 BF16 smoke at batches 1/5/8/16 was
bitwise equal with maximum absolute error 0.

The real Ascend TP4 screen completed 128/128 requests with zero errors and all
natural stops. Runtime proof records NPU0-3, BF16, `quantization=None` and
`speculative_config=None`.

| Concurrency | TTFT speedup P50/P95/P99 | TPOT speedup P50/P95/P99 |
|---:|---:|---:|
| 1 | 2.040x / 0.157x / 0.097x | 1.224x / 1.350x / 2.023x |
| 5 | 2.028x / 1.558x / 1.224x | 1.357x / 1.320x / 1.489x |
| 8 | 2.116x / 9.531x / 9.526x | 1.432x / 2.192x / 2.977x |
| 16 | 2.098x / 1.888x / 1.888x | 1.413x / 1.981x / 1.779x |

Decision: `iterate-performance`. The operator treatment clears TTFT P50 at all
four concurrency levels, but no TPOT P50 cell reaches 2x and c1 TTFT P95/P99
regress sharply. Do not promote from this single repetition. Profile the
non-speculative c16 decode path and target MMAR/dense-FFN TPOT next. Quality
remains unproven because the dataset reference-answer field is not meaningful.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-gdn-prefetch0p1-nospec-v1-20260906T125239Z`.
Decision SHA256:
`d4c7529b6bcd4594f93caf69671cb552994798e793c7139e0da2f0bef77a3e75`.
All `SHA256SUMS` entries verify, the candidate container stopped, NPU0-3 are
free, and the external NPU4-7 workload was unchanged.

## Ascend-native boundary and non-speculative profile

This optimization is Ascend-only. Acceptance evidence must come from the
Qwen3.5-27B vLLM-Ascend 0.23.0/CANN stack on Ascend 910B4; CUDA-only kernels,
GPU benchmark extrapolation, or a source-only claim cannot establish a gain.
Every retained run must also prove BF16, `quantization=None`,
`speculative_config=None`, and the assigned physical NPU set in its runtime
artifacts.

Dynamic CANN profiling of the conforming prefetch candidate completed as
`tp4-npu03-qwen35-gdn-prefetch0p1-nospec-msprof-v1-20260906T131000Z`.
Rank 0 was attached after warmup and served one real query_rewrite request
(1810 prompt tokens, 104 completion tokens, natural stop). The summed kernel
duration is diagnostic rather than wall time because NPU streams overlap.

Of 6,390,948 us summed kernel duration, collectives account for 64.9357% and
matmul for 24.4934%. `MatmulAllReduceMc2AicpuKernel` contributes 48.1818%,
ordinary matmul 23.4185%, and `MatmulAllReduce` 16.6553%. The next hypothesis
must therefore target Ascend MMAR/HCCL execution or an Ascend graph
transformation that reduces or overlaps these serialized row-parallel paths.
Do not disable retained MMAR or launch sequence parallelism until exact
vLLM-Ascend graph matching and runtime activation are proved.

Profile root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profiles/tp4-npu03-qwen35-gdn-prefetch0p1-nospec-msprof-v1-20260906T131000Z`.
The op-summary SHA256 is
`45b376e3401961dd3ffb90a92fa7fb45e5c4d185aacf4177011c25ef62c19dc0`;
all manifest entries verify. NPU0-3 were released and NPU4-7 were unchanged.

## Ascend sequence-parallel activation probe

The retained MMAR stack was tested with the vLLM-Ascend sequence-parallel
compiler pass enabled and `sp_min_token_num=1`. This was an activation probe,
not a formal A/B. One private real query_rewrite sample completed on physical
Ascend 910B4 NPU0-3 with 1810 prompt tokens, 104 completion tokens, natural
stop, zero errors, BF16 float weights, `quantization=None`, and
`speculative_config=None`.

The rank-0 compiled-graph symbol inventory contains 704 occurrences of
`npu_mm_all_reduce_base` and 767 of `npu_add_rms_norm_bias`, but zero
`reduce_scatter` and zero `all_gather`. This confirms the retained MMAR
path remains opaque to the sequence-parallel pattern; enabling the pass did
not produce the intended Ascend collective transformation. It also removed
capture sizes 1, 2, 6, 10 and 14 under TP4, creating an avoidable c1 graph
coverage risk.

Decision: `rejected-activation`; do not spend a formal benchmark matrix on
this combination and do not repeat it unchanged. Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/activation-probes/tp4-npu03-gdn-prefetch0p1-sp-pass-v1-20260906T1348Z`.
The manifest SHA256 is
`718355accf230244126b881cdff04b03e52ccf9a6dafd76e534857c6ad711a19`.
All entries verify. The probe container was stopped, NPU0-3 were released, and
the external NPU4-7 workload remained running and untouched.

## Ascend fused GDN prefill precision gate

The uncommitted source candidate in
`/cache/cch/.worktrees/WS-20260904-qwen35-v023-fused-gdn` adds an optional
`torch_npu.npu_chunk_gated_delta_rule` prefill path. Its availability smoke
and a real Qwen3.5 TP4-local shape probe both executed on physical Ascend 910B4
NPU0. The shape probe returned output `(1, 64, 12, 128)` and final state
`(1, 12, 128, 128)` (operation `exec-0000000000000364`).

The authoritative operator-repository BF16 golden was then run at
`B=1, T=64, Nk=4, Nv=12, Dk=Dv=128` from
`/cache/cch/ops-transformer/attention/chunk_gated_delta_rule/tests/pytest/chunk_gated_delta_rule_golden.py`
(operation `exec-0000000000000368`). It returned `FAILED` for both output
and recurrent state:

| Tensor | Max absolute error at reported worst index | Max-relative-error ratio | Golden limit |
|---|---:|---:|---:|
| output | 0.00260362 | 19.977 | 5 |
| final state | 0.000927791 | 60.381 | 5 |

Decision: `rejected-correctness`. Do not merge, integrate, or run an E2E
matrix for this fused-GDN candidate unchanged. It is additionally a prefill-only
treatment against a profile share of about 0.5666%, so it is not a credible
route to the outstanding TPOT P50 target. The source worktree was left
unmodified and uncommitted, NPU0 was released after the probe, and the existing
NPU4-7 workload was not touched.

## Ascend BF16 dense FFN fusion applicability rejection

The next profile-guided candidate was CANN's native `torch_npu.npu_ffn`
operator, not a CUDA analogue. The installed vLLM-Ascend 0.23.0 image exposes
the API, and the CANN operator source documents Atlas A2/910B4 support.
Qwen3.5-27B uses BF16, hidden size 5120, intermediate size 17408, and a
SwiGLU MLP; under TP4 the first fused projection would therefore require
`N1 = 2 * K2`.

The authoritative `npu_ffn` API contract rejects that combination:
`swiglu/geglu/reglu` fusion is supported only for the no-expert FP16
high-performance path. BF16 non-quantized execution supports
`silu/gelu/relu` with `N1 = K2`, which is not Qwen3.5's gated MLP.
Changing to FP16 or replacing SwiGLU would violate the frozen BF16 and
lossless-semantic contracts. This is therefore `rejected-applicability`
before allocating NPU time; no E2E performance claim is made.

The source checks were operations `exec-000000000000037b` and
`exec-000000000000037c`. Do not retry `npu_ffn(..., activation="swiglu")`
for this BF16 dense model unless the installed CANN API adds BF16 gated
activation support. Physical NPU0-3 remained idle, and the external workload
on NPU4-7 was not modified.

## Down-projection prefetch screen rejected

Run
`tp4-npu03-qwen35-gdn-gateup-down-prefetch0p1-nospec-v1-20260906T151000Z`
completed on real Ascend 910B4 NPU0-3. It changed one variable on top of the
retained non-speculative stack: `mlp.down` prefetch ratio `0.0 -> 0.1`.
The engine log proves vLLM-Ascend 0.23.0, CANN 9.1.0, TP4/DP1,
`device_config=npu`, BF16, `quantization=None`, and
`speculative_config=None`.

All c1/c5/c8/c16 cells completed: 128/128 requests, zero errors, and all
natural stops.

| Concurrency | TTFT speedup P50/P95/P99 | TPOT speedup P50/P95/P99 |
|---:|---:|---:|
| 1 | 2.143x / 0.155x / 0.095x | 1.224x / 1.237x / 1.609x |
| 5 | 2.053x / 1.797x / 1.425x | 1.363x / 1.439x / 1.624x |
| 8 | 2.065x / 2.226x / 2.226x | 1.393x / 1.726x / 1.794x |
| 16 | 3.824x / 2.041x / 2.041x | 1.339x / 1.389x / 0.568x |

Decision: reject down-projection prefetch from the retained stack. Relative
to gate/up-only prefetch, TPOT P50 changes by about 1.000x, 1.004x, 0.973x,
and 0.948x at c1/c5/c8/c16. The single-run c16 TTFT improvement does not
offset the primary decode regressions, the c16 TPOT P99 regression, or the
lack of three-repeat evidence. Retain gate/up-only prefetch and restore
`mlp.down=0.0`.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-gdn-gateup-down-prefetch0p1-nospec-v1-20260906T151000Z`.
Decision SHA256:
`a390075b67d6357d0e99f1456fc6a8ed34e5b6dc34efa0a6ff5ce5690972d077`.
Service log SHA256:
`609c2eda2269c0fa6b8d05b5526b08fbf4f67f54890360845133517b7b11409f`.
All manifest entries verify. The exact container and matching processes are
absent, NPU0-3 are free, and the external NPU4-7 workload remains running and
untouched.

The goal remains incomplete: no non-speculative TPOT P50 cell reaches 2x and
the semantic `精读无损` gate is still unproven. Resume from the gate/up-only
prefetch stack and select a BF16-compatible Ascend MMAR/dense-matmul treatment
using the existing CANN profile; do not retry down prefetch unchanged.

## MMAR weight-layout probe rejected

Real BF16 TP4-local shapes on physical Ascend 910B4 NPU0-3 compared the live
contiguous `[N,K]` parameter consumed as `weight.t()` with a pre-transposed
contiguous `[K,N]` MMAR weight. Correctness passed, but the eight-cell geometric
mean speedup was only `1.009789x` (range `0.994723x-1.033737x`), below the
predeclared `>=1.02x` gate and with one regressing cell. Reject before E2E and
do not integrate the extra layout/copy path unchanged. Evidence:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/mmar-weight-layout-npu03-v1/report.json`,
SHA256 `173f0cb4e90f843194448a8eab2cd2e900b62cb005fb4ea88ab100f374f8b643`.

## INFO production-log candidate rejected

The retained TP4/NPU0-3 stack was relaunched with exactly one intended change:
`VLLM_LOGGING_LEVEL=DEBUG -> INFO`; `TRITON_KERNEL_DUMP=1`, BF16, 133K,
MMAR, NZ1, gate/up prefetch 0.1, down prefetch 0.0, GDN projection fusion,
async scheduling, and `speculative_config=None` were preserved. Three c16
query_rewrite runs completed 96/96 requests with zero errors and natural EOS.
Their per-run P95 pairs `(TTFT ms, TPOT ms)` were
`(10352.929,104.020)`, `(18348.233,144.167)`, and
`(6762.540,69.736)`; median-of-three was `10352.929/104.020`, versus the
retained stack's `6796.297/69.560`. This is a `52.33%` TTFT and `49.54%`
TPOT regression, so the candidate is rejected and no c5/c8 expansion is
justified. A salted diagnostic c1 run is retained only as supporting evidence;
its TPOT P95 was neutral (`28.287 ms`), while its TTFT is not comparable to
the frozen unsalted contract.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-gdn-proj-fusion-prodlog-info-v1-20260906T175100Z`.
The candidate was stopped after evidence capture and the retained DEBUG stack
was restarted as `qwen35_gdn_proj_fusion_npu03_v1` on physical NPU0-3.
NPU4-7 were not allocated or modified. The dataset SHA256 is
`a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`;
the weak/sparse `answer` field still cannot prove `精读无损`.

## Deterministic paired quality gate

The dataset audit found that all 357 `answer` fields are empty, so a new
deterministic paired-output protocol replaced the invalid reference-similarity
claim. The TP4 cumulative control and retained candidate each completed 16/16
length-quantile samples with temperature 0, seed 1024, identical prompts, and
natural EOS.

Automatic comparison found 11/16 byte-identical and 12/16
whitespace-normalized-identical responses. Manual review of the five remaining
pairs found no material semantic regression: one was only empty/whitespace/EOS
representation, while four retained the same final intent, facts, and
constraints with only reason wording, punctuation, or word order changes.

Decision: sampled paired semantic gate passes 16/16 for the retained GDN
projection fusion plus gate/up prefetch stack. This is not a proof over the
full 357-row corpus. See `QUALITY_GATE_V1.md` for evidence paths, hashes,
rulings, and the distinction between this TP4 quality control and the frozen
TP8 MTP-off performance denominator.

## MMAR-off E2E screen rejected

The retained TP4/NPU0-3 stack was screened with one intended graph change:
`enable_matmul_allreduce=true -> false`. The ordinary FULL_DECODE_ONLY
rank-0 graph proves activation: it contains zero
`npu_mm_all_reduce_base`/zero `matmul_all_reduce` occurrences and 832
`all_reduce` occurrences. Its SHA256 is
`cbc36a6bd1aa4cf89ed872e5fe12b981502841f3520388e006880cf6ffbf4d68`.

The real query_rewrite c1 screen completed 32/32 requests with zero errors,
32 natural stop finishes, TTFT P95 6331.334766501095 ms and TPOT P95
28.374273561977503 ms. Against the retained same-screen reference
6298.128575/28.311849 ms, this regressed TTFT by 0.527248% and TPOT by
0.220490%. Reject by the fail-fast rule; do not expand this unchanged
candidate to c16 or the full matrix.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-gdn-proj-fusion-mmaroff-nospec-screen-v1-20260907T001500Z`.
All manifest entries verify; SHA256 of `SHA256SUMS` is
`21deab1aa598edb04bfd38f6c88bd30118c3a6b1f04ed244e68cc403d12f964f`.
The exact rejected container
`9ba137984b01029d893ae972bee2cfd6795c8aa4e6fdd4a29be8ead82168767a`
was stopped. The retained MMAR-enabled mode was restarted as
`qwen35_gdn_proj_fusion_npu03_v4` on physical NPU0-3; NPU4-7 were not
modified.

## Selective attention/GDN MMAR-off screen rejected

A prefix-selective vLLM-Ascend control was implemented in source commit
`5d2c6e648f75bac11774a1e2886c8b7a65c4c9a2` with four passing unit tests.
The first real screen kept MMAR for MLP down projections and routed only
attention/GDN `o_proj/out_proj` through ordinary matmul plus all-reduce.

The c1 screen completed 32/32 real query_rewrite requests with zero errors,
32 natural stops, TTFT P95 6371.730095427483 ms and TPOT P95
32.33907336178116 ms. Against the retained 6298.128575/28.311849 ms
reference this regressed TTFT by 1.168625% and TPOT by 14.224519%.
The graph contained 384 MMAR and 768 all-reduce occurrences, proving that
the selective control activated. Reject this direction unchanged.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-gdn-proj-fusion-mmar-attn-off-nospec-screen-v1`.
Graph SHA256:
`0602d2c7e7c479b7821e8c988123f868e3b9a168a9852657c0746e46c9bcffac`.
Manifest SHA256:
`9588d485594c611ac72a2fb27f0aa0622a9dd8aa5a0ab1c05b59506bc8849da1`.

## Selective MLP down-projection MMAR-off screen rejected

The complementary screen retained MMAR for attention/GDN
`o_proj/out_proj` and routed only MLP `down_proj` through ordinary
matmul plus all-reduce. It completed 32/32 real c1 query_rewrite requests
with zero errors, 32 natural stops, TTFT P95 6310.708106448874 ms and TPOT
P95 28.333869803263084 ms. Against the retained 6298.128575/28.311849 ms
reference, both metrics regressed: TTFT +0.199734% and TPOT +0.077779%.

The graph contained 320 `npu_mm_all_reduce_base` and 768 `all_reduce`
occurrences, proving selective activation. Reject by fail-fast; do not expand
to c16 or the full matrix. Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-npu03-qwen35-gdn-proj-fusion-mmar-down-off-nospec-screen-v1`.
All manifest entries verify; SHA256 of `SHA256SUMS` is
`78e15989e9fcb9580428c702fc83fed65535b93db22455953ca3f8ac8d6886d8`.
The exact candidate container exited cleanly and the retained stack was
restarted as `qwen35_gdn_proj_fusion_npu03_v5` on physical NPU0-3.

Both selective decomposition branches are now closed. Preserve MMAR for both
real shape families and continue with a materially new A2/910B4 MMAR kernel
or tiling implementation.

## ASCEND910B M=1 MMAR core-count experiment rejected

The first source experiment reduced the physical kernel launch width together
with the matmul core count. Real NPU0-3 validation showed severe output
corruption (candidate maximum absolute errors reached 304 and 536), because
the arch22 kernel executes Mc2SyncAll and HCCL post-processing on every
launched block. That implementation is invalid and must not be reused.

Operator commit `138a920157995613eb58c8ce9de7ec9f1f51633e` repaired the
contract by preserving the full platform launch width and changing only the
matmul tiling core count for M=1. The official host suite passed 109/109.
The resulting isolated package has SHA256
`420275e89e83d2e42b82152fc52db87f470b2a5372c7a8d7746200b31569c640`
and is installed under
`/cache/cch/qwen35-mmar-fullsync-arch22-custom-opp-v1`.

Two real BF16 TP4 scans then ran on physical NPU0-3 with 40 warmups, 200
iterations, seven repeats, median maximum-rank latency, no quantization, and
the exact profiled M=1 shapes. Correctness compares the complete fused output
with the frozen default output under twice the default fused-vs-unfused BF16
error envelope.

| Matmul cores | Correct | K1536 speedup | K4352 speedup | Decision |
|---:|:---:|---:|---:|---|
| 8 | yes | 0.974754x | 0.914781x | reject performance |
| 12 | yes | 1.036689x | 0.898306x | reject performance |
| 16 | no | 0.994298x | 0.986970x | reject correctness/performance |
| 18 | yes | 0.947797x | 0.988617x | reject performance |
| 20 | yes | 0.977601x | 0.972847x | reject performance |
| 22 | no | 0.997346x | 1.008609x | reject correctness/performance |

No label passed the predefined requirement that both shapes be correct and at
least 1.02x faster. Do not spend an E2E matrix on any of these settings and do
not repeat launch-width reduction. The experiment establishes that the
remaining M=1 cost is not solved by allocating fewer matmul cores; the next
kernel treatment must reduce or overlap the per-call HCCL
AllReduce/Commit/Wait/Finalize path while retaining full sync participation.

Immutable evidence:

- `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/tp4-npu03-mmar-m1-fullsync-core-scan-v2-20260907T000800Z`
- `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/tp4-npu03-mmar-m1-fullsync-core-scan-v3-20260907T001000Z`

Both runner operations exited successfully, all evidence manifests were
generated, NPU0-3 were released, and the workload on NPU4-7 was unchanged.

## Selective K4352 online-HCCL tiling rejected at operator gate

Operator commit `c1533e5` added
`ASCEND_MATMUL_ALLREDUCE_ONLINE_TILING_K` so the online-HCCL tiling path
could be restricted to the stronger profiled M=1, K=4352, N=5120 family
while K=1536 retained the frozen path. The official host suite passed
109/109. Build operation `exec-0000000000000207` produced the isolated
910B4 package with SHA256
`e44c6fd0c06221bfc8387026d5411f796e9ba1ecf6e9876efc95900cfc619c85`;
it is installed under
`/cache/cch/qwen35-mmar-online-k4352-arch22-custom-opp-v2`.

The first microbench evidence root is preserved as a diagnostic only. Its
evaluator compared fused outputs from independent HCCL process launches,
which is sensitive to BF16 reduction order and did not implement its own
documented error-envelope policy. Evidence tooling commits `e55b407` and
`e8b8f64` added a fixed-rank-order CPU FP32 sum of rank-local NPU BF16
matmul outputs and repaired the metric mapping. The v2 run then provided the
authoritative operator decision:

| Shape | Frozen median max-rank | Candidate | Speedup | Correct | Gate |
|---|---:|---:|---:|:---:|:---:|
| M1 K1536 N5120 | 84.39070 us | 85.17585 us | 0.990782x | yes | pass >=0.98x |
| M1 K4352 N5120 | 81.89830 us | 81.06975 us | 1.010220x | yes | fail >=1.02x |

Protocol was physical NPU0-3, TP4 BF16, 40 warmups, 200 measured iterations,
seven repeats, and median maximum-rank latency. Both shapes passed the
deterministic correctness envelope, but K4352 missed the predeclared
performance threshold. Reject before E2E and do not retry this K-only filter
unchanged.

Immutable evidence:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/tp4-npu03-mmar-m1-online-k4352-selective-frozen-ab-v2-20260907T032000Z`.
Decision SHA256:
`e5c7daf492937d2ec6d9c34c0f309dee9eb195c96b296914deefbcc530d52539`.
Manifest SHA256:
`77d157bfe13e4db02e875e3c7bb1c80baad810ded6e7d800fcc5afaae578aa2d`.
The benchmark containers exited, NPU0-3 were released, and NPU4-7 were not
modified.

## A2-native BF16 dense SwiGLU FFN candidate declared

After the selective K4352 MMAR path failed its operator gate, the next
materially different candidate targets the local dense MLP chain. Qwen3.5-27B
TP4 uses `[M,5120] x [5120,8704]`, SwiGLU to `[M,4352]`, then
`[M,4352] x [4352,5120]` for M=1/5/8/16.

The upstream FFN README marks A2 unsupported, but `ffn_def.cpp` registers
`ascend910b`; its high-performance SwiGLU contract is FP16-only. Treat this
as a feasibility question, not support evidence. Create an isolated worktree
from `ops-transformer@0684247214bae5abb5cb6dc7d90b34a6ad401cdd`.
Phase 0 must build a 910B package and prove BF16 SwiGLU starts. Phase 1 must
show deterministic correctness and at least 1.10x latency improvement at
every M before vLLM integration. The final TP all-reduce remains required.
No quantization, retraining, MTP, speculative decoding, or NPU4-7 use.

## A2 BF16 dense SwiGLU feasibility closed at M=1 gate

The isolated operator branch
`work/exp-20260907-qwen35-a2-bf16-swiglu-gated-mlp` at commit
`f0a5a5c` replaces the unavailable private `ExecMmOp` dependency with
self-contained MM1, SwiGLU and MM2 stages. Physical 910B4 NPU0 tests used the
exact TP4-local BF16 M=1 shape, deterministic sparse nonzero data, 20 warmups,
100 iterations and five repeats.

Both the candidate and a process-isolated system ACLNN
`MatMul -> SwiGLU -> MatMul` baseline produced four expected nonzero outputs
with zero maximum absolute error against the BF16-rounded analytic reference.
The system baseline median was `197.9728 us`; candidate v1 was `180.2859 us`,
or `1.098104733x`. This misses the predeclared `1.10x` promotion gate, so
do not integrate it into vLLM or extend the M=5/8/16 matrix.

A follow-up that reduced the SwiGLU stage launch count to its three M=1 tiles
preserved correctness but regressed to `206.3268 us`; it was reverted.
Candidate v1 package SHA256 is
`f19d80d998d1db084fe201533b8aacaa0627d08efcd723abcc744431dbe1c1b9`.
Rejected v2 package SHA256 is
`9a65281c2431be1f5cc88c8dfcb80c3d45fdc5184586cc9bcdcfe8e6a03b9e21`.
Full harness and decision details are in
`experimental/ffn/swiglu_gated_mlp/docs/QWEN35_A2_BF16_FEASIBILITY.md`
on the operator branch.

Harness lesson: do not mix system `libopapi` and custom `libcust_opapi` in
one process, and execute each system ACLNN executor before constructing the
next stage. Both unsafe patterns produced heap corruption.

The old `p0` workload was repeatedly relaunched on NPU0-3 by an external
mechanism during this screen. Exact competing containers were stopped or
reversibly renamed to create clean measurement windows. NPU4-7 were not used.

## A2 inplace MMAR+Add+RMSNorm integrated and rejected by E2E gate

The isolated vLLM-Ascend branch
`work/exp-20260907-qwen35-a2-inplace-mmar-rms` at commit
`7ffb081dbbc1069c2d3b4ad19a212752e5e06b73` binds
`aclnnInplaceMatmulAllReduceAddRmsNorm` as
`npu_inplace_matmul_all_reduce_add_rms_norm`. The graph pass requires the
residual to be an exclusive internal node and enables the inplace pattern only
for compile range `(1,8)`; range `(9,32768)` is deliberately excluded.
The custom extension SHA256 is
`7ef5fa67833b84226f8f40fcc7ac916b9bdfc8a2f7d6b26704fdf61e6ec41d9b`.
The focused unit suite passed 15 tests.

Physical NPU0-3 TP4 BF16 microbench covered the two Qwen3.5-27B row-parallel
families at M=1/5/8/16. All eight cells were correct and returned the residual
alias on every rank. M=1/5/8 speedups were 1.044x-1.068x, while both M=16
shapes were approximately 1.000x; this is why the integration caps the
inplace pass at eight tokens. Immutable microbench evidence:

- `/cache/cch/eval-runs/exp-20260907-qwen35-a2-inplace-mmar-rms/a2-inplace-mmar-rms-m1-v1-20260907T073500Z`
- `/cache/cch/eval-runs/exp-20260907-qwen35-a2-inplace-mmar-rms/a2-inplace-mmar-rms-m1-5-8-16-v2-20260907T074000Z`

The main service runner now contains an isolated
`qwen35-gdn-proj-fusion-inplace-tail` mode. It stacks the retained Qwen3.5
GDN projection fusion, dense gate/up prefetch ratio 0.1, MMAR online tiling,
and the new inplace tail pass. At real service compilation each TP rank
normalized 48 copies and fused 111 patterns for range `(1,8)`; each rank
reported `applicable=False` for `(9,32768)`.

One initial launch is diagnostic-only: the unrelated
`vllm-ep-310p-research-910b-monitor` container had all eight NPU devices and
the manager devices mounted, causing an official-image control probe to report
`device_count=0` and `rtGetSocVersion` failure. Stopping that sleep-only
container restored `device_count=4` and target `Ascend910B4`. No performance
claim is derived from the failed launch.

The authoritative single-repeat E2E screen used physical NPU0-3, the frozen
`/cache/cch/query_rewrite.jsonl` SHA256
`a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`,
32 natural-EOS requests per c1/c5/c8/c16 cell, and no quantization, MTP,
speculative decoding, or retraining. All 128 requests completed without
runtime errors.

| Concurrency | P95 TTFT | vs frozen baseline | P95 TPOT | vs frozen baseline |
|---:|---:|---:|---:|---:|
| c1 | 6115.848 ms | 0.158x | 33.420 ms | 1.168x |
| c5 | 7501.345 ms | 1.590x | 52.152 ms | 1.393x |
| c8 | 6298.099 ms | 2.020x | 69.599 ms | 1.580x |
| c16 | 6559.411 ms | 1.979x | 80.888 ms | 1.703x |

Relative to the retained best, P95 TPOT regressed by 18.2%, 18.5%, 11.0%,
and 16.3% at c1/c5/c8/c16. TTFT improved only at c8/c16 by 4.5%/3.5%;
c5 regressed 21.9%, and c1 developed a severe long tail. Therefore reject
this stack before a three-repeat promotion run and retain
`qwen35-gdn-proj-fusion-prefetch0p1-nospec-v1` as best.

Immutable E2E evidence:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-npu03-qwen35-gdn-proj-fusion-inplace-tail-nospec-v2-20260907T082700Z`.
The generated decision is `iterate-performance`; its quality gate remains
`unproven` because the dataset answer fields do not establish full
`精读无损`. Do not retry this exact inplace stack unchanged.

## vllm-ascend-lab upstream-preparation audit

The user-created repository was cloned to `/cache/cch/vllm-ascend-lab`.
Its remote is `https://github.com/c1917797-bit/vllm-ascend-lab.git`, and
the local preparation branch
`work/qwen35-27b-910b4-upstream-prep` starts from
`main@203ae3eb0a734c3a7ba638d84e116bcca24b1a09`. Nothing has been pushed.

The complete Chinese portability matrix and maintainer quality gate are in:

`/cache/cch/vllm-ascend-lab/.agents/workstreams/qwen35-27b-910b4-upstream-prep/HANDOFF.md`

Key decision: no existing optimization commit is safe to cherry-pick wholesale
onto the current repository main. The GDN projection fusion requires a current
vLLM-side rebase plus a minimal vllm-ascend backend change; the retained dense
MLP prefetch implementation conflicts with the feature removal in
`e77502ef715f612f2cc6f3c833174431f26cb765`; and the inplace MMAR candidate
is excluded because it failed the real E2E gate. The target repository product
code remains unchanged.

## Long-prefill AllReduce+RMSNorm candidate rejected at activation

The isolated vLLM-Ascend branch
`work/exp-20260907-qwen35-prefill-allreduce-rms` at signed commit
`74b83e11f563af47baa4d298bd0725d49ac4bc2c` adds an opt-in token threshold
to `MatmulAllreduceRowParallelOp`. With threshold 512, decode-sized graphs
retain the existing MMAR path while long-prefill graphs use ordinary BF16
GEMM plus TP AllReduce so the built-in `MatmulAllReduceAddRMSNormPass` can
attempt fusion. Focused CPU unit tests passed `14/14`; `ruff` was unavailable
in the image, so no lint claim is made.

The real TP4 activation used physical 910B4 NPU0-3 and stacked the retained
GDN projection fusion plus dense gate/up prefetch 0.1. Configuration evidence
confirmed `fuse_allreduce_rms=True`, and compilation split into `(1,512)` and
`(513,32768)`; both graphs compiled. During the subsequent maximum-shape
profile run, TP0 hit ACL error `507014`: AICore execution timed out in stream
synchronization. Engine startup failed before `/v1/models`, chat smoke,
correctness, or E2E benchmarking. Therefore this candidate is rejected at
the activation gate and produces no performance claim. Do not retry the same
910B4 long-prefill fusion unchanged; first isolate the fused operator at the
exact long-prefill shape and prove bounded execution plus numerical output.

Immutable evidence:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/activation-probes/tp4-npu03-qwen35-prefill-ar-rms-v1-20260907T1012Z`.
Service-log SHA256 is
`c40943f3aee9f9259c39728d200d77476a02f5c5d04f328b0db60fe7a7216104`;
container-inspect SHA256 is
`19b05f60bd4cf9d7db5963b251fb08bb1ca654c2f4907884efec3215a37f6d63`.
The failed container released NPU0-3; NPU4-7 were not modified.

Follow-up isolation narrowed the boundary. The repository's A2 TP4 fused-op
test was parameterized at signed-off commit `b462358b17debeef767d27a7ce3292b1101a0eaa`.
At the exact Qwen3.5 row-parallel shape K=4352/N=5120, BF16 correctness passed
at M=4096, 8192 and 16384 with one warmup and one measured invocation. Thus
the activation failure is not evidence that the operator is universally
unsupported on 910B4. Evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-probes/tp4-npu03-qwen35-ar-rms-shape-boundary-v1-20260907T1042Z`.

The implementation still remains rejected: the maximum-shape Dynamo trace
specialized the Python token-count branch to ordinary GEMM+AllReduce, and the
same FX graph fed both compile ranges. Consequently the short range did not
retain MMAR as designed. Any successor must perform range-specific graph
rewriting (for example decomposing MMAR only in the selected prefill range),
not a Python shape branch inside `apply_impl`.

## 2026-09-07 target and delivery-contract update

The current stop gate supersedes earlier 2x/3x targets: at every c1/c5/c8/c16
cell, the median of three real `query_rewrite.jsonl` runs must show both TTFT
P95 and TPOT P95 speedup `>=1.5x` versus the frozen MTP-off baseline. Report
P99 as a tail-risk guard and P50 as secondary evidence. Quantization,
retraining, speculative decoding and MTP remain excluded.

All deliverable changes must be runtime Python monkeypatches. Do not modify or
overlay vLLM source, and do not use vLLM-Ascend source overlays for final E2E
evidence. The current implementation is
`scripts/qwen35_ascend_monkeypatch/sitecustomize.py` (SHA256
`28091a36b6737470cfcecb70520d1dfe49f122531511b5cfcad16b566d165897`),
mounted read-only by `scripts/run_qwen35_tp4_dev_service.sh`. It defers all
Ascend imports until vLLM's device-less model inspection completes, then
installs the compile-range, bounded-MMAR, GDN prefetch and RMSNorm hooks.

The earlier `qwen35_prefill_range_npu03_20260907t4` source-overlay activation
proved the three compile ranges and 128 bounded-MMAR rewrites per TP rank, but
is noncompliant with the monkeypatch-only delivery contract and is not final
performance evidence. Monkeypatch attempts t6/t7/t8 failed before API startup:
t6/t7 exposed premature Ascend import; t8 confirmed that merely preserving the
image's CANN `PYTHONPATH` was insufficient. These failures have no performance
claim. The deferred-import implementation has passed host `py_compile` but has
not yet reached an NPU activation gate.

Execution is currently waiting on NPU0-3 availability. The externally started
container `vllm-ep-310p-research-910b-monitor` runs a TP2 quantized Qwen3 job
on physical NPU0-1. It mounts device nodes 0-7 even though `npu-smi` shows no
process on NPU2-7; stopping it was not authorized by the no-impact NPU4-7
boundary. Do not bypass this guard. Resume by obtaining explicit approval to
stop that all-device container, or wait until NPU0-1 are released, then launch
the deferred monkeypatch candidate on NPU0-3 and run correctness before E2E.

The device-free contract probe
`scripts/qwen35_ascend_monkeypatch/test_deferred_activation.py` passes. It
proves that a synthetic model-inspection failure is propagated without
activating any Ascend runtime target, a successful inspection activates all
runtime targets, and repeated successful inspection remains idempotent. It
also verifies ordered insertion of the 512/16384 compile boundaries, fallback
to the original non-linear-attention prefetch path, bounded gate/up prefetch
for the linear-attention path, and RMSNorm postprocessing only when residual
is absent. The graph-manager probe additionally proves that bounded MMAR is
not inserted when AllReduce+RMS fusion is disabled, is inserted immediately
before `MatmulAllReduceAddRMSNormPass` when enabled, and is not duplicated
when already present. This closes the pure-Python control-flow/configuration
gap behind t5-t8, but it does not replace the pending real 910B4 startup,
correctness, profiling, or E2E gates.

The historical paired-quality evidence was revalidated on 2026-09-07: all
four recorded SHA256 values still match and each raw/derived file is mode
`0600`. The dataset audit again found 357/357 empty `answer` fields. For the
final bounded-MMAR monkeypatch, capture 32 question-length-quantile samples
against the same-runtime retained cumulative control. Byte-identical responses
pass automatically; otherwise manually review every differing pair and require
zero material regressions. The earlier 16/16 sampled pass remains control
history and must not be generalized to the final candidate.

The authoritative performance analyzer accepts an optional
`--quality-decision` JSON only after validating schema
`qwen35-quality-human-decision/v1`, candidate id, dataset hash, same-runtime
control scope, at least 32 samples, all samples equivalent, zero material
regressions, reviewer/time metadata, every differing pair reviewed, and the
SHA256 of baseline capture, candidate capture and paired comparison. Without
this evidence, a performance-passing candidate with cross-run hash drift is
`hold-quality-unproven`; a performance miss remains `iterate` and does not
trigger unnecessary manual review.

The TP4 launcher no longer ignores
`vllm-ep-310p-research-910b-monitor` in its default container-reservation
gate. That container now auto-starts workers and cannot be treated as an idle
monitor shell. A fail-closed probe with `NPU_SMI_BIN=/bin/false` returned
exit 48 from the container-reservation check and created no test container,
proving the guard runs before both the process-table fallback and Docker
creation. This prevents a race when the external workers briefly disappear
between restarts.

## 2026-09-07 bounded-MMAR handoff audit

The final runtime-only monkeypatch deliberately decomposes MMAR only for
compile ranges whose token count is greater than 512 and at most 16384.
Decode-sized ranges at or below 512 and the maximum range above 16384 retain
the original MMAR path. This boundary aligns the successor with the isolated
910B4 operator proof at M=4096/8192/16384 and does not extend the fused
AllReduce+RMSNorm route into the maximum range associated with the earlier
full-service timeout. This is static control-flow evidence only; real TP4
startup must still prove per-rank range applicability and rewrite counts
before correctness or performance traffic.

At 2026-09-07T15:35:25Z, direct host evidence still showed
`vllm-ep-310p-research-910b-monitor` running since 13:38:15Z with TP workers
2684511 and 2684512 consuming about 28103/28102 MiB on physical NPU0/1.
Physical NPU2-7 had no running process and port 10010 was not listening.
Because the container reserves device nodes 0-7, the TP4 launcher must remain
fail-closed until the container exits or the user explicitly authorizes
stopping it.

## 2026-09-07 final runtime-monkeypatch activation and c1 decision

The external all-device blocker exited and four consecutive checks showed
NPU0-3 idle. Candidate `t11` then ran on physical 910B4 NPU0-3 only. Commit
`ebe9b69aad45a24fa79437705f00ebbeed977e55` fixes the missing worker-process
activation; the final `sitecustomize.py` SHA256 is
`9c8e74ae5ba9adaf74628d74c3361d2e8bcb86792ff1d4c54eca00381e1b92a8`.
All four TP workers installed the prefetch/RMSNorm/GraphFusion hooks, inserted
the bounded-MMAR pass, and each decomposed 128 MMAR nodes in the 513-16384
prefill range. The service reached `/v1/models`; a fixed-input smoke completed
1/1 with zero errors and natural EOS. Mount inspection proved that no vLLM or
vLLM-Ascend source tree was overlaid.

The c1 frozen workload completed three repetitions, 96/96 requests, with zero
errors and all natural stops. Median-of-three TTFT P95 was `505.1956 ms`, a
`1.9128x` speedup over the frozen MTP-off baseline `966.3259 ms`. Median TPOT
P95 was `32.3098 ms`, only `1.2085x` versus baseline `39.0459 ms`; the 1.5x
gate requires at most `26.0306 ms`, leaving about `19.43%` additional latency
reduction. The first repetition also had a warmup-like TTFT tail (P95
`6247.5032 ms`), while repetitions 2/3 were `505.1956/498.2918 ms`; retain all
three rather than deleting the adverse run.

Therefore reject this stack before c5/c8/c16 expansion, 32-sample semantic
capture, or profiling. It proves compliant runtime-only activation and strong
TTFT, but does not meet the user's TPOT stop gate. Immutable evidence is under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/runtime-monkeypatch-bounded-mmar-t11-20260907T1838Z`.
The exact t11 container was stopped after evidence capture and exited 0;
NPU0-3 were idle afterward. An unrelated workload that started on NPU4-7
during the screen was not stopped or modified.

Do not retry t11 unchanged. Existing parameter/topology/decomposition routes
are already closed by real evidence, and the A2 BF16 SwiGLU prototype's
`1.0981x` local gain is too small to close this E2E gap. The next admissible
step is a materially new ASCEND910B decode MMAR/HCCL lifecycle implementation,
first gated on exact BF16 M=1 row-parallel shapes and only then integrated by
runtime monkeypatch.

## 2026-09-08 target update and async-finalize operator decision

The current user target supersedes the historical 1.5x/2x/3x thresholds:
at every c1/c5/c8/c16 cell, median-of-three TTFT P95 must be at least 40%
lower and TPOT P95 at least 20% lower than the frozen MTP-off baseline.
Final acceptance still requires the 32-sample same-runtime paired semantic
gate with every differing pair reviewed and zero material regressions.

The frozen TP4 BF16 M=1 operator A/B ran on physical NPU0-3 under the
cooperative lease. Baseline versus opt-in async-finalize latency was
81.5492 -> 81.2656 us (1.0035x) for K1536 and
78.30915 -> 84.1352 us (0.9308x) for K4352. The geometric mean was
0.9664x; correctness remained inside the predeclared 2x baseline error
envelope, but the candidate failed both the per-shape no-regression and
1.03x gates. Reject it before runtime or E2E integration.

Both baseline and candidate also failed bitwise digest stability during the
5000-call stress stage while all outputs remained finite. This demonstrates
that byte-identical BF16 HCCL results are not a valid stress invariant for
this operator; successors must use a frozen numerical error envelope. This
does not rescue the candidate because its measured K4352 and geometric-mean
performance already fail.

Immutable evidence is
/cache/austinov/qwen35-query-rewrite/operator-microbench/tp4-npu03-mmar-m1-asyncfinalize-frozen-ab-v1-20260908T131500Z.
Decision SHA256 is
b19221c680a1ad9d4e9312f1d5b3510c58e364b0a2ce42da75982f903058d66d;
the SHA256 manifest hash is
fc1c8a6ceb151f73a426080fc12bee010458008bc88419708dbcdd69af078c2e.
Both one-shot containers exited, the NPU0-3 lease and ports were released,
NPU0-3 were idle, NPU4-7 were not touched, and the base image identity
remained unchanged.

Do not retry the async-finalize flag unchanged. The next step is a materially
different decode MMAR/HCCL lifecycle design, gated first at the same exact
M=1 row-parallel shapes before any runtime monkeypatch or E2E launch.
