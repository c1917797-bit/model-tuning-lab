# MXR Qwen3.6 Ascend Piercing

## Terminal decision — no-go on the current service objective

This workstream closed at `2026-09-19T21:44:00Z`, inside its fixed 24-hour
window, as `no-go` for the pinned Qwen3.6-27B / Ascend 910B4 /
vLLM-Ascend v0.23.0 path. The algorithm is not rejected as numerically invalid:
the official staged PTO and MegaGDN candidates passed real-NPU chained
output/final-state comparisons and bitwise replay at the exact TP4-local
geometry `H=12, Hg=4, D=128`.

The terminal reason is service opportunity, not correctness. Direct MXR
triangular inversion is about `3.158x` faster at length 4096 and `3.140x`
faster at length 16384, but the incumbent triangular-inversion kernels occupy
only `2.93%-2.96%` of the measured prefill NPU interval and do not execute in
decode. The optimistic prefill-NPU reduction is therefore about `2.0%`, below
the predeclared roughly-5% integration gate and irrelevant to the long 1024
token decode target.

The wider official six-stage MegaGDN route was also screened so that a narrow
MXR attribution would not hide a larger fusion opportunity. Those six service
kernels occupy `10.84%-10.87%` of the measured prefill NPU interval. At the
same 32768-token shape their rank-mean incumbent cost is about
`9.335 ms/layer`; official `pto_mega` measured `8.589 ms/layer` (`1.087x`),
while staged PTO measured `10.127 ms/layer`. The implied prefill-NPU saving is
about `0.87%`, before any BF16/FP16 adapter cost. It also misses the
predeclared `1.10x` target-shape threshold.

Primary immutable evidence:

- candidate numerical gate:
  `/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v8/numerical-gate.json`,
  SHA256 `ab112ae3ee4e2cf91af2399ccf18f65caf159831998f99b976dad7eff3dafa2c`;
- direct triangular timing:
  `/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v10/triangular-target-shape-timing.json`,
  SHA256 `5d32bf31804152fa283dca5e449332908029f913b5cedd47f104378fb3d14d98`;
- full staged/megakernel timing:
  `/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v11/full-gdn-candidate-timing.json`,
  SHA256 `d73b662c9d0fcc96029e665e0fd4d3c3a10b329c28050e6794640a1debbf9bb7`;
- real-service profile summary:
  `/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/prefill-mc2-mixed-v1/profile-current-v1/baseline/profile-summary.v1.json`,
  SHA256 `b3bddd3b1a8b96571f20c59d801aa21da3da673f875f86a3b04318afbdb480a8`.

No service monkeypatch, matched E2E A/B, LongBench-v2, or GSM8K result was
produced for MXR, because the candidate failed the admission bound before
those expensive stages. Do not state that task accuracy regressed or passed.
Do not rerun v1-v11 unchanged. The next portfolio item is KVBuffer, using
physical NPU4-7 and beginning with a measured decode-IO opportunity bound.

## Current state

The workstream has completed pre-NPU preparation, but the first NPU gate did
not reach MXR code. No MXR NPU correctness, performance, or quality result
exists yet. A fresh preflight at 2026-09-18T15:21:44Z found physical NPU4-7
process-free and all frozen source, submodule, and image identities correct.
The immutable first-attempt root is
`/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v1`.

The first gate and four narrower follow-up canaries all failed during
`torch_npu` lazy initialization with `aclInit` error `507899`,
`Resource_Busy`, and `drv devId=0 invalid`, before any official or candidate
MXR code executed. Physical NPU4-7 remained healthy, had no device-side
process, and stayed at their idle-HBM baseline. This is an environment gate
failure, not an MXR numerical or performance result.

The failed matrix covered: physical NPU4 mapped alone to logical 0; physical
NPU4-7 mapped to logical 0-3; host network plus host cgroup namespace; preserved
physical `/dev/davinci4-7` names; corrected logical index 0 after
`ASCEND_RT_VISIBLE_DEVICES=4`; and the documented pair
`ASCEND_RT_VISIBLE_DEVICES=4` plus `ASCEND_DEVICE_ID=0`. Do not rerun these
unchanged combinations.

