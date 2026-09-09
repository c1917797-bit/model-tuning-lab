# Ascend maintainer skill experience-ingestion handoff

## Status

- Execution: completed.
- Integration: ready for serialized review; not merged to the primary branch.
- Base: `93b3ae4659a1bc0e926998608a55efc96e174d8e`.
- No NPU, container, port, or host runtime resource is required.

## Objective

Convert reusable Qwen3.5 optimization lessons into narrow decision and evidence
rules in the existing maintainer skill tree. Do not encode experiment labels,
one-off measurements, or unverified performance claims as general policy.

## Completed changes

1. Added an opportunity-size and real-runtime-path admission gate before expensive
   implementation.
2. Distinguished diagnostics from treatment and closed unchanged failed routes.
3. Strengthened microbenchmark-to-E2E translation, fail-fast, and quality evidence.
4. Strengthened profiler critical-path and custom-collective lifecycle checks.
5. Clarified active versus historical container device declarations while
   preserving explicitly stricter user policies.

The changes are intentionally generic: no t11/t12/t13 label or one-off latency
number was promoted into maintainer policy. The long-term Qwen3.5 performance
and quality target remains open and requires device evidence.

## Validation

- `./scripts/validate-mst.sh`: passed, 26 skills.
- `git diff --check`: passed after each coherent change.
- All three workstream JSON files parse with `python3 -m json.tool`.
- Manual content review confirms every ingested lesson has a trigger, changed
  action, destination skill, and verification condition.

## Next actions

1. Push the final validated checkpoints once GitHub connectivity is healthy.
2. Review the work branch and integrate it serially.
3. Apply the new admission gates to the next Qwen3.5 candidate; do not treat
   this process update as performance or quality acceptance.
