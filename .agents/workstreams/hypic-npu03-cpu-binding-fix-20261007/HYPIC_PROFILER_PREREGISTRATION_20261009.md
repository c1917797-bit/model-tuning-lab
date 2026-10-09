# HYPIC NPU0-3 profiler preregistration

Date: 2026-10-09

## Purpose

Validate the real `ascend-cannbot-profiler` capture path against the unresolved
HYPIC hot/cold-path and quality-regression symptom. This is a bounded diagnostic
case, not a rerun or reinterpretation of the frozen six-phase performance and
127x3 quality verdicts.

## Frozen identity and scope

- Host: `chicaihong01/ma`, direct route only.
- Physical devices: NPU0-3 only; NPU4-7 are forbidden.
- Port: 8223.
- Image: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- Model: `/cache/efim/Qwen3.6-27B`, TP4.
- HYPIC source: `/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008`
  at `c12060cd47e7575ead059983d7a8bb4704165c98`.
- Service settings match the accepted retry21 identity, including
  `enable_cpu_binding=false`, material cache 3584 MiB, ten materialized
  segments, and GPU memory utilization 0.85.
- New raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r1`.

## Capture method

Use vLLM-Ascend's integrated `/start_profile` and `/stop_profile` endpoints.
Static source proof must show `ProfilerLevel.Level1`,
`AiCMetrics.PipeUtilization`, CPU+NPU activities, and text export. Compile/JIT
and two HYPIC materialization warmups occur before capture.

Two exact-owned services run serially:

1. `prefill`: start profiling before a 32768-token segmented request and stop
   after its one-token response. This is explicitly a Prefill-focused window;
   the one required Decode token remains in the trace.
2. `decode`: begin a 32-token streaming request with profiling off, pause after
   the first non-empty response chunk (Prefill complete), start profiling, then
   retain at least 16 subsequent non-empty Decode chunks before stopping.

## Acceptance

- Fresh admission proves NPU0-3 and port 8223 are free.
- A continuous physical-process guard records no foreign NPU0-3 process or
  probe error throughout each phase.
- Four TP workers are mapped one-to-one to physical NPU0-3.
- Both endpoint calls succeed and every measured request succeeds.
- Decode captures at least 16 post-TTFT chunks, exceeding the ten-step gate.
- Each phase produces non-empty profiler artifacts; artifact inventory and
  hashes are recorded. If `kernel_details.csv` is emitted, its header width is
  recorded and must be at least 47 columns. Absence is reported, never hidden.
- Only the exact owned container is stopped/removed; its workers and port are
  proven released.

Any foreign process, profiler endpoint failure, incomplete artifact, early
Decode termination, or cleanup ambiguity makes that phase invalid. Speed or
profile success cannot override the frozen quality decision
`REJECT_OR_QUALIFY` or claim a CANN/HCCL root cause by itself.
