---
name: ascend-npu-environment-orientation
description: Use before running or comparing Ascend NPU inference experiments, and whenever the host, container, model, framework, driver, firmware, CANN, or device topology may have changed.
---

# Ascend NPU Environment Orientation

## Purpose

Bind every tuning result to the exact source, model, software stack, hardware,
and runtime topology that produced it. Reachability or a running process is not
proof that the intended NPU path executed.

## Workflow

1. Create or open `.agents/experiments/<experiment-id>.yaml`.
2. Record source identity: repository commit, dependency revisions, local patch
   state, container image digest, and build flags.
3. Record model identity: model and tokenizer revisions, dtype, quantization,
   sequence limits, parallelism, and non-secret weight identity or checksum.
4. Record software identity: OS and architecture, Python, inference framework,
   PyTorch, torch-npu, CANN toolkit, driver, firmware, compiler, and operator
   package versions.
5. Record hardware identity: Ascend product, device count and IDs, visible
   devices, memory capacity, interconnect or HCCL topology, NUMA/CPU affinity,
   and power/clock mode when observable.
6. Record runtime identity: host versus container boundary, mounts, cache and
   storage locations, environment-variable names and non-secret values, launch
   command, and process-to-device binding.
   Report accelerator ownership as three independent observations: running
   container device mappings, active device-side process IDs with container
   attribution, and current HBM usage. Do not collapse an idle container claim
   into active computation, and do not treat the absence of an NPU process as
   exclusive availability while an overlapping container claim remains under
   an exclusive-use experiment contract.
7. Run a minimal inference canary and capture a controlled-side event proving
   the intended NPU device executed the workload.
   Before creating an immutable experiment result root, run a cheaper container
   canary with the exact planned runtime, device mapping, namespaces, driver
   mounts, and visibility variables. It must complete `torch.npu.set_device`,
   one tensor operation, and synchronization. `npu-smi` showing no process and
   idle HBM is necessary but does not prove that a new container can initialize
   ACL. If the canary reports `aclInit 507899`, `Resource_Busy`, or an invalid
   driver device ID, classify it as a pre-algorithm environment failure. Record
   running privileged/all-device containers and their visibility variables,
   preserve the exact failed configuration, and do not retry it unchanged.
   Inspect host kernel logs for Ascend UDA messages. In particular,
   `uda_occupy_dev_by_ns: Conflict open udevid` proves a device-namespace
   reservation even when `npu-smi` reports no process, HBM is idle, and `lsof`
   reports no ordinary device-file handle. Do not misclassify that state as an
   idle, usable card or as an algorithm failure.
   On drivers that expose UDA procfs, read both `/proc/uda/udevice` and
   `/proc/uda/namespace_node` before considering a reset. The former reports
   the owning namespace ID per physical `udevid`; the latter reports that
   namespace's `root_tgid` and complete logical-to-physical device list. Map
   `root_tgid` through `ps`, cgroups, Docker, and every containerd namespace
   (`ctr namespaces list` / `ctr -n <namespace> tasks list`). Docker-only
   inventory can miss the actual owner.
   When procfs maps the conflicting namespace directly to a live container root
   process, classify the owner as proven rather than merely suspected. Review
   the installed driver's UDA cleanup path when source is available. If root
   process exit schedules namespace destruction and calls `UDA_UNOCCUPY`, a
   stop-but-do-not-delete test is the minimal recovery candidate; a host-wide
   driver restart is not the first action. Stopping an externally owned task
   still requires explicit approval and a preserved identity/rollback record.
   Treat a successful canary as point-in-time evidence, not a reservation. An
   external resource controller can create a new all-device container after the
   canary exits and before the formal gate starts, reclaiming UDA devices while
   `npu-smi` remains process-free. Re-read both UDA procfs tables immediately
   before container creation and fail closed on any target-device owner.
   Because that check still has a time-of-check/time-of-use race, prefer one
   long-lived device-scoped container namespace that performs the minimal real
   tensor canary and, only after it passes, continues directly into the
   numerical gate. Do not release the namespace between those phases. If an
   external scheduler must coordinate allocation, obtain a real reservation
   rather than relying on repeated polling.
   If the operator explicitly approves stopping a suspected privileged
   all-device container, stop but do not delete or automatically restart it,
   verify its terminal state, and run exactly one unchanged non-privileged
   canary. If the same UDA conflict survives, the live-container hypothesis is
   not sufficient: preserve the stopped container and failed canary, do not
   repeat the matrix, and require separate explicit authorization plus a
   rollback plan before any driver namespace recovery, NPU reset, or service
   restart. The suspected container may still have contributed stale state, so
   record the conclusion as discriminating evidence rather than proof of the
   original namespace owner.
8. Compare with the previous baseline. If any material field drifted, declare
   the old and new measurements non-comparable until re-baselined.
9. Commit and push the orientation or re-baseline stage.

## Safety Boundaries

- Never record credentials, tokens, private model contents, or operator secrets.
- Do not infer hardware from image names, configuration, or successful HTTP
  responses; require device-side evidence.
- Do not modify drivers, firmware, clocks, power limits, or system services
  without explicit authorization and a rollback plan.
- Treat host, container, framework, and physical device as separate authorities.
- Never stop, pause, or share an overlapping foreign container merely because
  its mapped devices are currently idle. Preserve the distinction in the
  experiment record and wait for release or obtain explicit owner authorization.
- Do not start a privileged diagnostic container without explicit authorization.
  If ordinary device-scoped containers cannot initialize while a foreign
  privileged container exposes all devices, treat causality as unproven until a
  controlled canary succeeds after release or an explicitly approved diagnostic
  isolates the condition.
- Stopping an idle-looking privileged container can still interrupt interactive
  work. Require explicit approval even when UDA evidence makes that container a
  likely namespace owner. Never reset an NPU or restart driver services as an
  implicit follow-up.
- `ASCEND_RUNTIME_OPTIONS=NODRV`, an idle `sleep` command, and no
  `npu-smi` process do not disprove UDA ownership. The driver's procfs
  ownership table is authoritative for the namespace reservation.
- A canary that exits before the formal workload proves only that the device
  was usable at that instant. It does not make a later container launch safe
  against an external allocator.

## Output

The experiment record contains an `environment` section, evidence commands,
sanitized results, external artifact hashes or paths, drift status, and the Git
commit that established the baseline.

## Verification

- Every identity field is present or explicitly marked unavailable.
- Source and image identities are immutable hashes, not mutable labels alone.
- The canary identifies the expected physical NPU and execution process.
- The exact planned container configuration has passed ACL initialization and a
  real tensor operation before the formal result directory is created.
- Device mapping, device-side processes, and HBM are recorded separately, and
  the declared exclusivity policy is evaluated against all three.
- No secret or large binary artifact is staged.
- The orientation checkpoint is clean, committed, and pushed.