On 2026-09-19 the user-authorized `dias-cont-1` recovery completed. SIGTERM
did not terminate its PID-1 `sleep infinity`, so the authorized stop required
SIGKILL. The task disappeared, its container metadata was preserved, namespace
ID 0 and the all-device UDA claims disappeared, and physical NPU4-7 remained
process-free. Exactly one unchanged non-privileged canary then mapped only
physical NPU4 to logical device 0 and completed a real synchronized tensor
operation on `Ascend910B4` with value `1256.0`. This proves that releasing
the UDA owner repaired ACL initialization without a driver reset.

The subsequent immutable `npu-gate-v2` attempt nevertheless failed before
MXR code at `torch.npu.set_device(0)`. A new external containerd task,
`dias/agentgpu-910b4-qwen35-4b-v0`, had been created at
2026-09-19T20:40:31Z between the successful canary and the gate. Its root PID
3523970 runs `sleep infinity`, its OCI spec exposes `/dev/davinci0-7`, and
`/proc/uda/namespace_node` maps its namespace ID 0 to all eight devices.
Kernel records for the failed gate report `Conflict open udevid
(udevid=4; ns_id=0)`. `npu-smi` still reports no compute processes.

The immutable second-attempt root is
`/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v2`; do not overwrite or
rerun it. The new external task is not covered by the authorization that named
`dias-cont-1`; do not stop or delete it without new explicit approval. A
future attempt must fail closed on current UDA ownership and keep the real
canary plus MXR probe in one long-lived device-scoped container namespace.

At the same time, `combine-only-ep4_nk` is a foreign privileged container with
all host devices visible and active workers on physical NPU0-3. Another
privileged development container also has all devices visible. `npu-smi` does
not show either using NPU4-7, so their causal role remains unproven. Starting a
new temporary privileged diagnostic was rejected by the safety boundary and
requires explicit user approval. The other safe branch is to wait until the
all-device privileged workload exits, then run only the minimal container
canary. A successful canary must precede a new immutable `npu-gate-v2` root.

On 2026-09-19 the `combine-only-ep4_nk` service had exited and all eight NPUs
were process-free at idle HBM. Re-running one evidence-backed non-privileged
canary still failed. The host kernel log supplied the missing root-cause class:
it repeatedly reported
`uda_occupy_dev_by_ns: Conflict open udevid (udevid=4; ns_id=0)` for the canary
process. `lsof` showed no process holding the target device files. This proves
that the blocker is an Ascend UDA device-namespace reservation, not visible
compute/HBM occupancy and not MXR code.

The user explicitly authorized the discriminating Maxon test on 2026-09-19.
`docker stop --time 30 Maxon4ick_torch_910_dev` completed successfully; the
container was not deleted and remained `Exited (137)`. A fresh precheck showed
physical NPU4-7 process-free, AICore idle, and at the 2868-2869 MiB HBM
baseline. The single authorized non-privileged canary then failed before its
first tensor operation with the same `aclInit 507899`, `Resource_Busy`, and
`drv devId=0 invalid` error. Kernel records for 19:34:36-19:34:45 UTC tied the
canary PID to repeated
`uda_occupy_dev_by_ns: Conflict open udevid (udevid=4; ns_id=0)`.

This falsifies the hypothesis that the still-running Maxon process was a
sufficient cause of the current conflict. It does not identify the original
namespace owner or exclude stale state left by an earlier container. Do not
restart or delete Maxon, do not rerun the same canary, and do not create
`npu-gate-v2`. The next executable action is an operator-approved,
rollback-defined driver/UDA namespace recovery; an NPU reset or driver/service
restart is outside current authorization. No MXR code ran, so there is still no
MXR numerical, performance, or quality result.

