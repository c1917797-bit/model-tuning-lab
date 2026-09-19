# MXR Qwen3.6 Ascend Piercing

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

## Stop rule

Stop this workstream and move to KVBuffer if target-shape NPU timing shows no
clear advantage, or if an evidence-based end-to-end bound remains below about
5%. Do not spend another open-ended cycle on wrapper integration without a
kernel-level reason.
