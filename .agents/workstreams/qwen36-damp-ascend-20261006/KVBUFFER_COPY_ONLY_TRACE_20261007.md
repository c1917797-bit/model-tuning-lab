# KVBuffer copy-only trace checkpoint — 2026-10-07 12:05Z

## Decision and original failure

native_order_v2 production77b4 remains NOT numerical-matrix accepted.
Original B16 MA0a60 graph trial0/step37 active12 output0.003048780487804878
exceeds0.00303, while state/head errors pass2e-6. Original raw ff6c632f...,
frozen source64 manifest508ff442... and production/native binaries remain
unchanged. No new E2E throughput or LongBench-v2/GSM8K result is claimed.
One-ULP saved-output analysis is not task acceptance.

MA0abb selected physical6 saved-step attempt also failed before candidate
dispatch: protected0–3 PID/starttime changed during canary. MA0ac0 independently
identified outside HYPIC workers on0–3 and verified the exact own b977... CID
stopped/retained/Pid0/noExec/noOOM and source64 unchanged. No outside job stopped.
It is not a KVBuffer numerical failure. Earlier MA0a8a outside profiling was
physically5 (MA0ab3 original SMI), not4; the attribution correction is retained.

## Source and build evidence

Independent candidate_ub_trace_v1 was committed bdba855. MA0ad4 real no-device
CANN compile failed at TraceCopy header L450: unsigned long byte count cannot
narrow implicitly to uint32_t in aggregate initialization. Original build root:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/build-candidate-ub-trace-v1-20261007-1140
Original command-1.json SHA:
 bf67e9fa83ba1f3d98d6077262cb484cd5e0246fbf3940d5f44718ba776c6188
Its owned7434... compile container was stopped/retained; no NPU mapped.
No build/Meta PASS receipt exists for v1.

NEW candidate_ub_trace_v2 is a separate namespace/source/output root, changing
only bounded explicit uint32_t conversion plus version identity and factual
documentation. Original math/storage/gates unchanged. Source checkpoint:
 82adc9f91f34306e3c36b473e85b629f00222e94
Actual MA0ae5 software14+15 and MA0ae8 host8 passed (37total), not NPU evidence.
MA0ae3 harness newline SyntaxError remains retained; corrected only harness.
V2 manifest:
 176e585c18ef60b449919dffe4e73015c2fe687a56b92f77c5daf3d0524e512f
V2 builder e01f148a..., meta4c3f1c3f..., host3d4a0e08..., entryd8bdf781...
are exact actual source-bound code. Source closure77, complete host closure80.

MA0ae9 real no-device compile/link/export/dlopen/schema/Meta completed0.
2 positive and12 negative Meta cases passed, NPU/numeric/service flags false.
Build root:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/build-candidate-ub-trace-v2-20261007-1157
SO SHA:
 76ed09c737cf9d9940083bf30b1f82c69f0e0bce81e25d81526da3a4790454cd
build-receipt.json SHA:
 dd10951c44d92510bdc5cb6da22d497138530317fe7f54e4d574bef45166bbd0
meta-receipt.json SHA:
 4271324b1afd6ee80e266ce36310db9019f159c35f07c1f5702d09ce3bd91bb7
MA0af9 independently checked actual original commands/export/meta child receipts,
all sources and owned0118... stopped/Pid0/noExec/noOOM/noDevices.
MA0af7 also exited0 but full-source stdout was truncated; use compact MA0af9.
Retryable MA0add pre-handle timeout recovered idempotently, not duplicate work.

## Currently live operation — poll, do not relaunch

MA0afa (exec-0000000000000afa) is the once-only MAIN NPU diagnostic.
Output:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/candidate-ub-trace-diagnostic-v2-20261007
Container: kvbuffer_candidate_ub_trace_v2_diagnostic_20261007
Physical6→logical0 only; nonprivileged; 8GiB/1CPU+8GiB ordinary reserve;
600s total including90s cleanup. Formal timing/matrix/service authority false.
Fresh canary/actual PID/CID/source identity, full production output/state anchors,
three trace guards and eager+graph saved-step are mandatory. Native exact FP32
precast stays unobserved. Do not infer a causal repair from candidate trace alone.
This note predates its terminal result; no trace numerical result claimed.

## Memory inspection and boundaries

Actual MA0aad/MA0aae then MA0aea/MA0aed readonly inspections show:
1GiB HugeTLB pool1916pages,1892pool-free,24active (OVS). Free reserved pages are
not ordinary RAM. OVS PID27118 also~1.83GiB ordinary RSS; it is active and intact.
At11:56 ordinary MemAvailable62,573,280KiB(~59.7GiB), down from11:24~79.9GiB
during an outside HYPIC0–3 model run. That service's RSS includes shared pages;
do not interpret their sum as private physical memory.
Later cgroup snapshot: cannbench_ds~8.01GiB (RSS3.71/cache4.27), owner unknown;
own no-device compiler~0.52GiB, then stopped; idle agentgpu-v0~0.18MiB.
135 older related containers were stopped/Pid0/noExec. Deletion mostly frees
disk, not RAM. No material deletion, HugeTLB resize or outside stop performed.
Full-model72GiB admission and protected0–3 remain unchanged.

## Goals and successor

This diagnoses the actual KVBuffer deferred-state/native-rounding seam, not an
unrelated operator benchmark. If anchors pass, inspect actual UB seam, then
implement only an evidence-supported algorithm repair and run new numerical
matrix. If anchors fail, retain perturbation evidence; do not lower tolerances.
Mixed/cache/capture service packet and KIVI successor remain preparation-only.
DAMP37/64 is closed at its deadline, not paper-wide rejection.
KV cutoffOct8 08:29:54Z and portfolioOct9 11:17:31Z are fixed, not reset.
Original no-loss audit and latest user task-loss allowance≤1% remain separate
from tensor limits; final task report must give both pp and relative loss.
GitHub normal push still lacks authentication; local checkpoints are not pushed.
