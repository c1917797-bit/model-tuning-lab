# Ascend maintainer skill experience-ingestion handoff

## Status

- Execution: started.
- Integration: not ready.
- Base: `93b3ae4659a1bc0e926998608a55efc96e174d8e`.
- No NPU, container, port, or host runtime resource is required.

## Objective

Convert reusable Qwen3.5 optimization lessons into narrow decision and evidence
rules in the existing maintainer skill tree. Do not encode experiment labels,
one-off measurements, or unverified performance claims as general policy.

## Planned changes

1. Add an opportunity-size and real-runtime-path admission gate before expensive
   implementation.
2. Distinguish diagnostics from treatment and close unchanged failed routes.
3. Strengthen microbenchmark-to-E2E translation, fail-fast, and quality evidence.
4. Strengthen profiler critical-path and custom-collective lifecycle checks.
5. Clarify active versus historical container device declarations while
   preserving explicitly stricter user policies.

## Next actions

Implement the smallest coherent skill edits, validate the maintainer tree after
each group, update this handoff and evidence, then push each coherent checkpoint.
