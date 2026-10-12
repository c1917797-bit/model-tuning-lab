# R76 — numerical-stage fence closure, 2026-10-12

This is a bounded-stage failure/qualification record, not a paper-wide no-go.
The human twelve-hour authority remains09:19:55Z--21:19:55Z; numerical repair
ended15:19:55Z and the six-hour final-verification reserve is unchanged.

## Actual result and intervention

KIVI006 MC exec-0000000000000011 ran3811.238s and terminated exit1.
MAIN intentionally stopped its exact owned container at15:18:47Z so cleanup
would fit the frozen fence. It retained512/640 selected raw-output snapshots;
there is no complete client receipt or independent640 numerical verdict.
The resulting `actual full firstdecode/native-finish client failed` exception
followed that stop. Do not diagnose it as spontaneous algorithm/numerical failure.

Result: `/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-b1-matched1024-DIRECT-FP32-numeric-main-006/RESULT.json`
20751 bytes, SHA256 `46db2ecfd1e6726b5b30e33e344e24b0c73ddb1d8fb189c1541b46dbb5a10d63`.
Secondary errors were empty; cumulative cleanup19.285s.

The exact nonprivileged container was stopped but NOT deleted. Physical4--7
mapping was reverified before stop; Pid0/no ExecIDs/no OOM and all four owned
worker PIDs absent afterward. A fresh resolved `/usr/local/sbin/npu-smi` check
proved no4--7 NPU processes and HBM2869/2866/2867/2861MiB. No0--3 task was
modified. A guessed driver-tools executable path failed before execution and
was corrected by actual PATH resolution; it is not a device failure.

## Evidence scope

Same660 Devices[]173 software pass, the actual short NPU20-case pass, and
first64 whole pass remain valid within their original scopes. They do NOT
prove full1024 numerical/lifecycle coverage, graph correctness, paired E2E,
LongBench-v2 or GSM8K. No new non-HYPIC joint acceptance has passed.
No independent raw640 entry may consume this incomplete producer as qualified.
The AV acceleration proposal remains default OFF, incomplete and unqualified;
its old24 local tests do not cover two new cold-entry files.

AdaKV005 source and SKVQ011 source preparation remain distinct pending
same-image/device/whole-model gates. AdaKV's new B1 normal-EOS observer cold
entry failed on a missing own-source import path before NPU math; preserve
that failure as integration, not method invalidity. No final acceptance ticket
is ready; final reserve is not permission for another repair round.

## Reusable causal corrections

- Source-audit claims need the actual frozen common config: FULL_DECODE_ONLY
  means FULL decode and NONE mixed. A FULL-mixed development blocker was false
  and was retracted; do not alter common config to make an unnecessary domain.
- Exact content-addressed256KiB raw chunks reuse only identical bytes. A naive
 640-times-full-pool capacity estimate is not actual physical storage evidence.
- A source/test count is not executable readiness: cold CLI, report namespace,
  input lineage, output path, reference consumer and cleanup must be tested.
- Validate the real producer's elapsed budget plus independent whole adjudication,
  graph and final tasks before admission. The single-frame oracle cost is not a
  reliable full-matrix promise; required CPU/RAM headroom also constrains overlap.
- Preserve scheduler-caused intervention separately from observed model faults.
  Missing gates mean not effectively validated, not a conclusion against a paper.
- Sparse snapshots cannot prove30-minute continuous utilization or a hang.

## Exact durable closure

All originals remain under `/cache/cch/qwen36-paper-preparation-20261007/lowbit/`:

- `MAIN_R76_FENCE_STOP_ORIGINAL_MC0027.json`11860/ead2609bcef812227a741103314cbab33b924a20fc0fd2aa03988de7fe63273a
- `MAIN_R76_LONG006_TERMINAL_ORIGINAL_MC0011.json`11514/6153b7903733cd9a8e6aa5e142c79e7c362d94e0ccae9d3582a25955aed9b4d9
- `MAIN_R76_RELEASE_SNAPSHOT_ORIGINAL_MC0029.json`15405/a4a3f31ffc83a686c804b37470c026663120f37007f053c4c3ef861fb8a98315
- `MAIN_R76_NUMERICAL_FENCE_CLOSURE_20261012_001.json`4084/d2313cc7e9bf6667e76964241900741a6add2f02394bb5110431f25036907863

Previous push remains UNKNOWN. This knowledge checkpoint is not success, does
not reset the overall cutoff, and does not authorize rerunning unchanged failures.
