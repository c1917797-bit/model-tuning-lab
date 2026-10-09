# Actual fixed-input SparQ NPU score/reduction observation — 2026-10-09

## Scope and clocks
Qwen3.6-27B portfolio, physical NPU4–7 only; this source-bound diagnostic used
physical6 -> guest0. It is neither the original full ANN graph nor a model/
performance/task gate. Original ba508 failed60/128 remains FAILED.
Oct10 07:00:25Z first-repair and Oct12 07:00:25Z portfolio deadlines unchanged.

## Failed preparation retained
Actual01af terminal2/1.358s stopped before tests: MAIN incorrectly inherited
hard256MiB RLIMIT_AS into Go Docker CLI, which failed virtual page-summary
reservation. No Docker/NPU workload was created. This is not ordinary-RAM
exhaustion or algorithm failure. Separate1CPU orientation01b1 completed0;
actual MAIN+CLI peak RSS stayed far below256MiB. Native host's existing Docker
AS restoration/RSS budget was retained; no host memory/HugeTLB change.

Actual01b0 terminal1/1.973s ran28 software tests,27PASS/1FAIL: new positive
fixture expected85 padded slots, but128-39=89 and actual runtime returned89.
This was a real test/manifest arithmetic mistake, not a numerical failure.
Frozen v4 and original errors were retained. New separate v5 changed only
the positive assertion/name and manifest descriptive pad89; source producer,
consumer, algorithm arithmetic, tolerances and resources are unchanged.

Originals outside Git, under /cache/cch/qwen36-paper-preparation-20261007/sparse:
- MAIN_ORIENTATION_01AF_AS_FAILED_ORIGINAL_20261009.json
- MAIN_SCORE_V4_01B0_SOFTWARE_FAILED_ORIGINAL_20261009.json
- MAIN_SCORE_V5_01BD_SOFTWARE_ORIGINAL_20261009.json

## Actual current-source prerequisites and NPU execution
V5 root:
 /cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-ba508-fixed-score-shape-npu-v5-001
MF SHA9c6bfa71f266d8912a066cd8779a2e7ca93725b475dc57cc8955142f1e5351ea.
Actual01bd terminal0/2.179s: all28 tests PASS1.523s, Python compile, native41
source closure, default-OFF/help exit0. No software assertion claims NPU.

Actual MAIN01bf terminal0/229.281s: actual same660 Devices[] source/ABI,
weights-only saved8-row payload, exact CPU stop-retain, fresh physical6 canary,
8eager+8GLOBAL score-prefix observations, exact NPU stop-retain. Whole900s
including90cleanup, guest8GiB/host256MiB/reserve8GiB/7CPU17GiB summed unchanged.
Saved lengths [2157,2154,2151,2148,2145,39,2163,2160] all preserved.
Short row remains39live/89invalid scratch/current38; no padding-input rewrite.

Output:
 /cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-ba508-fixed-score-shape-npu-20261009-004
RESULT86328B SHA928c439a238d8955335a4e98a7189cbeced28d13e05f153eec1b36f873f80062.
NPU REPORT49237B SHA0ab0bf61360b372828fe5cdaabbb386649e1638713b46ad075dfe71da17c66ea.
Whole01bf original3075B SHAf509812781a49a40e22289a4960d69c0466eb9bda7de4d790721299cc41621a1:
 sparse/MAIN_SCORE_V5_01BF_NPU_OBSERVATION_ORIGINAL_20261009.json.
Actual independent whole-terminal consumer01cc completed0/0.540s; it checked
the complete16x8 domains/raw Refs/CPU->NPU handoff/live producer ownership/
physical mapping/stop-retain, and retained observed-not-a-pass/readyfalse.

## Complete observation, not promotion
Actual readonly01d7 completed0/1.198s and independently read every16 summary:
- All8x16 candidate vs cropped per-head reference scores bitwise identical.
- Every run has exactly one rank mismatch: row3, length2148, token2140;
  2FP32 ULP, absolute4.656612873077393e-10. Same in eager and graph.
- New candidate and reference scores both match actual saved scores bitwise.
- New full-capacity reduction of saved scores matches actual saved rank.
- All saved supports are legal under both new rank paths.
- Full fixed inputs, guards and pointer topology remain intact.
No tolerance was applied. Original settings were not recorded; new flags were
observed, not modified. This narrows the current discrepancy to the GQA SUM
reduction execution/domain seam. It does not establish all original failure
causes, full matrix correctness, graph/service integration or task quality.

Own CPU CIDd683839d55ee4027a41de300ae2efc9d0f9f9e79b909684670a1924819a9146f and
NPU CID5f9f7c4a81988091e37a1dc37d740288a96a1b96c32a5fb1d8b0a9d27e23c4da:
fresh01d7 inspect proved both stopped-retained/Pid0/noExec/noOOM/same660;
physical4–7 have no compute. Protected external0–3 activity was not operated.

## Next algorithm-linked step
Prepare a source-justified, graph-legal reduction adaptation and independent
reference before one new NPU run. No unchanged original/v3/v4 retry, in-graph
CPU item/dynamic allocation, silent tolerance change or fixed witness PASS
promotion. Preserve original128/20480 coverage and full outputs/feedback.
FULL native geometry and new complete streaming state observer are prepared
independently; old dump budget is not executable proof. Ada-KV is the next
distinct candidate, pending its real relocated-entry/native graph gates.
SparsePrefix has no distinct placement delta on uniform40x16384 protocol.
No accepted non-HYPIC E2E technique, new throughput or final task score yet.
