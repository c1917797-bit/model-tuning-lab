# HYPIC phase-6 retry7 terminal audit

- Classification: environmental pre-health isolation failure; not a HYPIC performance verdict.
- Controller: `exec-00000000000001e1`, exited 1 after 97.966 seconds under the corrected 14,400-second asynchronous timeout.
- Immutable root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry7`.
- Contract SHA256 `f82589e57fd6a8161d3a02d76820879d14f5d36f35252e61d90227264a65caae`; arm-result SHA256 `ae30162d2f99350346c68dcc6c095f50af53586231e99da8957d27772ab44292`; lane-guard SHA256 `d94ac87d6dad9e092251c5508edc6a5fa989f79898b212cdae96a6ba20baf547`; HYPIC startup evidence SHA256 `65f9cd806f8a57aac22dfc34b3069759024161605980ad4057db637a5d18d0e3`; pre-health release SHA256 `e215032b9f93fe5437ccb72de63beac10362f5ccf922a919cb0d6679ac0030be`.
- Continuous guard: 18 samples, zero probe errors. It observed foreign PID `3843558` on physical NPU1 at 11:05:13.067Z and 11:05:14.742Z, from container `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6` (`cannbench_ds`). At inspection this container had been running since 2026-10-06 with command `sleep infinity`; human launcher/owner remains unverified. Do not stop or alter it.
- The service did not reach health. No benchmark command or `performance.json` exists; `arm-result.json` is invalid with null metrics. No performance sample was measured.
- The exact retry7-owned service container `e33f1c39450acd07388a049af1587cc2ee28eed7fca9da586c7487526c37bc7d` was removed by the controller. Post-cleanup NPU0–3 had no running processes, port 8223 was free, and the retry7 label returned no container. No foreign resource was changed.

Retry7 is an environmental failure. Preserve this root and the separate HYPIC r13 paired-quality rejection; no performance inference follows from this run.
