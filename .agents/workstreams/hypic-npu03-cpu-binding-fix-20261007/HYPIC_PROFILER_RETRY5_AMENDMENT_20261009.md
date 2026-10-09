# HYPIC profiler retry5 amendment

Retry4 Decode was interrupted before capture: its continuous guard observed
external `Maxon4ick_vllm` PID 3541845 on physical NPU0 at
2026-10-09T17:18:18Z. The exact retry4-owned container, workers, and port
8223 were released. Retry4's terminal root is immutable and has no valid
Decode profile.

Retry5 is Decode-only and uses a new, never-before-used root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r5`.
The valid retry2 Prefill is not repeated. Model, image, HYPIC source,
service, warmup, profiler, capture, evidence, guard, and acceptance settings
remain as preregistered. A fresh direct-route check must establish that only
physical NPU0-3 and port 8223 are actually free. If a foreign process enters,
the attempt fails and releases only its own resources; it must not be reused.

The 46-column Prefill parser result remains a transparent miss of the original
`>=47` numeric acceptance gate, despite the presence of Level1 and
PipeUtilization semantic fields. Retry5 cannot retroactively alter that gate.

## Terminal result

Controller `exec-0000000000000507` terminated without a valid Decode profile.
At 2026-10-09T17:39:40Z, the continuous guard detected PID 3750311 on
physical NPU0, in the external `Maxon4ick_vllm` container
`87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa`.
Four guard samples had zero probe errors. The owned service was removed and
its workers and port 8223 were released. The root is now immutable.

The guard JSON's internal `attempt` field says r4 because the controller
retained a hard-coded label. Its file path, contract, result, container ID,
timestamps, and SHA256 identify this as r5; do not mistake the label for an
r4 rerun. The controller now derives the future guard label from its root.
Result SHA256: `b10005d2848cf4070761a38ebb9edf2b698fc8d1b2ab1fe1cd539f45d9fcc807`.
Guard SHA256: `c70898e22e29eaf0e77c4a69a9a9ee74c02670738c1422c6d4bb3be3e05bfdf1`.
Release SHA256: `60794eb7dc56140ac48c28a18379d3aa2c81357b84e0f9c6634a56d61c68482e`.
