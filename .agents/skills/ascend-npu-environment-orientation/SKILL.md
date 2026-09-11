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
8. Compare with the previous baseline. If any material field drifted, declare
   the old and new measurements non-comparable until re-baselined.
9. Commit and push the orientation or re-baseline stage.

## Model identity proof ladder

Treat model identity as multiple independent authorities rather than one name.
At minimum distinguish:

1. artifact provenance: repository/model card, revision, shard/index checksums;
2. architecture metadata: config `architectures`, `model_type`, dimensions and
   tokenizer identity;
3. live runtime identity: the exact model path/revision in the serving process,
   container mount/view, load format, adapters and tensor-parallel topology;
4. presentation identity: served-model/API alias and metrics labels.

An API alias, directory name, architecture class, or `model_type` is not by
itself proof of the checkpoint version. A newer checkpoint may intentionally
reuse an older architecture implementation. When the exact checkpoint matters,
prove the live process resolves the intended files and bind the result to
non-secret artifact hashes or upstream-published checksums. For bind-mounted
weights, comparing the host file with `/proc/<pid>/root/...` or equivalent
container view is stronger than trusting a launch string alone.

Do not compute multi-gigabyte model hashes inside an active latency benchmark
window. Prefer a pre-measurement identity checkpoint or previously verified
immutable hashes. If identity verification overlaps measurement, record the
overlap as benchmark interference rather than silently treating the run as
clean.

## Safety Boundaries

- Never record credentials, tokens, private model contents, or operator secrets.
- Do not infer hardware from image names, configuration, or successful HTTP
  responses; require device-side evidence.
- Do not infer checkpoint generation from the served-model alias or architecture
  class alone; prove the artifact and live file identity when version matters.
- Do not modify drivers, firmware, clocks, power limits, or system services
  without explicit authorization and a rollback plan.
- Treat host, container, framework, and physical device as separate authorities.

## Output

The experiment record contains an `environment` section, evidence commands,
sanitized results, external artifact hashes or paths, drift status, and the Git
commit that established the baseline.

## Verification

- Every identity field is present or explicitly marked unavailable.
- Source and image identities are immutable hashes, not mutable labels alone.
- Model-version claims identify which authority proved artifact provenance,
  architecture metadata, live loaded bytes, and presentation alias.
- The canary identifies the expected physical NPU and execution process.
- No secret or large binary artifact is staged.
- The orientation checkpoint is clean, committed, and pushed.
