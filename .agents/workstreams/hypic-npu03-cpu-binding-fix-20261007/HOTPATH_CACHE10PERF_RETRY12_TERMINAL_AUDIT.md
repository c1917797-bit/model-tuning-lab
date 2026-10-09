# HYPIC-only/repeat3 retry12 terminal audit

## Classification

Retry12 is an environmental pre-health isolation failure, not a HYPIC
performance result. The exact HYPIC-owned service was removed. No foreign
container was stopped or modified, and NPU4–7 were not used.

## Frozen attempt and outcome

- Controller: exec-000000000000022f
- Immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry12
- Frozen phase: cache10perf, hypic-only, repeat3
- Continuous guard: 14 samples, zero probe errors
- Foreign process captured twice: PID 91292, physical NPU1, container
  efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6
  (cannbench_ds)
- Scored requests: 0; service health was not reached; performance metrics
  are null.
- Exact owned service container:
  45700f96fe19350e43e04490555b97b856a63854c8a4325346b90e546c62f150;
  removed by the controller.
- Post-cleanup verification: physical NPU0–3 process list empty and port
  8223 free.

## Immutable evidence hashes

- contract.json:
  29bcacfab5221eb41b600684bbf62169768006174c25922d8a66fb22aa2d49b8
- arm-result.json:
  51cf772d9a5a89d8b54d0d03a2340f4fd182b912d1b117abc7b47e25eb27c0be
- hypic-only/hypic-evidence.jsonl:
  9ebb2fea144c6a1f907c13c1a1ce22e4eb345bf171b5f6b61882caf0bce7dc11
- hypic-only/lane-guard.json:
  73194d540af378da878fe0ce1eb7d306fe1535402bd02606de886909a1753d8c
- hypic-only/pre-health-release.json:
  3c029e80400e94ea2baf4b504b4988986e49ee2abdd12cb95a953068904af15c

The retry13 admission test validates the immutable retry12 failure evidence,
exact foreign PID/container identity, zero probe errors, and exact owned
resource release. Retry13 has a distinct root and does not alter the frozen
protocol or scientific acceptance gates.
