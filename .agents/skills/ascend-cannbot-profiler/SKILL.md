---
name: ascend-cannbot-profiler
description: Use when an Ascend inference paper or benchmark result requires CANN, profiler, operator, kernel, memory-movement, or HCCL communication analysis; consult cannbot-skills as an expert source before low-level changes.
---

# Ascend Cannbot Profiler

## Purpose

Bring CANN/operator-level discipline into Paper-to-Ascend and Ascend inference
benchmark work. Use this skill when a result cannot be explained at the Python,
configuration, or service layer alone, or when a paper proposes changes that
may land in vLLM-Ascend, CANN operators, kernels, memory movement, or HCCL
communication.

`cannbot-skills` is an expert reference source, not the main experiment owner.
This skill decides when to consult it, how to verify the real profiler/tooling
environment, and how to keep low-level conclusions scoped to evidence.

## When to use

Use this skill when any of these are true:

- a Paper-to-Ascend method touches attention kernels, MoE routing, expert GMM,
  KV cache layout, operator fusion, memory movement, communication overlap, or
  custom CANN/operator work;
- benchmark evidence shows a regression, noisy result, unexplained speedup, or
  bottleneck that needs profiler attribution;
- deciding whether to modify vLLM-Ascend, `ops-transformer`, CANN recipes, or a
  kernel/operator path;
- validating whether `torch_npu.profiler`, `msprof`, `asys`, or CANN offline
  parsing is available in the actual serving environment;
- translating profiler evidence into the next bounded tuning loop.

Do not use it merely because the workload runs on Ascend. Configuration-level,
scheduler-level, or built-in runtime-path experiments can stay with
`ascend-benchmark-evidence` unless profiling or low-level source mapping is
needed.

## Known target-host references

On `chicaihong01`, prior orientation prepared these source workspaces under
`/home/mtuser/cch`:

- `vllm-ascend`
- CANN `ops-transformer`
- `cannbot-skills`
- `cann-recipes-infer`

These paths are historical guidance, not permanent proof. Re-check the live
host and current commits before relying on them.

Prior evidence also found the vLLM-Ascend serving container contained
`torch_npu.profiler`, `msprof`, and `asys`, and that the inspected vLLM-Ascend
profiler path used `ProfilerLevel.Level1` with `AiCMetrics.PipeUtilization`.
Re-prove this in the actual container/session before a new claim.

## Workflow

1. If work is on `chicaihong01`, first use `chicaihong01-host-maintenance` and
   prove the canonical target repository and live target peer.
2. Read the active experiment record and branch-local handoff. Identify the one
   measured symptom this profiling pass should explain.
3. Re-prove the execution boundary: host vs container, active service, physical
   NPU IDs, process IDs, port, visible devices, and model/runtime identity.
4. Inspect the real serving environment for profiler tools. Prefer the profiler
   path already integrated into vLLM-Ascend before adding new instrumentation.
5. Consult `cannbot-skills` when present for CANN/profiler/operator guidance,
   but record any referenced rule as external expert guidance unless locally
   reproduced.
6. Keep the capture bounded. Warm compile/JIT outside the measured window, and
   profile Prefill and Decode separately unless the comparison deliberately
   covers both.
7. Validate profiler output completeness immediately. If raw collection looks
   valid but offline parsing fails, test filesystem/location issues before
   changing model code.
   An integrated vLLM-Ascend `/stop_profile` can leave only the raw
   `*_ascend_pt` tree. Parse a copy with the matching torch_npu/CANN image
   before judging CSV or trace completeness; preserve the original raw tree.
   Check every rank for a nonempty `kernel_details.csv`, `op_statistic.csv`,
   `api_statistic.csv`, and valid `trace_view.json`. Record the header width,
   rows, stack versions, and parser output. Use the presence of `Stream ID`,
   input/output shape fields, `aic_mac_ratio`, `aic_mte2_ratio`, and
   `aiv_vec_ratio` plus a recorded Level1/PipeUtilization config as the detailed
   metric gate. Exact column counts can vary by CANN release: 46 detailed
   columns were observed with torch_npu 2.10.0.post4/CANN 9.1.0, while the
   external Cannbot example describes approximately 47. A shallow nine-column
   file or missing statistics is still a failure. If a frozen experiment set
   an exact numeric threshold, record any mismatch as a protocol deviation
   instead of silently changing that experiment's verdict.
8. Analyze in this order: timeline gaps and serialization; per-step latency;
   top operators; top kernels with call count and shapes; AIC/MTE/AIV pipeline
   ratios; HCCL communication and overlap; cross-rank start/end spread;
   CPU/NUMA/scheduler correlation; source-path mapping.
9. Map the hot path to the smallest plausible layer: configuration, vLLM,
   vLLM-Ascend, CANN operator, `ops-transformer`, communication/topology, or
   system setting.
10. Feed an evidenced, opportunity-bounded treatment into
    `ascend-performance-optimization`. Feed a rejection or inconclusive gap
    directly back into `ascend-inference-tuning-loop`.

## Evidence rules

- Separate observed local evidence from `cannbot-skills` guidance.
- Treat summed operator or kernel durations across overlapping streams as
  hotspot-ranking evidence, not removable wall time. Use timeline union,
  serialization gaps, or critical-path evidence for an opportunity bound.
- An AICPU or communication duration can include waiting. Correlate its start,
  end, dependent kernels, and cross-rank spread before labeling it compute or
  launch overhead.
- Do not claim a kernel/operator root cause from host telemetry alone.
- Do not compare profiler captures across drifted model, workload, container,
  CANN, driver, firmware, power mode, or device topology.
- Store raw profiler trees, trace databases, CANN dumps, and large logs outside
  Git, usually under persistent `/cache` storage. Commit only commands, hashes,
  compact summaries, artifact paths, and decisions.
- Do not mutate CANN, drivers, firmware, clocks, power settings, or shared
  system services without explicit authorization and rollback.

## Operator and collective admission

- Capture the exact real-service phase, shapes, dtype, layout, ranks, and call
  frequency before generating or tuning an operator.
- Benchmark the official fused implementation and the simplest supported
  decomposition first. Reject a custom route that cannot beat the correct
  incumbent at the real shapes.
- Use `cannbot-skills` as an expert workflow and source of checks, not as
  black-box proof that a generated operator is correct or fast.
- Prove the proposed chip/runtime route on the actual target. A mechanism
  documented for another Ascend generation, compiler target, transport, or
  communication architecture is not transferable evidence.

Before service E2E, a custom multi-rank collective must pass a bounded
fresh-process canary that records per-rank phase markers and proves:

1. communicator initialization and finalization are balanced;
2. all ranks make progress or produce one globally visible error;
3. every wait has a timeout and a diagnosable failure phase;
4. fresh logical epochs prevent stale-state, restart, and ABA reuse;
5. repeated start/stop and crash-recovery trials do not inherit prior state.

If the canary stalls, record exact candidate bytes and the last completed phase,
clean up only owned resources, and close unchanged retries. A source fix is not
the root cause unless the failure phase or outcome changes.

## Lessons already learned

- A local operator win can still lose end to end when routing, packing, memory
  movement, or synchronization overhead dominates.
- Missing detailed profiler configuration can produce shallow kernel evidence.
- Standard first-pass NPU analysis should use Level1 plus PipeUtilization when
  supported by the actual stack.
- Profiler schedules must exit the active record window cleanly.
- Host and container tool inventories can differ; inspect where the workload
  actually runs.
- Some filesystems can break CANN offline parsing. Treat parser failure as an
  artifact-location hypothesis before rewriting runtime code.
