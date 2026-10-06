# Existing-paper evidence inventory — 2026-10-06

Read-only branch/raw-artifact audit, canonical root
`/opt/host/vnf/austinov/model-tuning-lab`, base `bb9a758`.
Portfolio cutoff2026-10-09T11:17:31Z; DAMP individual cutoff unchanged.
This is an evidence reconciliation, not new NPU/performance/task acceptance.
No non-HYPIC candidate currently meets final joint acceptance.

## Mandatory corrections

- Never say all papers were fully implemented/tested and showed no benefit.
- DeltaLog and KVBuffer have later actual Ascend implementations and service
  screens; opportunity-only labels in portfolio.json are stale.
- Old MXR/GoodEnough opportunity estimates used profiling with a Qwen3.8
  launch. MXR target-shape NPU output/state and local timing remain valid, but
  they do not establish current Qwen3.6 matched E2E rejection. GoodEnough's
  approximate algorithm was not implemented and cannot inherit MXR correctness.
- Native/CPU/source/ABI/diagnostic results are not final task accuracy.
- HYPIC is a prior success on a segmented-reuse workload, not a new deliverable.

## Original ten

| ID / method | Actual evidence | Scoped current conclusion / missing gate |
| --- | --- | --- |
|2605.21325 MXR|Official pinned PTO/MegaGDN; target local NPU chain output/state/replay; inversion about3.14-3.16x locally|No Qwen3.6 matched E2E or final task result; old mixed-model opportunity claim withdrawn|
|2608.15533 DeltaLog|Paper-equation AscendC; B1/B16x128, merge/slots/eager/graph, TP4x48 dispatch; v0.2.2 113.649628 vs frozen dense125.819134tok/s|Reject measured mixed-materialization implementation, single-screen about-9.672%; other scheduling mechanisms inconclusive; no final quality|
|2606.06034 GoodEnough|Mechanism/overlap screen only|Approximate algorithm not implemented/NPU-tested; no E2E/quality|
|2605.19049 KVBuffer|FP32 cap16/cap32 multi-step/graph/TP4; serial matched104.110913 vs108.996204tok/s (-4.482%); v5 106.005430 noncontemporary screen|Reject tested serial/vector versions; distinct parallel fold not implemented; final quality absent|
|2607.01299 HYPIC|Historical Ascend official implementation; segmented reuse three runs about+36.0663%|Historical sample only; 1024-cap task results are not current2048 acceptance; do not rerun/count as new|
|2605.05219 SparsePrefix|Actual checkpoint restore/replay; only7/8 measured replays matched; warmup divergence retained|Current correctness failure; need new lifecycle hypothesis before another run|
|2602.21144 SSM TP|Actual192/192 BF16 GDN fused MM-AllReduce selections and upstream overlap|No distinct incremental candidate in frozen stack; scoped applicability close|
|2601.11590 EPD-Serve|Deployment/Encode-path analysis|Current text workload has no Encode phase; scoped inapplicable|
|2608.30386 DASC|Paper-derived NR plugin; actual TP4 allocation/copy/restore branch|Three identical cache-hit inputs gave distinct outputs; current implementation failed; paper-wide benefit inconclusive|
|2603.15530 DUET|Official custom-chip architecture simulator audit|Not a fixed-Ascend software monkeypatch mechanism; scoped inapplicable|

Cross-paper GDN mega-op separately passed relevant state/graph, then measured
118.455179 vs125.819134tok/s (-5.852810%). It is not a substitute for an
unimplemented individual paper mechanism.

## Fifteen later canonical IDs