The target checkpoint is `/cache/efim/Qwen3.6-27B`. Its global GDN geometry is
16 key heads, 48 value heads, and 128 dimensions for both key and value. Under
TP4 the local target shape is therefore `Hg=4, H=12, Dk=Dv=128`, matching the
official PTO kernel's supported dimension and GQA ratio.

Exact official source archives are retained outside Git under
`/cache/cch/paper-sources/mxr-tri-inverse-20260918/`. The MegaGDN archive is
pinned to `d357fd38608f99ddf9b9fb2d217b2e731ecd3a72`; the PTO kernels archive is
pinned to `282ed20bbe9777f47370e7e4e2c2bd9df7f7ad37`. Do not silently update them.
The exact MegaGDN submodule pointer was recovered from the Git tree and checked
out from `https://gitcode.com/cann/pto-isa.git` at
`01666f3b386f296c95e6e05825fe63b8e6bb4ef4`.

`run_npu_gate_v1.py` is the frozen first-attempt controller. Its self-test and 19
focused CPU/control-plane tests pass. It checks both official archive hashes,
the exact PTO-ISA commit, the pinned v0.23 image ID, an unused container name,
and process-free physical NPU4-7 twice before creating the immutable result
root. It maps only physical NPU4 to logical device 0, monitors NPU4 ownership
and requires NPU5-7 to remain process-free. It never retries. It has already
been executed once and must not be reused or overwrite its result root. Use
`--preflight-only` only as a read-only resource check; create a v2 controller
only after the exact planned container canary initializes and computes once.

The NPU probe runs three chained segments at the TP4-local Qwen shape and
compares output plus the complete final state against the official double
reference. It also requires bitwise same-input replay. Timing is admitted only
after correctness and separately reports v0.23 versus MXR triangular solve,
staged six-kernel PTO, and fused MegaGDN. A 1.10x median speedup at both 4K and
16K local-token shapes is the predeclared clear-advantage threshold; this is an
operator gate, not an end-to-end acceptance claim.

## Important audit findings

- vLLM-Ascend v0.23.0 imports the chunk GDN function into
  `vllm_ascend.ops.gdn` and uses it for prefill. Its exact audited `gdn.py` hash
  is `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`.
- A later upstream main snapshot already probes and uses
  `torch_npu.npu_chunk_gated_delta_rule`; its audited `gdn.py` hash is
  `d26e15be45ec8a8bb84dab546d8a54963f75f90d0ae1b9fa0ce4167e73b01895`.
- Therefore v0.23 needs an opt-in replacement, while the v0.27 adapter must
  delegate to the native fused path by default and only override it for an
  explicit, evidence-backed comparison.
- The official `install_hook.py` edits the installed vLLM-Ascend package. That
  violates this repository's delivery boundary and must not be used in final
  integration.
- The official full wrapper falls back when a non-zero initial state is
  present. It is primarily a fresh-prefill path, not a decode optimization.
- The official aggregate accuracy helper contains a weak elementwise test
  (`all()` instead of `any()`) and scales `rtol` up to 0.5. It is not accepted
  as our correctness gate. We require finite output/state, explicit max/mean
  and Frobenius errors, quantiles, and repeated multi-step state evolution.
- The MegaGDN repository root has no license file, but its triangular inversion
  sources explicitly refer to the Clear BSD license in `huawei-csl/pto-kernels`.
  Do not vendor the rest of MegaGDN until every copied file's license provenance
  is resolved.

## Version-independent delivery boundary

`projects/mxr_vllm_ascend` owns configuration, source identity checks, adapter
selection, evidence, and eventually the custom kernel. Core code must not
import version-specific vLLM internals. `v023` and `v027` adapters are thin
routing layers only. Activation is disabled by default and fails closed on an
unknown version, unknown `gdn.py` identity, missing backend, or v0.27 native
fused-path override without explicit authorization.

## Admission order

