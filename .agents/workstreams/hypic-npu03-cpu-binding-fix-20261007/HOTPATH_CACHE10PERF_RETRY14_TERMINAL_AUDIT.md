# HYPIC-only/repeat3 retry14 terminal audit

## Classification

Retry14 is an environmental pre-health isolation failure, not a HYPIC
performance result. The exact HYPIC-owned service was removed. The foreign
workload was not stopped or modified, and NPU4–7 were not used.

## Frozen attempt and outcome

- Controller: exec-0000000000000242
- Immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry14
- Frozen phase: cache10perf, hypic-only, repeat3
- Continuous guard: 18 samples, zero probe errors
- Foreign process captured twice: PID 242978, physical NPU1, container
  efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6
  (cannbench_ds)
- Scored requests: 0; service health was not reached; metrics are null.
- Exact owned service container:
  2d85a0fbc2bc9841d3dbd21dc0009555308ae44fc73f4d0fadce9378b3161f8b;
  removed by the controller.
- Post-cleanup verification: physical NPU0–3 process list empty and port
  8223 free.

## Immutable evidence hashes

- contract.json:
  b260e81ab4f766ee1b5ee3c485d5d3f993dfdbb4ba8733dff339700616dd2c2a
- arm-result.json:
  8438fbd58b4be0c06412667c57442e7340e5dc08d1d7889a059f736113eaae0a
- hypic-only/hypic-evidence.jsonl:
  fb3f7f0f342b3738e637ecb517d90dc5b2f603ddc3ce0978dbb6a8cc6c9389be
- hypic-only/lane-guard.json:
  71f8ece8c31869544653661b26c9f520ed6a7a8210b93c2c4b79dfa8ad89b0ed
- hypic-only/pre-health-release.json:
  7afb397349d54ce1c19725bcd5e22523d84ac3e9d3d44cb8ed8222439e7ffc09

The sixth matched phase remains unmeasured. This report is not a HYPIC
performance verdict; the scientific protocol and quality rejection remain
unchanged.
