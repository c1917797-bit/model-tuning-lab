# Qwen3.5 MMAR Timeline Findings

This note records the verified CANN msprof timeline evidence from the first
control profiling pass. It is intentionally scoped to evidence that already
exists on chicaihong01 and does not claim end-to-end performance improvement.

## Artifact

- Timeline report: `/cache/austinov/qwen35-cannbot-round0-timeline-20260909-v1.json`
- Report SHA256: `32239a5d4e40a3541012015b921e213f12e5c77903c340b581245404946a2e77`
- Source profiler root: `/cache/austinov/qwen35-cannbot-round0-msprof-control-20260909T092151Z`
- Profiled image ID: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
- Profiled image digest: `sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a`

## What was verified

- The profile was collected from four ranks in a fresh control container on
  physical NPU0-3.
- All four raw `op_summary` CSV files were hashed and parsed directly.
- `MatmulAllReduce` and `MatmulAllReduceMc2AicpuKernel` intervals overlap
  heavily, so their raw durations must not be summed as removable wall time.
- Decode M=1 MMAR cross-rank start spread is small:
  - `1,1536;1536,5120`: mean 7.996 us, p95 12.120 us across 6720 occurrences.
  - `1,4352;4352,5120`: mean 5.146 us, p95 8.050 us across 6720 occurrences.
- Prefill shapes show much larger cross-rank start skew while still finishing
  nearly together:
  - `1536,1536;1536,5120`: mean start spread 5139.448 us, p95 6929.155 us.
  - `274,1536;1536,5120`: mean start spread 6548.021 us, p95 8163.175 us.

## Interpretation

The current evidence does not support blindly retuning every decode MMAR launch
parameter. The decode M=1 ranks are already closely aligned, while prefill has a
larger arrival skew. The next candidate should therefore investigate the
prefill/collective lifecycle or scheduler arrival gap before adding a custom
operator path.

This is a profiling result, not a pass/fail performance result. A candidate only
graduates after request correctness, semantic quality gates, and the full P95
matrix pass.

## Next candidate direction

1. Keep the current monkeypatch delivery model: read-only mount plus PYTHONPATH
   injection into disposable containers.
2. Add a narrow diagnostic or patch around MMAR lifecycle timing rather than a
   broad operator replacement.
3. Run fixed-input smoke and 32-sample canary before any c1/c16 fail-fast.
4. Only if c1/c16 pass the TTFT >=20% and TPOT >=10% gates, expand to
   c1/c5/c8/c16 x3 and the full 357-sample paired quality gate.
