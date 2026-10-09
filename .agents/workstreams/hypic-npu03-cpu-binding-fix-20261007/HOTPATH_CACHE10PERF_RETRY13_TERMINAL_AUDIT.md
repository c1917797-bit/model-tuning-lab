# HYPIC-only/repeat3 retry13 terminal audit

## Classification

Retry13 is an environmental pre-health isolation failure, not a HYPIC
performance result. No service health or scored benchmark request was reached.
The exact HYPIC-owned service was removed; the foreign workload was untouched.

## Frozen attempt and outcome

- Controller: exec-000000000000023e
- Immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry13
- Frozen phase: cache10perf, hypic-only, repeat3
- Continuous guard: 2 samples, zero probe errors
- Foreign process: PID 202622, physical NPU0, container
  87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa
  (Maxon4ick_vllm); human owner unverified
- Scored requests: 0; metrics are null.
- Exact owned service container:
  d96e0e80032cf4f5aa1f5abb277b95b8a74ef9df8308eb6f5e9f6a46fbb893e6;
  removed by the controller.
- Post-cleanup verification: physical NPU0–3 process list empty and port
  8223 free.

## Immutable evidence hashes

- contract.json:
  9819b6073659577c063afa5f91403c4fed7ec4f191f95e4c0345a5edb56c0838
- arm-result.json:
  300c9873ea527885172b4b52180965fa00a0da158a3a97f2ee2ed23fd26c13e0
- hypic-only/hypic-evidence.jsonl:
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- hypic-only/lane-guard.json:
  b434b9b6dabc56f574b6cd8a1bf64f28810a55ac19a706fcc573e895391cf9e9
- hypic-only/pre-health-release.json:
  0d5f1275949210bd637b181f6af63b0540a53e1b0a149663f721ba8a9fcd0168

This record does not change the scientific result or acceptance gates. Retry14
has its own immutable root and validates this exact pre-health failure before
any launch.