1. Source/license/build audit with exact hashes.
2. One NPU compile and target-shape output/final-state correctness matrix.
3. Target-shape timing for baseline, MXR-only, staged PTO, and full megakernel.
4. v0.23 plugin service canary and matched dense A/B.
5. Three-run formal performance only for a promising candidate.
6. LongBench-v2 and GSM8K with thinking disabled, `max_tokens=2048`, normal EOS.

Kernel timing is diagnostic evidence, not an end-to-end claim. Full-megakernel
gain must not be attributed solely to MXR triangular inversion.

## 24-hour terminal deadline

The user imposed a hard one-day wall-clock limit per paper at
`2026-09-19T19:52:15Z`. This MXR slot therefore ends no later than
`2026-09-20T19:52:15Z`. Queueing, waiting for devices, environment recovery,
build time, debugging, experiments, and reporting all consume the same window;
the clock is never paused or reset.

At the deadline this workstream must close as exactly one of `go`, `no-go`,
or `environment-inconclusive`, preserve a recoverable handoff, and activate
the next portfolio item. An environment-inconclusive result is not an
algorithm failure, but it still closes this slot; reopening requires an
explicit reprioritization and a new slot.

At activation time, an external Qwen3.5 TP4 workload was using physical
NPU0-3. Physical NPU4-7 remained process-free, but the proven UDA namespace
conflict still prevented initialization. Host-wide driver/module recovery is
therefore prohibited because it could disrupt NPU0-3. Do not rerun the
deterministically failing canary. Continue read-only blast-radius and
device-scoped recovery analysis; if a safe, separately authorized recovery
makes the exact canary pass, immediately create and run `npu-gate-v2`.
Otherwise close MXR as environment-inconclusive at the deadline and move to
DeltaLog.

Physical NPU4-7 are the invariant device set for the entire paper portfolio.
NPU0-3 are not a fallback even when idle. Before closing this slot, extract the
reusable paper-to-Ascend lessons (method parity, runtime seam, operator/CANN
adaptation, numerical gates, attribution, failures, and portability boundary)
into the maintainer skill as well as this workstream evidence.

A read-only audit at `2026-09-19T20:07:43Z` found a non-Docker containerd
task that earlier Docker-only checks did not cover. Namespace `dias` contains
`dias-cont-1`, created at `2026-09-18T13:20:32Z` and still running
`sleep infinity`. Its OCI specification exposes `/dev/davinci0-7`, manager,
SVM, and HDC devices and sets both visible-device variables to `0,1,2,3,4,5,6,7`;
it also sets `ASCEND_RUNTIME_OPTIONS=NODRV`.

The ownership is now proven rather than inferred. `/proc/uda/udevice` reports
udevid 0-7 as used by container namespace ID 0.
`/proc/uda/namespace_node` maps namespace ID 0 to
`root_tgid 1619069` and lists udevid 0-7; PID 1619069 is exactly the
`dias-cont-1` root `sleep` task in cgroup `/dias/dias-cont-1`. The installed
driver source in `uda_access.c` shows that root-process exit schedules
namespace destruction, which calls `uda_uninit_ns_node_dev`,
`UDA_UNOCCUPY`, and `uda_unoccupy_dev_by_ns`. This makes stopping only that
task the narrowest evidence-backed recovery, without a driver reset.

At the same observation, an external TP4 workload was active in a different
Docker mount namespace on physical NPU0-3 while NPU4-7 were process-free and
at idle HBM. Do not mutate `dias-cont-1` without explicit user approval. The
next discriminating action, if approved, is stop-but-do-not-delete followed by
verification that namespace ID 0 disappears and exactly one unchanged
non-privileged canary. Preserve all evidence and do not touch the NPU0-3
workload.

## Stop rule

Stop this workstream and advance to the next portfolio item, DeltaLog, if
target-shape NPU timing shows no clear advantage, if an evidence-based
end-to-end bound remains below about 5%, or if the hard deadline is reached.
Do not spend another open-ended cycle on wrapper integration without a
kernel-level reason.