| ID / method | Highest actual evidence | Missing service chain / conclusion scope |
| --- | --- | --- |
|2608.27513 DAMP|Packed development, lossless covariance/packing, recovered TP4x48 native smoke; compressed recurrence failed step45; actual trace binds quantizer division seam|Full TRAIN native capture running; exact quantizer/generalSR/graph/typed-cache/service/E2E/final quality incomplete|
|2312.04985 SparQ|Native selected-page ABI eager/graph, synthetic selector, actual Q/K/V output-preserving diagnostic|Token selector/running-V mean/lifecycle/service missing; page adaptation only rejected|
|2406.10774 Quest|Official mechanism plus shared/per-head Q/K/V diagnostics|D256/GQA summary/selector/cache/service missing; measured prompt/budget investment screen only|
|2609.13205 Self-Indexing|Equation-derived rotation/full-support and pooled/per-head diagnostics|Bit-packed selector/token backend/service missing; only current5% budget/prompt screen closed|
|2512.16391 Kascade|Pinned source; actual cross-layer/local hindsight diagnostic|Cross-rank remap/fixed dev anchors/token kernel absent; same-rank investment scope only|
|2606.03458 KVarN|Author tile bitwise parity; split metadata; mixed read/write; changed-lookup graph|Monolithic build failed; split204.207ms long-context investment diagnostic; allocator/sealing/service missing|
|2407.11550 Ada-KV|Corrected official selector; all16 layers compact/mixed write-read; C2x1024 sampled lifecycle; grouped TND|Ungrouped matched-2.168832%; grouped E2E/real reduced allocation/graph/slot/C16 incomplete|
|2609.00097 FFD|Pinned source and corrected GQA/SBS/delta interpretation; real output-preserving diagnostics|Actual Q2+residual/V cache/kernel/lifecycle absent; byte proxy and mass screen are not quality|
|2402.02750 KIVI|Pinned source;12 actual Q/K/V samples; unpacked equation diagnostic|Faithful packing/group scales/residual tail/cache/graph/service absent; native-FIA relabeling route rejected|
|2405.06219 SKVQ|Source/native C8 mechanism difference audit|No paper-specific NPU candidate; not fully pierced|
|2406.09904 QQQ|Official source/license; native input-mutation diagnosis and copy/dynamic-quant eager/graph repair|Complete native pipeline slower onM16/M256; author calibration/model loader/service absent|
|2601.16536 W4A16 Split-K|Paper, true shape/profile and native/ops source audit|Deployed tiling, faithful quant/loader/model candidate missing; investment warning only|
|2609.16009 Narrow MatMul|Paper min(M,N)=1 vs actual frozenM16 trace|Frozen C16 shape inapplicable; separate B1 workload not tested|
|2501.01005 FlashInfer|Native GQA/head-tiling/split-KV source overlap|Deployed tiling proof and distinct candidate absent; not evidence of optimal native performance|
|2604.03298 ENEC|Official Ascend lossless codec/source; actual resident/no-offload launch|Current TP4 has no targeted transfer bottleneck; offload workload out of scope|

## History and missing archive

Three additional historical records must not be silently counted as current
Qwen3.6 final acceptance:

- 2608.30310 Tail-Replay: TP4/48-layer recurrence and exact controls, partial-tail
  output-preserving diagnostics. Real cache-hit replacement/E2E/GSM8K remain
  open. Old rejection misusing intermediate0.01 as1% GSM8K was withdrawn.
- 2508.06447 SlimInfer: selection-shadow activation/rank agreement, not actual
  hidden/cache reduction, semantic migration or E2E.
- 2602.04852 DRRQR: historical Qwen3.8; nonaligned104/88 runtime-invalid results
  were corrected. Do not substitute its results for current Qwen3.6 acceptance.

Eight mentioned sources lack an archived conclusion in this bounded canonical/
historical audit:2608.20961,2603.05931,OpenReview c6TDOPEQ0e,2509.19873,
2605.22416,2606.16429,2604.19877, and earlier2503.08524. Missing archive is
not proof of no work anywhere or paper failure. Give source/applicability and
remaining-evidence disposition explicitly rather than fabricate a completion.

The count is25 current +3 historical +8 not archived =36 mentioned sources;
it is NOT36 completed migrations. AWQ/SmoothQuant engineering artifacts without
a pinned paper/service identity are not additional accepted paper results.

## Execution priorities within72h

1. DAMP: fix observed quantizer seam, anchor independent generalSR reference,
   complete compressed recurrence/graph/real cache, reach matched service screen.
2. KVBuffer: prepare distinct FP32 parallel log-contraction/boundary fold;
   reuse valid ABI/service probes and fair7.5GiB dense budget, no unchanged
   serial rerun; preserve earlier intermittent graph failure coverage.
3. Ada-KV only if a new allocation/graph/request-safe mechanism is actually
   ready. Do not displace final timing/task testing with a third preparation.

Parallel agents prepare; MAIN serializes NPU4-7. Final day is reserved for
three matched fixed1024 timing pairs and no-thinking2048 normal-EOS tasks.
The requirement remains at least one genuinely usable non-HYPIC method, not
an example or a local kernel gain. Unfilled gates must stay unfilled at cutoff.

Audit crosschecked raw hashes for DeltaLog v0.2.2 (5cb782...), GDN v13
(0ddd8e...), KVBuffer paired results (0605a1.../678ee3...), Ada-KV grouped
(3cc5a3...), MXR numerical (ab112a...), and Sparse Prefix replay (4f1498...).
Their full identities remain in each original workstream/raw receipt.
