# Prefill readiness checkpoint — 2026-10-06

This is reviewed, default-OFF preparation and actual no-device evidence, NOT a
DAMP performance/accuracy result. Canonical repository:
`/opt/host/vnf/austinov/model-tuning-lab`;
branch `work/qwen36-damp-ascend-20261006`.
The56 exact source hashes/publication boundary are in
PREFILL_READY_SOURCE_SCOPE.json. Five frozen dependencies were already tracked;
51 reviewed files are newly published. Draft observer, selected NPU gate,
final/calibrated admission and older smoke/service packages are not included.

## Actual completed evidence

- MA0526 float probe: compiled/exported/load/schema/Meta pass, no devices.
  Output `/cache/cch/qwen36-damp-20261006/prefill-float-build-v1`.
  SO80a06b48be444fbef9a37f7c9857c95518b8181cb8b5ba5ac6a1a21002cb85c0;
  build receipt7696732308c3dc7c9565cb91b471cf3df268cc94f59cde292c46dfaad60a6baf;
  Meta3f3991daa82aa3ccf92bc050b5a588749c7ae08956ce921460e23ad219a3436b.
- MA053d selected prefill: actual CXX/ASC/link/defined symbol/load/schema,
  Meta32 positive+44 negative pass, no devices.
  Output `/cache/cch/qwen36-damp-20261006/selected-prefill-build-v1`.
  SO28684cb4f502ead28fd9974a54f420d0ec027de19ccc6728ba3942209fc910d7;
  receipt50f161e606a7faa567b7588300f526f3294c7ecfbf69a88edaa8898b09d1825f;
  Metacc532ccc88bde7987f0f19bba9efddec8894a0f4f5a56b27d284980fcf429f78.
- MA054e MAIN independently passed16 continuous-core+35 cache-identity stdlib
  contracts. This is source-bound CPU/software evidence, not live scheduler
  observation or shared FA/GDN NPU cache acceptance.
- MA052d MAIN passed14 all-T controller contracts/default dry CLI. Controller
  remains default OFF and needs actual MA0455 terminal receipt, full source lock,
  completed parent result, fresh canaries and joint resource admission.
- NEW fixed-address4-file packet received full MAIN source review.
  MAIN independently passed all96 stdlib checks in MA056a, including11 fixed
  buffer contracts. The enclosing harness then failed because it assumed
  every default CLI contained a launchable field; the all-T CLI instead uses
  its pinned dry-plan-not-executed/no_docker_or_npu schema. Preserve MA056a
  exit1. MA0574 separately passed that actual source-bound CLI contract with
  no source/device change. Neither check is NPU evidence.

## Preserved static audit

MA0541 source-bound CANN audit copied tooling into an isolated output, preserving
the reference repository. Raw scan reports7 synchronization candidates, not
seven newly confirmed faults. The first flow invocation failed on unsupported
--frontend auto; preserve `prefill-sync-audit-v1` and its failed receipt.
MA0544 corrected flow run is separately stored at `prefill-sync-flow-v2`;
RESULT SHA67a0d924289dd81014f65c6a8e754a10ae2eb715dc31d0bd9b46fa4eb89ff5d9.
Actual VectorToScalar V_S Set/Wait helper is called before relevant scalar
reads; purported early return259 is an event declaration, and valid-failure
return262 follows Set/Wait. Probe invalid-tiling return30 precedes event use.
Metadata UB DataCopy lowering still needs actual API/device proof.
Neither zero flow findings nor manual rationale replaces NPU synchronization,
sentinel, changed-input or multi-step tests. Frozen kernels were not changed.

## Live chain and immediate resource schedule

MA0455 is the only owned TP4 job and must be polled, never duplicated:
`qwen36_damp_full_reference_resume_20261006_v1`, ID
b6e2a1510fb809d0913ee214d28cf0df238930eadd1e39189eba54b0d2f9e1f1.
Fresh MA0556 at16:29:22Z sees ON16/36 completed4096-token TRAIN clients, parent
running/no OOM. It is calibration collection, not formal1024-token timing.
OFF36 complete is reused unchanged. No full SOURCE_LOCK/RESULT, fitted192
plans, candidate service, E2E or final task result exists yet.

After successful terminal capture: persist actual terminal receipt+hash outside
Git, confirm exact owned parent stopped, and run fresh release/canary checks.
Then admit four disjoint all-T numerical shards jointly40GiB/quota4, optional
CPU fit jointly44GiB/quota6 (only after fresh ordinary-memory/CPU proof).
The new fixed-address float and selected-prefill gates may run on disjoint
physical cards only after their dependency/packet review and fresh MAIN
admission, not concurrently with TP4 capture or formal timing.
Do not invent canary/plan/runtime hashes to make a command appear runnable.

Remaining device chain: actual float bits, selected native-prefill packing,
arbitrary-SR calibrated192 plans, all actual batch sizes, shared FA/GDN lifecycle,
continuous/mixed/continuation service, matched dense timing and task accuracy.
A software pass/build/push is not a stop point or a usable candidate claim.

DAMP cutoff remains2026-10-07T08:48:03Z; portfolio cutoff2026-10-09T11:17:31Z.
Latest human task-loss allowance is<=1% E2E; report both percentage-point and
relative changes and preserve original no-loss audit. Never relax internal
numerical gates. Only physical4–7; protect0–3. Final timing is exclusive with
no profiling/CPU-build competition. No training/distillation/MTP bypass.
