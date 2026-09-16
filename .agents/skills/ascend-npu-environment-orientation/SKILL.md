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

## Output

The experiment record contains an `environment` section, evidence commands,
sanitized results, external artifact hashes or paths, drift status, and the Git
commit that established the baseline.

## Verification

- Every identity field is present or explicitly marked unavailable.
- Source and image identities are immutable hashes, not mutable labels alone.
- The canary identifies the expected physical NPU and execution process.
- Device mapping, device-side processes, and HBM are recorded separately, and
  the declared exclusivity policy is evaluated against all three.
- No secret or large binary artifact is staged.
- The orientation checkpoint is clean, committed, and pushed.
