# T36 upstream FusedGdnDecode findings

## Decision

Reject the exact T36 combined treatment before c5/c8/c16.  The pinned upstream
FusedGdnDecode operator is numerically admissible and produced a real,
repeatable decode improvement, but the warmed formal c1/32 TPOT P95 still
missed the project gate.  Do not rerun this exact combination unchanged and do
not present it as an accepted final candidate.

## Upstream boundary and project delta

The compute implementation is the unchanged experimental
`experimental/attention/fused_gdn_decode` operator from the pinned
ops-transformer snapshot
`d967eeb08ceef7c394d0d5e27767e5b08b77aa58`.  It fuses packed QKV splitting,
Q/K normalization, GDN gating, recurrent-state update, and output generation.
The shipped upstream torch bridge and generated OPP are mounted read-only.

The project-specific delta is only the missing integration seam:

- exact Qwen3.5-27B TP4 shape and dtype admission;
- pure-decode-only dispatch in vLLM-Ascend 0.23;
- BF16 or FP32 recurrent-state compatibility matching the upstream tiling keys;
- fail-closed behavior when the explicit contract is not satisfied;
- composition with retained T32 fused prefill and the experimental T35
  one-time conv-weight prepack;
- artifact hashes, activation proof, rollback, and official-image lifecycle.

No operator math, model weight, quantization, speculative decoding, TP
collective, or base-image source was replaced.

## Numerical admission

Artifact root:
`/cache/austinov/qwen35-t36-fused-gdn-decode-opp-v1`.

The exact device gate passed 48 BF16-input/BF16-state cases (12 shapes/seeds,
four recurrent steps each):

- maximum output absolute error: `3.0517578125e-05`;
- maximum recurrent-state absolute error: `4.8828125e-04`;
- invalid-output and invalid-state deltas: zero;
- repeat determinism deltas: zero;
- all outputs and states finite.

The earlier FP32-state gate also passed.  Both result files, the validation
script, OPP library, torch bridge, run package, wheel, and monkeypatch are
independently SHA-256 pinned by the launcher.

## Integration history

- v1 correctly failed closed during graph capture because the initial
  integration guard admitted FP32 recurrent state only, while the target
  service explicitly uses BF16 Mamba SSM cache.
- The pinned upstream source contains the matching BF16-state tiling key and
  kernel specialization.  After adding that already-supported dtype to the
  integration guard and running the independent BF16-state numerical gate, v2
  passed four-rank graph capture and service readiness.
- v2 activation proved four markers, one worker on each physical NPU0-3, no
  NPU4-7 device mounts, unchanged official image, one read-only Python
  monkeypatch mount, read-only upstream OPP/bridge mount, and no vLLM source
  overlays.

## Valid v2 evidence

Service artifact root:
`/cache/austinov/qwen35-t36-fused-gdn-decode-service-20260913-v2`.

- activation report: passed, SHA-256
  `de2b73d55f721f87641b1dda6e3f48ede8537a21a620c9eb37532ec75122df31`;
- smoke: 1/1, zero errors, natural EOS, SHA-256
  `11df687a3652045fdac93495a967d1a3c442fd6e1d8561c48c70264a7586c8d4`;
- independent warmup: 32/32, zero errors, natural EOS, SHA-256
  `9273ebb9b9a8c2712999f7b5fe7f2964a51b31c61ec1aa7f1958f213e7a7e9eb`;
- formal c1: 32/32, zero errors, natural EOS, SHA-256
  `71b8c2407d5624c6de4a1161995df2a1a6f9e5ce36cba5e149f0d0e00175a5a0`;
- stopped service log SHA-256
  `bf3ef1d61c2ca98d5406cf2d66cbd3dd75e9f71daead5074715ac128b2941980`.

| Metric | Fresh v14 control | T36 v2 | Reduction | Required |
|---|---:|---:|---:|---:|
| TTFT P95 | 841.073 ms | 615.101 ms | 26.867% | >=20% |
| TPOT P95 | 28.909 ms | 26.529 ms | 8.233% | >=10% |

The remaining deficit is `0.511 ms/token` relative to the exact
`26.0181 ms/token` threshold.  Compared with T35, T36 improves TPOT by
2.916%; compared with retained T32, the combined T35+T36 treatment improves
TPOT by 6.179%.  This proves useful upstream compute reuse, but not completion.

## Resume point

Keep T32 as the accepted TTFT base.  Retain T36 only as a proven experimental
decode component and provenance source, not as a promoted treatment.  The next
candidate must be materially different and upstream-derived, with a credible
budget above 0.511 ms/token after integration overhead.  Prefer either a newer
supported FusedGdnDecode integration/tiling improvement or a non-overlapping
decode/collective component.  It must first pass the same c1/32 fail-fast gate
before any c5/c8/c16 or full-quality run.
