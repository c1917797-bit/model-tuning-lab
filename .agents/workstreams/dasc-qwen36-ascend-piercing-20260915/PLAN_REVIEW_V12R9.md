# DASC successor plan review — 2026-09-16

This review supersedes stale v12r7-waiting statements in historical notes.

## Objective and evidence boundary

Deliver a paper-derived DASC Ascend plugin/monkeypatch with reproducible
cache-hit service benefit, then final E2E GSM8K quality evaluation. Do not
substitute DRRQR numbers or microbenchmarks for DASC results. The user's 1%
quality-loss requirement is E2E, not an intermediate tensor tolerance; do not
silently equate relative percent with percentage points.

## Actual preceding attempts

- v12r7 failed during package installation from read-only source. Fixed by
  copying source into disposable container scratch before an offline build.
- v12r8 reached model loading, four-rank geometry and dispatch evidence, and
  the first linear layer's exact compact allocation on all four ranks. It
  failed during graph dummy execution with `active_slots must match discovered
  block ids`. It did not reach readiness, numerical canary, performance or
  quality evaluation. The later controller error followed stopping our failed
  container and is not the primary root-cause evidence.
- v12r8 artifacts: `/cache/cch/dasc-qwen36-ascend-20260915/request-owned-active-state-v12r8`.
  service.log SHA256 e17a4d0afe7ca4b6c478d2f039b33d16d1e4b9d317b12232367fd6c794c96175;
  evidence.jsonl SHA256 e1a688f345aabbe13c7314472c0c09d903bb1a4c00ba76dd3ec79619da5677b9.

## One-variable successor

The pinned Ascend runner's `_dummy_run` constructs synthetic metadata without
normal `_prepare_inputs`. Explicitly scope that method in the plugin; do not
guess that an empty real request list implies a dummy run. Use the same stable
metadata buffers and dense workspaces, but never activate synthetic owners or
checkpoint dummy results to persistent storage. Refuse dummy execution while
real owners are live. Cover exception cleanup, capture-to-request pointer reuse,
and all-padding metadata. These software tests are not ACL graph validation.

## Ordered gates and decisions

1. Focused regression tests in the pinned image without devices; validate the
   maintainer tree. Preserve failed tests and fix diagnosed defects.
2. Once physical NPU4–7 are exclusively available, one new immutable successor
   attempt: graph capture, first real request, replay with changing batch sizes,
   all-rank/all-layer activation, exact bytes, request continuity and prefix
   restore. No formal throughput run before these pass.
3. If graph integration fails, localize the first failing boundary. Eager mode
   may be used as a labeled diagnostic, not a graph pass or unmatched speedup.
   Do not repeat unchanged deterministic failures or use an arbitrary retry
   count as a scientific stopping criterion.
4. If correctness passes, measure a matched plugin-disabled control and
   candidate on cache-hit workloads, warmup excluded; report TTFT, TPOT,
   throughput, hit tokens and memory separately. Common framework improvements
   belong in both arms. Existing valid baseline artifacts may be reused only
   when their full protocol and software identity match.
5. If benefit is weak, quantify actual load/store overhead and TP padding.
   Admit coupled GQA-group redistribution or targeted operators only when
   evidence identifies a meaningful E2E opportunity. Allocation reduction alone
   does not prove speedup. Do not start unrelated generic kernel optimization.
6. Only promising correct candidates advance to repeated performance and final
   GSM8K quality; document rejected/inconclusive outcomes and a bounded next
   hypothesis. Design portable layouts and explicit capability checks, but do
   not promise speedup on every untested Ascend environment.

## Resource check

Fresh check during this revision found physical NPU4–7 actively occupied by
PIDs 1846971/1846974/1846975/1846976 in container
cf8d3c40f281e55f5ea2e04bbc5412a625626f8a9a479651aa46bae514be162e,
named `vllm-ascend`, serving qwen35-27b with DP2/TP4 on port10010.
This is not the stopped DASC v12r8 container. Do not stop it or launch a
competing NPU experiment. CPU-only bounded regressions remain possible.

No new DASC NPU performance or quality result exists at this checkpoint.

## Software validation

Pinned v0.23.0 image, no mapped devices, backend autoload disabled, read-only
repository, offline, 2 CPU / 4 GiB limit: 24 focused tests passed in 7.40 s
(operation exec-000000000000161b), then all 54 project tests passed in 6.50 s
(exec-000000000000161d). Maintainer tree validation passed (26 skills), and
`git diff --check` passed. This does not establish NPU numerical or graph
correctness. The successor remains opt-in and unpromoted.

The v12r9 controller now requires all 48 linear layers on each of four ranks
for allocation, request initialization and continuity, rejecting duplicates or
mismatched layer identities. Its six positive/negative validator tests passed
in the pinned image without device mappings (exec-0000000000001624).
The host Python test attempt failed before collection because that interpreter
lacks `unittest` (exec-0000000000001623); do not change the host installation.
Use the pinned-image interpreter for these tests.
`run_v12r9_once.py` uses a new immutable result directory and requires the
explicit-dummy-scope fix commit 8899d8d. This strengthens evidence coverage but
does not replace numerical lifecycle tests.

## Preflight ownership correction

A 2026-09-16 review found that the inherited controller parsed only explicit
HostConfig.Devices mappings. Three running foreign Ascend containers were
privileged, had no explicit device entries, and declared physical NPU4-7 only
through ASCEND_RT_VISIBLE_DEVICES. The old parser could therefore have launched
v12r9 into an overlapping reservation even though the external heartbeat gate
correctly blocked it.

The controller now treats explicit PathOnHost device mappings as physical
authority for non-privileged containers and, for privileged containers,
conservatively unions valid visible-device declarations with explicit mappings.
Eleven focused parser and layer-cohort tests passed in the pinned v0.23.0 image
without device mappings (operation exec-0000000000001641). A live
`--preflight-only` run then identified all three foreign NPU4-7 claims and
failed closed (operation exec-0000000000001640). This is a safety correction,
not NPU algorithm, performance, or quality evidence. The full 54-test plugin
suite also passed in the pinned image without devices after the correction
(operation exec-0000000000001649).
