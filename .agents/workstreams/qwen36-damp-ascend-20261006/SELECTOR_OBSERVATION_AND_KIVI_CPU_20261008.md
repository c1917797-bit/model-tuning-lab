# Selector observation and KIVI CPU prerequisites — 2026-10-08 06:31Z

## Goal and decision scope

Keep the training-free, default-OFF plugin/monkeypatch goal on Qwen3.6-27B,
physical NPU4–7 only. No new non-HYPIC method has passed the full acceptance
chain. The latest human permits at most1% task-accuracy loss, not1% tensor
error; report percentage-point and relative task deltas. Fixed1024-token paired
performance, separate TTFT/TPOT, and no-thinking2048 normal-EOS LongBench-v2/GSM8K
remain pending. Do not change the fixed Oct8 08:29:54Z KV/H8 or Oct9 11:17:31Z
portfolio deadlines.

The single authorized32GiB hugepage release is completed/SPENT:
Oct7 16:04:28Z node0 pool471->439; OVS24GiB retained, never stopped.
Later ordinary available memory is not wholly caused by that release.

## Actual SparQ005: diagnostic observations, not a repaired PASS

Source root:
`/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-selector-fixed-witness-v1-005`
SOURCE SHA b2f92a0515a0fc77514aa1089dd4e5f418ef40de5b39e81c16f60b9f6faf0859.
MAIN121d43 software checks preceded MAIN121f completed0/227552ms.
Physical6->guest0; two default GLOBAL graphs,8 eager+8 graph observations.
All observed live/direct/static/original-workspace ordered supports, alpha,
channels, untouched input, guards and storage pointers matched. PA was an
explicit diagnostic stub: native PA/model/full009 matrix were NOT executed.

Both final eager and graph raw NPU cutoff scores are exactly
0.0028689084574580193 for selected361 and excluded1157: gap0, FP32 ULP
2.3283064365386963e-10, margin0ULP. They match independent CPU32 and old exact
scratch; CPU64 differs by those two tokens. This strengthens a ranking-boundary
hypothesis, not proof of original009 graph lifetime or root cause. Additional
observation can change allocation/lifetimes. Original009 remains FAILED.
The prior004 failure was CPU-reference construction inside GLOBAL capture,
not evidence that the candidate workspace itself cannot capture.

MAIN1228 independent consumer completed0/411ms and explicitly retained
observed-not-a-pass, native_numeric_status=failed, ready=false,
root_cause_confirmed=false. Do not relabel the original acceptance.
RESULT SHA57316b35c73946af9c656b475b232102a4e25f6a485faefc881364d0a7ea7b0a.
Whole originals saved in source root:
ORIGINAL_MAIN_121F_TERMINAL.json SHA
fcd95f5b89d769583fc16f3c2ed57888187c08d15914b4736c6018d23524eff7,
ORIGINAL_MAIN_1228_CONSUME.json.
New device evidence root:
`/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-fixed-selector-witness-20261008-005`.
Both exact owned CPU/NPU guests are stopped-retained; cleanup had no errors.

Next: independent official dtype/operation audit and a prospectively registered
support/PA/feedback oracle, preserving original error thresholds and full case,
step, graph and lifecycle coverage. An exact-FP32-tie explanation is not an
ad-hoc epsilon or task-accuracy allowance. Current probability-GQA variant must
not be described as byte-identical to official logit-GQA.

## Actual KIVI004: complete CPU packing/readout only

MAIN caught003's delivered full-CPU output name being rejected by a stale
tiny002 regex before launch.003 is NOT_RUN_NOT_ADMITTED, not an algorithm
failure.004 changes only three controller identity literals; inside/resources/
consumer and all10 mathematical source pins are unchanged.
Source root:
`/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-cpu-host-v1-004`
SOURCE SHA c625ba8b224da03e9bdccf6cba15a5bf8f5556cae4a8b8ce1d236370b5430b8b.
MAIN122d22 software checks0/741ms exercise the actual execute predicate,
positive/negative output paths, no-overwrite and publication failure paths.
MAIN122e completed0/37820ms: all four2/4bit x FP16/BF16 full CPU packing cases,
not just the earlier serialization probe.
MAIN1232 independent consumer completed0/271ms: CPU_ONLY_RAW_CONSUMED;
actual producer/consumer processes and raw words/independent compact readout
checked. HOST_RESULT SHA
c005910987b4b134d99393b0c96988796fcbe54d653ee8ba23114c66ee5f2ffa.
Run root:
`/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-cpu-host-004-main-20261008-01`.
Exact CID b71f17cd365f44460fb0fb0b545eacd84761fa93e20bbcec0b3a2afeead869da
stopped-retained. Whole122d/122e/1232 originals saved in source root.
native_ready=false, model_ready=false, npu_executed=false.
Next: the full176 native matrix producer/independent consumer/owned host.
The existing8-eager GUEST_NATIVE is not the176 matrix and cannot inherit this
CPU result as NPU permission.

## Source-copy observer lesson

MAIN1234 genuinely copied three public Python files from the exact stopped
owned Devices[] guestcdd4a68f..., but parent exit1 compared unordered Docker
Mounts arrays positionally. All3 cp commands exited0; Id/Image/State/ExecIDs/
Config/HostConfig were identical before/after. Unique Destination keyed full
mount records were identical, with order only changed.
Preserve1234 exit1. MAIN1236 independent read completed0/47ms and rehashed all
three actual files; no Docker copy/start/exec retry.
Root:
`/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-public-model-runtime-source-v1-001`
ORIGINAL_MAIN_1234_OPERATION.json SHA
65aa0458423ad67cf7edf46dcae43c1ec6448ee0586a9a1734729d7e34842081.
COPY_IDENTITY.json and ORIGINAL_MAIN_1236_CONSUME.json retain failed-parent scope.
This admits source provenance only, not runtime attach/model readiness.

## Ready queue and bounded next action

Three authorized agents continue independent source/API preparation. MAIN alone
runs/admit/cleans devices and Git. SparsePrefix v5 has44 software checks and a
real4-worker child but its aggregate host admission/controller is still being
completed: it is NOT yet once-run model-ready. Register diagnostic4 guestCPU+
1MAIN+2reserve=7 with remote prep CPU commands paused, unchanged all4 ranks/
48native GDN layers/full six-family byte corpus. Source/API preparation may
continue without remote CPU jobs. Ordinary memory is now sufficient; current
card idle gaps are incomplete entrypoint/numerical preparation, not evidence of
external card occupation. Never insert dummy loads.

Do not repeat deterministic failures unchanged or reset deadlines. Preserve
OFF code and exact failures while progressing source->NPU->actual model->
same-stack paired E2E->final tasks. Push remains blocked by previously proven
unchanged authentication; no credential bypass or redundant retry.
