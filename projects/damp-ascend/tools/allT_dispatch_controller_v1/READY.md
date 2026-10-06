# MAIN-only all-T correctness dispatcher (NEW, default OFF)

This packet prepares the actual four disjoint synthetic numerical shards for
`qwen36_damp_all_batch_v3`. It is not a general controller, a benchmark, a
service admission, a task-accuracy result or an automatic background run.
This source packet has not itself executed Docker/NPU. Frozen allT plan3,
allT gate7, collector/live28 and every numerical oracle remain unchanged.

## Exact scope and prerequisites

- Physical4→logical0: actual T1–4; physical5→logical0: T5–8;
  physical6→logical0: T9–12; physical7→logical0: T13–16.
- Frozen gate: two value-SR modes (identity/power2), two actual shared-arena
  layouts, 160 changing feedback turns, eight graph resets/replays, full
  typed-state/guard/pointer and malformed metadata/overlap checks. Limits
  remain state head-relative-L2<=1e-5 and output<=0.00303. Do not replace
  real T with padded T1/T16.
- Actual immutable image: 660ce23a…; actual v3 SO: a802d258…; build receipt:
  a9c8a682…; source manifest: a115f00e…; runtime gate manifest: 1755f390…;
  actual native manifest: 6eb9c6d5…. Full hashes are pinned in frozen plan3.
  Nine compiled and20 runtime sources, genuine build/export, actual full
  runner Meta32 positive/46 negative and native document/source are checked
  before container creation. Same-image candidate/native SO bytes are
  checked again inside each new container before any Torch/NPU canary.
- Requires MAIN's persisted original AWMCP MA0455 terminal structuredContent
  and its actual SHA. It checks peer_direct/exact MA peer and the authoritative
  found/job exec record completed0, not outer `ok`. It does not poll remote
  handles, contain credentials, infer terminal state or turn a failure into
  success. Source-bound parent RESULT and SOURCE_LOCK must be finalized with
  actual hashes; exact parent container b6e2a151… must be inspected stopped.
- Fresh process/HBM/AICore envelope is reused from the pinned actual host
  helper. Device-node holders and UDA declarations are recorded; idle device
  declarations are not killed. Actual 4–7 workers block creation.
  No external containers or processes are stopped. NPU0–3 PID/start/cgroup
  fingerprints must remain unchanged; a change conservatively aborts this
  controller without signalling external work.
- One fresh nonprivileged one-card container per shard; necessary control
  nodes only; no network, no capabilities, no-new-privileges. Repository,
  build, reference source, exact native manifest and driver mounts RO.
  Only that shard's new result directory is RW. Every actual inspect is
  checked against the exact prepared argv, image, devices, labels and mounts.
- Each correctness shard gets1 CPU and8 GiB cgroup, no swap. Initial ordinary
  RAM>=40 GiB (32+8reserve), actual Docker NCPU>=6 and result disk>=8 GiB.
  If MAIN explicitly allows one already-existing pinned2CPU/4GiB CPU-only
  selector, RAM>=44 GiB (32+4+8reserve), totalquota6. This controller never
  starts a selector. Default rejects fit overlap. Formal performance must
  not run with this numerical controller or the selector.
- Actual cgroup v1/v2 accounting and CPU quota are checked after each start
  and during numerical runs, respecting mount roots and exact PID cgroup
  components. Conservative mount headroom2560 at admission and512 at
  runtime is a policy reserve, not a proved peak upper bound. Neither
  mount-max nor HugeTLB or external workloads are changed.
- NEW run ID/output/name only, no overwrite/restart/retry. Names cannot be
  inferred absent from a Docker-daemon error. Result directories must not
  exist. SOURCE/actual inspections/engine NCPU/stdout/stderr receipts are
  written before later stages.

## Execution is a MAIN decision, not source preparation

Default dry-plan reads/hash-checks sources, actual old build/native/Meta
artifacts and prints incomplete fresh commands; it does not execute Docker,
load Torch, create output directories or claim any current idle/card fact:

```text
/usr/bin/python3 -B projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py
/usr/bin/python3 -B projects/damp-ascend/tools/allT_dispatch_controller_v1/test_controller.py
```

The first command must be invoked from canonical repository:
`/opt/host/vnf/austinov/model-tuning-lab`.
Software tests include synthetic fixtures and temporary JSON files. They
exercise safety contracts, not devices or the actual future resource lease.

Only after MAIN fully reviews this packet and the persisted successful
parent evidence, the actual execution invocation has both an explicit
flag and an explicit environment opt-in. MAIN fills real receipt paths
and full SHA strings; none are generated as pass by this source packet:

```text
DAMP_ALLT_DISPATCH_CONTROLLER_EXECUTE=1 /usr/bin/python3 -B projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py --execute --run-id v1 --packet-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/allT_dispatch_controller_v1/PACKET.json --packet-sha256 ACTUAL_PACKET_SHA --parent-operation-receipt ACTUAL_MAIN_PERSISTED_MA0455_JSON --parent-operation-sha256 ACTUAL_OPERATION_SHA --source-lock-sha256 ACTUAL_SOURCE_LOCK_SHA --parent-result-sha256 ACTUAL_PARENT_RESULT_SHA
```

`--allow-cpu-selector` is optional and is not an authorization to launch or
stop the selector. The four gate argv and native ABI/source arguments are
the frozen plan's existing real values; only the actual canary/device-proof
hashes are appended after observed success. Docker exec/stop targets use
confirmed immutable container IDs, not merely names.

## First failure and cleanup

Four canaries are foreground controller-owned concurrent local exec clients,
fixed90s timeout; actual result JSON is only produced from successful raw
output. Physical mapping authority comes from actual inspect and fresh host
checks, not from a device-name string. Only then are four numerical shard
exec clients dispatched, fixed3600s phase timeout under the unchanged DAMP
deadline **2026-10-07T08:48:03Z**. TTLs/thresholds/seeds are not extended.
No daemon, scheduler, automatic retry or background launch is installed.

Each raw stdout/stderr and command receipt is retained. On first exception,
FAILURE.json preserves the original error and nullable partial gate reports
before cleanup; secondary copy errors do not replace it. Unknown Docker
create outcomes are not re-created or guessed to be owned; they require
MAIN inspection. Only already-confirmed exact owned IDs are stop-retained,
with pre/post identity proof; no delete operation exists. Local docker-exec
clients may be terminated on another shard's failure, but no arbitrary host
PID is signalled. Stop and release failures have separate retained records.

Runtime monitors record actual protected identities, owned NPU PID cgroups,
actual memory/CPU quotas, self+daemon mount namespace headroom, ordinary RAM
reserve and disk. Post-release reuses the actual idle helper and verifies
target process emptiness/protected identities. A failure is scoped to the
implementation/resource/numerical gate; never a paper-wide no-go.

Four terminal reports must match the exact frozen source/runtime/SO/build
hashes before the original source-bound64-case validator is applied.
Only after all reports and stop/release proofs pass may RESULT state
restricted synthetic allT correctness dispatch. This is **not** arbitrary
SR/final192plans/prefill pack/service lifecycle/throughput/GSM8K acceptance.
The frozen allT graph gate itself owns numerical results; compiler/Meta or
this stdlib packet cannot substitute for them.
