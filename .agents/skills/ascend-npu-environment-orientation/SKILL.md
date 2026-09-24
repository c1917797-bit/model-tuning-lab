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
7. Run a minimal inference canary and capture a controlled-side event proving
   the intended NPU device executed the workload.
   If host `npu-smi` reports no compute PID but a new container reports zero
   HAL devices, inspect kernel UDA conflict messages and read
   `/proc/uda/namespace_node`. Map the matching `udevid` and `root_tgid`
   through `/proc/<pid>/cgroup` to the exact container, then inspect its
   process tree and mounts. An idle HBM/AICore reading does not rule out a
   namespace-level device claim. Do not repeat the same failed canary or
   relabel the failure as an operator numerical result.
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
- Do not stop a container merely because it declares the target cards. For an
  actual UDA conflict, identify the exact owner first. If the owner also maps
  protected cards, preserve that boundary; do not bypass a rejected stop via
  namespace sharing, `docker exec`, or another indirect route. Request a
  separately authorized, narrow resolution while continuing unaffected work.

## Output

The experiment record contains an `environment` section, evidence commands,
sanitized results, external artifact hashes or paths, drift status, and the Git
commit that established the baseline.

## Verification

- Every identity field is present or explicitly marked unavailable.
- Source and image identities are immutable hashes, not mutable labels alone.
- The canary identifies the expected physical NPU and execution process.
- No secret or large binary artifact is staged.
- The orientation checkpoint is clean, committed, and pushed.
