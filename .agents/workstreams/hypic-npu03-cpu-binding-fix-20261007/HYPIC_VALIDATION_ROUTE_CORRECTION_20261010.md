# HYPIC verification route correction — 2026-10-10

The frozen r13 experiment is **complete with a negative quality decision**, not an unfinished piercing to be restarted. Its one-switch, same-environment results are: LongBench-v2 max-2048 c8 127×3, no-cache 230/381 versus HYPIC-only 219/381 (-2.8871 pp); four-worker hot proof 368/381; and separate c16/1024 performance median weighted TPOT 74.727578 versus 58.643006 ms/token (-21.5243%). Preserve its immutable roots and `REJECT_OR_QUALIFY` decision. Full-request quality and universal hot-path attribution are different claims; the 13 cold requests limit the latter but do not invalidate or erase the former.

## Which earlier success is actually comparable?

1. The user-supplied colleague report used HYPIC v0.8.5 `3ad0967`, Qwen3.5-27B, 2×910C/TP2, quality max-1024/c32, and 32k/1024/c16 performance. It is an external reference, not an r13 denominator.
2. The closer 2026-09-06 NPU4–7 experiment used Qwen3.6-27B, 4×910B4/TP4, the same pinned image and HYPIC `3ad0967`. Its independently audited 18/18 units found performance TPOT -18.9911%, LongBench-v2 -0.2625 pp and GSM8K -0.1516 pp at max-1024/c32. Its source is `.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/decision-hypic-formal-npu4-7-tp4-b40960.json`; raw root is `/cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906`. NPU4–7 are reference evidence only, never a resource for this task.
   A source-level request-contract check further narrows that historical quality
   claim: `hypic_quality_eval.py` sent ordinary chat `messages` and did not
   attach `vllm_xargs.hypic_segment_ends`. Its recorded hot-path proof was for
   the fixed-output performance ruler, not for each LongBench/GSM8K quality
   request. The old quality scores therefore establish only the historical
   natural-request deployment comparison, **not** explicit-segment in-path
   quality preservation. In contrast, current `hotpath_quality_full.py` sends
   `vllm_xargs.hypic_segment_ends=[boundary,prompt_tokens]` and joins scored
   request IDs to boundary and worker-hot events. This is a workload/path
   change in addition to source, output cap, lane and capacity changes; do not
   use the old quality acceptance to overturn an explicit-segment 2048 result.
3. r13 changed physical lane/CPU set, output cap to 2048, quality concurrency to c8, context/cache capacity, and HYPIC source to `c12060c`. Its dataset and evaluator SHA256 match the older Qwen3.6 historical contract, but its generation ruler does not. Baseline and candidate *within r13* are matched; old and new absolute quality scores are not interchangeable.
4. Git ancestry proves `3ad0967` is the parent of `c12060c`, but the 9 changed files are not telemetry-only. Scheduler changes hold prefills during pending materialization, rebuild an evicted scheduler entry, and reset retry counts after success; runner adds request-level proof. This is a concrete source-drift hypothesis, not proof that these edits caused the quality drop.

The r13 quality rejection does not depend solely on an added universal-hot criterion: all-request correctness fell by 11/381; matched-hot descriptive counts also fell 226/368 to 212/368. Conversely, the original predeclared `candidate >= baseline` quality gate is stricter than the old historical “within baseline repeat variability” wording. Do not change r13's frozen gate post hoc. A successor must freeze its own evidence-backed tolerance before any new run.

## Next discriminating experiment, not another broad rerun

First replay r13 raw hashes, per-sample score flips, finish reasons and source attestations offline. Then preregister a **bounded HYPIC-on source-lineage comparison** using the same Qwen3.6 weights/image, physical NPU0–3, c8/max-2048 prompts, service capacity and scorer in both arms. Only the plugin source (`3ad0967` versus `c12060c`) may differ. Select the diagnostic indices from the existing r13 score-flip ledger before launch; include both regressed and non-regressed controls. Use clean independent source checkouts and new immutable roots, continuous physical-lane isolation, exact owned cleanup and an independent paired audit. The old source may lack request-ID telemetry, so report the proof level it actually supports; do not invent four-worker per-request evidence. This small post-hoc-selected subset tests source sensitivity only; it cannot replace the full r13 quality verdict.

If the source-lineage test does not discriminate, next isolate **one** remaining factor (2048 cap, c8 traffic, or cache residency) in a newly frozen paired test; do not vary several at once. If a specific fix wins its bounded test, run a fresh full max-2048 paired quality suite and matched performance only where the source/service identity makes earlier evidence non-reusable. Reuse an existing baseline only after exact fingerprint and raw-hash verification. Do not run another isolated GDN probe or repeat completed r13/r14/profiler roots. A valid failed reproduction is a completed experiment, while adoption requires a fresh passing quality gate.

## Discontinued side path

GDN r5 succeeded as a bounded synthetic operator check on physical NPU0: custom op registered; 64-token synthetic relative-L2 residual was 0.001797 for left composition versus 0.066829 for reverse composition. Its immutable `terminal.json` SHA256 is `70ad142e7d068aa6637b21022a6d870ebc725e873e3dc375b3a07c8369d669a6`; 18 isolation samples were clean and the exact owned container was released. This does **not** explain the r13 answer regressions. The preceding r1–r4 bootstrap failures were diagnostic harness failures, not paper failures; stop this route unless new E2E evidence makes it decision-changing.

No main/remote integration or all-29-Skill acceptance is claimed.
